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


@dataclass(frozen=True)
class StructureMetrics:
    """Nivel 1, por extractor.

    `teds=None` es NO_APLICABLE, **nunca cero** (ADR-0006), y por eso viaja
    pegado a `evaluable_coverage`: una nota calculada sobre un subconjunto
    distinto no se compara con otra sin decirlo.
    """

    teds: float | None
    teds_s: float | None
    cell_f1: float
    evaluable_coverage: float
    failures: Mapping[ExtractionFailure, int]
    ci: tuple[float, float]
    n_documents: int

    def __post_init__(self) -> None:
        congelar_mapas(self)


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
