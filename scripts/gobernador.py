"""Correr UNA unidad de cómputo con la temperatura acotada por medición.

## Qué controla, y qué no

Controla **la carga**, que es la única causa de calor que este proceso puede tocar:

* **hilos**: fija `OMP/MKL/OPENBLAS/TORCH_NUM_THREADS` en el entorno del hijo, ANTES
  de que arranque. *torch* los lee al cargarse; ponerlos después no hace nada.
* **prioridad**: el hijo entero va con `nice -n 19`.
* **pausa dura**: mientras el hijo corre, mide cada `INTERVALO` segundos. Si pasa del
  techo, **para el grupo de procesos con `SIGSTOP`** y lo reanuda con `SIGCONT` al
  bajar de la marca de reanudación. No aborta: espera, y lo dice.

**Si no hay termómetro no hay pausa dura**, y esta función lo declara en el registro
que devuelve (`vigilado: false`). No se afirma un grado que no se ha leído.

## Por qué el tiempo se mide con `wait4` y no con un cronómetro

`os.wait4` devuelve el `rusage` del hijo: `ru_utime + ru_stime` son **segundos de CPU
reales**, y no los altera que el gobernador lo pare a mitad. El reloj sí — por eso el
registro lleva `pausado_s` y `trabajo_s = reloj - pausado` al lado.

**Y hacen falta las dos, porque contestan preguntas distintas**: los segundos de CPU
dicen *cuánto cómputo consume* —la pregunta de la factura en la nube—, y son
invariantes al número de hilos; el reloj dice *si termina esta noche*, que es la
pregunta de B5-bis, y depende de los hilos. El puente entre ellas es
`hilos_efectivos = cpu_s / trabajo_s`, **medido** por unidad. Ver `runs/l5/termica.yaml`.
"""

from __future__ import annotations

import json
import os
import signal
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from termometro import Lectura, leer

RAIZ = Path(__file__).resolve().parents[1]
# Dos ritmos distintos, y separarlos importa:
#   LATIDO  es cada cuánto se mira si el hijo ha terminado. Marca el SUELO del reloj
#           de cada unidad, así que tiene que ser pequeño: con un solo bucle de 2 s,
#           una unidad de 0,2 s de CPU se publicaba como 2,1 s de reloj.
#   INTERVALO es cada cuánto se lee el termómetro, que cuesta un `reg.exe` (~50 ms).
#           Es la RESOLUCIÓN DEL GOBERNADOR: entre dos lecturas, no se sabe nada.
LATIDO = 0.1
INTERVALO = 2.0

Registro = dict[str, object]

_HILOS = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "TORCH_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


@dataclass
class Termica:
    """El sobre térmico. Declarado en `runs/l5/termica.yaml` ANTES de medir."""

    hilos: int
    techo: float
    reanudar: float
    objetivo_media: float
    vigilado: bool


@dataclass
class Muestreo:
    """Las lecturas tomadas durante un tramo, con su n y su rango."""

    grados: list[float] = field(default_factory=list)

    def anota(self, lectura: Lectura) -> None:
        if lectura.grados is not None:
            self.grados.append(lectura.grados)

    def resumen(self) -> Registro:
        if not self.grados:
            return {"n": 0}
        return {
            "n": len(self.grados),
            "max": round(max(self.grados), 1),
            "media": round(statistics.fmean(self.grados), 1),
            "min": round(min(self.grados), 1),
        }


def entorno(hilos: int) -> dict[str, str]:
    """El entorno del hijo, con los hilos fijados antes de que cargue nada."""
    fuera = dict(os.environ)
    fuera.update({v: str(hilos) for v in _HILOS})
    fuera["TOKENIZERS_PARALLELISM"] = "false"
    return fuera


def correr(
    extractor: str, ident: str, t: Termica, muestreo: Muestreo, tope_s: float = 0.0
) -> Registro:
    """Una unidad, bajo control térmico. Devuelve su registro completo.

    Si `tope_s` es positivo y el trabajo EFECTIVO —reloj menos pausado— lo pasa, el
    grupo se mata y la unidad queda **censurada por la derecha**: su `cpu_s` es una
    cota inferior, no una medida, y quien la publique tiene que decirlo.
    """
    salida = RAIZ / "runs" / "l5" / ".unidad.json"
    # stderr NO se tira: docling y camelot escriben ahí sus avisos, y un fallo cuya
    # causa se pierde es un error tragado. Se guarda a fichero —no a una tubería—
    # porque el padre no lee mientras el hijo corre y una tubería llena lo colgaría.
    error = RAIZ / "runs" / "l5" / ".unidad.err"
    salida.parent.mkdir(parents=True, exist_ok=True)
    orden = [
        "nice",
        "-n",
        "19",
        sys.executable,
        str(RAIZ / "scripts" / "unidad_computo.py"),
        extractor,
        ident,
    ]
    t0 = time.perf_counter()
    with salida.open("w") as fs, error.open("w") as fe:
        p = subprocess.Popen(
            orden, stdout=fs, stderr=fe, env=entorno(t.hilos), start_new_session=True
        )
        pausas, pausado, desde = 0, 0.0, 0.0
        parado = censurada = False
        proxima = 0.0
        while True:
            pid, estado, ru = os.wait4(p.pid, os.WNOHANG)
            if pid == p.pid:
                break
            ahora = time.perf_counter()
            lectura = leer() if ahora >= proxima else Lectura(None, "", "entre lecturas")
            if ahora >= proxima:
                proxima = ahora + INTERVALO
                muestreo.anota(lectura)
            if t.vigilado and lectura.grados is not None:
                if not parado and lectura.grados >= t.techo:
                    os.killpg(os.getpgid(p.pid), signal.SIGSTOP)
                    parado, pausas, desde = True, pausas + 1, time.perf_counter()
                    print(
                        f"      ‖ {lectura.grados:.1f} °C ≥ techo {t.techo:.0f} · "
                        f"parado, espera a {t.reanudar:.0f}",
                        flush=True,
                    )
                elif parado and lectura.grados <= t.reanudar:
                    os.killpg(os.getpgid(p.pid), signal.SIGCONT)
                    parado = False
                    pausado += time.perf_counter() - desde
                    print(
                        f"      ▸ {lectura.grados:.1f} °C · reanudado tras "
                        f"{time.perf_counter() - desde:.0f} s",
                        flush=True,
                    )
            if tope_s and not parado and (time.perf_counter() - t0 - pausado) > tope_s:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                censurada = True
                print(f"      ✂ tope de {tope_s / 60:.0f} min · unidad CENSURADA", flush=True)
            time.sleep(LATIDO)
    reloj = time.perf_counter() - t0
    # TRABAJO EFECTIVO: el reloj menos lo que el gobernador tuvo parado el proceso. Es
    # el reloj que se publica, porque penalizar a un extractor por haber enfriado la
    # máquina sería medir la refrigeración y no el extractor.
    trabajo = max(reloj - pausado, 1e-9)
    p.returncode = os.waitstatus_to_exitcode(estado) if estado >= 0 else -1
    try:
        registro = json.loads(salida.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        registro = {"ok": False, "causa": "SALIDA_ILEGIBLE"}
    return {
        "extractor": extractor,
        "documento": ident,
        "cpu_s": round(ru.ru_utime + ru.ru_stime, 3),
        "reloj_s": round(reloj, 3),
        "trabajo_s": round(trabajo, 3),
        "pausado_s": round(pausado, 1),
        # EL PUENTE ENTRE LAS DOS MONEDAS, y es MEDIDO y no configurado: `pdfplumber`
        # es monohilo y `docling` no, así que el paralelismo que consigue cada uno es
        # distinto y sólo esto permite reescalar el reloj a otro número de trabajadores.
        #     reloj ~ segundos de CPU / hilos efectivos
        "hilos_efectivos": round((ru.ru_utime + ru.ru_stime) / trabajo, 3),
        "pausas": pausas,
        "max_rss_mb": round(ru.ru_maxrss / 1024, 1),
        "rc": p.returncode,
        "stderr": error.read_text(encoding="utf-8", errors="replace")[-400:].strip(),
        "censurada": censurada,
        **({"ok": False, "causa": "TOPE_MINUTOS"} if censurada else registro),
    }


def descansa(trabajo_s: float, factor: float, muestreo: Muestreo, tope: float = 180.0) -> float:
    """La pausa entre unidades: proporcional a lo que acaba de costar, con tope.

    **Se muestrea la temperatura también aquí.** La media de la sesión incluye los
    descansos; medirla sólo mientras se trabaja daría una media falsa por arriba.
    """
    pausa = min(trabajo_s * factor, tope)
    fin = time.perf_counter() + pausa
    while time.perf_counter() < fin:
        muestreo.anota(leer())
        time.sleep(min(INTERVALO, max(0.05, fin - time.perf_counter())))
    return pausa
