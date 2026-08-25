"""Las páginas del corpus, por bandas. **Ningún número de aquí se teclea.**

    uv run python scripts/censo_paginas.py

Todo sale de `runs/l3/manifiesto.json`. Existe porque B5-bis estima el total con

    total = suma sobre bandas de (páginas de la banda por coste-página de la banda)

y ese `páginas de la banda` es el peso de la suma: si se copiara a mano a un YAML,
sería un número derivado tecleado, y este repo tiene un guardián entero contra eso.

## El número que cambió el método

Los **38 documentos de más de 50 páginas son el 3,8% de los documentos y el 36,6% de
las páginas**. Con esa asimetría, censurar los largos no recorta la cola: tira el
tercio que decide la respuesta. Lo mismo abre la pregunta de con qué se pondera el
TEDS agregado, que está decidida en `runs/l5/ponderacion.yaml`.
"""

from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = RAIZ / "runs" / "l3" / "manifiesto.json"

# Las del COSTE (agrupación secundaria de B2, ExtractBench). No son las del informe:
# el porqué de que sean distintas está en `runs/l5/estimacion.yaml`.
DEL_COSTE: dict[str, tuple[int, int]] = {"<=10": (1, 10), "11-50": (11, 50), ">50": (51, 10**9)}
# Las del INFORME (agrupación primaria de B2).
DEL_INFORME: dict[str, tuple[int, int]] = {"1-4": (1, 4), "5-12": (5, 12), "13+": (13, 10**9)}


@dataclass(frozen=True)
class Banda:
    """Una banda con lo que la suma necesita de ella, y su forma."""

    nombre: str
    documentos: list[str]
    paginas: list[int]

    @property
    def n_paginas(self) -> int:
        return sum(self.paginas)

    def resumen(self) -> str:
        q = statistics.quantiles(self.paginas, n=4) if len(self.paginas) > 3 else [0, 0, 0]
        return (
            f"{len(self.documentos):5d} doc  {self.n_paginas:6d} pág  "
            f"mediana {statistics.median(self.paginas):5.0f}  p25 {q[0]:4.0f}  p75 {q[2]:4.0f}"
        )


def paginas() -> dict[str, int]:
    """`external_id` → páginas, del manifiesto de L3."""
    man = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    return {d["external_id"]: int(d["n_pages"]) for d in man["documentos"]}


def repartir(cortes: dict[str, tuple[int, int]]) -> dict[str, Banda]:
    """El corpus repartido en bandas. Aborta si alguna sale vacía: una banda vacía
    haría que su término de la suma valiera cero sin que nadie lo notara."""
    todas = paginas()
    fuera: dict[str, Banda] = {}
    for nombre, (lo, hi) in cortes.items():
        dentro = {i: p for i, p in todas.items() if lo <= p <= hi}
        if not dentro:
            raise ValueError(f"la banda {nombre} ({lo}-{hi}) no tiene ni un documento")
        fuera[nombre] = Banda(nombre, sorted(dentro), [dentro[i] for i in sorted(dentro)])
    repartidos = sum(len(b.documentos) for b in fuera.values())
    if repartidos != len(todas):
        raise ValueError(f"las bandas cubren {repartidos} documentos de {len(todas)}")
    return fuera


def main() -> int:
    todas = paginas()
    total = sum(todas.values())
    print(
        f"\n  {len(todas)} documentos · {total} páginas · "
        f"mediana {statistics.median(todas.values()):.0f} · máximo {max(todas.values())}\n"
    )
    for titulo, cortes in (("bandas del COSTE", DEL_COSTE), ("bandas del INFORME", DEL_INFORME)):
        print(f"  {titulo}:")
        for b in repartir(cortes).values():
            print(
                f"    {b.nombre:<7} {b.resumen()}  "
                f"{100 * len(b.documentos) / len(todas):5.1f}% doc  "
                f"{100 * b.n_paginas / total:5.1f}% pág"
            )
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
