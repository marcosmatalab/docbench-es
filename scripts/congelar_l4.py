"""Re-congela los 30 fixtures de L4 **después** de corregir, y no deja colar nada más.

    uv run python scripts/congelar_l4.py --motivo "…"

## El candado, que es todo el fichero

Un script que rehace el manifiesto de congelación cuando se le pide es justo el
agujero que hace inútil congelar. Por eso éste **compara contra el congelado
original y exige que cada huella que ha cambiado tenga su corrección registrada**
en `runs/l4/correcciones.json`, con su evidencia contra el PDF.

- huella cambiada **con** corrección registrada → se re-congela
- huella cambiada **sin** corrección registrada → **aborta y no escribe nada**
- fixture nuevo o desaparecido → aborta

Así, «re-congelar» no puede ser nunca «tapar un cambio»: sólo puede ser «fijar lo
que se corrigió con evidencia, y nada más».

**El congelado original no se toca.** `runs/l4/congelacion.json` guarda el estado de
antes de la primera comparación y es el eslabón que hace auditable la cadena
*transcrito ciego → comparado → adjudicado → corregido*. Sobrescribirlo la borraría.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
L4 = RAIZ / "runs" / "l4"
FIXTURES = L4 / "fixtures"


def huellas() -> dict[str, str]:
    return {
        f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(FIXTURES.glob("*.json"))
    }


def sello_git() -> str:
    """El sello del árbol. **Con `check=True`**: un git que falle escribiría un sello
    vacío en el manifiesto sin avisar, y un manifiesto sellado con la cadena vacía es
    peor que uno sin sello, porque parece que lo tiene."""
    corto = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    sucio = subprocess.run(
        ["git", "status", "--porcelain"], cwd=RAIZ, capture_output=True, text=True, check=True
    ).stdout.strip()
    if not corto:
        raise RuntimeError("git no ha devuelto un sello: el manifiesto no se escribe sin él")
    return f"{corto}{'+sucio' if sucio else ''}"


CONTENIDO = ("filas", "ultima_fila", "spans", "dimension", "indice_de_la_ultima_fila")
"""Las claves que SON la transcripción. Todo lo demás es procedencia y anotación."""


def es_solo_anotacion(nombre: str) -> bool:
    """¿El cambio deja la TRANSCRIPCIÓN byte a byte igual?

    Una anotación —marcar un fixture como contaminado, por ejemplo— no es una
    corrección: no toca ni una celda, así que no necesita evidencia del PDF. Pero
    **sí mueve la huella**, y sin esta distinción el guardián obligaría a una de dos
    cosas malas: o registrar una corrección falsa, o dejar el fixture sin marcar.

    La versión anterior se lee de **git**, no de una copia: comparar contra algo que
    esté en el árbol de trabajo permitiría cambiar las dos cosas a la vez.
    """
    hecho = subprocess.run(
        ["git", "show", f"HEAD:runs/l4/fixtures/{nombre}"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )
    if hecho.returncode != 0:
        return False  # no está en HEAD: no hay contra qué comparar, no se asume nada
    viejo = json.loads(hecho.stdout)
    nuevo = json.loads((FIXTURES / nombre).read_text(encoding="utf-8"))
    return all(viejo.get(k) == nuevo.get(k) for k in CONTENIDO)


def sin_respaldo(
    antes: dict[str, str],
    ahora: dict[str, str],
    con_evidencia: set[str],
    anotados: set[str] = frozenset(),  # type: ignore[assignment]
) -> tuple[list[str], list[str]]:
    """EL GUARDIÁN. Las huellas que se movieron sin explicación, y al revés.

    Vive en su propia función para que se pueda **ver roja desde un test** sin
    montar un árbol entero. Un guardián que sólo se puede ejercitar corriendo el
    script completo acaba sin ejercitar.

    Devuelve `(cambiadas_sin_respaldo, correcciones_que_no_cambiaron_nada)`. Las dos
    son motivo de abortar, y por razones distintas: la primera es un cambio que se
    cuela, la segunda un registro que miente sobre lo que hizo. Un cambio respaldado
    lo está por una **corrección con evidencia del PDF** o por ser **sólo anotación**
    —la transcripción intacta—, y las dos se registran por separado.
    """
    cambiados = {n for n in ahora if ahora.get(n) != antes.get(n)}
    return sorted(cambiados - con_evidencia - anotados), sorted(con_evidencia - cambiados)


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--motivo", required=True)
    args = partes.parse_args()

    antes = json.loads((L4 / "congelacion.json").read_text(encoding="utf-8"))["huellas"]
    ahora = huellas()
    if set(antes) != set(ahora):
        print(f"  ABORTA: la lista de fixtures ha cambiado. {set(antes) ^ set(ahora)}")
        return 1

    cambiados = sorted(n for n in ahora if ahora[n] != antes[n])
    correcciones = json.loads((L4 / "correcciones.json").read_text(encoding="utf-8"))
    con_evidencia = {f"{c['fixture']}.json" for c in correcciones["correcciones"]}

    cambiados_set = {n for n in ahora if ahora[n] != antes[n]}
    anotados = {n for n in cambiados_set - con_evidencia if es_solo_anotacion(n)}
    sin_registrar, registradas_sin_cambio = sin_respaldo(antes, ahora, con_evidencia, anotados)
    if sin_registrar:
        print(f"  ABORTA: huellas cambiadas SIN corrección registrada: {sin_registrar}")
        print("  Un cambio sin evidencia contra el PDF no se congela. No se escribe nada.")
        return 1
    if registradas_sin_cambio:
        print(f"  ABORTA: correcciones registradas que no cambiaron nada: {registradas_sin_cambio}")
        return 1

    for n in cambiados:
        clase = "SÓLO ANOTACIÓN" if n in anotados else "corrección con evidencia"
        print(f"  cambiada, {clase}: {n}")
        print(f"    {antes[n][:16]}… → {ahora[n][:16]}…")
    print(f"  intactos: {len(ahora) - len(cambiados)} de {len(ahora)}")

    (L4 / "recongelacion.json").write_text(
        json.dumps(
            {
                "esquema": "docbench-es.recongelacion-fixtures/1",
                "sello": sello_git(),
                "motivo": args.motivo,
                "congelado_original": "runs/l4/congelacion.json",
                "correcciones": "runs/l4/correcciones.json",
                "DESPUES_DE": (
                    "la primera comparación y la adjudicación una a una. Las 6 correcciones"
                    " son errores de transcripción evidenciados contra el PDF (ADR-0039"
                    " regla 5); las 5 discrepancias de frontera NO se han tocado"
                ),
                "n": len(ahora),
                "cambiados": cambiados,
                "por_correccion_con_evidencia": sorted(set(cambiados) - anotados),
                "por_anotacion_sin_tocar_la_transcripcion": sorted(anotados),
                "intactos": len(ahora) - len(cambiados),
                "huellas": ahora,
            },
            indent=1,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print("  Escrito runs/l4/recongelacion.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
