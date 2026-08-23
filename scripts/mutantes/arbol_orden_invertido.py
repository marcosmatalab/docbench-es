"""El árbol de TEDS emite las celdas de cada fila al revés.

**El mutante que demostró que el criterio de aceptación de L2 estaba ciego.** El
golden se genera dando a la referencia el render canónico de las mismas tablas,
así que el mapeo `CanonicalTable → árbol` aparece en los dos lados de la
comparación y **se cancela**: con esta mutación, el HTML de los 20 casos sale con
las columnas invertidas y, antes de que existiera
`test_el_render_canonico_es_el_que_genero_el_golden`, la suite entera pasaba en
verde. Ver `LIMITS.md` 52.
"""

import docbench_es.core.teds._arbol as arbol

_original = arbol._celdas_por_fila


def pytest_configure(config: object) -> None:
    arbol._celdas_por_fila = lambda t: [list(reversed(f)) for f in _original(t)]
