"""§12 · Exactitud celda a celda, y por qué va acompañada de F1.

TEDS no tiene valores intuibles; esto sí. Lo que demuestra este fichero es que
las dos métricas no se solapan y que la de celda no premia al que escupe celdas
de más.

Presupuesto declarado: `max_examples=30`.
"""

from __future__ import annotations

from _estrategias import tabla_completa
from hypothesis import given, settings

from docbench_es.core.canonical import from_html
from docbench_es.core.cellmatch import cell_accuracy, cell_f1, emparejar
from docbench_es.core.teds import teds
from docbench_es.types import CanonicalCell, CanonicalTable

EJEMPLOS = 30
VACIA = CanonicalTable((), 0, 0, (1, 1), None, True, "html")
DOS_POR_DOS = "<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>"


@settings(max_examples=EJEMPLOS)
@given(t=tabla_completa())
def test_una_tabla_contra_si_misma_acierta_todas(t: CanonicalTable) -> None:
    """Demuestra el extremo bueno, y que el emparejado no pierde celdas por el camino."""
    assert cell_accuracy(t, t) == (1.0 if t.cells else None)
    assert cell_f1(t, t) == (1.0 if t.cells else None)


def test_una_celda_desplazada_cuenta_como_fallo() -> None:
    """Demuestra que el emparejado es POR POSICIÓN, que es lo que dice §12.

    No hay alineamiento difuso: una celda con el texto correcto en la columna
    equivocada es un fallo. En una tabla de importes, una columna de más cambia a
    qué concepto pertenece el número, así que darla por buena sería medir otra
    cosa.
    """
    gold = from_html(DOS_POR_DOS)[0]
    celdas = list(gold.cells)
    celdas[3] = CanonicalCell(1, 0, 1, 1, "d")  # 'd' se va encima de 'c'
    movida = CanonicalTable(tuple(celdas), 2, 2, (1, 1), None, True, "html")

    assert cell_accuracy(movida, gold) == 0.75


def test_inventarse_celdas_no_baja_la_exactitud_pero_si_el_f1() -> None:
    """**Por qué se publican las dos.** Demuestra el agujero de la exactitud sola.

    §12 define la exactitud como `correctas / celdas de la verdad`: el
    denominador es la verdad, así que **añadir celdas de más no baja la nota**. Un
    extractor que devolviera la tabla correcta más veinte celdas inventadas
    sacaría la misma exactitud que el que la devuelve limpia.

    El F1 sí lo paga, porque mira también lo que el extractor dijo. Publicar sólo
    la exactitud premiaría al que rellena.
    """
    gold = from_html(DOS_POR_DOS)[0]
    inventadas = tuple(CanonicalCell(2 + i, 0, 1, 1, f"basura {i}") for i in range(20))
    inflada = CanonicalTable((*gold.cells, *inventadas), 22, 2, (1, 1), None, True, "html")

    assert cell_accuracy(inflada, gold) == 1.0, "la exactitud NO lo ve: ése es el punto"
    f1 = cell_f1(inflada, gold)
    assert f1 is not None and f1 < 0.35, "el F1 sí lo ve"


def test_la_verdad_sin_celdas_es_no_aplicable_y_nunca_cero() -> None:
    """Demuestra el caso degenerado de §12, que es una regla del proyecto entera.

    Sin celdas en la verdad no hay denominador. Devolver 0,0 diría que el
    extractor falló todas, y esa confusión es la que ADR-0006 y la regla de oro 4
    persiguen en el nivel 1: **`NO_APLICABLE` no es cero**.
    """
    algo = from_html(DOS_POR_DOS)[0]
    assert cell_accuracy(algo, VACIA) is None
    assert cell_f1(algo, VACIA) is None
    assert cell_accuracy(VACIA, VACIA) is None

    # Y al revés sí hay medición: la verdad tiene celdas y el extractor no dio
    # ninguna. Eso es un cero medido, no un NO_APLICABLE.
    assert cell_accuracy(VACIA, algo) == 0.0


def test_una_celda_repetida_no_cuenta_dos_veces() -> None:
    """Demuestra que el emparejado es de multiconjuntos y no de pertenencia.

    Una tabla con `SOLAPE` puede traer la misma celda dos veces. Si el conteo
    fuera «¿está en la verdad?», esa repetición sumaría dos aciertos sobre una
    sola celda real y la exactitud pasaría de 1. `validate` ya marca el solape
    como fatal, pero la métrica no puede depender de que alguien lo mire.
    """
    gold = from_html(DOS_POR_DOS)[0]
    repetida = CanonicalTable((*gold.cells, gold.cells[0]), 2, 2, (1, 1), None, True, "html")

    resultado = emparejar(repetida, gold)
    assert resultado.aciertos == 4, "cuatro, no cinco"
    assert resultado.en_prediccion == 5
    exactitud = cell_accuracy(repetida, gold)
    assert exactitud is not None and exactitud <= 1.0


def test_la_exactitud_no_puede_pasar_de_uno() -> None:
    """Segundo asesino del emparejado por pertenencia, con datos distintos.

    La tabla de asesinos de `scripts/mutantes/matar.py --tabla` mostró que
    `cellmatch_por_pertenencia` lo mataba **un solo test**: una garantía
    sostenida por una sola aserción. Éste es el segundo, y a propósito usa otra
    forma de tabla y mira otra cosa —la cota superior de la tasa, no el recuento
    de aciertos— para que los dos no se caigan por el mismo motivo.

    Contar pertenencia en vez de multiconjunto hace que una celda repetida sume
    dos aciertos sobre una sola celda real, y entonces `aciertos / celdas de la
    verdad` **pasa de 1**. Una exactitud mayor que 1 no es un número grande: es un
    número imposible, y publicarlo delataría la métrica entera.
    """
    gold = from_html("<table><tr><td>x</td></tr></table>")[0]
    triplicada = CanonicalTable(
        (gold.cells[0], gold.cells[0], gold.cells[0]), 1, 1, (1, 1), None, True, "html"
    )
    exactitud = cell_accuracy(triplicada, gold)
    assert exactitud is not None
    assert exactitud <= 1.0, f"exactitud imposible: {exactitud}"
    assert exactitud == 1.0, "la celda buena sigue contando una vez"


def test_dos_tablas_que_solo_difieren_en_is_header() -> None:
    """**La decisión de `_firma`, fijada en las dos direcciones.**

    `_firma` no mira `is_header`, así que un extractor que se equivoque en TODAS
    las cabeceras saca `cell_accuracy = 1,0`. Dicho solo, eso es un agujero — y
    justo en el hito que descubrió que `is_header` salía mal en el 100% de las
    cabeceras de PubTabNet.

    No lo es porque el fallo **se mide en el otro sitio**: `is_header` decide el
    corte `<thead>`/`<tbody>` (ADR-0021), así que TEDS lo ve. Este test fija las
    dos mitades a la vez, que es lo que lo hace útil: **si alguien mete
    `is_header` en `_firma` se cae por arriba, y si alguien deja de usarlo para
    partir el árbol se cae por abajo.** Cualquiera de los dos cambios convertiría
    la decisión en doble contabilidad o en un agujero de verdad.
    """

    def _tabla(cabecera: bool) -> CanonicalTable:
        return CanonicalTable(
            cells=(
                CanonicalCell(0, 0, text="a", is_header=cabecera),
                CanonicalCell(1, 0, text="b"),
            ),
            n_rows=2,
            n_cols=1,
            page_span=(1, 1),
            caption=None,
            expresses_spans=True,
            source_format="html",
        )

    gold, pred = _tabla(True), _tabla(False)

    assert cell_accuracy(pred, gold) == 1.0, "la celda se transcribió bien: eso es lo que mide"
    assert teds(pred, gold) < 1.0, "y el papel de la celda en la tabla SÍ se penaliza, en TEDS"
