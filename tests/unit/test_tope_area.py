"""El TOPE DE ÁREA, y por qué su número no sale del aire.

Fichero aparte por el límite de 300 líneas. `TOPE_AREA` no es endurecimiento de
seguridad: es **la precondición para que la métrica se pueda calcular**. El coste
de `comprobar` es proporcional al ÁREA de la rejilla y no al tamaño de la entrada
(límite 38), y en L5 son ocho extractores sobre mil documentos — y un extractor es
justo lo que produce spans basura.

Las dos direcciones, porque un tope es una barrera: la tabla más grande del corpus
real **pasa**, y una que se pase **sale fatal nombrando el área**.
"""

from __future__ import annotations

from docbench_es.types import CanonicalCell, CanonicalTable


def test_la_tabla_mas_grande_del_corpus_real_pasa_de_sobra() -> None:
    """**El aro en la dirección buena, y el que justifica el número del tope.**

    Sin él, un tope demasiado bajo sacaría de la verdad de referencia tablas
    legítimas, y el fallo sería invisible: menos documentos con verdad y ninguna
    señal de por qué. La mayor tabla real del corpus de L3 son **1103 x 3 = 3.309**
    posiciones (`BOE-A-2026-5518` t0), o sea **302 veces por debajo** del tope.
    """
    t = CanonicalTable(
        cells=tuple(CanonicalCell(f, c) for f in range(1103) for c in range(3)),
        n_rows=1103,
        n_cols=3,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )

    assert t.n_rows * t.n_cols == 3309
    assert t.is_wellformed()[0], "la tabla más grande del BOE tiene que pasar"


def test_una_tabla_que_se_pasa_del_tope_sale_fatal_nombrando_el_area() -> None:
    """**El tope, con su conducta declarada: fatal, no reventar ni truncar.**

    El coste de `comprobar` es proporcional al ÁREA y no al tamaño de la entrada:
    65 bytes de HTML con `rowspan="65534" colspan="1000"` declaran 65,5 M
    posiciones y cuestan ~9 GB. En L5 son ocho extractores sobre mil documentos y
    **los extractores son justo lo que produce spans basura**, así que esto no es
    endurecimiento: es la precondición para que la métrica se pueda calcular.

    Y tiene que **nombrar el área**: un fatal que no dice cuánto medía manda a
    mirar la tabla a ojo.
    """
    t = CanonicalTable(
        cells=(CanonicalCell(0, 0),),
        n_rows=65534,
        n_cols=1000,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )

    ok, problemas = t.is_wellformed()

    assert not ok
    assert len(problemas) == 1, "un defecto, un código: no se analiza nada más"
    assert problemas[0].startswith("AREA_EXCESIVA:")
    assert "65534x1000" in problemas[0] and "65,534,000" in problemas[0]
