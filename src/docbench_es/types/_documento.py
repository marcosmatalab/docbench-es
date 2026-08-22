"""§6.1 y §6.3 · Referencias, documentos y extracciones."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

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


def _escapar(campo: str) -> str:
    """Escapa `%` y `/` para que la clave de `DocRef` sea inyectiva.

    Escrito a mano y no con `urllib.parse.quote` **por el contrato de capas**:
    `.importlinter` prohíbe que `core` importe `urllib`, y `core` importa
    `types`, así que un `urllib` aquí rompe la promesa «el núcleo es puro» por
    una cadena indirecta —aunque `urllib.parse` no toque la red—. La regla del
    repo es que el contrato no se toca para que quepa el código; se toca el
    código. Descubierto en L1, al ser `core.canonical` el primer módulo de `core`
    que importa el modelo de datos.

    Inyectiva porque `%` se escapa ANTES que `/`: la vuelta es inequívoca. Los
    identificadores reales del BOE —`BOE-A-2026-1234`— no llevan ninguno de los
    dos, así que la clave sigue siendo legible.
    """
    return campo.replace("%", "%25").replace("/", "%2F")


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

        Los dos campos van escapados, así que la `/` que separa es la única `/`
        de la clave. Sin escapar, `("boe", "A/B")` y `("boe/A", "B")` daban ambos
        `boe/A/B`: **dos documentos distintos colapsados en una sola unidad de
        remuestreo**, que estrecha el intervalo de confianza y publica más
        precisión de la que hay. `external_id` es campo libre de cualquier
        adaptador, así que no basta con confiar en que nadie meta una barra.
        """
        return f"{_escapar(self.entity)}/{_escapar(self.external_id)}"


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
