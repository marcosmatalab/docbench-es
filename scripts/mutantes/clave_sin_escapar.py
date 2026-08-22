"""`key()` deja de escapar: el bug de colision que arreglo L0."""

import docbench_es.types._documento as documento


def pytest_configure(config: object) -> None:
    documento._escapar = lambda campo: campo
