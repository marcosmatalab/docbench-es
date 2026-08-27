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

__all__ = ["CaraACara", "Deteccion", "Nivel1", "cara_a_cara", "medir"]


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


def _por_documento(
    extracciones: Iterable[Extraction],
) -> dict[str, list[Extraction]]:
    fuera: dict[str, list[Extraction]] = {}
    for ex in extracciones:
        fuera.setdefault(ex.doc_ref.external_id, []).append(ex)
    return fuera


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
        if len(pred) == len(gold):
            igual += 1
            tripletas += [(clave, p, g) for p, g in zip(pred, gold, strict=True)]
            pares_f1[clave] = list(zip(pred, gold, strict=True))
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
    )


@dataclass(frozen=True)
class CaraACara:
    """El mismo denominador para todos. **La única cuenta que contesta «cuál es mejor».**

    La regla de emparejado tiene un sesgo de supervivencia declarado en
    `runs/l5/emparejado.yaml`: un extractor que detecta mal las tablas falla el recuento en
    más documentos, ésos salen de SU cuenta, y **su TEDS acaba calculándose sobre sus
    documentos fáciles**. Cuanto peor detecta, más se le excluye y mejor pinta lo que
    queda.

    Que `evaluable_coverage` viaje pegado a la nota hace el sesgo **legible**, no lo quita.
    Esto lo quita para la comparación: se puntúa a todos sobre **la intersección**, los
    documentos donde **todos** acertaron el recuento.

    **`n` es un dato en sí.** Si de 338 los cuatro coinciden en el recuento en 150, eso
    dice algo sobre la dificultad del corpus que ninguna nota de TEDS dice — y se publica
    también, y sobre todo, si sale baja.

    **Lo que esto NO afirma: un ranking.** Mismo denominador es necesario y no suficiente;
    decir «A es mejor que B» exige la comparación pareada con su potencia, que es lo que
    L6 existe para hacer (ADR-0009).
    """

    extractores: tuple[str, ...]
    documentos: tuple[str, ...]
    teds: Mapping[str, float]
    poblacion: int
    """Los documentos con tabla en la verdad. El denominador de `n`."""

    @property
    def n(self) -> int:
        return len(self.documentos)

    def __str__(self) -> str:
        """**Sin intersección no hay empate: no hay comparación**, y se dice así.

        Un «0,0% sobre 338» se leería como un resultado malo; lo que pasa es que no hay
        ningún documento donde todos acertaran el recuento, o sea que no se les puede
        poner sobre el mismo denominador. Es la misma distinción que `NO_APLICABLE`
        contra `0,00`, un nivel más arriba.
        """
        if self.n == 0:
            return f"cara a cara: NO HAY COMPARACIÓN · 0 de {self.poblacion} documentos"
        return (
            f"cara a cara sobre {self.n} de {self.poblacion} documentos "
            f"({100 * self.n / self.poblacion:.1f}%) · {len(self.extractores)} extractores"
        )


def cara_a_cara(filas: Mapping[str, Nivel1]) -> CaraACara:
    """Las mismas puntuaciones sobre la INTERSECCIÓN. **No es una segunda medida.**

    Con un solo extractor la intersección es su propio conjunto y la cara a cara no aporta
    nada; se calcula igual, y su `n` lo dice.
    """
    if not filas:
        return CaraACara(extractores=(), documentos=(), teds={}, poblacion=0)
    comunes = set.intersection(*(set(f.por_documento) for f in filas.values()))
    documentos = tuple(sorted(comunes))
    return CaraACara(
        extractores=tuple(sorted(filas)),
        documentos=documentos,
        teds={
            nombre: sum(f.por_documento[d] for d in documentos) / len(documentos)
            for nombre, f in sorted(filas.items())
            if documentos
        },
        poblacion=max(f.deteccion.documentos for f in filas.values()),
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
