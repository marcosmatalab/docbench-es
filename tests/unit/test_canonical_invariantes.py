"""§6.2 · Los invariantes de la forma canónica, y el criterio de aceptación de L1.

Lo que este fichero tiene que demostrar es que **una tabla rota se detecta**, y el
manual pone el listón en el 100%. Property-based y no de ejemplo: los solapes y
los spans fuera de rango son un espacio combinatorio, y los casos escritos a mano
cubren los que a uno se le ocurren, que son justo los que ya funcionan.

**Los dos mutantes.** Cada test de aquí se ha corrido contra dos versiones rotas
de `validate` antes de darlo por bueno: `siempre_ok`, que devuelve `(True, [])`, y
`siempre_roto`, que devuelve `(False, ["x"])`. La suite tiene que caerse contra
**los dos**. Un test que sólo afirma `not ok` pasa en verde contra el que rechaza
todo, y entonces no demuestra detección: demuestra pesimismo.
"""

from __future__ import annotations

import pytest
from _estrategias import (
    codigos,
    tabla_bien_formada,
    tabla_completa,
)
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from docbench_es.core.canonical import validate
from docbench_es.types import CanonicalCell, CanonicalTable, HallazgoTabla


def _sin_fatales(problemas: list[str]) -> bool:
    return not any(HallazgoTabla(c).es_fatal for c in codigos(problemas))


def _reemplazar(t: CanonicalTable, i: int, celda: CanonicalCell) -> CanonicalTable:
    celdas = list(t.cells)
    celdas[i] = celda
    return CanonicalTable(
        cells=tuple(celdas),
        n_rows=t.n_rows,
        n_cols=t.n_cols,
        page_span=t.page_span,
        caption=t.caption,
        expresses_spans=t.expresses_spans,
        source_format=t.source_format,
    )


@given(t=tabla_completa())
def test_la_tabla_completa_no_produce_ni_un_hallazgo(t: CanonicalTable) -> None:
    """**El control negativo, y va el primero.**

    Demuestra que el validador no es un pesimista. Una tabla que cubre cada
    posición exactamente una vez sale `(True, [])` literal, sin ni siquiera un
    hallazgo informativo. Sin este test, un `validate` que devolviera
    `(False, ["x"])` para todo pasaría en verde los seis que vienen detrás, y el
    «100% de detección» sería cierto y no significaría nada.
    """
    assert validate(t) == (True, []), f"{t.cells}"


@given(t=tabla_bien_formada())
def test_la_fila_corta_es_legal_y_no_invalida_la_tabla(t: CanonicalTable) -> None:
    """Demuestra que lo cotidiano del BOE no se rechaza.

    Una `<tr>` con menos `<td>` que columnas tiene la tabla es HTML legal y el
    navegador la pinta sin quejarse. Si `validate` la rechazara, `from_html`
    fallaría sobre el corpus real y no habría medición ninguna que publicar.
    """
    ok, problemas = validate(t)
    assert ok is True, problemas
    assert _sin_fatales(problemas), problemas


@st.composite
def _tabla_con_solape(draw: st.DrawFn) -> tuple[CanonicalTable, int]:
    """Crece el `colspan` de una celda hasta pisar a la de su derecha.

    Es la forma que tendría el bug de verdad —un conversor que lee mal un
    `colspan`—, no un solape de laboratorio.
    """
    t = draw(tabla_completa())
    candidatos = [
        i
        for i, c in enumerate(t.cells)
        if c.col + c.colspan < t.n_cols and t.cell_at(c.row, c.col + c.colspan) is not None
    ]
    assume(candidatos)
    i = draw(st.sampled_from(candidatos))
    c = t.cells[i]
    crecida = CanonicalCell(c.row, c.col, c.rowspan, c.colspan + 1, c.text, c.is_header)
    return _reemplazar(t, i, crecida), i


@given(caso=_tabla_con_solape())
def test_solape_detectado_siempre(caso: tuple[CanonicalTable, int]) -> None:
    """Demuestra el invariante 1 sobre tablas donde el span es la NORMA.

    En las secciones I+III del BOE, el 63% [50-74] de los documentos con tabla
    traen span > 1 (n=57 documentos). Un validador que sólo supiera de celdas
    sueltas dejaría fuera justo esa parte del corpus, y su «100% detectado»
    estaría medido sobre lo fácil.
    """
    t, _ = caso
    ok, problemas = validate(t)
    assert ok is False, problemas
    assert HallazgoTabla.SOLAPE in codigos(problemas), problemas


@st.composite
def _tabla_con_span_fuera_de_rango(draw: st.DrawFn) -> CanonicalTable:
    t = draw(tabla_completa())
    i = draw(st.integers(min_value=0, max_value=len(t.cells) - 1))
    c = t.cells[i]
    de_mas = draw(st.integers(min_value=1, max_value=4))
    if draw(st.booleans()):
        rota = CanonicalCell(
            c.row, c.col, t.n_rows - c.row + de_mas, c.colspan, c.text, c.is_header
        )
    else:
        rota = CanonicalCell(
            c.row, c.col, c.rowspan, t.n_cols - c.col + de_mas, c.text, c.is_header
        )
    return _reemplazar(t, i, rota)


@given(t=_tabla_con_span_fuera_de_rango())
def test_span_fuera_de_rango_detectado(t: CanonicalTable) -> None:
    """Demuestra el invariante 3: el rectángulo de una celda cabe en la tabla.

    Una celda que se sale es la firma de un conversor que perdió la cuenta de las
    filas. Si pasara, `cell_at` respondería por posiciones que no existen y TEDS
    puntuaría un árbol que no se corresponde con ninguna tabla.
    """
    ok, problemas = validate(t)
    assert ok is False, problemas
    assert HallazgoTabla.SPAN_FUERA_DE_RANGO in codigos(problemas), problemas


@given(
    t=tabla_completa(),
    span=st.integers(min_value=-3, max_value=0),
    en_filas=st.booleans(),
    semilla=st.integers(min_value=0, max_value=99),
)
def test_span_menor_que_uno_es_fatal_y_la_celda_sigue_invisible(
    t: CanonicalTable, span: int, en_filas: bool, semilla: int
) -> None:
    """Demuestra la decisión de L1 sobre el caso degenerado que declaró L0.

    L0 dejó `cell_at` devolviendo `None` para una celda de span 0 —invisible, como
    un hueco— y dejó dicho que **quien lo reporta es `is_wellformed()`**. Esto
    demuestra las dos mitades a la vez: la celda sigue sin cubrir nada, y ahora
    además **se cuenta**. Si en vez de reportarlo se normalizara a 1 en silencio,
    un error del conversor se convertiría en una tabla plausible que TEDS
    puntuaría como buena.
    """
    i = semilla % len(t.cells)
    c = t.cells[i]
    rota = (
        CanonicalCell(c.row, c.col, span, c.colspan, c.text, c.is_header)
        if en_filas
        else CanonicalCell(c.row, c.col, c.rowspan, span, c.text, c.is_header)
    )
    t_rota = _reemplazar(t, i, rota)

    ok, problemas = validate(t_rota)
    assert ok is False, problemas
    assert HallazgoTabla.SPAN_MENOR_QUE_UNO in codigos(problemas), problemas
    assert t_rota.cell_at(rota.row, rota.col) is not rota, "la celda degenerada no cubre nada"


def test_la_columna_vacia_es_fatal_y_la_fila_vacia_no() -> None:
    """Demuestra la asimetría, que no es un capricho: cada lado se justifica.

    `<tr></tr>` es HTML legal, así que una fila entera sin cubrir es informativa.
    Una COLUMNA entera sin cubrir, en cambio, no la puede producir ningún formato
    de origen: los cinco rellenan de izquierda a derecha, así que una columna
    vacía significa que `n_cols` se calculó de más. Eso es un bug del conversor
    disfrazado de tabla plausible, y sale fatal.
    """
    fila_vacia = CanonicalTable(
        cells=(CanonicalCell(0, 0), CanonicalCell(0, 1)),
        n_rows=2,  # la segunda <tr> existe y está vacía
        n_cols=2,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    ok, problemas = validate(fila_vacia)
    assert ok is True, problemas
    assert HallazgoTabla.FILA_VACIA in codigos(problemas), problemas

    columna_vacia = CanonicalTable(
        cells=(CanonicalCell(0, 0), CanonicalCell(1, 0)),
        n_rows=2,
        n_cols=2,  # nadie cubre nunca la columna 1
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    ok, problemas = validate(columna_vacia)
    assert ok is False, problemas
    assert HallazgoTabla.COLUMNA_VACIA in codigos(problemas), problemas


@pytest.mark.parametrize(
    ("formato", "expresa", "combinada"),
    [
        ("markdown", True, False),  # markdown no puede expresar spans: mentir hacia arriba
        ("text", True, False),
        ("html", False, True),  # dice que no puede y trae una celda combinada
    ],
)
def test_expresses_spans_imposible_es_fatal(formato: str, expresa: bool, combinada: bool) -> None:
    """Demuestra la regla que no se relaja, hecha código.

    `expresses_spans` lo fija el conversor según el formato de origen. Un
    extractor que se declare capaz de `rowspan` devolviendo Markdown miente, y su
    mentira **le beneficia**: pasaría de `NO_APLICABLE` a competir en el estrato
    de celdas combinadas, que es el que se sobremuestrea y el titular. Esto es lo
    que la suite de conformidad de L5 usará para cazarlo.
    """
    celda = CanonicalCell(0, 0, 2 if combinada else 1, 1)
    t = CanonicalTable(
        cells=(celda,),
        n_rows=2 if combinada else 1,
        n_cols=1,
        page_span=(1, 1),
        caption=None,
        expresses_spans=expresa,
        source_format=formato,
    )
    ok, problemas = validate(t)
    assert ok is False, problemas
    assert HallazgoTabla.EXPRESSES_SPANS_IMPOSIBLE in codigos(problemas), problemas


def test_la_tabla_vacia_es_valida_y_el_page_span_al_reves_no() -> None:
    """Demuestra los dos casos que el manual declara y nadie mira.

    §12 define TEDS de dos tablas vacías como 1, así que la tabla vacía **tiene
    que ser construible y válida**: si `validate` la rechazara, ese caso
    degenerado no se podría ni representar. Y un `page_span` invertido es la
    firma de una tabla multipágina mal ensamblada: barato de comprobar, y si no
    se comprueba aquí no lo comprueba nadie.
    """
    vacia = CanonicalTable((), 0, 0, (1, 1), None, False, "text")
    assert validate(vacia) == (True, [])

    del_reves = CanonicalTable((), 0, 0, (7, 3), None, False, "text")
    ok, problemas = validate(del_reves)
    assert ok is False, problemas
    assert HallazgoTabla.PAGE_SPAN_INVALIDO in codigos(problemas), problemas


@settings(max_examples=50)
@given(t=tabla_bien_formada())
def test_validate_y_is_wellformed_dan_la_misma_respuesta(t: CanonicalTable) -> None:
    """Demuestra que **no hay dos fuentes de verdad**.

    §9.1 pone `validate()` en `core.canonical` y §6.2 pone `is_wellformed()` en la
    dataclass. El contrato de capas prohíbe que `types` importe `core`, así que el
    algoritmo vive en `types` y `core.canonical.validate` delega. Este test es lo
    que impide que alguien «arregle» esa asimetría reimplementando la validación
    en el otro lado: el día que las dos respuestas se separen, esto se cae.
    """
    assert validate(t) == t.is_wellformed()
