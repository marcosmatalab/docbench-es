"""La temperatura de la CPU, leída de HWiNFO64 a través del registro de Windows.

## Por qué el registro y no `/sys`

Esto corre en **WSL2**, que es una máquina virtual: `/sys/class/thermal/*/temp` está
vacío, `lm-sensors` no ve nada y `MSAcpi_ThermalZoneTemperature` no devuelve nada en
este equipo. **Comprobado, no supuesto.** La única fuente real es el anfitrión.

HWiNFO64 publica el valor de cualquier sensor en `HKCU\\Software\\HWiNFO64\\VSB`
cuando se le marca **«Add to Registry»** sobre esa fila. Sin ese clic la clave **no
existe**, y este módulo devuelve `None` con su motivo escrito: no se inventa un grado.

    uv run python scripts/termometro.py        # imprime la lectura o por qué no hay
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass

CLAVE = r"HKCU\Software\HWiNFO64\VSB"

# El sensor que se busca, por orden de preferencia. En Ryzen, `Tctl/Tdie` es EL que
# gobierna el boost y el corte térmico: es el que hay que vigilar, no el del socket.
PREFERIDOS = ("tctl", "tdie", "cpu package", "core (tctl", "cpu (tctl")

_FILA = re.compile(r"^\s{2,}([A-Za-z]+?)(\d+)\s+REG_SZ\s+(.*?)\s*$")


@dataclass(frozen=True)
class Lectura:
    """Un grado con su procedencia, o la ausencia de grado con su motivo."""

    grados: float | None
    etiqueta: str
    motivo: str

    def __bool__(self) -> bool:
        return self.grados is not None


def _volcado() -> tuple[str, str]:
    """El contenido de la clave VSB, o el motivo por el que no se pudo leer."""
    exe = shutil.which("reg.exe") or "/mnt/c/Windows/System32/reg.exe"
    try:
        p = subprocess.run([exe, "query", CLAVE], capture_output=True, timeout=10, check=False)
    except FileNotFoundError:
        return "", "no hay reg.exe: esto no corre sobre Windows"
    except subprocess.TimeoutExpired:
        return "", "reg.exe no respondió en 10 s"
    if p.returncode != 0:
        return "", (
            f"la clave {CLAVE} no existe: HWiNFO no está publicando ningún sensor. "
            "Clic derecho sobre «CPU (Tctl/Tdie)» → «Add to Registry»"
        )
    # reg.exe escribe en la página de códigos de la consola; los ValueRaw son dígitos
    # ASCII, así que un byte mal decodificado en una etiqueta no estropea la lectura.
    return p.stdout.decode("utf-8", errors="replace"), ""


def _sensores(volcado: str) -> dict[str, dict[str, str]]:
    """Las filas `Label3`/`ValueRaw3` reagrupadas por su índice."""
    fuera: dict[str, dict[str, str]] = {}
    for linea in volcado.splitlines():
        m = _FILA.match(linea)
        if m:
            campo, indice, valor = m.group(1), m.group(2), m.group(3)
            fuera.setdefault(indice, {})[campo.lower()] = valor
    return fuera


def leer() -> Lectura:
    """La temperatura de la CPU ahora mismo, o el motivo por el que no hay."""
    volcado, motivo = _volcado()
    if motivo:
        return Lectura(None, "", motivo)
    sensores = _sensores(volcado)
    if not sensores:
        return Lectura(None, "", f"{CLAVE} existe pero está vacía")
    candidatos = []
    for datos in sensores.values():
        etiqueta = datos.get("label", "")
        crudo = datos.get("valueraw", "")
        try:
            grados = float(crudo.replace(",", "."))
        except ValueError:
            continue
        bajo = etiqueta.lower()
        for orden, aguja in enumerate(PREFERIDOS):
            if aguja in bajo:
                candidatos.append((orden, grados, etiqueta))
                break
    if not candidatos:
        etiquetas = ", ".join(sorted({d.get("label", "?") for d in sensores.values()})) or "?"
        return Lectura(
            None,
            "",
            f"HWiNFO publica {len(sensores)} sensor(es) pero ninguno es la temperatura "
            f"de la CPU. Publicados: {etiquetas}",
        )
    candidatos.sort()
    _, grados, etiqueta = candidatos[0]
    # Un sensor puede publicarse y devolver 0 si HWiNFO se ha quedado sin refrescar.
    if not 0.0 < grados < 130.0:
        return Lectura(None, etiqueta, f"«{etiqueta}» devolvió {grados}, fuera de rango")
    return Lectura(grados, etiqueta, "")


def main() -> int:
    lectura = leer()
    if lectura:
        print(f"  {lectura.etiqueta}: {lectura.grados:.1f} °C")
        return 0
    print(f"  SIN TERMÓMETRO · {lectura.motivo}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
