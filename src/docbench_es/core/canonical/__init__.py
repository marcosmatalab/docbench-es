"""§9.1 · `core.canonical` — la forma canónica. Puro: entra texto, sale tabla.

**Paquete y no fichero.** §8 lo dibuja como `canonical.py`, pero cinco conversores
más la validación más la normalización no caben en las 300 líneas que manda
`CLAUDE.md`. Se parte por el mismo motivo y con el mismo precedente que `types`
(ADR-0013), y la superficie de import no cambia: `from docbench_es.core.canonical
import from_html` es exactamente lo que dice §9.1.

**`from_html` no es sólo el camino de los concursantes: es también el de la
verdad.** El XML del BOE lleva marcado HTML de tabla dentro —`<table>`, `<td>`,
`rowspan`—, y §17.1 dice que la verdad `DERIVED` es transcripción de ese XML. En
L4, `truth.derived` pasará por este mismo conversor. Un bug aquí sesga los DOS
lados de la comparación a la vez, y eso no se cancela: se vuelve invisible. Es la
razón de que `from_html` lleve dos tests independientes —ida y vuelta contra un
renderizador de test, y golden escritos a mano con las formas reales del BOE— en
lugar de uno. Si algún día parece que sobra uno de los dos, no sobra.

**`expresses_spans` lo fija el conversor, nunca el extractor.** Es la regla que
no se relaja de §9.1: un extractor no puede declararse capaz de algo que su
formato no permite. `validate()` la hace cumplir en las dos direcciones y la
suite de conformidad de L5 la usa para cazar al que miente.
"""

from __future__ import annotations

from docbench_es.core.canonical._dataframe import MarcoDeDatos, from_dataframe
from docbench_es.core.canonical._html import from_html
from docbench_es.core.canonical._markdown import from_markdown
from docbench_es.core.canonical._normalizar import (
    NORMALIZACIONES,
    Normalizacion,
    normalize_cell_text,
)
from docbench_es.core.canonical._tei import from_tei
from docbench_es.core.canonical._texto import from_text_heuristic
from docbench_es.types import CanonicalTable

__all__ = [
    "NORMALIZACIONES",
    "MarcoDeDatos",
    "Normalizacion",
    "from_dataframe",
    "from_html",
    "from_markdown",
    "from_tei",
    "from_text_heuristic",
    "holes",
    "normalize_cell_text",
    "validate",
]


def validate(t: CanonicalTable) -> tuple[bool, list[str]]:
    """Los invariantes de §6.2. `ok=False` sólo si hay algún hallazgo FATAL.

    Delega en `CanonicalTable.is_wellformed()`, que es donde vive el algoritmo:
    el contrato de capas prohíbe que `types` importe `core`, así que la única
    manera de que §6.2 y §9.1 tengan las dos su función sin duplicar la lógica es
    ésta. Ver ADR-0019.

    Y delega en el MÉTODO, no en `types._invariantes`: `docbench_es.types` es la
    única superficie de import del modelo de datos (ADR-0013) y hay un test de L0
    que lo hace cumplir. Importar el submódulo privado convertiría su reparto
    interno en API.
    """
    return t.is_wellformed()


def holes(t: CanonicalTable) -> tuple[tuple[int, int], ...]:
    """Las posiciones sin cubrir, en orden de fila y columna.

    Es la mitad ejecutable del «o declara los huecos» de §6.2 (ADR-0018). Un
    hueco **no es una celda vacía**, y L2 necesita la diferencia para emitir
    celda ausente en vez de celda vacía: son árboles distintos y TEDS los puntúa
    distinto.

    Misma definición de «cubrir» que `cell_at`, calculada de una pasada sobre las
    celdas en vez de una consulta por posición: L2 la llama una vez por tabla y
    con `colspan` de hasta 33 la diferencia entre O(celdas + area) y
    O(celdas por area) se nota. Un test afirma que las dos derivaciones coinciden.
    """
    # Recortado a la tabla, y no es una optimización: sin el recorte, una celda
    # con `rowspan="65534" colspan="1000"` —60 bytes de HTML— materializaba 65
    # millones de tuplas, 28 s y 7,5 GB, para una rejilla de 1x1000. Una posición
    # fuera de la tabla no puede ser un hueco de la tabla, así que no aporta nada.
    cubierto = {
        (fila, col)
        for celda in t.cells
        for fila in range(max(celda.row, 0), min(celda.row + celda.rowspan, t.n_rows))
        for col in range(max(celda.col, 0), min(celda.col + celda.colspan, t.n_cols))
    }
    return tuple(
        (fila, col)
        for fila in range(t.n_rows)
        for col in range(t.n_cols)
        if (fila, col) not in cubierto
    )
