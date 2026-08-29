"""`docbench portada` · de `informe.json` a la puerta de entrada del proyecto.

**Lee, no mide**, igual que `docbench report`: toda la aritmética está en
`report.portada`, que es puro sobre un `dict`. Esto abre ficheros, cuenta el repo y
escribe dos salidas.

    uv run docbench portada --informe runs/l5/informe.json --salida docs/index.html
    uv run docbench portada --comprobar     # no escribe: dice si están rancias

**El modo por defecto COMPRUEBA y no escribe**, que es al revés de lo cómodo y es
deliberado: lo que corre en la puerta es la comprobación, y un comando cuyo modo por
defecto sobrescribe artefactos versionados invita a que alguien lo meta en un hook y
convierta un rojo en un `git diff` silencioso.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from docbench_es.report.portada import FIN, INICIO, bloque_corto, cifras, del_repo, pagina

INFORME = Path("runs/l5/informe.json")
SALIDA = Path("docs/index.html")


def _remoto(raiz: Path) -> str:
    """`https://github.com/usuario/repo/`, o vacío. **De `git`, nunca tecleado.**

    Sin remoto no se inventa una URL: se devuelve vacío y los enlaces salen relativos,
    que es lo que funciona en un clon abierto desde el sistema de ficheros.
    """
    try:
        url = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=raiz,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""
    if not url:
        return ""
    url = url.removesuffix(".git").replace("git@github.com:", "https://github.com/")
    return f"{url}/"


def _pagina_publicada(remoto: str, salida: Path) -> str:
    """A dónde apunta el README. **La URL de Pages sale del remoto, con la misma regla.**

    `https://github.com/u/r/` -> `https://u.github.io/r/`, que es donde GitHub Pages
    sirve una carpeta `docs/`. Sin remoto, la ruta del fichero: el README vive al lado.
    """
    if not remoto.startswith("https://github.com/"):
        return str(salida)
    usuario, _, repo = remoto.removeprefix("https://github.com/").strip("/").partition("/")
    return f"https://{usuario}.github.io/{repo}/"


def _partes(informe: Path, raiz: Path, salida: Path) -> tuple[str, str, str]:
    """La página, el bloque corto y el resumen de lo que se ha contado."""
    datos = json.loads(informe.read_text(encoding="utf-8"))
    censo = del_repo(raiz)
    todas = cifras(datos, censo)
    orden = sorted(datos["extractores"], key=lambda n: -float(datos["extractores"][n]["teds"]))
    remoto = _remoto(raiz)
    html = pagina(todas, orden, remoto)
    corto = bloque_corto(todas, _pagina_publicada(remoto, salida))
    resumen = (
        f"{len(todas)} cifras · {censo.limites} límites · {censo.adr} ADR · "
        f"{censo.mutantes} mutantes · techo {censo.techo_ms} ms"
    )
    return html, corto, resumen


def _readme_con(bloque: str, texto: str) -> str:
    i, j = texto.index(INICIO), texto.index(FIN) + len(FIN)
    return texto[:i] + bloque + texto[j:]


def portada(
    informe: Annotated[Path, typer.Option("--informe", help="el informe de la campaña")] = INFORME,
    salida: Annotated[Path, typer.Option("--salida", help="dónde escribir la página")] = SALIDA,
    readme: Annotated[Path, typer.Option(help="el documento con el bloque corto")] = Path(
        "README.md"
    ),
    escribir: Annotated[bool, typer.Option("--escribir", help="escribe las dos salidas")] = False,
) -> None:
    """La portada del proyecto: una página y el bloque corto del README."""
    if not informe.exists():
        typer.echo(f"  no hay informe en {informe}: corre `docbench report` antes", err=True)
        raise typer.Exit(code=4)
    raiz = Path.cwd()
    html, corto, resumen = _partes(informe, raiz, salida)

    if not readme.exists() or INICIO not in readme.read_text(encoding="utf-8"):
        typer.echo(f"  ABORTA: falta la marca {INICIO} en {readme}", err=True)
        raise typer.Exit(code=2)
    viejo_readme = readme.read_text(encoding="utf-8")
    nuevo_readme = _readme_con(corto, viejo_readme)

    rancias = [
        nombre
        for nombre, actual, nuevo in (
            (str(salida), salida.read_text(encoding="utf-8") if salida.exists() else "", html),
            (str(readme), viejo_readme, nuevo_readme),
        )
        if actual != nuevo
    ]
    typer.echo(f"\n  portada de {informe} · {resumen}")
    if not escribir:
        if rancias:
            typer.echo(f"  RANCIAS: {', '.join(rancias)}. Regenéralas:", err=True)
            typer.echo("    uv run docbench portada --escribir", err=True)
            raise typer.Exit(code=1)
        typer.echo("  las dos salidas coinciden con el informe.\n")
        return
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(html, encoding="utf-8")
    readme.write_text(nuevo_readme, encoding="utf-8")
    typer.echo(f"  escritas {salida} y el bloque PORTADA de {readme}\n")
