"""N3 vuelve a declarar solo Cc y Zs: la regresion de U+2028 que encontro hypothesis."""

import docbench_es.core.canonical._normalizar as normalizar


def pytest_configure(config: object) -> None:
    normalizar.CATEGORIAS_DE_ESPACIO = ("Cc", "Zs")
