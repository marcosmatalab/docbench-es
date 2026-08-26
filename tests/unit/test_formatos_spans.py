"""Las dos listas de formatos dicen lo que los conversores hacen. Se comprueba.

Va aparte de `test_canonical_conversores.py` porque no prueba un conversor: prueba **el
acuerdo entre `types.FORMATOS_CON_SPANS` y los cinco conversores**. Y porque aquel
fichero se pasó de 300 líneas al meterlo.

## La clase de fallo que cierra

`expresses_spans` lo fija el conversor según el formato de origen, así que las dos listas
de `types` son **una copia de lo que hace el código**. Una copia se queda vieja, y ésta
se quedó vieja **durante cuatro hitos**: `_dataframe.py` pone `expresses_spans=False` en
su primera línea y explica por qué, pero `dataframe` no estaba en `FORMATOS_SIN_SPANS`.

Consecuencia medida: una `CanonicalTable` con `source_format="dataframe"` podía declarar
`expresses_spans=True` y `is_wellformed()` la daba por buena. Y `camelot`, que devuelve
marcos, está entre los cuatro extractores de la campaña de los 616 — habría competido en
el estrato de celdas combinadas cobrando ceros en vez de salir `NO_APLICABLE`, que es
justo el sesgo que `expresses_spans` existe para impedir.

Lo delató escribir el primer extractor y preguntarse qué formato devuelve `pdfplumber`.
"""

from __future__ import annotations

from docbench_es.core.canonical import (
    from_dataframe,
    from_html,
    from_markdown,
    from_tei,
    from_text_heuristic,
)
from docbench_es.types import FORMATOS_CANONICOS, FORMATOS_CON_SPANS, FORMATOS_SIN_SPANS


def test_los_cinco_conversores_cuadran_con_las_listas_de_spans() -> None:
    """**La lista es una afirmación sobre lo que hacen los conversores. Se comprueba.**

    `expresses_spans` lo fija el conversor según el formato de origen, así que
    `types.FORMATOS_CON_SPANS` y `FORMATOS_SIN_SPANS` no son la verdad: son una copia de
    la verdad. Y una copia se queda vieja.

    **Se quedó vieja, y durante cuatro hitos.** `_dataframe.py` pone
    `expresses_spans=False` en su primera línea y dice por qué —un `DataFrame` es una
    rejilla rectangular y un `MultiIndex` no distingue «combinada» de «repetida»—, pero
    `dataframe` no estaba en `FORMATOS_SIN_SPANS`. Consecuencia medida: una tabla con
    `source_format="dataframe"` podía declarar `expresses_spans=True` y `is_wellformed()`
    la daba por buena. Y `camelot`, que devuelve marcos, está en la campaña.

    Este test ejecuta los cinco sobre una tabla mínima y compara. No es una lista de
    valores esperados escrita a mano: **pregunta al código**.
    """
    salidas = {
        "html": from_html("<table><tr><td>a</td><td>b</td></tr></table>"),
        "markdown": from_markdown("| a | b |\n|---|---|\n| 1 | 2 |"),
        "tei": from_tei("<table><row><cell>a</cell><cell>b</cell></row></table>"),
        "text": from_text_heuristic("a  b\n1  2"),
    }
    assert set(salidas) | {"dataframe"} == set(FORMATOS_CANONICOS), (
        "este test no cubre los cinco formatos canónicos; falta alguno por preguntar"
    )
    for formato, tablas in salidas.items():
        assert tablas, f"{formato}: el conversor no devolvió ninguna tabla que preguntar"
        for t in tablas:
            assert t.source_format == formato
            declarado = formato in FORMATOS_CON_SPANS
            assert t.expresses_spans is declarado, (
                f"`{formato}`: el conversor pone expresses_spans={t.expresses_spans} y "
                f"types dice {declarado}. La lista es una copia de lo que hace el "
                f"conversor, así que manda el conversor"
            )
            assert (formato in FORMATOS_SIN_SPANS) is not declarado


def test_from_dataframe_no_expresa_spans_y_la_lista_lo_dice() -> None:
    """`dataframe` aparte porque su conversor no toma una cadena sino marcos.

    Es **el que estaba mal**, así que se pregunta explícitamente en vez de darlo por
    incluido en el bucle de arriba.
    """

    class _Marco:
        columns = ("a", "b")

        def itertuples(self, index: bool = False) -> object:
            return iter([("1", "2")])

    tablas = from_dataframe([_Marco()])
    assert tablas and tablas[0].source_format == "dataframe"
    assert tablas[0].expresses_spans is False
    assert "dataframe" in FORMATOS_SIN_SPANS
