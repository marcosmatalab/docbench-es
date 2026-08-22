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
"""

from __future__ import annotations

import re

from docbench_es.core.canonical._normalizar import normalize_cell_text
from docbench_es.types import CanonicalCell, CanonicalTable

SEPARADOR = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")
"""La fila de guiones de GFM, con o sin barras en los extremos y con alineación."""


def _celdas_de(linea: str) -> list[str]:
    """Parte una fila por `|`. **No hay escapado de `\\|`**, declarado en LIMITS 34."""
    limpia = linea.strip()
    if limpia.startswith("|"):
        limpia = limpia[1:]
    if limpia.endswith("|"):
        limpia = limpia[:-1]
    return [normalize_cell_text(t) for t in limpia.split("|")]


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
