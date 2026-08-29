"""§12 bis · La portada: la puerta de entrada de diez minutos, **generada**.

## El problema que resuelve, y no es de rigor

`LIMITS.md` son 2.400 líneas, `RESULTS.md` 2.100 y `MANUAL.md` 2.000. Quien ya sabe qué
está mirando se convence rápido; quien no, rebota. **Los límites no existen para quien no
llega a ellos**, y ése es un problema de distribución, no de método.

## Por qué GENERADA, que es la única parte discutible

Una portada con los números tecleados sería **la copia número catorce del titular y la
primera en quedarse vieja**: exactamente lo que `scripts/derivadas.py` existe para
impedir. El repo ya tiene el caso medido —el README se quedó **33 commits** rancio— y ya
tiene la cura: `scripts/estado_readme.py`, un generador con dos salidas. Ésta es la misma
forma, con otra fuente:

    uv run docbench portada --informe runs/l5/informe.json --salida docs/index.html

* **`docs/index.html`** — la página entera, servida por GitHub Pages;
* **el bloque `PORTADA` del `README.md`** — la versión corta, con tope de líneas.

## Las dos fuentes, y por qué son dos

`runs/l5/informe.json` para lo que cambia **con la campaña**; el censo del repo para lo
que cambia **en cualquier commit**. El porqué, con el modo de fallo que evita, está en
`_censo.py` — y no es una comodidad: congelar el recuento de límites dentro de
`informe.json` pondría la puerta roja sin arreglo disponible el día que entre el
siguiente, porque rehacer ese fichero exige los 143 MB de diarios que el repo no lleva.

## Y qué NO hace este módulo

**No mide nada.** Igual que `report.informe`, es serialización de lo que
`report.nivel1` y `report.cara_a_cara` ya calcularon. Si la portada y la tabla en
Markdown discreparan, el bug estaría en el renderizado — y por eso las dos salen de las
mismas cifras y las compara la regla **R9** de `scripts/derivadas.py`.
"""

from __future__ import annotations

from docbench_es.report.portada._censo import Censo, del_repo
from docbench_es.report.portada._cifras import Cifra, cifras
from docbench_es.report.portada._corto import FIN, INICIO, bloque_corto
from docbench_es.report.portada._pagina import marca, pagina

__all__ = [
    "FIN",
    "INICIO",
    "Censo",
    "Cifra",
    "bloque_corto",
    "cifras",
    "del_repo",
    "marca",
    "pagina",
]
