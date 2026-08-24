"""El manifiesto contra el PLAN congelado. Separado por el límite de 300 líneas.

La partición sale sola: `verificar_corpus.py` comprueba que el manifiesto es
coherente **consigo mismo y con el disco**, y esto comprueba que además es
**lo que se planeó**. Lo primero se puede hacer sin plan; lo segundo no.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

Json = dict[str, object]


def _mapa(d: Json, clave: str) -> Json:
    valor = d.get(clave)
    return valor if isinstance(valor, dict) else {}


def _lista(d: Json, clave: str) -> list[Json]:
    valor = d.get(clave)
    return [x for x in valor if isinstance(x, dict)] if isinstance(valor, list) else []


def _texto(d: Json, clave: str) -> str:
    valor = d.get(clave)
    return valor if isinstance(valor, str) else ""


def _entero(d: Json, clave: str) -> int:
    valor = d.get(clave)
    return valor if isinstance(valor, int) else -1


def _real(d: Json, clave: str) -> float | None:
    valor = d.get(clave)
    return float(valor) if isinstance(valor, int | float) else None


def _fallos_contra_el_plan(m: Json, plan: Json, ruta: Path | None = None) -> list[str]:
    """El manifiesto contra el plan **congelado antes de cosechar**.

    Es la comprobación que convierte el plan en algo más que un documento: si la
    ventana o el filtro no coinciden, lo cosechado no es lo que se planeó, y un
    plan que se ajusta después de ver los resultados no es un plan (§16).
    """
    fuera: list[str] = []
    # LO PRIMERO: que el plan que se pasa sea EL que se congeló. Sin esto, todo lo
    # demás de esta función compara el manifiesto contra un fichero cualquiera, y
    # bastaría escribir a posteriori un plan que cuadrase con lo cosechado.
    declarado = _texto(m, "plan_hash")
    if ruta is not None and declarado:
        real = hashlib.sha256(ruta.read_bytes()).hexdigest()
        if real != declarado:
            fuera.append(
                f"el plan que se pasa NO es el congelado: el manifiesto declara "
                f"{declarado[:12]}… y {ruta} da {real[:12]}…"
            )
    elif not declarado:
        fuera.append("el manifiesto no trae `plan_hash`: no está atado a ningún plan")
    ventana, del_plan = _mapa(m, "ventana"), _mapa(plan, "ventana")
    for extremo in ("desde", "hasta"):
        if str(del_plan.get(extremo)) != str(ventana.get(extremo)):
            fuera.append(
                f"la ventana {extremo}={ventana.get(extremo)} no es la del plan "
                f"({del_plan.get(extremo)})"
            )
    objetivo = _entero(plan, "objetivo_emparejados")
    aceptados = _entero(_mapa(m, "emparejado"), "aceptados")
    if aceptados < objetivo:
        fuera.append(f"{aceptados} emparejados, por debajo del objetivo del plan ({objetivo})")
    en_plan = plan.get("filtro_secciones")
    secciones = {str(s) for s in en_plan} if isinstance(en_plan, list) else set()
    if secciones:
        ajenas = {_texto(d, "seccion") for d in _lista(m, "documentos")} - secciones
        if ajenas:
            fuera.append(f"documentos de secciones que el plan no pide: {sorted(ajenas)}")
    minimo = _real(plan, "ritmo_minimo_s") or 0.0
    medido = _real(_mapa(m, "ritmo"), "espaciado_mediano_s")
    if minimo and medido is None:
        # Saltárselo en silencio es el mismo fallo que el directorio ausente: sin
        # espaciado medido NO se puede afirmar que se respetó el ritmo prometido.
        fuera.append(
            f"NO EJECUTADA la comprobación del ritmo: el manifiesto no trae "
            f"`espaciado_mediano_s`, así que el {minimo} s declarado no se comprueba"
        )
    elif minimo and medido is not None and medido < minimo:
        fuera.append(
            f"espaciado mediano {medido} s, por debajo del {minimo} s declarado: "
            "se cosechó más rápido de lo prometido"
        )
    return fuera
