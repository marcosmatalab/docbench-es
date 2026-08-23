"""TEDS rechaza todo: ninguna tabla se parece a ninguna. El `siempre_roto` de §9.2.

Caza al test que sólo afirma la **mitad negativa** —«romper el texto baja la
nota», «borrar una celda baja la nota»—, que es la dirección tranquilizadora: una
métrica que devuelve 0 siempre satisface «bajó» en todas ellas. Lo que este
mutante NO puede satisfacer es la mitad positiva: una tabla contra sí misma vale
1, y dos tablas vacías valen 1 (§12).
"""

import docbench_es.core.teds as teds_mod


def pytest_configure(config: object) -> None:
    teds_mod.teds = lambda pred, gold: 0.0
    teds_mod.teds_struct = lambda pred, gold: 0.0
