"""§6.2 · La forma canónica de tabla.

Es el único formato sobre el que se calcula TEDS: ningún extractor compara
contra su propio formato nativo. Y `expresses_spans` lo fija el CONVERSOR
según el formato de origen, nunca el extractor, porque un extractor no puede
declararse capaz de algo que su formato no permite (ADR-0006).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalCell:
    """Una celda, con su rectángulo. `row`/`col` son la esquina superior izquierda."""

    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    text: str = ""
    is_header: bool = False


@dataclass(frozen=True)
class CanonicalTable:
    """Una tabla en forma canónica.

    `expresses_spans=False` es lo que hace que un extractor salga NO_APLICABLE
    en las métricas de celda combinada, en vez de salir cero. Un cero diría que
    lo intentó y falló; NO_APLICABLE dice que su formato no puede expresarlo.
    """

    cells: tuple[CanonicalCell, ...]
    n_rows: int
    n_cols: int
    page_span: tuple[int, int]
    caption: str | None
    expresses_spans: bool
    source_format: str

    def cell_at(self, row: int, col: int) -> CanonicalCell | None:
        """La celda que CUBRE la posición (row, col), contando sus spans.

        Casos degenerados, declarados a propósito porque L1 construye sus
        invariantes encima:

        - Fuera de rango, o hueco sin cubrir: devuelve `None`.
        - Si dos celdas solapan —una tabla mal formada—, devuelve la PRIMERA
          en el orden de `cells`. No arregla el solape ni lo esconde: quien
          detecta y reporta solapes es `is_wellformed()`.
        - **`rowspan` o `colspan` menor que 1**: la celda no cubre ninguna
          posición, así que es invisible para `cell_at` y toda consulta sobre
          ella devuelve `None`, igual que un hueco. NO se normaliza a 1 a la
          callada: un span de 0 es una tabla mal formada, y silenciarlo aquí
          convertiría un error del conversor en una tabla plausible que TEDS
          puntuaría como si fuera buena. Quien tiene que reportarlo es
          `is_wellformed()`, en L1.
        """
        for cell in self.cells:
            if (
                cell.row <= row < cell.row + cell.rowspan
                and cell.col <= col < cell.col + cell.colspan
            ):
                return cell
        return None

    def is_wellformed(self) -> tuple[bool, list[str]]:
        """Solapes, huecos y spans fuera de rango. Devuelve los problemas.

        Lo implementa **L1**, con sus tests de propiedad de `hypothesis`. En L0
        levanta `NotImplementedError` a propósito: devolver `(True, [])` haría
        pasar en verde a cualquier tabla, y el criterio de L1 es justo que las
        tablas rotas se detecten al 100%.
        """
        raise NotImplementedError("core.canonical, hito L1")
