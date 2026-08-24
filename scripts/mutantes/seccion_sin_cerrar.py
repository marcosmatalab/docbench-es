"""**MUTANTE.** `cerrar_seccion` vuelve a NO terminar el grupo de filas.

Es el estado en que estaba el repo hasta el cierre de L3: `cerrar_seccion` sólo
resolvía los `rowspan="0"` y no avanzaba hasta `yheight`, así que un `rowspan` de
la última fila del `<thead>` se derramaba en el `<tbody>` y **desplazaba los datos
una columna**, con `validate` diciendo `ok=True`.

**Por qué este mutante y no otro.** El fallo no producía ningún hallazgo: la tabla
salía bien formada, con los números en la celda equivocada. Un bug que no se puede
ver en la salida sólo se caza con un test que fije la geometría, y un test que
nadie ha visto rojo no es un test. Éste lo pone rojo.
"""

from __future__ import annotations

from docbench_es.core.canonical import _rejilla


def _sin_terminar_el_grupo(self: _rejilla.Colocador) -> None:
    """Lo de antes: resuelve los pendientes y **no avanza**."""
    self._resolver_pendientes()


_rejilla.Colocador.cerrar_seccion = _sin_terminar_el_grupo  # type: ignore[method-assign]
