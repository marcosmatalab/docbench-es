"""De qué documentos se alimenta la suite de conformidad. **El conjunto se ELIGE.**

`veredicto_de_spans` devuelve `SIN_EVIDENCIA` cuando un extractor declara
`expresses_spans=False`, su formato sí permite spans y **no hubo ocasión** de demostrarlo.
Si el conjunto no trajera ni una celda combinada, **todo extractor saldría `SIN_EVIDENCIA`
para siempre** y el veredicto no discriminaría nada: una comprobación cuyo verde no
significa lo que parece.

Por eso el conjunto se declara en un fichero —`runs/l5/conformidad.yaml`— con **qué
casillas del veredicto puede producir**, y por eso ese fichero no es la última palabra:

**`trae_combinadas` sale del FIXTURE CONGELADO, no del YAML.** El YAML dice cuál cree que
trae combinadas; aquí se mira cuántos `spans` tiene su tabla en la verdad de referencia de
L4, que está congelada. Si el fixture falta, esto **levanta**: un fichero que desaparece
daría `spans=0`, o sea «no trae combinadas», o sea un conjunto degradado en silencio a uno
que ya no puede confirmar un `False` honesto. Es el mismo agujero que `Elegido.cuadra`
tenía en `scripts/conjunto_conformidad.py` hasta que se le puso `fixture_existe` delante.

Las rutas entran por argumento y no salen de una raíz adivinada: quien traiga su extractor
trae su conjunto, y un `runs/` codificado aquí sería el camino privilegiado que
`.claude/rules/extractores.md` prohíbe.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import yaml

from docbench_es.errors import ContractViolation
from docbench_es.extract.conformance import Caso

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from pathlib import Path

    from docbench_es.corpus.store import Almacen

__all__ = ["Conjunto", "cargar_conjunto", "veredictos_posibles"]

SECCIONES = (("con_celdas_combinadas", True), ("sin_celdas_combinadas", False))
"""Las dos listas del YAML. La segunda importa tanto como la primera: sin un documento
**sin** combinadas, un extractor que las inventara donde no las hay pasaría."""


@dataclass(frozen=True)
class Conjunto:
    """Los casos y **el denominador del conjunto**: qué puede y qué no puede producir."""

    casos: tuple[Caso, ...]
    con_combinadas: int
    origen: Path

    @property
    def hay_ocasion(self) -> bool:
        return self.con_combinadas > 0

    def __str__(self) -> str:
        return (
            f"{len(self.casos)} documentos · {self.con_combinadas} con celdas combinadas "
            f"en la verdad congelada · puede producir "
            f"{', '.join(veredictos_posibles(self.hay_ocasion))} · {self.origen}"
        )


def veredictos_posibles(hay_ocasion: bool) -> list[str]:
    """Qué casillas de `VeredictoSpans` puede emitir un conjunto. **Su denominador.**

    `CONTRADICCION` y la mitad de `COHERENTE` no dependen del conjunto: salen de lo que el
    extractor declare. Las dos que sí dependen son `ESCONDIDO` —hace falta que el
    documento traiga combinadas para que el extractor pueda emitirlas— y la forma de
    `COHERENTE` que confirma un `False` honesto, que necesita lo mismo.
    """
    return sorted(
        {"CONTRADICCION", "COHERENTE"} | ({"ESCONDIDO"} if hay_ocasion else {"SIN_EVIDENCIA"})
    )


def _spans(fixture: Path) -> int:
    if not fixture.exists():
        raise ContractViolation(
            f"falta el fixture congelado {fixture}. Sin él, «trae celdas combinadas» "
            f"pasaría a ser una opinión del YAML, y un fichero que desaparece degradaría "
            f"el conjunto sin que nada se pusiera rojo"
        )
    return len(json.loads(fixture.read_text(encoding="utf-8")).get("spans") or [])


def cargar_conjunto(plan: Path, almacen: Almacen, fixtures: Path) -> Conjunto:
    """Los casos declarados en `plan`, con sus bytes y con su verdad congelada.

    Levanta si el YAML declara una cosa y el fixture dice otra: un conjunto que no cuadra
    con la verdad de referencia no es un conjunto degradado, es uno que no se sabe qué mide.
    """
    declarado = yaml.safe_load(plan.read_text(encoding="utf-8"))
    casos: list[Caso] = []
    con = 0
    for clave, dice_que_trae in SECCIONES:
        for entrada in declarado[clave]:
            trae = _spans(fixtures / f"{entrada['tabla']}.json") > 0
            if trae is not dice_que_trae:
                raise ContractViolation(
                    f"{entrada['tabla']}: {plan.name} lo pone en {clave} y la verdad "
                    f"congelada de L4 dice {'' if trae else 'NO '}traer celdas combinadas"
                )
            casos.append(Caso(doc=almacen.cargar(str(entrada["id"])), trae_combinadas=trae))
            con += int(trae)
    return Conjunto(casos=tuple(casos), con_combinadas=con, origen=plan)
