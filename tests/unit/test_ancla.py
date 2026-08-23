"""La precondición que impide editar un documento publicado por un ancla ambigua.

Ver `scripts/ancla.py`: de las dos formas de fallar, duplicar se ve y **borrar
no**. Por eso lo que se fija aquí no es el resultado de la edición sino la
precondición, que es lo único que cubre las dos mitades.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from ancla import unica  # noqa: E402

PUBLICADOS = ("RESULTS.md", "LIMITS.md", "ESTADO.md", "CHANGELOG.md", "metrics.md")


def test_unica_devuelve_el_indice_cuando_el_ancla_es_ambigua_no() -> None:
    assert unica("antes<CORTE>despues", "<CORTE>") == 5


def test_el_ancla_real_que_rompio_results_aborta_sobre_el_documento_real() -> None:
    """El caso de L2, con su documento y su ancla, no una imitación.

    `### El coste en la puerta` es un encabezado **por hito**, así que aparece dos
    veces en `RESULTS.md` y seguirá apareciendo más conforme haya más hitos. Un
    `s.index` sobre él corta por el de L1 y duplica todo lo que hay hasta L2: fue
    exactamente eso, y fueron ~230 líneas.

    Este test se mantiene solo: cuanto más crece `RESULTS.md`, más cierto es.
    """
    texto = (RAIZ / "RESULTS.md").read_text(encoding="utf-8")
    assert texto.count("### El coste en la puerta") >= 2, "si baja a 1, el caso ya no discrimina"
    with pytest.raises(SystemExit, match="no se edita nada"):
        unica(texto, "### El coste en la puerta")


def test_un_ancla_que_no_existe_aborta_en_vez_de_borrar_hasta_el_final() -> None:
    """La mitad invisible: cero apariciones.

    `find()` devuelve -1 y `s[:-1]` recorta en silencio; `index()` revienta pero
    sólo si nadie lo envuelve en un `try`. Las dos acaban en un documento al que
    le falta algo, y **lo que falta no se nota leyendo**. Por eso el cero es un
    error tan duro como el dos.
    """
    with pytest.raises(SystemExit, match="aparece 0 veces"):
        unica("un documento cualquiera", "### Un encabezado que ya no está")


def _escribe_en_publicado(fuente: str) -> bool:
    """¿Este código escribe en un documento publicado? Por AST, no por grep."""
    arbol = ast.parse(fuente)
    for n in ast.walk(arbol):
        constantes = [c.value for c in ast.walk(n) if isinstance(c, ast.Constant)]
        nombra = any(isinstance(c, str) and c.endswith(PUBLICADOS) for c in constantes)
        escribe = isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Attribute) and n.func.attr in ("write_text", "write"))
            or (isinstance(n.func, ast.Name) and n.func.id == "open")
        )
        if escribe and nombra:
            return True
    return False


def test_el_detector_de_escrituras_sabe_decir_que_si() -> None:
    """Control negativo del test de abajo, que hoy pasa por lista vacía.

    Sin esto, un detector roto daría la misma luz verde que un repo limpio.
    """
    assert _escribe_en_publicado('Path("RESULTS.md").write_text(s)')
    assert not _escribe_en_publicado('Path("casos.json").write_text(s)')


def test_ningun_script_versionado_edita_un_publicado_sin_pasar_por_unica() -> None:
    """La regla «va en todos», comprobada en vez de recordada.

    Hoy **ningún script versionado edita un documento publicado**: el que rompió
    `RESULTS.md` era de un solo uso. Este test no vigila el presente, vigila el
    día que alguien versione uno — y ese día le obliga a importar `unica` antes de
    que el ancla ambigua vuelva a costar 230 líneas.
    """
    culpables = [
        str(p.relative_to(RAIZ))
        for p in (RAIZ / "scripts").rglob("*.py")
        if _escribe_en_publicado(p.read_text(encoding="utf-8"))
        and "from ancla import" not in p.read_text(encoding="utf-8")
    ]
    assert culpables == [], f"editan un documento publicado sin la precondición: {culpables}"
