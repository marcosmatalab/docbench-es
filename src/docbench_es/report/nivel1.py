"""§12 · El nivel 1: de las extracciones y la verdad a `StructureMetrics`.

**El emparejado está pre-registrado y no se decide aquí**: `runs/l5/emparejado.yaml`, con
sus alternativas descartadas. En una línea: **por orden, y sólo cuando los recuentos
coinciden**; si el extractor devuelve N tablas y la verdad tiene M con N≠M, el documento
sale `NO_APLICABLE` —nunca 0,00— y su discrepancia se cuenta aparte.

Por página no se puede emparejar: la verdad de L5 es `DERIVED` y **el XML no tiene
páginas** (LIMITS 32), así que el `page_span` del lado de la verdad es relleno.

## Los dos agregados, y por qué salen los dos

`runs/l5/ponderacion.yaml`, congelado antes de medir:

* **primario, media por documento** — el documento es la unidad de muestreo **y la de
  remuestreo** (regla de oro 3), así que es el único estimador cuyo intervalo hablaría de
  la misma población que su punto;
* **secundario, ponderado por páginas** — contesta la pregunta de quien procesa un
  boletín entero, y **no cuesta una segunda medida**: son los mismos TEDS con otros pesos.

## La cobertura NO es la de `teds_batch`, y la diferencia importa

`core.teds.teds_batch` calcula su cobertura sobre **los pares que le llegan**, y aquí los
documentos con recuento distinto **no llegan**. Tomar la suya diría que la cobertura es
alta porque lo que no cuadra se quedó fuera de la cuenta — el 2.283 otra vez. La de aquí
se cuenta sobre **todas las tablas de la verdad** de los documentos considerados.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import TYPE_CHECKING

from benchcore.types import Cost

from docbench_es.core.cellmatch import cell_f1
from docbench_es.core.teds import teds_batch
from docbench_es.types import StructureMetrics

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Iterable, Mapping, Sequence

    from docbench_es.types import CanonicalTable, Extraction, ExtractionFailure

__all__ = ["Deteccion", "Nivel1", "medir"]


@dataclass(frozen=True)
class Deteccion:
    """El acuerdo con la referencia en CUÁNTAS tablas hay. **No es calidad.**

    Un extractor que parte una tabla en tres «encuentra» más; uno que fusiona dos
    encuentra menos y puede estar acertando. Un recuento suelto se lee como calidad sin
    serlo —la misma clase que un 0,00 de anclaje—; **con la verdad al lado deja de ser un
    recuento y pasa a ser un acuerdo**, que sí significa algo.
    """

    documentos: int
    """La población considerada: los que tienen alguna tabla en la verdad."""
    con_recuento_igual: int
    """Los que puntúan. **Es el denominador de `teds`.**"""
    tablas_de_mas: int
    tablas_de_menos: int
    tablas_de_la_verdad: int

    @property
    def acuerdo(self) -> float:
        return self.con_recuento_igual / self.documentos if self.documentos else 0.0


@dataclass(frozen=True)
class Nivel1:
    """Lo que va en una fila de la tabla, con lo que la hace leíble al lado."""

    metricas: StructureMetrics
    deteccion: Deteccion
    teds_por_pagina: float | None
    """El agregado SECUNDARIO de `ponderacion.yaml`. Los mismos TEDS con otros pesos."""
    coste: Cost
    latencia_mediana_ms: int
    n_extracciones: int
    paginas: int
    """Las páginas de los documentos que este extractor PROCESÓ, de la fuente y no de lo
    que devolvió: un documento que falla no devuelve páginas y **sí cuesta tiempo**.

    Es el denominador del coste, y **no es el del TEDS**: por eso el coste va en su propio
    bloque y no en una columna más. Misma fila implica mismo denominador."""
    por_documento: Mapping[str, float]
    """La nota de cada documento que PUNTUÓ. Es lo que hace posible la cara a cara, y
    viaja aquí porque recalcularla exigiría rehacer el emparejado."""
    poblacion_documentos: tuple[str, ...]
    """Los documentos CON tabla en la verdad, por nombre. Es el denominador del acuerdo, y
    viaja entero —no sólo su recuento— porque el acuerdo POR BANDA no se puede reconstruir
    desde un número."""


def _por_documento(
    extracciones: Iterable[Extraction],
) -> dict[str, list[Extraction]]:
    fuera: dict[str, list[Extraction]] = {}
    for ex in extracciones:
        fuera.setdefault(ex.doc_ref.external_id, []).append(ex)
    return fuera


def _emparejar(
    pred: Sequence[CanonicalTable], gold: Sequence[CanonicalTable]
) -> list[tuple[CanonicalTable, CanonicalTable]] | None:
    """La regla PRE-REGISTRADA de `runs/l5/emparejado.yaml`, en una función y con nombre.

    **Por orden, y sólo cuando los recuentos coinciden.** `None` significa «este documento
    no puntúa» —`NO_APLICABLE`, nunca 0,00— y no es lo mismo que una lista vacía.

    Está separada de `medir` porque es **la decisión que mueve el titular**, no un detalle
    de implementación: con la misma verdad y el mismo extractor, otra regla da otro TEDS.
    Una decisión así tiene que poder romperse a propósito y verse el rojo, y para eso hace
    falta que sea una unidad con nombre — el mutante `emparejado_sin_recuento` la sustituye
    por el emparejado por orden a secas, que es la alternativa que `emparejado.yaml`
    descarta por catastrófica: un extractor que se salta la primera tabla compara su 2 con
    la 1 de la verdad y saca notas ruinosas en todas por un solo fallo de detección.
    """
    if len(pred) != len(gold):
        return None
    return list(zip(pred, gold, strict=True))


def _f1_del_documento(pares: Sequence[tuple[CanonicalTable, CanonicalTable]]) -> float | None:
    """Media de los F1 de las tablas del documento. `None` si ninguna es evaluable.

    Mismo agregado que TEDS —por documento y luego por documentos— para que las dos
    columnas de la tabla hablen de la misma población.
    """
    notas = [f for p, g in pares if (f := cell_f1(p, g)) is not None]
    return sum(notas) / len(notas) if notas else None


def medir(
    extracciones: Iterable[Extraction],
    verdades: Mapping[str, Sequence[CanonicalTable]],
    paginas: Mapping[str, int],
) -> Nivel1:
    """Una fila de la tabla de nivel 1, para UN extractor.

    `verdades` trae sólo los documentos **con** tablas: los 662 sin ninguna no puntúan
    —salen `NO_APLICABLE`, nunca 0,00— y su tasa de falso positivo es otra medida, con
    otro denominador y otro régimen (ADR-0045).
    """
    por_doc = _por_documento(extracciones)
    tripletas: list[tuple[str, CanonicalTable, CanonicalTable]] = []
    pares_f1: dict[str, list[tuple[CanonicalTable, CanonicalTable]]] = {}
    de_mas = de_menos = igual = tablas_verdad = 0
    fallos: dict[ExtractionFailure, int] = {}
    costes: list[Cost] = []
    latencias: list[int] = []

    for ex in (e for lista in por_doc.values() for e in lista):
        costes.append(ex.cost)
        latencias.append(ex.latency_ms)
        if ex.failed and ex.failure_reason is not None:
            fallos[ex.failure_reason] = fallos.get(ex.failure_reason, 0) + 1

    for clave, gold in verdades.items():
        if not gold:
            continue
        tablas_verdad += len(gold)
        pred = tuple(t for ex in por_doc.get(clave, ()) for t in ex.tables)
        pares = _emparejar(pred, gold)
        if pares is not None:
            igual += 1
            tripletas += [(clave, p, g) for p, g in pares]
            pares_f1[clave] = pares
        else:
            de_mas += max(0, len(pred) - len(gold))
            de_menos += max(0, len(gold) - len(pred))

    informe = teds_batch(tripletas)
    estructura = teds_batch(tripletas, solo_estructura=True)
    f1_por_doc = [f for pares in pares_f1.values() if (f := _f1_del_documento(pares)) is not None]
    evaluables = informe.evaluable_coverage * len(tripletas)
    con_tabla = sum(1 for g in verdades.values() if g)

    return Nivel1(
        metricas=StructureMetrics(
            teds=informe.aggregate,
            teds_s=estructura.aggregate,
            cell_f1=sum(f1_por_doc) / len(f1_por_doc) if f1_por_doc else None,
            evaluable_coverage=evaluables / tablas_verdad if tablas_verdad else 0.0,
            failures=fallos,
            n_documents=sum(1 for v in informe.per_document.values() if v is not None),
            agregado="POR_DOCUMENTO",
            regimen="CENSO",
        ),
        deteccion=Deteccion(
            documentos=con_tabla,
            con_recuento_igual=igual,
            tablas_de_mas=de_mas,
            tablas_de_menos=de_menos,
            tablas_de_la_verdad=tablas_verdad,
        ),
        teds_por_pagina=_ponderado_por_pagina(informe.per_document, paginas),
        coste=sum(costes[1:], costes[0]) if costes else Cost.zero(),
        latencia_mediana_ms=int(median(latencias)) if latencias else 0,
        n_extracciones=len(latencias),
        paginas=sum(paginas.get(clave, 0) for clave in por_doc),
        por_documento={c: v for c, v in informe.per_document.items() if v is not None},
        poblacion_documentos=tuple(sorted(c for c, g in verdades.items() if g)),
    )


def _ponderado_por_pagina(
    por_documento: Mapping[str, float | None], paginas: Mapping[str, int]
) -> float | None:
    """El agregado secundario. **Un documento sin páginas conocidas no se cuela con peso 0.**

    Se salta, y al saltarse sale del numerador **y** del denominador — que es la
    diferencia entre no medirlo y medirlo como si valiera cero.
    """
    pesos = [(paginas[c], v) for c, v in por_documento.items() if v is not None and c in paginas]
    total = sum(p for p, _ in pesos)
    return sum(p * v for p, v in pesos) / total if total else None
