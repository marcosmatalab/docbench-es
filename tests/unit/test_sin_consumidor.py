"""Lo que está construido pero NO VALIDADO, y la barrera que lo mantiene fuera.

**El patrón que lo motiva.** El hito que ESCRIBE un módulo no encuentra los bugs
que encuentra el hito que lo CONSUME. Caso medido: L1 cerró en verde con
`from_html` y fue L2, al construir el árbol de TEDS, quien descubrió que no
marcaba como cabecera un `<td>` dentro de `<thead>` — el **100%** de las
cabeceras de PubTabNet mal marcadas.

De los cinco conversores de §9.1, **sólo `from_html` tiene consumidor real**. Los
otros cuatro están escritos, tienen tests propios y **nadie los ha usado para
producir nada**. Su primer consumidor real llega en **L5**, con los ocho
extractores: `pymupdf4llm` y `marker` emiten Markdown, `camelot` DataFrames,
`grobid` TEI y `tesseract` texto plano.

Hasta entonces se marcan **NO VALIDADOS** y **ninguna cifra publicada puede pasar
por ellos**. Esto no es una nota en `LIMITS.md`: es un test que lo impide, porque
una prohibición que se comprueba leyendo es una prohibición que se rompe sin que
nadie se entere.
"""

from __future__ import annotations

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

SIN_CONSUMIDOR = frozenset({"from_markdown", "from_dataframe", "from_tei", "from_text_heuristic"})
"""Los cuatro conversores de §9.1 que nadie usa todavía. Su hito es L5."""

CAMPOS_SIN_LECTOR = frozenset({"page_span", "caption"})
"""Campos de `CanonicalTable` que ninguna métrica lee. `page_span` además no está
medido (LIMITS 32): lo pone quien llama."""

# Dónde SÍ pueden aparecer: donde se definen y se reexportan. En ningún otro
# sitio de `src/`, y en ninguno de los scripts que producen un número publicado.
PERMITIDOS = (
    "core/canonical/_markdown.py",
    "core/canonical/_dataframe.py",
    "core/canonical/_tei.py",
    "core/canonical/_texto.py",
    "core/canonical/__init__.py",
)

# Antes esto era una tupla de tres nombres escrita a mano, y la afirmación de
# `LIMITS.md` 49 era más ancha que el test: decía «los scripts que producen
# números publicados» cuando miraba tres de siete. `sondeo_boe.py`,
# `mutantes/matar.py` y `medir_puerta.py` publican números en `RESULTS.md` y no se
# miraban. Ahora se recorren TODOS, que además es el patrón que ya usaba
# `test_ancla.py`: una lista a mano es una lista que se queda corta en silencio.
SCRIPTS = sorted((RAIZ / "scripts").rglob("*.py"))


def _llamadas(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    return {
        n.func.id
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }


def _atributos(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    return {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}


def test_ninguna_ruta_que_publica_un_numero_toca_los_conversores_sin_validar() -> None:
    """**La barrera de la decisión (b), comprobada por AST y no por lectura.**

    Si un número publicado pasara por un conversor que nadie ha ejercitado sobre
    datos reales, ese número heredaría un fallo del tipo del `is_header`: presente
    en el 100% de los casos y invisible porque nada lo consumía.

    El día que L5 les dé consumidor, este test se cae y **obliga a quitarlos de la
    lista a mano**, que es justo el momento en que hay que decidir si ya están
    validados.

    **QUÉ DETECTA Y QUÉ NO** —el paso 6 del guion de `/hito` aplicado a este
    mismo test, porque un test que no declara su alcance es una garantía que
    alguien va a leer de más—:

    *Detecta*: una llamada literal `from_markdown(...)` en `src/` o en los
    scripts que publican números.

    *No detecta*: **despacho dinámico**. Un `getattr(canonical, nombre)`, un
    diccionario `{"markdown": from_markdown}`, un registro por `entry_points` o
    un `importlib.import_module` pasan por delante sin que se entere, porque en
    el AST no hay ningún nodo `Call` con ese nombre.

    *Por qué aun así vale hoy*: **comprobado, no supuesto**. En `src/` hay un solo
    `getattr` —`types/_inmutable.py`, y lee campos de una dataclass, no
    funciones—; **ninguna función `from_*` aparece usada como VALOR** en ningún
    sitio; no hay `importlib`, `entry_points` ni `globals()[...]`; y
    `benchcore.registry` no se importa desde `src/`. Verificado por AST sobre
    `src/` y sobre TODOS los `scripts/**.py`, no una lista escrita a mano.

    *Cuándo deja de valer*: **en L5**. `pyproject.toml` ya declara entry points
    para `docbench.extractor`, y un extractor que resolviera su conversor por
    nombre quedaría fuera del alcance de este test. Ese día hay que cambiar la
    comprobación —de sitios de llamada a inspección del registro— o aceptar que
    la barrera dejó de existir y decirlo.
    """
    culpables: dict[str, set[str]] = {}
    fuentes = [
        *(p for p in (RAIZ / "src").rglob("*.py")),
        *SCRIPTS,
    ]
    for ruta in fuentes:
        relativa = str(ruta.relative_to(RAIZ))
        if any(relativa.endswith(p) for p in PERMITIDOS):
            continue
        usados = _llamadas(ruta) & SIN_CONSUMIDOR
        if usados:
            culpables[relativa] = usados

    assert culpables == {}, (
        f"un conversor NO VALIDADO en una ruta que produce números: {culpables}. "
        f"Si ya tiene consumidor real, quítalo de SIN_CONSUMIDOR y dilo en ESTADO.md"
    )


def test_ningun_modulo_de_metricas_lee_page_span_ni_caption() -> None:
    """Demuestra que los dos campos sin lector siguen sin lector.

    `page_span` **no está medido** —lo pone quien llama, LIMITS 32— y `caption`
    no lo lee ninguna métrica. Mientras sea así, se marcan igual que los
    conversores: construidos y no validados.

    Si una métrica empieza a leerlos, este test se cae y obliga a medirlos antes
    de que un número dependa de ellos. Es la misma barrera, aplicada a datos en
    vez de a funciones.
    """
    metricas = [
        *(RAIZ / "src" / "docbench_es" / "core" / "teds").glob("*.py"),
        RAIZ / "src" / "docbench_es" / "core" / "cellmatch.py",
    ]
    lectores = {
        str(m.relative_to(RAIZ)): _atributos(m) & CAMPOS_SIN_LECTOR
        for m in metricas
        if _atributos(m) & CAMPOS_SIN_LECTOR
    }
    assert lectores == {}, f"una métrica lee un campo no validado: {lectores}"


def test_from_html_si_tiene_consumidor_y_por_eso_no_esta_en_la_lista() -> None:
    """El control negativo: la lista no está vacía de contenido por accidente.

    `from_html` **sí** tiene consumidor real —el generador del golden de
    PubTabNet, y en L4 la verdad derivada del BOE—, y por eso no está en
    `SIN_CONSUMIDOR`. Sin esta comprobación, alguien podría vaciar la lista y los
    dos tests de arriba pasarían en verde sin comprobar nada.
    """
    assert "from_html" not in SIN_CONSUMIDOR
    assert len(SIN_CONSUMIDOR) == 4
    generador = _llamadas(RAIZ / "scripts" / "pubtabnet_golden.py")
    assert "from_html" in generador, "el generador del golden lo usa de verdad"
