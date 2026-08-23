"""`<thead>` se lleva sólo la PRIMERA fila de cabecera, no el prefijo máximo.

Rompe el punto 2 de ADR-0021. Es más sutil que el anterior porque **con una sola
fila de cabecera las dos reglas coinciden**, y las estrategias de `hypothesis`
fijan `is_header = fila == 0`: ninguna propiedad puede generar `n_cabecera >= 2`.
Lo mata el caso a mano de dos filas de cabecera, y de rebote 6 de los 20 casos de
PubTabNet, que sí las traen.
"""

import docbench_es.core.teds._arbol as arbol

_original = arbol._filas_de_cabecera


def pytest_configure(config: object) -> None:
    arbol._filas_de_cabecera = lambda filas: min(_original(filas), 1)
