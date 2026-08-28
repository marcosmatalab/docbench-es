"""Las DOS contabilidades de la suite, con sus porcentajes y en un solo sitio.

    uv run python scripts/contabilidades.py

**Por qué existe, y es una razón concreta y no de comodidad.** El criterio
pre-registrado de la deuda 7 de `ESTADO.md` decía *«L5 es el primero que puede subir
el arnés en vez de bajarlo»* sin nombrar **cuál** de las dos columnas, y en L5 las dos
fueron en direcciones opuestas: el recuento subió y la fracción bajó. Un criterio que
no nombra su columna no es un criterio (LIMITS 110), y un criterio que la nombra
necesita **un comando que la calcule**, o vuelve a depender de que alguien reconstruya
el número a mano.

**No hay segunda implementación, y eso es el punto.** Esto llama a `recuentos()` de
`tests/unit/conftest.py`, que es donde vive el cálculo y que corre en cada colección.
Copiar aquí la aritmética crearía la cuarta copia que ese `conftest` existe para
evitar; lo único que se añade son los dos porcentajes, que no están almacenados en
ningún sitio porque se derivan.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def porcentaje(parte: int, total: int) -> str:
    """`n/a` cuando no hay denominador. **Un 0,0% diría que se midió y salió cero.**"""
    return "n/a" if total <= 0 else f"{100 * parte / total:.1f}%".replace(".", ",")


def lineas(cuenta: dict[str, int]) -> list[str]:
    """Las dos contabilidades, en el orden en que hay que leerlas.

    Primero el arnés —lo que mide un mutante— y después la protección real —lo que
    mide un mutante **o** un control negativo en el propio fichero—. Publicar sólo la
    primera exagera el hueco; publicar sólo la segunda lo esconde, y por eso las dos
    salen del mismo comando y no de dos.
    """
    total = cuenta["total"]
    return [
        f"  suite completa .................. {total:>5} tests",
        f"  arnés (les apunta un mutante) ... {cuenta['dentro']:>5}   "
        f"{porcentaje(cuenta['dentro'], total)}   <- la columna «% arnés»",
        f"  fuera del arnés ................. {cuenta['fuera']:>5}   "
        f"{porcentaje(cuenta['fuera'], total)}",
        f"  protegidos por ALGO ............. {cuenta['protegidos']:>5}   "
        f"{porcentaje(cuenta['protegidos'], total)}",
        f"  sin ningún control .............. {cuenta['sin_nada']:>5}   "
        f"{porcentaje(cuenta['sin_nada'], total)}",
        f"  mutantes en el PLAN ............. {cuenta['mutantes']:>5}",
    ]


def _recuentos() -> dict[str, int]:
    """Los recuentos de `tests/unit/conftest.py`, sin duplicar su cálculo."""
    ruta = RAIZ / "tests" / "unit" / "conftest.py"
    sys.path.insert(0, str(ruta.parent))
    spec = importlib.util.spec_from_file_location("_conftest_contabilidades", ruta)
    if spec is None or spec.loader is None:  # pragma: no cover - no ocurre en el repo
        raise RuntimeError(f"no se pudo cargar {ruta}")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    cuenta: dict[str, int] = modulo.exigir_sano(modulo.recuentos())
    return cuenta


def main() -> int:
    cuenta = _recuentos()
    print("\n  LAS DOS CONTABILIDADES · deuda 7 de ESTADO.md, límites 51 y 60\n")
    for linea in lineas(cuenta):
        print(linea)
    print(
        "\n  La primera mide EL ARNÉS; la segunda, la protección real. No son "
        "intercambiables:\n  un criterio sobre una de ellas no dice nada sobre la otra.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
