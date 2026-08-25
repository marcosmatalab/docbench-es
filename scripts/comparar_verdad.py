"""¿Reproduce la verdad derivada las 30 tablas transcritas a mano? **El comando.**

Las reglas de qué cuenta como «reproduce» están en **ADR-0040**, escritas y
congeladas **antes de correr esto ni una vez**, porque quien escribió los fixtures,
quien escribió el código medido y quien escribe el comparador son la misma persona.

    uv run python scripts/comparar_verdad.py --detalle
    uv run python scripts/comparar_verdad.py --informe   # runs/l4/informe.json

## El colocador de aquí es INDEPENDIENTE, y es lo más importante del fichero

Para saber en qué columna cae cada celda anclada de un fixture hay que colocarlas.
**Esto NO usa `core.canonical._rejilla`**, y la razón es el límite 52: si el fixture
se coloca con el mismo código que coloca la verdad, **un error de colocación se
cancela en los dos lados** y la comparación sale verde sobre dos tablas igualmente
mal construidas. Es literalmente lo que pasó con el grupo de filas: la colocación
estaba mal y ninguna suite lo veía.

Son veinte líneas escritas a mano con la regla del estándar. **Si discrepan de
`_rejilla`, eso es un hallazgo, no un fallo de aquí.**

## El INFORME, y por qué el desglose sale de aquí y no de atar cabos

`--informe` emite `runs/l4/informe.json` con **una fila por fixture**: si coincide,
cuántas discrepancias tiene y de qué clase, si está **contaminado** y si se
**corrigió** tras adjudicar. Con eso, el desglose publicado —«21 coincidencias
limpias + 1 contaminada + 3 corregidas»— **se lee del artefacto**.

**Antes se deducía**, cruzando a mano la lista de fixtures con discrepancia contra un
`"contaminadas": 1` que ni siquiera decía cuál era, y por eso se llegó a publicar una
horquilla —«21 o 22»— sobre algo que estaba **completamente determinado por dos
artefactos que ya existían**. Una cifra derivable publicada como no medible dice
menos de lo que se sabe.

## Qué se compara, y con qué alcance

- **La DIMENSIÓN, en las 30**, ventaneadas incluidas. Es lo que recupera lo que la
  ventana no ve, y es exactamente donde estaba el fallo del grupo de filas.
- **El CONTENIDO, según el `alcance`**: las 27 completas posición a posición; las 3
  con ventana, sólo su ventana y su última fila.
- **Posición a posición**, con los tres estados que L1 construyó: celda **anclada**,
  posición **cubierta** por un span, y **hueco**. Confundir vacío con ausente
  perdería la distinción que TEDS-S puntúa 1,000000 contra 0,857143.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import informe_l4  # noqa: E402

from docbench_es.core.canonical import normalize_cell_text  # noqa: E402
from docbench_es.entity import boe_xml  # noqa: E402
from docbench_es.truth.derived import derivar  # noqa: E402
from docbench_es.types import CanonicalTable, DocRef  # noqa: E402

ANCLA, CUBIERTA, HUECO = "ancla", "cubierta", "hueco"

Rejilla = dict[tuple[int, int], str]
Textos = dict[tuple[int, int], str]


def _entero(d: dict[str, object], k: str) -> int:
    v = d.get(k)
    return v if isinstance(v, int) else -1


@dataclass(frozen=True)
class Discrepancia:
    """Una diferencia, **sin adjudicar**. La causa la decide una persona (ADR-0039)."""

    fixture: str
    clase: str
    detalle: str


def colocar(filas: list[list[str]], spans: list[dict[str, int]]) -> tuple[Rejilla, Textos]:
    """La rejilla del FIXTURE, con un colocador escrito **aquí y a mano**.

    La regla del estándar: cada celda va a la primera columna libre a la derecha
    del cursor de su fila, y ocupa `rowspan` x `colspan` desde ahí.
    """
    por_ancla = {
        (int(s["row"]), int(s["col"])): (int(s["rowspan"]), int(s["colspan"])) for s in spans
    }
    rejilla: Rejilla = {}
    textos: Textos = {}
    for fila, celdas in enumerate(filas):
        cursor = 0
        for texto in celdas:
            while (fila, cursor) in rejilla:
                cursor += 1
            alto, ancho = por_ancla.get((fila, cursor), (1, 1))
            for f in range(fila, fila + alto):
                for c in range(cursor, cursor + ancho):
                    rejilla[(f, c)] = CUBIERTA
            rejilla[(fila, cursor)] = ANCLA
            textos[(fila, cursor)] = normalize_cell_text(texto)
            cursor += ancho
    return rejilla, textos


def rejilla_de(t: CanonicalTable) -> tuple[Rejilla, Textos]:
    """La rejilla de una `CanonicalTable`, leída de sus celdas declaradas.

    No pasa por ningún colocador: las celdas ya traen su `row`, `col` y sus spans.
    """
    rejilla: Rejilla = {}
    textos: Textos = {}
    for c in t.cells:
        for f in range(c.row, c.row + c.rowspan):
            for col in range(c.col, c.col + c.colspan):
                rejilla[(f, col)] = CUBIERTA
        rejilla[(c.row, c.col)] = ANCLA
        textos[(c.row, c.col)] = normalize_cell_text(c.text)
    return rejilla, textos


def _posiciones(fx: dict[str, object], n_cols: int) -> list[tuple[int, int]]:
    """Las posiciones dentro del ALCANCE del fixture."""
    filas = fx["filas"]
    n_filas_ventana = len(filas) if isinstance(filas, list) else 0
    dentro = [(f, c) for f in range(n_filas_ventana) for c in range(n_cols)]
    ultima = fx.get("indice_de_la_ultima_fila")
    if isinstance(ultima, int):
        dentro += [(ultima, c) for c in range(n_cols)]
    return dentro


def comparar(fx: dict[str, object], t: CanonicalTable) -> list[Discrepancia]:
    """Una tabla contra su fixture. **Todas las diferencias, no la primera.**"""
    nombre = f"{fx['external_id']}-t{fx['tabla']}"
    fuera: list[Discrepancia] = []
    bruto_dim = fx.get("dimension")
    dim: dict[str, object] = bruto_dim if isinstance(bruto_dim, dict) else {}
    esperado = (_entero(dim, "n_rows"), _entero(dim, "n_cols"))
    if (t.n_rows, t.n_cols) != esperado:
        fuera.append(
            Discrepancia(
                nombre,
                "DIMENSION",
                f"a mano {esperado[0]}x{esperado[1]}, la verdad {t.n_rows}x{t.n_cols}",
            )
        )

    crudas = fx.get("filas")
    filas = (
        [[str(x) for x in f] for f in crudas if isinstance(f, list)]
        if isinstance(crudas, list)
        else []
    )
    brutos = fx.get("spans")
    spans = [s for s in brutos if isinstance(s, dict)] if isinstance(brutos, list) else []
    rejilla_fx, textos_fx = colocar(filas, spans)

    # La ÚLTIMA fila de un fixture con ventana se coloca APARTE, en su propio índice.
    # Rellenar las filas de en medio con celdas inventadas para llegar hasta ella
    # metería anclas falsas en la rejilla; y no hacen falta, porque en las tres
    # ventaneadas ningún span de arriba alcanza la última fila —son filas de datos.
    ultima, indice = fx.get("ultima_fila"), fx.get("indice_de_la_ultima_fila")
    if isinstance(ultima, list) and isinstance(indice, int):
        sola, textos_sola = colocar([list(map(str, ultima))], [])
        rejilla_fx |= {(indice, c): e for (f, c), e in sola.items() if f == 0}
        textos_fx |= {(indice, c): x for (f, c), x in textos_sola.items() if f == 0}

    rejilla_t, textos_t = rejilla_de(t)

    for pos in _posiciones(fx, esperado[1]):
        estado_fx = rejilla_fx.get(pos, HUECO)
        estado_t = rejilla_t.get(pos, HUECO)
        if estado_fx != estado_t:
            fuera.append(
                Discrepancia(nombre, "ESTADO", f"{pos}: a mano {estado_fx}, la verdad {estado_t}")
            )
        elif estado_fx == ANCLA and textos_fx[pos] != textos_t.get(pos, ""):
            fuera.append(
                Discrepancia(
                    nombre,
                    "TEXTO",
                    f"{pos}: a mano {textos_fx[pos]!r}, la verdad {textos_t.get(pos, '')!r}",
                )
            )
    return fuera


def _tabla_de(fx: dict[str, object]) -> tuple[CanonicalTable, bool]:
    """La tabla del documento, **y si está DENTRO de la verdad derivada**.

    Una tabla que `validate` rechaza no entra en el `Truth`, así que compararla
    contra un fixture mediría algo que ningún extractor va a puntuar. Que esté
    fuera es en sí un resultado, y por eso viaja al lado en vez de esconderse.
    """
    ident = str(fx["external_id"])
    xml = (RAIZ / "runs" / "l3" / "docs" / f"{ident}.xml").read_text(
        encoding="utf-8", errors="replace"
    )
    todas = boe_xml.tablas(xml)
    ref = DocRef(entity="boe", external_id=ident, published_on=None, url=None, kind="pdf")
    derivacion = derivar(ref, todas)
    bruto = fx["tabla"]
    indice = bruto if isinstance(bruto, int) else 0
    fuera = {i for i, _ in derivacion.descartadas}
    return todas[indice], indice not in fuera


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--detalle", action="store_true")
    partes.add_argument("--informe", action="store_true", help="escribe runs/l4/informe.json")
    args = partes.parse_args()

    fixtures = sorted((RAIZ / "runs" / "l4" / "fixtures").glob("*.json"))
    corregidos = informe_l4.corregidos(RAIZ)
    coinciden, con_discrepancia = 0, []
    todas: list[Discrepancia] = []
    filas_informe: list[dict[str, object]] = []
    for f in fixtures:
        fx = json.loads(f.read_text(encoding="utf-8"))
        tabla, en_la_verdad = _tabla_de(fx)
        ds = comparar(fx, tabla)
        if not en_la_verdad:
            ds.append(Discrepancia(f.stem, "SIN_VERDAD", "la tabla es FATAL: no entra en el Truth"))
        if ds:
            con_discrepancia.append(f.stem)
            todas += ds
        else:
            coinciden += 1
        filas_informe.append(
            informe_l4.fila(
                fx, f.stem, len(ds), sorted({d.clase for d in ds}), f.stem in corregidos
            )
        )

    print(f"\n  {coinciden} de {len(fixtures)} coinciden · {len(todas)} discrepancias")
    por_clase: dict[str, int] = {}
    for d in todas:
        por_clase[d.clase] = por_clase.get(d.clase, 0) + 1
    print(f"  por clase: {por_clase or '{}'}")
    print(f"  fixtures con alguna: {con_discrepancia or '(ninguno)'}")
    if args.detalle:
        for d in todas:
            print(f"    [{d.clase:<9}] {d.fixture}: {d.detalle}")
    cuentas = informe_l4.desglose(filas_informe)
    print(
        f"  de los {coinciden} que coinciden: {cuentas['limpias']} limpias"
        f" + {cuentas['contaminadas']} contaminada"
        f" + {cuentas['corregidas_tras_adjudicar']} corregidas"
    )
    if args.informe:
        destino = informe_l4.escribir(RAIZ, filas_informe, len(todas))
        print(f"  informe en {destino.relative_to(RAIZ)}")
    print("\n  SIN ADJUDICAR. La causa de cada una la decide una persona (ADR-0039).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
