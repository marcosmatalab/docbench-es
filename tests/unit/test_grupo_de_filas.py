"""El paso «ending a row group» del estándar, y el fallo que escondía no tenerlo.

Fichero aparte de `test_canonical_html.py` por el límite de 300 líneas, y la
partición sale sola: allí está **el conversor** y aquí **un paso concreto del
modelo de tablas** con las dos secciones donde se nota.

`cerrar_seccion` sólo resolvía los `rowspan="0"` y no avanzaba hasta `yheight`, así
que un `rowspan` de la última fila de un grupo se metía en el grupo siguiente y
**desplazaba los datos**. Con `validate` diciendo `ok=True`, que es la peor forma
de fallar que tiene este repo: una tabla bien formada con los números en la celda
equivocada. En L4 habría sido la verdad de referencia.

Los dos tests son **el mismo mutante por dos caminos**: uno mira dónde caen los
datos y el otro cuántas filas hay, sobre pares de secciones distintos.
"""

from __future__ import annotations

from docbench_es.core.canonical import from_html


def test_un_rowspan_de_la_ultima_fila_del_thead_no_se_derrama_en_el_tbody() -> None:
    """**El paso del estándar que faltaba, y el fallo que escondía.**

    El estándar termina cada grupo de filas avanzando hasta `yheight`, de modo que
    el grupo siguiente empieza DESPUÉS de lo que se derrame del anterior. Sin ese
    avance, un `<th rowspan="2">` de la última fila del `<thead>` se metía en el
    `<tbody>` y **empujaba los datos de la primera fila una columna a la derecha**,
    mientras las demás filas quedaban donde tocaba.

    Y lo peor: `validate` daba `ok=True` sobre una tabla con los números en la
    celda equivocada — que en L4 habría sido la verdad de referencia. Medido en
    `BOE-A-2026-7193`: 13x5 en vez de 14x4, y su `<colgroup>` declaraba 4.
    """
    html = (
        "<table><colgroup><col/><col/><col/><col/></colgroup>"
        '<thead><tr><th colspan="2" rowspan="2"></th><th colspan="2">Tarifa</th></tr>'
        '<tr><th rowspan="2">Fijo</th><th>Variable</th></tr></thead>'
        "<tbody><tr><td>TUR.1</td><td>bajo</td><td>3,93</td><td>3,82</td></tr>"
        "<tr><td>TUR.2</td><td>alto</td><td>8,11</td><td>3,61</td></tr></tbody></table>"
    )

    t = from_html(html)[0]

    assert t.n_cols == 4, "lo que declara su propio <colgroup>"
    fila = [t.cell_at(f, 0) for f in range(t.n_rows)]
    tur1 = next(f for f, c in enumerate(fila) if c and c.text.strip() == "TUR.1")
    tur2 = next(f for f, c in enumerate(fila) if c and c.text.strip() == "TUR.2")
    columnas = [
        [c.text.strip() for col in range(t.n_cols) if (c := t.cell_at(f, col))]
        for f in (tur1, tur2)
    ]
    assert columnas[0] == ["TUR.1", "bajo", "3,93", "3,82"]
    assert columnas[1] == ["TUR.2", "alto", "8,11", "3,61"], "alineada con TUR.1"


def test_un_rowspan_del_ultimo_tbody_tampoco_se_mete_en_el_tfoot() -> None:
    """El segundo asesino de `seccion_sin_cerrar`, con otra forma.

    El primero mira **dónde caen los datos**; éste mira **cuántas filas hay**, y
    sobre otro par de secciones. Un mutante al que mata un solo test es una
    garantía sostenida por una sola aserción: si alguien reescribe aquel test, el
    paso del estándar se puede perder sin que nada se ponga rojo.

    `<tfoot>` va después de `<tbody>` en el orden del documento, así que el
    derrame del último `<tbody>` lo empuja igual que empujaba al `<tbody>` el del
    `<thead>`.
    """
    html = (
        "<table><tbody><tr><td>a</td><td>b</td></tr>"
        '<tr><td rowspan="3">se derrama</td><td>c</td></tr></tbody>'
        "<tfoot><tr><td>total</td><td>9</td></tr></tfoot></table>"
    )

    t = from_html(html)[0]

    assert t.n_rows == 5, "2 del tbody + 2 de derrame + 1 del tfoot"
    total = next(c for c in t.cells if c.text.strip() == "total")
    assert total.row == 4, "el <tfoot> empieza DESPUÉS del derrame, no encima"
    novena = t.cell_at(4, 1)
    assert novena is not None and novena.text.strip() == "9"
