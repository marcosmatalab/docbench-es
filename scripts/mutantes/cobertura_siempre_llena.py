"""**MUTANTE.** `evaluable_coverage` vale 1,0 pase lo que pase. El `siempre_ok` de la
regla de oro 4.

La regla dice que la nota de un extractor **va siempre con su cobertura evaluable**, y el
límite 35 lo pone como condición sobre el objeto que emite el informe. Una cobertura
constante de 1,0 cumple la forma —la columna está, viaja en la misma fila— y vacía el
contenido: las cuatro notas de L5, que se calculan sobre coberturas del 23,6% al 38,0%,
pasarían a leerse como si fueran comparables.

Sólo lo mata un test que exija que la cobertura **baje** cuando la verdad tiene tablas que
no se pudieron emparejar, o que sea 0,0 cuando no se pudo emparejar ninguna.
"""

from __future__ import annotations

from dataclasses import replace

from docbench_es.report import nivel1

_original = nivel1.medir


def _cobertura_llena(*args: object, **kwargs: object) -> object:
    fila = _original(*args, **kwargs)  # type: ignore[arg-type]
    return replace(fila, metricas=replace(fila.metricas, evaluable_coverage=1.0))


nivel1.medir = _cobertura_llena  # type: ignore[assignment]
