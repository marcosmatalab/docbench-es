"""**MUTANTE.** El titular de la portada sale sin su panel dentro de la etiqueta.

Es LIMITS 113 roto en el único sitio donde todavía se puede romper: **el renderizado de
la puerta de entrada**. `cifras()` puede emitir un panel perfecto —`acuerdo.panel` con
sus cuatro nombres— y la página imprimir el número solo: la aritmética queda intacta y
`assert "panel" in cifras` pasa en verde.

Con este mutante, «103 de 338» se publica **sin decir sobre qué panel es**. Y ése es
exactamente el número que **sólo sabe bajar** al añadir un extractor, porque es una
intersección sobre tantos conjuntos como extractores tenga el panel. Sin la etiqueta, el
día que entre el quinto la caída se leería como que el corpus empeoró o como que la
extracción va peor — y sería la misma clase de fallo que este hito acaba de corregir, un
número con la etiqueta de otra cuenta, sólo que **diferido** a la comparación de mañana.

El panel sigue en la página, en el párrafo de después: se mueve, no se borra. Un mutante
que lo borrara del todo lo cazaría cualquier `"camelot" in html`; éste exige un test que
mire **dónde** está, que es lo que la regla pide de verdad.

Sólo lo mata un test que compruebe el SITIO —dentro de `<div class="figure">`—, no la
presencia. Los que comprueban el objeto pasan en verde contra esto.
"""

from __future__ import annotations

from collections.abc import Mapping

from docbench_es.report.portada import _pagina
from docbench_es.report.portada._cifras import Cifra

_original = _pagina._titular


def _sin_panel_en_la_etiqueta(c: Mapping[str, Cifra]) -> str:
    entero = _original(c)
    inicio = entero.index('<p class="bind">')
    fin = entero.index("</p>", inicio) + len("</p>")
    return entero[:inicio] + entero[fin:] + f"\n  {entero[inicio:fin]}"


_pagina._titular = _sin_panel_en_la_etiqueta  # type: ignore[assignment]
