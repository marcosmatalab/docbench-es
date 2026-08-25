"""El INFORME de L4: una fila por fixture, y el desglose que se publica.

Vive aparte de `comparar_verdad.py` **porque aquél llegó a 309 líneas** y la regla
del repo no admite excepciones sin razón escrita. La partición no es arbitraria: el
comparador **decide** —qué cuenta como reproducir, ADR-0040— y esto **serializa** lo
que decidió. Sigue siendo el comparador quien lo emite: es su comando y sus datos.

## Por qué existe el informe

El desglose publicado —«21 coincidencias limpias + 1 contaminada + 3 corregidas»— se
**deducía** cruzando a mano la lista de fixtures con discrepancia contra un
`"contaminadas": 1` que ni siquiera decía cuál era. Y por eso se llegó a publicar una
horquilla —«21 o 22»— sobre algo **completamente determinado por dos artefactos que
ya existían**.

> **Antes de declarar algo NO MEDIBLE, comprueba si es DERIVABLE de lo que ya está
> medido.** Una horquilla que se puede cerrar y se publica abierta dice menos de lo
> que se sabe, y eso también es una forma de no ser preciso.

Con el informe, el desglose **se lee de un artefacto**. Ver `LIMITS.md` 71.
"""

from __future__ import annotations

import json
from pathlib import Path


def corregidos(raiz: Path) -> set[str]:
    """Los fixtures que se corrigieron tras adjudicar, del registro de correcciones."""
    ruta = raiz / "runs" / "l4" / "correcciones.json"
    if not ruta.exists():
        return set()
    registro = json.loads(ruta.read_text(encoding="utf-8"))
    return {str(c["fixture"]) for c in registro["correcciones"]}


def fila(
    fx: dict[str, object], nombre: str, n_discrepancias: int, clases: list[str], fue_corregido: bool
) -> dict[str, object]:
    """Lo que se sabe de un fixture después de compararlo. **Sin adjudicar.**"""
    return {
        "fixture": nombre,
        "coincide": n_discrepancias == 0,
        "discrepancias": n_discrepancias,
        "clases": clases,
        "contaminada": bool(fx.get("contaminada", False)),
        "corregido_tras_adjudicar": fue_corregido,
        "alcance": fx.get("alcance"),
    }


def cobertura(celdas_comparadas: int, celdas_ancladas: int) -> dict[str, object]:
    """El denominador del «53,1% de cobertura», **emitido en vez de tecleado**.

    Se publicó como *«1.213 de 2.283 celdas»* **sin que ningún script emitiera el
    2.283 ni ningún JSON lo guardara**. Reconstruirlo desde los fixtures da 2.301 o
    2.281 según cómo se cuente, y los 3 de alcance `ventana` no registran los spans
    del tramo no transcrito, así que **un lector no podía derivarlo**. Un porcentaje
    cuyo denominador nadie puede recomputar es exactamente lo que prohíbe la regla de
    oro 2.
    """
    return {
        "celdas_comparadas": celdas_comparadas,
        "celdas_ancladas_en_las_30_tablas": celdas_ancladas,
        "porcentaje": round(100 * celdas_comparadas / celdas_ancladas, 1),
    }


def desglose(filas: list[dict[str, object]]) -> dict[str, int]:
    """Los tres sumandos de los que coinciden. **Tienen que sumar el total.**"""
    coinciden = [r for r in filas if r["coincide"]]
    return {
        "limpias": sum(
            1 for r in coinciden if not r["contaminada"] and not r["corregido_tras_adjudicar"]
        ),
        "contaminadas": sum(1 for r in coinciden if r["contaminada"]),
        "corregidas_tras_adjudicar": sum(1 for r in coinciden if r["corregido_tras_adjudicar"]),
    }


def escribir(
    raiz: Path,
    filas: list[dict[str, object]],
    discrepancias: int,
    celdas_comparadas: int,
    celdas_ancladas: int,
) -> Path:
    """Escribe `runs/l4/informe.json` y devuelve su ruta."""
    cuentas = desglose(filas)
    destino = raiz / "runs" / "l4" / "informe.json"
    destino.write_text(
        json.dumps(
            {
                "esquema": "docbench-es.informe-l4/1",
                "comando": "uv run python scripts/comparar_verdad.py --informe",
                "reglas": "docs/adr/0040-las-reglas-del-comparador-de-verdad.md",
                "n": len(filas),
                "coinciden": sum(1 for r in filas if r["coincide"]),
                "discrepancias": discrepancias,
                "desglose_de_los_que_coinciden": cuentas,
                "cobertura": cobertura(celdas_comparadas, celdas_ancladas),
                "contaminadas_declaradas": [str(r["fixture"]) for r in filas if r["contaminada"]],
                "por_fixture": filas,
            },
            indent=1,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return destino
