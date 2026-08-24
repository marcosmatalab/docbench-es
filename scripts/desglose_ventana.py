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

Escribe `runs/l3/desglose.json` **con la fecha de la lectura dentro**: cuanto más
se aleje de la cosecha, menos vale, y eso hay que poder verlo sin preguntar.

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
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from sello import sello  # noqa: E402

from docbench_es.entity.base import cargar_perfil  # noqa: E402
from docbench_es.entity.boe import BoeAdapter  # noqa: E402

EQUINOCCIO = date(2026, 3, 20)
"""El corte, escrito en el plan ANTES de cosechar: «cruza el equinoccio del 20 de
marzo». No se elige ahora mirando dónde queda mejor la tasa."""


def _trozo(intentados: Counter[date], aceptados: Counter[date]) -> dict[str, object]:
    n_int, n_acc = sum(intentados.values()), sum(aceptados.values())
    return {
        "intentados": n_int,
        "aceptados": n_acc,
        "descartes": n_int - n_acc,
        "tasa_descarte": (n_int - n_acc) / n_int if n_int else 0.0,
        "dias_de_publicacion": len(intentados),
    }


def _linea(nombre: str, t: dict[str, object]) -> str:
    return (
        f"  {nombre:<10} {t['intentados']:>5} intentados · {t['aceptados']:>5} aceptados · "
        f"{t['descartes']:>3} descartes · tasa {float(str(t['tasa_descarte'])):>6.2%} · "
        f"{t['dias_de_publicacion']} días de publicación"
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

    trozos = {
        "invierno": _trozo(inv_i, inv_a),
        "primavera": _trozo(pri_i, pri_a),
        "toda_la_ventana": _trozo(intentados, aceptados),
    }
    salida = {
        "esquema": "docbench-es.desglose-ventana/1",
        # LA FECHA DE LA LECTURA, no la de la cosecha. Es lo que permite juzgar
        # cuánto vale la reconstrucción: pegada a la cosecha vale mucho, seis meses
        # después vale poco, y sin la fecha no se puede saber cuál de las dos es.
        "leido_en": datetime.now(UTC).isoformat(timespec="seconds"),
        "sello": sello(),
        "reconstruido": (
            "los `intentados` por día NO los guardó la cosecha (límite 63): se "
            "vuelven a leer los sumarios con `BoeAdapter.discover`, el código de "
            "producción. Supone que el origen entrega hoy los mismos ítems que "
            "entregó durante la cosecha; el cuadre exacto es lo que lo sostiene"
        ),
        "corte": EQUINOCCIO.isoformat(),
        "ventana": {k: str(v) for k, v in plan["ventana"].items()},
        "dias_sin_boletin": len(adaptador.dias_sin_boletin),
        "rendimiento_docs_por_dia": round(sum(intentados.values()) / len(intentados), 1),
        "trozos": trozos,
    }
    ruta = args.manifiesto.parent / "desglose.json"
    ruta.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"Ventana {plan['ventana']['desde']} a {plan['ventana']['hasta']}, corte {EQUINOCCIO}")
    for nombre, t in trozos.items():
        print(_linea(nombre, t))
    print(f"  días sin boletín: {len(adaptador.dias_sin_boletin)} · fuera del denominador")
    print(f"  rendimiento medido: {salida['rendimiento_docs_por_dia']} docs/día")
    print(f"  escrito {ruta} · leido_en {salida['leido_en']} · sello {salida['sello']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
