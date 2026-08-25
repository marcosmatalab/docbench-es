"""B6 · La prueba de humo de L5: `pdfplumber` sobre las 30 tablas de L4. El comando.

    uv run --extra extract-local python scripts/humo_l5.py

## Qué es y qué NO es

**NO es un número publicable.** 30 documentos elegidos por riqueza de spans no son
muestra de nada, y publicar un TEDS de aquí sería exactamente lo que este repo
prohíbe. Las condiciones de parada y esta frase están congeladas en
`runs/l5/humo.yaml`, **escritas y commiteadas antes de correr esto ni una vez**.

Lo que sí es: **la primera vez que la cadena L1→L2→L3→L4 tiene un consumidor real.**
Ése es el patrón que «Construido y NO VALIDADO» de `ESTADO.md` declara — L1 cerró en
verde y **L2 descubrió que `from_html` marcaba mal el 100% de las cabeceras de
PubTabNet**.

## El adaptador de aquí es DESECHABLE, y hay que decirlo

`pdfplumber` devuelve listas de listas; `CanonicalTable` quiere celdas con posición.
Las ~15 líneas que hacen esa conversión viven aquí y **se tiran** cuando L5 escriba
`extract.base` de verdad. No son un extractor: el extractor es `pdfplumber`. La regla
de oro 1 prohíbe construir un extractor propio, no adaptar la salida de uno ajeno —
que es precisamente lo que L5 va a hacer ocho veces.

## El emparejado es OPTIMISTA y va declarado

Un documento tiene varias tablas y la verdad de L4 apunta a una concreta. Emparejarlas
bien es trabajo de L5. Aquí se toman **todas las tablas que `pdfplumber` encuentra en
el documento y se queda la de mejor TEDS**, o sea que **un oráculo elige la tabla**.

**Eso es una cota SUPERIOR, no una medida.** Da igual para lo que esta prueba
pregunta —¿discrimina?, ¿revienta?, ¿cuánto cuesta?— y falsearía cualquier número
publicado, que es la otra razón de que no se publique ninguno.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import pdfplumber  # noqa: E402

from docbench_es.core.canonical import normalize_cell_text  # noqa: E402
from docbench_es.core.teds import teds, teds_struct  # noqa: E402
from docbench_es.entity import boe_xml  # noqa: E402
from docbench_es.types import CanonicalCell, CanonicalTable  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"
FIXTURES = RAIZ / "runs" / "l4" / "fixtures"


def de_pdfplumber(filas: list[list[str | None]], pagina: int) -> CanonicalTable | None:
    """El adaptador DESECHABLE: rejilla rectangular, sin spans. `pdfplumber` no los da."""
    limpias = [f for f in filas if f]
    if not limpias:
        return None
    n_cols = max(len(f) for f in limpias)
    celdas = tuple(
        CanonicalCell(row=i, col=j, text=normalize_cell_text(c or ""))
        for i, f in enumerate(limpias)
        for j, c in enumerate(f)
    )
    return CanonicalTable(celdas, len(limpias), n_cols, (pagina, pagina), None, True, "dataframe")


def verdad_de(fx: dict[str, object]) -> CanonicalTable:
    xml = (DOCS / f"{fx['external_id']}.xml").read_text(encoding="utf-8", errors="replace")
    indice = fx["tabla"]
    return boe_xml.tablas(xml)[int(indice) if isinstance(indice, int) else 0]


def main() -> int:
    fixtures = sorted(FIXTURES.glob("*.json"))
    filas: list[dict[str, object]] = []
    for f in fixtures:
        fx = json.loads(f.read_text(encoding="utf-8"))
        gold = verdad_de(fx)
        t0 = time.perf_counter()
        try:
            with pdfplumber.open(DOCS / f"{fx['external_id']}.pdf") as pdf:
                n_paginas = len(pdf.pages)
                candidatas = [
                    tabla
                    for n, pagina in enumerate(pdf.pages, 1)
                    for bruto in pagina.extract_tables()
                    if (tabla := de_pdfplumber(bruto, n)) is not None
                ]
            error = ""
        except Exception as e:  # el humo también es que reviente, y se cuenta
            candidatas, n_paginas, error = [], 0, f"{type(e).__name__}: {e}"
        segundos = time.perf_counter() - t0
        mejor = max((teds(c, gold) for c in candidatas), default=0.0)
        mejor_s = max((teds_struct(c, gold) for c in candidatas), default=0.0)
        filas.append(
            {
                "fixture": f.stem,
                "teds": round(mejor, 6),
                "teds_s": round(mejor_s, 6),
                "tablas_halladas": len(candidatas),
                "paginas": n_paginas,
                "segundos": round(segundos, 3),
                "error": error,
            }
        )
        print(f"  {f.stem:<22} TEDS {mejor:.4f}  TEDS-S {mejor_s:.4f}  "
              f"{len(candidatas):>3} tablas  {segundos:6.2f} s  {error[:40]}")

    ts = [float(r["teds"]) for r in filas]
    seg = [float(r["segundos"]) for r in filas]
    paginas = sum(int(r["paginas"]) for r in filas)
    rotos = [r for r in filas if r["error"]]
    resumen = {
        "ADVERTENCIA": "NO ES UN NUMERO PUBLICABLE. Ver runs/l5/humo.yaml",
        "emparejado": "un ORACULO elige la tabla: cota superior, no medida",
        "n": len(filas),
        "teds_mediana": round(statistics.median(ts), 6),
        "teds_min": round(min(ts), 6),
        "teds_max": round(max(ts), 6),
        "teds_distintos": len(set(round(x, 4) for x in ts)),
        "revientan": len(rotos),
        "errores": [r["error"] for r in rotos],
        "segundos_mediana_por_documento": round(statistics.median(seg), 3),
        "segundos_total": round(sum(seg), 1),
        "paginas_totales": paginas,
        "segundos_por_pagina": round(sum(seg) / paginas, 3) if paginas else None,
        "por_documento": filas,
    }
    (RAIZ / "runs" / "l5" / "humo.json").write_text(
        json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n  n={len(filas)} · TEDS mediana {resumen['teds_mediana']:.4f} "
          f"· rango {min(ts):.4f}-{max(ts):.4f} · {resumen['teds_distintos']} valores distintos")
    print(f"  revientan: {len(rotos)} de {len(filas)}")
    print(f"  {resumen['segundos_mediana_por_documento']} s/documento mediana · "
          f"{resumen['segundos_por_pagina']} s/pagina · {paginas} paginas")
    print("\n  LAS TRES CONDICIONES DE PARADA (runs/l5/humo.yaml):")
    print(f"    plana .... {'PARA' if resumen['teds_distintos'] <= 1 else 'pasa'}"
          f"  ({resumen['teds_distintos']} valores distintos)")
    print(f"    revienta . {'PARA' if len(rotos) > 3 else 'pasa'}  ({len(rotos)} de 30)")
    caro = float(resumen["segundos_mediana_por_documento"]) > 2.0
    print(f"    caro ..... {'PARA' if caro else 'pasa'}"
          f"  ({resumen['segundos_mediana_por_documento']} s/documento)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
