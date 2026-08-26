"""`docbench conform --extractor <id>` · **el criterio de terminado de un extractor.**

`.claude/rules/extractores.md` lo dice sin margen: *«el criterio de terminado de un
extractor nuevo es uno solo: `docbench conform --extractor <id>` en verde. Nada más, y
nada menos»*. Este fichero es lo que hace que esa frase sea verdad y no una intención.

**El extractor se carga por el registro, o sea por el mismo camino que el de un cliente.**
Nada de un diccionario de los propios: si hubiera un atajo, la suite sólo probaría el
camino que nadie de fuera usa.

Y todo lo que imprime lleva **su denominador**: cuántos documentos, cuántos con celdas
combinadas, y qué veredictos podía producir el conjunto. «Verde» a secas es
indistinguible de no haber mirado nada.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from docbench_es.corpus.store import Almacen
from docbench_es.errors import DocbenchError
from docbench_es.extract.conformance import comprobar
from docbench_es.extract.conjunto import cargar_conjunto
from docbench_es.extract.registry import cargar, nombres

CONJUNTO = Path("runs/l5/conformidad.yaml")
MANIFIESTO = Path("runs/l3/manifiesto.json")
DOCS = Path("runs/l3/docs")
FIXTURES = Path("runs/l4/fixtures")


def conform(
    extractor: Annotated[str, typer.Option("--extractor", "-e", help="id registrado")],
    conjunto: Annotated[Path, typer.Option(help="el conjunto de conformidad")] = CONJUNTO,
    manifiesto: Annotated[Path, typer.Option(help="manifiesto del corpus")] = MANIFIESTO,
    docs: Annotated[Path, typer.Option(help="carpeta con los bytes")] = DOCS,
    fixtures: Annotated[Path, typer.Option(help="verdad congelada de L4")] = FIXTURES,
) -> None:
    """Pasa un extractor por la suite de conformidad y dice qué le falta, todo de una vez."""
    try:
        clase = cargar(extractor)
    except DocbenchError as exc:
        typer.echo(f"  {exc}\n  registrados: {nombres() or '(ninguno)'}", err=True)
        raise typer.Exit(code=exc.exit_code) from exc
    if not isinstance(clase, type):
        typer.echo(f"  '{extractor}' carga un {type(clase).__name__}, no una clase", err=True)
        raise typer.Exit(code=1)
    instancia = clase()

    sonda = instancia.probe()
    typer.echo(f"\n  {extractor} · probe: {sonda.status} · {sonda.detail or sonda.version}")
    try:
        elegidos = cargar_conjunto(conjunto, Almacen(manifiesto, docs), fixtures)
    except (DocbenchError, OSError) as exc:
        typer.echo(f"  no se pudo montar el conjunto: {exc}", err=True)
        raise typer.Exit(code=4) from exc
    typer.echo(f"  conjunto: {elegidos}\n")

    informe = comprobar(instancia, elegidos.casos)
    for h in informe.hallazgos:
        typer.echo(f"    [{h.severidad}] {h.comprobacion}: {h.detalle}")
    typer.echo(f"\n  {informe}\n")
    if not informe.pasa:
        raise typer.Exit(code=1)
