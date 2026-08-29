"""Las tres últimas piezas de la portada: los límites, las puertas y el pie.

Salen de `_pagina.py` por el límite de 300 líneas de `CLAUDE.md`, y la costura cae donde
tiene que caer: arriba está lo que sale de **la campaña** —el titular, las bandas, las
notas, la errata—, y aquí lo que sale del **repo** y no cambia cuando se vuelve a correr
una campaña. Son dos cadencias distintas, que es la misma distinción que hace `_censo.py`.
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.portada._cifras import Cifra

from docbench_es.report.portada._cifras import CARDINALES

__all__ = ["LIMITES", "PUERTAS", "limites", "pie", "puertas"]

LIMITES: tuple[tuple[str, str], ...] = (
    (
        "El corpus es el BOE",
        "que está mejor maquetado que la media de una empresa. Estos números son un "
        "<b>techo optimista</b> para cualquier otra entidad.",
    ),
    (
        "El error de la verdad de referencia es desconocido.",
        "Es transcripción del XML oficial, no lectura del PDF, y su discordancia contra "
        "una auditoría humana no está medida todavía.",
    ),
    (
        "La tasa de tabla que no está en la referencia sube con la longitud",
        "y <b>no se llama alucinación</b>, porque la adjudicación contra el PDF —mirar el "
        "PDF, no el XML— no está hecha.",
    ),
    (
        "Faltan familias de extractor:",
        "<b>TEI</b> y <b>OCR</b>. El hito cerró con los que caben en el presupuesto de "
        "cómputo, por una regla congelada antes de medirlo.",
    ),
)
"""Los cuatro límites de la portada. **Prosa, sin un solo número dentro.**

No es una selección de los más graves: son los que más cambian **cómo se leen los números
de arriba**, que es otro criterio y es el que sirve en una puerta de entrada. Los demás
—todos, con su fecha— están en `LIMITS.md`, y el recuento va en la puerta de al lado.
"""

PUERTAS: tuple[tuple[str, str, str], ...] = (
    (
        "RESULTS.md",
        "RESULTS.md",
        "Cada número con el comando que lo produce y el sello del árbol donde se midió.",
    ),
    ("LIMITS.md", "LIMITS.md", "Los {limites} límites. Dónde se rompe cada supuesto, con fecha."),
    (
        "docs/adr/",
        "docs/adr/",
        "{adr} decisiones de diseño, cada una con su alternativa descartada.",
    ),
    (
        "runs/l5/informe.json",
        "runs/l5/informe.json",
        "La salida cruda de la campaña. Todo lo de esta página sale de aquí.",
    ),
)
"""`(rótulo, ruta en el repo, descripción)`. **Las rutas son del repo, no URL.**

Quien construye el enlace es `puertas()`, porque el prefijo depende de dónde se sirva la
página y eso no se sabe aquí. Con URL escritas, la portada sólo valdría para un remoto.
"""


def _v(c: Mapping[str, Cifra], clave: str) -> str:
    return escape(c[clave].valor)


def _marca(c: Mapping[str, Cifra], clave: str, tag: str = "span") -> str:
    return f'<{tag} data-cifra="{clave}">{_v(c, clave)}</{tag}>'


def limites(c: Mapping[str, Cifra]) -> str:
    filas = "\n".join(f"    <li><b>{t}</b> {d}</li>" for t, d in LIMITES)
    return f"""<section>
  <p class="eyebrow">Lo que este banco no mide</p>
  <h2>{CARDINALES.get(len(LIMITES), str(len(LIMITES))).capitalize()} de los
  {_marca(c, "limites")}, los que
  más cambian cómo se leen los números de arriba</h2>
  <ul class="limits">
{filas}
  </ul>
</section>"""


def puertas(c: Mapping[str, Cifra], base: str) -> str:
    """Las cuatro puertas. `base` es la raíz del repo en GitHub, o vacío para relativo.

    Servida por GitHub Pages, `docs/index.html` está en la raíz del sitio y un
    `../RESULTS.md` no resuelve a nada; abierta desde un clon con `file://`, una URL a
    GitHub saca al lector del árbol que tiene delante. Se resuelven las dos, y **sin
    inventar un remoto que no exista**.
    """
    valores = {"limites": _marca(c, "limites"), "adr": _marca(c, "adr")}
    filas = []
    for nombre, ruta, texto in PUERTAS:
        if base:
            tipo = "tree" if ruta.endswith("/") else "blob"
            href = f"{base}{tipo}/main/{ruta.rstrip('/')}"
        else:
            href = f"../{ruta}"
        filas.append(
            f'    <a class="door" href="{href}"><span class="f">{escape(nombre)}</span>'
            f'<span class="d">{texto.format(**valores)}</span></a>'
        )
    return f"""<section>
  <p class="eyebrow">Dónde está la profundidad</p>
  <h2>{CARDINALES.get(len(PUERTAS), str(len(PUERTAS))).capitalize()} puertas</h2>
  <div class="doors">
{chr(10).join(filas)}
  </div>
</section>"""


def pie(c: Mapping[str, Cifra]) -> str:
    return f"""<footer>
  Campaña {_marca(c, "hito")} · {_marca(c, "documentos")} documentos ·
  {_marca(c, "paginas")} páginas · {_marca(c, "tablas_verdad")} tablas en la verdad de
  referencia<br>
  sello de la corrida <code data-cifra="sello_corrida">{_v(c, "sello_corrida")}</code> ·
  informe emitido sobre <code data-cifra="sello_informe">{_v(c, "sello_informe")}</code> ·
  {_marca(c, "cpu")}, {_marca(c, "procesos")} procesos visibles<br>
  Esta página la genera <code>docbench portada</code> desde
  <code>runs/l5/informe.json</code>. Ninguna cifra está tecleada.
</footer>"""
