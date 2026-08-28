"""§12 · El informe de la campaña **como DATO**, no como prosa.

## Por qué existe, y es una razón concreta

`RESULTS.md` publicaba el titular del hito —«103 de 338»— **tecleado a mano**, y las
tablas de nivel 1 igual. Un número tecleado no lo puede comprobar `scripts/derivadas.py`,
que es el guardián que existe precisamente para que un número derivado no se teclee; y su
propio mensaje de error dice, en mayúsculas, **UN NÚMERO DERIVADO NO SE TECLEA**. Con la
prosa como única fuente, el titular más importante del hito era la única cifra del repo
sin nadie detrás.

L4 ya tenía su `runs/l4/informe.json` y por eso su número se podía comprobar. L5 tenía
cuatro artefactos de la campaña —población, cómputo, humo, censo— y **ninguno con el
resultado**.

## Qué NO es este fichero

**No es una medida nueva.** Es exactamente lo que `report.nivel1` y `report.cara_a_cara`
ya calculan, serializado. Si la tabla en Markdown y este JSON discreparan, el bug estaría
en el renderizado — y por eso el JSON se emite en la misma llamada que el Markdown y no
en un comando aparte que alguien tenga que acordarse de correr.

**Y no sustituye al `.md`.** El Markdown es para leer y lleva sus notas; esto es para que
un guardián compare.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.cara_a_cara import CaraACara
    from docbench_es.report.nivel1 import Nivel1

__all__ = ["informe"]


def _de_extractor(nombre: str, fila: Nivel1, cc: CaraACara, version: str) -> dict[str, object]:
    """Una fila, con **cada número al lado del denominador sobre el que se calculó**.

    `puntuan` y `acuerdo_de_recuento` van los dos porque **no son el mismo número** y
    confundirlos publicó el titular de L5 con un 24,3% donde había un 30,5%.
    """
    m, d = fila.metricas, fila.deteccion
    return {
        "version": version,
        "teds": m.teds,
        "teds_s": m.teds_s,
        "cell_f1": m.cell_f1,
        "teds_por_pagina": fila.teds_por_pagina,
        "cobertura_evaluable": m.evaluable_coverage,
        "agregado": m.agregado,
        "regimen": m.regimen,
        "acuerdo_de_recuento": d.con_recuento_igual,
        "acuerdo_de_recuento_tasa": d.acuerdo,
        "puntuan": m.n_documents,
        "no_aplicables_con_recuento_bueno": d.con_recuento_igual - m.n_documents,
        "tablas_de_mas": d.tablas_de_mas,
        "tablas_de_menos": d.tablas_de_menos,
        "fallos": dict(m.failures),
        "n_extracciones": fila.n_extracciones,
        "paginas": fila.paginas,
        "latencia_mediana_ms": fila.latencia_mediana_ms,
        "coste_ms": fila.coste.wall_ms,
        "coste_eur": str(fila.coste.eur),
        "coste_medido": fila.coste.measured,
        "cara_a_cara_teds": cc.teds.get(nombre),
        "cara_a_cara_delta": cc.delta(nombre),
    }


def informe(
    filas: Mapping[str, Nivel1],
    cc: CaraACara,
    versiones: Mapping[str, str],
    sello_corrida: Mapping[str, object],
    sello_informe: Mapping[str, object],
) -> dict[str, object]:
    """El resultado de la campaña, entero y en un `dict` serializable.

    Los **dos sellos** viajan dentro porque una corrida y su informe son dos actos
    separados: sin los dos, el fichero dice qué salió y calla sobre de dónde.
    """
    d = next(iter(filas.values())).deteccion if filas else None
    return {
        "sello_de_la_corrida": dict(sello_corrida),
        "sello_del_informe": dict(sello_informe),
        "poblacion": {
            "documentos_con_tabla": d.documentos if d else 0,
            "tablas_de_la_verdad": d.tablas_de_la_verdad if d else 0,
            "documentos_procesados": max((f.n_extracciones for f in filas.values()), default=0),
            "paginas_procesadas": max((f.paginas for f in filas.values()), default=0),
        },
        "acuerdo": {
            "los_extractores_coinciden_en_el_recuento": cc.n_acuerdo,
            "puntuan_todos": cc.n,
            "no_aplicables": cc.no_aplicables,
            "denominador": cc.poblacion,
            "por_banda": {
                b: {"coinciden": n, "poblacion": t} for b, (n, t) in cc.por_banda.items()
            },
        },
        "extractores": {
            n: _de_extractor(n, f, cc, versiones.get(n, "—")) for n, f in sorted(filas.items())
        },
    }
