"""El cuarto extractor: **el único que declara `expresses_spans=True`.**

Y por eso el que más daño haría mintiendo: si declarase capaz y su camino de conversión
perdiera los `rowspan`, entraría en el estrato de celdas combinadas —el que se
sobremuestrea y se declara titular— cobrando ceros **como si hubiera competido**, y encima
siendo el 63% del presupuesto de la campaña. Es la clase exacta del agujero de `camelot`.

Se comprobó **antes de escribir una línea**, sobre `BOE-A-2026-7446`, cuya verdad congelada
declara 3x8 con **siete** combinadas: docling devuelve 3x8 y siete, y su HTML trae
`rowspan="2"` y `colspan="2"`. Está en `runs/l5/formatos.yaml`.

## Aquí NO hay tests de conducta, y la razón es el reloj

Cualquier llamada a `extract()` importa `torch` y construye un `DocumentConverter`, que
carga modelos: **decenas de segundos** contra un techo de puerta de 8 500 ms. Su conducta
—que `extract` no lanza ante un PDF corrupto, que las tablas salen bien formadas, que el
coste es puro— la cubre `tests/contract/test_extractor_contract.py`, que corre la suite de
conformidad sobre **todos** los extractores registrados y vive en `make full`.

Lo que sí corre en la puerta es lo que decide si un número está bien puesto: las
declaraciones, el aro del conversor y que los hilos viajen en la versión.
"""

from __future__ import annotations

import ast
from pathlib import Path

from docbench_es.core.canonical import from_html
from docbench_es.extract.docling import HILOS, DoclingExtractor
from docbench_es.types import FORMATOS_CON_SPANS

RUTA = Path(__file__).resolve().parents[2] / "src" / "docbench_es" / "extract" / "docling.py"
FORMATO = "html"

CON_SPANS = (
    '<table><tr><th rowspan="2">Número</th><th colspan="2">Período</th></tr>'
    "<tr><td>Trimestre</td><td>Año</td></tr></table>"
)


def test_el_conversor_dice_lo_mismo_que_types_y_que_el_extractor() -> None:
    """**El aro del PASO 0, y aquí en la dirección contraria a los otros tres**: lo que se
    exige es que el formato SÍ permita spans y que el extractor lo declare."""
    tabla = from_html(CON_SPANS)[0]
    assert tabla.source_format == FORMATO
    assert tabla.expresses_spans is DoclingExtractor.expresses_spans is True
    assert FORMATO in FORMATOS_CON_SPANS


def test_el_conversor_conserva_los_spans_de_verdad() -> None:
    """Que el formato los permita no basta: el conversor tiene que sacarlos. Si esto se
    rompe, docling declara capaz y entrega tablas planas — el escenario de `camelot`."""
    tabla = from_html(CON_SPANS)[0]
    combinadas = [(c.rowspan, c.colspan) for c in tabla.cells if c.rowspan > 1 or c.colspan > 1]
    assert sorted(combinadas) == [(1, 2), (2, 1)], combinadas
    assert tabla.is_wellformed()[0], tabla.is_wellformed()[1]


def test_expresses_spans_no_esta_tecleado_sino_derivado() -> None:
    """Vale igual para el que declara `True`: si mañana su formato cambia a markdown, la
    declaración cambia sola en vez de quedarse mintiendo."""
    arbol = ast.parse(RUTA.read_text(encoding="utf-8"))
    asignaciones = [
        n
        for c in ast.walk(arbol)
        if isinstance(c, ast.ClassDef)
        for n in c.body
        if isinstance(n, ast.Assign)
        and any(getattr(t, "id", "") == "expresses_spans" for t in n.targets)
    ]
    assert len(asignaciones) == 1
    assert isinstance(asignaciones[0].value, ast.Call)


def test_los_hilos_viajan_en_la_version_publicada() -> None:
    """El experimento A midió que subirlos cuesta entre 4 y 12 veces la CPU para el mismo
    reloj o peor (LIMITS 89), y el presupuesto de 2,53 h está medido con dos. Dos corridas
    con hilos distintos no son la misma fila."""
    assert f"+{HILOS}h" in DoclingExtractor.version, DoclingExtractor.version
    assert HILOS == 2


def test_las_variables_de_entorno_se_ponen_al_importar_el_modulo() -> None:
    """**Al importar, no al extraer.** OpenMP y BLAS las leen cuando `torch` se carga, y
    ponerlas después no tiene efecto: medido en B5-bis, `hilos_efectivos` salía 4,2 con el
    entorno pidiendo 2. Se comprueba por AST porque el efecto sólo se ve con torch dentro.
    """
    arbol = ast.parse(RUTA.read_text(encoding="utf-8"))
    en_modulo = [n for n in arbol.body if isinstance(n, ast.For)]
    assert en_modulo, "el bucle que fija el entorno tiene que estar en el nivel del módulo"
    fuente = ast.unparse(en_modulo[0])
    assert "environ" in fuente and "OMP_NUM_THREADS" in fuente, fuente


def test_las_seis_declaraciones_dicen_lo_que_deben() -> None:
    """`kind='hibrido'` es la taxonomía de §7.2 —cómo se ejecuta—, no la de §16, que lo
    llama *document-AI*. Son dos taxonomías con nombres parecidos sobre los mismos ocho
    objetos, y confundirlas haría que la tabla de cobertura de familias contara mal."""
    assert DoclingExtractor.id == "docling"
    assert DoclingExtractor.kind == "hibrido"
    assert DoclingExtractor.runs_locally is True
    assert DoclingExtractor.expresses_spans is True
    assert DoclingExtractor.benchcore_api.startswith("1")


def test_no_hay_ninguna_llamada_a_extract_en_este_fichero() -> None:
    """**El guardián de esta decisión.** Un `extract()` aquí importaría torch y cargaría
    modelos: decenas de segundos contra un techo de 8 500 ms. Si alguien añade uno, la
    puerta se pone lenta y nadie sabría por qué — así que se pone rojo aquí primero.
    """
    arbol = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    llamadas = [
        n.func.attr
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    ]
    assert "extract" not in llamadas
    assert "probe" not in llamadas, "probe también importa docling"
