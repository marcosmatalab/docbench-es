"""§6 · Todo el modelo de datos. **No importa nada del proyecto.**

`docbench_es.types` es la ÚNICA superficie de import del modelo de datos. Los
submódulos `_*` son privados y ningún módulo de fuera los importa: lo comprueba
`tests/unit/test_types.py`, para que la superficie única sea contrato y no
convención.

Por qué esto es un paquete y no el `types.py` de §8: las ~30 estructuras salen
sobre 340 líneas y `CLAUDE.md` prohíbe pasar de 300. Ver `docs/adr/0013`.

`Cost`, `LicenseDecl`, `PrivacyDecl` y `ProbeResult` **no se redefinen aquí**:
son de `benchcore`, que es el contrato compartido con `gonogo`, y se reexportan
para que quien consume el modelo tenga un solo sitio del que importar.
"""

from benchcore.types import (
    Capabilities,
    Cost,
    LicenseDecl,
    PrivacyDecl,
    ProbeResult,
    ProbeStatus,
    TokenUsage,
)

from docbench_es.types._campana import (
    AnswerMetrics,
    CampaignResult,
    GlossaryContribution,
    GlossaryMetrics,
    RoutingPlan,
    RoutingRule,
    SamplingPlan,
    Stratum,
    StructureMetrics,
    TedsReport,
)
from docbench_es.types._documento import (
    DocRef,
    Extraction,
    ExtractionFailure,
    RawDoc,
)
from docbench_es.types._glosario import ConfusablePair, Glossary, Term
from docbench_es.types._invariantes import (
    FORMATOS_CANONICOS,
    FORMATOS_SIN_SPANS,
    HallazgoTabla,
)
from docbench_es.types._tabla import CanonicalCell, CanonicalTable
from docbench_es.types._verdad import (
    AnswerResult,
    Fact,
    Question,
    Truth,
    TruthMode,
    Verifier,
)

__all__ = [
    "FORMATOS_CANONICOS",
    "FORMATOS_SIN_SPANS",
    "AnswerMetrics",
    "AnswerResult",
    "CampaignResult",
    "CanonicalCell",
    "CanonicalTable",
    "Capabilities",
    "ConfusablePair",
    "Cost",
    "DocRef",
    "Extraction",
    "ExtractionFailure",
    "Fact",
    "Glossary",
    "GlossaryContribution",
    "GlossaryMetrics",
    "HallazgoTabla",
    "LicenseDecl",
    "PrivacyDecl",
    "ProbeResult",
    "ProbeStatus",
    "Question",
    "RawDoc",
    "RoutingPlan",
    "RoutingRule",
    "SamplingPlan",
    "Stratum",
    "StructureMetrics",
    "TedsReport",
    "Term",
    "TokenUsage",
    "Truth",
    "TruthMode",
    "Verifier",
]
