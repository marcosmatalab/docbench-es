"""El segundo extractor real, y **el primer consumidor de `from_markdown`**.

La sección «Construido y NO VALIDADO» de `ESTADO.md` predice que el hito que CONSUME un
módulo encuentra bugs que el que lo ESCRIBE no encuentra. Van tres de tres: `from_html`
en L2, `from_dataframe` con `pdfplumber`, y aquí `from_markdown` — que deja **el marcado
de Markdown dentro del texto de la celda**, medido en 116 de 594 celdas (LIMITS 103).

Lo que estos tests fijan, y ninguno necesita la biblioteca:

* **el aro del PASO 0**: lo que declara `from_markdown` coincide con `types` y con lo que
  el extractor declara de sí;
* **que `expresses_spans` está derivado y no tecleado**, por AST;
* **que el marcado llega al texto**, que es un límite declarado y no una conducta
  deseada: el día que se cierre LIMITS 103 este test se cae, y tiene que caerse.

Lo que sí necesita la biblioteca se salta con su razón dicha: `extract-local` arrastra
torch y CUDA y no se instala en la puerta.
"""

from __future__ import annotations

import ast
import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest

import _pdf_minimo as pdfs
from docbench_es.core.canonical import from_markdown
from docbench_es.extract.pymupdf4llm import FORMATO_NATIVO, Pymupdf4llmExtractor
from docbench_es.types import FORMATOS_SIN_SPANS, DocRef, RawDoc

RUTA = Path(__file__).resolve().parents[2] / "src" / "docbench_es" / "extract" / "pymupdf4llm.py"

sin_biblioteca = pytest.mark.skipif(
    importlib.util.find_spec("pymupdf4llm") is None,
    reason="pymupdf4llm vive en el extra `extract-local`, que no se instala en la puerta",
)

TABLA_GFM = """
|**Número**|**Hito/**<br>**Objetivo**|
|---|---|
|242|C15.I5|
"""
"""La cabecera real de `BOE-A-2026-7446` tal como la emite `pymupdf4llm`, copiada de la
corrida. La verdad congelada de L4 dice `Número` y `Hito/ Objetivo`."""


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


# ─────────────────────────────── el aro del PASO 0 ───────────────────────────


def test_el_conversor_dice_lo_mismo_que_types_y_que_el_extractor() -> None:
    """El primer acto de escribir un extractor, hecho test. Tres afirmaciones, una vez."""
    salida = from_markdown(TABLA_GFM)
    assert len(salida) == 1
    tabla = salida[0]
    assert tabla.source_format == FORMATO_NATIVO
    assert tabla.expresses_spans is Pymupdf4llmExtractor.expresses_spans
    assert (FORMATO_NATIVO in FORMATOS_SIN_SPANS) is not tabla.expresses_spans
    assert tabla.is_wellformed()[0]


def test_expresses_spans_no_esta_tecleado_sino_derivado() -> None:
    """Lo que hace seguro copiar este fichero para el siguiente extractor: o el formato y
    la declaración coinciden, o no arranca."""
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
    assert isinstance(asignaciones[0].value, ast.Call), "lo fija el conversor, no el extractor"


def test_el_marcado_de_markdown_ya_no_llega_al_texto_de_la_celda() -> None:
    """**LIMITS 103, cerrado — y este test es lo que queda de él.**

    Llegaban **116 de 594 celdas (19,5%)** con marcado dentro sobre los cinco documentos
    de conformidad: 86 con `**`, 54 con `<br>`. Era una asimetría entre conversores del
    mismo repo —`from_html` lee el TEXTO del nodo y `from_markdown` leía la fuente—, o
    sea un sesgo sistemático **entre familias**: quien emitía HTML cobraba texto limpio
    gratis y quien emitía Markdown cobraba un cero por el formato de su salida.

    Se comprueba contra las cadenas EXACTAS de la verdad congelada de L4, no contra una
    forma inventada aquí: `Número` y `Hito/ Objetivo`.
    """
    textos = [c.text for c in from_markdown(TABLA_GFM)[0].cells]
    assert textos[:2] == ["Número", "Hito/ Objetivo"], textos
    assert not any("**" in t or "<br>" in t for t in textos), textos


def test_las_seis_declaraciones_dicen_lo_que_deben() -> None:
    assert Pymupdf4llmExtractor.id == "pymupdf4llm"
    assert Pymupdf4llmExtractor.kind == "parser"
    assert Pymupdf4llmExtractor.runs_locally is True
    assert Pymupdf4llmExtractor.expresses_spans is False
    assert "+ad" in Pymupdf4llmExtractor.version


def test_un_pdf_corrupto_no_lanza_y_se_cuenta_con_su_causa() -> None:
    """Con o sin biblioteca, la extracción sale fallida y con causa del enum cerrado."""
    ex = Pymupdf4llmExtractor().extract(_doc(pdfs.roto()))
    assert ex.failed is True
    assert ex.failure_reason is not None
    assert ex.warnings
    assert ex.extractor_id == "pymupdf4llm"


def test_cost_of_es_pura_y_cuadra_con_la_extraccion() -> None:
    extractor = Pymupdf4llmExtractor()
    ex = extractor.extract(_doc(pdfs.roto()))
    assert extractor.cost_of(ex) == extractor.cost_of(ex) == ex.cost
    assert extractor.cost_of(ex).measured is True


# ───────────────────────────── con la biblioteca delante ─────────────────────


@sin_biblioteca
def test_saca_el_texto_de_una_pagina_de_verdad() -> None:
    ex = Pymupdf4llmExtractor().extract(_doc(pdfs.solo_texto()))
    assert ex.failed is False
    assert "HOLA MUNDO" in ex.text
    assert ex.pages_processed == 1
    assert ex.native_format == FORMATO_NATIVO


@sin_biblioteca
def test_un_pdf_corrupto_sale_como_corrupto_y_no_como_error_de_proveedor() -> None:
    """`pymupdf` envuelve los errores de MuPDF en `FileDataError`, que la tabla compartida
    de `_salida` traduce. Sin esa entrada, la fila `corrupt_pdf` se quedaría a cero."""
    ex = Pymupdf4llmExtractor().extract(_doc(pdfs.roto()))
    assert ex.failure_reason == "corrupt_pdf", ex.warnings


@sin_biblioteca
def test_ninguna_tabla_suya_expresa_spans_pase_lo_que_pase() -> None:
    """Es lo que gobierna que su TEDS salga `NO_APLICABLE` y no cero. Regla de oro 4."""
    ex = Pymupdf4llmExtractor().extract(_doc(pdfs.con_tabla()))
    assert ex.failed is False
    assert all(not t.expresses_spans for t in ex.tables)
    assert all(c.rowspan == 1 and c.colspan == 1 for t in ex.tables for c in t.cells)
