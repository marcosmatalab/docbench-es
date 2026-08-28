"""`docbench report` · de los diarios de una corrida a la tabla de nivel 1.

**Lee, no mide.** Toda la aritmética está en `report.nivel1` y `core`, que son puros y se
prueban sin corpus; esto sólo abre ficheros y los junta. Es lo que hace que la tabla se
pueda **regenerar sobre extracciones viejas** sin volver a correr cuatro horas — la
promesa que `.importlinter` protege con «el núcleo es puro».

**La verdad se deriva aquí y no viene del disco**: `truth.derived` es determinista sobre
el XML del BOE, así que reconstruirla cuesta segundos y evita un artefacto más que se
pueda quedar viejo. Sale del `companions["xml"]` que guarda `corpus.store`, o sea de los
mismos bytes cuyo `sha256` se rehizo al cargarlos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from docbench_es.corpus.store import Almacen
from docbench_es.entity import boe_xml
from docbench_es.errors import DocbenchError
from docbench_es.extract.diario import Diario
from docbench_es.extract.sello import sello_de_corrida
from docbench_es.report.cara_a_cara import cara_a_cara
from docbench_es.report.informe import informe
from docbench_es.report.nivel1 import Nivel1, medir
from docbench_es.report.procedencia import difieren
from docbench_es.report.tables import tabla_nivel1
from docbench_es.truth.derived import derivar

CAMPANA = Path("runs/l5/campana")
MANIFIESTO = Path("runs/l3/manifiesto.json")
DOCS = Path("runs/l3/docs")


def _verdades(almacen: Almacen, ids: list[str]) -> tuple[dict[str, tuple[object, ...]], int]:
    """La verdad derivada de cada documento, y **cuántas tablas se descartaron**.

    `derivar` saca de la verdad las tablas con hallazgos FATALES —solapes y spans fuera de
    rango que el XML del BOE produce de verdad, LIMITS 30—. Ese recuento se devuelve
    porque es un denominador: una tabla que no está en la verdad no es una tabla que el
    extractor falló.
    """
    fuera: dict[str, tuple[object, ...]] = {}
    descartadas = 0
    for ident in ids:
        doc = almacen.cargar(ident)
        xml = doc.companions.get("xml")
        if xml is None:
            continue
        d = derivar(doc.ref, boe_xml.tablas(xml.decode("utf-8", errors="replace")))
        descartadas += len(d.descartadas)
        if d.verdad.tables:
            fuera[ident] = d.verdad.tables
    return fuera, descartadas


def report(
    campana: Annotated[
        Path, typer.Option("--campaign", help="el directorio de la corrida")
    ] = CAMPANA,
    manifiesto: Annotated[Path, typer.Option(help="manifiesto del corpus")] = MANIFIESTO,
    docs: Annotated[Path, typer.Option(help="carpeta con los bytes")] = DOCS,
    salida: Annotated[Path | None, typer.Option(help="dónde escribir el .md")] = None,
) -> None:
    """La tabla de nivel 1 de una corrida ya hecha."""
    sello = campana / "sello.json"
    if not sello.exists():
        typer.echo(f"  no hay corrida en {campana}: falta {sello.name}", err=True)
        raise typer.Exit(code=4)
    crudo = json.loads(sello.read_text(encoding="utf-8"))
    versiones = {str(e["id"]): str(e["version"]) for e in crudo["extractores"]}
    typer.echo(f"\n  corrida de {crudo['commit']} · {crudo['documentos']} documentos\n")

    almacen = Almacen(manifiesto, docs)
    diarios = {n: Diario(campana / f"{n}.jsonl") for n in versiones}
    leidos = {n: d.leer() for n, d in diarios.items()}
    for nombre, leido in leidos.items():
        typer.echo(f"  {nombre}: {leido}")
    ids = sorted({e.doc_ref.external_id for x in leidos.values() for e in x.extracciones})
    try:
        verdades, descartadas = _verdades(almacen, ids)
    except DocbenchError as exc:
        typer.echo(f"\n  {exc}", err=True)
        raise typer.Exit(code=exc.exit_code) from exc
    paginas = {e.external_id: e.n_pages or 0 for e in almacen.entradas}
    typer.echo(
        f"\n  verdad derivada: {len(verdades)} documentos con tabla de {len(ids)} · "
        f"{descartadas} tablas fuera de la verdad por hallazgo fatal\n"
    )

    filas: dict[str, Nivel1] = {
        n: medir(x.extracciones, verdades, paginas)  # type: ignore[arg-type]
        for n, x in leidos.items()
    }
    mio = sello_de_corrida(
        "informe de nivel 1",
        {"sello_de_la_corrida": sello, **{n: campana / f"{n}.jsonl" for n in versiones}},
        {"campana": str(campana)},
    )
    texto = tabla_nivel1(filas, versiones, crudo, mio, paginas)
    typer.echo(texto)

    movido = difieren(crudo, mio)
    typer.echo(
        f"\n  árboles: corrida {crudo.get('commit')} · informe {mio.get('commit')} — "
        + (
            "EL MISMO"
            if not movido
            else f"DISTINTOS en {', '.join(movido)}, y va dicho en la tabla"
        )
    )
    if salida is not None:
        salida.write_text(texto + "\n", encoding="utf-8")
        suyo = salida.with_suffix(salida.suffix + ".sello.json")
        suyo.write_text(json.dumps(mio, indent=1, ensure_ascii=False), encoding="utf-8")
        # EL JSON SE ESCRIBE EN LA MISMA LLAMADA, no en un comando aparte. Un artefacto
        # que hay que acordarse de regenerar es un artefacto que se queda viejo, y éste
        # existe justamente para que el titular del hito no sea un número tecleado.
        datos = campana.parent / "informe.json"
        datos.write_text(
            json.dumps(
                informe(filas, cara_a_cara(filas, paginas), versiones, crudo, mio),
                indent=1,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        typer.echo(f"  escrito {salida} · sello del informe en {suyo} · datos en {datos}")
