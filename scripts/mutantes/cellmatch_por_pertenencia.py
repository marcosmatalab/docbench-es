"""El emparejado de celdas cuenta pertenencia en vez de multiconjunto.

Una celda repetida —lo que pasa en una tabla con SOLAPE— suma dos aciertos sobre
una sola celda real, y la exactitud puede pasar de 1.
"""

import docbench_es.core.cellmatch as cm


def _emparejar(pred, gold):
    firmas = {cm._firma(c) for c in gold.cells}
    aciertos = sum(1 for c in pred.cells if cm._firma(c) in firmas)
    return cm.Emparejado(aciertos, len(pred.cells), len(gold.cells))


def pytest_configure(config: object) -> None:
    cm.emparejar = _emparejar
