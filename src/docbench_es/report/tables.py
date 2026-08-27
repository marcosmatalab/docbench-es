"""§12 · La tabla de nivel 1 en Markdown. **Ninguna columna viaja sin su denominador.**

Lo que esta tabla tiene que impedir, y son tres cosas concretas que ya han pasado en este
repo:

* **que una nota se lea sin su cobertura.** Un TEDS del 0,91 sobre el 40% de las tablas y
  otro del 0,88 sobre el 95% no se ordenan: la cobertura evaluable va en la MISMA fila,
  siempre, y por eso `StructureMetrics` la lleva pegada desde §6;
* **que el recuento de tablas se lea como calidad.** No lo es: uno que parte una tabla en
  tres encuentra más y uno que fusiona dos encuentra menos y puede estar acertando. Aquí
  no hay columna de «tablas encontradas»: hay **acuerdo con la referencia**, que es otra
  cosa y lleva la verdad dentro;
* **que un `NO_APLICABLE` se confunda con un cero.** Se imprime `n/a`, nunca `0,00`.

Y la nota al pie no es decorativa: es donde vive el régimen —censo, sin intervalo— y el
agregado, que desde ADR-0045 viajan dentro de la métrica en vez de en la cabeza de quien
la escribió.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docbench_es.report.coste import tabla_coste
from docbench_es.report.nivel1 import cara_a_cara
from docbench_es.report.procedencia import bloque

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.nivel1 import CaraACara, Nivel1

__all__ = ["tabla_cara_a_cara", "tabla_nivel1"]

CABECERA = (
    "| extractor | versión | TEDS | TEDS-S | F1 celda | TEDS/pág. | cobertura "
    "evaluable | acuerdo de recuento | +/- tablas | fallos | latencia mediana |"
)
SEPARADOR = "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"

CABEZA = [
    "## Nivel 1 · estructura de tablas · L5",
    "",
    "**ESTO NO ES UN RANKING.** No ordena a nadie y no se puede leer como si lo hiciera.",
    "",
    "**Por qué no.** Poner a todos sobre el mismo denominador —que es lo que hace la cara "
    "a cara de abajo— es **necesario y no suficiente**: decir «A es mejor que B» exige la "
    "comparación pareada con su potencia, o sea McNemar y bootstrap agrupado por documento "
    "(ADR-0009), y eso es **L6**. Elegir aquí un umbral sería inventarse una potencia sin "
    "calcularla.",
    "",
    "**Y por eso las filas van en orden alfabético, nunca por nota** —ni ésta ni la cara a "
    "cara—: ordenar por nota *es* ordenar, diga lo que diga el texto de al lado.",
    "",
    "**Lo que esta tabla sí dice**, cada cosa con su denominador en la misma fila: en "
    "cuántos documentos cada extractor coincide con la referencia en **cuántas tablas "
    "hay**, sobre qué proporción de tablas es evaluable, **cuántas veces falla y por qué "
    "causa**, y cuánto tarda. La ordenación llega en L6.",
    "",
    "**Y no es lo que hace el campo.** ExtractBench ordena catorce sistemas y "
    "PulseBench-Tab nueve, los dos **sin un solo intervalo de confianza**; comprobado con "
    "su comando y su cita en "
    "[`docs/quien-publica-los-bancos.md`](docs/quien-publica-los-bancos.md).",
    "",
]


def _num(valor: float | None, decimales: int = 4) -> str:
    """`n/a` para `None`, **nunca `0,00`**. Es la decisión B3 en el renderizado."""
    return "n/a" if valor is None else f"{valor:.{decimales}f}".replace(".", ",")


def _pct(valor: float) -> str:
    return f"{100 * valor:.1f}%".replace(".", ",")


def _fallos(fila: Nivel1) -> str:
    """Las causas con su recuento, o `0`. **Nunca vacío**: un hueco se lee como «no se
    miró», y la tasa de fallo por extractor es un resultado publicado (regla de oro 6)."""
    fallos = fila.metricas.failures
    if not fallos:
        return "0"
    return " ".join(f"{causa}={n}" for causa, n in sorted(fallos.items()))


def tabla_nivel1(
    filas: Mapping[str, Nivel1],
    versiones: Mapping[str, str],
    sello: Mapping[str, object] | None = None,
    arbol_informe: Mapping[str, object] | None = None,
) -> str:
    """La tabla, con su nota al pie. **La nota es parte de la tabla, no un adorno.**

    `versiones` entra aparte porque la versión es del extractor y no de la medida, y
    porque sin ella dos corridas con `flavor` o número de hilos distintos se publicarían
    como la misma fila.
    """
    lineas = [CABECERA, SEPARADOR]
    for nombre in sorted(filas):
        f = filas[nombre]
        m, d = f.metricas, f.deteccion
        lineas.append(
            f"| `{nombre}` | {versiones.get(nombre, '—')} | {_num(m.teds)} | "
            f"{_num(m.teds_s)} | {_num(m.cell_f1)} | {_num(f.teds_por_pagina)} | "
            f"{_pct(m.evaluable_coverage)} | {_pct(d.acuerdo)} | "
            f"+{d.tablas_de_mas}/-{d.tablas_de_menos} | {_fallos(f)} | "
            f"{f.latencia_mediana_ms} ms |"
        )
    return "\n".join(
        [
            *CABEZA,
            *bloque(sello or {}, arbol_informe),
            "",
            *lineas,
            "",
            *tabla_cara_a_cara(cara_a_cara(filas)),
            "",
            *tabla_coste(filas, sello or {}),
            "",
            *_nota(filas),
        ]
    )


def tabla_cara_a_cara(cc: CaraACara) -> list[str]:
    """La segunda cuenta: **las mismas puntuaciones sobre el mismo denominador.**

    Va debajo de la primera y no en un documento aparte porque es la que contesta *«cuál
    es mejor»*, y separarla de la de arriba es exactamente cómo se acaba citando la que no
    toca.
    """
    if cc.n == 0:
        return [
            "### Cara a cara",
            "",
            "**No hay intersección: ningún documento tiene el recuento acertado por "
            "todos.** Eso no es un empate, es que **no se pueden comparar** — y es un "
            "resultado sobre la dificultad del corpus, no un fallo de la tabla.",
        ]
    filas = [f"| `{n}` | {_num(v)} |" for n, v in sorted(cc.teds.items())]
    return [
        "### Cara a cara · el mismo denominador para todos",
        "",
        f"**{cc.n} de {cc.poblacion}** documentos ({_pct(cc.n / cc.poblacion)}): "
        "aquéllos en los que **todos** los extractores acertaron el recuento de tablas.",
        "",
        "**Alfabético, no por nota.** El mismo denominador hace la comparación posible; "
        "no la resuelve.",
        "",
        "| extractor | TEDS sobre la intersección |",
        "|---|---:|",
        *filas,
        "",
        "**Por qué hace falta esta segunda cuenta.** La de arriba tiene un sesgo de "
        "supervivencia declarado (`runs/l5/emparejado.yaml`): un extractor que detecta "
        "mal falla el recuento en más documentos, ésos salen de SU cuenta, y su nota "
        "acaba calculada sobre **sus documentos fáciles**. Cuanto peor detecta, más se "
        "le excluye y mejor pinta lo que queda.",
        "",
        f"**Y este {cc.n} es un dato en sí**: dice en cuántos documentos los "
        f"{len(cc.extractores)} extractores coinciden con la referencia en algo tan "
        "básico como CUÁNTAS tablas hay.",
        "",
        "**Esto no es un ranking.** Mismo denominador es necesario y no suficiente: "
        "decir «A es mejor que B» exige la comparación pareada con su potencia, que es "
        "lo que hace L6 (ADR-0009). Aquí van los números y su n; no se ordena a nadie.",
    ]


def _nota(filas: Mapping[str, Nivel1]) -> list[str]:
    """Lo que hay que leer para que ninguna columna signifique de más."""
    if not filas:
        return ["**Sin extractores: la tabla está vacía y eso no es un resultado.**"]
    una = next(iter(filas.values()))
    m, d = una.metricas, una.deteccion
    return [
        f"**Agregado:** {m.agregado} —media por documento, sin ponderar—, que es el "
        "primario de `runs/l5/ponderacion.yaml`. `TEDS/pág.` es el secundario, "
        "ponderado por páginas: **los mismos TEDS con otros pesos**.",
        "",
        f"**Régimen:** {m.regimen}. Los documentos con tabla son la población entera, no "
        "una muestra, así que **no llevan intervalo** (ADR-0015). Un IC degenerado sobre "
        "un censo mentiría sobre la naturaleza del número.",
        "",
        f"**Denominadores.** La población con tabla son **{d.documentos}** documentos y "
        f"**{d.tablas_de_la_verdad}** tablas de referencia. `cobertura evaluable` es "
        "sobre tablas; `acuerdo de recuento` es sobre documentos, y es **el denominador "
        "del TEDS**: sólo puntúan los documentos donde el extractor devuelve tantas "
        "tablas como la verdad (`runs/l5/emparejado.yaml`).",
        "",
        "**`+/- tablas` NO es una columna de calidad.** Cuenta el desacuerdo con la "
        "referencia, no la habilidad: uno que parte una tabla en tres encuentra más y "
        "uno que fusiona dos encuentra menos **y puede estar acertando**. Quien ordena "
        "es el TEDS contra la verdad, no el recuento.",
        "",
        "**`n/a` no es cero.** Un `NO_APLICABLE` dice que no se pudo medir; un 0,00 diría "
        "que se midió y salió cero (decisión B3).",
    ]
