"""Una serie de la puerta, y **la comparación entre dos**. El estadístico y su ruido.

## Por qué existe, y sale de una tabla que llevaba cuatro días publicada

`RESULTS.md` publicó el 24 ago 2026 dos series de 40 el mismo día, y tituló *«el
protocolo reproduce a 10 ms»*. Los 10 ms son de la **mediana**. En esa misma tabla, sin
restar, están los dos p90: **6262 y 6327**, o sea **65 ms**. Y el techo se compara contra
el p90, no contra la mediana.

> **El proyecto eligió el estadístico conceptualmente correcto y validó el estable.**
> Son dos, y sólo uno tenía aval.

Tiene causa mecánica y no sólo aritmética: el p90 de n=40 se estima con unas **cuatro**
observaciones de la cola; la mediana usa las cuarenta. Un estimador de cola con cuatro
puntos se mueve más que uno central con cuarenta, y eso no se arregla mirándolo mejor.

## Lo que cambia, que es la regla de decisión y no el estadístico

**El techo se sigue comparando contra el p90** —gatear sobre la mediana escondería la
cola, que es justo lo que un techo existe para vigilar—, pero **una sola serie ya no
decide**: el techo se considera roto cuando **todas** las series miden por encima. Con
dos, cuesta 40 minutos una vez por hito en vez de 20, y a cambio construye sola, hito a
hito, la serie de reproducibilidad del p90 que hoy no existe. Ver ADR-0048.

**Y la disciplina de la sección que lo destapó se aplica igual aquí:** con n=2 no se
publica una tasa. Se publica el par.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

ROTO, NO_CONCLUYENTE = 1, 3
"""Códigos de salida. El **3** es la aportación de ADR-0048: el caso en que unas series
pasan del techo y otras no **no es verde**, y darle el código del verde sería contestar
con una moneda al aire una pregunta que el instrumento sabe que no ha resuelto."""


@dataclass(frozen=True)
class Serie:
    """Una serie de 40 corridas en frío. Los datos crudos, no el resumen.

    Guarda los tiempos y no sus estadísticos porque **el p90 de dos series juntas no es
    el p90 de sus p90**, y alguna vez habrá que recalcular sobre el conjunto.
    """

    tiempos: tuple[int, ...]
    cargas: tuple[float, ...]
    medianas_por_tanda: tuple[float, ...]
    descartadas: int

    @property
    def p90(self) -> int:
        """El **37.º de 40**: `ordenadas[int(0,90·n)]`, el percentil empírico 92,5.

        La convención está declarada en ADR-0022 y **no se toca**: es conservadora
        —nunca subestima— y cambiarla ahora haría incomparables L0 a L7, que es justo
        lo que el protocolo existe para evitar.
        """
        ordenadas = sorted(self.tiempos)
        return ordenadas[min(len(ordenadas) - 1, int(0.90 * len(ordenadas)))]

    @property
    def mediana(self) -> int:
        return int(statistics.median(self.tiempos))


def _desviacion(muestras: tuple[int, ...]) -> str:
    """La desviación típica, o «n/a» con una sola muestra.

    `statistics.stdev` revienta con n=1, y `--por-tanda 1` es una invocación legal del
    script. Con una muestra la dispersión no es cero, es que **no se ha medido**.
    """
    return f"{statistics.stdev(muestras):.0f}" if len(muestras) > 1 else "n/a (n=1)"


def resumen(serie: Serie, techo: int) -> str:
    """El bloque de una serie. **El máximo va SIEMPRE al lado del p90** (ADR-0022)."""
    ordenadas = tuple(sorted(serie.tiempos))
    return (
        f"\n  n={len(ordenadas)} en verde · descartadas por rc!=0: {serie.descartadas}\n"
        f"  mínimo {ordenadas[0]} · mediana {serie.mediana} · "
        f"p90 {serie.p90} · máximo {ordenadas[-1]}\n"
        f"  desviación típica {_desviacion(ordenadas)} · "
        f"medianas por tanda {int(min(serie.medianas_por_tanda))}"
        f"-{int(max(serie.medianas_por_tanda))}\n"
        f"  carga de la máquina: mediana {statistics.median(serie.cargas):.2f} · "
        f"rango {min(serie.cargas):.2f} a {max(serie.cargas):.2f}\n"
        f"  techo {techo} · margen en el p90: {techo - serie.p90} ms"
    )


def comparacion(series: tuple[Serie, ...]) -> str:
    """El par, **restado**, que es la operación que nadie hizo durante cuatro días.

    Con una sola serie lo dice en vez de callarse: una serie no mide reproducibilidad,
    y un instrumento que imprime la misma cara con n=1 y con n=2 miente por omisión.
    """
    if len(series) < 2:
        return (
            "\n  UNA SOLA SERIE: no mide la reproducibilidad del p90 y no decide el techo"
            " (ADR-0048).\n  Diagnostica, que es otra cosa."
        )
    p90s = [s.p90 for s in series]
    medianas = [s.mediana for s in series]
    filas = "  ".join(
        f"serie {i + 1}: p90 {s.p90} · mediana {s.mediana}" for i, s in enumerate(series)
    )
    return (
        f"\n  EL PAR, RESTADO\n  {filas}\n"
        f"  entre la mayor y la menor: **{max(p90s) - min(p90s)} ms en el p90** y"
        f" {max(medianas) - min(medianas)} ms en la mediana\n"
        f"  Con n={len(series)} no se publica una tasa: se publica el par. Esto NO dice"
        " que la reproducibilidad\n  del p90 SEA esa; dice que estas series difirieron eso."
    )


def veredicto(series: tuple[Serie, ...], techo: int) -> tuple[int, str]:
    """**La regla de decisión de ADR-0048**, sin el bucle de medir, para poder probarla.

    Tres direcciones y **tres códigos**, porque son tres cosas distintas:

    | Cuántas pasan del techo | Código | Qué significa |
    |---|---|---|
    | todas | 1 | roto: se re-justifica o se reestructura |
    | algunas | **3** | **no concluyente**: el margen es menor que el ruido del estimador |
    | ninguna | 0 | dentro |
    """
    pasan = [s for s in series if s.p90 > techo]
    p90s = [s.p90 for s in series]
    if not pasan:
        return 0, "OK"
    if len(pasan) == len(series):
        cuantas = "la única serie" if len(series) == 1 else f"las {len(series)} series"
        aviso = (
            f"EL P90 PASA DEL TECHO en {cuantas}: {p90s}.\n"
            "  Ver ADR-0022: re-justificar o reestructurar, y ANTES `--durations`."
        )
        if len(series) == 1:
            aviso += (
                "\n  Y una sola serie DIAGNOSTICA pero NO decide el techo (ADR-0048):"
                " para decidir hacen falta dos."
            )
        return ROTO, aviso
    margen = min(abs(techo - p) for p in p90s)
    return NO_CONCLUYENTE, (
        f"NO CONCLUYENTE: {len(pasan)} de {len(series)} series pasan del techo {techo}: {p90s}.\n"
        f"  El margen más pequeño contra el techo es de {margen} ms y las series difieren"
        f" {max(p90s) - min(p90s)} ms\n  entre ellas. Decidir con esto sería una moneda al aire."
        " No se sube el techo y no se declara roto:\n  se anota el par y se vuelve a medir en el"
        " cierre (ADR-0048)."
    )
