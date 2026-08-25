"""§6.2 · El «o» de los huecos, resuelto y ejecutable.

§6.2 dice que la unión de celdas *«cubre exactamente `n_rows x n_cols` **o declara
los huecos**»*. Ese «o» no es traducible tal como está escrito —`CanonicalTable`
no tiene campo de huecos ni el manual nombra función alguna—, así que L1 lo
resuelve (ADR-0018) y este fichero es su forma ejecutable.

La distinción es **hueco de cola** (legítimo, informativo) contra **hueco
interior** (fatal). Y toda ella depende de una pregunta que tiene dos respuestas
opuestas sobre un caso real: qué significa «hay una celda a la derecha».

**Presupuesto de ejemplos: 60**, el mismo que las otras propiedades de
invariantes.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from _estrategias import codigos, tabla_bien_formada, tabla_con_rowspan_sobre_fila_corta
from docbench_es.core.canonical import holes, validate
from docbench_es.types import CanonicalCell, CanonicalTable, HallazgoTabla

EJEMPLOS = 60


def _hay_posicion_ocupada_a_la_derecha(t: CanonicalTable, fila: int, col: int) -> bool:
    """La lectura DESCARTADA: la rejilla rellena.

    «Un hueco es de cola si no hay ninguna posición ocupada a su derecha, venga de
    donde venga la celda que la ocupa.» Se deja escrita y ejecutable para que la
    alternativa no haya que reconstruirla de memoria dentro de seis meses: es la
    que `test_la_lectura_de_la_rejilla_rellena_rechaza_html_legal` refuta.
    """
    return any(t.cell_at(fila, c) is not None for c in range(col + 1, t.n_cols))


@settings(max_examples=EJEMPLOS)
@given(t=tabla_con_rowspan_sobre_fila_corta())
def test_el_rowspan_que_baja_sobre_una_fila_corta_es_legal(t: CanonicalTable) -> None:
    """**La condición 1.** Demuestra que la definición no tiene falso positivo.

    La forma: un `rowspan` que baja desde una fila de arriba y ocupa una columna a
    la derecha de donde se corta una fila corta. Las posiciones intermedias están
    vacías y **sí** hay una posición ocupada a su derecha, pero por una celda que
    no origina en esa fila.

    Es HTML legal. Con un 42% de tablas con `rowspan` en las secciones I+III del
    BOE, una definición que rechazara esto rechazaría corpus real, y el hito
    entero mediría sobre lo que sobrevive al validador en vez de sobre el corpus.

    La forma se genera **a propósito** y no se confía a que la estrategia general
    la encuentre: no generar la forma que importa es exactamente el fallo que L0
    documentó y corrigió en su propio test de `key()`.
    """
    ok, problemas = validate(t)
    assert ok is True, problemas
    assert HallazgoTabla.HUECO_INTERIOR not in codigos(problemas), problemas
    assert HallazgoTabla.HUECO_COLA in codigos(problemas), (
        "el hueco existe y se declara; lo que no es, es fatal"
    )


# 25 y no EJEMPLOS: esta propiedad sólo comprueba que la lectura descartada
# discrimina, y la familia que genera es pequeña y cerrada.
@settings(max_examples=25)
@given(t=tabla_con_rowspan_sobre_fila_corta())
def test_la_lectura_de_la_rejilla_rellena_rechaza_html_legal(t: CanonicalTable) -> None:
    """Demuestra POR QUÉ se descartó la otra lectura, en vez de afirmarlo.

    Sobre esta misma tabla —legal, y que el navegador pinta sin quejarse— la
    lectura de la rejilla rellena encuentra una posición ocupada a la derecha del
    hueco y la declararía interior, o sea fatal. Este test se cae el día que
    alguien cambie la definición a esa: no por opinión, sino porque entonces las
    dos afirmaciones de este fichero serían incompatibles.
    """
    huecos = holes(t)
    assert huecos, "la estrategia tiene que producir huecos, o no está probando nada"
    assert any(_hay_posicion_ocupada_a_la_derecha(t, f, c) for f, c in huecos), (
        "sin esto, el caso no discrimina entre las dos lecturas"
    )
    assert validate(t)[0] is True, "y aun así la tabla es válida: gana la lectura del origen"


def test_hueco_interior_es_fatal() -> None:
    """Demuestra la otra dirección, sin la cual la anterior sería permisividad.

    Aquí el hueco está a la izquierda de una celda que **sí origina en esa fila**.
    Ningún formato de los cinco puede producirlo: los cinco rellenan de izquierda
    a derecha, así que un hueco a la izquierda de una celda de la propia fila
    significa que la colocación está mal. Es un bug del conversor disfrazado de
    tabla plausible, y TEDS lo puntuaría como si fuera una tabla.
    """
    t = CanonicalTable(
        cells=(
            CanonicalCell(0, 0, text="a"),
            CanonicalCell(0, 1, text="b"),
            CanonicalCell(1, 1, text="perdió la de la izquierda"),
        ),
        n_rows=2,
        n_cols=2,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    ok, problemas = validate(t)
    assert ok is False, problemas
    assert HallazgoTabla.HUECO_INTERIOR in codigos(problemas), problemas


@settings(max_examples=EJEMPLOS)
@given(t=tabla_bien_formada(), rompe=st.booleans(), span=st.integers(min_value=-2, max_value=9))
def test_holes_enumera_exactamente_lo_que_cell_at_no_cubre(
    t: CanonicalTable, rompe: bool, span: int
) -> None:
    """Demuestra que la declaración de huecos **no puede caducar**.

    `holes()` es derivada y no un campo almacenado a propósito: un campo puede
    desacordar con `cells`, y entonces habría dos fuentes de verdad sobre la misma
    tabla. Este test ata la derivada a `cell_at`, que es lo que L2 usará para
    recorrer la rejilla.
    """
    if rompe and t.cells:
        # También sobre tablas ROTAS, que es donde las dos derivaciones podrían
        # separarse: `holes` recorre las celdas de una pasada y `cell_at` consulta
        # posición a posición, y una celda con span degenerado o fuera de rango
        # las trata distinto si no comparten la misma definición de «cubrir».
        primera = t.cells[0]
        t = CanonicalTable(
            cells=(CanonicalCell(primera.row, primera.col, span, primera.colspan), *t.cells[1:]),
            n_rows=t.n_rows,
            n_cols=t.n_cols,
            page_span=t.page_span,
            caption=t.caption,
            expresses_spans=t.expresses_spans,
            source_format=t.source_format,
        )
    esperado = tuple(
        (f, c) for f in range(t.n_rows) for c in range(t.n_cols) if t.cell_at(f, c) is None
    )
    assert holes(t) == esperado


def test_un_hueco_no_es_una_celda_vacia() -> None:
    """Demuestra la distinción de la que depende TEDS en L2.

    `<tr><td>a</td></tr>` y `<tr><td>a</td><td></td></tr>` son árboles distintos y
    TEDS los puntúa distinto. Si `holes()` no los separara, L2 tendría que
    inventarse la diferencia o perderla, y perderla premiaría al extractor que se
    come una celda al final de la fila.
    """
    # Dos filas y no una: con una sola fila el hueco seria la COLUMNA entera, que
    # es fatal y por otro motivo. La segunda fila cubre la columna 1, y asi lo
    # unico que distingue a las dos tablas es la celda vacia contra el hueco.
    abajo = (CanonicalCell(1, 0, text="b"), CanonicalCell(1, 1, text="c"))
    con_hueco = CanonicalTable(
        cells=(CanonicalCell(0, 0, text="a"), *abajo),
        n_rows=2,
        n_cols=2,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    con_celda_vacia = CanonicalTable(
        cells=(CanonicalCell(0, 0, text="a"), CanonicalCell(0, 1, text=""), *abajo),
        n_rows=2,
        n_cols=2,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )

    assert holes(con_hueco) == ((0, 1),)
    assert holes(con_celda_vacia) == ()
    assert validate(con_hueco)[0] is True
    assert validate(con_celda_vacia) == (True, [])


@settings(max_examples=EJEMPLOS)
@given(
    t=tabla_bien_formada(),
    de_mas=st.integers(min_value=1, max_value=3),
)
def test_la_fila_de_mas_se_declara_y_no_se_traga(t: CanonicalTable, de_mas: int) -> None:
    """Demuestra que una fila inventada no pasa en silencio.

    `n_rows` mayor que la extensión de las celdas es HTML legal —`<tr></tr>` al
    final—, así que no es fatal. Pero **tiene que aparecer**: si no apareciera,
    un conversor que se inventara tres filas produciría una tabla que valida
    limpia y que TEDS puntuaría contra una verdad de tres filas menos.
    """
    inflada = CanonicalTable(
        cells=t.cells,
        n_rows=t.n_rows + de_mas,
        n_cols=t.n_cols,
        page_span=t.page_span,
        caption=t.caption,
        expresses_spans=t.expresses_spans,
        source_format=t.source_format,
    )
    ok, problemas = validate(inflada)
    assert ok is True, problemas
    assert HallazgoTabla.FILA_VACIA in codigos(problemas), problemas
