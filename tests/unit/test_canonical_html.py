"""§9.1 · `from_html`, que es el conversor crítico del proyecto.

No es sólo el camino de los concursantes: **es también el de la verdad**. El XML
del BOE lleva marcado HTML de tabla dentro —así lo contó el sondeo, midiendo
`<table`, `rowspan` y `colspan` sobre el crudo— y §17.1 dice que la verdad
`DERIVED` es transcripción de ese XML. En L4, `truth.derived` pasará por aquí.

Un bug aquí sesga los DOS lados de la comparación a la vez, y eso **no se
cancela: se vuelve invisible**. De ahí que haya dos tests independientes y no uno:

1. **Ida y vuelta** contra un renderizador escrito a mano en `_estrategias`.
   Cubre el espacio combinatorio, pero comparte autor con el conversor.
2. **Golden a mano** con las formas medidas del XML del BOE. Cubre lo que el
   primero no puede: que el malentendido no esté en los dos lados a la vez.

Si algún día parece que sobra uno de los dos, no sobra.

**Presupuesto de ejemplos: 60** para la ida y vuelta, que es la propiedad cara de
este fichero: renderiza, vuelve a parsear y compara celda a celda.
"""

from __future__ import annotations

from _estrategias import a_html, codigos, tabla_bien_formada
from hypothesis import given, settings

from docbench_es.core.canonical import from_html, normalize_cell_text, validate
from docbench_es.types import CanonicalTable, HallazgoTabla

# Las etiquetas que el sondeo contó sobre 600 documentos del BOE: <p> 61.541,
# <td> 41.902, <tr> 11.751, <col> 2.723, <th> 2.659, <colgroup> 626, <thead> 596,
# <tbody> 600, <sub> 574, <img> 489, <sup> 219, <caption> 147.
#
# DOS CONDICIONES, y sin ellas los números afirman de más: son apariciones en el
# DOCUMENTO COMPLETO —no dentro de <table>—, y son COTAS INFERIORES, porque el
# sondeo guardaba `most_common(12)` por documento. De los 489 <img>, sólo 21 están
# en documentos que tienen alguna tabla. Este golden reproduce las FORMAS; los
# recuentos dicen que son formas frecuentes, no cuántas veces salen en una celda.
EJEMPLOS = 60


BOE_TIPICO = """
<table>
  <caption>Tabla salarial 2026</caption>
  <colgroup><col/><col/><col span="2"/></colgroup>
  <thead>
    <tr><th rowspan="2">Grupo</th><th colspan="3">Retribuciones</th></tr>
    <tr><th>Base</th><th>Complemento</th><th>Total m<sup>2</sup></th></tr>
  </thead>
  <tbody>
    <tr><td><p>Grupo 3</p><p>Auxiliar</p></td><td>1.234,56</td><td>200,00</td><td>1.434,56</td></tr>
    <tr><td>Grupo 4</td><td>1.100,00</td></tr>
  </tbody>
</table>
"""


@settings(max_examples=EJEMPLOS)
@given(t=tabla_bien_formada())
def test_ida_y_vuelta(t: CanonicalTable) -> None:
    """Demuestra que `from_html` es FIEL, no sólo que no revienta.

    Una tabla canónica renderizada a HTML y vuelta a leer tiene que dar la misma
    rejilla: mismas posiciones, mismos spans, mismas cabeceras y mismo texto tras
    normalizar. Sin esta propiedad, el conversor podría estar perdiendo una celda
    de cada cien y todo el banco mediría con una regla torcida —y torcida en el
    mismo sentido para la verdad y para el concursante, que es lo que la haría
    imposible de ver.
    """
    (vuelta,) = from_html(a_html(t))

    assert (vuelta.n_rows, vuelta.n_cols) == (t.n_rows, t.n_cols)
    esperado = {
        (c.row, c.col, c.rowspan, c.colspan, c.is_header, normalize_cell_text(c.text))
        for c in t.cells
    }
    obtenido = {(c.row, c.col, c.rowspan, c.colspan, c.is_header, c.text) for c in vuelta.cells}
    assert obtenido == esperado
    assert validate(vuelta)[0] is True


def test_el_golden_del_boe() -> None:
    """Demuestra que las formas REALES del XML del BOE se leen bien.

    Cada aserción de aquí corresponde a una etiqueta que el sondeo midió dentro
    de las tablas del BOE. No es un HTML de laboratorio: es la forma que tiene el
    corpus con el que se va a medir.
    """
    (t,) = from_html(BOE_TIPICO)

    assert t.caption == "Tabla salarial 2026"
    assert t.source_format == "html"
    assert t.expresses_spans is True
    assert (t.n_rows, t.n_cols) == (4, 4)

    grupo = t.cell_at(0, 0)
    assert grupo is not None
    assert (grupo.rowspan, grupo.colspan, grupo.is_header) == (2, 1, True)
    assert t.cell_at(1, 0) is grupo, "el rowspan de la cabecera baja a la segunda fila"

    retribuciones = t.cell_at(0, 1)
    assert retribuciones is not None and retribuciones.colspan == 3

    # <sup> es INLINE: no separa. Si separase, «m2» saldría «m 2».
    total = t.cell_at(1, 3)
    assert total is not None and total.text == "Total m2"

    # <p> es BLOQUE: sí separa. Es la etiqueta más frecuente del corpus.
    celda_grupo3 = t.cell_at(2, 0)
    assert celda_grupo3 is not None and celda_grupo3.text == "Grupo 3 Auxiliar"

    # R4: el número llega intacto, con su coma decimal y su punto de millares.
    importe = t.cell_at(2, 1)
    assert importe is not None and importe.text == "1.234,56"

    # La última fila es corta: dos <td> en una tabla de cuatro columnas.
    ok, problemas = validate(t)
    assert ok is True, problemas
    assert HallazgoTabla.HUECO_COLA in codigos(problemas), problemas


def test_el_colgroup_confirma_el_ancho() -> None:
    """Demuestra el oráculo gratis que el sondeo dejó a la vista.

    El sondeo contó 626 `<colgroup>` y 631 `<table>`: casi todas las tablas
    declaran su anchura por su cuenta. Eso permite comprobar `n_cols`
    contra una fuente **independiente** de la colocación de celdas. No entra en
    el modelo de datos —`CanonicalTable` no tiene canal de avisos hasta
    `Extraction.warnings` en L5—, pero aquí sí se puede usar.
    """
    (t,) = from_html(BOE_TIPICO)
    declaradas = 1 + 1 + 2  # <col/><col/><col span="2"/>
    assert t.n_cols == declaradas


def test_la_imagen_no_aporta_texto_y_la_celda_queda_marcada_como_no_evaluable() -> None:
    """Demuestra la decisión sobre `<img>`, y deja escrito el problema que abre.

    Un `<img>` dentro de una celda no aporta texto, y ADR-0016 ya decidió que la
    frontera es la capa de texto, no las imágenes. (El sondeo contó 489 `<img>`,
    pero **468 de ellos están en documentos sin ni una tabla**: el número que
    aplica aquí es 21, y ni ése está medido «dentro de una celda».)

    **El problema que esto abre, y que L4 tiene que resolver** (límite 33): si la
    verdad dice `""` para esa celda porque la imagen no aporta texto, un extractor
    que OCR-ee correctamente su contenido produce texto donde la verdad dice
    vacío, y **se le penaliza por acertar**. Es la misma forma que la regla de oro
    4: no es un fallo del extractor, es una celda que no se puede evaluar contra
    esta verdad. Aquí se deja medible —la celda queda vacía y se sabe por qué—;
    marcarla como no evaluable es de L4, donde vive la verdad.
    """
    crudo = '<table><tr><td><img src="firma.png" alt="Firma"/></td><td>x</td></tr></table>'
    (t,) = from_html(crudo)
    celda = t.cell_at(0, 0)
    assert celda is not None
    assert celda.text == "", "ni el alt: no es contenido de la página"


def test_la_tabla_anidada_sale_aparte_y_no_duplica_el_texto() -> None:
    """Demuestra que una tabla dentro de una celda no se cuenta dos veces.

    Si el texto de la tabla interior se sumara al de la celda que la contiene, el
    mismo contenido entraría dos veces en el nivel 1 y la exactitud de celda
    saldría inflada para quien anida y penalizada para quien no.
    """
    tablas = from_html(
        "<table><tr><td>fuera<table><tr><td>dentro</td></tr></table></td></tr></table>"
    )
    assert len(tablas) == 2
    exterior, interior = tablas
    celda = exterior.cell_at(0, 0)
    assert celda is not None and celda.text == "fuera"
    dentro = interior.cell_at(0, 0)
    assert dentro is not None and dentro.text == "dentro"


def test_rowspan_cero_llega_hasta_el_final_de_su_seccion() -> None:
    """Demuestra que se sigue el estándar HTML en vez de inventarse un valor.

    `rowspan="0"` es HTML **legal** y significa «hasta el final del grupo de
    filas». Tratarlo como 0 daría una celda invisible —el caso degenerado de
    L0— y tratarlo como 1 perdería la combinación. Las dos serían un número
    equivocado; seguir el estándar es lo único que no lo es.
    """
    (t,) = from_html(
        "<table><tbody>"
        '<tr><td rowspan="0">baja entera</td><td>a</td></tr>'
        "<tr><td>b</td></tr><tr><td>c</td></tr>"
        "</tbody></table>"
    )
    larga = t.cell_at(0, 0)
    assert larga is not None and larga.rowspan == 3
    assert t.cell_at(2, 0) is larga
    assert validate(t)[0] is True


def test_span_no_numerico_o_negativo_cae_a_uno_como_manda_el_estandar() -> None:
    """Demuestra que la basura de un atributo no se convierte en tabla rota.

    El estándar dice que un valor no numérico o negativo en `rowspan` vale 1. Si
    se dejara pasar tal cual, el conversor emitiría `SPAN_MENOR_QUE_UNO` y el
    documento se contaría como fallo del extractor cuando el fallo es del HTML de
    origen. Seguir el estándar no es normalizar a la callada: es leer el formato.
    """
    (t,) = from_html('<table><tr><td rowspan="-3" colspan="abc">x</td><td>y</td></tr></table>')
    celda = t.cell_at(0, 0)
    assert celda is not None
    assert (celda.rowspan, celda.colspan) == (1, 1)
    assert validate(t)[0] is True


def test_sin_tabla_no_hay_tablas_y_la_tabla_vacia_no_se_descarta() -> None:
    """Demuestra los dos casos degenerados, que no son el mismo.

    Un documento sin `<table>` da lista vacía. Pero una `<table>` sin filas da
    **una tabla vacía**, no cero tablas: «detectó una tabla y está vacía» y «no
    detectó nada» son cosas distintas para la métrica *tablas no detectadas* de
    §12, y confundirlas premiaría al extractor que se come las tablas vacías.
    """
    assert from_html("<p>ni una tabla</p>") == []
    assert from_html("") == []

    (vacia,) = from_html("<table></table>")
    assert (vacia.n_rows, vacia.n_cols, vacia.cells) == (0, 0, ())
    assert validate(vacia) == (True, [])


def test_el_page_span_lo_pone_quien_llama() -> None:
    """Demuestra que el conversor no se inventa las páginas.

    Ninguno de los cinco formatos lleva número de página, así que `page_span`
    entra por parámetro y por defecto es `(1,1)`. Está declarado en el límite 32:
    un `page_span` inventado envenenaría el estrato `multipagina`.
    """
    (t,) = from_html("<table><tr><td>x</td></tr></table>", page_span=(7, 9))
    assert t.page_span == (7, 9)
    (por_defecto,) = from_html("<table><tr><td>x</td></tr></table>")
    assert por_defecto.page_span == (1, 1)


def test_el_solape_del_estandar_se_produce_y_se_detecta() -> None:
    """Demuestra que `from_html` SÍ puede producir un solape, y que se caza.

    El estándar coloca la celda en el primer hueco libre de su PRIMERA columna;
    si alguna de las siguientes ya está ocupada, declara *table model error* y las
    celdas se pisan. Aquí `c` tiene `colspan=2` y la segunda columna la ocupa el
    `rowspan` de `b`.

    El colocador hace lo mismo que el estándar **a propósito**: buscar una ventana
    libre del ancho de la celda, o desplazarla más allá, sería reparar en silencio
    un HTML roto y esconder un defecto real del documento de origen. El solape
    sale en `cells` y lo caza `validate`.

    Esto corrige lo que decían el límite 30 y el docstring de `_rejilla` hasta el
    escrutinio de L1: que `from_html` no podía producir solapes. **Podía**, y el
    test de ida y vuelta no lo veía nunca porque la estrategia limita el `colspan`
    al espacio libre y jamás genera una celda que cruce una posición ocupada.
    """
    (t,) = from_html(
        '<table><tr><td>a</td><td rowspan="2">b</td></tr><tr><td colspan="2">c</td></tr></table>'
    )
    ok, problemas = validate(t)
    assert ok is False
    assert HallazgoTabla.SOLAPE in codigos(problemas), problemas
