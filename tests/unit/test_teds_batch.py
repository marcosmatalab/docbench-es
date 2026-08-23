"""§12 + ADR-0006 · `teds_batch`: la cobertura evaluable y los `NO_APLICABLE`.

Aquí es donde la regla de oro 4 deja de ser una frase del README y pasa a ser
código: *«un extractor que no expresa `rowspan`/`colspan` sale `NO_APLICABLE`, no
cero, y su nota va siempre con su cobertura evaluable»*.

El límite 35 lo convirtió en requisito de L5. Esto es la mitad que se puede
construir ya: que el objeto que emite la nota **no pueda emitirla sin la
cobertura al lado**, porque las dos son campos del mismo `TedsReport`.
"""

from __future__ import annotations

import pytest
from _estrategias import tabla_completa
from hypothesis import given, settings
from hypothesis import strategies as st

from docbench_es.core.canonical import from_html
from docbench_es.core.teds import teds_batch
from docbench_es.types import CanonicalTable

CON_SPAN = '<table><tr><td colspan="2">total</td></tr><tr><td>a</td><td>b</td></tr></table>'
SIN_SPAN = "<table><tr><td>total</td><td></td></tr><tr><td>a</td><td>b</td></tr></table>"


def _plana(t: CanonicalTable) -> CanonicalTable:
    """La misma tabla declarando que su formato no puede con celdas combinadas."""
    return CanonicalTable(
        cells=tuple(c for c in t.cells if c.rowspan == 1 and c.colspan == 1),
        n_rows=t.n_rows,
        n_cols=t.n_cols,
        page_span=t.page_span,
        caption=None,
        expresses_spans=False,
        source_format="markdown",
    )


def test_el_que_no_expresa_spans_sale_no_aplicable_y_no_cero() -> None:
    """**La regla de oro 4, hecha número.**

    La verdad trae una celda combinada; el extractor devuelve Markdown, que no
    puede expresarla. Su resultado es `None`, aparece nombrado en
    `not_applicable`, y **no entra en el agregado**. Si entrara como cero, la
    media del extractor bajaría por algo que no es un fallo suyo sino un límite
    de su formato, y la comparación entre familias quedaría amañada sin querer.
    """
    gold = from_html(CON_SPAN)[0]
    informe = teds_batch([("boe/uno", _plana(gold), gold)])

    assert informe.per_document["boe/uno"] is None
    assert informe.not_applicable == ("boe/uno",)
    assert informe.aggregate is None, "sin evaluables no hay media, y NUNCA cero"
    assert informe.evaluable_coverage == 0.0


def test_la_nota_no_puede_viajar_sin_su_cobertura() -> None:
    """Demuestra que la cobertura es un campo del mismo objeto, no una nota al pie.

    Dos documentos, uno evaluable y otro no: el agregado sale sobre el evaluable
    y la cobertura dice 0,5. Quien publique `aggregate` sin mirar
    `evaluable_coverage` estará publicando una nota calculada sobre la mitad del
    corpus, que es el titular falso del límite 35.
    """
    con_span, sin_span = from_html(CON_SPAN)[0], from_html(SIN_SPAN)[0]
    informe = teds_batch([("boe/uno", _plana(con_span), con_span), ("boe/dos", sin_span, sin_span)])

    assert informe.evaluable_coverage == 0.5
    assert informe.aggregate == 1.0, "la media es del evaluable, que acertó"
    assert informe.not_applicable == ("boe/uno",)
    assert set(informe.per_document) == {"boe/uno", "boe/dos"}


def test_sin_celdas_combinadas_en_la_verdad_todos_compiten() -> None:
    """Demuestra que `NO_APLICABLE` no se reparte gratis.

    Si la verdad no trae celdas combinadas, un extractor de Markdown puede
    reproducirla entera: no hay nada que su formato no exprese, así que **sí** se
    le puntúa. Marcarlo `NO_APLICABLE` por su formato y no por el caso concreto
    le regalaría el estrato fácil.
    """
    gold = from_html(SIN_SPAN)[0]
    informe = teds_batch([("boe/tres", _plana(gold), gold)])

    assert informe.not_applicable == ()
    assert informe.evaluable_coverage == 1.0
    assert informe.per_document["boe/tres"] == 1.0


def test_un_lote_vacio_no_inventa_una_media() -> None:
    """Demuestra el caso degenerado: sin pares, no hay nota ni cobertura.

    Cero documentos es cero información. Un `aggregate` de 0,0 aquí sería un
    número inventado que además parecería un resultado malísimo.
    """
    informe = teds_batch([])
    assert informe.aggregate is None
    assert informe.evaluable_coverage == 0.0
    assert informe.per_document == {}


def test_dos_tablas_del_mismo_documento_no_se_pisan() -> None:
    """**El hallazgo del escrutinio de L2, fijado.**

    La clave es la del documento —lo dice el propio docstring de `teds_batch`—,
    así que un documento con varias tablas manda varios pares con la misma clave.
    La versión anterior guardaba `dict[clave] = nota` y **el último par borraba al
    anterior**: medido, `[("doc", mala, gold), ("doc", gold, gold)]` devolvía
    `{"doc": 1.0}` con `evaluable_coverage = 1.0`. La tabla mal extraída
    desaparecía del informe **y la cobertura afirmaba que se evaluó todo**, que es
    la regla de oro 6 rota en las dos mitades: ni se contó el fallo ni se avisó.

    Sesga hacia arriba justo en los documentos con más tablas, que son los más
    difíciles, y como la clave de documento es la unidad de remuestreo del
    bootstrap de L6, el sesgo sobreviviría al intervalo de confianza.
    """
    gold = from_html(SIN_SPAN)[0]
    mala = from_html("<table><tr><td>otra cosa</td></tr></table>")[0]
    informe = teds_batch([("boe/uno", mala, gold), ("boe/uno", gold, gold)])

    assert list(informe.per_document) == ["boe/uno"], "una entrada por documento"
    nota = informe.per_document["boe/uno"]
    assert nota is not None
    assert nota < 1.0, "la tabla mal extraída tiene que seguir pesando en la media"
    assert informe.aggregate == nota


def test_la_cobertura_se_cuenta_sobre_tablas_y_no_sobre_documentos() -> None:
    """§6: *«`evaluable_coverage`: sobre cuántas TABLAS se pudo calcular»*.

    Con una tabla por documento las dos cuentas coinciden, y por eso el fallo
    anterior era invisible. Aquí un solo documento manda dos tablas y **una no es
    evaluable**: la cobertura tiene que ser 0,5, no 1,0.

    Si se contara sobre documentos, un documento con 1 de 20 tablas evaluables
    saldría como cobertura total, que es exactamente la comparación entre
    subconjuntos distintos que prohíbe la regla de oro 4.
    """
    gold = from_html(SIN_SPAN)[0]
    con_span = from_html(CON_SPAN)[0]
    informe = teds_batch([("boe/uno", gold, gold), ("boe/uno", _plana(con_span), con_span)])

    assert informe.evaluable_coverage == 0.5
    assert informe.per_document["boe/uno"] == 1.0, "la evaluable sigue puntuando"
    assert informe.not_applicable == (), "el documento SÍ tiene una tabla evaluable"


@settings(max_examples=40)
@given(
    tablas=st.lists(tabla_completa(), min_size=1, max_size=6),
    claves=st.lists(st.sampled_from(["a", "b"]), min_size=1, max_size=6),
    aplanar=st.lists(st.booleans(), min_size=1, max_size=6),
)
def test_ninguna_tabla_se_pierde_por_el_camino(
    tablas: list[CanonicalTable], claves: list[str], aplanar: list[bool]
) -> None:
    """**La propiedad que `teds_batch` no tenía, y su familia de fallo es nueva.**

    `teds_batch` no estaba cubierto por ninguna propiedad, y la familia de fallo
    que L2 acaba de descubrir —**varias tablas con la misma clave**— no la
    generaba nada: `test_teds_batch.py` mandaba un par por clave, y con un par por
    clave todas las cuentas coinciden. Por eso el sobreescribir pasó el hito
    entero sin que nada se pusiera rojo.

    Las claves se sortean de un alfabeto de **dos**, no libres: con claves libres
    la colisión es casi imposible y la propiedad no probaría nada. Es el mismo
    razonamiento que `tabla_con_dos_filas_de_cabecera`.

    Lo que fija: **la contabilidad cierra**. Tantos documentos como claves
    distintas, y la cobertura contada sobre TABLAS. Bajo `batch_sobrescribe` la
    segunda igualdad se rompe en cuanto una clave se repite.
    """
    # Algunas predichas se aplanan: sin pares NO evaluables la cobertura sale 1,0
    # siempre y la igualdad de abajo no discrimina nada. Comprobado: sin esto, la
    # propiedad pasaba en verde contra el mutante `batch_sobrescribe`.
    pares = [
        (c, _plana(t) if ap else t, t) for c, t, ap in zip(claves, tablas, aplanar, strict=False)
    ]
    if not pares:
        return
    informe = teds_batch(pares)

    assert set(informe.per_document) == {c for c, _, _ in pares}

    def _evaluable(pred: CanonicalTable, gold: CanonicalTable) -> bool:
        combina = any(c.rowspan > 1 or c.colspan > 1 for c in gold.cells)
        return not (combina and not pred.expresses_spans)

    assert informe.evaluable_coverage * len(pares) == pytest.approx(
        sum(1 for _, p, g in pares if _evaluable(p, g))
    ), "la cobertura se cuenta sobre TABLAS, así que tiene que cerrar con el nº de pares"
