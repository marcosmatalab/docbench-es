"""La portada: **que sea derivada de verdad, y que el panel esté donde tiene que estar.**

Dos familias de aserción, y no son la misma:

* **que ninguna cifra esté tecleada** — se compara la página generada contra
  `runs/l5/informe.json` y contra el censo del repo, en las tres direcciones que usa la
  regla R9: la que no cuadra, la que falta y **la que sobra**;
* **que el panel esté DENTRO de la etiqueta del titular** — que es una comprobación de
  sitio, no de valor, y es la que mata al mutante `portada_sin_panel`.

**La segunda no se puede escribir sobre el objeto, sólo sobre el HTML.** `cifras()` puede
emitir un panel perfecto y la página imprimirlo en un párrafo de después: el número
saldría igual de incompleto y `assert "panel" in cifras` pasaría en verde. Es la misma
lección que el mutante `no_aplicable_impreso_cero` — la aritmética puede estar bien y el
renderizado mentir— una capa más arriba.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from docbench_es.cli.portada import _pagina_publicada, _remoto
from docbench_es.report.portada import FIN, INICIO, bloque_corto, cifras, del_repo, pagina
from docbench_es.report.portada._pagina import _titular

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

import regla_portada  # noqa: E402

INFORME = RAIZ / "runs" / "l5" / "informe.json"


@pytest.fixture(scope="module")
def informe() -> dict[str, object]:
    if not INFORME.exists():  # pragma: no cover - sólo sin campaña
        pytest.skip("no hay runs/l5/informe.json")
    datos: dict[str, object] = json.loads(INFORME.read_text(encoding="utf-8"))
    return datos


@pytest.fixture(scope="module")
def html(informe: dict[str, object]) -> str:
    ext: dict[str, dict[str, float]] = informe["extractores"]  # type: ignore[assignment]
    orden = sorted(ext, key=lambda n: -float(ext[n]["teds"]))
    return pagina(cifras(informe, del_repo(RAIZ)), orden, "")


def test_el_panel_va_dentro_de_la_etiqueta_del_titular(html: str) -> None:
    """**LIMITS 113 en el renderizado.** «103 de 338» es una intersección sobre tantos
    conjuntos como extractores tenga el panel: sin el panel al lado, el número está
    incompleto y **dos valores con paneles distintos parecerían comparables**.

    Que el panel salga *en alguna parte* de la página no basta y por eso este test mira
    dentro del bloque: una nota al pie se lee después del número, o sea tarde.
    """
    assert regla_portada.panel_dentro_de_la_etiqueta(html), (
        'el panel no está dentro de `<div class="figure">`: el titular sale incompleto'
    )
    figura = re.search(r'<div class="figure">(.*?)</div>', html, re.S)
    assert figura is not None
    assert 'data-cifra="titular"' in figura.group(1), "el número y su panel van juntos o no valen"


def test_la_monotonia_va_atada_al_numero_y_no_de_nota_al_pie(html: str) -> None:
    """**El segundo asesino de `portada_sin_panel`, y no es una copia del primero.**

    El de arriba comprueba dónde está el **panel**; éste, dónde está la **frase que
    explica por qué el panel importa** — que el número *sólo sabe bajar* al añadir un
    extractor—. Son dos exigencias distintas del límite 113 y podrían romperse por
    separado: se puede imprimir el panel dentro y la explicación fuera, y entonces el
    lector tiene los nombres sin saber qué le hacen al número.

    Un mutante con un solo asesino es **una sola aserción sosteniendo una garantía**, que
    es lo que este repo llama punto único de fallo. Con dos, la garantía tiene dos patas
    y cada una dice algo que la otra no.
    """
    figura = re.search(r'<div class="figure">(.*?)</div>', html, re.S)
    assert figura is not None

    dentro = figura.group(1)

    assert "sólo sabe bajar" in dentro, (
        "la monotonía se ha ido fuera de la etiqueta: el número queda sin lo que lo"
        " califica, y una nota al pie se lee después de haberlo leído"
    )
    assert "no son comparables" in dentro, "y la consecuencia va con ella, no aparte"


def test_el_panel_publicado_es_el_del_informe_y_no_una_lista_escrita(
    informe: dict[str, object], html: str
) -> None:
    """El panel sale de `acuerdo.panel`. Una lista escrita en la plantilla se quedaría
    vieja **el día que entre el quinto extractor**, que es justo el día en que el titular
    baja y en que la etiqueta importa más."""
    acuerdo: dict[str, list[str]] = informe["acuerdo"]  # type: ignore[assignment]
    esperado = " · ".join(acuerdo["panel"])

    publicado = regla_portada.publicadas(html)

    assert publicado["panel"] == esperado
    assert all(nombre in publicado["panel"] for nombre in acuerdo["panel"])


def test_ninguna_cifra_de_la_pagina_esta_sin_fuente(informe: dict[str, object], html: str) -> None:
    """**La tercera dirección**, la que ninguna otra regla de `derivadas.py` tenía: no que
    falte una cifra, sino que **sobre** una. Un número escrito a mano en la plantilla
    pasaría cualquier comprobación de «lo publicado coincide con lo medido», porque no
    hay nada con qué compararlo."""
    emitidas = set(cifras(informe, del_repo(RAIZ)))

    sin_fuente = {k for k in regla_portada.publicadas(html) if k.split(" ")[0] not in emitidas}

    assert not sin_fuente, f"cifras en la portada que el instrumento no emite: {sin_fuente}"


def test_todas_las_cifras_emitidas_salen_en_la_pagina(
    informe: dict[str, object], html: str
) -> None:
    """Y la dirección contraria, que hace falta: sin ella, una plantilla que no imprimiera
    **ninguna** cifra pasaría el test de arriba con las manos en los bolsillos."""
    publicadas = set(regla_portada.publicadas(html))

    faltan = {k for k in cifras(informe, del_repo(RAIZ)) if k not in publicadas}

    assert not faltan, f"el instrumento emite cifras que la portada no publica: {faltan}"


def test_una_cifra_movida_en_la_pagina_la_caza_la_regla(html: str) -> None:
    """**El control negativo de R9.** Una comprobación que nadie ha visto en rojo no es una
    comprobación, y ésta vigila la primera pantalla del proyecto."""
    vistas = regla_portada.publicadas(html)
    movido = html.replace(
        f'data-cifra="titular" class="n">{vistas["titular"]}<',
        'data-cifra="titular" class="n">1 de 1<',
    )
    assert movido != html, "el caso rojo no llegó a mover nada"

    assert regla_portada.publicadas(movido)["titular"] == "1 de 1"
    assert regla_portada.publicadas(html)["titular"] != "1 de 1", "y con la buena, la buena"


def test_el_bloque_corto_lleva_el_titular_con_su_panel_y_la_errata(
    informe: dict[str, object],
) -> None:
    """La versión corta puede recortar lo que sea **menos** las tres cosas que impiden
    leer mal el resto: el panel, la no comparabilidad de las notas y la errata."""
    todas = cifras(informe, del_repo(RAIZ))

    corto = bloque_corto(todas, "docs/index.html")

    for clave in ("titular", "panel", "cobertura_min", "cobertura_max", "errata_antes"):
        assert todas[clave].valor in corto, f"la versión corta se dejó `{clave}`"
    assert f"~~{todas['errata_antes'].valor}~~" in corto, "el número viejo va TACHADO, no borrado"


def test_cada_cifra_dice_de_donde_sale(informe: dict[str, object]) -> None:
    """`Cifra.fuente` no es documentación: es el argumento de R9 cuando se pone roja. Una
    cifra sin fuente convierte «sale del JSON» en una afirmación sobre la página entera y
    sobre ninguna cifra concreta."""
    todas = cifras(informe, del_repo(RAIZ))

    assert todas
    assert all(c.fuente.startswith(("informe.json:", "censo:")) for c in todas.values())


def test_la_pagina_no_puede_imprimir_una_clave_que_no_existe(informe: dict[str, object]) -> None:
    """**Revienta en vez de imprimir un hueco.** Un `KeyError` en la generación es barato;
    un número que falta en la portada no se ve, y el hueco se lee como que no lo hay."""
    with pytest.raises(KeyError):
        _titular({k: v for k, v in cifras(informe, del_repo(RAIZ)).items() if k != "titular"})


def test_las_dos_salidas_publicadas_coinciden_con_el_informe(informe: dict[str, object]) -> None:
    """**La barrera de la rancidez, y va EN PROCESO a propósito.**

    Que la portada la *genere* un comando no basta: un generador que nadie corre deja el
    fichero viejo igual, y encima con la apariencia de estar derivado. Es el README otra
    vez, que estuvo **33 commits** publicando «Hito L0 de 10» con cuatro hitos cerrados.

    **Por qué aquí y no corriendo `docbench portada` en un subproceso**, que es lo que
    hacía la primera versión: `scripts/derivadas.py` —que la puerta ya ejecuta— lleva
    dentro la regla R9, y R9 **ya compara `docs/index.html`** contra el informe. El
    subproceso duplicaba esa mitad y sólo aportaba la otra, el bloque del README. Dos
    procesos de Python para lo que hace una comparación de cadenas es la clase de coste
    que ADR-0022 manda buscar **antes** de tocar el techo.

    Se reconstruye con **el mismo prefijo de enlaces que usa el comando**, que sale de
    `git remote`: comparar contra una página construida con enlaces relativos daría un
    rojo por la URL y no por ninguna cifra.
    """
    ext: dict[str, dict[str, float]] = informe["extractores"]  # type: ignore[assignment]
    orden = sorted(ext, key=lambda n: -float(ext[n]["teds"]))
    todas = cifras(informe, del_repo(RAIZ))
    remoto = _remoto(RAIZ)
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    i, j = readme.index(INICIO), readme.index(FIN) + len(FIN)

    assert (RAIZ / "docs" / "index.html").read_text(encoding="utf-8") == pagina(
        todas, orden, remoto
    ), "docs/index.html está rancio. Regenéralo: uv run docbench portada --escribir"
    assert readme[i:j] == bloque_corto(todas, _pagina_publicada(remoto, Path("docs/index.html"))), (
        "el bloque PORTADA del README está rancio: uv run docbench portada --escribir"
    )
