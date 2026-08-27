"""§6.8 · Plan, campaña, agregados por nivel y objetos de salida."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from benchcore.types import Cost

from docbench_es.types._documento import DocRef, ExtractionFailure
from docbench_es.types._inmutable import congelar_mapas


@dataclass(frozen=True)
class Stratum:
    """Un estrato del muestreo. `weight` es su proporción REAL en el corpus.

    Es lo que permite publicar las dos cifras: la del estrato sobremuestreado
    y la ponderada a la distribución real. Publicar solo una de las dos es
    elegir la que más conviene.
    """

    name: str
    target: int
    found: int
    weight: float


@dataclass(frozen=True)
class SamplingPlan:
    """El plan de muestreo, CONGELADO antes de medir (ADR-0009).

    `doc_refs` no es opcional: son los documentos concretos ya sorteados, y es
    lo único que hace que "congelado" signifique algo. Sin ellos, el plan es
    una intención y el estrato se puede reelegir después de ver los números.
    """

    version: int
    entity: str
    campaign: str
    strata: tuple[Stratum, ...]
    seed: int
    design: Literal["mcnemar_paired", "independent"]
    effect_to_detect: float
    assumed_discordance: float
    alpha: float
    target_power: float
    n_documents_required: int
    frozen_at: datetime
    doc_refs: tuple[DocRef, ...]


Regimen = Literal["CENSO", "MUESTRA"]
"""Sobre qué se calculó una métrica, y por tanto **si lleva intervalo o no**.

`CENSO` es la población entera: no es una estimación y no lleva intervalo (ADR-0015).
`MUESTRA` es una parte declarada: lleva el suyo, o no se publica.

Va como campo y no como comentario porque **un intervalo ausente y uno olvidado se leen
igual**. Ver ADR-0045.
"""

Agregado = Literal["POR_DOCUMENTO", "PONDERADO_POR_PAGINA", "POR_TABLA"]
"""Cómo se promedió. Los tres dan números distintos y los tres son legítimos.

Los 38 documentos de más de 50 páginas son el **3,8% de los documentos** y el **36,6% de
las páginas**, así que la elección no es un detalle: mueve el titular. La decisión y su
porqué están congelados en `runs/l5/ponderacion.yaml`, escritos antes de medir.
"""


@dataclass(frozen=True)
class StructureMetrics:
    """Nivel 1, por extractor. **Lleva dentro su régimen y su agregado** (ADR-0045).

    `teds=None` es NO_APLICABLE, **nunca cero** (ADR-0006), y por eso viaja
    pegado a `evaluable_coverage`: una nota calculada sobre un subconjunto
    distinto no se compara con otra sin decirlo.

    **Y por lo mismo lleva `agregado` y `regimen`.** Los encontró el PASO 0 de su
    primer productor —este tipo se declaró en L0 y nadie lo había rellenado nunca,
    que es la cuarta confirmación del patrón de `ESTADO.md`—:

    * `runs/l5/ponderacion.yaml` decidió que hay **tres** agregados y que dan **tres
      números distintos**. Un `teds=0,87` sin decir cuál es un número cuyo
      denominador no viaja en el artefacto;
    * `ci` era obligatorio, y la población de estructura de L5 es un **censo** —los
      338 con tabla—, que por ADR-0015 **no lleva intervalo**. El tipo obligaba a
      inventar un `(x, x)` o a quitarlo de donde sí hace falta.

    `n_documents` es **sobre cuántos**: 338, no 616 ni 1.000. Sale del censo.
    """

    teds: float | None
    teds_s: float | None
    # `core.cellmatch.cell_f1` devuelve `float | None`: `None` cuando la verdad no
    # trae celdas (NO_APLICABLE, regla de oro 4). Declararlo `float` a secas
    # obligaba a quien lo rellenara a meter un 0,0, que es justo lo que ADR-0006
    # prohíbe: cero dice «lo intentó y falló», no «no había nada que medir».
    cell_f1: float | None
    evaluable_coverage: float
    failures: Mapping[ExtractionFailure, int]
    n_documents: int
    agregado: Agregado
    regimen: Regimen
    # EL INTERVALO ES EL DE `teds`, que es el agregado primario. Los demás campos no
    # llevan intervalo hasta que alguien los necesite y lo declare: un `ci` para
    # cuatro números es un intervalo sin dueño, y eso no es mejor que ninguno.
    ci: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        """Ata el régimen al intervalo **en las dos direcciones**. ADR-0045.

        Es el mismo mecanismo que `Extraction` usa con `failed` y `failure_reason`:
        el objeto incoherente **no se construye**, así que no hay que acordarse de
        comprobarlo después.

        La dirección que no es obvia es la segunda. Sin ella, `ci=None` sería
        ambiguo —«no llevaba intervalo» y «se me olvidó» se leen igual—, y el campo
        `regimen` dejaría de significar nada.
        """
        congelar_mapas(self)
        if self.regimen == "MUESTRA" and self.ci is None:
            raise ValueError(
                "regimen='MUESTRA' exige `ci`: una estimación sin intervalo no se "
                "publica (ADR-0015, regla de oro 2)"
            )
        if self.regimen == "CENSO" and self.ci is not None:
            raise ValueError(
                f"regimen='CENSO' con ci={self.ci}: un censo no es una estimación y no "
                "lleva intervalo (ADR-0015). Un IC degenerado miente sobre la naturaleza "
                "del número"
            )
        if self.ci is not None and self.ci[0] > self.ci[1]:
            raise ValueError(f"ci={self.ci} está del revés: es (bajo, alto)")
        if self.n_documents < 0:
            raise ValueError(f"n_documents={self.n_documents}: no hay poblaciones negativas")
        if self.teds is not None and self.n_documents == 0:
            raise ValueError(
                f"teds={self.teds} sobre 0 documentos. Una nota sin población no es una "
                "nota: si no se pudo medir, `teds` es None (NO_APLICABLE)"
            )


@dataclass(frozen=True)
class AnswerMetrics:
    """Nivel 2, por extractor. `n_documents` es la unidad de remuestreo."""

    accuracy: float
    accuracy_vs_oracle: float | None
    by_verifier: Mapping[str, float]
    ci: tuple[float, float]
    n_questions: int
    n_documents: int

    def __post_init__(self) -> None:
        congelar_mapas(self)


@dataclass(frozen=True)
class GlossaryMetrics:
    """Nivel 3, por extractor: cuánto aporta cargar la capa semántica."""

    accuracy_with: float
    accuracy_without: float
    delta: float
    ci_delta: tuple[float, float]
    confusion_rate: Mapping[str, float]

    def __post_init__(self) -> None:
        congelar_mapas(self)


@dataclass(frozen=True)
class CampaignResult:
    """El resultado completo de una campaña.

    `plan_hash` la ata a su plan congelado y `substance_hash` a lo que se midió
    de verdad, para que dos corridas con la misma semilla se puedan comparar
    bit a bit.
    """

    campaign: str
    entity: str
    plan_hash: str
    extractors: tuple[str, ...]
    level1: Mapping[str, StructureMetrics]
    level2: Mapping[str, AnswerMetrics] | None
    level3: Mapping[str, GlossaryMetrics] | None
    costs: Mapping[str, Cost]
    started_at: datetime
    finished_at: datetime
    substance_hash: str

    def __post_init__(self) -> None:
        congelar_mapas(self)


@dataclass(frozen=True)
class TedsReport:
    """Salida de `core.teds.teds_batch`. Los NO_APLICABLE van nombrados."""

    per_document: Mapping[str, float | None]
    aggregate: float | None
    evaluable_coverage: float
    not_applicable: tuple[str, ...]

    def __post_init__(self) -> None:
        congelar_mapas(self)


@dataclass(frozen=True)
class GlossaryContribution:
    """Salida de `glossary.contribution`, siempre con su intervalo."""

    delta: float
    ci: tuple[float, float]
    n_documents: int
    by_stratum: Mapping[str, float]

    def __post_init__(self) -> None:
        congelar_mapas(self)


@dataclass(frozen=True)
class RoutingRule:
    """Una regla de enrutado, con su medición dentro.

    `measured` es OBLIGATORIO: sin él, `docbench route --validate` rechaza la
    regla. Es lo que impide que una heurística escondida se disfrace de
    recomendación medida (ADR-0012).
    """

    when: Mapping[str, object]
    extractor: str
    measured: Mapping[str, object]
    fallback: str | None = None
    execution: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        congelar_mapas(self)


@dataclass(frozen=True)
class RoutingPlan:
    """Salida de `route.recommend`. Se serializa a `routing.yaml` ejecutable."""

    rules: tuple[RoutingRule, ...]
    default: RoutingRule
    summary: Mapping[str, float]
    generated_from: str
    substance_hash: str

    def __post_init__(self) -> None:
        congelar_mapas(self)
