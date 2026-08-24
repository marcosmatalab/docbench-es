"""El sello de una medición: sobre QUÉ árbol se midió, no sólo cuándo.

**El fallo que cierra.** `RESULTS.md` publicó durante todo L3 que un mutante se
caía en «18 de 54 tests». Era cierto cuando se midió y dejó de serlo en cuanto
alguien añadió un test, porque **el denominador es el tamaño de la suite**. La
fecha no lo delata: un lector ve «23 ago» y no sabe si desde entonces la suite ha
crecido. El commit sí lo delata — se compara con `git log` en un segundo.

Es una clase que el guardián de recuentos **no puede** cubrir. Aquéllos son
recuentos que se recalculan en cada colección, así que no pueden quedarse viejos.
Éstos son **mediciones**: cuestan minutos, se hacen una vez, y su denominador se
mueve solo por debajo. La regeneración en cada cierre los mantiene frescos; el
sello los hace honestos **entre medias**.

El sello lo imprime **el propio instrumento**, no quien escribe el documento: si
lo pusiera el redactor a mano sería una copia más, capaz de quedarse vieja — el
mismo bug una capa por encima.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _git(*orden: str) -> str:
    """La salida de `git`, y **`?` si git falla**, nunca cadena vacía.

    Con `check=False` y sin mirar el código, un `git status` que reventara devolvía
    `""`, que se cuenta como cero ficheros sucios: **un árbol sucio con cara de
    limpio**, que es justo lo que el sello existe para no dejar pasar.
    """
    salida = subprocess.run(["git", *orden], cwd=RAIZ, capture_output=True, text=True, check=False)
    return salida.stdout.strip() if salida.returncode == 0 else "?"


def sello(n_tests: int | None = None) -> str:
    """`abc1234`, `abc1234+7` si hay 7 ficheros sin commitear, y el n si se pasa.

    El `+N` importa tanto como el hash: una medición sobre un árbol sucio **no es
    reproducible desde ningún commit**, y quien la lea tiene derecho a saberlo
    antes de compararla con la suya.
    """
    corto = _git("rev-parse", "--short", "HEAD") or "(sin HEAD)"
    estado = _git("status", "--porcelain")
    if estado == "?":
        return f"{corto}+? · {n_tests} tests" if n_tests is not None else f"{corto}+?"
    sucios = len([x for x in estado.splitlines() if x])
    marca = f"{corto}+{sucios}" if sucios else corto
    return f"{marca} · {n_tests} tests" if n_tests is not None else marca
