"""**MUTANTE.** El emparejado deja de exigir que los recuentos coincidan.

Es **la alternativa que `runs/l5/emparejado.yaml` descarta por catastrófica**, no una
variante razonable: empareja por orden la k-ésima con la k-ésima y se queda con las que
haya. Un extractor que se salta la primera tabla compara su tabla 2 contra la 1 de la
verdad, su 3 contra la 2, y saca notas ruinosas en TODAS por un solo fallo de detección.

**Qué números haría mentir, que es el motivo de que exista este mutante.** Con él, todo
documento «puntúa»: el acuerdo de recuento sube al 100%, la cobertura evaluable se infla,
los `NO_APLICABLE` desaparecen —y con ellos la distinción entre «no se pudo comparar» y
«se comparó y salió mal», que es la decisión B3— y el TEDS publicado pasa a medir
desalineamiento en vez de calidad. O sea: **las cuatro columnas del titular de L5 a la
vez**, y ninguna se vería rara.

Sólo lo mata un test que afirme que un documento con N≠M **no cuenta**: ni en el acuerdo,
ni en la cobertura, ni en la nota.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docbench_es.report import nivel1

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Sequence

    from docbench_es.types import CanonicalTable


def _por_orden_a_secas(
    pred: Sequence[CanonicalTable], gold: Sequence[CanonicalTable]
) -> list[tuple[CanonicalTable, CanonicalTable]] | None:
    """Nunca dice «este documento no puntúa»: siempre devuelve pares."""
    return list(zip(pred, gold, strict=False))


nivel1._emparejar = _por_orden_a_secas  # type: ignore[assignment]
