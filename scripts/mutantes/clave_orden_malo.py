"""`key()` escapa la barra pero NO el porcentaje primero.

Es el bug clasico de un escapado a mano: esc("%2F") == esc("/"), o sea que una
cadena que PARECE una secuencia de escape colisiona con lo que escapa. El
escapado de `urllib` no podia tener este bug; uno a mano si.
"""

import docbench_es.types._documento as documento


def pytest_configure(config: object) -> None:
    documento._escapar = lambda campo: campo.replace("/", "%2F")
