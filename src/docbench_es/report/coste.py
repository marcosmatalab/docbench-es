"""§12 · El bloque de coste. **Va aparte porque el denominador no es el mismo.**

Y ésa es la razón principal, por encima de que el coste no sea calidad:

* el **TEDS** se calcula sobre el conjunto evaluable —como mucho los 338 con tabla, y
  **distinto para cada extractor**, porque cada uno acierta el recuento en otros;
* el **coste** se calcula sobre **los 616**, porque un documento cuesta tiempo aunque no
  puntúe, y uno que falla cuesta tiempo y no devuelve nada.

**Misma fila implica mismo denominador.** Meter s/página junto al TEDS sería exactamente
el 2.283 otra vez: dos números con dos poblaciones leyéndose como si tuvieran una.

## Y mira hacia adelante

Coste y calidad son **dos ejes**. El día que entren extractores por API, lo que se publica
es una **curva coste-exactitud**, no una tabla más ancha. Un bloque aparte ya tiene la
forma que esa curva necesita; trece columnas no la tienen.

## La máquina se declara, y de dónde sale importa

Un coste por página de una herramienta local sin la máquina al lado es un número de **esta**
máquina presentado como si fuera de cualquiera. Sale del **sello de la corrida**, no de la
máquina que informa: el informe se puede regenerar meses después y en otro sitio. El modelo
de CPU entró al sello el 27 ago 2026, así que **una corrida anterior no lo trae**, y eso se
imprime en vez de rellenarse con lo que haya debajo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.nivel1 import Nivel1

__all__ = ["tabla_coste"]


def _maquina(sello: Mapping[str, object]) -> str:
    """La línea de máquina, **con el hueco dicho cuando lo hay**."""
    cpu = sello.get("cpu")
    modelo = str(cpu) if cpu else "modelo de CPU **no registrado** (sello anterior al campo)"
    return (
        f"**Máquina** (del sello de la corrida, no de la que informa): {modelo} · "
        f"{sello.get('cpus', '?')} CPU visibles · carga "
        f"{str(sello.get('carga', '?')).replace('.', ',')} al "
        "arrancar · **un solo proceso, secuencial**, un documento y un extractor cada vez."
    )


def tabla_coste(filas: Mapping[str, Nivel1], sello: Mapping[str, object]) -> list[str]:
    """El coste de los locales: **tiempo**, que es lo único que gastan.

    `Cost.eur` es **cero MEDIDO**, no un hueco. La distinción es la misma que separa
    `n/a` de `0,00`: un cero medido es un dato, y un dato ausente no lo es.
    """
    if not filas:
        return ["**Sin extractores: no hay coste que publicar, y eso no es coste cero.**"]
    docs = max(f.n_extracciones for f in filas.values())
    pags = max(f.paginas for f in filas.values())
    lineas = [
        "### Coste · herramientas locales en español",
        "",
        _maquina(sello),
        "",
        f"**n = {docs} documentos y {pags} páginas** — la campaña entera. **No es la n del "
        "TEDS**, que se cuenta sobre el conjunto evaluable de cada extractor y es más "
        "pequeña y distinta para cada uno. Por eso esto es un bloque y no dos columnas.",
        "",
        "| extractor | s/página | s/documento | reloj total | euros |",
        "|---|---:|---:|---:|---:|",
    ]
    for nombre in sorted(filas):
        f = filas[nombre]
        s = f.coste.wall_ms / 1000
        lineas.append(
            f"| `{nombre}` | {s / f.paginas if f.paginas else 0:.3f}".replace(".", ",")
            + f" | {s / f.n_extracciones if f.n_extracciones else 0:.2f}".replace(".", ",")
            + f" | {s / 3600:.3f} h".replace(".", ",")
            + f" | {f.coste.eur:.2f} €".replace(".", ",")
            + " |"
        )
    return [
        *lineas,
        "",
        "**Cero euros es un cero MEDIDO**, no un dato que falte: estos cuatro corren en "
        "local y no gastan. Un `NO_APLICABLE` diría otra cosa.",
        "",
        "**Alfabético, no por coste.** Por lo mismo que arriba: ordenar es ordenar, y el "
        "más barato no es el mejor mientras la calidad viva en otro eje.",
    ]
