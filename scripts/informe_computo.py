"""El informe de B5-bis: segundos de CPU por documento y por página.

Va aparte de `computo_l5.py` porque son dos responsabilidades distintas —medir y
contar lo medido— y porque el orquestador ya rozaba las 300 líneas. Mismo criterio
que `informe_l4.py` frente a `comparar_verdad.py`.

**La regla que gobierna este fichero**: una unidad censurada por tope es una COTA
INFERIOR, no una medida, y no entra en ninguna mediana. Ver `runs/l5/termica.yaml`.
"""

from __future__ import annotations

import statistics
from typing import Protocol

from gobernador import Registro
from unidad_computo import EXTRACTORES


class ConMedidas(Protocol):
    """Lo que el informe necesita del punto de control, y nada más."""

    medidas: list[Registro]
    termica: Registro


def numero(m: Registro, clave: str) -> float:
    """Un campo numérico del registro. **Revienta si no lo es**, en vez de devolver 0.0:
    un cero silencioso en el denominador de un s/página se publicaría sin que nadie lo
    notara."""
    v = m.get(clave)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(
            f"{clave} no es un número en {m.get('extractor')}/{m.get('documento')}: {v!r}"
        )
    return float(v)


def _comprobar_el_ciclo(medidas: list[Registro]) -> None:
    """La afirmación del ciclo de trabajo, comprobada **contra los datos de cada unidad**.

    El ciclo promete `cpu_s / reloj_s <= fracción x núcleos`. Es la única barrera que
    aguanta —ni `OMP_NUM_THREADS` ni `taskset` acotan a `pymupdf4llm`, que abre 45 hebras
    que se reponen la afinidad— así que si dejara de cumplirse no habría ninguna otra, y
    nadie se enteraría. Se comprueba aquí y se nombra la unidad que la incumpla.
    """
    rotas = [
        m
        for m in medidas
        if "cpu_por_reloj" in m and numero(m, "cpu_por_reloj") > numero(m, "techo_del_ciclo")
    ]
    con_dato = [m for m in medidas if "cpu_por_reloj" in m]
    if not con_dato:
        print("\n  ciclo de trabajo: sin datos que comprobar")
        return
    peor = max(con_dato, key=lambda m: numero(m, "cpu_por_reloj"))
    if rotas:
        print(f"\n  EL CICLO NO ACOTÓ en {len(rotas)} de {len(con_dato)} unidades:")
        for m in rotas[:5]:
            print(
                f"    {m.get('extractor')} · {m.get('documento')}: "
                f"{numero(m, 'cpu_por_reloj'):.2f} núcleos sobre un tope de "
                f"{numero(m, 'techo_del_ciclo'):.2f}"
            )
        return
    print(
        f"\n  ciclo de trabajo: las {len(con_dato)} unidades por debajo del tope. "
        f"La peor, {peor.get('extractor')} con {numero(peor, 'cpu_por_reloj'):.2f} "
        f"núcleos de media sobre {numero(peor, 'techo_del_ciclo'):.2f}"
    )


def informe(estado: ConMedidas) -> None:
    """Segundos de CPU por documento y por página, que es lo que hace sumable el total."""
    if not estado.medidas:
        print("  sin medidas todavía")
        return
    censo = sum(1 for m in estado.medidas if m.get("censurada"))
    print(
        f"\n  {len(estado.medidas)} unidades medidas · moneda primaria: segundos de CPU"
        f"{f' · {censo} CENSURADAS por tope' if censo else ''}\n"
    )
    print(
        f"  {'extractor':<13} {'s CPU/doc':>10} {'s CPU/pág':>10} {'s reloj/doc':>12} "
        f"{'RSS MB':>8} {'fallos':>7} {'cens':>5} {'n':>4}"
    )
    for nombre in EXTRACTORES:
        suyas = [m for m in estado.medidas if m.get("extractor") == nombre]
        if not suyas:
            continue
        # Una censurada es una COTA INFERIOR, no una medida: no entra en la mediana.
        # Comerse una como si lo fuera hundiría la mediana justo del caso más caro.
        limpias = [m for m in suyas if not m.get("censurada")]
        cortadas = len(suyas) - len(limpias)
        if not limpias:
            cota = min(numero(m, "cpu_s") for m in suyas)
            print(
                f"  {nombre:<13} {'—':>10} {'—':>10} {'—':>12} {'—':>8} {'—':>7} "
                f"{cortadas:5d} {len(suyas):4d}   TODAS censuradas: cota inferior "
                f"{cota:.0f} s CPU"
            )
            continue
        cpu = [numero(m, "cpu_s") for m in limpias]
        paginas = sum(numero(m, "paginas") for m in limpias)
        fallos = sum(1 for m in limpias if not m.get("ok"))
        marca = "≥" if cortadas else " "
        print(
            f"  {nombre:<13} {statistics.median(cpu):10.3f} "
            f"{marca}{sum(cpu) / paginas:9.4f} "
            f"{statistics.median([numero(m, 'reloj_s') for m in limpias]):12.3f} "
            f"{max(numero(m, 'max_rss_mb') for m in limpias):8.0f} {fallos:7d} "
            f"{cortadas:5d} {len(suyas):4d}"
        )
    if censo:
        print(
            "\n  «≥» = hay unidades censuradas por tope: el s/pág de esa fila es una COTA\n"
            "  INFERIOR, no su valor. Ver runs/l5/termica.yaml, censura."
        )
    _comprobar_el_ciclo(estado.medidas)
    print(f"\n  térmica de la sesión: {estado.termica or '—'}")
    print("\n  reproducir: uv run --extra extract-local python scripts/computo_l5.py")
