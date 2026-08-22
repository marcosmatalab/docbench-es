"""§9.1 · `from_text_heuristic`. **`expresses_spans=False`**, y el último recurso.

**Aquí está la frontera de la regla de oro 1.** Este conversor no lee PDF, así
que no es un extractor: convierte la salida de uno. Pero es el juez haciendo
detección de tablas por cuenta del concursante, y eso obliga a que sea
**deliberadamente tonto**:

- Separadores fijos: tabulador o dos o más espacios. Nada de inferir columnas por
  posición de píxel ni por alineación.
- Cero inferencia de fusiones: ninguna celda sale nunca con span > 1.
- **Antes lista vacía que una tabla inventada.** Si las filas no dan el mismo
  número de columnas, no hay tabla.

La declaración de «confianza baja» que pide §9.1 **es `source_format == "text"`**:
ya está en el modelo, es uno de los cinco valores legales de §6.2 y no puede
desincronizarse de nada. No se añade un campo nuevo.

**Orden con la normalización, que importa:** las columnas se parten ANTES de
normalizar. Aquí la anchura del hueco ES la columna, y N4 —el colapso de
espacios— la borraría.
"""

from __future__ import annotations

import re

from docbench_es.core.canonical._normalizar import normalize_cell_text
from docbench_es.types import CanonicalCell, CanonicalTable

COLUMNAS = re.compile(r"\t|[ ]{2,}")
"""Tabulador o dos espacios seguidos. Fijo y declarado, no aprendido."""

MINIMO_FILAS = 2
MINIMO_COLUMNAS = 2


def _bloques(texto: str) -> list[list[list[str]]]:
    bloque: list[list[str]] = []
    salida: list[list[list[str]]] = []
    for linea in texto.splitlines():
        partes = [t for t in COLUMNAS.split(linea.strip()) if t]
        if len(partes) >= MINIMO_COLUMNAS:
            bloque.append(partes)
            continue
        if len(bloque) >= MINIMO_FILAS:
            salida.append(bloque)
        bloque = []
    if len(bloque) >= MINIMO_FILAS:
        salida.append(bloque)
    return salida


def from_text_heuristic(text: str, *, page_span: tuple[int, int] = (1, 1)) -> list[CanonicalTable]:
    """Último recurso para OCR plano. `expresses_spans=False`, confianza baja.

    Caso degenerado declarado: si las filas de un bloque no coinciden en número
    de columnas, **ese bloque no es una tabla** y no se emite. Es la diferencia
    entre no medir y medir mal: una tabla inventada entraría en el recuento de
    tablas del nivel 1 y en TEDS contra una verdad con la que no tiene nada que
    ver.
    """
    tablas: list[CanonicalTable] = []
    for bloque in _bloques(text):
        anchuras = {len(fila) for fila in bloque}
        if len(anchuras) != 1:
            continue  # columnas inconsistentes: antes nada que una tabla inventada
        celdas = tuple(
            CanonicalCell(row=f, col=c, text=normalize_cell_text(texto))
            for f, fila in enumerate(bloque)
            for c, texto in enumerate(fila)
        )
        tablas.append(
            CanonicalTable(
                cells=celdas,
                n_rows=len(bloque),
                n_cols=anchuras.pop(),
                page_span=page_span,
                caption=None,
                expresses_spans=False,
                source_format="text",
            )
        )
    return tablas
