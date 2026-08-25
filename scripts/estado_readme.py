"""Regenera el bloque de estado del README **desde `ESTADO.md`**. El comando.

    uv run python scripts/estado_readme.py            # comprueba, no escribe
    uv run python scripts/estado_readme.py --escribir

## Por qué existe

El README **se quedó 33 commits rancio**: con cuatro hitos cerrados seguía diciendo
*«Hito L0 de 10 de la v0.1.0. Todavía no hay número»* y *«L1 a L8b pendientes»*, y
publicaba la puerta sobre un commit de L0. Y la ironía es el argumento: **el propio
README contiene** *«en un repo que vende rigor, escribir en presente lo que no existe
es el peor fallo posible, más grave que un bug»*.

**El arreglo no es actualizarlo.** Un fichero que hay que acordarse de tocar se va a
quedar rancio otra vez, y ya sabemos cuántos commits tarda: **33**. Así que el estado
**se deriva** de `ESTADO.md`, que sí se actualiza en cada cierre porque lo inyecta el
hook `SessionStart` y porque `/cerrar` lo exige.

## Cómo

El README lleva dos marcas HTML y **todo lo que hay entre ellas se genera**. Fuera de
ellas se escribe a mano, como siempre. `tests/unit/test_barreras.py` comprueba que lo
generado coincide con lo que hay: si `ESTADO.md` avanza y el README no, **la puerta se
pone roja** en vez de quedarse callada.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INICIO, FIN = "<!-- ESTADO:inicio -->", "<!-- ESTADO:fin -->"
T_INICIO, T_FIN = "<!-- TITULAR:inicio -->", "<!-- TITULAR:fin -->"


def hitos() -> list[tuple[str, str, str]]:
    """`(hito, estado, número)` de cada fila de la tabla de `ESTADO.md`."""
    fuera = []
    for linea in (RAIZ / "ESTADO.md").read_text(encoding="utf-8").splitlines():
        if not linea.startswith("| L"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) < 5:
            continue
        nombre = celdas[0].split("`")[0].strip().rstrip(" ")
        fuera.append((nombre.split(" ")[0], celdas[2], celdas[4]))
    return fuera


def bloque(prefijo: str = "") -> str:
    """El texto que va entre las dos marcas. **Derivado, nunca tecleado.**"""
    filas = hitos()
    cerrados = [h for h, e, _ in filas if "CERRADO" in e]
    siguiente = next((h for h, e, _ in filas if "el siguiente" in e), "—")
    ultimo = next((n for h, e, n in reversed(filas) if "CERRADO" in e), "")
    puerta = re.search(r"\*\*Puerta: p90 (\d+) ms, techo (\d+), margen (\d+) ms\*\*", ultimo)
    sello = re.search(r"sello `([0-9a-f]+)`", ultimo)
    fecha = re.search(
        r"CERRADO (\d{4}-\d{2}-\d{2})", [e for _, e, _ in filas if "CERRADO" in e][-1]
    )
    lineas = [
        INICIO,
        "| | |",
        "|---|---|",
        f"| Release en curso | `v0.1.0` · **{len(cerrados)} hitos cerrados**"
        f" ({', '.join(cerrados)}), el último el {fecha.group(1) if fecha else '—'}."
        f" Siguiente: **{siguiente}** |",
    ]
    if puerta and sello:
        lineas.append(
            f"| La puerta | `make fast` en verde. **p90 {puerta.group(1)} ms** local"
            f" sobre `{sello.group(1)}`, techo {puerta.group(2)} (ADR-0022),"
            f" margen {puerta.group(3)} ms, n=40 en frío. El presupuesto del manual son"
            f" 90 s y es del runner. Procedencia en [`RESULTS.md`]({prefijo}RESULTS.md) |"
        )
    lineas += [
        f"| Dónde va el checkpoint | [`ESTADO.md`]({prefijo}ESTADO.md), que se actualiza al cerrar"
        " cada hito. **Esta tabla se genera desde ahí** con"
        " `uv run python scripts/estado_readme.py --escribir` |",
        FIN,
    ]
    return "\n".join(lineas)


def titular() -> str:
    """La primera línea del README. **Decía «Hito L0 de 10» con cuatro hitos más
    cerrados**, y el propio README dice que escribir en presente lo que no existe es
    el peor fallo posible aquí. Se deriva."""
    filas = hitos()
    cerrados = [h for h, e, _ in filas if "CERRADO" in e]
    siguiente = next((h for h, e, _ in filas if "el siguiente" in e), "—")
    ultimo = next((n for h, e, n in reversed(filas) if "CERRADO" in e), "")
    criterio = next((c for h, e, c in [(h, e, n) for h, e, n in filas] if h == cerrados[-1]), "")
    del criterio
    numero = ultimo.split(",")[0].replace("**", "").strip() if ultimo else "—"
    return "\n".join(
        [
            T_INICIO,
            f"> **{len(cerrados)} de 10 hitos de la `v0.1.0` cerrados** —"
            f" {', '.join(cerrados)} — y el siguiente es **{siguiente}**. El último"
            f" número medido: **{numero}** ({cerrados[-1]}).",
            ">",
            "> Lo que hay medido está en [`RESULTS.md`](RESULTS.md); lo que este"
            " proyecto **no** mide, en [`LIMITS.md`](LIMITS.md). **Esta línea se genera"
            " desde [`ESTADO.md`](ESTADO.md)**: no se teclea.",
            T_FIN,
        ]
    )


def actual(texto: str, ini: str = INICIO, fin: str = FIN) -> str:
    i, j = texto.index(ini), texto.index(fin) + len(fin)
    return texto[i:j]


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--escribir", action="store_true")
    args = partes.parse_args()

    for ruta in (RAIZ / "README.md", RAIZ / "docs" / "reading-order.md"):
        rc = _un_fichero(ruta, args.escribir)
        if rc:
            return rc
    return 0


def _un_fichero(ruta: Path, escribir: bool) -> int:
    """Un documento con marcas. **Los dos, no sólo el README.**

    `docs/reading-order.md` es la tercera puerta que lee un extraño y se quedó
    diciendo «a 21 de agosto de 2026 el repo está en L0» con cinco hitos cerrados,
    enlazada desde un README que ya era correcto. Una puerta arreglada que apunta a
    una sin arreglar no está arreglada.
    """
    texto = ruta.read_text(encoding="utf-8")
    for marca in (INICIO, FIN):
        if marca not in texto:
            print(f"  ABORTA: falta la marca {marca} en {ruta.name}")
            return 2
    prefijo = "../" if ruta.parent.name == "docs" else ""
    partidas = [(INICIO, FIN, bloque(prefijo))]
    if T_INICIO in texto:
        partidas.append((T_INICIO, T_FIN, titular()))
    rancias = [(i, f, n) for i, f, n in partidas if actual(texto, i, f) != n]
    if not rancias:
        print(f"  {ruta.name} coincide con ESTADO.md.")
        return 0
    if not escribir:
        print(f"  {ruta.name} ESTÁ RANCIO. Regenéralo:")
        print("    uv run python scripts/estado_readme.py --escribir")
        for _, _, n in rancias:
            print(f"\n{n}\n")
        return 1
    for i, f, n in partidas:
        texto = texto.replace(actual(texto, i, f), n)
    ruta.write_text(texto, encoding="utf-8")
    print(f"  {ruta.name} regenerado desde ESTADO.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
