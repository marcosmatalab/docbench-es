"""**MUTANTE.** El `NO_APLICABLE` se imprime `0,0000` en vez de `n/a`. Decisión B3, en el
último sitio donde todavía se puede romper: el renderizado.

La aritmética puede estar perfecta —`teds=None`, `cell_f1=None`, régimen y agregado en su
sitio— y la tabla publicada seguir mintiendo, porque **lo que se lee es el Markdown**. Un
0,00 dice «se midió y salió cero»; un `n/a` dice «no se pudo medir». Con este mutante, un
extractor al que no le cuadró ni un documento sale con un cero redondo en cada columna y
parece medido y malo, en vez de no medido.

Sólo lo mata un test que mire el **texto** de la tabla, no el objeto: los tests que
comprueban `metricas.teds is None` pasan en verde contra esto.
"""

from __future__ import annotations

from docbench_es.report import tables

_original = tables._num


def _cero_en_vez_de_n_a(valor: float | None, decimales: int = 4) -> str:
    if valor is None:
        return f"{0:.{decimales}f}".replace(".", ",")
    return _original(valor, decimales)


tables._num = _cero_en_vez_de_n_a  # type: ignore[assignment]
