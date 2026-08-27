"""EL RELOJ DE LAS DURACIONES. **Uno solo, y lo llaman los tres instrumentos.**

    python3 scripts/reloj.py     -> milisegundos de CLOCK_MONOTONIC

La puerta la cronometran TRES sitios: `medir_puerta.py` para la serie que se publica, el
hook `registrar-puerta.sh` para el aro que decide si se puede commitear, y `fast.yml` en
CI. Antes eran tres relojes distintos, y luego fueron tres LECTURAS distintas del mismo
tipo de reloj. Las dos cosas están mal por la misma razón que no se copió la huella del
árbol: **crea dos definiciones de la misma magnitud que se van por su lado.** Aquí hay
una definición y tres llamantes.

## Por qué CLOCK_MONOTONIC y no /proc/uptime, que es lo que había aquí un rato

`/proc/uptime` **es BOOTTIME**: `fs/proc/uptime.c` lo saca de `ktime_get_boottime_ts64()`,
y boottime **cuenta el tiempo suspendido**; CLOCK_MONOTONIC **se para** durante la
suspensión (docs.kernel.org/core-api/timekeeping.html). O sea que en una máquina que se
suspenda de verdad —un portátil cerrando la tapa a mitad de `make fast`— `/proc/uptime`
metería las horas de la tapa cerrada dentro de la duración de la puerta, y el aro
registraría una regresión que no existe. CLOCK_MONOTONIC no.

**Y en la máquina donde se descubrió esto NO habría fallado, que es lo que lo hace
peligroso.** Medido el 27 ago 2026 en WSL2: `BOOTTIME - MONOTONIC = 0,000 s` con
**41.028 s (11,40 h)** de reloj de pared que la VM no contó en NINGÚN reloj. El anfitrión
**congela la VM entera**: el kernel invitado no se ejecuta, así que no avanza ningún reloj
y tampoco recorre su ruta de suspensión, que es lo que boottime necesita para contarla.
Los tres relojes coincidían POR UN ACCIDENTE DE PLATAFORMA, que es la peor clase de
coincidencia: la que hace pasar los tests en la máquina del que escribe.

## Lo que esto SÍ y NO mide, dicho para que nadie lo "arregle" luego

Mide **tiempo de máquina disponible**, no tiempo de calendario. Si la VM se congela 164 s
en mitad de una corrida, esos 164 s NO entran. Es deliberado y es lo que quiere un techo
de rendimiento: una pausa del anfitrión no es la puerta poniéndose lenta.

Y el coste: **unos 20 ms de arranque de Python por medida**, sobre una puerta de ~7 s. Es
un 0,3%, se paga dos veces por corrida y **no se optimiza**: el día que alguien lo cambie
por un `date` o un `/proc/uptime` «que es más rápido», vuelven las tres definiciones.

## La letra pequeña que hace que el hook funcione

En Linux `time.monotonic()` es `clock_gettime(CLOCK_MONOTONIC)`, que es **de sistema, no
de proceso**. Por eso `--empieza` y `--acaba`, que son dos procesos distintos, pueden
restar sus lecturas. Si algún día esto corre donde el monotónico sea por proceso, la resta
deja de significar nada — y el guardián de `t0 > ahora` no lo cazaría, porque un valor por
proceso también es pequeño y creciente.
"""

from __future__ import annotations

import time

__all__ = ["ms"]


def ms() -> int:
    """Milisegundos de `CLOCK_MONOTONIC`. Enteros, porque la puerta se publica en ms."""
    return int(time.monotonic() * 1000)


if __name__ == "__main__":
    print(ms())
