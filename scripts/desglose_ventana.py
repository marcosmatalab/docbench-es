"""La tasa de descarte por PARTES de la ventana. **Reconstruida, y se dice.**

La ventana de L3 cruza el equinoccio del 20 de marzo a propósito: para que la tasa
publicada no sea de una sola época. Pero **el manifiesto no permite partirla**: los
1.000 aceptados llevan su `fecha_sumario` y los 43 descartes viven en un contador
sin fecha (`Cosecha.por_causa`). Un descarte sin fecha no se puede atribuir a un
trozo de la ventana, así que **el propósito de haberla elegido cruzada no se podía
cumplir con lo que se guardó**. Es el límite 63.

Lo que hace esto es reconstruir el denominador **por el mismo camino por el que se
cosechó**: `BoeAdapter.discover`, que es el código de producción y no una copia,
sobre los mismos sumarios. Sólo sumarios: **ni un documento**. Y `discover` es
determinista —recorre los días en orden y los ítems en el orden del sumario— así
que los `intentados` primeros refs que entrega SON los que se intentaron.

    uv run python scripts/desglose_ventana.py runs/l3/manifiesto.json

**Lo que esto NO es.** No es una medición nueva de la cosecha: es una lectura del
origen posterior a ella. Si el BOE reordenara o retirara un ítem de un sumario
viejo, la reconstrucción y la cosecha discreparían — y por eso el script comprueba
que el total reconstruido cuadra con `intentados`, y se cae si no.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from docbench_es.entity.base import cargar_perfil  # noqa: E402
from docbench_es.entity.boe import BoeAdapter  # noqa: E402

EQUINOCCIO = date(2026, 3, 20)
"""El corte, escrito en el plan ANTES de cosechar: «cruza el equinoccio del 20 de
marzo». No se elige ahora mirando dónde queda mejor la tasa."""


def _trozo(nombre: str, intentados: Counter[date], aceptados: Counter[date]) -> str:
    n_int, n_acc = sum(intentados.values()), sum(aceptados.values())
    descartes = n_int - n_acc
    tasa = descartes / n_int if n_int else 0.0
    dias = len(intentados)
    return (
        f"  {nombre:<10} {n_int:>5} intentados · {n_acc:>5} aceptados · "
        f"{descartes:>3} descartes · tasa {tasa:>6.2%} · {dias} días de publicación"
    )


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("manifiesto", type=Path)
    partes.add_argument("--plan", type=Path, default=RAIZ / "runs" / "l3" / "plan.yaml")
    args = partes.parse_args()

    manifiesto = json.loads(args.manifiesto.read_text(encoding="utf-8"))
    plan = yaml.safe_load(args.plan.read_text(encoding="utf-8"))
    intentados_total = int(manifiesto["emparejado"]["intentados"])

    adaptador = BoeAdapter(cargar_perfil(RAIZ / "entities" / "boe.yaml"))
    refs = []
    for ref in adaptador.discover(plan["ventana"]["desde"], plan["ventana"]["hasta"]):
        refs.append(ref)
        if len(refs) >= intentados_total:
            break
    if len(refs) != intentados_total:
        print(f"NO CUADRA: el origen entrega {len(refs)} y la cosecha intentó {intentados_total}")
        return 1

    intentados: Counter[date] = Counter(r.published_on for r in refs if r.published_on)
    aceptados: Counter[date] = Counter(
        date.fromisoformat(str(d["fecha_sumario"])) for d in manifiesto["documentos"]
    )
    ajenos = set(aceptados) - set(intentados)
    if ajenos:
        print(f"NO CUADRA: aceptados en días que no se intentaron: {sorted(ajenos)}")
        return 1

    inv_i = Counter({d: n for d, n in intentados.items() if d < EQUINOCCIO})
    inv_a = Counter({d: n for d, n in aceptados.items() if d < EQUINOCCIO})
    pri_i = Counter({d: n for d, n in intentados.items() if d >= EQUINOCCIO})
    pri_a = Counter({d: n for d, n in aceptados.items() if d >= EQUINOCCIO})

    print(f"Ventana {plan['ventana']['desde']} a {plan['ventana']['hasta']}, corte {EQUINOCCIO}")
    print(_trozo("invierno", inv_i, inv_a))
    print(_trozo("primavera", pri_i, pri_a))
    print(_trozo("TODA", intentados, aceptados))
    print(f"  días sin boletín: {len(adaptador.dias_sin_boletin)} · fuera del denominador")
    print(f"  rendimiento medido: {sum(intentados.values()) / len(intentados):.1f} docs/día")
    return 0


if __name__ == "__main__":
    sys.exit(main())
