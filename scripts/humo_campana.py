"""Los 12 documentos del humo de la campaña, elegidos por COBERTURA y no por azar.

    uv run python scripts/humo_campana.py            # imprime la tabla
    uv run python scripts/humo_campana.py --escribir # congela runs/l5/humo_campana.json

## Por qué existe

La campaña de los 616 tiene que ser **una sola corrida con los cuatro extractores
dentro**: el corredor rechaza reanudar sobre otro árbol, y con razón —filas de commits
distintos no son una tabla, son cuatro medidas puestas al lado—. La consecuencia es que
**si el cuarto extractor revienta en el documento 400, se pierde la corrida entera**.

Doce documentos con los cuatro extractores cuestan minutos. Es un seguro barato sobre
cuatro horas.

## Y por qué NO es una muestra

Se toman **los dos primeros por identificador** de cada una de las seis celdas
—tres bandas de páginas por con/sin tabla—. Es determinista, no lleva semilla y **no
pretende representar nada**: su trabajo es tocar los sitios donde un extractor nuevo se
rompe de formas distintas.

* **la banda larga** (>50 páginas) es donde aparecen el agotamiento de memoria y los
  tiempos de corte, y son **36,6% del cómputo** aunque sean 38 documentos;
* **los documentos sin tabla** son el control negativo de detección, y son donde un
  extractor que inventa tablas se ve — no en los que sí las tienen.

**Ningún número de esta corrida se publica.** Lo que se mira es si termina.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_paginas import DEL_COSTE  # noqa: E402

POBLACION = RAIZ / "runs" / "l5" / "poblacion.json"
MANIFIESTO = RAIZ / "runs" / "l3" / "manifiesto.json"
DESTINO = RAIZ / "runs" / "l5" / "humo_campana.json"
POR_CELDA = 2
"""Dos por celda: uno solo no distingue «este documento» de «esta clase de documento»."""


def _banda(paginas: int) -> str:
    for nombre, (lo, hi) in DEL_COSTE.items():
        if lo <= paginas <= hi:
            return nombre
    raise ValueError(f"{paginas} páginas no cae en ninguna banda")


def elegidos() -> list[dict[str, object]]:
    """Los 12, con la celda que cubren. Determinista: sin semilla y sin azar."""
    pob = json.loads(POBLACION.read_text(encoding="utf-8"))
    con_tabla = set(pob["con_tabla"])
    sin_tabla = {x for banda in pob["sin_tabla_muestreados"].values() for x in banda}
    paginas = {
        str(d["external_id"]): int(d["n_pages"])
        for d in json.loads(MANIFIESTO.read_text(encoding="utf-8"))["documentos"]
    }
    celdas: dict[tuple[str, bool], list[str]] = {}
    for ident in sorted(con_tabla | sin_tabla):
        if ident not in paginas:
            continue
        celdas.setdefault((_banda(paginas[ident]), ident in con_tabla), []).append(ident)
    fuera: list[dict[str, object]] = []
    for banda in DEL_COSTE:
        for con in (True, False):
            for ident in celdas.get((banda, con), [])[:POR_CELDA]:
                fuera.append(
                    {"id": ident, "banda": banda, "con_tabla": con, "paginas": paginas[ident]}
                )
    return fuera


def main(argv: list[str]) -> int:
    docs = elegidos()
    print(f"\n  {len(docs)} documentos · {POR_CELDA} por celda · 3 bandas x con/sin tabla\n")
    print(f"  {'documento':<20} {'banda':>7} {'paginas':>8} {'tabla':>6}")
    for d in docs:
        tabla = "si" if d["con_tabla"] else "NO"
        print(f"  {d['id']:<20} {d['banda']:>7} {d['paginas']:>8} {tabla:>6}")
    faltan = [
        (b, c)
        for b in DEL_COSTE
        for c in (True, False)
        if sum(1 for d in docs if d["banda"] == b and d["con_tabla"] == c) < POR_CELDA
    ]
    if faltan:
        print(f"\n  CELDAS INCOMPLETAS: {faltan}. El humo no cubre lo que dice cubrir.")
    if "--escribir" in argv:
        DESTINO.write_text(json.dumps([str(d["id"]) for d in docs], indent=1), encoding="utf-8")
        print(f"\n  escrito {DESTINO.relative_to(RAIZ)}")
    return 1 if faltan else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
