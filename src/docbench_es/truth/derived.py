"""§9.4 · La verdad de referencia **derivada de la versión estructurada oficial**.

El modo `DERIVED` de ADR-0002: la verdad sale de un documento que el propio
organismo publica en estructura —el XML del BOE— así que **cuesta cero y no la
escribe nadie de este proyecto**. Es la premisa económica de todo el banco: sin
ella, medir mil documentos exigiría anotarlos a mano.

## Quién ensambla, y por qué aquí

**`truth.derived` ensambla el `Truth`; el adaptador aporta la materia prima.** No es
una obligación del contrato de capas —`truth` y `entity` son hermanos en la misma
línea de `.importlinter` y pueden importarse en las dos direcciones, comprobado por
ejecución en `tests/unit/test_capas_permitidas.py`—. Es una decisión de diseño, y la
razón es **L13**:

> La segunda entidad **hereda el ensamblado en vez de reimplementarlo.**

Todo lo que es común a cualquier entidad con verdad derivada —validar las tablas,
sacar de la verdad las que no se pueden puntuar, poner a `None` los campos que no
son de este modo, fechar— vive aquí una vez. Lo que el adaptador aporta es lo único
que sabe él: **sus tablas**. Si el ensamblado viviera en el adaptador, la segunda
entidad lo copiaría, y la tercera copiaría la copia.

## Precondiciones declaradas

- **Este módulo NO baja nada.** Recibe las tablas ya extraídas. Quien las consigue
  es el adaptador, que es quien tiene la red.
- **Una tabla que `validate` rechaza NO entra en la verdad, y se cuenta.** Una
  verdad que incluyera una tabla malformada puntuaría a todos los extractores
  contra algo que el propio proyecto declara inválido. Salen en `descartadas`, con
  su causa, porque la regla de oro 6 dice que ningún error se traga.
- **`facts` va VACÍO, y es una desviación declarada de §9.4** (límite 67). El manual
  dice que `truth` genera los `Fact` con plantillas sobre la matriz; eso exige el
  vocabulario de §9.6, que es **L9**, y es su único consumidor. La tupla vacía dice
  «no hay hechos», no unos falsos.
- **`confidence`, `n_annotators` y `discordance_rate` son `None` SIEMPRE aquí.** Son
  de `ANNOTATED` y `CONSENSUS`. Un cero se agregaría y mentiría.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from docbench_es.core.canonical import validate
from docbench_es.types import Truth

if TYPE_CHECKING:  # pragma: no cover - sólo para el tipado
    from collections.abc import Sequence

    from docbench_es.types import CanonicalTable, DocRef

__all__ = ["Derivacion", "derivar"]


@dataclass(frozen=True)
class Derivacion:
    """La verdad, **y lo que quedó fuera de ella con su causa**.

    Devolver sólo el `Truth` escondería las tablas descartadas, y la tasa de tablas
    sin verdad de referencia es un resultado del hito, no un detalle.
    """

    verdad: Truth
    descartadas: tuple[tuple[int, tuple[str, ...]], ...]
    """`(índice de la tabla, hallazgos fatales)`. El índice es el del documento, no
    el de la verdad: hace falta para ir a mirarla."""

    @property
    def n_evaluables(self) -> int:
        return len(self.verdad.tables)


def derivar(ref: DocRef, tablas: Sequence[CanonicalTable]) -> Derivacion:
    """El `Truth` en modo `DERIVED` a partir de las tablas del documento oficial.

    **Determinista y sin efectos**: las mismas tablas dan la misma verdad, salvo
    `built_at`. No toca red, ni disco, ni reloj más allá de esa marca.
    """
    buenas: list[CanonicalTable] = []
    fuera: list[tuple[int, tuple[str, ...]]] = []
    for i, t in enumerate(tablas):
        ok, problemas = validate(t)
        if ok:
            buenas.append(t)
        else:
            # Sólo los FATALES: un `HUECO_COLA` informativo no saca a nadie de la
            # verdad, y meterlo aquí inflaría la tasa de descarte con ruido legal.
            fuera.append((i, tuple(p for p in problemas if _es_fatal(p))))
    return Derivacion(
        verdad=Truth(
            mode="DERIVED",
            doc_ref=ref,
            tables=tuple(buenas),
            facts=(),
            confidence=None,
            n_annotators=None,
            discordance_rate=None,
            built_at=datetime.now(UTC),
        ),
        descartadas=tuple(fuera),
    )


def _es_fatal(problema: str) -> bool:
    from docbench_es.types import HallazgoTabla

    return HallazgoTabla(problema.split(":", 1)[0]).es_fatal
