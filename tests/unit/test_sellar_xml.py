"""Que la captura de hashes de los XML **sea completa o lo diga**.

El manifiesto pone hash al PDF y no al XML (límite 62), y el XML es la verdad de
referencia contra la que se puntúa a todos los extractores: la mitad menos
protegida del par es la que decide quién gana. Meter el campo en el esquema es L4;
**capturar el hash no puede esperar**, porque lo que separa una captura buena de
una mala es el hueco entre la descarga y el hash.

De ahí los dos aros de este fichero, y los dos son de la misma familia: una
captura que se presenta como completa sin serlo, y una captura que se rehace sobre
bytes que ya no son los que se bajaron.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from sellar_xml import capturar  # noqa: E402


def _corpus(tmp: Path, n: int = 3) -> tuple[dict[str, object], Path]:
    docs = tmp / "docs"
    docs.mkdir()
    for i in range(n):
        (docs / f"BOE-A-2026-{i:05d}.xml").write_bytes(f"<doc>{i}</doc>".encode())
    return {"documentos": [{"external_id": f"BOE-A-2026-{i:05d}"} for i in range(n)]}, docs


def test_la_captura_dice_cuando_y_sobre_que_arbol_se_tomo(tmp_path: Path) -> None:
    """**Un hash sin fecha no dice nada.** No distingue «tomado al bajarlo» de
    «tomado seis meses después», que es justo la diferencia que hace que esta
    captura valga o no valga: el hueco entre la descarga y el hash.

    Y el commit por la misma razón que el sello de cualquier medición del repo: la
    fecha no delata un árbol que se movió; el hash de `HEAD` sí.
    """
    manifiesto, docs = _corpus(tmp_path)

    captura = capturar(manifiesto, docs)

    assert captura["sellados"] == 3
    assert str(captura["tomado_en"]).startswith("20")
    assert captura["sello"], "sin sello no se sabe sobre qué árbol se tomó"


def test_un_xml_que_falta_no_se_salta_en_silencio(tmp_path: Path) -> None:
    """El control negativo: **una captura incompleta que se presenta como completa
    es la misma familia que un manifiesto sin sus bytes.**

    Y el conteo tiene que quedar desparejado a la vista —`sellados` contra
    `documentos_en_manifiesto`—, no sólo apuntado en una lista que nadie mira.
    """
    manifiesto, docs = _corpus(tmp_path)
    (docs / "BOE-A-2026-00001.xml").unlink()

    captura = capturar(manifiesto, docs)

    assert captura["faltan"] == ["BOE-A-2026-00001"]
    assert captura["sellados"] == 2
    assert captura["documentos_en_manifiesto"] == 3, "el denominador NO se encoge"


def test_se_sella_el_manifiesto_no_el_directorio(tmp_path: Path) -> None:
    """Un XML suelto en la carpeta **no es parte del corpus**.

    Recorrer el directorio en vez del manifiesto daría una cuenta que no cuadra con
    ninguna otra cifra del hito, y sellaría como corpus lo que sólo es un fichero
    que alguien dejó ahí.
    """
    manifiesto, docs = _corpus(tmp_path)
    (docs / "BOE-A-2026-99999.xml").write_bytes(b"<intruso/>")

    captura = capturar(manifiesto, docs)

    assert captura["sellados"] == 3
    assert "BOE-A-2026-99999" not in json.dumps(captura)


def test_no_se_rehace_una_captura_que_ya_existe(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """**El aro que hace de «se pliega, no se recalcula» un mecanismo.**

    Rehacer la captura en L4 tomaría el hash de los bytes de ese día, no de los que
    se bajaron: bendeciría para siempre un fichero ya sustituido, que es peor que
    no tener hash — porque a partir de ahí la comprobación diría que todo cuadra.
    Refijar a propósito exige `--refijar` con su razón.
    """
    import sellar_xml

    manifiesto, _ = _corpus(tmp_path)
    ruta = tmp_path / "manifiesto.json"
    ruta.write_text(json.dumps(manifiesto), encoding="utf-8")
    (tmp_path / "xml_sha256.json").write_text('{"tomado_en": "2026-08-24"}', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["sellar_xml.py", str(ruta)])

    assert sellar_xml.main() == 1
    assert "YA EXISTE" in capsys.readouterr().out
