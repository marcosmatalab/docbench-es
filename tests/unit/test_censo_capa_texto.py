"""El censo de páginas sin capa de texto, **con su control negativo delante**.

El censo dio **0 de 10.298 páginas** sobre el corpus entero, y un cero es exactamente el
resultado que hay que desconfiar: un censo roto también da cero. Por eso el primer test de
este fichero no es que cuente bien las páginas con texto, sino que **encuentre una que no
lo tiene** — un PDF con líneas dibujadas y ni un operador de texto.

Y por eso el instrumento es `pypdf` y no `pymupdf` ni `pdfplumber`: `pyproject.toml` lo
declara desde L3 como preparación de corpus y no como extractor del banco. Preguntarle a
un concursante si el examen estaba en blanco no vale.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import _pdf_minimo as pdfs

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_capa_texto import UMBRAL_POBRE, censar, resumen  # noqa: E402


def _corpus(tmp_path: Path, **documentos: bytes) -> Path:
    for nombre, datos in documentos.items():
        (tmp_path / f"{nombre}.pdf").write_bytes(datos)
    return tmp_path


def test_encuentra_una_pagina_sin_capa_de_texto(tmp_path: Path) -> None:
    """**El control negativo, y va primero.** Sin él, «0 de 10.298» sería indistinguible
    de un censo que no mira nada."""
    docs = _corpus(tmp_path, escaneado=pdfs.sin_capa_de_texto())
    censo = censar(["escaneado"], docs)
    assert [(d.paginas, d.sin_texto) for d in censo] == [(1, 0 + 1)]


def test_una_pagina_con_texto_no_cuenta_como_sin_texto(tmp_path: Path) -> None:
    """El control positivo. Los dos hacen falta: uno solo deja pasar un censo constante."""
    docs = _corpus(tmp_path, digital=pdfs.solo_texto())
    censo = censar(["digital"], docs)
    assert [(d.paginas, d.sin_texto) for d in censo] == [(1, 0)]


def test_el_resumen_cuadra_los_denominadores(tmp_path: Path) -> None:
    """`documentos_con_alguna_pagina_sin_texto` y `documentos_enteros_sin_texto` son cosas
    distintas, y confundirlas es la forma barata de publicar un número más bonito."""
    docs = _corpus(
        tmp_path, uno=pdfs.sin_capa_de_texto(), dos=pdfs.solo_texto(), tres=pdfs.con_tabla()
    )
    r = resumen(censar(["uno", "dos", "tres"], docs))
    assert r.documentos == 3
    assert r.paginas == 3
    assert r.paginas_sin_texto == 1
    assert r.con_alguna_pagina_sin_texto == 1
    assert r.enteros_sin_texto == 1


def test_un_pdf_que_no_se_puede_abrir_no_desaparece_del_denominador(tmp_path: Path) -> None:
    """Un documento que revienta al abrirse **se cuenta con cero páginas**. Saltárselo
    encogería el denominador del censo sin que nadie lo viera."""
    docs = _corpus(tmp_path, malo=pdfs.roto())
    censo = censar(["malo"], docs)
    assert len(censo) == 1
    assert censo[0].paginas == 0
    assert resumen(censo).documentos == 1
    assert resumen(censo).ilegibles == 1, "y en su propia fila, no entre los cortos"


def test_el_umbral_de_pagina_pobre_es_una_segunda_cifra_y_no_un_criterio() -> None:
    """El número que manda es el de CERO caracteres, que no depende de ningún umbral
    elegido por nadie. `UMBRAL_POBRE` se publica al lado, no en su lugar."""
    assert UMBRAL_POBRE > 0
    assert isinstance(UMBRAL_POBRE, int)


@pytest.mark.parametrize("ident", ["no-existe"])
def test_un_documento_que_no_esta_en_disco_se_salta(tmp_path: Path, ident: str) -> None:
    """Distinto del anterior: aquí no hay fichero, así que no hay nada que censar. El
    denominador del censo son los documentos ENCONTRADOS, y el del manifiesto lo publica
    `verificar_corpus.py`."""
    assert censar([ident], tmp_path) == []
