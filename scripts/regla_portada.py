"""**R9 · la portada publicada, contra `runs/l5/informe.json` y el censo del repo.**

    uv run python scripts/derivadas.py --detalle

## Por qué existe

`docs/index.html` y el bloque `PORTADA` del `README.md` son **la primera pantalla** de
alguien que no va a volver, y publican el titular del hito, las cuatro notas, la errata y
el método. Es la copia número catorce del titular, y sería **la primera en quedarse
vieja**: es exactamente lo que le pasó al README, que estuvo **33 commits** publicando
«Hito L0 de 10» con cuatro hitos más cerrados.

Que la portada la **genere** un comando no basta por sí solo. Un generador que nadie
corre deja el fichero viejo igual, y encima con la apariencia de estar derivado — que es
peor, porque nadie va a comprobarlo a mano. Así que la puerta compara.

## Qué comprueba, y en las TRES direcciones

`report.portada` marca cada número de la página con `data-cifra="<clave>"`, así que aquí
no se busca «¿aparece 103 en el HTML?» —103 sale también en el pie y en cualquier
tabla— sino qué dice el elemento que **dice ser** el titular. Con eso salen tres
comprobaciones, y la tercera no la tenía ninguna otra regla de este fichero:

1. **la que no cuadra** — una clave publicada con otro valor;
2. **la que falta** — una clave que el instrumento emite y la página no lleva;
3. **la que sobra** — una clave EN LA PÁGINA que el instrumento no emite. Un número en
   la portada sin fuente es precisamente lo que la portada existe para no tener, y sin
   esta dirección se podría añadir uno a mano y pasaría en verde.

## Y el panel, que es una comprobación de SITIO y no de valor

El titular sólo está completo con su panel dentro de la etiqueta (LIMITS 113): «103 de
338» sin decir sobre qué cuatro extractores es una intersección sin conjuntos. Que el
panel esté **en alguna parte de la página** no vale — tiene que estar **dentro del bloque
del titular**. Eso lo comprueba `panel_dentro_de_la_etiqueta()`, y es lo que mata el
mutante `portada_sin_panel`.
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from html import unescape
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from docbench_es.report.portada import cifras, del_repo  # noqa: E402
from rota import Rota  # noqa: E402

INFORME = RAIZ / "runs" / "l5" / "informe.json"
PAGINA = RAIZ / "docs" / "index.html"
MARCA = re.compile(r'data-cifra="([a-z0-9_]+)"[^>]*>([^<]*)<')
FIGURA = re.compile(r'<div class="figure">(.*?)</div>', re.S)


@lru_cache(maxsize=1)
def _esperadas() -> dict[str, str] | None:
    """Clave -> valor, tal y como los emite el instrumento. `None` si falta el informe."""
    if not INFORME.exists():
        return None
    datos = json.loads(INFORME.read_text(encoding="utf-8"))
    return {k: c.valor for k, c in cifras(datos, del_repo(RAIZ)).items()}


def publicadas(html: str) -> dict[str, str]:
    """Clave -> valor, tal y como están en la página. **Repetidas incluidas.**

    Una clave puede salir varias veces —`limites` está en el método, en el titular de la
    sección de límites y en una puerta— y las tres tienen que decir lo mismo. Si dos
    copias de la misma clave divergen, la que gana es la primera y la segunda sale como
    desajuste: es el fallo que este repo lleva contando desde el límite 111.
    """
    fuera: dict[str, str] = {}
    for clave, crudo in MARCA.findall(html):
        # `&gt;50` y `>50` son el MISMO valor: uno es el otro escapado para HTML, y
        # comparar sin desescapar pondría roja la banda `>50` por su tipografía.
        valor = unescape(crudo).strip()
        if clave in fuera and fuera[clave] != valor:
            fuera[f"{clave} (segunda copia)"] = valor
        else:
            fuera.setdefault(clave, valor)
    return fuera


def panel_dentro_de_la_etiqueta(html: str) -> bool:
    """¿El panel está DENTRO del bloque del titular, y no sólo en la página?

    `<div class="figure">` es la etiqueta del titular. El panel tiene que estar ahí
    dentro, con el número, y no en un párrafo de después: una nota al pie se lee
    después de haber leído el número, o sea demasiado tarde.
    """
    figura = FIGURA.search(html)
    return figura is not None and 'data-cifra="panel"' in figura.group(1)


def portada_contra_el_informe(_texto: str, documento: str) -> list[Rota]:
    """La portada, contra su fuente. **Corre una sola vez**, como R6.

    Va colgada de `RESULTS.md` porque no es una comprobación sobre el texto de nadie: es
    sobre dos ficheros fijos. Si corriera por documento, un mismo desajuste saldría nueve
    veces y el recuento de «derivadas rotas» diría nueve donde hay una.
    """
    if documento != "RESULTS.md":
        return []
    esperadas = _esperadas()
    if esperadas is None:
        return []
    if not PAGINA.exists():
        return [
            Rota(
                "docs/index.html",
                0,
                "la portada no existe",
                "no está",
                "uv run docbench portada --escribir",
            )
        ]
    html = PAGINA.read_text(encoding="utf-8")
    vistas = publicadas(html)
    fuera: list[Rota] = []
    for clave, esperado in esperadas.items():
        base = clave.split(" ")[0]
        if base not in vistas:
            fuera.append(Rota("docs/index.html", 0, f"cifra {clave}", "no aparece", esperado))
    for clave, publicado in vistas.items():
        suya = esperadas.get(clave.split(" ")[0])
        if suya is None:
            fuera.append(
                Rota(
                    "docs/index.html",
                    0,
                    f"cifra {clave} SIN FUENTE",
                    publicado,
                    "no la emite nadie",
                )
            )
        elif publicado != suya:
            linea = html[: html.index(f'data-cifra="{clave.split(" ")[0]}"')].count("\n") + 1
            fuera.append(Rota("docs/index.html", linea, f"cifra {clave}", publicado, suya))
    if not panel_dentro_de_la_etiqueta(html):
        # LIMITS 113: el titular es una función del panel y sólo sabe bajar. Fuera de la
        # etiqueta, el número está incompleto, y un número incompleto en la puerta de
        # entrada es peor que uno que falta: éste se lee.
        fuera.append(
            Rota(
                "docs/index.html",
                0,
                "el panel NO está en la etiqueta del titular",
                "fuera",
                "dentro",
            )
        )
    if not vistas:
        fuera.append(Rota("docs/index.html", 0, "cifras marcadas", "0 vistas", "≥1"))
    return fuera
