"""El diario y el sello: **cómo se persiste una corrida y sobre qué árbol se midió.**

Dos afirmaciones que sostienen números publicados:

* **una `Extraction` sobrevive la ida y la vuelta entera.** `.importlinter` protege que
  *«el núcleo es puro: se puede reejecutar sobre extracciones viejas»*, y eso exige poder
  RECONSTRUIR, no sólo escribir un resumen. La comparación es del objeto completo: un
  formato que perdiera la `caption` o el `page_span` pasaría una comparación escrita a
  mano campo por campo;
* **lo que no se pudo leer se cuenta y viaja pegado al resultado.** Una línea cortada
  —el corte de una corrida que murió escribiendo— se salta, porque en la reanudación esa
  unidad se rehízo; saltársela en silencio encogería el denominador sin que nadie se
  entere.

Y el sello contesta *«¿de qué árbol venía esto?»* para una corrida interrumpida, que es
la pregunta que no se puede contestar si se escribe al terminar.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from benchcore.types import Cost, ProbeResult, TokenUsage

from _corpus_falso import unos_cuantos
from docbench_es.errors import ContractViolation
from docbench_es.extract._salida import extraccion
from docbench_es.extract.base import FamiliaExtractor
from docbench_es.extract.diario import Diario, a_json, de_json
from docbench_es.extract.sello import arbol, git, sello_de_corrida
from docbench_es.types import (
    CanonicalCell,
    CanonicalTable,
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


# ─────────────────────────────────── el sello ────────────────────────────────


def test_el_arbol_lleva_commit_sucios_y_huella() -> None:
    """El commit solo engaña sobre un árbol sucio, y el recuento de sucios engaña más
    fino: editar un fichero que ya estaba sucio no mueve el número."""
    a = arbol()
    assert set(a) == {"commit", "sucios", "huella"}
    assert isinstance(a["huella"], str) and len(str(a["huella"])) == 16


def test_git_que_falla_dice_interrogante_y_no_cadena_vacia() -> None:
    """Una cadena vacía se cuenta como cero ficheros sucios: **un árbol sucio con cara de
    limpio**, que es justo lo que el sello existe para no dejar pasar."""
    assert git("no-es-un-subcomando-de-git") == "?"


def test_el_sello_lleva_la_huella_de_cada_entrada(tmp_path: Path) -> None:
    """Dos corridas del mismo commit sobre poblaciones distintas no son la misma corrida."""
    uno = tmp_path / "a.json"
    uno.write_text("[1]", encoding="utf-8")
    s = sello_de_corrida("prueba", {"pob": uno, "no_esta": tmp_path / "b.json"})
    entradas = json.loads(json.dumps(s))["entradas"]
    assert entradas["pob"]["sha256"] != "(no existe)"
    assert entradas["no_esta"]["sha256"] == "(no existe)"


# ─────────────────────────────────── el diario ───────────────────────────────


def _tabla() -> CanonicalTable:
    return CanonicalTable(
        cells=(
            CanonicalCell(row=0, col=0, text="a", rowspan=2, is_header=True),
            CanonicalCell(row=0, col=1, text="b"),
            CanonicalCell(row=1, col=1, text="c"),
        ),
        n_rows=2,
        n_cols=2,
        page_span=(3, 4),
        caption="pie",
        expresses_spans=True,
        source_format="html",
    )


def _extraccion(doc: RawDoc) -> Extraction:
    ex = extraccion(_Extractor(), doc, time.perf_counter(), "html", texto="hola", avisos=("a",))
    coste = Cost(
        eur=Decimal("0.0001234"),
        usd=Decimal("0.00013"),
        tokens=TokenUsage(input_uncached=7, output=3),
        price_table="tarifa-2026",
        fx_rate=Decimal("1.08"),
        estimated=True,
        measured=False,
        wall_ms=42,
    )
    return replace(ex, tables=(_tabla(),), cost=coste)


def test_una_extraccion_sobrevive_la_ida_y_la_vuelta_entera(tmp_path: Path) -> None:
    """**Sin esto, «el núcleo se puede reejecutar sobre extracciones viejas» es una frase.**

    Se compara el objeto entero, no campo a campo elegido: un formato que perdiera la
    `caption` o el `page_span` pasaría una comparación escrita a mano.
    """
    doc = unos_cuantos(tmp_path, 1).cargar(IDS[0])
    original = _extraccion(doc)
    assert de_json(json.loads(json.dumps(a_json(original)))) == original


def test_el_dinero_viaja_como_cadena_y_vuelve_como_decimal(tmp_path: Path) -> None:
    """Un `float` en el JSON convertiría el dinero en coma flotante al leerlo."""
    doc = unos_cuantos(tmp_path, 1).cargar(IDS[0])
    crudo = json.loads(json.dumps(a_json(_extraccion(doc))))
    assert crudo["cost"]["eur"] == "0.0001234", "un float convertiría el dinero en binario"
    vuelta = de_json(crudo)
    assert isinstance(vuelta.cost.eur, Decimal)


def test_una_causa_que_no_es_del_enum_cerrado_no_se_reconstruye(tmp_path: Path) -> None:
    """Si no, el informe contaría un fallo en una fila que nadie declaró."""
    doc = unos_cuantos(tmp_path, 1).cargar(IDS[0])
    crudo = a_json(_extraccion(doc))
    crudo["failed"], crudo["failure_reason"] = True, "vete-a-saber"
    with pytest.raises(ContractViolation, match="enum cerrado"):
        de_json(crudo)


def test_un_campo_que_falta_levanta_diciendo_cual(tmp_path: Path) -> None:
    """Un diario a medias no se cuela como una extracción a medias."""
    doc = unos_cuantos(tmp_path, 1).cargar(IDS[0])
    crudo = a_json(_extraccion(doc))
    crudo["cost"] = "esto no es un objeto"
    with pytest.raises(ContractViolation, match="cost"):
        de_json(crudo)


def test_una_linea_cortada_a_mitad_no_cuenta_como_hecha(tmp_path: Path) -> None:
    """El corte de una corrida que murió escribiendo. **Media línea es media extracción**,
    así que se descarta y se rehace en vez de darse por buena."""
    ruta = tmp_path / "d.jsonl"
    doc = unos_cuantos(tmp_path, 1).cargar(IDS[0])
    diario = Diario(ruta)
    diario.anotar(_extraccion(doc))
    with ruta.open("a", encoding="utf-8") as f:
        f.write('{"extractor_id": "falso", "doc_ref": {"exter')
    assert diario.hechos() == {IDS[0]}
    leido = diario.leer()
    assert (len(leido.extracciones), leido.ilegibles) == (1, 1)
    assert "1 líneas ilegibles" in str(leido), "el descarte viaja pegado al resultado"


def test_un_documento_con_dos_lineas_no_se_lee_como_un_dato_de_mas(tmp_path: Path) -> None:
    """El bootstrap remuestrea DOCUMENTOS (regla de oro 3): uno repetido estrecha el
    intervalo y publica más precisión de la que hay."""
    ruta = tmp_path / "d.jsonl"
    doc = unos_cuantos(tmp_path, 1).cargar(IDS[0])
    diario = Diario(ruta)
    diario.anotar(_extraccion(doc))
    diario.anotar(_extraccion(doc))
    with pytest.raises(ContractViolation, match="más de una línea"):
        diario.leer()
