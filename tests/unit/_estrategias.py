"""Estrategias de `hypothesis` para tablas canónicas. NO es un fichero de tests.

Vive aquí y no en `src/` a propósito: si el generador de tablas viviera junto al
validador, un mismo malentendido sobre lo que es una tabla legal estaría en los
dos lados y se darían la razón. El generador **reimplementa** la colocación del
estándar HTML —izquierda a derecha, saltando lo ocupado— de forma independiente,
y ésa es toda su gracia.

Los spans van sesgados hacia arriba a propósito. El sondeo del BOE del 22 de
agosto de 2026 midió que en las secciones I+III **el 63% de los documentos con tabla traen span
> 1 y el 42% traen `rowspan` > 1**, con un máximo observado de 33. Un generador
que produjera sobre todo tablas de celdas sueltas probaría el caso raro.
"""

from __future__ import annotations

from html import escape

from hypothesis import strategies as st

from docbench_es.types import CanonicalCell, CanonicalTable

TEXTOS = st.text(alphabet="abcáéñ 0123456789,.", min_size=0, max_size=6)


def _libre(ocupado: set[tuple[int, int]], fila: int, col: int, alto: int, ancho: int) -> bool:
    return all((fila + df, col + dc) not in ocupado for df in range(alto) for dc in range(ancho))


@st.composite
def _celdas_colocadas(
    draw: st.DrawFn,
    n_filas: int,
    ancho_max: int,
    *,
    permitir_cortar: bool,
) -> list[CanonicalCell]:
    """El algoritmo de colocación del estándar HTML, escrito a mano.

    Para cada fila, un cursor que avanza de izquierda a derecha saltando lo que ya
    ocupa un `rowspan` de arriba. `permitir_cortar` es lo que distingue una tabla
    con huecos de cola —la fila corta, cotidiana en el BOE— de una tabla completa.
    """
    ocupado: set[tuple[int, int]] = set()
    celdas: list[CanonicalCell] = []
    for fila in range(n_filas):
        col = 0
        while col < ancho_max:
            if (fila, col) in ocupado:
                col += 1
                continue
            if permitir_cortar and draw(st.booleans()):
                break  # la fila se acaba aquí: lo que quede a la derecha es hueco de cola
            ancho = 1
            while col + ancho < ancho_max and (fila, col + ancho) not in ocupado:
                ancho += 1
            colspan = draw(st.integers(min_value=1, max_value=ancho))
            alto = 1
            while fila + alto < n_filas and _libre(ocupado, fila + alto, col, 1, colspan):
                alto += 1
            rowspan = draw(st.integers(min_value=1, max_value=alto))
            for df in range(rowspan):
                for dc in range(colspan):
                    ocupado.add((fila + df, col + dc))
            celdas.append(
                CanonicalCell(
                    row=fila,
                    col=col,
                    rowspan=rowspan,
                    colspan=colspan,
                    text=draw(TEXTOS),
                    is_header=fila == 0,
                )
            )
            col += colspan
    return celdas


def _envolver(celdas: list[CanonicalCell], n_filas: int) -> CanonicalTable:
    """`n_cols` se DERIVA de la extensión máxima, como hace `from_html`.

    `n_filas` no: son las `<tr>` vistas, y una `<tr></tr>` al final es HTML legal,
    así que `n_rows` puede pasarse de la extensión de las celdas. Eso es
    `FILA_VACIA`, informativo.
    """
    n_cols = max((c.col + c.colspan for c in celdas), default=0)
    return CanonicalTable(
        cells=tuple(celdas),
        n_rows=n_filas,
        n_cols=n_cols,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )


@st.composite
def tabla_completa(draw: st.DrawFn, max_lado: int = 5) -> CanonicalTable:
    """Sin un solo hueco: toda posición cubierta por exactamente una celda.

    Es el control negativo duro. `validate` sobre esto tiene que devolver
    literalmente `(True, [])`, sin ni siquiera un hallazgo informativo.
    """
    n_filas = draw(st.integers(min_value=1, max_value=max_lado))
    ancho = draw(st.integers(min_value=1, max_value=max_lado))
    celdas = draw(_celdas_colocadas(n_filas, ancho, permitir_cortar=False))
    return _envolver(celdas, n_filas)


@st.composite
def tabla_bien_formada(draw: st.DrawFn, max_lado: int = 5) -> CanonicalTable:
    """Legal, pero con filas cortas: puede traer huecos de cola y filas vacías."""
    n_filas = draw(st.integers(min_value=1, max_value=max_lado))
    ancho = draw(st.integers(min_value=1, max_value=max_lado))
    celdas = draw(_celdas_colocadas(n_filas, ancho, permitir_cortar=True))
    return _envolver(celdas, n_filas)


@st.composite
def tabla_con_rowspan_sobre_fila_corta(draw: st.DrawFn) -> CanonicalTable:
    """**La forma de la condición 1.** Se genera a propósito, no por suerte.

    Un `rowspan` que baja desde una fila de arriba y ocupa una columna a la
    DERECHA de donde se corta una fila corta. La posición de la derecha está
    ocupada, pero por una celda que **no origina en esa fila**:

        fila 0:  A | B | C | D(rowspan=3)
        fila 1:  E | F | G |   ↓
        fila 2:  x |   |   |   ↓        ← (2,1) y (2,2) huecos; (2,3) ocupada

    Es HTML legal y el navegador lo pinta sin quejarse. Que la estrategia lo
    genere **antes** de fijar la definición de hueco interior es la única forma de
    que la definición no se fije sobre un caso que nadie miró: no generar la forma
    que importa es exactamente el fallo que L0 documentó en su propio sondeo.
    """
    ancho = draw(st.integers(min_value=2, max_value=5))
    n_filas = draw(st.integers(min_value=2, max_value=5))
    col_larga = ancho - 1
    corte = draw(st.integers(min_value=0, max_value=col_larga - 1))
    celdas: list[CanonicalCell] = [
        CanonicalCell(row=0, col=col_larga, rowspan=n_filas, colspan=1, text="baja entera")
    ]
    for fila in range(n_filas):
        # La última fila se corta antes de la columna larga: ahí están los huecos.
        hasta = corte if fila == n_filas - 1 else col_larga
        celdas.extend(
            CanonicalCell(row=fila, col=col, rowspan=1, colspan=1, text=f"{fila},{col}")
            for col in range(hasta)
        )
    return _envolver(celdas, n_filas)


def codigos(problemas: list[str]) -> set[str]:
    """El código de cada hallazgo, sin el detalle.

    Los tests afirman sobre el código del enum cerrado y nunca sobre la prosa del
    detalle: si afirmaran sobre la prosa, cambiar una palabra de un mensaje
    rompería la suite y el enum dejaría de ser el contrato.
    """
    return {p.split(":", 1)[0] for p in problemas}


def a_html(t: CanonicalTable) -> str:
    """Renderiza una tabla canónica a HTML. **Sólo para tests.**

    Escrito a mano y a propósito **fuera** de `src/`: es la otra mitad del test de
    ida y vuelta, y si compartiera código con `from_html` los dos se darían la
    razón sobre el mismo malentendido. Por eso el test de ida y vuelta no basta
    solo y va acompañado de golden escritos a mano.

    Los huecos de cola no se emiten: en HTML una fila corta es sencillamente una
    `<tr>` con menos `<td>`, que es de donde salen.
    """
    partes = ["<table>"]
    if t.caption:
        partes.append(f"<caption>{escape(t.caption)}</caption>")
    for fila in range(t.n_rows):
        partes.append("<tr>")
        for celda in sorted((c for c in t.cells if c.row == fila), key=lambda c: c.col):
            etiqueta = "th" if celda.is_header else "td"
            atributos = ""
            if celda.rowspan != 1:
                atributos += f' rowspan="{celda.rowspan}"'
            if celda.colspan != 1:
                atributos += f' colspan="{celda.colspan}"'
            partes.append(f"<{etiqueta}{atributos}>{escape(celda.text)}</{etiqueta}>")
        partes.append("</tr>")
    partes.append("</table>")
    return "".join(partes)
