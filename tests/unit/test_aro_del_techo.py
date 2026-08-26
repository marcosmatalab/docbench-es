"""El techo de la puerta, vigilado **en cada commit** y no sólo al cerrar hito.

La puerta estuvo a 25,5 s —tres veces el techo de 8500— durante diez commits, con
`medir_puerta.py` funcionando perfectamente. No fue descuido: es estructura. Aquel
instrumento sólo se corre al cerrar hito, y entre cierre y cierre pasa el trabajo, así
que la ventana de ceguera es casi todo el calendario (LIMITS 102).

## Y las dos mitades que no son obvias

**La medida tiene que ser EN FRÍO.** Registrar la duración de un `make fast` cualquiera
habría dejado pasar los diez commits igual. Medido sobre `99be97d`, con la regresión
dentro: **30 259 ms en frío contra 2 781 en caliente**. Quien trabaja no la ve, y el
techo sí.

**Y lo que se compara es el MÍNIMO, no la última.** Medido nada más montar el aro: seis
corridas en frío del mismo árbol dieron 6 367, 6 383, 6 819, 7 835, 9 236 y 9 661 ms,
sobre un árbol cuya serie de n=40 da p90 6 866. O sea que **una sola corrida se pasa del
techo una de cada tres** por contención, y un aro que bloquea una de cada tres veces sin
motivo se acaba sorteando. El mínimo es optimista **y lo declara**; lo que no puede
esconder es lo único que este aro tiene que cazar: una regresión que multiplica TODAS
las corridas.

Se ejercita el hook de verdad, con su entrada de verdad, en un proyecto de juguete: un
guardián que sólo se ha visto funcionar a mano está en el estado que el paso 4 de
`/cerrar` llama insuficiente.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
HOOKS = RAIZ / ".claude" / "hooks"
ARO = HOOKS / "guard-commit.sh"
REGISTRAR = HOOKS / "registrar-puerta.sh"

ORDEN = json.dumps({"tool_input": {"command": "git commit -m prueba"}})


def _techo_del_hook() -> int:
    texto = REGISTRAR.read_text(encoding="utf-8")
    casa = re.search(r"^TECHO=(\d+)$", texto, re.MULTILINE)
    assert casa, "el hook no declara TECHO"
    return int(casa.group(1))


def _techo_del_instrumento() -> int:
    texto = (RAIZ / "scripts" / "medir_puerta.py").read_text(encoding="utf-8")
    casa = re.search(r'"--techo",\s*type=int,\s*default=(\d+)', texto)
    assert casa, "medir_puerta.py no declara un techo por defecto"
    return int(casa.group(1))


def _proyecto(tmp_path: Path, registro: str | None, huella_al_dia: bool = True) -> Path:
    """Un proyecto de juguete con los tres hooks y las marcas que se le pidan."""
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    for nombre in ("guard-commit.sh", "registrar-puerta.sh", "huella-puerta.sh"):
        shutil.copy(HOOKS / nombre, tmp_path / ".claude" / "hooks" / nombre)
    huella = subprocess.run(
        [str(tmp_path / ".claude" / "hooks" / "huella-puerta.sh")],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)},
    ).stdout.strip()
    (tmp_path / ".claude" / ".ultima-puerta").write_text(
        huella if huella_al_dia else "otra-huella", encoding="utf-8"
    )
    if registro is not None:
        marca = huella if huella_al_dia else "otra-huella"
        (tmp_path / ".claude" / ".ultima-puerta.txt").write_text(
            registro.replace("HUELLA", marca), encoding="utf-8"
        )
    return tmp_path


def _decide(proyecto: Path) -> str:
    hecho = subprocess.run(
        [str(proyecto / ".claude" / "hooks" / "guard-commit.sh")],
        input=ORDEN,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(proyecto)},
    )
    assert hecho.returncode == 0, hecho.stderr
    if not hecho.stdout.strip():
        return "PASA"
    return str(json.loads(hecho.stdout)["hookSpecificOutput"]["permissionDecisionReason"])


def test_los_dos_techos_son_el_mismo_numero() -> None:
    """Está escrito en el hook Y en `medir_puerta.py`, y son dos copias.

    Una copia comprobada es una copia; una sin comprobar es un bug esperando a que
    alguien mueva la otra y deje al aro vigilando un techo que ya nadie usa.
    """
    assert _techo_del_hook() == _techo_del_instrumento() == 8500


def test_una_medida_fria_por_debajo_del_techo_deja_commitear(tmp_path: Path) -> None:
    """**El control positivo.** Sin él, los tests de «bloquea» pasarían con un aro que
    bloqueara siempre, que es un aro inútil de la otra manera."""
    assert _decide(_proyecto(tmp_path, "HUELLA 6430 frio 3")) == "PASA"


def test_una_medida_caliente_no_vale_por_buena_que_sea(tmp_path: Path) -> None:
    """**El caso que motiva todo esto.** 2.781 ms en caliente está muy por debajo del
    techo, y debajo de ellos había una puerta de 30 s."""
    razon = _decide(_proyecto(tmp_path, "HUELLA 2781 caliente 0"))
    assert "EN FRÍO" in razon, razon
    assert "make frio" in razon


def test_una_medida_fria_por_encima_del_techo_bloquea(tmp_path: Path) -> None:
    """Verde no es suficiente: la puerta estuvo verde los diez commits."""
    razon = _decide(_proyecto(tmp_path, "HUELLA 25949 frio 4"))
    assert "PASA DEL TECHO" in razon, razon
    assert "25949" in razon and "8500" in razon
    assert "MÍNIMO de 4" in razon, "el aro dice sobre cuántas corridas decide"


def test_sin_ninguna_medida_tampoco_se_commitea(tmp_path: Path) -> None:
    """Un aro que no se ha corrido no es un aro superado: la misma regla que
    `NO_EJECUTADA` en la suite de conformidad."""
    razon = _decide(_proyecto(tmp_path, None))
    assert "NO HAY MEDIDA" in razon, razon


def test_una_medida_de_otro_arbol_no_vale(tmp_path: Path) -> None:
    """La huella del registro se compara igual que la del verde: una medida rápida de
    otro árbol no dice nada de éste."""
    proyecto = _proyecto(tmp_path, "otro-arbol 100 frio 9")
    assert _decide(proyecto) != "PASA"


@pytest.mark.parametrize(
    ("caches", "espera"),
    [((), "frio"), ((".mypy_cache",), "caliente"), ((".hypothesis",), "caliente")],
)
def test_frio_exige_que_no_quede_ninguna_cache(
    tmp_path: Path, caches: tuple[str, ...], espera: str
) -> None:
    """Con el criterio flojo —sólo `.mypy_cache`— borrar una caché contaría como frío y
    la cifra saldría optimista. `.hypothesis` no es velocidad: es lo ya explorado."""
    (tmp_path / ".claude").mkdir()
    shutil.copy(REGISTRAR, tmp_path / "registrar-puerta.sh")
    for c in caches:
        (tmp_path / c).mkdir()
    subprocess.run(
        [str(tmp_path / "registrar-puerta.sh"), "--empieza"],
        check=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)},
    )
    assert (tmp_path / ".claude" / ".puerta-inicio").read_text().split()[1] == espera


def _registrar(proyecto: Path, ms: int, frio: bool) -> tuple[int, str, int]:
    """Corre `--empieza`/`--acaba` simulando una corrida de `ms` milisegundos.

    Devuelve el registro ya partido. La duración sale unos milisegundos por encima de
    `ms` —el hook mide contra el reloj de verdad—, así que los tests comparan **entre
    registros** y no contra el nominal: lo que se afirma es cuál de los dos gana.
    """
    for c in (".mypy_cache", ".pytest_cache", ".ruff_cache", ".hypothesis"):
        ruta = proyecto / c
        if frio:
            shutil.rmtree(ruta, ignore_errors=True)
        else:
            ruta.mkdir(exist_ok=True)
    entorno = {**os.environ, "CLAUDE_PROJECT_DIR": str(proyecto)}
    hook = str(proyecto / ".claude" / "hooks" / "registrar-puerta.sh")
    subprocess.run([hook, "--empieza"], check=True, env=entorno)
    inicio = proyecto / ".claude" / ".puerta-inicio"
    t0, estado = inicio.read_text().split()
    inicio.write_text(f"{int(t0) - ms} {estado}\n", encoding="utf-8")
    subprocess.run([hook, "--acaba"], check=True, env=entorno, capture_output=True)
    _, minimo, estado, n = (proyecto / ".claude" / ".ultima-puerta.txt").read_text().strip().split()
    return int(minimo), estado, int(n)


def test_el_minimo_sobrevive_a_una_corrida_con_contencion(tmp_path: Path) -> None:
    """**El caso medido**: 6.534 y luego 9.524 sobre el mismo árbol. Si se guardara la
    última, el aro bloquearía por una corrida con mala suerte."""
    proyecto = _proyecto(tmp_path, None)
    bueno, _, _ = _registrar(proyecto, 6534, frio=True)
    assert _registrar(proyecto, 9524, frio=True) == (bueno, "frio", 2)


def test_una_corrida_caliente_no_borra_el_minimo_en_frio(tmp_path: Path) -> None:
    """Un `make fast` de trabajo no puede tirar la medida que el aro necesita —ni
    tampoco mejorarla: no mide lo mismo."""
    proyecto = _proyecto(tmp_path, None)
    en_frio, _, _ = _registrar(proyecto, 6534, frio=True)
    assert _registrar(proyecto, 900, frio=False) == (en_frio, "frio", 1), (
        "una caliente de 900 ms no es el suelo, y tampoco borra el que había"
    )


def test_repetir_en_frio_baja_el_minimo_y_lo_dice(tmp_path: Path) -> None:
    """El control positivo del mínimo: una corrida mejor SÍ lo mejora, o el aro sería
    imposible de desbloquear tras una mala."""
    proyecto = _proyecto(tmp_path, None)
    _registrar(proyecto, 9600, frio=True)
    assert _decide(proyecto) != "PASA", "9600 pasa del techo y tiene que bloquear"
    _registrar(proyecto, 6400, frio=True)
    assert _decide(proyecto) == "PASA"
