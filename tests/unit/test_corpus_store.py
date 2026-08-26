"""El almacén: del manifiesto de L3 a los `RawDoc` que come un extractor.

Lo que estos tests demuestran no es que sepa leer un JSON, sino **que el `sha256` se
rehace de verdad en cada carga y que un corpus que cambió por debajo para la campaña en
vez de puntuarla**. Un corpus movido no da un error: da otro número, con la misma pinta
que el bueno, y una campaña de cuatro horas no puede tener una garantía más floja que el
verificador de L3 — cuyo CUMPLE incluye rehacer los 1.000 hashes contra los bytes.

Se monta un corpus de juguete en `tmp_path` en vez de usar `runs/l3`: el corpus real no
está en git (LIMITS 74), así que un test que dependiera de él no correría en la puerta —
y es justo aquí donde hace falta que corra.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from _corpus_falso import contenido_de, unos_cuantos
from docbench_es.corpus.store import Almacen
from docbench_es.errors import ContractViolation


def test_carga_un_documento_entero_con_lo_que_dice_el_manifiesto(tmp_path: Path) -> None:
    """**El control positivo, y sin él lo de abajo no significa nada**: una comprobación
    que siempre levanta pasaría todos los tests de «levanta»."""
    almacen = unos_cuantos(tmp_path)
    doc = almacen.cargar("BOE-A-2026-1001")
    assert doc.ref.key() == "boe/BOE-A-2026-1001"
    assert doc.primary == contenido_de("BOE-A-2026-1001")
    assert doc.n_pages == 2
    assert doc.primary_mime == "application/pdf"
    assert doc.sha256 == hashlib.sha256(doc.primary).hexdigest()
    assert doc.companions["xml"] == b"<doc/>"


def test_un_pdf_que_cambio_por_debajo_para_la_campana(tmp_path: Path) -> None:
    """No es una nota mala: es un número **no atribuible** a ese manifiesto."""
    almacen = unos_cuantos(tmp_path)
    (almacen.docs / "BOE-A-2026-1000.pdf").write_bytes(b"%PDF-1.4\notros bytes\n%%EOF")
    with pytest.raises(ContractViolation) as caido:
        Almacen(almacen.ruta, almacen.docs).cargar("BOE-A-2026-1000")
    assert "sha256" in str(caido.value)
    assert "BOE-A-2026-1000" in str(caido.value)


def test_un_documento_del_manifiesto_que_no_esta_en_disco(tmp_path: Path) -> None:
    """Un corpus incompleto no da una nota mala: da **un denominador falso**."""
    almacen = unos_cuantos(tmp_path)
    (almacen.docs / "BOE-A-2026-1002.pdf").unlink()
    with pytest.raises(ContractViolation, match="denominador"):
        almacen.cargar("BOE-A-2026-1002")


def test_pedir_uno_que_el_manifiesto_no_declara(tmp_path: Path) -> None:
    almacen = unos_cuantos(tmp_path)
    with pytest.raises(ContractViolation, match="3 documentos"):
        almacen.cargar("BOE-A-2026-9999")


def test_recorrer_va_en_el_orden_del_manifiesto_y_uno_a_uno(tmp_path: Path) -> None:
    """Perezoso: los 616 de la campaña son ~360 MB y el corredor procesa uno, escribe su
    punto de control y lo suelta."""
    almacen = unos_cuantos(tmp_path)
    assert len(almacen) == 3
    assert [d.ref.external_id for d in almacen.recorrer()] == almacen.ids()
    pedidos = ["BOE-A-2026-1002", "BOE-A-2026-1000"]
    assert [d.ref.external_id for d in almacen.recorrer(pedidos)] == pedidos


def test_sin_xml_al_lado_el_documento_se_carga_igual(tmp_path: Path) -> None:
    """El acompañante es opcional: un extractor sólo necesita el PDF."""
    almacen = unos_cuantos(tmp_path, con_xml=False)
    assert almacen.cargar("BOE-A-2026-1000").companions == {}


def test_las_entradas_se_pueden_mirar_sin_leer_360_mb(tmp_path: Path) -> None:
    """`Entrada` existe para decidir QUÉ se procesa —por sección, estrato o páginas— sin
    abrir los bytes antes de saberlo."""
    almacen = unos_cuantos(tmp_path)
    largos = [e.external_id for e in almacen.entradas if (e.n_pages or 0) >= 2]
    assert largos == ["BOE-A-2026-1001", "BOE-A-2026-1002"]
    assert almacen.entradas[0].estratos == frozenset({"sin-tabla"})
    assert almacen.entradas[0].seccion == "3"
