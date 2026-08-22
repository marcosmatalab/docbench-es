"""§6.4 y §6.5 · Verdad de referencia, preguntas y respuestas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from benchcore.types import Cost

from docbench_es.types._documento import DocRef
from docbench_es.types._tabla import CanonicalTable

# ADR-0002 · Cuatro modos, declarados por el adaptador de entidad.
# En modo NONE el motor se NIEGA a publicar exactitud: código de salida 6.
TruthMode = Literal["DERIVED", "ANNOTATED", "CONSENSUS", "NONE"]

# Los seis verificadores. Cada uno tiene que discriminar entre una respuesta
# correcta y una incorrecta, o el denominador del nivel 2 queda envenenado.
Verifier = Literal["exact", "numeric", "set", "date", "boolean", "span"]


@dataclass(frozen=True)
class Fact:
    """Un dato concreto extraído de la verdad, con su procedencia exacta."""

    id: str
    doc_ref: DocRef
    path: str
    value: str | float | date
    unit: str | None
    provenance: str


@dataclass(frozen=True)
class Truth:
    """La verdad de referencia de un documento, con su modo siempre delante.

    `confidence` y `n_annotators` solo tienen sentido en ANNOTATED y CONSENSUS,
    y `discordance_rate` solo en CONSENSUS. Van como `None` en los demás modos
    en vez de como cero: un cero se agregaría y mentiría.
    """

    mode: TruthMode
    doc_ref: DocRef
    tables: tuple[CanonicalTable, ...]
    facts: tuple[Fact, ...]
    confidence: float | None
    n_annotators: int | None
    discordance_rate: float | None
    built_at: datetime


@dataclass(frozen=True)
class Question:
    """Una pregunta con su respuesta conocida y el verificador que la juzga.

    `tolerance` es obligatorio si `verifier == "numeric"`: comparar dos
    importes por igualdad exacta convierte un acierto en un fallo por un
    céntimo de redondeo. Lo comprueba `ask validate`, en L9.
    """

    id: str
    entity: str
    doc_ref: DocRef
    text: str
    answer: str | float | date | frozenset[str] | bool
    verifier: Verifier
    tolerance: float | None
    origin: Literal["template", "handwritten"]
    template_id: str | None
    trap: str | None
    difficulty: frozenset[str]
    requires_table: bool


@dataclass(frozen=True)
class AnswerResult:
    """El resultado de una pregunta para un extractor.

    `confidently_wrong` está separado de `correct` porque no cuestan lo mismo:
    una respuesta mal dada sin señalar duda es la que llega a un comité y se
    firma. Es el número que un cliente quiere ver aparte.
    """

    question_id: str
    extractor_id: str
    given: str
    correct: bool
    confidently_wrong: bool
    confused_with: str | None
    cost: Cost
    latency_ms: int
