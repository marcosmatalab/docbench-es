"""Que el XML oficial del BOE llega a forma canónica **sin un parseador nuevo**.

Lo que este fichero demuestra no es que `from_html` funcione —eso lo demostró L2
contra PubTabNet— sino que **el XML del BOE se le puede dar tal cual**, que es lo
que permite que la verdad sea `DERIVED` sin escribir un extractor propio (regla de
oro 1).

Y una barrera pequeña con su control negativo: **sólo cuentan los spans mayores
que 1**. Un `colspan="1"` no combina nada, y contarlo inflaría la cifra sobre la
que se apoya media justificación del proyecto — «el 63% de los documentos con
tabla traen celdas combinadas» diría otra cosa.
"""

from __future__ import annotations

from _boe_falso import XML_CON_TABLA, XML_SIN_TABLA

from docbench_es.entity.boe_xml import estratos, rasgos, tablas, texto_plano

XML_SPAN_UNO = '<doc><table><tr><td colspan="1">sola</td></tr></table></doc>'
XML_CON_IMAGEN = '<doc><p>Anexo</p><img src="grafico.png"/></doc>'


def test_el_xml_del_boe_se_le_pasa_entero_a_from_html() -> None:
    """La tabla sale en forma canónica, con su `rowspan` respetado.

    Se le pasa el documento **entero**, sin recortar las `<table>` con un regex
    primero: recortar es normalizar, toda normalización se documenta, y aquí no
    compraría nada — `from_html` ya ignora lo que no es tabla — mientras que sí
    metería un paso propio capaz de perder una tabla sin que nadie se entere.
    """
    canonicas = tablas(XML_CON_TABLA)

    assert len(canonicas) == 1
    assert canonicas[0].n_rows == 3 and canonicas[0].n_cols == 2
    assert any(c.rowspan == 2 for c in canonicas[0].cells), "el rowspan del XML llega entero"


def test_un_documento_sin_tablas_da_cero_tablas() -> None:
    """Cero tablas es una respuesta, no un fallo: es lo que mide «tablas no detectadas»."""
    assert tablas(XML_SIN_TABLA) == []


def test_el_texto_plano_no_pega_palabras_al_quitar_las_etiquetas() -> None:
    """Cada etiqueta se sustituye por un ESPACIO, no se borra.

    Sin el espacio, `<p>uno</p><p>dos</p>` daría `unodos` — una palabra que no
    existe en ninguno de los dos documentos— y la similitud contra el PDF bajaría
    por un motivo inventado aquí. Sería descartar pares buenos por un bug de
    normalización, que es lo que la regla de oro 7 persigue.
    """
    plano = texto_plano("<p>uno</p><p>dos</p>")

    assert plano.split() == ["uno", "dos"]


def test_solo_cuentan_los_spans_mayores_que_uno() -> None:
    """**El control negativo del recuento de spans.**

    Un `colspan="1"` es sintácticamente un span y semánticamente nada. Si contara,
    `celdas-combinadas` se comería a `tabla-simple` y la cifra que sostiene medio
    proyecto —cuántos documentos traen celdas combinadas— sería otra.
    """
    con_span_uno = rasgos(XML_SPAN_UNO)
    con_span_real = rasgos(XML_CON_TABLA)

    assert con_span_uno.n_colspan == 0 and con_span_uno.max_span == 0
    assert con_span_real.n_rowspan == 1 and con_span_real.max_span == 2


def test_los_cuatro_estratos_que_salen_del_xml_y_los_dos_que_no() -> None:
    """§9.4 · Lo que se puede decidir sin extractor y sin páginas.

    Los cuatro de tabla salen. `escaneado` y `multipagina` **no se emiten**: el
    primero es una propiedad de la capa de texto del PDF y el segundo exige saber
    si una tabla cruza una página, y el XML del BOE no tiene páginas. No se
    aproximan — un `multipagina` estimado envenenaría el estrato entero.
    """
    assert estratos(rasgos(XML_CON_TABLA)) == frozenset({"celdas-combinadas"})
    assert estratos(rasgos(XML_SPAN_UNO)) == frozenset({"tabla-simple"})
    assert estratos(rasgos(XML_SIN_TABLA)) == frozenset({"sin-tabla"})
    assert estratos(rasgos(XML_CON_IMAGEN)) == frozenset({"anexo-png"})

    todos = frozenset().union(
        *(estratos(rasgos(x)) for x in (XML_CON_TABLA, XML_SPAN_UNO, XML_SIN_TABLA))
    )
    assert "escaneado" not in todos and "multipagina" not in todos


def test_el_estrato_es_uno_solo_y_no_dos() -> None:
    """Las categorías son excluyentes por diseño, y la ponderación de §12 lo exige.

    Un documento con celdas combinadas ya no es `tabla-simple`. Emitir los dos
    repartiría el mismo documento en dos casillas y la ponderación por estrato
    sumaría más del 100%.
    """
    for xml in (XML_CON_TABLA, XML_SPAN_UNO, XML_SIN_TABLA, XML_CON_IMAGEN):
        assert len(estratos(rasgos(xml))) == 1
