"""§6.2 + §9.2 · Cómo puntúa TEDS un HUECO frente a una CELDA VACÍA.

Es el segundo riesgo de diseño de L2, y la razón de que fuera un riesgo: en L1 se
decidió que **un hueco no es una celda vacía** (ADR-0018) y se dejó `holes()` como
función pública diciendo que L2 la consumiría. Había que comprobar las dos mitades
de esa afirmación, y sólo una se sostiene.

**La distinción SÍ existe en TEDS, y está medida contra la referencia.** Un hueco
es un `<td>` que no está en el árbol; una celda vacía es un `<td>` presente con
contenido vacío. Son árboles distintos y puntúan distinto.

**Pero `core.teds` NO llama a `holes()`, y hay que decirlo en voz alta.** El árbol
se construye recorriendo las celdas que originan en cada fila, así que un hueco no
es un nodo que haya que omitir: es un nodo que nunca existió. La distinción se
respeta por construcción. `holes()` sigue siendo útil —`validate` declara los
huecos, y L4 y L5 los necesitan para el informe—, pero la frase de L1 «lo que L2
usa para emitir celda ausente» era optimista y queda corregida aquí y en ADR-0018.
"""

from __future__ import annotations

import ast
from pathlib import Path

from docbench_es.core.canonical import from_html, holes
from docbench_es.core.teds import teds, teds_struct

# Tres tablas que sólo se diferencian en la última celda de la última fila.
COMPLETA = (
    "<table><tbody><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></tbody></table>"
)
CON_HUECO = "<table><tbody><tr><td>a</td><td>b</td></tr><tr><td>c</td></tr></tbody></table>"
CON_VACIA = (
    "<table><tbody><tr><td>a</td><td>b</td></tr><tr><td>c</td><td></td></tr></tbody></table>"
)


def test_el_hueco_y_la_celda_vacia_no_son_la_misma_tabla() -> None:
    """Demuestra que la distinción de L1 existe de verdad en la forma canónica."""
    hueco, vacia = from_html(CON_HUECO)[0], from_html(CON_VACIA)[0]
    assert holes(hueco) == ((1, 1),)
    assert holes(vacia) == ()
    assert len(vacia.cells) == len(hueco.cells) + 1


def test_teds_s_distingue_hueco_de_celda_vacia() -> None:
    """**La demostración que pedía el riesgo 2**, con los dos números.

    Contra la misma tabla completa, en TEDS-S:

    - la que trae una **celda vacía** puntúa **1,000000**: ignorado el contenido,
      una celda vacía es idéntica a una llena y la rejilla es la misma;
    - la que trae un **hueco** puntúa **0,857143**: le falta un nodo, y eso no lo
      tapa ignorar el contenido.

    Los dos valores están comprobados contra la implementación de referencia de
    PubTabNet, no calculados sólo aquí.
    """
    completa, hueco, vacia = (from_html(h)[0] for h in (COMPLETA, CON_HUECO, CON_VACIA))

    assert round(teds_struct(vacia, completa), 6) == 1.0
    assert round(teds_struct(hueco, completa), 6) == 0.857143
    assert teds_struct(hueco, completa) < teds_struct(vacia, completa)


def test_teds_completo_los_distingue_cuando_el_hueco_esta_en_la_verdad() -> None:
    """Demuestra que en TEDS completo la distinción también existe, pero al revés.

    Contra la tabla COMPLETA los dos dan 0,857143, y no por casualidad: borrar un
    nodo cuesta 1, y renombrar una celda vacía a una con texto también cuesta 1
    porque la distancia va normalizada. Los dos costes coinciden, así que el
    número coincide.

    La distinción aparece cuando **la verdad es la que tiene el hueco**, que es el
    caso real: el BOE trae filas cortas. Ahí el extractor que reproduce el hueco
    saca 1,0 y el que rellena con una celda vacía paga por la celda de más.
    Si TEDS no los separase, un extractor podría rellenar todas las filas cortas
    con celdas vacías y no pagar nada por inventarse contenido.
    """
    hueco, vacia = from_html(CON_HUECO)[0], from_html(CON_VACIA)[0]

    assert teds(hueco, hueco) == 1.0
    assert round(teds(vacia, hueco), 6) == 0.857143
    assert teds(vacia, hueco) < teds(hueco, hueco)


def test_core_teds_no_llama_a_holes() -> None:
    """Demuestra en código la corrección a la justificación de L1.

    `holes()` no aparece en `core.teds`. El árbol nace de las celdas que originan
    en cada fila y el hueco es la ausencia de un nodo, así que la distinción no
    necesita la función. Este test existe para que la afirmación de L1 —«es lo que
    L2 usa»— no se quede escrita en tres sitios siendo falsa.
    """
    # Por AST y no buscando la cadena "holes(": el docstring de `_arbol` explica
    # justamente por qué NO hace falta, así que un `grep` daría positivo sobre la
    # prosa que dice lo contrario de lo que se busca. Un chequeo por texto sobre
    # código es un chequeo que mide el comentario.
    raiz = Path(__file__).resolve().parents[2] / "src" / "docbench_es" / "core" / "teds"
    llamadas: list[str] = []
    for modulo in sorted(raiz.glob("*.py")):
        arbol = ast.parse(modulo.read_text(encoding="utf-8"))
        llamadas += [
            n.func.id
            for n in ast.walk(arbol)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        ]
    assert "holes" not in llamadas, f"core.teds llama a holes(): {llamadas}"
