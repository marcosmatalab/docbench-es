"""§6.6 · Glosario y capa semántica.

El glosario es **del adaptador de entidad, no del motor** (ADR-0008). El motor
no sabe qué es un "complemento de destino": lo sabe el adaptador del BOE.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from docbench_es.types._documento import DocRef


@dataclass(frozen=True)
class Term:
    """Un término del vocabulario de la entidad.

    `definition` es **operativa, no de diccionario**: dice cómo se reconoce en
    un documento, no qué significa en abstracto. Y `discriminator` dice qué
    evidencia del documento lo separa de aquello con lo que se confunde.
    """

    key: str
    definition: str
    aliases: tuple[str, ...]
    not_to_confuse_with: tuple[str, ...]
    discriminator: str
    appears_in: tuple[str, ...]
    verified_on: date
    verified_by: Literal["human", "imported"]


@dataclass(frozen=True)
class ConfusablePair:
    """Dos términos que se confunden, y la evidencia que los separa.

    De aquí salen las preguntas trampa, que se escriben a mano y se cuentan
    aparte de las de plantilla.
    """

    id: str
    term_a: str
    term_b: str
    why_confused: str
    discriminator: str
    example_doc: DocRef | None
    trap_questions: tuple[str, ...]


@dataclass(frozen=True)
class Glossary:
    """El vocabulario de una entidad, versionado."""

    entity: str
    version: int
    updated: date
    terms: tuple[Term, ...]
    confusables: tuple[ConfusablePair, ...]

    def to_prompt_block(self) -> str:
        """Cómo se inyecta el glosario en el sistema de respuesta.

        Lo implementa **L11**, que es el hito que mide cuántos puntos aporta
        cargarlo. En L0 levanta `NotImplementedError`: devolver `""` mediría
        una capa semántica vacía y publicaría una ganancia de cero puntos que
        no es un resultado, es un bug.
        """
        raise NotImplementedError("glossary.model, hito L11")
