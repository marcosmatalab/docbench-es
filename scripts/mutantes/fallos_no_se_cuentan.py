"""**MUTANTE.** La tabla publica «0 fallos» para todos, siempre. El `siempre_ok` de la
regla de oro 6.

**Ataca el cero que L5 publica.** La primera tabla dice `0, 0, 0 y 0` en la columna de
fallos, y un cero medido y un cero por no mirar se imprimen exactamente igual. Este
mutante es la segunda forma de ese cero: `medir` deja de contar las causas y la columna
sale limpia pase lo que pase.

Sólo lo mata un test que meta una extracción **fallida** por el arnés y exija que su causa
aparezca contada con su nombre. Un test que compruebe «la columna existe» o «no hay causas
raras» pasa en verde contra esto, y ésa es justo la dirección tranquilizadora.
"""

from __future__ import annotations

from dataclasses import replace

from docbench_es.report import nivel1

_original = nivel1.medir


def _sin_fallos(*args: object, **kwargs: object) -> object:
    fila = _original(*args, **kwargs)  # type: ignore[arg-type]
    return replace(fila, metricas=replace(fila.metricas, failures={}))


nivel1.medir = _sin_fallos  # type: ignore[assignment]
