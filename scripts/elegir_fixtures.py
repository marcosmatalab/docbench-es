"""La muestra de tablas de L4, **estratificada y por semilla**.

**Por qué existe este script en vez de elegirlas a ojo.** Quien elige la muestra,
quien transcribe las tablas y quien escribe el código que se compara contra ellas
son **la misma persona**. Elegir a ojo produciría, sin mala fe, una muestra de
tablas cómodas — y la muestra ES el instrumento de medida del hito. La semilla
está en `runs/l4/plan.yaml`, commiteada **antes** de que esto se ejecutara ni una
vez, así que «no me gusta ésta, tiro otra vez» no se puede hacer sin que se vea.

    uv run python scripts/elegir_fixtures.py

## Las tres decisiones que van en el plan y no aquí

- **La población son los 338 documentos CON TABLA**, no los 1.000 del corpus. Con
  1.000, dos de cada tres extracciones caerían en un documento sin tabla y la
  muestra real acabaría siendo «lo que quede».
- **La unidad es el DOCUMENTO** (regla de oro 3), y de cada uno sale **una tabla**,
  también por semilla. Tomarlas todas dejaría que el documento de 332 tablas
  decidiera el resultado él solo.
- **Estratificado** sobre dos estratos x tres bandas, proporcional a la población.

## Lo que NO hace

**No mira las tablas.** Elige identificadores y devuelve un índice; quien transcribe
abre el PDF después. Si este script ordenara por algo de la tabla —tamaño, número
de celdas— estaría eligiendo por una propiedad del objeto medido.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
PLAN = RAIZ / "runs" / "l4" / "plan.yaml"
SALIDA = RAIZ / "runs" / "l4" / "seleccion.json"


def _banda(paginas: int, bandas: dict[str, list[int | None]]) -> str:
    for nombre, (a, b) in bandas.items():
        if paginas >= (a or 0) and (b is None or paginas <= b):
            return nombre
    return "?"


def main() -> int:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    censo = json.loads((RAIZ / plan["censo"]).read_text(encoding="utf-8"))

    # EL SELLO PRIMERO. Si el censo no es el que el plan congeló, la selección no
    # es reproducible: el corpus de tablas cambió el 24 ago 2026 al arreglar el
    # grupo de filas, y una muestra del censo viejo no describe este corpus.
    sello = str(censo["condiciones"]["sello"])
    if sello != str(plan["censo_sello"]):
        print(f"NO CUADRA: el censo dice sello {sello} y el plan congeló {plan['censo_sello']}")
        print("  Vuelve a correr scripts/censo_corpus.py, o el plan apunta a otro corpus.")
        return 1

    con_tabla = [f for f in censo["por_documento"] if int(f["n_tablas_from_html"]) > 0]
    if len(con_tabla) != int(plan["poblacion"]["documentos_con_tabla"]):
        esperado = plan["poblacion"]["documentos_con_tabla"]
        print(f"NO CUADRA: {len(con_tabla)} documentos con tabla, el plan dice {esperado}")
        return 1

    celdas: dict[tuple[str, str], list[dict[str, object]]] = {}
    for f in con_tabla:
        for e in f["estratos"]:
            celdas.setdefault((e, _banda(int(f["n_pages"]), plan["bandas"])), []).append(f)

    azar = random.Random(int(plan["semilla"]))
    elegidos: list[dict[str, object]] = []
    for fila in plan["estratos"]:
        clave = (fila["estrato"], fila["banda"])
        disponibles = sorted(celdas.get(clave, []), key=lambda f: str(f["external_id"]))
        if len(disponibles) != int(fila["poblacion"]):
            print(f"NO CUADRA: {clave} tiene {len(disponibles)}, el plan dice {fila['poblacion']}")
            return 1
        for doc in azar.sample(disponibles, int(fila["n"])):
            # La tabla, también por semilla: la muestra no la elige quien la mira.
            indice = azar.randrange(int(doc["n_tablas_from_html"]))
            elegidos.append(
                {
                    "external_id": str(doc["external_id"]),
                    "tabla": indice,
                    "estrato": fila["estrato"],
                    "banda": fila["banda"],
                    "n_pages": int(doc["n_pages"]),
                    "n_tablas_del_documento": int(doc["n_tablas_from_html"]),
                    "ya_inspeccionado": str(doc["external_id"]) in plan["ya_inspeccionadas"],
                }
            )

    elegidos.sort(key=lambda d: (str(d["external_id"]), int(d["tabla"])))  # type: ignore[arg-type]
    salida = {
        "esquema": "docbench-es.seleccion-l4/1",
        "plan_hash": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "censo_sello": sello,
        "semilla": int(plan["semilla"]),
        "n": len(elegidos),
        "ya_inspeccionados": sum(1 for d in elegidos if d["ya_inspeccionado"]),
        "seleccion": elegidos,
    }
    SALIDA.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")

    print(
        f"{len(elegidos)} tablas de {len(elegidos)} documentos distintos · "
        f"semilla {plan['semilla']}"
    )
    print(f"  plan_hash {salida['plan_hash'][:12]}… · censo {sello}")
    print(f"  ya inspeccionadas antes: {salida['ya_inspeccionados']}")
    for d in elegidos:
        marca = "  (YA VISTA)" if d["ya_inspeccionado"] else ""
        print(
            f"    {d['external_id']} t{d['tabla']:<3} {d['estrato']:<18}{d['banda']:<6}"
            f"{d['n_pages']:>4} pág · {d['n_tablas_del_documento']:>3} tablas{marca}"
        )
    print(f"\n  escrito {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
