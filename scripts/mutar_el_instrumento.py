"""El arnés de mutantes contra **el instrumento de L4**, no contra la suite. El comando.

    uv run python scripts/mutar_el_instrumento.py            # los 22, con su recuento
    uv run python scripts/mutar_el_instrumento.py --solo seccion_sin_cerrar --detalle

## Por qué existe, y es la única forma de que «0 fallos del código» valga algo

L4 publica **cero discrepancias atribuibles al código** sobre 1.213 celdas. Ese cero
tiene dos lecturas incompatibles y **desde fuera se leen igual**:

1. `truth.derived` reproduce el PDF, o
2. estos 30 fixtures **no pueden ver** un fallo de `truth.derived`.

Un cero sin distinguirlas es indistinguible de una venda en los ojos. La prueba que
las separa es la de siempre en este repo, aplicada un nivel más arriba: **se rompe
el código a propósito y se cuenta cuántos fixtures se caen**.

**El mutante de referencia es `seccion_sin_cerrar`**, que es el bug real de hace unas
horas: `cerrar_seccion` no terminaba el grupo de filas, un `rowspan` del `<thead>` se
derramaba en el `<tbody>` y **desplazaba los datos una columna** con `validate`
diciendo `ok=True`. Si al reintroducirlo las 30 siguen coincidiendo, el cero no vale.

## Las dos cifras que publica, y no son la misma

- **`mata`**: de los fixtures que coinciden sin mutar, cuántos dejan de coincidir.
- **`cambia`**: de los **30**, cuántos cambian su conjunto de discrepancias. Hace
  falta además de `mata` porque **un fixture que ya tiene una discrepancia de
  frontera no puede «dejar de coincidir»**: `mata` no lo puede contar nunca. Es
  exactamente lo que pasó con `seccion_sin_cerrar` y `BOE-A-2026-7446-t0`, que es
  una de las dos tablas de la muestra con la forma que dispara ese bug.
- **`alcanzado`**: si el código del mutante **llegó a ejecutarse** durante las 30
  comparaciones, medido con `sys.settrace` sobre los eventos de llamada.

La combinación es lo que hay que leer, porque un cero significa dos cosas distintas:

| alcanzado | cambia | Qué es |
|---|---|---|
| sí | > 0 | el instrumento ve ese fallo |
| **sí** | **0** | **HUECO MEDIDO del instrumento**: el fallo ocurre y no se nota.
  Va a `LIMITS.md` con su nombre |
| no | 0 | el mutante no llega al sujeto. No dice nada del instrumento |
| sí | 0, y **equivalente** | el mutante no cambia la salida. Tampoco dice nada |

Confundir esas filas convertiría en virtud lo que es un agujero, o al revés:
acusaría al instrumento de no ver algo que no está. Las dos versiones de este
barrido se equivocaron en una de las dos direcciones antes de llegar aquí.

## Una decisión que empeora el resultado a propósito

El mutante se aplica **antes** de importar el comparador, igual que `pytest -p` hace
con sus plugins. Consecuencia: si el mutante toca algo que usan **los dos lados** —el
comparador y la verdad—, el error **se cancela** y el mutante sobrevive. Es el
límite 52 otra vez. Se elige así porque es la dirección pesimista: hace que el
instrumento parezca peor de lo que es, y un instrumento que se mide a sí mismo tiene
que equivocarse hacia ahí.

**`n3_incompleta` muta una CONSTANTE**, no una función, así que no puede tener
`alcanzado` por llamada y sale `dato`. Su alcance se lee del módulo, que sí ejecuta.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MUTANTES = RAIZ / "scripts" / "mutantes"
EQUIVALENTES = {
    "n3_incompleta": (
        "muta la constante CATEGORIAS_DE_ESPACIO quitando Zl y Zp, y `normalize_cell_text`"
        ' termina en `" ".join(s.split())`, que los considera espacio igualmente. Comprobado'
        " sobre las cuatro categorías —Zl, Zp, Zs, Cc—: la salida es idéntica con y sin"
        " mutante, así que NINGÚN instrumento puede verlo por la salida de esa función"
    )
}
"""Mutantes cuyo efecto **no se observa en la salida del sujeto**, con la evidencia.

Un mutante equivalente que sale «mata 0» **no es un hueco del instrumento**: es un
mutante que no rompe nada visible. Meterlo en la columna de huecos acusaría al
instrumento de no ver algo que no está. La primera versión de este barrido lo hacía.
"""


def _los_mutantes() -> list[str]:
    return sorted(f.stem for f in MUTANTES.glob("*.py") if f.stem not in {"matar", "__init__"})


def _clave(clase: str, detalle: str) -> str:
    """La IDENTIDAD de una discrepancia: su clase y su posición. **Nunca su texto.**

    `detalle` lleva dentro el texto normalizado de la celda, así que compararlo
    entero hace que **un mutante que sólo cambie cómo se renderiza el texto cuente
    como detectado sin haber detectado nada**. Fue un falso positivo real:
    `normalizador_agresivo` salía «cambia 3 de 30» y las 3 eran las mismas
    discrepancias de frontera de siempre, con el mensaje en minúsculas.
    """
    posicion = re.match(r"^\((\d+), (\d+)\)", detalle)
    return f"{clase}@{posicion.group(0) if posicion else '-'}"


def _comparar_las_30() -> tuple[set[str], dict[str, list[str]]]:
    """Las 30 comparaciones. Devuelve los que coinciden y el detalle de los demás."""
    # `comparar_verdad` a secas y NO `scripts.comparar_verdad`: el mismo fichero bajo
    # dos nombres de módulo pone `mypy --strict` en rojo, y el nombre que ya usa la
    # suite sellada `test_comparar_verdad.py` es el pelado.
    sys.path.insert(0, str(RAIZ / "scripts"))
    sys.path.insert(0, str(RAIZ / "src"))
    from comparar_verdad import _tabla_de, comparar

    coinciden: set[str] = set()
    fallan: dict[str, list[str]] = {}
    for f in sorted((RAIZ / "runs" / "l4" / "fixtures").glob("*.json")):
        fx = json.loads(f.read_text(encoding="utf-8"))
        try:
            with _trazando():
                tabla, en_la_verdad = _tabla_de(fx)
            ds = [_clave(d.clase, d.detalle) for d in comparar(fx, tabla)]
            if not en_la_verdad:
                ds.append("SIN_VERDAD@-")
        except Exception as e:  # el instrumento también lo nota si revienta
            ds = [f"EXCEPCION@{type(e).__name__}"]
        if ds:
            fallan[f.stem] = ds
        else:
            coinciden.add(f.stem)
    return coinciden, fallan


ALCANZADO = [False]
FICHERO_DEL_MUTANTE = [""]


@contextmanager
def _trazando() -> Iterator[None]:
    """Traza **sólo la DERIVACIÓN**, no la comparación.

    La primera versión trazaba las 30 comparaciones enteras, y por eso daba
    `alcanzado: sí` a los mutantes del normalizador: la función del mutante la
    llamaba **el comparador**, que importa `normalize_cell_text` del paquete. El
    sujeto medido es `truth.derived` y lo que cuelga de él; que el mutante toque el
    instrumento no es alcance, es contaminación.
    """

    def traza(marco: object, evento: str, _arg: object) -> None:
        codigo = getattr(marco, "f_code", None)
        if evento == "call" and getattr(codigo, "co_filename", "") == FICHERO_DEL_MUTANTE[0]:
            ALCANZADO[0] = True

    sys.settrace(traza)
    try:
        yield
    finally:
        sys.settrace(None)


def _hijo(mutante: str) -> int:
    """Aplica el mutante, corre las 30 y escribe el resultado en JSON."""
    sys.path.insert(0, str(MUTANTES))
    modulo = importlib.import_module(mutante)
    if hasattr(modulo, "pytest_configure"):
        modulo.pytest_configure(None)

    FICHERO_DEL_MUTANTE[0] = str(MUTANTES / f"{mutante}.py")
    alcanzado = ALCANZADO

    coinciden, fallan = _comparar_las_30()
    print(
        json.dumps(
            {
                "mutante": mutante,
                "coinciden": sorted(coinciden),
                "fallan": fallan,
                "alcanzado": alcanzado[0],
            }
        )
    )
    return 0


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--hijo")
    partes.add_argument("--solo", default="")
    partes.add_argument("--detalle", action="store_true")
    args = partes.parse_args()
    if args.hijo:
        return _hijo(args.hijo)

    base_coinciden, base_fallan = _comparar_las_30()
    print(f"\n  SIN MUTAR: {len(base_coinciden)} de 30 coinciden · el control negativo")
    print(f"  las {len(base_fallan)} que no: todas de FRONTERA, adjudicadas y no corregidas\n")
    print(f"  {'mutante':<30}{'mata':>6}{'de':>4}{'cambia':>8}{'alcanzado':>11}   qué es")

    huecos: list[str] = []
    fuera: list[str] = []
    no_medidos: list[str] = []
    equivalentes: list[str] = []
    tabla: list[dict[str, object]] = []
    for mutante in _los_mutantes():
        if args.solo and mutante != args.solo:
            continue
        salida = subprocess.run(
            ["uv", "run", "python", str(Path(__file__)), "--hijo", mutante],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
        linea = salida.stdout.strip().splitlines()[-1] if salida.stdout.strip() else ""
        if not linea.startswith("{"):
            # Un mutante que sólo arranca dentro de pytest —porque su
            # `pytest_configure` importa `conftest`— NO es un cero: es una
            # medición que no se hizo. Se dice, no se cuenta como superviviente.
            razon = "requiere pytest" if "conftest" in salida.stderr else "no arranca"
            print(f"  {mutante:<30}{'—':>6}{'':>4}{'':>8}{'':>11}   NO MEDIDO: {razon}")
            no_medidos.append(mutante)
            continue
        r = json.loads(linea)
        muertos = sorted(base_coinciden - set(r["coinciden"]))
        cambian = sorted(
            n
            for n in set(base_fallan) | set(r["fallan"])
            if base_fallan.get(n, []) != r["fallan"].get(n, [])
        )
        resucitados = sorted(set(r["coinciden"]) - base_coinciden)
        equivalente = mutante in EQUIVALENTES
        alcanzado = "sí" if r["alcanzado"] else "no"
        if len(cambian) == 0 and equivalente:
            que_es = "EQUIVALENTE: no cambia la salida"
            equivalentes.append(mutante)
        elif len(cambian) == 0 and r["alcanzado"]:
            que_es = "HUECO DEL INSTRUMENTO"
            huecos.append(mutante)
        elif len(cambian) == 0:
            que_es = "fuera de este camino"
            fuera.append(mutante)
        else:
            que_es = ""
        marca = f"{len(muertos):>6}{len(base_coinciden):>4}{len(cambian):>8}"
        print(f"  {mutante:<30}{marca}{alcanzado:>11}   {que_es}")
        tabla.append(
            {
                "mutante": mutante,
                "mata": len(muertos),
                "de": len(base_coinciden),
                "cambia": len(cambian),
                "alcanzado": alcanzado,
                "que_es": que_es or "el instrumento lo ve",
                "muertos": muertos,
            }
        )
        if resucitados:
            print(f"{'':<32}RESUCITA {len(resucitados)}: {resucitados}")
        if args.detalle and cambian:
            for n in cambian:
                print(f"{'':<32}† {n}")
                for d in r["fallan"].get(n, ["(deja de fallar)"])[:2]:
                    print(f"{'':<34}{d[:120]}")

    if not args.solo:
        (RAIZ / "runs" / "l4" / "mutantes.json").write_text(
            json.dumps(
                {
                    "esquema": "docbench-es.mutantes-del-instrumento/1",
                    "comando": "uv run python scripts/mutar_el_instrumento.py",
                    "base_coinciden": len(base_coinciden),
                    "de": 30,
                    "no_medidos": no_medidos,
                    "huecos": huecos,
                    "equivalentes": {m: EQUIVALENTES[m] for m in equivalentes},
                    "fuera_de_este_camino": fuera,
                    "tabla": tabla,
                },
                indent=1,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    if no_medidos:
        print(f"\n  NO MEDIDOS ({len(no_medidos)}): {no_medidos}. No cuentan como cero.")
    if equivalentes:
        print(f"\n  EQUIVALENTES ({len(equivalentes)}): {equivalentes}. No son huecos.")
    print(f"\n  fuera de este camino ({len(fuera)}): {fuera}")
    if huecos:
        print(f"\n  HUECOS MEDIDOS DEL INSTRUMENTO ({len(huecos)}): {huecos}")
        print("  Se ejecutan y no los ve nadie. Van a LIMITS.md con su nombre.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
