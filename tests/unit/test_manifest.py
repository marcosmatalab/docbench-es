"""Que el manifiesto **nace publicable**, que es un requisito de diseño (ADR-0033).

La asimetría que lo decide: publicar el corpus después es **gratis** si el
manifiesto nace con lo necesario dentro, y es **otro hito** si no — porque la fecha
de última actualización y la sección **no se pueden reconstruir sin volver al
origen**, y volver seis meses después no devuelve lo mismo.

Los cuatro requisitos tienen test, y el de la atribución es una barrera: sin ella
el corpus incumpliría su licencia al publicarse, y el momento de notarlo es **al
construir el manifiesto**, no al publicarlo.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from _boe_falso import PDF_URL, XML_URL, Origen, Reloj
from benchcore.types import LicenseDecl

from docbench_es.corpus.harvest import cosechar
from docbench_es.corpus.manifest import (
    ESQUEMA,
    LICENCIA_DEL_CODIGO,
    Manifiesto,
    Procedencia,
    crear,
)
from docbench_es.entity.base import cargar_perfil
from docbench_es.entity.boe import BoeAdapter
from docbench_es.entity.boe_api import BoeApi
from docbench_es.entity.boe_xml import texto_plano
from docbench_es.errors import ContractViolation
from docbench_es.types import RawDoc

RAIZ = Path(__file__).resolve().parents[2]
DIA = date(2026, 8, 3)
HOY = date(2026, 8, 24)
PERFIL = cargar_perfil(RAIZ / "entities" / "boe.yaml")

UNO = Procedencia(
    external_id="BOE-A-2026-17075",
    fecha_sumario=DIA,
    seccion="1",
    url_pdf=PDF_URL,
    url_xml=XML_URL,
    sha256="abc123",
    n_pages=3,
    strata=frozenset({"celdas-combinadas"}),
    fetched_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
    cosechado_en=HOY,
)


def _crear(*, licencia: LicenseDecl | None = None, intentados: int = 2) -> Manifiesto:
    """El manifiesto de ejemplo. Los dos parámetros son los que cada test mueve."""
    return crear(
        entidad="boe",
        plan_hash="f" * 64,
        desde=DIA,
        hasta=DIA,
        documentos=[UNO],
        licencia=PERFIL.licencia if licencia is None else licencia,
        umbral_coherencia=PERFIL.umbral_coherencia,
        intentados=intentados,
        por_causa={"incoherente": 1},
        dias_sin_boletin=[date(2026, 8, 4)],
        espaciado_mediano_s=1.0,
        espaciado_minimo_s=1.0,
        n_espaciados=3,
    )


def test_requisito_1_la_procedencia_es_por_documento_con_su_seccion_y_su_fecha() -> None:
    """Sin la sección **no se puede re-derivar la población del denominador**, y sin
    la fecha del sumario no se sabe de qué ventana salió cada documento — que es lo
    que ADR-0030 exige para publicar cualquier tasa. Ninguna de las dos se puede
    reconstruir sin volver al origen."""
    datos = json.loads(_crear().a_texto())

    doc = datos["documentos"][0]

    assert doc["seccion"] == "1"
    assert doc["fecha_sumario"] == "2026-08-03"
    assert doc["cosechado_en"] == "2026-08-24", "la que exigen las condiciones del BOE"
    assert doc["url_pdf"] and doc["url_xml"], "las dos, no una"


def test_requisito_2_sin_atribucion_no_hay_manifiesto() -> None:
    """**La barrera.** Publicar un corpus sin la atribución que su licencia exige
    incumple la licencia, y eso se nota al construirlo o no se nota.

    ADR-0033 pide el **texto literal dentro**, no una referencia a dónde leerlo.
    """
    sin_atribucion = type(PERFIL.licencia)(**{**PERFIL.licencia.__dict__, "attribution": "   "})

    with pytest.raises(ContractViolation) as capturado:
        _crear(licencia=sin_atribucion)

    assert "attribution" in str(capturado.value)


def test_requisito_2_con_atribucion_va_dentro_y_literal() -> None:
    """La otra dirección, y **literal**: reescribirla sería atribuir con palabras
    que el organismo no ha autorizado (ADR-0031, condición 5)."""
    datos = json.loads(_crear().a_texto())

    assert datos["atribucion"] == (
        "Basado en datos de la Agencia Estatal Boletín Oficial del Estado"
    )


def test_requisito_3_la_licencia_del_corpus_va_separada_de_la_del_codigo() -> None:
    """Confundirlas es lo que hace impublicable un dataset.

    El código es Apache-2.0 y el corpus está sujeto a las condiciones del BOE, que
    exigen atribución. Son dos campos porque son dos cosas.
    """
    datos = json.loads(_crear().a_texto())

    assert datos["licencia_codigo"] == LICENCIA_DEL_CODIGO == "Apache-2.0"
    assert datos["licencia_corpus"]["name"].startswith("Reutilización autorizada")
    assert datos["licencia_corpus"] != datos["licencia_codigo"]


def test_requisito_4_el_formato_de_maquina_lleva_su_esquema_y_es_estable() -> None:
    """El markdown se renderiza **a partir** de esto, nunca al revés.

    Y el JSON es estable entre corridas idénticas: si el orden de las claves
    cambiara, cada campaña produciría un `diff` enorme y nadie vería qué cambió de
    verdad.
    """
    manifiesto = _crear()

    texto = manifiesto.a_texto()

    assert json.loads(texto)["esquema"] == ESQUEMA
    assert texto == manifiesto.a_texto()
    assert json.loads(texto) == manifiesto.a_json()


def test_la_tasa_nunca_viaja_sola_dentro_del_json() -> None:
    """**ADR-0030**: ventana, dispersión, umbral y denominador van con ella.

    Aquí van los tres que este objeto conoce —ventana, umbral y denominador—. La
    dispersión entre ventanas es de quien agregue varias campañas, y por eso el
    manifiesto guarda las fechas: sin ellas no se puede agrupar por ventana.
    """
    datos = json.loads(_crear().a_texto())

    assert datos["ventana"] == {"desde": "2026-08-03", "hasta": "2026-08-03"}
    assert datos["emparejado"]["umbral_coherencia"] == 0.85
    assert datos["emparejado"]["intentados"] == 2
    assert datos["emparejado"]["tasa_descarte"] == 0.5
    assert datos["dias_sin_boletin"] == ["2026-08-04"]


def test_el_manifiesto_tampoco_se_construye_si_la_cosecha_no_cuadra() -> None:
    """Segunda puerta, la misma regla: un descarte que desaparece se lleva por
    delante el denominador de la tasa publicada."""
    with pytest.raises(ContractViolation) as capturado:
        _crear(intentados=99)

    assert "no cuadra" in str(capturado.value)


def test_una_cosecha_real_del_boe_produce_un_manifiesto_publicable() -> None:
    """**El camino entero**, de la API falsa al JSON: cosechar y publicar encajan.

    Sin esto, las dos mitades podrían estar bien por separado y no casar — que es
    justo lo que pasa cuando el manifiesto se diseña después de la cosecha.
    """
    reloj = Reloj()
    adaptador = BoeAdapter(
        PERFIL, BoeApi(PERFIL.ritmo, Origen().cliente(), reloj.leer, reloj.dormir)
    )

    def textos(doc: RawDoc) -> tuple[str | None, str | None]:
        xml = texto_plano(doc.companions["xml"].decode("utf-8"))
        return xml, xml

    cosecha = cosechar(
        adaptador,
        desde=DIA,
        hasta=DIA,
        textos=textos,
        umbral_coherencia=PERFIL.umbral_coherencia,
        cosechado_en=HOY,
    )
    manifiesto = crear(
        entidad=adaptador.id,
        plan_hash="f" * 64,
        desde=DIA,
        hasta=DIA,
        documentos=cosecha.aceptados,
        licencia=adaptador.license(),
        umbral_coherencia=PERFIL.umbral_coherencia,
        intentados=cosecha.intentados,
        por_causa=cosecha.por_causa,
        dias_sin_boletin=cosecha.dias_sin_boletin,
        espaciado_mediano_s=cosecha.ritmo.espaciado_mediano_s,
        espaciado_minimo_s=cosecha.ritmo.espaciado_minimo_s,
        n_espaciados=cosecha.ritmo.n_espaciados,
    )

    datos = json.loads(manifiesto.a_texto())
    assert len(datos["documentos"]) == 2
    assert {d["seccion"] for d in datos["documentos"]} == {"1", "3"}
    assert datos["documentos"][0]["url_xml"].startswith("https://")
