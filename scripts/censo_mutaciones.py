"""Las tablas base del censo y las diecisiete familias de mutación.

Fichero aparte de `censo_invariantes.py` por el límite de 300 líneas de
`CLAUDE.md`. Aquí vive **qué se rompe y qué código tiene que salir**; allí, cómo
se cuenta y qué se publica.
"""

from __future__ import annotations

from collections.abc import Iterator

from docbench_es.core.canonical import from_html
from docbench_es.types import CanonicalCell, CanonicalTable, HallazgoTabla

# Tamaños del censo. El 33 no es decorativo: es el span máximo que midió el
# sondeo del BOE del 22 de agosto de 2026, y un validador que sólo funcionara con
# tablas pequeñas mediría su 100% sobre el caso fácil.
TAMANOS = [(1, 1), (1, 3), (3, 1), (2, 2), (3, 4), (4, 3), (4, 4), (2, 33), (33, 2)]
PATRONES = ("suelta", "fila_larga", "columna_larga", "bloque")

# Las rejillas de arriba son sintéticas y COMPLETAS. Un «cero falsos positivos»
# medido sólo sobre ellas afirmaría menos de lo que parece, porque no contiene
# ninguna de las formas que el sondeo del BOE midió de verdad. Éstas sí, y entran
# al censo por `from_html`, no construidas a mano, que es como llegarán en L4 y L5.
FORMAS_DEL_BOE = {
    "fila corta (<tr> con menos <td>)": (
        "<table><tr><td>a</td><td>b</td><td>c</td></tr><tr><td>d</td></tr></table>"
    ),
    'rowspan="0" con <thead>/<tbody>': (
        "<table><thead><tr><th>Grupo</th><th>Base</th></tr></thead>"
        '<tbody><tr><td rowspan="0">baja entera</td><td>1.234,56</td></tr>'
        "<tr><td>200,00</td></tr><tr><td>150,00</td></tr></tbody></table>"
    ),
    "<colgroup> y <col span>": (
        '<table><colgroup><col/><col/><col span="2"/></colgroup>'
        '<tr><th rowspan="2">G</th><th colspan="3">R</th></tr>'
        "<tr><th>a</th><th>b</th><th>c</th></tr></table>"
    ),
    "<p> y <sup> dentro de la celda": (
        "<table><tr><td><p>Grupo 3</p><p>Auxiliar</p></td>"
        "<td>Total m<sup>2</sup></td></tr><tr><td>x</td><td>y</td></tr></table>"
    ),
    "<img> como único contenido de celda": (
        '<table><tr><td><img src="f.png" alt="Firma"/></td><td>x</td></tr>'
        "<tr><td>a</td><td>b</td></tr></table>"
    ),
    "<caption>": "<table><caption>Cuadro 1</caption><tr><td>a</td></tr></table>",
    "tabla anidada dentro de una celda": (
        "<table><tr><td>fuera<table><tr><td>dentro</td></tr></table></td>"
        "<td>z</td></tr><tr><td>a</td><td>b</td></tr></table>"
    ),
    # Era «el máximo observado en el sondeo», y es FALSO: 33 es el máximo de la
    # ventana de agosto. Recomputado sobre las tres ventanas (n=600):
    # otoño **59**, agosto 33, primavera 22. El censo se queda en 33 —cambiar la
    # forma movería el 8.525/8.525 publicado— y la distancia hasta 59 se declara
    # en `LIMITS.md` en vez de esconderse detrás de una etiqueta que no era cierta.
    "span 33, el máximo de la ventana de agosto (el de las tres es 59)": (
        '<table><tr><td colspan="33">cabecera larga</td></tr>'
        "<tr>" + "<td>x</td>" * 33 + "</tr></table>"
    ),
}


def _base(n_filas: int, n_cols: int, patron: str) -> CanonicalTable:
    """Una tabla legal y COMPLETA: cada posición cubierta exactamente una vez."""
    ocupado: set[tuple[int, int]] = set()
    celdas: list[CanonicalCell] = []

    def poner(fila: int, col: int, rowspan: int, colspan: int) -> None:
        for f in range(fila, fila + rowspan):
            for c in range(col, col + colspan):
                ocupado.add((f, c))
        celdas.append(CanonicalCell(fila, col, rowspan, colspan, f"{fila},{col}", fila == 0))

    if patron == "fila_larga":
        poner(0, 0, 1, n_cols)
    elif patron == "columna_larga":
        poner(0, 0, n_filas, 1)
    elif patron == "bloque" and n_filas >= 2 and n_cols >= 2:
        poner(0, 0, 2, 2)
    for fila in range(n_filas):
        for col in range(n_cols):
            if (fila, col) not in ocupado:
                poner(fila, col, 1, 1)
    return CanonicalTable(
        cells=tuple(celdas),
        n_rows=n_filas,
        n_cols=n_cols,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )


def _con_celdas(t: CanonicalTable, celdas: tuple[CanonicalCell, ...]) -> CanonicalTable:
    return CanonicalTable(
        cells=celdas,
        n_rows=t.n_rows,
        n_cols=t.n_cols,
        page_span=t.page_span,
        caption=t.caption,
        expresses_spans=t.expresses_spans,
        source_format=t.source_format,
    )


def _sustituir(t: CanonicalTable, i: int, celda: CanonicalCell) -> CanonicalTable:
    celdas = list(t.cells)
    celdas[i] = celda
    return _con_celdas(t, tuple(celdas))


def _pisa_a_la_derecha(t: CanonicalTable, c: CanonicalCell) -> bool:
    return any(
        t.cell_at(fila, c.col + c.colspan) is not None for fila in range(c.row, c.row + c.rowspan)
    )


def _pisa_abajo(t: CanonicalTable, c: CanonicalCell) -> bool:
    return any(
        t.cell_at(c.row + c.rowspan, col) is not None for col in range(c.col, c.col + c.colspan)
    )


def _mutaciones_legales(t: CanonicalTable) -> Iterator[tuple[str, CanonicalTable]]:
    """Cambios que NO rompen nada: rellenar un hueco de cola creciendo un span.

    Son control negativo, no detección. Salieron de meter las formas reales del
    BOE en el censo: sobre una tabla con fila corta, crecer un `colspan` o un
    `rowspan` hacia el hueco produce una tabla perfectamente legal —es lo que se
    vería si la celda tuviera de verdad ese span—, y `validate` **tiene que
    aceptarla**. Antes estaban contadas como «tendría que detectarse», que era
    pedirle al validador que rechazara HTML válido.
    """
    for i, c in enumerate(t.cells):
        if c.col + c.colspan < t.n_cols and not _pisa_a_la_derecha(t, c):
            yield (
                "colspan +1 rellenando un hueco",
                _sustituir(t, i, CanonicalCell(c.row, c.col, c.rowspan, c.colspan + 1)),
            )
        if c.row + c.rowspan < t.n_rows and not _pisa_abajo(t, c):
            yield (
                "rowspan +1 rellenando un hueco",
                _sustituir(t, i, CanonicalCell(c.row, c.col, c.rowspan + 1, c.colspan)),
            )


UN_SOLO_CODIGO = frozenset(
    {
        HallazgoTabla.SPAN_MENOR_QUE_UNO,
        HallazgoTabla.POSICION_NEGATIVA,
        HallazgoTabla.SPAN_FUERA_DE_RANGO,
        HallazgoTabla.PAGE_SPAN_INVALIDO,
        HallazgoTabla.EXPRESSES_SPANS_IMPOSIBLE,
        HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO,
    }
)
"""Defectos de UN solo sitio: tienen que dar su código FATAL y ninguno más.

Comprobar sólo la pertenencia deja pasar los códigos de más, y los códigos de más
no son cosméticos: la tasa de tablas mal formadas por extractor de L5 se calcula
por código, así que un defecto que emite tres la infla y la correlaciona consigo
misma. Un `colspan=0` llegó a producir `SPAN_MENOR_QUE_UNO`, `HUECO_INTERIOR` y
`COLUMNA_VACIA` a la vez.

Los demás quedan fuera porque su mutación sí cambia la tabla de más de una manera:
borrar una celda deja un hueco Y puede vaciar una columna, de verdad.

Los tres defectos que hacen DESCARTAR una celda —span degenerado, span fuera de
rango y posición negativa— entran aquí porque `comprobar` deja de analizar la
cobertura en cuanto hay una celda sin colocar: con una celda descartada no se sabe
qué área ocupaba, así que cualquier hueco o columna vacía que saliera sería
consecuencia de ese defecto, no un hallazgo propio.
"""


def _mutaciones(t: CanonicalTable) -> Iterator[tuple[str, HallazgoTabla, CanonicalTable]]:
    """Todas las formas de romper una tabla, con el código que TIENE que salir."""
    for i, c in enumerate(t.cells):
        # Sólo cuenta como solape si la posición de al lado está OCUPADA. Sobre
        # una tabla con hueco de cola, crecer un span RELLENA el hueco y la tabla
        # resultante es legal: exigir que se detecte sería exigir que `validate`
        # rechace HTML válido. Esas crecidas van al censo de mutaciones legales.
        if c.col + c.colspan < t.n_cols and _pisa_a_la_derecha(t, c):
            yield (
                "colspan +1 sobre la vecina",
                HallazgoTabla.SOLAPE,
                _sustituir(t, i, CanonicalCell(c.row, c.col, c.rowspan, c.colspan + 1)),
            )
        if c.row + c.rowspan < t.n_rows and _pisa_abajo(t, c):
            yield (
                "rowspan +1 sobre la de abajo",
                HallazgoTabla.SOLAPE,
                _sustituir(t, i, CanonicalCell(c.row, c.col, c.rowspan + 1, c.colspan)),
            )
        yield (
            "rowspan fuera de rango",
            HallazgoTabla.SPAN_FUERA_DE_RANGO,
            _sustituir(t, i, CanonicalCell(c.row, c.col, t.n_rows - c.row + 1, c.colspan)),
        )
        yield (
            "colspan fuera de rango",
            HallazgoTabla.SPAN_FUERA_DE_RANGO,
            _sustituir(t, i, CanonicalCell(c.row, c.col, c.rowspan, t.n_cols - c.col + 1)),
        )
        for span in (0, -1, -7):
            yield (
                f"rowspan={span}",
                HallazgoTabla.SPAN_MENOR_QUE_UNO,
                _sustituir(t, i, CanonicalCell(c.row, c.col, span, c.colspan)),
            )
            yield (
                f"colspan={span}",
                HallazgoTabla.SPAN_MENOR_QUE_UNO,
                _sustituir(t, i, CanonicalCell(c.row, c.col, c.rowspan, span)),
            )
        yield (
            "posicion negativa",
            HallazgoTabla.POSICION_NEGATIVA,
            _sustituir(t, i, CanonicalCell(-1, c.col, c.rowspan, c.colspan)),
        )
        yield (
            "celda duplicada",
            HallazgoTabla.SOLAPE,
            _con_celdas(t, (*t.cells, c)),
        )
        # Hueco interior: se borra una celda que tiene otra a su derecha ORIGINADA
        # en la misma fila. Es la unica forma de hueco que ningun formato produce.
        hermanas = [o for o in t.cells if o.row == c.row and o.col > c.col]
        columna_cubierta_en_otra_fila = any(
            o.row != c.row and o.col <= c.col < o.col + o.colspan for o in t.cells
        )
        if hermanas and columna_cubierta_en_otra_fila:
            yield (
                "celda del medio borrada",
                HallazgoTabla.HUECO_INTERIOR,
                _con_celdas(t, tuple(o for o in t.cells if o is not c)),
            )
    yield (
        "n_cols inflado",
        HallazgoTabla.COLUMNA_VACIA,
        CanonicalTable(t.cells, t.n_rows, t.n_cols + 1, t.page_span, None, True, t.source_format),
    )
    yield (
        "dimension negativa",
        HallazgoTabla.DIMENSION_INCOHERENTE,
        CanonicalTable(t.cells, -1, t.n_cols, t.page_span, None, True, t.source_format),
    )
    yield (
        "celdas en una tabla de cero filas",
        HallazgoTabla.DIMENSION_INCOHERENTE,
        CanonicalTable(t.cells, 0, 0, t.page_span, None, True, t.source_format),
    )
    yield (
        "solape del estandar: celda que cruza una posicion ocupada",
        HallazgoTabla.SOLAPE,
        from_html(
            '<table><tr><td>a</td><td rowspan="2">b</td></tr>'
            '<tr><td colspan="2">c</td></tr></table>'
        )[0],
    )
    yield (
        "page_span invertido",
        HallazgoTabla.PAGE_SPAN_INVALIDO,
        CanonicalTable(t.cells, t.n_rows, t.n_cols, (9, 2), None, True, t.source_format),
    )
    yield (
        "source_format que no es ninguno de los cinco",  # informativo, no invalida
        HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO,
        CanonicalTable(t.cells, t.n_rows, t.n_cols, t.page_span, None, True, "ocr"),
    )
    if any(c.rowspan > 1 or c.colspan > 1 for c in t.cells):
        yield (
            "expresses_spans=False con celda combinada",
            HallazgoTabla.EXPRESSES_SPANS_IMPOSIBLE,
            CanonicalTable(t.cells, t.n_rows, t.n_cols, t.page_span, None, False, t.source_format),
        )
