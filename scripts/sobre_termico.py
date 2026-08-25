"""El sobre térmico: qué dice `runs/l5/termica.yaml` y cómo se resuelve al correr.

Va aparte de `computo_l5.py` porque leer la política y orquestar la corrida son dos
responsabilidades — y porque el orquestador volvió a pasarse de 300 líneas al juntarlas.

## Las dos cosas que este fichero mantiene separadas

* **No hay termómetro** → no se afirma ni un grado. Nunca se toca.
* **No hay sobre que vigilar** → se corre a todos los hilos.

La segunda se deducía de la primera, y no se sigue: es una decisión de una persona, con
fecha y razón, y vive en el YAML y no en la cabeza de nadie. Un guardián apagado sin
razón escrita es peor que uno que nunca existió.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from gobernador import Termica  # noqa: E402

SOBRE = RAIZ / "runs" / "l5" / "termica.yaml"


def _hilos(valor: object) -> int:
    """`todos` se resuelve al correr. Un número derivado no se teclea: así, subir
    `processors` en `.wslconfig` basta y no hay que editar el sobre."""
    if isinstance(valor, str) and valor.strip().lower() == "todos":
        return os.cpu_count() or 1
    return int(str(valor))


def modo_de_vigilancia() -> str:
    """`ninguna` o `termometro`, de `runs/l5/termica.yaml`. **La decisión vive ahí.**

    Separa dos cosas que estaban juntas: *no hay termómetro* —de lo que nunca se sigue
    que se pueda afirmar un grado— y *no hay sobre que vigilar*, que es una decisión de
    una persona con fecha y razón escrita. Un guardián apagado sin razón escrita es peor
    que uno que nunca existió.
    """
    d = yaml.safe_load(SOBRE.read_text(encoding="utf-8")).get("vigilancia", {})
    modo = str(d.get("modo", "termometro")).strip().lower()
    if modo not in {"ninguna", "termometro"}:
        raise ValueError(f"vigilancia.modo desconocido en {SOBRE.name}: {modo!r}")
    return modo


def sobre(vigilado: bool) -> tuple[Termica, dict[str, float]]:
    """El sobre térmico, LEÍDO de `runs/l5/termica.yaml`. Un número derivado no se teclea."""
    d = yaml.safe_load(SOBRE.read_text(encoding="utf-8"))
    lim, carga = d["limites"], d["carga"]
    ciclo = d["ciclo"]
    t = Termica(
        hilos=_hilos(carga["hilos_con_termometro" if vigilado else "hilos_sin_termometro"]),
        techo=float(lim["techo_c"]),
        reanudar=float(lim["reanudar_c"]),
        objetivo_media=float(lim["objetivo_media_c"]),
        vigilado=vigilado,
        periodo=float(ciclo["periodo_s"]),
        fraccion=float(ciclo["fraccion_con_termometro" if vigilado else "fraccion_sin_termometro"]),
        latido=float(ciclo["latido_s"]),
    )
    # El tope por unidad ya no escala con los hilos: con «todos» siempre se corre a la
    # máxima velocidad de la máquina, así que no hay configuración lenta contra la que un
    # tope fijo fuera injusto. Sigue siendo red de seguridad contra un extractor colgado.
    ritmo = {
        # El descanso ENTRE unidades ya no es la barrera: lo es el ciclo de trabajo,
        # que acota el consumo medio DENTRO de cada unidad. Antes, a ciegas, este
        # factor valía 1,0 y duplicaba la sesión sin añadir ninguna seguridad.
        "base": float(carga["descanso_base"]),
        "tope": float(carga["descanso_tope_s"]),
        "unidad": float(carga["tope_unidad_min"]) * 60.0,
    }
    return t, ritmo


def factor_de_descanso(base: float, actual: float, media: float | None, objetivo: float) -> float:
    """La pausa se alarga si la media de la sesión pasa del objetivo y se acorta si va
    holgada. Es el único lazo que controla la MEDIA; el pico lo controla el `SIGSTOP`."""
    if media is None:
        return actual
    if media > objetivo:
        return min(actual * 1.4, 4.0)
    if media < objetivo - 6.0:
        return max(base, actual / 1.3)
    return actual
