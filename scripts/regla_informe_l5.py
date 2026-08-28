"""**R7 · las cifras de L5 publicadas en `RESULTS.md`, contra `runs/l5/informe.json`.**

    uv run python scripts/derivadas.py --detalle

## Por qué existe

El titular del hito —«103 de los 338 documentos»— y las cuatro filas de la tabla de
nivel 1 estaban **tecleadas** en `RESULTS.md`. Un número tecleado no lo comprueba nadie, y
el mensaje de error de `scripts/derivadas.py` dice en mayúsculas *UN NÚMERO DERIVADO NO SE
TECLEA*. Que la cifra más citable del hito fuera la única sin guardián no era un descuido
menor: el escrutinio adversarial de L5 encontró que **el titular estaba mal** —publicaba
82 donde eran 103, porque confundía dos intersecciones— y no lo cazó ningún test.

L4 tenía su `runs/l4/informe.json`; L5 tenía cuatro artefactos de la campaña y ninguno con
el resultado. Ahora lo tiene, lo escribe `docbench report` en la misma llamada que el
Markdown, y esta regla compara.

## Qué NO comprueba

Que el JSON sea correcto: eso lo demuestran los tests de `report.nivel1` y
`report.cara_a_cara`. Esto comprueba que **lo publicado coincide con lo medido**, que es
otra cosa y es la que se rompe sola con el tiempo.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INFORME = RAIZ / "runs" / "l5" / "informe.json"

from rota import Rota  # noqa: E402


@lru_cache(maxsize=1)
def _informe() -> dict[str, dict[str, object]] | None:
    """El informe de la campaña, o `None` si no está. **Un fichero que falta no es un
    fallo de esta regla**: es una campaña que no se ha corrido, y decir «roto» ahí sería
    acusar al documento de mentir cuando lo que pasa es que no hay con qué comparar."""
    if not INFORME.exists():
        return None
    datos: dict[str, dict[str, object]] = json.loads(INFORME.read_text(encoding="utf-8"))
    return datos


def _num(valor: float | None, decimales: int = 4) -> str:
    return "n/a" if valor is None else f"{valor:.{decimales}f}".replace(".", ",")


def _pct(valor: float) -> str:
    return f"{100 * valor:.1f}%".replace(".", ",")


def cifras_de_l5(texto: str, documento: str) -> list[Rota]:
    """Las cifras de L5 de `RESULTS.md`, contra el informe de la campaña."""
    if documento != "RESULTS.md":
        return []
    datos = _informe()
    if datos is None:
        return []
    acuerdo = datos["acuerdo"]
    extractores = datos["extractores"]
    fuera: list[Rota] = []

    def _rota(patron: str, esperado: str, que: str) -> None:
        casa = re.search(patron, texto)
        if casa is None:
            fuera.append(Rota(documento, 0, que, "no aparece", esperado))
        elif casa.group(1) != esperado:
            linea = texto[: casa.start()].count("\n") + 1
            fuera.append(Rota(documento, linea, que, casa.group(1), esperado))

    _rota(
        r"[Ss]ólo en (\d+) de los \d+ documentos con tabla",
        str(acuerdo["los_extractores_coinciden_en_el_recuento"]),
        "informe.json acuerdo",
    )
    _rota(
        r"\| \*\*acuerdo de recuento\*\* \| \*\*(\d+)\*\*",
        str(acuerdo["los_extractores_coinciden_en_el_recuento"]),
        "informe.json acuerdo",
    )
    _rota(
        r"\| \*\*puntúan los cuatro\*\* \| \*\*(\d+)\*\*",
        str(acuerdo["puntuan_todos"]),
        "informe.json puntúan",
    )
    _rota(r"\| diferencia \| \*\*(\d+)\*\*", str(acuerdo["no_aplicables"]), "informe.json n/a")

    bandas: dict[str, dict[str, int]] = acuerdo["por_banda"]  # type: ignore[assignment]
    for banda, cuenta in bandas.items():
        etiqueta = re.escape(banda)
        _rota(
            rf"\| {etiqueta} \| {cuenta['poblacion']} \| (\d+) \|",
            str(cuenta["coinciden"]),
            f"informe.json banda {banda}",
        )

    for nombre, e in extractores.items():
        assert isinstance(e, dict)
        _rota(
            rf"\| `{re.escape(nombre)}` \| ([0-9,]+) \| [0-9,]+ \| [0-9,]+ \| [0-9,]+ \|",
            _num(e["teds"]),
            f"informe.json {nombre} teds",
        )
        _rota(
            rf"\| `{re.escape(nombre)}` \| ([0-9,]+) \| [0-9,]+ \| [+-][0-9,]+ \|",
            _num(e["cara_a_cara_teds"]),
            f"informe.json {nombre} cara a cara",
        )
        _rota(
            rf"\| `{re.escape(nombre)}` \| [0-9,]+ \| [0-9,]+ \| [0-9,]+ \| [0-9,]+ \| ([0-9,]+%)",
            _pct(e["cobertura_evaluable"]),
            f"informe.json {nombre} cobertura",
        )
    return fuera
