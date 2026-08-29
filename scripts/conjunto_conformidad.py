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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docbench_es.extract.conjunto import veredictos_posibles as _veredictos

RAIZ = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(RAIZ / "scripts"))

from fuera_de_git import exige  # noqa: E402

PLAN = RAIZ / "runs" / "l5" / "conformidad.yaml"
FIXTURES = RAIZ / "runs" / "l4" / "fixtures"
DOCS = RAIZ / "runs" / "l3" / "docs"
MANIFIESTO = RAIZ / "runs" / "l3" / "manifiesto.json"


@dataclass(frozen=True)
class Elegido:
    """Un documento del conjunto, con lo declarado y lo que dice la verdad congelada."""

    ident: str
    tabla: str
    declara_combinadas: bool
    spans_en_la_verdad: int
    fixture_existe: bool
    forma_declarada: str
    forma_real: str
    paginas_declaradas: int
    paginas_reales: int | None
    pdf: bool

    @property
    def cuadra(self) -> bool:
        """**`fixture_existe` va primero, y no es un detalle.**

        Sin él, un fixture borrado daba `spans_en_la_verdad=0` y un documento declarado
        «sin combinadas» seguía cuadrando: **un fichero desaparecido pasaba en silencio**,
        que es la forma de este repo de decir que la comprobación no comprobaba.
        """
        return (
            self.fixture_existe
            and self.declara_combinadas == (self.spans_en_la_verdad > 0)
            and self.forma_declarada == self.forma_real
            and self.paginas_declaradas == self.paginas_reales
        )

    def por_que_no(self) -> str:
        """Qué falla, en castellano y nombrándolo. Vacío si cuadra."""
        if not self.fixture_existe:
            return f"{self.tabla}: no existe runs/l4/fixtures/{self.tabla}.json"
        if self.declara_combinadas != (self.spans_en_la_verdad > 0):
            return (
                f"{self.tabla}: declara combinadas={self.declara_combinadas} y la verdad "
                f"congelada trae {self.spans_en_la_verdad} spans"
            )
        if self.forma_declarada != self.forma_real:
            return f"{self.tabla}: declara «{self.forma_declarada}» y es «{self.forma_real}»"
        if self.paginas_declaradas != self.paginas_reales:
            return (
                f"{self.ident}: declara {self.paginas_declaradas} páginas y el manifiesto "
                f"dice {self.paginas_reales}"
            )
        return ""


def _paginas() -> dict[str, int]:
    """`external_id` → páginas, del manifiesto de L3. **Versionado**, así que esto se
    puede comprobar en cualquier clon, a diferencia de los PDF."""
    man = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    return {d["external_id"]: int(d["n_pages"]) for d in man["documentos"]}


def conjunto() -> list[Elegido]:
    """Los elegidos, con su declaración contrastada contra los fixtures de L4.

    **Todo lo que esta función compara sale de ficheros VERSIONADOS** —los fixtures
    congelados y el manifiesto—, salvo `pdf`. Esa separación es la que permite que la
    parte que importa se compruebe en CI y sólo los bytes del corpus se salten.
    """
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    paginas = _paginas()
    fuera: list[Elegido] = []
    for clave, declara in (("con_celdas_combinadas", True), ("sin_celdas_combinadas", False)):
        for entrada in plan[clave]:
            tabla = str(entrada["tabla"])
            ruta = FIXTURES / f"{tabla}.json"
            spans, forma_real = 0, "(sin fixture)"
            if ruta.exists():
                d = json.loads(ruta.read_text(encoding="utf-8"))
                spans = len(d.get("spans") or [])
                dim = d["dimension"]
                forma_real = f"{dim['n_rows']}x{dim['n_cols']} " + (
                    f"con {spans} span{'s' if spans != 1 else ''}" if spans else "sin spans"
                )
            fuera.append(
                Elegido(
                    ident=str(entrada["id"]),
                    tabla=tabla,
                    declara_combinadas=declara,
                    spans_en_la_verdad=spans,
                    fixture_existe=ruta.exists(),
                    forma_declarada=str(entrada["forma"]),
                    forma_real=forma_real,
                    paginas_declaradas=int(entrada["paginas"]),
                    paginas_reales=paginas.get(str(entrada["id"])),
                    pdf=(exige(DOCS) / f"{entrada['id']}.pdf").exists(),
                )
            )
    return fuera


def veredictos_posibles(elegidos: list[Elegido]) -> set[str]:
    """Qué casillas de `VeredictoSpans` puede emitir este conjunto. **Su denominador.**

    **La regla no vive aquí: vive en `docbench_es.extract.conjunto`**, que es lo que corre
    de verdad cuando alguien pasa un extractor por la suite. Esto era una segunda copia
    —misma decisión escrita dos veces— y una copia sólo tiene dos futuros: quedarse vieja
    o obligar a acordarse. Se delega, y lo que queda aquí es el puente desde `Elegido`.
    """
    return set(_veredictos(any(e.spans_en_la_verdad > 0 for e in elegidos)))


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
    descuadran = [e.por_que_no() for e in elegidos if not e.cuadra]
    if descuadran:
        print("  DESCUADRAN con la verdad congelada de L4:")
        for d in descuadran:
            print(f"    {d}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
