"""Mide la puerta como manda ADR-0022: 40 corridas en frío, 10 tandas de 4.

Existe para que el protocolo de medición sea **una orden y no una costumbre**. La
diferencia importa: dos tandas de L2 dieron medianas de 5440 y 5473 con rangos que
no se solapaban del todo, así que el número depende de cuántas corridas y de si
se limpió la caché. Un protocolo que cada uno recuerda a su manera produce cifras
que no se pueden comparar entre hitos, y la serie de la puerta es justo una
comparación entre hitos.

    uv run python scripts/medir_puerta.py            # 10 tandas de 4
    uv run python scripts/medir_puerta.py        # el techo sale de `.techos`
    echo $?                                          # 1 si el p90 pasa del techo

**Comprueba el código de salida de cada corrida y descarta la que falla.** `make`
para en el primer paso que falla, así que una puerta rota da un tiempo MENOR: sin
esta comprobación, un fallo se publicaría como una mejora. Pasó en L1, con una
tanda entera de 60 ms que era `ruff` en rojo.

**Y ABORTA SI EL ÁRBOL SE MUEVE DURANTE LA SERIE.** Comprueba `HEAD` más
`git status --porcelain` antes de empezar y **después de cada corrida**: si algo
cambió, la serie **se descarta entera y no se imprime ni un tiempo**. Sale de un
fallo real de L3: 40 corridas con un docstring editado a mitad, o sea una parte de
la serie sobre un árbol y el resto sobre otro — y cuántas de cada, no se sabe.

Es la forma barata de la regla ancha: **ninguna medición corre mientras el árbol
se mueve.** Una regla que alguien tiene que recordar se olvida; ésta la comprueba
el propio instrumento, que además es quien sabe cuándo empieza y cuándo acaba.

No se imprimen los tiempos parciales a propósito. Mirar el p90 de una serie
contaminada **sesga la decisión siguiente** aunque luego se descarte: el número ya
está en la cabeza de quien decide.

**Lo que este script NO puede hacer**, y por eso ADR-0022 lo dice en voz alta: no
se ejecuta solo. El paso mecánico de verdad es el aviso de CI, que sale en cada
PR sin que nadie decida ejecutarlo. Y su guardia mira el árbol de `git`, así que
**no ve un cambio en algo que `git` no sigue** —un fichero ignorado, una variable
de entorno, otro proceso comiéndose la máquina—. Para eso está la columna de
`load average`, que tampoco lo cierra: lo declara.
"""

from __future__ import annotations

import argparse
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(RAIZ / "scripts"))
from reloj import ms  # noqa: E402
from sello import sello  # noqa: E402

CACHES = (
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".import_linter_cache",
    "htmlcov",
)


def _en_frio() -> None:
    """Borra TODAS las cachés, incluida `.hypothesis`.

    `.hypothesis` no es una caché de velocidad: guarda lo ya explorado, así que
    una corrida en caliente **busca menos**. Medir en frío es lo único que hace
    comparables dos corridas, y de paso es lo que destapó la regresión de U+2028.
    """
    for nombre in CACHES:
        shutil.rmtree(RAIZ / nombre, ignore_errors=True)
    (RAIZ / ".coverage").unlink(missing_ok=True)


def _carga() -> float:
    """`load average` de 1 minuto. Sale de la deuda que dejaron cinco tandas.

    La desviacion tipica de este mismo protocolo ha ido **134, 76, 286, 73 y 359** entre tandas, y
    ninguna de esas variaciones se pudo explicar porque **nadie registró el estado
    de la máquina**. Sin esta columna, la respuesta a «¿por qué se movió?» es
    siempre «no se sabe», y eso ya se ha escrito cuatro veces.
    """
    try:
        return os.getloadavg()[0]
    except OSError:
        return float("nan")


def _huella_arbol(raiz: Path = RAIZ) -> str:
    """`HEAD` + todo lo que `git status` ve sin commitear, incluidos los sin seguir.

    `--porcelain` es el formato estable —`--short` no lo es— y trae los `??`, que
    es justo donde vive un fichero recién creado: el caso del hito que estrena
    módulos. Las cachés que este script borra no salen porque están en
    `.gitignore`; si algún día una dejara de estarlo, la serie abortaría siempre y
    el aviso diría cuál.
    """

    def _git(*orden: str) -> str:
        return subprocess.run(
            ["git", *orden], cwd=raiz, capture_output=True, text=True, check=False
        ).stdout

    return _git("rev-parse", "HEAD").strip() + "\n" + _git("status", "--porcelain")


def _lo_que_se_movio(antes: str, ahora: str) -> str:
    """Las líneas que aparecen en una huella y no en la otra, en las dos direcciones."""
    a, b = set(antes.splitlines()), set(ahora.splitlines())
    fuera = [f"    - {linea}" for linea in sorted(a - b)]
    dentro = [f"    + {linea}" for linea in sorted(b - a)]
    return "\n".join(fuera + dentro)


def _desviacion(muestras: list[int]) -> str:
    """La desviación típica, o «n/a» con una sola muestra.

    `statistics.stdev` revienta con n=1, y `--por-tanda 1` es una invocación legal
    del propio script: no puede acabar en traza. Con una muestra la dispersión no
    es cero, es que **no se ha medido**, y eso se escribe.
    """
    return f"{statistics.stdev(muestras):.0f}" if len(muestras) > 1 else "n/a (n=1)"


def movimiento(antes: str, ahora: str, corrida: int, tanda: int) -> str | None:
    """El aviso si el árbol se movió, o `None` si no. **La decisión, sin el bucle.**

    Separada para que se pueda probar que dice «sí» y que dice «no» sin correr
    cuarenta veces `make fast`. Un guardia que sólo se ha visto funcionar una vez
    a mano está en el estado que el paso 4 de `/cerrar` llama insuficiente.
    """
    if antes == ahora:
        return None
    return (
        f"\nEL ÁRBOL SE MOVIÓ durante la corrida {corrida} (tanda {tanda}).\n"
        f"{_lo_que_se_movio(antes, ahora)}\n\n"
        "  La serie se DESCARTA ENTERA y no se imprime ningún tiempo: una parte se midió\n"
        "  sobre un árbol y el resto sobre otro. Deja el árbol quieto y vuelve a empezar."
    )


def techo_local() -> int:
    """El techo local, leído de `.techos`. **No hay un literal en este fichero.**

    Estaba tecleado aquí y en `.claude/hooks/registrar-puerta.sh`, y un test comparaba
    las dos copias entre sí. No se separaron entre ellas: se separaron **juntas** del ADR
    que las fija, y el test siguió verde. La fuente única lo cierra por el lado que
    faltaba; el porqué completo está escrito en el propio `.techos`.
    """
    for linea in (RAIZ / ".techos").read_text(encoding="utf-8").splitlines():
        if linea.startswith("TECHO_LOCAL_MS="):
            return int(linea.split("=", 1)[1].strip())
    raise RuntimeError("`.techos` no declara TECHO_LOCAL_MS: el instrumento no tiene techo")


def _una_corrida() -> tuple[int, int, float]:
    _en_frio()
    carga = _carga()
    inicio = ms()
    resultado = subprocess.run(
        ["make", "fast"], cwd=RAIZ, capture_output=True, text=True, check=False
    )
    return ms() - inicio, resultado.returncode, carga


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--tandas", type=int, default=10)
    partes.add_argument("--por-tanda", type=int, default=4)
    partes.add_argument(
        "--techo", type=int, default=techo_local(), help="techo local de ADR-0022, de `.techos`"
    )
    args = partes.parse_args()

    print(f"sello: {sello()}")
    huella = _huella_arbol()
    todas: list[int] = []
    cargas: list[float] = []
    medianas: list[float] = []
    descartadas = 0
    corrida = 0
    for tanda in range(1, args.tandas + 1):
        fila: list[int] = []
        for _ in range(args.por_tanda):
            ms, rc, carga = _una_corrida()
            corrida += 1
            aviso = movimiento(huella, _huella_arbol(), corrida, tanda)
            if aviso is not None:
                print(aviso)
                return 2
            cargas.append(carga)
            if rc == 0:
                fila.append(ms)
                todas.append(ms)
            else:
                descartadas += 1
        if fila:
            medianas.append(statistics.median(fila))
        print(f"  tanda {tanda:>2}: {fila}")

    if not todas:
        print("NINGUNA corrida en verde: no hay medición, no hay número.")
        return 1

    ordenadas = sorted(todas)
    p90 = ordenadas[min(len(ordenadas) - 1, int(0.90 * len(ordenadas)))]
    print(
        f"\n  n={len(todas)} en verde · descartadas por rc!=0: {descartadas}\n"
        f"  mínimo {ordenadas[0]} · mediana {statistics.median(ordenadas):.0f} · "
        f"p90 {p90} · máximo {ordenadas[-1]}\n"
        f"  desviación típica {_desviacion(ordenadas)} · "
        f"medianas por tanda {int(min(medianas))}-{int(max(medianas))}\n"
        f"  carga de la máquina: mediana {statistics.median(cargas):.2f} · "
        f"rango {min(cargas):.2f} a {max(cargas):.2f}\n"
        f"  techo {args.techo} · margen en el p90: {args.techo - p90} ms"
    )
    if p90 > args.techo:
        print("EL P90 PASA DEL TECHO. Ver ADR-0022: re-justificar o reestructurar.")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
