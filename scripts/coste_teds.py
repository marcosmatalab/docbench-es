"""Cuánto cuesta un `teds()` según el tamaño de la tabla. Ver `LIMITS.md` 42.

Zhang-Shasha es O(n²·d²) en el peor caso, y `_distancia.py` afirmaba que «para una
tabla de documento es inmediato» y que el coste sólo se dispara con «miles de
filas». **No estaba medido, y es falso**: a 100x10 un solo par cuesta segundos, y
el sondeo del BOE midió `rowspan` de hasta 33, o sea que las tablas grandes no son
hipotéticas.

Importa para L5, que multiplica esto por ocho extractores y miles de tablas.

    uv run python scripts/coste_teds.py
    uv run python scripts/coste_teds.py --repeticiones 5
"""

from __future__ import annotations

import argparse
import statistics
import time

from docbench_es.core.teds import teds
from docbench_es.types import CanonicalCell, CanonicalTable

FORMAS = ((10, 5), (20, 8), (40, 8), (60, 10), (80, 10), (100, 10))


def _tabla(filas: int, columnas: int) -> CanonicalTable:
    return CanonicalTable(
        cells=tuple(
            CanonicalCell(f, c, text=f"{f}-{c}") for f in range(filas) for c in range(columnas)
        ),
        n_rows=filas,
        n_cols=columnas,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--repeticiones", type=int, default=3)
    args = partes.parse_args()

    print(f"{'tabla':>10}{'celdas':>9}{'mediana':>12}   (n={args.repeticiones}, mismo par)")
    for filas, columnas in FORMAS:
        a, b = _tabla(filas, columnas), _tabla(filas, columnas)
        muestras = []
        for _ in range(args.repeticiones):
            inicio = time.monotonic_ns()
            teds(a, b)
            muestras.append((time.monotonic_ns() - inicio) / 1_000_000)
        mediana = statistics.median(muestras)
        print(f"{filas:>6}x{columnas:<3}{filas * columnas:>9}{mediana:>10.0f} ms")
    print("\nNo es una estimación: son tiempos, con su n y su resolución (ms). ADR-0015.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
