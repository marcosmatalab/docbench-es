"""Qué documentos se miden en B5-bis, y en qué orden.

Va aparte de `computo_l5.py` porque elegir la muestra y orquestar la corrida son dos
responsabilidades distintas — y porque el orquestador se pasó de 300 líneas al meterlas
juntas, que es la regla de `CLAUDE.md` avisando de lo mismo.

Todo lo que decide aquí está congelado en `runs/l5/estimacion.yaml`, **escrito y
commiteado antes de medir nada**: la n por banda, la semilla, y qué documento se excluye.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_paginas import DEL_COSTE, repartir  # noqa: E402
from unidad_computo import EXTRACTORES  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"
ESTIMACION = RAIZ / "runs" / "l5" / "estimacion.yaml"


def muestra() -> list[tuple[str, int, str]]:
    """La muestra: **aleatoria dentro de cada banda**, con la semilla de
    `runs/l5/estimacion.yaml`, que se escribió antes de mirar nada.

    No «los más largos de cada banda», que era el método de la primera versión: medía
    el techo de cada banda y luego había que censurar el documento de 309 páginas, y
    **censurar los largos tira el 36,6% de las páginas del corpus**, no la cola. Y no
    «los medianos», que sería cómodo pero dejaría el intervalo sin ser un intervalo de
    muestreo. Aleatoria es lo único que hace que el bootstrap signifique lo que dice.

    Se excluye **un** documento, el de 309 páginas, y sus páginas **siguen contando** en
    el peso de su banda: lo que se excluye es que caiga en la muestra. La dirección de
    ese sesgo está argumentada en el pre-registro —conservadora, porque el coste por
    página baja con la longitud cuando hay un coste fijo por documento— y se comprueba
    después por regresión.
    """
    d = yaml.safe_load(ESTIMACION.read_text(encoding="utf-8"))["muestra"]
    base, n = int(d["n_base_por_banda"]), int(d["n_por_banda"])
    bandas = repartir(DEL_COSTE)
    mas_largo = max(
        ((i, p) for b in bandas.values() for i, p in zip(b.documentos, b.paginas, strict=True)),
        key=lambda x: x[1],
    )[0]
    candidatos = {
        nombre: sorted(
            (i, p)
            for i, p in zip(b.documentos, b.paginas, strict=True)
            if i != mas_largo and (DOCS / f"{i}.pdf").exists()
        )
        for nombre, b in bandas.items()
    }

    # PRIMERA PASADA: el sorteo base, EXACTAMENTE como se hizo la primera vez. Un solo
    # `Random` recorriendo las bandas en orden, igual que entonces, o las 72 medidas ya
    # tomadas dejarían de corresponder a esta muestra.
    rng = random.Random(int(d["semilla"]))
    elegidos = {nombre: rng.sample(c, base) for nombre, c in candidatos.items()}

    # SEGUNDA PASADA: la ampliación de la regla de parada, con SU PROPIA semilla.
    #
    # `random.sample(pob, 9)` NO contiene a `random.sample(pob, 6)`: no son anidados. La
    # regla de parada estaba escrita en el pre-registro y el muestreo no la soportaba —
    # ampliar habría cambiado el sorteo entero y tirado lo medido. Sortear los que faltan
    # DE ENTRE LOS QUE NO SALIERON da un conjunto distribuido igual que un muestreo
    # aleatorio simple de tamaño n, y además deja intacto el de tamaño `base`.
    if n > base:
        extra = random.Random(int(d["semilla_de_la_ampliacion"]))
        for nombre, c in candidatos.items():
            resto = [x for x in c if x not in elegidos[nombre]]
            elegidos[nombre] += extra.sample(resto, n - base)

    return [(i, p, nombre) for nombre, ds in elegidos.items() for i, p in ds]


def unidades(docs: list[tuple[str, int, str]]) -> list[tuple[str, str, int, str]]:
    """El orden de trabajo: por VUELTAS, no por extractor.

    La primera vuelta cubre los cuatro extractores por las tres bandas. Si esto se
    corta a la mitad —y está pensado para poder cortarse—, lo medido sigue teniendo la
    forma completa en vez de cuatro extractores y una sola banda.
    """
    por_banda: dict[str, list[tuple[str, int, str]]] = {}
    for ident, paginas, banda in docs:
        por_banda.setdefault(banda, []).append((ident, paginas, banda))
    vueltas = max(len(v) for v in por_banda.values())
    fuera = []
    for vuelta in range(vueltas):
        for extractor in EXTRACTORES:
            for banda, suyos in por_banda.items():
                if vuelta < len(suyos):
                    ident, paginas, _ = suyos[vuelta]
                    fuera.append((extractor, ident, paginas, banda))
    return fuera
