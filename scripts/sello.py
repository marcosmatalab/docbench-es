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

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from docbench_es.extract.sello import cpus_visibles
from docbench_es.extract.sello import git as _git

RAIZ = Path(__file__).resolve().parents[1]

__all__ = ["cpus_visibles", "sello", "trabajadores"]


def trabajadores() -> str:
    """Cuántos procesos levanta `pytest -n auto` AQUÍ. **Parte del sello desde L5.**

    `auto` resuelve al número de núcleos, así que **el margen de la puerta dejó de ser
    una propiedad del repo y pasó a serlo de la máquina**. El 1,67x medido en 8 núcleos
    no se reproduce en un runner de dos, y quien lo intente no tendrá con qué
    explicarse la diferencia.

    Es la misma regla que `docs/metrics.md` ya aplica a la carga de la máquina —se
    declara porque se midió que importa—: **una cifra que depende de una condición no
    declarada no es reproducible, es irrepetible.**
    """
    entorno = os.environ.get("PYTEST_ADDOPTS", "")
    # El entorno GANA: `pytest` mete `addopts` del `pyproject` primero y la línea de
    # órdenes —donde va `PYTEST_ADDOPTS`— después, así que el último `-n` manda. Es
    # como se mide en serie sin mover el árbol, y el sello tiene que reflejarlo.
    if "-n 0" in entorno or "no:xdist" in entorno:
        return "serie"
    if "-n auto" not in _pyproject_addopts():
        return "serie"
    # `auto` de `xdist` resuelve a núcleos lógicos, que es lo que da `os.cpu_count`.
    return f"{os.cpu_count() or '?'}w"


# `cpus_visibles` y `git` viven en `docbench_es.extract.sello` y se reexportan aquí.
# **Eran dos implementaciones de «qué árbol es éste y qué máquina lo mide»**, una para
# los documentos y otra para las corridas, y dos copias sólo tienen dos futuros: quedarse
# viejas o obligar a acordarse. Lo que SÍ es de aquí es `trabajadores()`, que es
# específico de `pytest` y no tiene nada que hacer en `src/`.


def _pyproject_addopts() -> str:
    config = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    return next((x for x in config.splitlines() if x.startswith("addopts")), "")


def sello(n_tests: int | None = None) -> str:
    """`abc1234`, `abc1234+7` si hay 7 ficheros sin commitear, y el n si se pasa.

    El `+N` importa tanto como el hash: una medición sobre un árbol sucio **no es
    reproducible desde ningún commit**, y quien la lea tiene derecho a saberlo
    antes de compararla con la suya.
    """
    corto = _git("rev-parse", "--short", "HEAD") or "(sin HEAD)"
    estado = _git("status", "--porcelain")
    if estado == "?":
        return (
            f"{corto}+? · {n_tests} tests · {trabajadores()}"
            if n_tests is not None
            else f"{corto}+?"
        )
    sucios = len([x for x in estado.splitlines() if x])
    marca = f"{corto}+{sucios}" if sucios else corto
    if n_tests is None:
        return f"{marca} · {trabajadores()}"
    return f"{marca} · {n_tests} tests · {trabajadores()}"
