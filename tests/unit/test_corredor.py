"""El corredor: **lo que hace que una corrida de cuatro horas no se pierda.**

Dos cosas se afirman aquí, y las dos se demuestran **matando la corrida a mitad**, no
leyendo el código:

1. **El sello se escribe ANTES de la primera unidad.** Si se escribiera al terminar, lo
   que quedara en disco tras una caída no sabría de qué árbol venía, y sería
   indistinguible de un resultado sobre un árbol que ya nadie tiene.
2. **El punto de control es el resultado.** Cada unidad se anota en cuanto termina, así
   que reanudar es saltarse lo que ya tiene línea. No hay un `estado.json` que pueda
   desincronizarse del resultado, porque no hay un `estado.json`.

Y una tercera que sale de las dos: **reanudar sobre un árbol distinto se rechaza**. Es la
regla que `scripts/medir_puerta.py` ya aplica a la puerta, y aquí muerde más porque las
dos mitades acabarían en el mismo fichero y en la misma media.

El formato del diario y el contenido del sello se comprueban en `test_diario.py`.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from benchcore.types import Cost, ProbeResult

from _corpus_falso import unos_cuantos
from docbench_es.errors import ContractViolation
from docbench_es.extract import corredor as mod
from docbench_es.extract._salida import extraccion
from docbench_es.extract.base import FamiliaExtractor
from docbench_es.extract.corredor import Resumen, correr
from docbench_es.extract.diario import Diario
from docbench_es.types import (
    Extraction,
    ExtractionFailure,
    RawDoc,
)

IDS = [f"BOE-A-2026-{1000 + i}" for i in range(5)]


class _Extractor:
    """Un extractor de mentira que se puede hacer caer donde uno quiera."""

    kind: FamiliaExtractor = "parser"
    runs_locally = True
    expresses_spans = False
    benchcore_api = "1.x"

    def __init__(self, ident: str = "falso", revienta_en: str | None = None) -> None:
        self.id = ident
        self.version = "0.0+ad0"
        self.revienta_en = revienta_en
        self.vistos: list[str] = []
        self.sellos_al_extraer: list[bool] = []
        self.destino: Path | None = None

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        self.vistos.append(doc.ref.external_id)
        if self.destino is not None:
            self.sellos_al_extraer.append((self.destino / "sello.json").exists())
        if doc.ref.external_id == self.revienta_en:
            raise RuntimeError("me caigo aquí, como se cae una corrida de verdad")
        cae = doc.ref.external_id.endswith("3")
        causa: ExtractionFailure | None = "corrupt_pdf" if cae else None
        return extraccion(self, doc, time.perf_counter(), "dataframe", causa=causa, detalle="x")

    def cost_of(self, ex: Extraction) -> Cost:
        return ex.cost

    def probe(self) -> ProbeResult:
        return ProbeResult(component_id=self.id, status="OK")


# ────────────────────────────────── el corredor ──────────────────────────────


def test_el_sello_ya_esta_escrito_cuando_corre_la_primera_unidad(tmp_path: Path) -> None:
    """**La afirmación entera, comprobada desde dentro de la extracción.**

    El extractor mira si el sello existe cada vez que lo llaman. Si se escribiera al
    terminar, la primera respuesta sería `False`.
    """
    destino = tmp_path / "corrida"
    extractor = _Extractor()
    extractor.destino = destino
    correr(
        [extractor],
        unos_cuantos(tmp_path, 5),
        IDS,
        destino,
        que="t",
        entradas={},
        eco=lambda _: None,
    )
    assert extractor.sellos_al_extraer == [True] * 5


def test_una_corrida_que_se_cae_deja_hechas_las_unidades_que_termino(tmp_path: Path) -> None:
    """El punto de control **es** el resultado: lo anotado antes de la caída está."""
    destino = tmp_path / "corrida"
    almacen = unos_cuantos(tmp_path, 5)
    with pytest.raises(RuntimeError, match="me caigo"):
        correr(
            [_Extractor(revienta_en=IDS[2])],
            almacen,
            IDS,
            destino,
            que="t",
            entradas={},
            eco=lambda _: None,
        )
    assert (destino / "sello.json").exists(), "el sello se escribió antes de empezar"
    assert Diario(destino / "falso.jsonl").hechos() == {IDS[0], IDS[1]}


def test_reanudar_se_salta_lo_que_ya_tenia_linea(tmp_path: Path) -> None:
    """Y **no lo vuelve a extraer**: se comprueba sobre lo que el extractor llegó a ver."""
    destino = tmp_path / "corrida"
    almacen = unos_cuantos(tmp_path, 5)
    with pytest.raises(RuntimeError):
        correr(
            [_Extractor(revienta_en=IDS[2])],
            almacen,
            IDS,
            destino,
            que="t",
            entradas={},
            eco=lambda _: None,
        )
    segundo = _Extractor()
    resumen = correr([segundo], almacen, IDS, destino, que="t", entradas={}, eco=lambda _: None)[0]
    assert segundo.vistos == IDS[2:], "volvió a extraer algo que ya estaba"
    assert (resumen.reanudadas, resumen.hechas) == (2, 3)
    assert len(Diario(destino / "falso.jsonl").hechos()) == 5


def test_reanudar_sobre_otro_arbol_se_rechaza(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Una campaña medida mitad sobre un árbol y mitad sobre otro **no es una campaña**."""
    destino = tmp_path / "corrida"
    almacen = unos_cuantos(tmp_path, 5)
    correr([_Extractor()], almacen, IDS[:2], destino, que="t", entradas={}, eco=lambda _: None)
    monkeypatch.setattr(mod, "arbol", lambda: {"commit": "otro", "sucios": 0, "huella": "x" * 16})
    with pytest.raises(ContractViolation, match="otro árbol"):
        correr([_Extractor()], almacen, IDS, destino, que="t", entradas={}, eco=lambda _: None)


def test_el_fallo_de_un_documento_se_cuenta_por_causa_y_no_para_la_corrida(tmp_path: Path) -> None:
    """La tasa de fallo por extractor es **un resultado**, no un detalle. Regla de oro 6."""
    destino = tmp_path / "corrida"
    resumen = correr(
        [_Extractor()],
        unos_cuantos(tmp_path, 5),
        IDS,
        destino,
        que="t",
        entradas={},
        eco=lambda _: None,
    )[0]
    assert resumen.hechas == 5, "un fallo no para la corrida"
    assert resumen.por_causa == {"corrupt_pdf": 1}
    assert "corrupt_pdf=1" in str(resumen)
    assert "de 5" in str(resumen), "el denominador va en el resumen"


def test_una_campana_sin_extractores_es_un_error_y_no_una_campana_vacia(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation, match="sin extractores"):
        correr([], unos_cuantos(tmp_path, 1), IDS[:1], tmp_path / "c", que="t", entradas={})


def test_el_resumen_de_una_corrida_sin_documentos_no_divide_por_cero() -> None:
    """Caso degenerado: `n/a` no es `0.0%`. Una tasa sobre cero documentos no existe."""
    assert "n/a" in str(Resumen(extractor="x", version="1", pedidas=0))
