"""El conjunto de conformidad de extractores: qué trae y qué veredictos puede producir.

    uv run python scripts/conjunto_conformidad.py

## Por qué esto no es una lista y ya

Porque `veredicto_de_spans` devuelve `SIN_EVIDENCIA` cuando un extractor declara
`expresses_spans=False`, su formato sí permite spans, y **no hubo ocasión** de
demostrarlo. Si el conjunto no trajera ni una celda combinada, **todo extractor saldría
`SIN_EVIDENCIA` para siempre** y el veredicto no discriminaría nada.

Así que el conjunto **declara qué casillas puede producir**, igual que todo guardián de
este repo declara su denominador — y este programa **comprueba esa declaración contra la
verdad de referencia de L4**, que está congelada. «Trae celdas combinadas» no es una
opinión: son los `spans` de un fixture que no se puede tocar.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
PLAN = RAIZ / "runs" / "l5" / "conformidad.yaml"
FIXTURES = RAIZ / "runs" / "l4" / "fixtures"
DOCS = RAIZ / "runs" / "l3" / "docs"


@dataclass(frozen=True)
class Elegido:
    """Un documento del conjunto, con lo declarado y lo que dice la verdad congelada."""

    ident: str
    tabla: str
    declara_combinadas: bool
    spans_en_la_verdad: int
    pdf: bool

    @property
    def cuadra(self) -> bool:
        return self.declara_combinadas == (self.spans_en_la_verdad > 0)


def conjunto() -> list[Elegido]:
    """Los elegidos, con su declaración contrastada contra los fixtures de L4."""
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    fuera: list[Elegido] = []
    for clave, declara in (("con_celdas_combinadas", True), ("sin_celdas_combinadas", False)):
        for entrada in plan[clave]:
            tabla = str(entrada["tabla"])
            ruta = FIXTURES / f"{tabla}.json"
            spans = 0
            if ruta.exists():
                spans = len(json.loads(ruta.read_text(encoding="utf-8")).get("spans") or [])
            fuera.append(
                Elegido(
                    ident=str(entrada["id"]),
                    tabla=tabla,
                    declara_combinadas=declara,
                    spans_en_la_verdad=spans,
                    pdf=(DOCS / f"{entrada['id']}.pdf").exists(),
                )
            )
    return fuera


def veredictos_posibles(elegidos: list[Elegido]) -> set[str]:
    """Qué casillas de `VeredictoSpans` puede emitir este conjunto. **Su denominador.**

    `CONTRADICCION` y la mitad de `COHERENTE` no dependen del conjunto: salen de lo que
    el extractor declare. Las dos que sí dependen son `ESCONDIDO` —hace falta que el
    documento traiga combinadas para que el extractor pueda emitirlas— y la forma de
    `COHERENTE` que confirma un `False` honesto, que necesita lo mismo.
    """
    hay_ocasion = any(e.spans_en_la_verdad > 0 for e in elegidos)
    posibles = {"CONTRADICCION", "COHERENTE"}
    if hay_ocasion:
        posibles.add("ESCONDIDO")
    else:
        # Sin ocasión, el `False` honesto no se puede confirmar NUNCA.
        posibles.add("SIN_EVIDENCIA")
    return posibles


def main() -> int:
    elegidos = conjunto()
    con = [e for e in elegidos if e.spans_en_la_verdad > 0]
    print(f"\n  {len(elegidos)} documentos · {len(con)} con celdas combinadas en la verdad\n")
    print(f"  {'documento':<20} {'tabla':<24} {'declara':>8} {'spans':>6} {'pdf':>4} {'?':>2}")
    for e in elegidos:
        print(
            f"  {e.ident:<20} {e.tabla:<24} {e.declara_combinadas!s:>8} "
            f"{e.spans_en_la_verdad:>6} {e.pdf!s:>4} {'ok' if e.cuadra else 'NO':>2}"
        )
    print(
        f"\n  veredictos que este conjunto PUEDE producir: {sorted(veredictos_posibles(elegidos))}"
    )
    if not con:
        print("  AVISO: sin ni una celda combinada, todo extractor saldría SIN_EVIDENCIA")
    descuadran = [e.tabla for e in elegidos if not e.cuadra]
    if descuadran:
        print(f"  DESCUADRAN con la verdad congelada de L4: {descuadran}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
