"""§9.1 · Los otros cuatro conversores, y la regla que no se relaja.

`from_html` tiene fichero propio porque es el que alimenta también a la verdad.
Aquí van `from_markdown`, `from_dataframe`, `from_tei` y `from_text_heuristic`, y
sobre todo lo que comparten: **`expresses_spans` lo fija el conversor según el
formato de origen, nunca el extractor**.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from _estrategias import codigos
from hypothesis import given, settings
from hypothesis import strategies as st

from docbench_es.core.canonical import (
    from_dataframe,
    from_html,
    from_markdown,
    from_tei,
    from_text_heuristic,
    validate,
)
from docbench_es.types import HallazgoTabla

MD = """
Texto que no es tabla.

| Grupo | Base | Complemento |
|-------|------|-------------|
| 3     | 1.234,56 | 200,00 |
| 4     | 1.100,00 |
"""


class MarcoFalso:
    """Un doble de `DataFrame`, **fiel en lo que importa**: `itertuples` lleva índice.

    `DataFrame.itertuples()` tiene `index=True` por defecto y devuelve el índice
    como primer elemento de cada tupla. El primer doble de este fichero no lo
    hacía, y por eso ningún test cazó que `from_dataframe` llamaba a
    `itertuples()` sin `index=False`: cada fila salía desplazada una columna y el
    índice entraba como contenido, en TODAS las tablas de camelot.

    **Un doble que simplifica la interfaz real no prueba nada**: prueba el doble.
    """

    def __init__(self, columnas: list[object], filas: list[tuple[object, ...]]) -> None:
        self.columns = columnas
        self._filas = filas

    def itertuples(self, index: bool = True) -> Iterator[tuple[object, ...]]:
        if index:
            return iter([(i, *fila) for i, fila in enumerate(self._filas)])
        return iter(self._filas)


def test_markdown_lee_la_tabla_y_la_fila_corta_queda_como_hueco() -> None:
    """Demuestra que Markdown se lee sin inventar lo que no trae.

    La última fila tiene dos celdas en una tabla de tres columnas. No se rellena
    con una celda vacía: se deja como hueco de cola, porque celda vacía y hueco
    son árboles distintos para TEDS y rellenar sería decidir por el extractor.
    """
    (t,) = from_markdown(MD)
    assert (t.n_rows, t.n_cols) == (3, 3)
    assert t.source_format == "markdown"
    cabecera = t.cell_at(0, 0)
    assert cabecera is not None and cabecera.is_header is True and cabecera.text == "Grupo"
    importe = t.cell_at(1, 1)
    assert importe is not None and importe.text == "1.234,56"
    assert t.cell_at(2, 2) is None

    ok, problemas = validate(t)
    assert ok is True, problemas
    assert HallazgoTabla.HUECO_COLA in codigos(problemas)


def test_dataframe_no_expresa_spans_y_eso_tiene_precio() -> None:
    """**La decisión que mueve el titular del proyecto.**

    Un DataFrame es una rejilla rectangular: no tiene `rowspan`. ADR-0006 ya lo
    dice al listar «Camelot devuelve DataFrames» entre los formatos que pierden
    las celdas combinadas.

    El precio, que va escrito en `LIMITS.md` como **requisito de L5** y no como
    recordatorio: camelot sale `NO_APLICABLE` en toda tabla con celdas
    combinadas, y su nota **no se puede enseñar sin su cobertura evaluable al
    lado**. Cuánto es eso no está medido: el sondeo contó documentos con tabla,
    no tablas (LIMITS 36).
    """
    marco = MarcoFalso(["Grupo", "Base"], [("3", "1.234,56"), ("4", None)])
    (t,) = from_dataframe([marco])

    assert t.expresses_spans is False
    assert t.source_format == "dataframe"
    assert (t.n_rows, t.n_cols) == (3, 2)
    cabecera = t.cell_at(0, 1)
    assert cabecera is not None and cabecera.is_header is True and cabecera.text == "Base"
    vacia = t.cell_at(2, 1)
    assert vacia is not None and vacia.text == "", "None es celda vacía, no hueco"
    assert validate(t) == (True, [])


def test_dataframe_rechaza_lo_que_no_es_un_marco() -> None:
    """Demuestra que un objeto equivocado se ve, no se traga.

    Pasar una lista de listas donde se espera un DataFrame es un error de
    programación del extractor, no un documento difícil. Tragárselo devolvería
    cero tablas y el documento se contaría como «sin tablas», que es un número
    equivocado esperando a que alguien lo publique.
    """
    with pytest.raises(TypeError, match="columns"):
        from_dataframe([["a", "b"]])


@pytest.mark.parametrize(
    ("conversor", "entrada", "expresa"),
    [
        (from_html, "<table><tr><td>x</td></tr></table>", True),
        (from_tei, "<TEI><table><row><cell>x</cell></row></table></TEI>", True),
        (from_markdown, "| a |\n|---|\n| 1 |", False),
        (from_text_heuristic, "a  b\nc  d", False),
    ],
)
def test_expresses_spans_lo_fija_el_conversor(
    conversor: object, entrada: str, expresa: bool
) -> None:
    """Demuestra la regla que no se puede relajar, formato por formato.

    Es una propiedad del FORMATO DE ORIGEN, no del extractor y no del contenido:
    ninguna entrada, por rara que sea, puede hacer que Markdown exprese
    `rowspan`. Así ningún extractor puede declararse capaz de algo que su formato
    no permite, y la suite de conformidad de L5 tiene contra qué contrastarlo.
    """
    tablas = conversor(entrada)  # type: ignore[operator]
    assert [t.expresses_spans for t in tablas] == [expresa]


def test_markdown_no_expresa_spans_ni_aunque_la_entrada_lo_pida() -> None:
    """Demuestra que la regla aguanta la entrada hostil, no sólo la amable.

    Un extractor que emita Markdown con `rowspan` escrito dentro de una celda no
    consigue que su tabla declare que expresa spans. Si lo consiguiera, bastaría
    con escribir la palabra para saltar de `NO_APLICABLE` al estrato titular.
    """
    (t,) = from_markdown('| rowspan="3" | b |\n|---|---|\n| 1 | 2 |')
    assert t.expresses_spans is False
    assert all(c.rowspan == 1 and c.colspan == 1 for c in t.cells)


@settings(max_examples=50)
@given(
    filas=st.integers(min_value=2, max_value=4),
    columnas=st.integers(min_value=2, max_value=4),
    relleno=st.text(alphabet="abc0123,.", min_size=1, max_size=5),
)
def test_ningun_conversor_emite_una_tabla_invalida(filas: int, columnas: int, relleno: str) -> None:
    """**La propiedad que convierte la validación en red de seguridad.**

    Lo que sale de un conversor valida limpio. Sin esto, `validate` sería un
    adorno que nadie ejecuta en el camino real: la detección al 100% se mediría
    sobre tablas de laboratorio mientras el corpus de verdad pasa por otro sitio.

    Las dos primeras aserciones no son decoración: sin ellas, el día que un
    conversor devolviera lista vacía este test recorrería cero tablas y pasaría
    en verde sin comprobar nada. Un bucle vacío es la forma más silenciosa que
    tiene un test de mentir en la dirección tranquilizadora.
    """
    rejilla = [[f"{relleno}{f}{c}" for c in range(columnas)] for f in range(filas)]
    md = "\n".join(
        [
            "| " + " | ".join(rejilla[0]) + " |",
            "|" + "---|" * columnas,
            *("| " + " | ".join(fila) + " |" for fila in rejilla[1:]),
        ]
    )
    txt = "\n".join("   ".join(fila) for fila in rejilla)

    tablas = from_markdown(md) + from_text_heuristic(txt)
    assert len(tablas) == 2, "las dos entradas tienen que producir tabla, o el test no prueba nada"
    for tabla in tablas:
        assert (tabla.n_rows, tabla.n_cols) == (filas, columnas)
        ok, problemas = validate(tabla)
        assert ok is True, problemas
        assert not problemas, "una rejilla completa no tiene ni huecos ni filas vacías"


def test_entrada_vacia_en_los_cinco() -> None:
    """Demuestra el caso degenerado de los cinco, que la regla del núcleo exige.

    Ninguno revienta y ninguno inventa: entrada vacía, cero tablas. Es la
    diferencia entre «no hay tabla» y una excepción que el extractor tendría que
    convertir en `failure_reason`, contaminando la tasa de fallo con algo que no
    es un fallo.
    """
    assert from_html("") == []
    assert from_markdown("") == []
    assert from_tei("") == []
    assert from_text_heuristic("") == []
    assert from_dataframe([]) == []


def test_el_rangeindex_de_camelot_no_se_convierte_en_cabecera() -> None:
    """Demuestra que no se inventa una fila que no está en el documento.

    `camelot.read_pdf(...)[i].df` trae `columns` como `RangeIndex`: las etiquetas
    son `0, 1, 2…` y **no salen del PDF**. Emitirlas como fila de cabecera
    metería una fila de contenido inventada en **todas** las tablas de camelot,
    que es uno de los cuatro extractores de `make quickstart`. Se declara que no
    hay cabecera, que es lo único que de verdad se sabe (LIMITS 36).

    La otra mitad: unas cabeceras `"0"`, `"1"` escritas de verdad en el documento
    son CADENAS, no enteros, y sí se conservan. La distinción es de tipo, no de
    texto, porque si fuera de texto se perdería una cabecera legítima.
    """
    camelot = MarcoFalso([0, 1], [("3", "1.234,56")])
    (t,) = from_dataframe([camelot])
    assert (t.n_rows, t.n_cols) == (1, 2), "sin fila de cabecera inventada"
    assert not any(c.is_header for c in t.cells)
    assert [c.text for c in t.cells] == ["3", "1.234,56"]

    de_verdad = MarcoFalso(["0", "1"], [("3", "1.234,56")])
    (u,) = from_dataframe([de_verdad])
    assert (u.n_rows, u.n_cols) == (2, 2), "cabeceras de texto: se conservan"
    cabecera = u.cell_at(0, 0)
    assert cabecera is not None and cabecera.is_header


def test_una_tabla_seguida_de_texto_se_cierra_donde_toca() -> None:
    """Demuestra el caso NORMAL de la salida de un extractor, que faltaba.

    `pymupdf4llm` y `marker` devuelven un documento entero: párrafos, una tabla,
    más párrafos. Si el bloque no se cerrara al encontrar texto que no es tabla,
    las filas de después entrarían en la tabla o la tabla no saldría. Ningún test
    del hito tenía una tabla **seguida de** texto, que es la forma con la que va a
    llegar el 100% del corpus en L5.
    """
    md = "Antes.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nDespués, y más texto.\n"
    (t,) = from_markdown(md)
    assert (t.n_rows, t.n_cols) == (2, 2)

    txt = "Antes.\n\nGrupo   Base\n3       1,00\n\nDespués.\n"
    (u,) = from_text_heuristic(txt)
    assert (u.n_rows, u.n_cols) == (2, 2)


def test_markdown_sin_fila_de_guiones_no_es_una_tabla() -> None:
    """Demuestra la regla que impide inflar el recuento de tablas del nivel 1.

    GFM exige la fila de guiones. Sin ella, cualquier párrafo con una barra
    vertical —«Sección I | Disposiciones generales»— se convertiría en tabla, y
    el extractor que emite Markdown saldría con tablas de más frente a la verdad.
    """
    assert from_markdown("| Seccion I | Disposiciones |\n| y otra linea | con barra |") == []


def test_html_sin_cerrar_no_pierde_la_tabla() -> None:
    """Demuestra el caso que `cerrar_lo_que_quede` declara y nadie probaba.

    Un `<table>` sin su `</table>` es HTML roto que el navegador pinta igual.
    Descartarlo perdería el documento entero y lo contaría como «sin tablas»,
    que es un número equivocado, no una ausencia de dato.
    """
    (t,) = from_html("<table><tr><td>a</td><td>b</td></tr>")
    assert (t.n_rows, t.n_cols) == (1, 2)
    assert validate(t)[0] is True


def test_celda_sin_fila_se_coloca_igual() -> None:
    """Demuestra el otro caso declarado del colocador: `<td>` sin `<tr>`.

    El HTML tolerante lo permite y los navegadores lo pintan. Si el colocador
    reventara o lo descartara, un documento entero se perdería por una etiqueta
    que falta.
    """
    (t,) = from_html("<table><td>a</td><td>b</td></table>")
    assert (t.n_rows, t.n_cols) == (1, 2)
    assert validate(t)[0] is True
