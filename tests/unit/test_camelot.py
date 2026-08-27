"""El tercer extractor: **la primera familia de §16 que no busca texto.**

`camelot` no estrena conversor —`from_dataframe` lo validó `pdfplumber`— y eso es
exactamente lo que hace esperar menos hallazgos: los tres de este hito salieron de
ESTRENAR uno. La predicción está escrita para poder fallar.

Lo que estos tests fijan y no es obvio:

* **`pages="all"` y `flavor="lattice"` se pasan explícitos**, y se comprueba por AST. El
  defecto de `read_pdf` es `pages='1'`: sin pasarlo, camelot lee la primera página y nada
  más, y la tabla diría que encuentra pocas tablas cuando sólo miró una página;
* **`pages_processed` sale de lo DECLARADO, no de lo devuelto.** camelot sólo devuelve
  páginas con tabla, así que contar sus resultados diría que un documento de 90 páginas
  tiene 2 — y ese número alimenta el coste por página;
* **un documento sin tablas NO es un fallo suyo.** Buscar tablas es su trabajo; 662 de los
  1.000 documentos no tienen ninguna, y contarlos como fallo inflaría su tasa con dos
  tercios del corpus.
"""

from __future__ import annotations

import ast
import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest

import _pdf_minimo as pdfs
from docbench_es.core.canonical import from_dataframe
from docbench_es.extract._marco import Rejilla
from docbench_es.extract.camelot import SABOR, CamelotExtractor
from docbench_es.types import FORMATOS_SIN_SPANS, DocRef, RawDoc

RUTA = Path(__file__).resolve().parents[2] / "src" / "docbench_es" / "extract" / "camelot.py"
FORMATO = "dataframe"

sin_biblioteca = pytest.mark.skipif(
    importlib.util.find_spec("camelot") is None,
    reason="camelot vive en el extra `extract-local`, que no se instala en la puerta",
)


def _doc(datos: bytes, paginas: int | None = 1) -> RawDoc:
    return RawDoc(
        ref=DocRef(entity="prueba", external_id="PDF-1", published_on=None, url=None, kind="pdf"),
        primary=datos,
        primary_mime="application/pdf",
        companions={},
        sha256="0" * 64,
        fetched_at=datetime(2026, 8, 26, tzinfo=UTC),
        n_pages=paginas,
    )


def _llamadas(nombre: str) -> list[ast.Call]:
    arbol = ast.parse(RUTA.read_text(encoding="utf-8"))
    return [
        n
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == nombre
    ]


# ─────────────────────────────── el aro del PASO 0 ───────────────────────────


def test_el_conversor_dice_lo_mismo_que_types_y_que_el_extractor() -> None:
    """Se ejercita con una `Rejilla` y no con un marco de pandas **a propósito**: el aro
    es sobre el FORMATO, y así corre en la puerta, donde no hay pandas."""
    tabla = from_dataframe([Rejilla((("a", "b"), ("c", "d")))])[0]
    assert tabla.source_format == FORMATO
    assert tabla.expresses_spans is CamelotExtractor.expresses_spans
    assert (FORMATO in FORMATOS_SIN_SPANS) is not tabla.expresses_spans


def test_expresses_spans_no_esta_tecleado_sino_derivado() -> None:
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


# ──────────────────────────────── las dos trampas ────────────────────────────


def test_read_pdf_recibe_pages_y_flavor_explicitos() -> None:
    """**La trampa que costaría el 90% de las páginas sin que nada se pusiera rojo.**

    `read_pdf` lleva `pages='1'` por defecto. Un extractor que no lo pase mira la primera
    página de cada documento y devuelve tablas de verdad, así que ni falla ni avisa: sólo
    publica un recuento bajo. Se comprueba por AST y no ejecutando, porque el síntoma de
    ejecutar es *menos tablas*, que es indistinguible de *documento con menos tablas*.
    """
    llamadas = _llamadas("read_pdf")
    assert len(llamadas) == 1, "una sola llamada, o este test mira la que no es"
    nombres = {k.arg for k in llamadas[0].keywords}
    assert {"pages", "flavor"} <= nombres, nombres


def test_el_sabor_va_en_la_version_publicada() -> None:
    """`lattice` y `stream` dan resultados distintos sobre el mismo documento. Si el sabor
    no viaja en la versión, dos corridas incomparables se publican como la misma fila."""
    assert SABOR in CamelotExtractor.version
    assert CamelotExtractor.version.count("+") == 2, CamelotExtractor.version


# ──────────────────────────── declaraciones y conducta ───────────────────────


def test_las_seis_declaraciones_dicen_lo_que_deben() -> None:
    assert CamelotExtractor.id == "camelot"
    assert CamelotExtractor.runs_locally is True
    assert CamelotExtractor.expresses_spans is False
    assert CamelotExtractor.benchcore_api.startswith("1")


def test_un_pdf_corrupto_no_lanza_y_se_cuenta_con_su_causa() -> None:
    ex = CamelotExtractor().extract(_doc(pdfs.roto()))
    assert ex.failed is True
    assert ex.failure_reason is not None
    assert ex.warnings


def test_cost_of_es_pura_y_cuadra_con_la_extraccion() -> None:
    extractor = CamelotExtractor()
    ex = extractor.extract(_doc(pdfs.roto()))
    assert extractor.cost_of(ex) == extractor.cost_of(ex) == ex.cost


# ───────────────────────────── con la biblioteca delante ─────────────────────


@sin_biblioteca
def test_saca_una_tabla_de_verdad_y_no_inventa_cabecera() -> None:
    """Las etiquetas de columna del marco de camelot son enteros posicionales, así que
    `from_dataframe` declara que no hay cabecera. Si un día dejaran de serlo, se
    inventaría **una fila de contenido en cada tabla suya** — LIMITS 36."""
    ex = CamelotExtractor().extract(_doc(pdfs.con_tabla()))
    assert ex.failed is False
    assert len(ex.tables) == 1
    tabla = ex.tables[0]
    assert [c.text for c in tabla.cells] == ["A", "B", "C", "D"]
    assert not any(c.is_header for c in tabla.cells)
    assert tabla.is_wellformed()[0], tabla.is_wellformed()[1]


@sin_biblioteca
def test_un_documento_sin_tablas_no_es_un_fallo() -> None:
    """662 de los 1.000 no tienen ninguna. Contarlos como fallo inflaría su tasa con dos
    tercios del corpus, y la tasa de fallo por extractor es un resultado publicado."""
    ex = CamelotExtractor().extract(_doc(pdfs.solo_texto()))
    assert ex.failed is False
    assert ex.tables == ()


@sin_biblioteca
def test_las_paginas_miradas_salen_de_lo_declarado_y_no_de_lo_devuelto() -> None:
    """camelot devuelve sólo páginas CON tabla. `pages_processed` alimenta el coste por
    página: contarlo de sus resultados diría que un documento de 90 páginas tiene 2."""
    ex = CamelotExtractor().extract(_doc(pdfs.solo_texto(), paginas=90))
    assert ex.pages_processed == 90
    assert ex.tables == ()
