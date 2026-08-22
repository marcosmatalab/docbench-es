"""`validate` rechaza toda tabla."""

import docbench_es.types._tabla as tabla


def _siempre_roto(t: object) -> tuple[bool, list[str]]:
    return (False, ["SOLAPE: mutante"])


def pytest_configure(config: object) -> None:
    tabla.comprobar = _siempre_roto
