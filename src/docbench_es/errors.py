"""§6.9 · La jerarquía de errores, y §11 · sus códigos de salida.

Dos reglas gobiernan este fichero.

**Ningún error se traga.** Un documento que falla se registra con su causa del
enum cerrado `ExtractionFailure` —que vive en `docbench_es.types`, porque lo
necesita `Extraction` y `types` no importa nada del proyecto— y **se cuenta en
el informe**. La tasa de fallo por extractor es un resultado, no un detalle de
implementación.

**El código de salida es código, no una tabla en un manual.** Cada error lleva
el suyo de §11 como atributo de clase. Separar el 2 (política) y el 4
(infraestructura) del 1 (fallos por encima del umbral) es lo que evita que un
equipo aprenda a ignorar el rojo: no es lo mismo "la medición salió peor de lo
tolerado" que "la campaña no llegó a arrancar porque la licencia lo prohíbe".

Las tres cuyo significado coincide con el del contrato heredan **también** de
la de `benchcore`. Así un `except BenchcoreError` en el motor caza lo que lance
el plugin de un cliente, y un `except DocbenchError` caza todo lo del proyecto.
"""

from typing import ClassVar

from benchcore.errors import (
    BudgetExceeded as _BenchcoreBudgetExceeded,
)
from benchcore.errors import (
    ContractViolation as _BenchcoreContractViolation,
)
from benchcore.errors import (
    PolicyViolation as _BenchcorePolicyViolation,
)

__all__ = [
    "AdapterError",
    "BudgetExceeded",
    "ContractViolation",
    "DocbenchError",
    "PolicyViolation",
    "TruthUnavailable",
]


class DocbenchError(Exception):
    """Raíz de todo lo que lanza este proyecto.

    Su código es el 1, el genérico: la medición terminó pero hay fallos por
    encima del umbral declarado. Las subclases lo estrechan.
    """

    exit_code: ClassVar[int] = 1


class AdapterError(DocbenchError):
    """El adaptador falló: no alcanzo la fuente, el proveedor cayó.

    Código 4, infraestructura. Deliberadamente distinto del 1: que no se pueda
    llegar al corpus no es un resultado de medición, y contarlo como tal
    convertiría una caída de red en una nota mala del extractor.
    """

    exit_code: ClassVar[int] = 4


class PolicyViolation(DocbenchError, _BenchcorePolicyViolation):
    """Licencia o privacidad. **La campaña no arrancó.** Código 2.

    No es un aviso. Si un adaptador declara `may_send_to_third_party=False`, el
    motor rechaza los extractores por API y esto es lo que lanza (ADR-0003).
    """

    exit_code: ClassVar[int] = 2


class BudgetExceeded(DocbenchError, _BenchcoreBudgetExceeded):
    """El presupuesto duro se agotó y se abortó **antes de gastar**. Código 3."""

    exit_code: ClassVar[int] = 3


class ContractViolation(DocbenchError, _BenchcoreContractViolation):
    """Un plugin no cumple el Protocol que dice cumplir. Código 5.

    Se lanza en carga, nunca a mitad de campaña: un plugin roto tiene que parar
    la ejecución antes de gastar un euro, no después.
    """

    exit_code: ClassVar[int] = 5


class TruthUnavailable(DocbenchError):
    """Se pidió exactitud en una entidad con `truth_mode: NONE`. Código 6.

    El motor **se niega**. No devuelve un número inventado, no devuelve cero y
    no degrada a un aviso. Sin verdad de referencia no hay exactitud que
    publicar, y publicarla igualmente es la peor cosa que este repo puede hacer.
    """

    exit_code: ClassVar[int] = 6
