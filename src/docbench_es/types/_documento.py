"""§6.1 y §6.3 · Referencias, documentos y extracciones."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal
from urllib.parse import quote

from benchcore.types import Cost

from docbench_es.types._inmutable import congelar_mapas
from docbench_es.types._tabla import CanonicalTable

# §6.9 · El enum es CERRADO. Vive aquí y no en `errors` porque `Extraction` lo
# necesita y `types` no importa nada del proyecto; `errors` lo reexporta.
# Cerrado significa que ningún fallo puede registrarse como "otro" y
# desaparecer del informe: la tasa de fallo por extractor es un resultado.
ExtractionFailure = Literal[
    "timeout",
    "out_of_memory",
    "unsupported_format",
    "corrupt_pdf",
    "encrypted_pdf",
    "no_text_layer",
    "provider_error",
    "policy_blocked",
]


@dataclass(frozen=True)
class DocRef:
    """La referencia a un documento en el sistema de origen."""

    entity: str
    external_id: str
    published_on: date | None
    url: str | None
    kind: str

    def key(self) -> str:
        """`entity/external_id`, estable entre procesos y entre corridas.

        Es **la unidad de remuestreo del bootstrap**: las preguntas de un mismo
        documento están correlacionadas, así que lo que se remuestrea son
        documentos. Sin una clave estable eso no se puede hacer.

        Los dos campos van percent-encoded con `safe=""`, así que la `/` que
        separa es la única `/` de la clave. Sin escapar, `("boe", "A/B")` y
        `("boe/A", "B")` daban ambos `boe/A/B`: **dos documentos distintos
        colapsados en una sola unidad de remuestreo**, que estrecha el intervalo
        de confianza y publica más precisión de la que hay. `external_id` es
        campo libre de cualquier adaptador, así que no basta con confiar en que
        nadie meta una barra.
        """
        return f"{quote(self.entity, safe='')}/{quote(self.external_id, safe='')}"


@dataclass(frozen=True)
class RawDoc:
    """El documento tal cual llegó de la fuente, sin tocar."""

    ref: DocRef
    primary: bytes
    primary_mime: str
    companions: Mapping[str, bytes]
    sha256: str
    fetched_at: datetime
    n_pages: int | None

    def __post_init__(self) -> None:
        congelar_mapas(self)


@dataclass(frozen=True)
class Extraction:
    """Lo que devuelve un extractor. Nunca lanza: un fallo viaja aquí dentro.

    `failed=True` con su `failure_reason` del enum es la única forma de
    declarar un fallo. Un extractor que lanza se lleva por delante la campaña
    entera y borra del informe su propia tasa de fallo.
    """

    extractor_id: str
    extractor_version: str
    doc_ref: DocRef
    text: str
    tables: tuple[CanonicalTable, ...]
    native_format: str
    pages_processed: int
    cost: Cost
    latency_ms: int
    warnings: tuple[str, ...]
    failed: bool = False
    failure_reason: ExtractionFailure | None = None

    def __post_init__(self) -> None:
        """Ata `failed` a `failure_reason`. Los dos sentidos son un error.

        Sin esto, `Extraction(failed=True, failure_reason=None)` se construía sin
        protestar: un documento caído **sin causa**, que no puede aparecer en la
        tabla de tasa de fallo por causa y desaparece del informe. Es exactamente
        el error tragado que prohíbe la regla de oro 6, sólo que en el modelo de
        datos en vez de en un `except`.

        El sentido contrario —una causa con `failed=False`— también levanta:
        significa que alguien registró un fallo que luego no se cuenta como tal,
        y eso infla a la baja la tasa de fallo del extractor.
        """
        if self.failed and self.failure_reason is None:
            raise ValueError(
                f"{self.extractor_id}: failed=True exige failure_reason del enum cerrado. "
                f"Un fallo sin causa no se puede contar en el informe."
            )
        if not self.failed and self.failure_reason is not None:
            raise ValueError(
                f"{self.extractor_id}: failure_reason={self.failure_reason!r} con failed=False. "
                f"O es un fallo y se cuenta, o no lo es y no lleva causa."
            )
