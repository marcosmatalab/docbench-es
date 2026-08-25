"""B5-bis · el total, por suma ponderada por páginas, con su intervalo.

    uv run python scripts/estimar_computo.py

## La fórmula, y por qué no es una mediana

    total = suma sobre bandas de (páginas de la banda x coste por página de la banda)

La primera versión de B5-bis iba a responder «¿cabe?» con una **mediana** de segundos
por documento, censurando por tope los que no cupieran. Estaba mal tres veces: excluir
las censuradas sesga la mediana **a la baja** —sólo contribuyen las rápidas—, «¿cabe?»
no es una pregunta sobre la mediana **sino sobre la suma**, y una cota inferior sólo
decide **en un sentido**. El pre-registro completo está en `runs/l5/estimacion.yaml`.

## Y decide el RELOJ, no los segundos de CPU

Son dos monedas y contestan preguntas distintas: los segundos de CPU dicen *cuánto
cómputo consume* y son invariantes a los hilos; el reloj dice *si termina esta noche*.
Se publican las dos, decide el reloj, y el puente —`hilos_efectivos`— va al lado.
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_paginas import DEL_COSTE, repartir  # noqa: E402
from unidad_computo import EXTRACTORES  # noqa: E402

PUNTO = RAIZ / "runs" / "l5" / "computo.json"
ESTIMACION = RAIZ / "runs" / "l5" / "estimacion.yaml"
REMUESTREOS = 10_000


def _num(m: dict[str, object], clave: str) -> float:
    v = m.get(clave)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f"{clave} no es un número en {m.get('extractor')}/{m.get('documento')}")
    return float(v)


def pesos() -> dict[str, int]:
    """Las páginas de cada banda. **Derivadas del manifiesto**, nunca tecleadas."""
    return {n: b.n_paginas for n, b in repartir(DEL_COSTE).items()}


def comprobar_censo() -> None:
    """El censo declarado en el pre-registro contra el que sale del manifiesto."""
    d = yaml.safe_load(ESTIMACION.read_text(encoding="utf-8"))["censo_declarado"]
    bandas = repartir(DEL_COSTE)
    docs = sum(len(b.documentos) for b in bandas.values())
    pags = sum(b.n_paginas for b in bandas.values())
    if (docs, pags) != (int(d["documentos"]), int(d["paginas"])):
        raise SystemExit(
            f"EL CENSO NO CUADRA con runs/l5/estimacion.yaml: el manifiesto da "
            f"{docs} documentos y {pags} páginas; el pre-registro declara "
            f"{d['documentos']} y {d['paginas']}. No se estima nada hasta aclararlo."
        )


def por_banda(medidas: list[dict[str, object]], clave: str) -> dict[str, list[tuple[float, float]]]:
    """Por banda, la lista de `(coste, páginas)` de cada documento medido."""
    fuera: dict[str, list[tuple[float, float]]] = {}
    for m in medidas:
        banda = m.get("banda")
        if isinstance(banda, str):
            fuera.setdefault(banda, []).append((_num(m, clave), _num(m, "paginas")))
    return fuera


def razon(docs: list[tuple[float, float]]) -> float:
    """El estimador de razón de la banda: coste total / páginas totales.

    **No** la media de los coste/página por documento: ésa daría más peso a los
    documentos cortos dentro de la banda, y lo que la suma quiere es el coste medio
    por página de la banda. Ver `runs/l5/estimacion.yaml`, `intervalo`.
    """
    pags = sum(p for _, p in docs)
    if pags <= 0:
        raise ValueError("una banda con cero páginas medidas no tiene coste por página")
    return sum(c for c, _ in docs) / pags


def total(por_b: dict[str, list[tuple[float, float]]], p: dict[str, int]) -> float:
    return sum(p[b] * razon(docs) for b, docs in por_b.items())


def intervalo(
    por_b: dict[str, list[tuple[float, float]]], p: dict[str, int], semilla: int
) -> tuple[float, float]:
    """Bootstrap de percentiles remuestreando **DOCUMENTOS dentro de cada banda**.

    Regla de oro 3 del repo: las páginas de un mismo documento están correlacionadas,
    así que remuestrear páginas daría un intervalo falsamente estrecho.
    """
    rng = random.Random(semilla)
    totales = []
    for _ in range(REMUESTREOS):
        t = 0.0
        for banda, docs in por_b.items():
            re = [docs[rng.randrange(len(docs))] for _ in docs]
            t += p[banda] * razon(re)
        totales.append(t)
    totales.sort()
    return totales[int(0.025 * REMUESTREOS)], totales[int(0.975 * REMUESTREOS) - 1]


def pendiente(docs: list[tuple[float, float]]) -> float:
    """Mínimos cuadrados de coste/página contra páginas. **Comprueba el argumento del
    pre-registro**: si el coste/página baja con la longitud, excluir el documento más
    largo sesga el total al alza, o sea conservador. Si sale positiva, era falso."""
    if len(docs) < 3:
        return float("nan")
    xs = [p for _, p in docs]
    ys = [c / p for c, p in docs]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / den if den else 0.0


def main() -> int:
    comprobar_censo()
    if not PUNTO.exists():
        print(f"  no hay medidas todavía: falta {PUNTO.relative_to(RAIZ)}")
        return 1
    estado = json.loads(PUNTO.read_text(encoding="utf-8"))
    medidas = [m for m in estado.get("medidas", []) if isinstance(m, dict)]
    p = pesos()
    d = yaml.safe_load(ESTIMACION.read_text(encoding="utf-8"))
    semilla = int(d["muestra"]["semilla"])

    print(f"\n  pesos por banda (páginas, del manifiesto): {p} · total {sum(p.values())}")
    print(
        f"  bootstrap: {REMUESTREOS} remuestreos de DOCUMENTOS dentro de banda, semilla {semilla}\n"
    )
    print(
        f"  {'extractor':<13} {'h CPU los 1.000':>16} {'h RELOJ los 1.000':>19} "
        f"{'IC95 reloj (h)':>22} {'hilos ef.':>10} {'n':>3} {'fallos':>7}"
    )

    reloj_total = 0.0
    for nombre in EXTRACTORES:
        suyas = [m for m in medidas if m.get("extractor") == nombre]
        if not suyas:
            continue
        censuradas = [m for m in suyas if m.get("censurada")]
        if censuradas:
            print(
                f"  {nombre:<13} SIN ESTIMACIÓN: {len(censuradas)} unidad(es) censurada(s) "
                "por tope. Una censurada rompe la suma, no sólo la mediana."
            )
            continue
        cpu_b, rel_b = por_banda(suyas, "cpu_s"), por_banda(suyas, "trabajo_s")
        if set(cpu_b) != set(p):
            print(f"  {nombre:<13} SIN ESTIMACIÓN: faltan bandas {sorted(set(p) - set(cpu_b))}")
            continue
        h_cpu, h_rel = total(cpu_b, p) / 3600, total(rel_b, p) / 3600
        lo, hi = (v / 3600 for v in intervalo(rel_b, p, semilla))
        efectivos = statistics.median([_num(m, "hilos_efectivos") for m in suyas])
        fallos = sum(1 for m in suyas if not m.get("ok"))
        reloj_total += h_rel
        print(
            f"  {nombre:<13} {h_cpu:16.2f} {h_rel:19.2f} "
            f"{f'{lo:.2f} a {hi:.2f}':>22} {efectivos:10.2f} {len(suyas):3d} {fallos:7d}"
        )

    print(f"\n  SUMA DE LOS MEDIDOS, en reloj: {reloj_total:.2f} h sobre los 1.000 documentos")
    print(
        "  El presupuesto de runs/l5/computo.yaml son ~4 h. La regla, si no cabe: "
        "SE RECORTAN EXTRACTORES, NO DOCUMENTOS."
    )

    largos = por_banda([m for m in medidas if m.get("banda") == ">50"], "cpu_s")
    if ">50" in largos:
        s = pendiente(largos[">50"])
        signo = (
            "NEGATIVA, el argumento del pre-registro se sostiene"
            if s < 0
            else ("POSITIVA: EL ARGUMENTO DEL PRE-REGISTRO ERA FALSO y hay que publicarlo")
        )
        print(f"\n  pendiente de coste/página contra páginas en la banda >50: {s:+.3e} · {signo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
