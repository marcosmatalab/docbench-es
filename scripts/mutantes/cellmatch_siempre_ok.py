"""La exactitud celda a celda es 1 pase lo que pase. El `siempre_ok` de §12.

Caza al test que no comprueba nada: cualquier aserción de la forma «esto no baja»
o «esto es como mucho 1» la cumple un 1,0 constante. Sólo lo mata un test que
exija que la exactitud BAJE ante un error real —una celda desplazada, una celda
que falta— o que `None` cuando la verdad no tiene celdas (NO_APLICABLE, regla 4).
"""

import docbench_es.core.cellmatch as cm


def pytest_configure(config: object) -> None:
    cm.cell_accuracy = lambda pred, gold: 1.0
    cm.cell_f1 = lambda pred, gold: 1.0
