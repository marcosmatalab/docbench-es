"""Lo que la portada necesita del REPO y no de la campaña. **Y por qué son dos fuentes.**

La regla de la portada es que **ninguna cifra se teclea en la plantilla**. La pregunta
que queda es de dónde sale cada una, y la respuesta la decide **la cadencia**, no la
comodidad:

| cifra | cambia cuando | vive en |
|---|---|---|
| titular, bandas, notas, coste | se corre la campaña | `runs/l5/informe.json` |
| límites, ADR, mutantes, techo | **en cualquier commit** | el repo, ahora mismo |

**Meter las de la derecha en `informe.json` habría sido peor, y es un caso medido.** Ese
fichero lo escribe `docbench report`, que necesita los **143 MB de diarios** que el repo
no versiona (LIMITS 109). Un `114` congelado ahí dentro se quedaría viejo el día que
entre el límite 115, y arreglarlo exigiría rehacer una campaña de 2,30 h con el corpus
delante — o sea que la puerta se pondría roja **sin arreglo disponible**, que es la peor
clase de guardián. Contándolos aquí, en cada generación, no pueden estar viejos.

Es la misma decisión, y por la misma razón, que `tests/unit/conftest.py` tomó con los
recuentos: *«un JSON que escribe `matar.py` sólo está al día si alguien se acuerda de
correr `matar.py`»*.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Censo", "del_repo"]


@dataclass(frozen=True)
class Censo:
    """El estado del repo hoy, contado. **Ningún campo tiene valor por defecto.**

    Sin defecto a propósito: un campo con `= 0` deja pasar un censo que no se hizo, y un
    cero en la portada se lee como una medida —la decisión B3 otra vez, tres capas más
    arriba—.
    """

    limites: int
    """Entradas numeradas de `LIMITS.md`."""
    adr: int
    """Ficheros de `docs/adr/`."""
    mutantes: int
    """Ficheros de `scripts/mutantes/`, sin `matar.py`, que es el arnés y no un mutante."""
    techo_ms: int
    """`TECHO_LOCAL_MS` de `.techos`."""
    techo_anterior_ms: int
    """`TECHO_LOCAL_ANTERIOR_MS` de `.techos`: contra qué bajó."""
    p90_ms: int
    """`PUERTA_P90_MS` de `.techos`: la medida que justifica el techo."""
    error_del_estimador: float
    """`error_contra_lo_medido` de `runs/l5/reloj.json`. El fallo de predicción del coste."""


def _clave(techos: str, clave: str) -> int:
    casa = re.search(rf"^{clave}=(\d+)$", techos, re.M)
    if casa is None:
        raise ValueError(f"`.techos` no declara {clave}: la portada no puede publicar la puerta")
    return int(casa.group(1))


def del_repo(raiz: Path) -> Censo:
    """Cuenta el repo tal y como está. **Todo por ejecución, nada leído de una prosa.**

    Los límites se cuentan por su numeración, igual que `reglas_de_censo._cuantos_limites`,
    y no por la frase «hay N límites numerados» que publican los documentos: contar la
    prosa haría que la portada repitiera un número en vez de medirlo, y esa frase ya se
    quedó vieja una vez —82 cuando eran 88—.
    """
    limites = set(
        re.findall(r"^(\d+)\. ", (raiz / "LIMITS.md").read_text(encoding="utf-8"), flags=re.M)
    )
    techos = (raiz / ".techos").read_text(encoding="utf-8")
    reloj = json.loads((raiz / "runs" / "l5" / "reloj.json").read_text(encoding="utf-8"))
    return Censo(
        limites=len(limites),
        adr=len(list((raiz / "docs" / "adr").glob("*.md"))),
        mutantes=len(
            [p for p in (raiz / "scripts" / "mutantes").glob("*.py") if p.stem != "matar"]
        ),
        techo_ms=_clave(techos, "TECHO_LOCAL_MS"),
        techo_anterior_ms=_clave(techos, "TECHO_LOCAL_ANTERIOR_MS"),
        p90_ms=_clave(techos, "PUERTA_P90_MS"),
        error_del_estimador=float(reloj["error_contra_lo_medido"]["valor"]),
    )
