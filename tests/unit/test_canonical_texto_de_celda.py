"""Qué considera cada conversor «el texto de una celda», **y que los dos digan lo mismo**.

La asimetría que este fichero cierra costó el 19,5% de las celdas de un extractor de la
campaña (LIMITS 103): `from_html` lee el **texto del nodo** —un `<b>` desaparece solo, un
`<br>` sale como espacio— y `from_markdown` leía **la fuente**, así que el `**` se quedaba
dentro. El mismo contenido en dos formatos daba dos textos canónicos distintos.

Y no era un detalle de formato: **la penalización caía sobre el extractor**. Quien emite
HTML cobraba texto limpio gratis; quien emite Markdown cobraba un cero por el formato de
su salida. Es el mismo animal que un `expresses_spans` que miente —una comparación amañada
sin querer— una capa más abajo.

**El test que importa es el de paridad**: mismo contenido, los dos formatos, mismo texto.
Los demás son el desglose de qué se reconoce, y sobre todo **de qué NO** — porque de los
dos errores posibles, no quitar marcado penaliza y se ve, y quitar contenido corrompe y no
se ve.
"""

from __future__ import annotations

import pytest

from docbench_es.core.canonical import from_html, from_markdown
from docbench_es.core.canonical._markdown import INLINE, texto_de_celda

# (contenido en Markdown, el mismo contenido en HTML)
PAREJAS = [
    ("**Numero**", "<b>Numero</b>"),
    ("__Numero__", "<strong>Numero</strong>"),
    ("*a*", "<em>a</em>"),
    ("_a_", "<i>a</i>"),
    ("Hito/<br>Objetivo", "Hito/<br>Objetivo"),
    ("`c`", "<code>c</code>"),
    ("[t](http://u)", '<a href="http://u">t</a>'),
    ("sin marcado", "sin marcado"),
]


def _celda_html(interior: str) -> str:
    return from_html(f"<table><tr><td>{interior}</td></tr></table>")[0].cells[0].text


@pytest.mark.parametrize(("md", "html"), PAREJAS)
def test_los_dos_conversores_dicen_lo_mismo_del_mismo_contenido(md: str, html: str) -> None:
    """**La afirmación entera de este fichero.** Si esto se rompe, vuelve el sesgo entre
    familias: el mismo documento puntúa distinto según el formato que emita el extractor."""
    assert texto_de_celda(md) == _celda_html(html)


def test_contra_las_cadenas_exactas_de_la_verdad_congelada() -> None:
    """No contra una forma inventada aquí: contra lo que dice `BOE-A-2026-7446-t0`, cuyo
    fixture declara *«el texto se copia tal como se ve»*."""
    assert texto_de_celda("**Número**") == "Número"
    assert texto_de_celda("**Hito/**<br>**Objetivo**") == "Hito/ Objetivo"
    assert (
        texto_de_celda("**Indicadores cualitativos para**<br>**los hitos**")
        == "Indicadores cualitativos para los hitos"
    )


@pytest.mark.parametrize(
    "bruto",
    ["snake_case_name", "2*3*4", "a**b**", "nota al pie *", "10 * 4 = 40", "__ __"],
)
def test_lo_que_no_se_toca_no_se_toca(bruto: str) -> None:
    """**El control en la dirección cara.** Un asterisco de nota al pie o un `snake_case`
    convertidos en contenido alterado no los ve nadie; el marcado que se queda, sí.

    `a**b**` entra aquí por una razón medida: sin el guardia que mira que un delimitador
    no toque otro, salía `a*b*` — lo peor de los dos mundos, marcado a medias **y**
    contenido tocado.
    """
    assert texto_de_celda(bruto) == bruto


def test_el_marcado_anidado_que_si_se_reconoce() -> None:
    """`**a *b* c**` es el caso que el orden de `INLINE` sí resuelve: negrita antes que
    énfasis. El cruzado no, y está declarado en `INLINE`."""
    assert texto_de_celda("**a *b* c**") == "a b c"


def test_el_escape_de_barra_se_deshace() -> None:
    """`\\|` es la forma GFM de meter una barra en una celda. LIMITS 34 dice que la
    PARTICIÓN por `|` no la respeta; el texto sí la deshace."""
    assert texto_de_celda(r"x \| y") == "x | y"


def test_la_tabla_de_constructos_no_esta_vacia_y_se_puede_enumerar() -> None:
    """El denominador del conversor: **cuántos constructos dice reconocer**. Sin esto, un
    `INLINE` vaciado por accidente dejaría todos los tests de arriba en verde salvo uno."""
    nombres = [n for n, _, _ in INLINE]
    assert len(nombres) == len(set(nombres)) >= 7, nombres
    assert nombres[0] == "salto de línea", "el <br> va primero: puede estar DENTRO de una negrita"
    assert nombres.index("imagen") < nombres.index("enlace"), "![alt](src) contiene [alt](src)"
    assert nombres.index("negrita") < nombres.index("énfasis"), "** antes que *"


def test_una_tabla_entera_pasa_por_el_mismo_camino() -> None:
    """Que `from_markdown` USE `texto_de_celda`, y no que exista y nadie la llame."""
    tabla = from_markdown("|**a**|`b`|\n|---|---|\n|[c](u)|d<br>e|")[0]
    assert [x.text for x in tabla.cells] == ["a", "b", "c", "d e"]
