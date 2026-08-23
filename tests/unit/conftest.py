"""Los recuentos volátiles del repo, calculados en cada colección.

**El problema que resuelve.** El cierre de L2 pasó los mutantes de 12 a 18 y los
tests fuera del arnés de 38 a 23. La corrección se escribió en `RESULTS.md` con su
nota al lado… y **se quedó vieja en `LIMITS.md` 51, en `ESTADO.md` y en
`.claude/skills/cerrar/SKILL.md`**, los tres dentro del mismo commit. `unica()`
impide editar a ciegas UN documento; nada impedía corregir uno y olvidar tres.

**Por qué se calcula aquí y no en un fichero generado.** Un JSON que escribe
`matar.py` sólo está al día si alguien acuerda de correr `matar.py`, y entonces el
fichero es una cuarta copia que puede quedarse vieja — el mismo fallo, una capa
más abajo. `pytest_collection_modifyitems` corre **en cada `pytest tests/unit`**,
o sea en cada `make fast`: los números no pueden estar viejos porque no están
almacenados en ningún sitio. Y el recuento es **exacto**, con la parametrización
ya resuelta, que es lo que un `grep "def test_"` no puede dar.

`tests/unit/test_recuentos.py` es quien los compara contra los documentos.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]

RECUENTOS: dict[str, int] = {}
"""Se rellena al colectar. Vacío fuera de una corrida de pytest, a propósito."""

COMPLETA = False
"""¿La colección cubrió `tests/unit` ENTERO?

Con `pytest tests/unit/test_x.py` los recuentos son los de ese fichero y no los
del repo. Quien compare contra documentos publicados tiene que saberlo y saltarse
la comprobación, en vez de declarar que todos los documentos mienten."""

FUERA_POR_FICHERO: dict[str, int] = {}
"""Fichero de test -> nº de tests, sólo para los que NINGÚN mutante apunta."""


def _plan() -> tuple[set[str], int]:
    """Los ficheros de test a los que apunta algún mutante, según el PLAN.

    Se lee el `PLAN` de `matar.py` directamente en vez de copiarlo: es la
    definición de «dentro del arnés», y copiarla aquí crearía justo la segunda
    fuente de verdad que este fichero existe para evitar.
    """
    ruta = RAIZ / "scripts" / "mutantes" / "matar.py"
    spec = importlib.util.spec_from_file_location("_matar", ruta)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    plan: list[tuple[str, str]] = modulo.PLAN
    ficheros = {Path(f).name for _, suite in plan for f in suite.split()}
    return ficheros, len(plan)


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    del session, config
    dentro_de, n_mutantes = _plan()
    por_fichero: dict[str, int] = {}
    for item in items:
        nombre = Path(str(item.path)).name
        por_fichero[nombre] = por_fichero.get(nombre, 0) + 1

    global COMPLETA
    en_disco = {p.name for p in (RAIZ / "tests" / "unit").glob("test_*.py")}
    COMPLETA = en_disco == set(por_fichero)

    FUERA_POR_FICHERO.clear()
    FUERA_POR_FICHERO.update({f: n for f, n in por_fichero.items() if f not in dentro_de})
    RECUENTOS.clear()
    RECUENTOS.update(
        {
            "mutantes": n_mutantes,
            "total": sum(por_fichero.values()),
            "dentro": sum(n for f, n in por_fichero.items() if f in dentro_de),
            "fuera": sum(FUERA_POR_FICHERO.values()),
        }
    )
