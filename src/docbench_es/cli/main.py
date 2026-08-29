"""`docbench` · la CLI. **Cada subcomando declarado tiene código detrás.**

El ejecutable se retiró en la auditoría en frío de `a0d85ed` porque apuntaba a un módulo
que no existía: un ejecutable prometido que revienta con `ModuleNotFoundError` es
exactamente lo que la regla que gobierna este repo llama el fallo más grave. Volvió con
L5, que es la condición que se puso entonces, y con la regla que evita repetirlo:

**Aquí no se declara un subcomando sin su implementación.** Ni un `--help` que diga
«todavía no»: este repo tiene una sección entera de «Construido y NO VALIDADO» por
adelantarse, y un stub es exactamente eso. Los que faltan de §8 —`entity`, `corpus`,
`truth`, `ask`, `report`, `route`, `drift`, `publish`…— entran con su hito.
"""

from __future__ import annotations

import typer

from docbench_es.cli import conform as _conform
from docbench_es.cli import portada as _portada
from docbench_es.cli import report as _report
from docbench_es.cli import run as _run

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Banco de extracción documental en español. `docbench <comando> --help`.",
)


@app.callback()
def raiz() -> None:
    """Un `callback` vacío, y no es decorativo.

    Sin él, `typer` **colapsa** una app de un solo comando en ese comando: hoy se
    invocaría `docbench --extractor x` y el día que entre el segundo subcomando pasaría a
    ser `docbench conform --extractor x`. La invocación publicada en `.claude/rules` y en
    el `Makefile` cambiaría sola al añadir código en otro sitio.
    """


app.command("conform")(_conform.conform)
app.command("run")(_run.run)
app.command("report")(_report.report)
app.command("portada")(_portada.portada)

if __name__ == "__main__":  # pragma: no cover - se entra por el entry point
    app()
