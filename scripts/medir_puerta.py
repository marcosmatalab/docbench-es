"""Mide la puerta como manda ADR-0022: 40 corridas en frío, 10 tandas de 4.

Existe para que el protocolo de medición sea **una orden y no una costumbre**. La
diferencia importa: dos tandas de L2 dieron medianas de 5440 y 5473 con rangos que
no se solapaban del todo, así que el número depende de cuántas corridas y de si
se limpió la caché. Un protocolo que cada uno recuerda a su manera produce cifras
que no se pueden comparar entre hitos, y la serie de la puerta es justo una
comparación entre hitos.

    uv run python scripts/medir_puerta.py            # 10 tandas de 4
    uv run python scripts/medir_puerta.py --techo 8500
    echo $?                                          # 1 si el p90 pasa del techo

**Comprueba el código de salida de cada corrida y descarta la que falla.** `make`
para en el primer paso que falla, así que una puerta rota da un tiempo MENOR: sin
esta comprobación, un fallo se publicaría como una mejora. Pasó en L1, con una
tanda entera de 60 ms que era `ruff` en rojo.

**Lo que este script NO puede hacer**, y por eso ADR-0022 lo dice en voz alta: no
se ejecuta solo. El paso mecánico de verdad es el aviso de CI, que sale en cada
PR sin que nadie decida ejecutarlo.
"""

from __future__ import annotations

import argparse
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CACHES = (
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".import_linter_cache",
    "htmlcov",
)


def _en_frio() -> None:
    """Borra TODAS las cachés, incluida `.hypothesis`.

    `.hypothesis` no es una caché de velocidad: guarda lo ya explorado, así que
    una corrida en caliente **busca menos**. Medir en frío es lo único que hace
    comparables dos corridas, y de paso es lo que destapó la regresión de U+2028.
    """
    for nombre in CACHES:
        shutil.rmtree(RAIZ / nombre, ignore_errors=True)
    (RAIZ / ".coverage").unlink(missing_ok=True)


def _carga() -> float:
    """`load average` de 1 minuto. Sale de la deuda que dejaron cinco tandas.

    La desviacion tipica de este mismo protocolo ha ido **134, 76, 286, 73 y 359** entre tandas, y
    ninguna de esas variaciones se pudo explicar porque **nadie registró el estado
    de la máquina**. Sin esta columna, la respuesta a «¿por qué se movió?» es
    siempre «no se sabe», y eso ya se ha escrito cuatro veces.
    """
    try:
        return os.getloadavg()[0]
    except OSError:
        return float("nan")


def _una_corrida() -> tuple[int, int, float]:
    _en_frio()
    carga = _carga()
    inicio = time.monotonic_ns()
    resultado = subprocess.run(
        ["make", "fast"], cwd=RAIZ, capture_output=True, text=True, check=False
    )
    return (time.monotonic_ns() - inicio) // 1_000_000, resultado.returncode, carga


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--tandas", type=int, default=10)
    partes.add_argument("--por-tanda", type=int, default=4)
    partes.add_argument("--techo", type=int, default=8500, help="techo local de ADR-0022")
    args = partes.parse_args()

    todas: list[int] = []
    cargas: list[float] = []
    medianas: list[float] = []
    descartadas = 0
    for tanda in range(1, args.tandas + 1):
        fila: list[int] = []
        for _ in range(args.por_tanda):
            ms, rc, carga = _una_corrida()
            cargas.append(carga)
            if rc == 0:
                fila.append(ms)
                todas.append(ms)
            else:
                descartadas += 1
        if fila:
            medianas.append(statistics.median(fila))
        print(f"  tanda {tanda:>2}: {fila}")

    if not todas:
        print("NINGUNA corrida en verde: no hay medición, no hay número.")
        return 1

    ordenadas = sorted(todas)
    p90 = ordenadas[min(len(ordenadas) - 1, int(0.90 * len(ordenadas)))]
    print(
        f"\n  n={len(todas)} en verde · descartadas por rc!=0: {descartadas}\n"
        f"  mínimo {ordenadas[0]} · mediana {statistics.median(ordenadas):.0f} · "
        f"p90 {p90} · máximo {ordenadas[-1]}\n"
        f"  desviación típica {statistics.stdev(ordenadas):.0f} · "
        f"medianas por tanda {int(min(medianas))}-{int(max(medianas))}\n"
        f"  carga de la máquina: mediana {statistics.median(cargas):.2f} · "
        f"rango {min(cargas):.2f} a {max(cargas):.2f}\n"
        f"  techo {args.techo} · margen en el p90: {args.techo - p90} ms"
    )
    if p90 > args.techo:
        print("EL P90 PASA DEL TECHO. Ver ADR-0022: re-justificar o reestructurar.")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
