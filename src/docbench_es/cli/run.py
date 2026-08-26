"""`docbench run` · la campaña: N extractores sobre una población declarada.

**Lo que este subcomando NO es todavía.** `make bench` y `make quickstart` invocan
`docbench run --plan <plan.yaml>`, y **ese plan es el plan de muestreo congelado de L6**,
que aún no existe (LIMITS 8: `quickstart` necesita CLI, extractores y los 20 documentos
versionados de L7). Lo que existe hoy es una **población declarada** —`runs/l5/poblacion.
json`, congelada con su diseño y sus porqués— así que eso es lo que se acepta. Añadir un
`--plan` que leyera cualquier YAML sería prometer el muestreo antes de tener el muestreo.

**`--offline` no es decorativo.** Con él, un extractor que declare `runs_locally=False`
**no arranca la campaña**: es la regla de oro 5 aplicada al revés —allí es la fuente la
que prohíbe el egress; aquí es quien mide—, y en los dos casos el motor rechaza en vez de
avisar.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from docbench_es.corpus.store import Almacen
from docbench_es.errors import DocbenchError
from docbench_es.extract.corredor import correr
from docbench_es.extract.registry import cargar, nombres

POBLACION = Path("runs/l5/poblacion.json")
MANIFIESTO = Path("runs/l3/manifiesto.json")
DOCS = Path("runs/l3/docs")
SALIDA = Path("runs/l5/campana")


def _poblacion(ruta: Path) -> list[str]:
    """Los `external_id`, de una lista o del diseño de dos poblaciones de L5.

    `runs/l5/poblacion.json` trae `con_tabla` —censo— y `sin_tabla_muestreados` —muestra
    estratificada, que es el control negativo de detección—. **Los dos entran**: tirar los
    segundos ahorraría cómputo y borraría el único sitio donde se ve un extractor que
    inventa una tabla donde no la hay.
    """
    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    if isinstance(crudo, list):
        return [str(x) for x in crudo]
    fuera = [str(x) for x in crudo.get("con_tabla", ())]
    for estrato in crudo.get("sin_tabla_muestreados", {}).values():
        fuera += [str(x) for x in estrato]
    return fuera


def _extractores(pedidos: str) -> list[object]:
    disponibles = nombres()
    quienes = (
        disponibles if pedidos == "all" else [x.strip() for x in pedidos.split(",") if x.strip()]
    )
    fuera: list[object] = []
    for nombre in quienes:
        clase = cargar(nombre)
        if not isinstance(clase, type):
            raise DocbenchError(f"'{nombre}' carga un {type(clase).__name__}, no una clase")
        fuera.append(clase())
    return fuera


def run(
    extractors: Annotated[str, typer.Option("--extractors", "-e", help="ids, o `all`")] = "all",
    poblacion: Annotated[Path, typer.Option(help="la población declarada")] = POBLACION,
    manifiesto: Annotated[Path, typer.Option(help="manifiesto del corpus")] = MANIFIESTO,
    docs: Annotated[Path, typer.Option(help="carpeta con los bytes")] = DOCS,
    salida: Annotated[Path, typer.Option(help="dónde va el diario de la corrida")] = SALIDA,
    limite: Annotated[int, typer.Option(help="corta la población: para humo, no para medir")] = 0,
    offline: Annotated[
        bool, typer.Option(help="rechaza extractores que no corran en local")
    ] = False,
) -> None:
    """Corre la campaña. Reanudable: se salta lo que ya tiene línea en el diario."""
    try:
        elegidos = _extractores(extractors)
    except DocbenchError as exc:
        typer.echo(f"  {exc}\n  registrados: {nombres() or '(ninguno)'}", err=True)
        raise typer.Exit(code=getattr(exc, "exit_code", 1)) from exc
    if not elegidos:
        typer.echo(f"  ningún extractor seleccionado de {nombres()}", err=True)
        raise typer.Exit(code=5)
    remotos = [e for e in elegidos if not getattr(e, "runs_locally", False)]
    if offline and remotos:
        typer.echo(
            f"  --offline y {[getattr(e, 'id', '?') for e in remotos]} no corren en local. "
            f"La campaña NO arranca: no es un aviso.",
            err=True,
        )
        raise typer.Exit(code=2)

    ids = _poblacion(poblacion)
    if limite:
        ids = ids[:limite]
        typer.echo(f"  AVISO: población recortada a {len(ids)}. Esto es humo, no una medida.")
    almacen = Almacen(manifiesto, docs)
    typer.echo(
        f"\n  {len(elegidos)} extractores por {len(ids)} documentos = "
        f"{len(elegidos) * len(ids)} unidades · almacén de {len(almacen)}\n"
    )
    try:
        resumenes = correr(
            elegidos,  # type: ignore[arg-type]
            almacen,
            ids,
            salida,
            que="campaña de estructura L5",
            entradas={"poblacion": poblacion, "manifiesto": manifiesto},
            eco=typer.echo,
        )
    except DocbenchError as exc:
        typer.echo(f"\n  {exc}", err=True)
        raise typer.Exit(code=getattr(exc, "exit_code", 1)) from exc
    typer.echo("")
    for r in resumenes:
        typer.echo(f"  {r}")
    typer.echo("")
