"""Una rejilla de listas con la superficie de un marco de datos, para `from_dataframe`.

Varias bibliotecas del banco no devuelven un `DataFrame` sino **listas de listas**:
`pdfplumber.Page.extract_tables()` da `list[list[str | None]]`, y lo mismo harán los
extractores de OCR cuando lleguen. `from_dataframe` pide `columns` e `itertuples`, así
que hace falta un adaptador de tres líneas — y hace falta **uno solo**, aquí, porque
escribirlo en cada extractor es escribir cinco veces la misma decisión sobre la cabecera
y equivocarse en una.

**Y la decisión sobre la cabecera es la que importa.** `columns` son enteros 0,1,2… a
propósito: `from_dataframe` los reconoce como un `RangeIndex` y **declara que no hay
cabecera**, que es lo único que de verdad se sabe. Ninguna de estas bibliotecas dice cuál
de sus filas es la cabecera; emitir una la inventaría en cada tabla, y una fila de
contenido convertida en cabecera cambia el árbol que puntúa TEDS.

Esto **no construye una `CanonicalTable`** —lo prohíbe `.claude/rules/extractores.md`—:
le da a `core.canonical` lo que pide y se aparta.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Iterator, Sequence

__all__ = ["Rejilla"]


@dataclass(frozen=True)
class Rejilla:
    """Las filas tal cual las dio la biblioteca. `None` es celda vacía, no hueco."""

    filas: tuple[tuple[str | None, ...], ...]

    @property
    def columns(self) -> Sequence[object]:
        """Posiciones, no nombres: la señal de «esta tabla no trae cabecera»."""
        return list(range(max((len(f) for f in self.filas), default=0)))

    def itertuples(self, index: bool = True) -> Iterator[tuple[object, ...]]:
        """Como `pandas`: con `index=True` el primer elemento es el número de fila.

        Se respeta el `index=True` por defecto aunque `from_dataframe` llame siempre con
        `False`. Un adaptador que ignorara el argumento sería un doble que se comporta
        distinto que el original, y el día que algo lo llame sin argumentos devolvería
        una columna de menos **en silencio**.
        """
        for i, fila in enumerate(self.filas):
            yield (i, *fila) if index else fila
