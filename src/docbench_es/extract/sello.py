"""Sobre QUÉ ÁRBOL y QUÉ MÁQUINA se midió. **Se escribe antes de medir, no después.**

Una corrida de cuatro horas se cae. Cuando se cae, lo que queda en disco tiene que poder
contestar *«¿de qué árbol venía esto?»* — y si el sello se escribiera al terminar, la
respuesta de una corrida interrumpida sería el silencio, que es indistinguible de una
corrida sobre un árbol que ya nadie tiene.

## Qué lleva, y por qué cada campo

* **`commit` + `sucios`** — una medición sobre un árbol sucio **no es reproducible desde
  ningún commit**, y quien la lea tiene derecho a saberlo antes de comparar con la suya.
* **`cpus` y `carga`** — condición de máquina, declarada. Una cifra de reloj tomada con 8
  CPU y comparada con una tomada con 28 es una comparación **entre máquinas distintas**,
  aunque el hardware sea el mismo.
* **`entradas`** — el `sha256` de cada fichero de entrada. Dos corridas del mismo commit
  sobre poblaciones distintas no son la misma corrida.
* **`empezada`** — cuándo. Lo único que se puede saber al arrancar, y por eso lo único
  que este sello promete.

**No lleva `n_tests`.** Contarlos exige colectar la suite, y una campaña no puede pagar
eso ni fingir que lo sabe. Ese recuento es del sello de los DOCUMENTOS, que es otro
trabajo: `scripts/sello.py`.

## Por qué vive aquí y no en `core`

Porque toca el mundo: `git`, el reloj, la carga de la máquina. El contrato de capas dice
que **el núcleo es puro**, así que un `subprocess` en `core` rompería la promesa de que se
puede reejecutar sobre extracciones viejas sin nada alrededor. `scripts/sello.py` importa
de aquí lo que comparten, para que «qué árbol es éste» tenga una sola implementación.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

__all__ = ["arbol", "carga", "cpus_visibles", "git", "sello_de_corrida"]

RAIZ = Path(__file__).resolve().parents[3]


def git(*orden: str, cwd: Path | None = None) -> str:
    """La salida de `git`, y **`?` si git falla**, nunca cadena vacía.

    Con `check=False` y sin mirar el código, un `git status` que reventara devolvía `""`,
    que se cuenta como cero ficheros sucios: **un árbol sucio con cara de limpio**, que es
    justo lo que el sello existe para no dejar pasar.
    """
    hecho = subprocess.run(
        ["git", *orden], cwd=cwd or RAIZ, capture_output=True, text=True, check=False
    )
    return hecho.stdout.strip() if hecho.returncode == 0 else "?"


def cpus_visibles() -> int:
    """Cuántas CPU lógicas ve ESTE proceso. **Condición de máquina, como la carga.**

    No es una propiedad del hardware sino de cómo está configurado: en WSL2 lo fija
    `processors` en `.wslconfig`, y el 2026-08-25 valía 8 con 32 lógicos en el anfitrión.
    """
    return os.cpu_count() or 0


def modelo_de_cpu() -> str:
    """El modelo de CPU, de `/proc/cpuinfo`. **Se declara porque el coste es tiempo.**

    Un coste por página de una herramienta local sin la máquina al lado no es un número:
    es un número de esta máquina presentado como si fuera de cualquiera. Entró al sello el
    27 ago 2026, así que **las corridas anteriores no lo traen** — y el informe lo dice en
    vez de leerlo de la máquina que informa, que puede no ser la que corrió.
    """
    try:
        for linea in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if linea.startswith("model name"):
                return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    return "(desconocido)"


def carga() -> float:
    """El `load average` de un minuto. Se declara porque **se midió que importa**."""
    return round(os.getloadavg()[0], 2)


def arbol(cwd: Path | None = None) -> dict[str, str | int]:
    """`commit`, cuántos ficheros sin commitear, **y la huella de lo que cambia**.

    El commit solo engaña sobre un árbol sucio, y el recuento de sucios engaña más fino:
    editar un fichero que ya estaba sucio **no mueve el número**, así que dos corridas
    sobre código distinto tendrían el mismo sello. `huella` cierra ese hueco con el
    `sha256` de `status --porcelain` más `diff HEAD`.

    **Lo que la huella NO cubre**: el CONTENIDO de un fichero sin seguir. `git diff` no lo
    ve; `--porcelain` sí ve su nombre, así que un fichero nuevo se nota al aparecer y sus
    ediciones posteriores no. Es el mismo límite que `stop-gate.sh` tiene con el fixture
    recién creado, y va en LIMITS 101.
    """
    estado = git("status", "--porcelain", cwd=cwd)
    cambios = git("diff", "HEAD", cwd=cwd)
    return {
        "commit": git("rev-parse", "--short", "HEAD", cwd=cwd) or "(sin HEAD)",
        "sucios": -1 if estado == "?" else len([x for x in estado.splitlines() if x]),
        "huella": hashlib.sha256((estado + "\n" + cambios).encode()).hexdigest()[:16],
    }


def sucios(cwd: Path | None = None) -> tuple[str, ...]:
    """Los ficheros que `git status --porcelain` ve movidos, **por nombre**.

    No entra en el sello: entra en el MENSAJE del guardián que rechaza reanudar. Bloquear
    con «el árbol cambió» obliga a investigar o a sortear el guardián; bloquear con la
    lista delante es accionable. Es la misma lección que la carga en el aro del techo:
    **sigue bloqueando igual, sólo dice dónde mirar.**

    Y por eso NO decide nada: el guardián compara el árbol entero a propósito. Estrecharlo
    a «la ruta de extracción» sería un guardián que se fía de su propio criterio sobre qué
    importa, y así es como se acaba protegiendo cero ficheros.
    """
    estado = git("status", "--porcelain", cwd=cwd)
    if estado == "?":
        return ("(git no contestó)",)
    return tuple(linea[3:] for linea in estado.splitlines() if linea)


def _huella(ruta: Path) -> str:
    if not ruta.exists():
        return "(no existe)"
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def sello_de_corrida(
    que: str, entradas: dict[str, Path], extra: dict[str, str | int | float] | None = None
) -> dict[str, object]:
    """El sello entero, listo para escribir a disco **antes de la primera unidad**."""
    return {
        "que": que,
        "empezada": datetime.now(tz=UTC).isoformat(),
        **arbol(),
        "cpus": cpus_visibles(),
        "cpu": modelo_de_cpu(),
        "carga": carga(),
        "entradas": {
            nombre: {"ruta": str(r), "sha256": _huella(r)} for nombre, r in entradas.items()
        },
        **(extra or {}),
    }
