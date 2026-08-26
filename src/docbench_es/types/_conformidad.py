"""§6.10 · El vocabulario de una suite de conformidad: un hallazgo y su severidad.

Lo comparten `entity.conformance` y `extract.conformance`, y vive aquí —y no en
cualquiera de las dos— porque un tipo que usan dos módulos hermanos no pertenece a
ninguno. Decidido en **ADR-0044**.

## Tres severidades, y la tercera es la razón de que este tipo exista

`benchcore.conform.Finding` tiene la misma forma exacta —`check`, `severity`, `detail`—
y su `Severity` es `Literal["FALLA", "AVISO"]`. Le basta, porque `benchcore.conform`
mira **la forma** del contrato: o el miembro está o no está.

Las suites de este repo **ejecutan** el sujeto contra documentos, y ahí aparece un
tercer resultado que allí no existe: **`NO_EJECUTADA`**. Si `discover` no trae ni un
documento, la idempotencia de `fetch` no falla — es que no se ha comprobado. Si el
conjunto de conformidad no trae ni una celda combinada, no se puede distinguir un
extractor que las aplana de uno al que no le tocó ninguna.

Contar cualquiera de las dos como aprobada sería **publicar como observado algo que no
se observó**. Por eso `NO_EJECUTADA` no es un aviso: pesa como un fallo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = ["Hallazgo", "Severidad"]

Severidad = Literal["FALLA", "AVISO", "NO_EJECUTADA"]
"""Las dos de `benchcore.conform.Severity` más la que sale de ejecutar.

**`NO_EJECUTADA` pesa como `FALLA` y no como `AVISO`**, y es la decisión entera: un aro
por el que no se ha pasado no está superado. Quien quiera aprobar sin ejecutar tiene que
decirlo en voz alta cambiando esta regla, no dejando un aviso que nadie lee.
"""


@dataclass(frozen=True)
class Hallazgo:
    """Una comprobación con su resultado y el porqué, en castellano.

    `detalle` no es decorativo: es lo que convierte *«no cumple»* en algo accionable
    para quien está escribiendo el adaptador o el extractor. Una suite que devuelve
    veredictos sin detalle obliga a leer su código para saber qué arreglar.
    """

    comprobacion: str
    severidad: Severidad
    detalle: str
