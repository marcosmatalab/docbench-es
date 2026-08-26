"""La suite de conformidad de extractores, vista ROJA antes de servir de nada.

Un aro que nunca ha rechazado a nadie no es un aro: es una afirmación. Aquí se le pasan
seis extractores de mentira, **cada uno roto de una forma distinta**, y se exige que la
suite los rechace **nombrando la comprobación** — porque un `NO PASA` sin detalle obliga
a leer el código de la suite para saber qué arreglar.

Ninguno de estos vive en `src/`, y eso es la regla de oro 1 en su forma literal: este
repo no construye extractores. Son moldes con la forma del hueco.

## Y el aro que la suite se aplica a sí misma

`test_el_bueno_pasa` es el control positivo. Sin él, una suite que devolviera `FALLA`
siempre pasaría todos los tests de abajo y no serviría para nada.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from benchcore.types import Cost, ProbeResult, TokenUsage

from docbench_es.extract.conformance import Caso, comprobar
from docbench_es.types import CanonicalCell, CanonicalTable, DocRef, Extraction, RawDoc


def _coste(wall_ms: int = 1) -> Cost:
    """Un `Cost` mínimo. `Decimal` y no `float`: la regla de la casa sobre el dinero."""
    return Cost(
        eur=Decimal("0"),
        usd=None,
        tokens=TokenUsage(input_uncached=0, input_cached=0, cache_write=0, output=0, reasoning=0),
        price_table=None,
        fx_table=None,
        fx_rate=None,
        estimated=False,
        measured=True,
        wall_ms=wall_ms,
    )


COSTE = _coste()


def _doc(ident: str) -> RawDoc:
    ref = DocRef(
        entity="boe", external_id=ident, published_on=date(2026, 4, 1), url=None, kind="disposicion"
    )
    return RawDoc(
        ref=ref,
        primary=b"%PDF-1.4 falso",
        primary_mime="application/pdf",
        companions={},
        sha256="0" * 64,
        fetched_at=datetime(2026, 4, 1, tzinfo=UTC),
        n_pages=2,
    )


def _tabla(*, combinadas: bool, formato: str = "html") -> CanonicalTable:
    """2x2. Con `combinadas`, la primera celda ocupa las dos columnas de su fila."""
    celdas: tuple[CanonicalCell, ...]
    if combinadas:
        celdas = (
            CanonicalCell(row=0, col=0, colspan=2, text="cabecera"),
            CanonicalCell(row=1, col=0, text="a"),
            CanonicalCell(row=1, col=1, text="b"),
        )
    else:
        celdas = (
            CanonicalCell(row=0, col=0, text="x"),
            CanonicalCell(row=0, col=1, text="y"),
            CanonicalCell(row=1, col=0, text="a"),
            CanonicalCell(row=1, col=1, text="b"),
        )
    return CanonicalTable(
        cells=celdas,
        n_rows=2,
        n_cols=2,
        page_span=(1, 1),
        caption=None,
        expresses_spans=combinadas,
        source_format=formato,
    )


class _Base:
    """El molde que sí cumple. Los rotos heredan y estropean UNA cosa."""

    id = "falso"
    version = "0"
    kind = "parser"
    runs_locally = True
    expresses_spans = True
    benchcore_api = "1.0"
    formato = "html"
    emite_combinadas = False

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        return Extraction(
            extractor_id=self.id,
            extractor_version=self.version,
            doc_ref=doc.ref,
            text="",
            tables=(_tabla(combinadas=self.emite_combinadas, formato=self.formato),),
            native_format=self.formato,
            pages_processed=1,
            cost=COSTE,
            latency_ms=1,
            warnings=(),
        )

    def cost_of(self, ex: Extraction) -> Cost:
        return COSTE

    def probe(self) -> ProbeResult:
        return ProbeResult(
            component_id=self.id,
            status="OK",
            version="0",
            detail="",
            latency_ms=1,
            checked_at=datetime(2026, 4, 1, tzinfo=UTC),
        )


def _casos(*, con_ocasion: bool = True) -> list[Caso]:
    return [
        Caso(doc=_doc("BOE-A-2026-1"), trae_combinadas=con_ocasion),
        Caso(doc=_doc("BOE-A-2026-2"), trae_combinadas=False),
    ]


def test_el_bueno_pasa() -> None:
    """**El control positivo.** Sin él, una suite que fallara siempre pasaría el resto."""
    informe = comprobar(_Base(), _casos())
    assert informe.pasa, str(informe)
    assert informe.veredicto_spans == "COHERENTE"


def test_sin_documentos_no_pasa_porque_no_se_ha_comprobado_nada() -> None:
    """`NO_EJECUTADA` pesa como fallo: un aro por el que no se ha pasado no está
    superado. Con documentos cero la suite correría entera y saldría verde sin haber
    ejecutado el extractor ni una vez."""
    informe = comprobar(_Base(), [])
    assert not informe.pasa
    assert [h.severidad for h in informe.hallazgos] == ["NO_EJECUTADA"]


def test_sin_ocasion_de_spans_el_honesto_queda_sin_evidencia_y_no_pasa() -> None:
    """El caso que motiva que el conjunto **se elija**: si ningún documento trae celdas
    combinadas en la verdad, un `expresses_spans=False` no se puede confirmar."""

    class _Aplana(_Base):
        expresses_spans = False

    informe = comprobar(_Aplana(), _casos(con_ocasion=False))
    assert informe.veredicto_spans == "SIN_EVIDENCIA"
    assert not informe.pasa, "sin evidencia no es un aprobado"
    assert not informe.hubo_ocasion


def test_con_ocasion_el_mismo_honesto_si_pasa() -> None:
    """La otra mitad, y la que hace que el conjunto elegido valga: **el mismo extractor**,
    cambiando sólo si el conjunto ofrecía ocasión, pasa de no aprobar a aprobar."""

    class _Aplana(_Base):
        expresses_spans = False

    informe = comprobar(_Aplana(), _casos(con_ocasion=True))
    assert informe.veredicto_spans == "COHERENTE"
    assert informe.pasa, str(informe)


def test_declararse_capaz_desde_markdown_es_contradiccion() -> None:
    """Pedir competir en el estrato titular con un formato que no puede expresarlo."""

    class _Miente(_Base):
        formato = "markdown"

    informe = comprobar(_Miente(), _casos())
    assert informe.veredicto_spans == "CONTRADICCION"
    assert not informe.pasa
    assert any(h.comprobacion == "spans" and h.severidad == "FALLA" for h in informe.hallazgos)


def test_declararse_incapaz_emitiendo_combinadas_es_escondido() -> None:
    """Refugiarse en `NO_APLICABLE` trayéndolas. Es la casilla que una igualdad se come."""

    class _Escondido(_Base):
        expresses_spans = False
        emite_combinadas = True

    informe = comprobar(_Escondido(), _casos())
    assert informe.veredicto_spans == "ESCONDIDO"
    assert not informe.pasa


def test_un_extract_que_lanza_ante_un_pdf_corrupto_no_pasa() -> None:
    """El aro que sostiene la tasa de fallo: quien lanza se lleva la campaña por delante
    y borra del informe su propia tasa, que es un resultado publicado."""

    class _Revienta(_Base):
        def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
            if b"esto no es un PDF" in doc.primary:
                raise RuntimeError("boom")
            return super().extract(doc, page_range)

    informe = comprobar(_Revienta(), _casos())
    assert not informe.pasa
    fallo = next(h for h in informe.hallazgos if h.comprobacion == "extract_no_lanza")
    assert "RuntimeError" in fallo.detalle, fallo.detalle


def test_un_cost_of_impuro_no_pasa() -> None:
    """Si el coste depende de cuándo se pregunte, el coste por éxito no se reproduce."""

    class _Impuro(_Base):
        _n = 0

        def cost_of(self, ex: Extraction) -> Cost:
            _Impuro._n += 1
            return _coste(_Impuro._n)

    informe = comprobar(_Impuro(), _casos())
    assert not informe.pasa
    assert any(h.comprobacion == "cost_of_pura" for h in informe.hallazgos)


def test_una_extraccion_que_no_se_identifica_no_pasa() -> None:
    """Sin `extractor_id` correcto no se puede agregar nada por extractor."""

    class _Anonimo(_Base):
        def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
            ex = super().extract(doc, page_range)
            return Extraction(**{**ex.__dict__, "extractor_id": "otro"})

    informe = comprobar(_Anonimo(), _casos())
    assert not informe.pasa
    assert any(h.comprobacion == "identificacion" for h in informe.hallazgos)


def test_al_que_le_falta_un_miembro_la_suite_para_en_la_forma() -> None:
    """No tiene sentido ejecutar a quien no cumple la forma: el informe lo dice y para."""
    miembros = {k: v for k, v in vars(_Base).items() if not k.startswith("__")}
    del miembros["probe"]
    cojo = type("Cojo", (), miembros)

    informe = comprobar(cojo(), _casos())
    assert not informe.pasa
    assert len(informe.hallazgos) == 1
    assert informe.hallazgos[0].comprobacion == "forma"
    assert "probe" in informe.hallazgos[0].detalle


@pytest.mark.parametrize("formato", ["Markdown", "md", "lo-que-sea"])
def test_un_formato_no_canonico_deja_los_spans_no_ejecutada(formato: str) -> None:
    """No se decide por defecto: la suite dice que no pudo, en vez de dar por bueno."""

    class _Raro(_Base):
        pass

    _Raro.formato = formato
    informe = comprobar(_Raro(), _casos())
    assert informe.veredicto_spans is None
    assert not informe.pasa
    assert any(h.comprobacion == "formato_canonico" for h in informe.hallazgos)
