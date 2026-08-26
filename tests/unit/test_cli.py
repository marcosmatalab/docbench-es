"""La CLI: **ningún subcomando declarado sin implementación detrás.**

No es una regla de estilo. El entry point `docbench` se retiró en la auditoría en frío de
`a0d85ed` porque apuntaba a un módulo que no existía y lanzarlo reventaba con
`ModuleNotFoundError`: **un ejecutable prometido que no existe** es exactamente lo que la
regla que gobierna este repo llama el fallo más grave. Volvió con L5 y con su CLI.

Lo que estos tests demuestran es que la promesa se sostiene **por ejecución**: el entry
point declarado en `pyproject.toml` se importa, y el `--help` de cada subcomando registrado
sale en verde. Un stub que dijera «todavía no» pasaría el primero y no el segundo.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from docbench_es.cli.main import app

RAIZ = Path(__file__).resolve().parents[2]
ejecutar = CliRunner()


def _declarado_en_pyproject() -> str:
    config = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    return str(config["project"]["scripts"]["docbench"])


def _comandos() -> list[str]:
    """Los nombres registrados en la app, **que es el denominador de todo lo de aquí**."""
    return [str(c.name) for c in app.registered_commands]


def test_el_entry_point_de_pyproject_apunta_a_algo_que_existe() -> None:
    """El fallo literal de `a0d85ed`, convertido en test.

    Se resuelve el `modulo:atributo` declarado, no el que este fichero importa: si alguien
    cambia la línea de `pyproject.toml` a un módulo que no existe, esto se cae — que es
    justo lo que no pasó la primera vez.
    """
    import importlib

    modulo, _, atributo = _declarado_en_pyproject().partition(":")
    cargado = getattr(importlib.import_module(modulo), atributo, None)
    assert cargado is not None, f"{_declarado_en_pyproject()} no resuelve"
    assert callable(cargado), "un entry point de consola tiene que ser invocable"


def test_hay_al_menos_un_subcomando_y_se_dicen_cuales() -> None:
    """El control negativo de todo lo demás: con la app vacía, el bucle de abajo
    recorrería cero comandos y saldría verde sin comprobar nada."""
    assert _comandos(), "la app no registra ningún subcomando"
    assert "conform" in _comandos(), f"registrados: {_comandos()}"


@pytest.mark.parametrize("comando", _comandos())
def test_cada_subcomando_declarado_tiene_implementacion_detras(comando: str) -> None:
    """`--help` de cada uno, en verde. Un subcomando sin código detrás no llega aquí."""
    salida = ejecutar.invoke(app, [comando, "--help"])
    assert salida.exit_code == 0, salida.output


def test_conform_exige_extractor_y_no_revienta_sin_el() -> None:
    """Sin `--extractor` sale el uso, con código 2 de `click`. **No una traza.**"""
    salida = ejecutar.invoke(app, ["conform"])
    assert salida.exit_code == 2, salida.output


def test_conform_con_un_extractor_que_no_existe_dice_cuales_hay() -> None:
    """El error de un plan equivocado se contesta con el denominador, no con un `KeyError`.

    Y con el código de salida de §11 —el 5 de `ContractViolation`—, que es lo que permite
    a un CI distinguir «la medición salió mal» de «el plan pide algo que no está».
    """
    salida = ejecutar.invoke(app, ["conform", "--extractor", "no-existe"])
    assert salida.exit_code == 5, salida.output
    assert "pdfplumber" in salida.output + str(salida.stderr or "")
