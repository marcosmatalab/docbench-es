"""`teds_batch` vuelve a guardar `dict[clave] = nota`: la última tabla pisa a las demás.

La versión que tenía L2 antes del escrutinio. Un documento con varias tablas
—la clave es la del documento, no la de la tabla— perdía todas menos la última,
**sin contarlo y sin avisar**, y `evaluable_coverage` seguía diciendo 1,0. Regla
de oro 6 rota en las dos mitades. Ver ADR-0024.
"""

import docbench_es.core.teds as teds_mod
from docbench_es.types import TedsReport


def _batch(pairs, *, solo_estructura=False):
    por_documento = {}
    no_aplicable = []
    for clave, pred, gold in pairs:
        if teds_mod._es_evaluable(pred, gold):
            por_documento[clave] = teds_mod._puntuar(pred, gold, solo_estructura=solo_estructura)
        else:
            por_documento[clave] = None
            no_aplicable.append(clave)
    evaluables = [v for v in por_documento.values() if v is not None]
    return TedsReport(
        per_document=por_documento,
        aggregate=sum(evaluables) / len(evaluables) if evaluables else None,
        evaluable_coverage=len(evaluables) / len(por_documento) if por_documento else 0.0,
        not_applicable=tuple(no_aplicable),
    )


def pytest_configure(config: object) -> None:
    teds_mod.teds_batch = _batch
