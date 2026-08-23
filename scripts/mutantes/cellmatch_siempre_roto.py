"""La exactitud celda a celda es 0 pase lo que pase. El `siempre_roto` de §12.

El espejo del anterior: caza al test que sólo mira la mitad negativa. Y caza algo
más concreto de este proyecto —la regla de oro 4—: **`None` no es 0**. Una verdad
sin celdas tiene que dar NO_APLICABLE, y un 0,0 constante lo pisa devolviendo un
número que se puede promediar, que es exactamente el fallo que la regla prohíbe.
"""

import docbench_es.core.cellmatch as cm


def pytest_configure(config: object) -> None:
    cm.cell_accuracy = lambda pred, gold: 0.0
    cm.cell_f1 = lambda pred, gold: 0.0
