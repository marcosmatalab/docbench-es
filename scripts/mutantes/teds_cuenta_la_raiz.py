"""El denominador cuenta tambien la raiz <table>.

Es el error sutil: todos los TEDS del proyecto salen un poco mas altos, en todos
los casos, y ninguna grafica lo enseña. Solo lo caza comparar con la referencia.
"""

import docbench_es.core.teds._arbol as arbol_mod

_original = arbol_mod.n_nodos


def pytest_configure(config: object) -> None:
    import docbench_es.core.teds as teds_mod

    teds_mod.n_nodos = lambda nodo: _original(nodo) + 1
