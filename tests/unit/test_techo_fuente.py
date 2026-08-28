"""LA FUENTE ÚNICA DEL TECHO, y que sus tres lectores digan lo mismo que ella.

Sale de `test_aro_del_techo.py` porque aquél pasó de 300 líneas, y la costura cae donde
tenía que caer: allí se prueba **el aro** —frío contra caliente, bloquea contra deja
pasar—, y aquí **de dónde sale el número** que el aro compara.

Y son dos cosas distintas de verdad, no una partición por tamaño: el aro funcionaba
perfectamente mientras el número que vigilaba llevaba un hito entero viejo. Ver LIMITS
111.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
REGISTRAR = RAIZ / ".claude" / "hooks" / "registrar-puerta.sh"
WORKFLOW = RAIZ / ".github" / "workflows" / "fast.yml"

sys.path.insert(0, str(RAIZ / "scripts"))

import medir_puerta  # noqa: E402


def _de_la_fuente(clave: str) -> int:
    """El techo tal y como lo lee cualquiera: de `.techos`, la fuente única."""
    casa = re.search(rf"^{clave}=(\d+)$", (RAIZ / ".techos").read_text(encoding="utf-8"), re.M)
    assert casa, f"`.techos` no declara {clave}"
    return int(casa.group(1))


def _techo_del_hook() -> int:
    """Lo que el hook USA, preguntándoselo. **No lo que dice su código.**

    Antes esto era un `re.search` de `^TECHO=(\\d+)$` sobre el texto del hook: una copia
    comparada contra otra copia. Ahora el hook lo lee de `.techos`, así que lo que hay
    que comprobar es que **lee bien**, y eso sólo lo dice ejecutarlo.
    """
    hecho = subprocess.run(
        [str(REGISTRAR), "--techo"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(RAIZ)},
    )
    salida = hecho.stdout.strip()
    assert salida.isdigit(), f"el hook no devuelve su techo: {hecho.stdout!r} {hecho.stderr!r}"
    return int(salida)


def _techo_del_instrumento() -> int:
    """Lo que `medir_puerta.py` USA, y de paso que no haya vuelto a teclearlo."""
    texto = (RAIZ / "scripts" / "medir_puerta.py").read_text(encoding="utf-8")
    assert not re.search(r'"--techo",\s*type=int,\s*default=\d', texto), (
        "medir_puerta.py ha vuelto a tener el techo TECLEADO en vez de leerlo de `.techos`"
    )
    return int(medir_puerta.techo_local())


def test_los_tres_lectores_del_techo_dan_lo_que_dice_la_fuente() -> None:
    """**Ya no se comparan copias entre sí: se comparan contra la fuente.**

    Esto ponía `_hook() == _instrumento() == 8500`, con el literal clavado. Comparaba dos
    copias entre ellas y fijaba el número a mano, así que sólo podía cazar que **una** se
    moviera. Lo que pasó fue lo otro: las dos se quedaron en 8500 mientras ADR-0022 fijaba
    9000 local para L4 —o sea que **se separaron juntas del ADR**— y este test siguió
    verde todo L5. Un test de dos copias protege contra que se separen; no contra que las
    dos estén viejas. Es la forma del límite 106, y ahora también la del 111.

    Sin literal a propósito: si el techo cambia, este test sigue valiendo sin que nadie
    tenga que acordarse de tocarlo. Lo que afirma es que **los tres leen lo mismo**.
    """
    fuente = _de_la_fuente("TECHO_LOCAL_MS")
    assert fuente > 0
    assert _techo_del_hook() == fuente, "el hook no está leyendo `.techos`"
    assert _techo_del_instrumento() == fuente, "medir_puerta.py no está leyendo `.techos`"
    # El tercero —el workflow de CI— tiene su propio test, porque lee la OTRA clave y
    # compararlo con ésta lo daría por roto. Hasta que se escribió, este test se llamaba
    # «los tres lectores» y comprobaba dos.


def test_el_techo_de_ci_tampoco_esta_tecleado_en_el_workflow() -> None:
    """**La cuarta copia, la que no miraba nadie.** `grep -r 21000 tests/ scripts/` daba
    cero: el techo de CI vivía sólo en `fast.yml`, escrito a mano, y ni un test ni una
    regla lo comparaba con nada.

    Se comprueba lo comprobable sin un runner: que el workflow **no lleva el número** y
    que **nombra la fuente**. Que el valor exportado sea el bueno se sigue de que lo lee
    del mismo fichero que los otros dos.
    """
    texto = WORKFLOW.read_text(encoding="utf-8")
    ci = _de_la_fuente("TECHO_CI_MS")
    assert not _lleva_el_numero(texto, ci), "el techo de CI ha vuelto a estar tecleado"
    assert ".techos" in texto, "el workflow no lee la fuente única del techo"


def test_el_workflow_de_ci_lee_la_clave_que_toca_y_no_otra() -> None:
    """**El tercer lector, EJECUTADO.** Los otros dos se comprueban corriéndolos; éste se
    comprobaba leyendo, y leer no distingue leer bien de leer la clave equivocada.

    Un workflow que hiciera `grep TECHO_LOCAL_MS` pasaría las dos aserciones del test de
    arriba —no lleva el número, nombra `.techos`— y pondría la alarma de CI en el techo
    LOCAL, o sea 2,5 veces más estricta de lo que ADR-0022 decide. Así que se extrae su
    línea del YAML y se ejecuta.
    """
    linea = next(
        (
            linea.strip()
            for linea in WORKFLOW.read_text(encoding="utf-8").splitlines()
            if "TECHO_MS=$(" in linea
        ),
        None,
    )
    assert linea, "el workflow ya no calcula TECHO_MS: la alarma de CI no tiene techo"
    hecho = subprocess.run(
        ["bash", "-c", f'{linea}; echo "$TECHO_MS"'],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )
    assert hecho.stdout.strip() == str(_de_la_fuente("TECHO_CI_MS")), (
        f"el workflow lee otra cosa: {hecho.stdout!r} {hecho.stderr!r}"
    )


def _lleva_el_numero(texto: str, techo: int) -> bool:
    """Si un texto trae el techo TECLEADO. La comprobación, aparte de su sujeto.

    Está separada para poder verla en rojo: un test que sólo afirma «el workflow no lo
    lleva» pasaría igual con una función que devolviera `False` siempre, que es el
    `siempre_ok` de toda la vida.
    """
    return str(techo) in texto


def test_el_detector_del_numero_tecleado_dice_que_si_cuando_lo_hay() -> None:
    """**El control negativo de este fichero.** Sin él, «el workflow no lleva el número»
    lo cumpliría un detector que no mira nada — y ésa es la dirección tranquilizadora."""
    ci = _de_la_fuente("TECHO_CI_MS")
    assert _lleva_el_numero(f"        env:\n          TECHO_MS: {ci}\n", ci)
    assert not _lleva_el_numero("TECHO_MS=$(grep -E '^TECHO_CI_MS=' .techos | cut -d= -f2)", ci)
