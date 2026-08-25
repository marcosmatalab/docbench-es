"""Los dos hooks publican CUÁNTO protegen, y aquí se afirma que no es cero.

## La clase de fallo que este fichero existe para cerrar

> **UNA PROTECCIÓN QUE NO DICE CUÁNTO PROTEGE ES INDISTINGUIBLE DE NO PROTEGER NADA.**

Es el modo de fallo **por defecto** de cualquier guardián basado en patrones: el glob
no casa, el guardián **no se queja** —no tiene de qué— y su verde significa *«no hay
nada que vigilar»* en vez de *«todo está bien»*. Las dos cosas se leen igual desde
fuera, y la primera es un agujero.

**Pasó en este repo, en el cierre de L4.** `stop-gate.sh` llevaba
`GLOBS=(… 'runs/*/fixtures')`, que como pathspec de git casa con el **directorio** y
no con lo que hay dentro: protegía **cero** ficheros mientras `LIMITS.md` publicaba
*«arreglado en los dos hooks»*. Nada lo delató; lo encontró un escrutinio.

## El arreglo, y son dos mitades

1. **Cada guardián publica su conjunto**: `--cuantos` lista los ficheros que protege
   ahora mismo, calculado con los mismos patrones que usa para decidir.
2. **Y un test afirma que ese número es > 0 y que la lista casa con lo esperado.**
   El recuento solo no arregla nada — nadie lo mira. Esta es la mitad que lo hace
   cumplir, y por eso está en la puerta.

Con su control negativo: **si el glob se rompe, el test se cae nombrando el patrón.**

## Por qué se comprueba el COMPORTAMIENTO y no el texto del script

Los dos hooks usan sintaxis distinta —pathspec de git en uno, `case` de shell en el
otro— así que comparar sus cadenas no diría nada. Lo que se compara es **el conjunto
de ficheros que cada uno protege de verdad**, que es lo único que importa y lo único
que se rompe igual en las dos sintaxis.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / ".claude" / "hooks"

LOS_DOS = ["stop-gate.sh", "guard-frozen.sh"]


def _protegidos(hook: Path) -> set[str]:
    """Lo que el hook dice que protege AHORA MISMO."""
    hecho = subprocess.run(
        ["bash", str(hook), "--cuantos"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(RAIZ)},
        check=True,
    )
    return {linea for linea in hecho.stdout.splitlines() if linea.strip()}


@pytest.mark.parametrize("nombre", LOS_DOS)
def test_cada_hook_protege_mas_de_cero_ficheros(nombre: str) -> None:
    """**El candado de la clase.** Cero protegidos es el fallo silencioso."""
    protegidos = _protegidos(HOOKS / nombre)

    assert protegidos, (
        f"`{nombre}` protege CERO ficheros. Su glob no casa con nada, así que su"
        " silencio significa «no hay nada que vigilar», no «todo está bien»"
    )


@pytest.mark.parametrize("nombre", LOS_DOS)
def test_cada_hook_protege_lo_que_tiene_que_proteger(nombre: str) -> None:
    """Un número > 0 tampoco basta: puede proteger otra cosa. Se nombra el conjunto.

    Si mañana se añade una familia de congelados y nadie toca este test, esto sigue
    verde — por eso la lista se deriva del **disco**, no de una constante: los 30
    fixtures son «los que hay», no «los 30 que escribí aquí».
    """
    protegidos = _protegidos(HOOKS / nombre)
    obligatorios = {
        *(f"runs/l4/fixtures/{f.name}" for f in (RAIZ / "runs/l4/fixtures").glob("*.json")),
        "runs/l4/congelacion.json",
        "runs/l4/congelacion_comparador.json",
        "runs/l4/correcciones.json",
        "runs/l4/recongelacion.json",
        "runs/l3/plan.yaml",
        "runs/l4/plan.yaml",
        *(
            f"tests/fixtures/pubtabnet/{f.name}"
            for f in (RAIZ / "tests/fixtures/pubtabnet").iterdir()
        ),
    }

    faltan = sorted(obligatorios - protegidos)

    assert not faltan, f"`{nombre}` NO protege {len(faltan)} ficheros que debería: {faltan[:5]}"


def test_el_recuento_que_publica_limits_sale_de_correr_los_hooks() -> None:
    """`LIMITS.md` 77 dice «hoy los dos protegen 41». Que lo diga un comando.

    Es la regla de oro 2 aplicada a un recuento: si no se puede reproducir, no
    existe. Y como el número cambia al añadir un congelado, esto se cae y obliga a
    actualizarlo — que es justo lo que se quiere.
    """
    limits = (RAIZ / "LIMITS.md").read_text(encoding="utf-8")
    protegidos = _protegidos(HOOKS / "stop-gate.sh")

    assert f"protegen **{len(protegidos)}**" in limits, (
        f"los hooks protegen {len(protegidos)} ficheros y LIMITS 77 dice otra cosa"
    )


def test_los_dos_hooks_protegen_el_mismo_conjunto() -> None:
    """Prevención y detección tienen que cubrir lo mismo, o una de las dos miente.

    El límite 27 dice que son complementarios **en las VÍAS que cubren** —uno ve
    Write/Edit, el otro ve el resultado al cerrar el turno— no en el **conjunto de
    ficheros**. Si divergen ahí, hay una familia protegida sólo a medias y nadie lo
    sabría: es la misma clase de fallo que el glob que no casa.
    """
    solo_stop = _protegidos(HOOKS / "stop-gate.sh") - _protegidos(HOOKS / "guard-frozen.sh")
    solo_guard = _protegidos(HOOKS / "guard-frozen.sh") - _protegidos(HOOKS / "stop-gate.sh")

    assert not solo_stop, f"sólo `stop-gate` los ve: {sorted(solo_stop)}"
    assert not solo_guard, f"sólo `guard-frozen` los ve: {sorted(solo_guard)}"


@pytest.mark.parametrize(
    ("nombre", "roto", "arreglado"),
    [
        ("stop-gate.sh", "'runs/*/fixtures/*'", "'runs/*/fixtures'"),
        ("guard-frozen.sh", "*/runs/*/fixtures/*", "*/runs/*/fixtures"),
    ],
)
def test_si_el_glob_se_rompe_el_recuento_lo_delata(
    tmp_path: Path, nombre: str, roto: str, arreglado: str
) -> None:
    """**EL CONTROL NEGATIVO, y es exactamente el bug que ocurrió.**

    Se rompe el glob del mismo modo —quitándole la barra y el asterisco finales— y se
    exige que los 30 fixtures **desaparezcan** del conjunto protegido. Si no
    desaparecieran, este fichero entero estaría midiendo otra cosa.

    Los nombres van al revés en los parámetros a propósito: `roto` es el patrón BUENO
    que se sustituye, `arreglado` el estropeado. Se rompe una copia en `tmp_path`; los
    hooks del repo no se tocan.
    """
    copia = tmp_path / nombre
    shutil.copy(HOOKS / nombre, copia)
    texto = copia.read_text()
    assert roto in texto, f"el patrón {roto} ya no está en `{nombre}`: ¿cambió el glob?"
    copia.write_text(texto.replace(roto, arreglado))

    protegidos = _protegidos(copia)

    fixtures = {p for p in protegidos if p.startswith("runs/l4/fixtures/")}
    assert not fixtures, (
        f"`{nombre}` con el glob {arreglado} SIGUE viendo {len(fixtures)} fixtures:"
        " este control negativo no está probando lo que dice probar"
    )
    assert protegidos, "y el resto sí se sigue protegiendo: la rotura es del glob, no del hook"
