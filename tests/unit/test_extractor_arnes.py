"""El arnés que comparten los ocho extractores: la rejilla y la salida.

`_marco.Rejilla` y `_salida` existen para que un extractor sea de verdad un envoltorio
fino. Y por eso mismo un fallo aquí **sale multiplicado por ocho** y en columnas que se
publican: la causa del fallo, la latencia y el coste.

Los dos casos que estos tests sostienen, y que se descubrieron ejecutando:

* **el envoltorio de la biblioteca**: `pdfplumber` mete todo lo de `pdfminer` dentro de un
  `PdfminerException` propio, así que sin desenvolver, la tabla de fallo por causa habría
  tenido una sola columna — `provider_error` — con el enum cerrado funcionando;
* **la cabecera inventada**: si `Rejilla.columns` devolviera nombres en vez de posiciones,
  `from_dataframe` emitiría una fila de cabecera **en cada tabla** de cada extractor de
  rejilla, y una fila de contenido marcada como cabecera cambia el árbol que puntúa TEDS.
"""

from __future__ import annotations

import time
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from docbench_es.core.canonical import from_dataframe
from docbench_es.extract._marco import Rejilla
from docbench_es.extract._salida import causa_de, coste, extraccion
from docbench_es.extract.base import FamiliaExtractor
from docbench_es.types import DocRef, RawDoc


class _Extractor:
    """Lo mínimo que `extraccion` necesita: quién es y qué versión."""

    id = "de-prueba"
    version = "9.9+ad0"
    kind: FamiliaExtractor = "parser"
    runs_locally = True
    expresses_spans = False
    benchcore_api = "1.x"


def _doc() -> RawDoc:
    return RawDoc(
        ref=DocRef(entity="x", external_id="D-1", published_on=None, url=None, kind="pdf"),
        primary=b"%PDF-1.4\n",
        primary_mime="application/pdf",
        companions={},
        sha256="0" * 64,
        fetched_at=datetime(2026, 8, 26, tzinfo=UTC),
        n_pages=1,
    )


# ───────────────────────────────── la rejilla ─────────────────────────────────


def test_la_rejilla_no_inventa_una_cabecera() -> None:
    """`columns` son posiciones, así que `from_dataframe` declara que no hay cabecera.

    Con nombres, la primera fila de datos de CADA tabla se marcaría como cabecera.
    """
    tabla = from_dataframe([Rejilla((("uno", "dos"), ("3", "4")))])[0]
    assert (tabla.n_rows, tabla.n_cols) == (2, 2)
    assert [c.text for c in tabla.cells] == ["uno", "dos", "3", "4"]
    assert not any(c.is_header for c in tabla.cells)


def test_una_celda_none_es_celda_vacia_y_no_un_hueco() -> None:
    """Son árboles distintos y TEDS los puntúa distinto. La decisión es del conversor."""
    tabla = from_dataframe([Rejilla((("a", None), ("c", "d")))])[0]
    assert [c.text for c in tabla.cells] == ["a", "", "c", "d"]
    assert tabla.is_wellformed()[0]


def test_una_fila_corta_no_invalida_la_tabla_pero_se_declara() -> None:
    """`HUECO_COLA` es informativo: una fila corta es cotidiana en el BOE. Lo que no puede
    es desaparecer, porque entonces nadie sabe que la rejilla venía torcida."""
    tabla = from_dataframe([Rejilla((("a", "b", "c"), ("d",)))])[0]
    ok, problemas = tabla.is_wellformed()
    assert ok is True
    assert any(p.startswith("HUECO_COLA") for p in problemas), problemas


def test_itertuples_respeta_index_como_lo_hace_pandas() -> None:
    """Un doble que ignorara el argumento devolvería una columna de menos en silencio el
    día que alguien lo llame sin él."""
    rejilla = Rejilla((("a", "b"), ("c", "d")))
    assert list(rejilla.itertuples(index=False)) == [("a", "b"), ("c", "d")]
    assert list(rejilla.itertuples()) == [(0, "a", "b"), (1, "c", "d")]
    assert list(rejilla.columns) == [0, 1]


def test_una_rejilla_vacia_no_revienta() -> None:
    assert list(Rejilla(()).columns) == []


# ─────────────────────────────── la causa del fallo ───────────────────────────


class _Envoltorio(Exception):
    """Lo que hace `pdfplumber`: `raise PdfminerException(e)`, con `e` dentro."""


def test_una_excepcion_de_la_tabla_da_su_causa() -> None:
    assert causa_de(MemoryError("sin sitio")) == "out_of_memory"


def test_una_excepcion_desconocida_no_desaparece_sino_que_sale_de_proveedor() -> None:
    """Lo desconocido se cuenta, con su tipo y su mensaje. Regla de oro 6."""
    assert causa_de(ValueError("vete a saber")) == "provider_error"


def test_una_causa_envuelta_por_la_biblioteca_se_encuentra_igual() -> None:
    """**El caso real.** Sin desenvolver, esto salía `provider_error` y la columna
    `corrupt_pdf` de la tabla de fallo por causa se quedaba a cero para siempre."""

    class PDFSyntaxError(Exception):  # el NOMBRE es lo que mira la tabla, no la ruta
        pass

    try:
        try:
            raise PDFSyntaxError("No /Root object!")
        except PDFSyntaxError as dentro:
            raise _Envoltorio(dentro) from None
    except _Envoltorio as fuera:
        assert causa_de(fuera) == "corrupt_pdf"


def test_el_control_negativo_del_desenvolver_no_inventa_causas() -> None:
    """Un envoltorio **sin nada dentro** sigue siendo desconocido. Si esto diera
    `corrupt_pdf`, el desenvolver estaría fabricando causas en vez de encontrarlas."""
    assert causa_de(_Envoltorio("vacío")) == "provider_error"


def test_desenvolver_no_se_cuelga_con_un_ciclo() -> None:
    """Dos excepciones que se referencian mutuamente no pueden colgar una campaña."""
    a, b = _Envoltorio("a"), _Envoltorio("b")
    a.__context__, b.__context__ = b, a
    assert causa_de(a) == "provider_error"


# ─────────────────────────────────── la salida ────────────────────────────────


def test_un_fallo_se_cuenta_con_su_latencia_y_su_coste() -> None:
    """Los segundos que costó descubrir que no se podía leer **se gastaron igual**.

    Descontarlos abarataría precisamente al extractor que más se cae, que es el incentivo
    exactamente al revés.
    """
    arranque = time.perf_counter() - 0.05
    ex = extraccion(_Extractor(), _doc(), arranque, "dataframe", causa="corrupt_pdf", detalle="x")
    assert ex.failed is True
    assert ex.failure_reason == "corrupt_pdf"
    assert ex.latency_ms >= 50, ex.latency_ms
    assert ex.cost.wall_ms == ex.latency_ms
    assert ex.warnings == ("x",)


def test_la_extraccion_no_puede_decir_ser_de_otro() -> None:
    """`extractor` entra entero y no como `(id, version)` sueltos: el aro
    `identificacion` de la conformidad, cumplido por construcción."""
    ex = extraccion(_Extractor(), _doc(), time.perf_counter(), "dataframe")
    assert (ex.extractor_id, ex.extractor_version) == (_Extractor.id, _Extractor.version)
    assert ex.failed is False
    assert ex.failure_reason is None


def test_el_coste_de_un_extractor_local_es_cero_medido_y_no_desconocido() -> None:
    """`Cost.unknown()` diría que no se sabe, y un informe que sume un desconocido como si
    fuera cero publica un total más barato que la realidad."""
    c = coste(37)
    assert c.measured is True
    assert c.estimated is False
    assert c.eur == 0
    assert c.wall_ms == 37


def test_un_fallo_sin_causa_sigue_sin_poder_construirse_desde_el_arnes() -> None:
    """Lo ata `Extraction.__post_init__`, y aquí se comprueba que el arnés no lo sortea.

    Un documento caído **sin causa** no puede aparecer en la tabla de fallo por causa, o
    sea que desaparece del informe: el error tragado de la regla de oro 6, en el modelo de
    datos en vez de en un `except`.
    """
    buena = extraccion(_Extractor(), _doc(), time.perf_counter(), "dataframe")
    with pytest.raises(ValueError, match="failure_reason"):
        replace(buena, failed=True)
    with pytest.raises(ValueError, match="failure_reason"):
        replace(buena, failure_reason="timeout")
