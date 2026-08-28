"""**MUTANTE.** La cara a cara puntúa sobre la UNIÓN y rellena con 0,00 lo que falta.

Es el `siempre_ok` del segundo denominador: mantiene la tabla, mantiene la `n`, y le quita
lo único que hacía: comparar a todos sobre **los mismos documentos**. Con la unión, cada
extractor vuelve a puntuar sobre un conjunto distinto —el suyo más los de los demás— y el
hueco se rellena con un cero, que es exactamente lo que la decisión B3 prohíbe: «no se
pudo medir» impreso como «se midió y salió cero».

**Y no se ve en la forma.** La sección sigue saliendo, con su tabla, su n y su nota al pie
diciendo que no es un ranking. Sólo lo mata un test que construya dos extractores que
acierten el recuento en documentos DISTINTOS y afirme que la intersección son los comunes
—o que, sin comunes, la respuesta es «no hay comparación» y no un empate a cero—.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from docbench_es.report import cara_a_cara as modulo

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.nivel1 import Nivel1

_original = modulo.cara_a_cara


def _sobre_la_union(
    filas: Mapping[str, Nivel1], paginas: Mapping[str, int] | None = None
) -> modulo.CaraACara:
    fuera = _original(filas, paginas)
    if not filas:
        return fuera
    todos = tuple(sorted({d for f in filas.values() for d in f.por_documento}))
    if not todos:
        return fuera
    return replace(
        fuera,
        documentos=todos,
        teds={
            nombre: sum(f.por_documento.get(d, 0.0) for d in todos) / len(todos)
            for nombre, f in sorted(filas.items())
        },
    )


modulo.cara_a_cara = _sobre_la_union  # type: ignore[assignment]
