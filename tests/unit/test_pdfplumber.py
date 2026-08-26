"""El primer extractor real, y **el aro que hoy encontró el agujero de `dataframe`**.

El primer acto de escribir un extractor no es escribir código: es preguntar **qué declara
su conversor, y si coincide con lo que dice `types`**. Esa pregunta encontró que
`"dataframe"` faltaba en `FORMATOS_SIN_SPANS` —cuatro hitos con el código y la lista
diciendo cosas distintas, apuntando a `camelot`—, así que aquí deja de ser una pregunta y
pasa a ser un test: `test_el_conversor_dice_lo_mismo_que_types_y_que_el_extractor`.

El resto se parte en dos por una razón práctica: **lo que no necesita la biblioteca corre
en la puerta** —y es casi todo, porque las declaraciones y el aro del conversor son
comprobables sin abrir un PDF— y lo que sí la necesita se salta donde no está.
`extract-local` arrastra torch y CUDA, así que en CI no está.
"""

from __future__ import annotations

import ast
import importlib.util
import io
from datetime import UTC, datetime
from pathlib import Path

import pytest

import _pdf_minimo as pdfs
from docbench_es.core.canonical import from_dataframe
from docbench_es.extract._marco import Rejilla
from docbench_es.extract.pdfplumber import FORMATO_NATIVO, PdfplumberExtractor
from docbench_es.types import FORMATOS_SIN_SPANS, DocRef, RawDoc

RUTA = Path(__file__).resolve().parents[2] / "src" / "docbench_es" / "extract" / "pdfplumber.py"

sin_biblioteca = pytest.mark.skipif(
    importlib.util.find_spec("pdfplumber") is None,
    reason="pdfplumber vive en el extra `extract-local`, que no se instala en la puerta",
)
"""La puerta NO instala `extract-local` —arrastra torch y CUDA—, así que estos se saltan
allí. Lo que NO se salta es todo lo de arriba: las declaraciones, el aro del conversor y
que un PDF corrupto se cuente. Esa es la mitad que decide si un número está bien puesto."""


def _doc(datos: bytes, ident: str = "PDF-1") -> RawDoc:
    return RawDoc(
        ref=DocRef(entity="prueba", external_id=ident, published_on=None, url=None, kind="pdf"),
        primary=datos,
        primary_mime="application/pdf",
        companions={},
        sha256="0" * 64,
        fetched_at=datetime(2026, 8, 26, tzinfo=UTC),
        n_pages=1,
    )


# ─────────────────────────────── el aro del conversor ───────────────────────────────


def test_el_conversor_dice_lo_mismo_que_types_y_que_el_extractor() -> None:
    """**El aro que hay que pasar al escribir CADA extractor.** Tres afirmaciones, una vez.

    Se ejecuta el conversor —no se lee su docstring, no se consulta una lista— y se exige
    que lo que sale coincida con `types` y con lo que el extractor declara de sí. Si las
    tres no cuadran, hay un extractor que puede cobrar un cero donde le tocaba
    `NO_APLICABLE`, que es la comparación amañada sin querer de la regla de oro 4.
    """
    salida = from_dataframe([Rejilla((("a", "b"), ("c", "d")))])
    assert len(salida) == 1
    tabla = salida[0]
    assert tabla.source_format == FORMATO_NATIVO, "el conversor devuelve otro formato"
    assert tabla.expresses_spans is PdfplumberExtractor.expresses_spans
    assert (FORMATO_NATIVO in FORMATOS_SIN_SPANS) is not tabla.expresses_spans
    assert tabla.is_wellformed()[0]


def test_expresses_spans_no_esta_tecleado_sino_derivado() -> None:
    """Lo que hace que copiar este fichero para el siguiente extractor sea seguro.

    Con `expresses_spans = False` escrito a mano, quien copie y cambie el formato se lleva
    la declaración del anterior. Derivándolo de `expresa_spans(FORMATO_NATIVO)`, o coincide
    o no arranca. Se comprueba por AST porque el VALOR sería el mismo de las dos formas:
    lo que distingue una de otra es cómo llegó ahí.
    """
    arbol = ast.parse(RUTA.read_text(encoding="utf-8"))
    clases = [n for n in ast.walk(arbol) if isinstance(n, ast.ClassDef)]
    asignaciones = [
        n
        for c in clases
        for n in c.body
        if isinstance(n, ast.Assign)
        and any(getattr(t, "id", "") == "expresses_spans" for t in n.targets)
    ]
    assert len(asignaciones) == 1, "debería asignarse exactamente una vez"
    assert isinstance(asignaciones[0].value, ast.Call), (
        "expresses_spans está tecleado como constante. Lo fija el conversor, no el "
        "extractor: tiene que salir de una llamada a `expresa_spans`"
    )


# ─────────────────────────── las declaraciones, sin biblioteca ───────────────────────


def test_las_seis_declaraciones_son_de_clase_y_dicen_lo_que_deben() -> None:
    """`kind` es `parser` y no una familia de §16: son dos taxonomías distintas."""
    assert PdfplumberExtractor.id == "pdfplumber"
    assert PdfplumberExtractor.kind == "parser"
    assert PdfplumberExtractor.runs_locally is True
    assert PdfplumberExtractor.expresses_spans is False
    assert PdfplumberExtractor.benchcore_api.startswith("1")


def test_la_version_lleva_la_de_la_biblioteca_y_la_del_adaptador() -> None:
    """Sin la segunda, cambiar los ajustes de detección movería la tabla de resultados
    sin mover ninguna versión publicada, y el número dejaría de ser atribuible."""
    version = PdfplumberExtractor.version
    assert "+ad" in version, version
    biblioteca, _, adaptador = version.partition("+ad")
    assert biblioteca and adaptador.isdigit(), version


def test_cost_of_es_pura_y_cuadra_con_lo_que_la_extraccion_ya_traia() -> None:
    """Dos llamadas dan lo mismo, **y lo mismo que `ex.cost`**: si difirieran, el coste
    por éxito dependería de a quién se le pregunta."""
    doc = _doc(pdfs.roto())
    ex = PdfplumberExtractor().extract(doc)
    extractor = PdfplumberExtractor()
    assert extractor.cost_of(ex) == extractor.cost_of(ex)
    assert extractor.cost_of(ex) == ex.cost
    assert extractor.cost_of(ex).measured is True, "un extractor local NO gasta, y es un hecho"


def test_un_pdf_corrupto_no_lanza_y_se_cuenta_con_su_causa() -> None:
    """**El aro que más veces se cae**, y el que sostiene la tasa de fallo por extractor.

    No necesita la biblioteca instalada: sin ella el fallo es `provider_error`, con ella es
    `corrupt_pdf`. Los dos son del enum cerrado y los dos se cuentan, que es lo que se
    afirma aquí. Cuál de los dos sale lo comprueba el test de abajo, con la biblioteca.
    """
    ex = PdfplumberExtractor().extract(_doc(pdfs.roto()))
    assert ex.failed is True
    assert ex.failure_reason is not None
    assert ex.warnings, "un fallo sin detalle es un error a medio tragar"
    assert ex.extractor_id == "pdfplumber"


def test_un_page_range_invalido_no_lanza_pero_queda_declarado_en_limits() -> None:
    """LIMITS 99: un error del arnés entra en la tasa de fallo del extractor.

    Se comprueba la conducta —no lanza, se cuenta— y se deja dicho que la causa es del
    llamador. La campaña de los 616 no pasa rango, así que hoy no contamina nada.
    """
    ex = PdfplumberExtractor().extract(_doc(pdfs.solo_texto()), page_range=(0, 5))
    assert ex.failed is True
    assert ex.failure_reason == "provider_error"
    assert "page_range" in ex.warnings[0]


# ───────────────────────────── con la biblioteca delante ─────────────────────────────


@sin_biblioteca
def test_saca_el_texto_de_una_pagina_de_verdad() -> None:
    ex = PdfplumberExtractor().extract(_doc(pdfs.solo_texto()))
    assert ex.failed is False
    assert "HOLA MUNDO" in ex.text
    assert ex.pages_processed == 1
    assert ex.native_format == FORMATO_NATIVO
    assert ex.tables == (), "sin líneas dibujadas no hay tabla que detectar"


@sin_biblioteca
def test_una_tabla_de_verdad_sale_canonica_y_bien_formada() -> None:
    """El camino entero: rejilla de la biblioteca → `Rejilla` → `from_dataframe` → tabla."""
    ex = PdfplumberExtractor().extract(_doc(pdfs.con_tabla()))
    assert ex.failed is False
    assert len(ex.tables) == 1
    tabla = ex.tables[0]
    assert (tabla.n_rows, tabla.n_cols) == (2, 2)
    assert [c.text for c in tabla.cells] == ["A", "B", "C", "D"]
    assert tabla.is_wellformed()[0], tabla.is_wellformed()[1]
    assert not any(c.is_header for c in tabla.cells), "pdfplumber no dice cuál es la cabecera"
    assert tabla.page_span == (1, 1)


@sin_biblioteca
def test_un_pdf_corrupto_sale_como_corrupto_y_no_como_error_de_proveedor() -> None:
    """Con la biblioteca delante, la causa es la fina. Es lo que hace que la tabla de
    fallos por causa signifique algo y no sea una columna de `provider_error`."""
    ex = PdfplumberExtractor().extract(_doc(pdfs.roto()))
    assert ex.failure_reason == "corrupt_pdf", ex.warnings


@sin_biblioteca
def test_un_pdf_sin_capa_de_texto_no_es_un_exito_vacio() -> None:
    """Un extractor que devuelve cero tablas y cero texto **sin declararlo** desaparece de
    la tasa de fallo y aparece como un documento sin tablas. Son cosas distintas."""
    vacio = pdfs.solo_texto(b" ")
    ex = PdfplumberExtractor().extract(_doc(vacio))
    assert ex.failed is True
    assert ex.failure_reason == "no_text_layer"


@sin_biblioteca
def test_el_rango_de_paginas_es_medio_abierto_y_en_base_1() -> None:
    import pdfplumber as biblioteca

    with biblioteca.open(io.BytesIO(pdfs.con_tabla())) as d:
        assert len(d.pages) == 1
    ex = PdfplumberExtractor().extract(_doc(pdfs.con_tabla()), page_range=(1, 2))
    assert ex.pages_processed == 1, "de la 1 a la 2 sin incluirla es una página"
