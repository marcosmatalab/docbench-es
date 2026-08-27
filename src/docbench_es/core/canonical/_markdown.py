"""§9.1 · `from_markdown`. **`expresses_spans=False` SIEMPRE.**

Markdown no tiene `rowspan` ni `colspan`. No es una limitación de esta
implementación: es del formato, y por eso la decisión la toma el conversor y no
el extractor. ADR-0006 lo dice al derecho —convertir Markdown a HTML pierde las
celdas combinadas por completo— y de ahí sale que pymupdf4llm y marker salgan
`NO_APLICABLE` en el estrato de celdas combinadas, no cero.

Se leen tablas GFM: una fila de cabecera, una fila de guiones, y las que sigan.
La fila de guiones es OBLIGATORIA, como en GFM. Sin ella, cualquier párrafo con
una barra vertical se convertiría en tabla y el recuento de tablas del nivel 1
saldría inflado para quien emite Markdown.

## El conversor devuelve EL TEXTO de la celda, no su fuente

`**x**` **es** el texto `x` con énfasis, igual que en HTML `<b>x</b>` **es** el
texto `x`. El marcado es presentación, no contenido, y quitarlo no es una
normalización nueva: es **extraer el texto**, que es lo que hace un conversor.

**Y hacía falta quitar una asimetría, no añadir una regla.** `from_html` lo lleva
haciendo desde L1 —lee el texto del nodo, así que `<b>` desaparece solo y `<br>`
sale como un espacio— y esto no lo hacía. Medido con el primer consumidor real de
este conversor, `pymupdf4llm`: **116 de 594 celdas (19,5%)** llegaban con marcado
dentro, contra una verdad congelada que dice `Número` donde esto decía
`**Número**`. Quitando el marcado son **idénticas**: la extracción era perfecta y
la penalización era de aquí.

Eso es un **sesgo sistemático entre familias** —quien emite HTML cobraba texto
limpio gratis y quien emite Markdown cobraba un cero por el formato de su
salida—, que es el mismo animal que un `expresses_spans` que miente, una capa más
abajo. Por eso se arregla en el conversor y **nunca** en el extractor: allí sería
normalizar a favor de uno. Ver LIMITS 103.

**Lo que se reconoce está enumerado en `INLINE`, y lo que no, también.** Un
conversor que dice «quito el marcado» sin decir cuál es un conversor que no se
puede auditar.
"""

from __future__ import annotations

import re

from docbench_es.core.canonical._normalizar import normalize_cell_text
from docbench_es.types import CanonicalCell, CanonicalTable

SEPARADOR = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")
"""La fila de guiones de GFM, con o sin barras en los extremos y con alineación."""


INLINE: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("salto de línea", re.compile(r"<br\s*/?>", re.IGNORECASE), " "),
    ("imagen", re.compile(r"!\[([^\]]*)\]\([^)]*\)"), r"\1"),
    ("enlace", re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),
    ("código", re.compile(r"`+([^`]*)`+"), r"\1"),
    ("negrita", re.compile(r"(?<!\w)(\*\*|__)(?=\S)(.+?)(?<=\S)\1(?!\w)"), r"\2"),
    ("énfasis", re.compile(r"(?<![*_\w])([*_])(?=\S)([^*_]+?)(?<=\S)\1(?![*_\w])"), r"\2"),
    ("escape", re.compile(r"\\([\\`*_{}\[\]()#+\-.!|])"), r"\1"),
)
r"""Los constructos inline que este conversor reconoce, **en el orden en que se aplican**.

El orden no es cosmético: `<br>` va primero porque puede estar DENTRO de una negrita
—`**Hito/<br>Objetivo**`—, y la imagen antes que el enlace porque `![alt](src)` contiene
un `[alt](src)`.

**Lo que NO se reconoce, y se dice en vez de suponerse:**

* **el énfasis pegado a una palabra** —`a**b**`— se deja TAL CUAL, entero. GFM sí lo
  marcaría con `*`, pero los guardias protegen el caso caro: un asterisco de nota al pie o
  un `snake_case` convertidos en contenido alterado **en silencio**. De los dos errores
  posibles, no quitar marcado **penaliza y se ve**; quitar contenido **corrompe y no se
  ve**. Se elige el visible. El guardia de énfasis mira además que el delimitador no toque
  otro delimitador: sin eso, `a**b**` salía `a*b*`, que es lo peor de los dos mundos
  —marcado a medias Y contenido tocado—;
* **etiquetas HTML que no sean `<br>`**. Markdown las admite y `pymupdf4llm` no las emite;
  el día que un extractor las traiga, se añade aquí con su caso;
* **énfasis anidado o cruzado** —`**a *b* c**` sale bien, `*a **b* c**` no—. Implementar
  las reglas de énfasis de GFM enteras es un parser, y esto no lo es.
"""


def texto_de_celda(bruto: str) -> str:
    """El texto de una celda de Markdown: sin marcado y ya normalizado.

    Pública porque es la mitad del contrato de este conversor —qué considera «texto»— y
    lo que compara el test de paridad con `from_html`.
    """
    fuera = bruto
    for _, patron, reemplazo in INLINE:
        fuera = patron.sub(reemplazo, fuera)
    return normalize_cell_text(fuera)


def _celdas_de(linea: str) -> list[str]:
    """Parte una fila por `|`. **No hay escapado de `\\|`**, declarado en LIMITS 34."""
    limpia = linea.strip()
    if limpia.startswith("|"):
        limpia = limpia[1:]
    if limpia.endswith("|"):
        limpia = limpia[:-1]
    return [texto_de_celda(t) for t in limpia.split("|")]


def _bloques(texto: str) -> list[list[str]]:
    bloque: list[str] = []
    salida: list[list[str]] = []
    for linea in texto.splitlines():
        if "|" in linea:
            bloque.append(linea)
            continue
        if len(bloque) >= 2:
            salida.append(bloque)
        bloque = []
    if len(bloque) >= 2:
        salida.append(bloque)
    return salida


def from_markdown(md: str, *, page_span: tuple[int, int] = (1, 1)) -> list[CanonicalTable]:
    """Las tablas GFM del texto. `expresses_spans=False` pase lo que pase.

    Caso degenerado: sin fila de guiones no hay tabla, y la lista sale vacía. Una
    fila con menos celdas que la cabecera deja **huecos de cola**, no celdas
    vacías: rellenarlas sería decidir por el extractor, y hueco y celda vacía son
    árboles distintos para TEDS.
    """
    tablas: list[CanonicalTable] = []
    for bloque in _bloques(md):
        if not SEPARADOR.match(bloque[1]):
            continue
        filas = [_celdas_de(bloque[0]), *(_celdas_de(ln) for ln in bloque[2:])]
        celdas = tuple(
            CanonicalCell(row=f, col=c, text=texto, is_header=f == 0)
            for f, fila in enumerate(filas)
            for c, texto in enumerate(fila)
        )
        tablas.append(
            CanonicalTable(
                cells=celdas,
                n_rows=len(filas),
                n_cols=max((len(f) for f in filas), default=0),
                page_span=page_span,
                caption=None,
                expresses_spans=False,
                source_format="markdown",
            )
        )
    return tablas
