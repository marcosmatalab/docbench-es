"""Sobre qué documentos corre L5, y por qué son dos poblaciones y no una.

    uv run python scripts/poblacion_l5.py

## El número que abre la pregunta

**662 de los 1.000 documentos no tienen ni una tabla** en la verdad de referencia. No
puntúan: salen `NO_APLICABLE`, nunca 0,00. Y cuestan **el 54,7% del cómputo** — más que
su 41,0% de las páginas, porque son cortos y la página corta cuesta más: el coste fijo
por documento se reparte entre menos páginas. En `docling`, una página de la banda `<=10`
cuesta **5,2 veces** más que una de la banda `>50`.

## Y lo que se perdería tirándolos, que es lo que casi nadie mide

Un extractor que **inventa** una tabla donde no la hay está haciendo algo malo, y los
662 sin tabla son **el único sitio donde eso se ve**. Es un control negativo de
detección. Así que no se tiran: se muestrean.

Dos poblaciones, dos denominadores, dos preguntas:

* **los 338 con tabla** → censo. TEDS y todo lo demás. Sin intervalo (ADR-0015).
* **los 662 sin tabla** → muestra estratificada declarada. Tasa de falso positivo de
  detección, con intervalo de Wilson.

El diseño y sus porqués están congelados en `runs/l5/poblacion.yaml`.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_paginas import DEL_COSTE, paginas  # noqa: E402
from censo_tablas import publicado  # noqa: E402

PLAN = RAIZ / "runs" / "l5" / "poblacion.yaml"
# El modelo de coste sale de la corrida de POCOS HILOS, que es la configuración en la
# que L5 va a correr: el experimento A midió que 28 hilos por unidad cuestan entre 4 y
# 12 veces la CPU para el mismo reloj o peor. Ver LIMITS 89.
MEDIDAS = RAIZ / "runs" / "l5" / "computo_base_2hilos.json"


def _banda(n: int) -> str:
    for nombre, (lo, hi) in DEL_COSTE.items():
        if lo <= n <= hi:
            return nombre
    raise ValueError(f"{n} páginas no cae en ninguna banda")


def coste_por_pagina() -> dict[tuple[str, str], float]:
    """`(extractor, banda)` → segundos de RELOJ por página, de lo medido en B5-bis."""
    d = json.loads(MEDIDAS.read_text(encoding="utf-8"))
    por: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for m in d["medidas"]:
        por.setdefault((str(m["extractor"]), str(m["banda"])), []).append(
            (float(m["trabajo_s"]), float(m["paginas"]))
        )
    return {k: sum(t for t, _ in v) / sum(p for _, p in v) for k, v in por.items()}


def horas(ids: list[str], pag: dict[str, int], coste: dict[tuple[str, str], float]) -> float:
    """Las horas de reloj de procesar esos documentos con los extractores medidos."""
    extractores = sorted({e for e, _ in coste})
    total = 0.0
    for i in ids:
        b = _banda(pag[i])
        total += pag[i] * sum(coste[(e, b)] for e in extractores)
    return total / 3600


def poblaciones() -> tuple[list[str], dict[str, list[str]]]:
    """Los 338 que puntúan, y los 662 que no repartidos por estrato."""
    # EL CENSO PUBLICADO, NO LOS 1.000 XML. Son el mismo número —lo comprueba
    # `test_datos_fuera_de_git.py` cuando el corpus está— y la diferencia es que así
    # esto corre en un clon frío. Antes arrastraba los 362 MB de `runs/l3/docs`, y
    # `censo_tablas` devolvía `{}` sin ellos: la predicción salía **distinta** en vez de
    # fallar. Y de paso es el 90% del coste del instrumento: 44 ms de los 48.
    pag, tab = paginas(), publicado()
    con = sorted(i for i in pag if tab.get(i, 0) > 0)
    estratos: dict[str, list[str]] = {b: [] for b in DEL_COSTE}
    for i in sorted(pag):
        if tab.get(i, 0) == 0:
            estratos[_banda(pag[i])].append(i)
    return con, estratos


def muestra_sin_tabla() -> dict[str, list[str]]:
    """La muestra de los que no puntúan, con la semilla y los tamaños del plan.

    **Un estrato entero cuando es pequeño, muestra cuando es grande.** Con asignación
    proporcional, el estrato `>50` —que son SEIS documentos— habría recibido dos, y una
    tasa sobre dos documentos no es una tasa. Censando los estratos pequeños se tiene su
    valor exacto sin intervalo (ADR-0015) y se gasta la muestra donde hay población.
    """
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))["muestra_de_los_que_no_puntuan"]
    _, estratos = poblaciones()
    rng = random.Random(int(plan["semilla"]))
    fuera: dict[str, list[str]] = {}
    for nombre, ids in estratos.items():
        n = plan["tamanos"][nombre]
        if n == "censo" or int(n) >= len(ids):
            fuera[nombre] = list(ids)
        else:
            fuera[nombre] = sorted(rng.sample(ids, int(n)))
    return fuera


def main() -> int:
    pag = paginas()
    con, estratos = poblaciones()
    coste = coste_por_pagina()
    muestra = muestra_sin_tabla()

    print(f"\n  {'población':<34} {'docs':>5} {'páginas':>8} {'horas':>7}")
    print(
        f"  {'CON tabla · censo, puntúan':<34} {len(con):5d} "
        f"{sum(pag[i] for i in con):8d} {horas(con, pag, coste):7.2f}"
    )
    for nombre in DEL_COSTE:
        ids, todos = muestra[nombre], estratos[nombre]
        etiqueta = "censo" if len(ids) == len(todos) else f"muestra de {len(todos)}"
        print(
            f"  {f'SIN tabla {nombre} · {etiqueta}':<34} {len(ids):5d} "
            f"{sum(pag[i] for i in ids):8d} {horas(ids, pag, coste):7.2f}"
        )
    elegidos = con + [i for ids in muestra.values() for i in ids]
    print(
        f"  {'TOTAL de la campaña':<34} {len(elegidos):5d} "
        f"{sum(pag[i] for i in elegidos):8d} {horas(elegidos, pag, coste):7.2f}"
    )
    print(
        f"  {'(los 1.000, para comparar)':<34} {1000:5d} "
        f"{sum(pag.values()):8d} {horas(sorted(pag), pag, coste):7.2f}"
    )
    print(f"\n  extractores medidos: {sorted({e for e, _ in coste})}")
    print(
        f"  horas de RELOJ con el modelo de {MEDIDAS.name}, o sea la configuración de\n"
        "  POCOS HILOS, que es en la que L5 va a correr. Ver LIMITS 89.\n"
        "  Reproducir: uv run python scripts/poblacion_l5.py"
    )

    (RAIZ / "runs" / "l5" / "poblacion.json").write_text(
        json.dumps({"con_tabla": con, "sin_tabla_muestreados": muestra}, ensure_ascii=False),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
