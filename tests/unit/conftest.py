"""Los recuentos volátiles del repo, calculados en cada colección.

**El problema que resuelve.** El cierre de L2 pasó los mutantes de 12 a 18 y los
tests fuera del arnés de 38 a 23. La corrección se escribió en `RESULTS.md` con su
nota al lado… y **se quedó vieja en `LIMITS.md` 51, en `ESTADO.md` y en
`.claude/skills/cerrar/SKILL.md`**, los tres dentro del mismo commit. `unica()`
impide editar a ciegas UN documento; nada impedía corregir uno y olvidar tres.

**Por qué se calcula aquí y no en un fichero generado.** Un JSON que escribe
`matar.py` sólo está al día si alguien se acuerda de correr `matar.py`, y entonces
el fichero es una cuarta copia que puede quedarse vieja — el mismo fallo una capa
más abajo. `pytest_collection_modifyitems` corre **en cada `pytest tests/unit`**,
o sea en cada `make fast`: los números no pueden estar viejos porque no están
almacenados en ningún sitio. Y el recuento es **exacto**, con la parametrización
ya resuelta, que es lo que un `grep "def test_"` no puede dar.

**La precondición, que la primera versión no declaró y por eso se rompió.** Estos
recuentos salen de lo COLECTADO. `pytest tests/unit/test_recuentos.py` colecta 5
tests y da `dentro=0`, `total=5`: cifras ciertas sobre esa corrida y **falsas
sobre el repo**. La primera versión las usaba igual y se ponía roja hablando de
una desincronización que no existía. Ahora eso lo resuelve `recuentos()`.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
UNIT = RAIZ / "tests" / "unit"

COLECTADOS: dict[str, int] = {}
"""Lo que salió de la colección de ESTA corrida. Puede ser parcial: ver `COMPLETA`."""

FUERA_POR_FICHERO: dict[str, int] = {}
"""Fichero de test -> nº de tests, sólo para los que NINGÚN mutante apunta."""

COMPLETA = False
"""¿La colección cubrió `tests/unit` ENTERO?

Con `pytest tests/unit/test_x.py`, o con `-k`, los recuentos son los de esa
selección y no los del repo. Quien compare contra documentos publicados tiene que
saberlo, o acaba declarando que todos los documentos mienten.
"""

_RECUPERADOS: dict[str, int] = {}


class RecuentoDegenerado(RuntimeError):
    """Los recuentos no cumplen sus invariantes estructurales.

    No es lo mismo que «un documento cita un número viejo». Esto dice que **la
    medición no se hizo**, y las dos cosas se leen igual en un fallo si no se
    distinguen — que es exactamente el error que `matar.py` ya documenta cuando
    pytest no recoge ni un test.
    """


def _plan() -> tuple[set[str], int]:
    """Los ficheros de test a los que apunta algún mutante, y cuántos mutantes hay.

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
    return {Path(f).name for _, suite in plan for f in suite.split()}, len(plan)


def _cuadrar(por_fichero: dict[str, int]) -> tuple[dict[str, int], dict[str, int]]:
    dentro_de, n_mutantes = _plan()
    fuera = {f: n for f, n in por_fichero.items() if f not in dentro_de}
    return (
        {
            "mutantes": n_mutantes,
            "total": sum(por_fichero.values()),
            "dentro": sum(n for f, n in por_fichero.items() if f in dentro_de),
            "fuera": sum(fuera.values()),
        },
        fuera,
    )


def exigir_sano(cuenta: dict[str, int]) -> dict[str, int]:
    """Rechaza los recuentos DEGENERADOS antes de que nadie compare contra ellos.

    Son invariantes estructurales, no umbrales inventados:

    - `total == dentro + fuera`, porque cada test cae en un lado o en el otro;
    - `mutantes >= 1`, o el `PLAN` está vacío;
    - `dentro >= 1`, o no se colectó ni un fichero del arnés;
    - `fuera >= 1`, porque este mismo fichero está fuera del arnés.

    Sin esto, una colección parcial produce `dentro=0` y la comparación acusa a
    todos los documentos de mentir. Un recuento degenerado **no es un desacuerdo**:
    es que no hay medición, y decir «no hay medición» es distinto de decir «el
    documento está mal».
    """
    if not cuenta:
        raise RecuentoDegenerado("los recuentos están vacíos: la colección no llegó a correr")
    esperado = cuenta["dentro"] + cuenta["fuera"]
    problemas = [
        f"total={cuenta['total']} pero dentro+fuera={esperado}"
        if cuenta["total"] != esperado
        else "",
        "mutantes=0: el PLAN de matar.py está vacío" if cuenta["mutantes"] < 1 else "",
        "dentro=0: no se colectó ni un fichero del arnés" if cuenta["dentro"] < 1 else "",
        "fuera=0: ni siquiera este fichero se contó" if cuenta["fuera"] < 1 else "",
    ]
    rotos = [p for p in problemas if p]
    if rotos:
        raise RecuentoDegenerado(
            f"recuentos degenerados, no hay medición: {'; '.join(rotos)} · {cuenta}"
        )
    return cuenta


def _recuperar() -> dict[str, int]:
    """Colecta `tests/unit` ENTERO en un subproceso. **233 ms medidos.**

    Es lo que permite que la comprobación viva también en las corridas parciales
    en vez de saltarse, que es lo que hacía la primera versión. Se paga sólo
    cuando la selección **incluye** estos tests: si `-k` los deselecciona, no
    llegan a ejecutarse y no hay coste.
    """
    if _RECUPERADOS:
        return _RECUPERADOS
    salida = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )
    por_fichero = {
        m.group(1): int(m.group(2))
        for linea in salida.stdout.splitlines()
        if (m := re.match(r"^tests/unit/(test_\w+\.py): (\d+)$", linea))
    }
    if not por_fichero:
        raise RecuentoDegenerado(
            "el subproceso de colección no devolvió ni un fichero; sin eso no hay "
            f"recuento que comparar.\nrc={salida.returncode}\n{salida.stdout[-600:]}"
        )
    cuenta, fuera = _cuadrar(por_fichero)
    FUERA_POR_FICHERO.clear()
    FUERA_POR_FICHERO.update(fuera)
    _RECUPERADOS.update(exigir_sano(cuenta))
    return _RECUPERADOS


def recuentos() -> dict[str, int]:
    """Los recuentos VERDADEROS del repo, venga la corrida como venga.

    Completa: los de la colección, gratis. Parcial: se recuperan con un
    subproceso. En ningún caso se devuelven cifras de una selección parcial, que
    es lo que rompió la primera versión.
    """
    if COMPLETA:
        return exigir_sano(COLECTADOS)
    return _recuperar()


def fuera_por_fichero() -> dict[str, int]:
    """El desglose de los que quedan fuera del arnés, **ya recuperado si hacía falta**.

    Existe para que nadie lea `FUERA_POR_FICHERO` directamente: en una corrida
    parcial ese diccionario trae el desglose de la selección, no el del repo, y
    sólo se rellena de verdad al llamar a `recuentos()`.
    """
    recuentos()
    return dict(FUERA_POR_FICHERO)


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    del session, config
    por_fichero: dict[str, int] = {}
    for item in items:
        nombre = Path(str(item.path)).name
        por_fichero[nombre] = por_fichero.get(nombre, 0) + 1

    global COMPLETA
    en_disco = {p.name for p in UNIT.glob("test_*.py")}
    COMPLETA = en_disco == set(por_fichero)

    cuenta, fuera = _cuadrar(por_fichero)
    FUERA_POR_FICHERO.clear()
    FUERA_POR_FICHERO.update(fuera)
    COLECTADOS.clear()
    COLECTADOS.update(cuenta)
