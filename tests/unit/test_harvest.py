"""La cosecha: **aquí nacen las cifras de L3 y no son reversibles.**

Todo lo demás de este hito se puede reescribir. Esto no: sus decisiones quedan
congeladas en un corpus de 1.000 documentos, y equivocarse significa volver a
pedirle 2.000 ficheros al BOE. Así que cada punto tiene su test **antes** de que
se baje el primer documento, y varios son barreras con sus dos direcciones.

Sin red: el origen es `_boe_falso` con `httpx.MockTransport`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from _boe_falso import PDF_URL, XML_URL, Origen, Reloj

from docbench_es.corpus import _cosecha, harvest
from docbench_es.corpus.harvest import Cosecha, ParadaPorFallos, Ritmo, cosechar
from docbench_es.corpus.manifest import Procedencia
from docbench_es.entity.base import cargar_perfil
from docbench_es.entity.boe import BoeAdapter
from docbench_es.entity.boe_api import BoeApi
from docbench_es.entity.boe_xml import texto_plano
from docbench_es.errors import ContractViolation
from docbench_es.types import DocRef, RawDoc

RAIZ = Path(__file__).resolve().parents[2]
DIA = date(2026, 8, 3)
HOY = date(2026, 8, 24)


def _adaptador(origen: Origen) -> BoeAdapter:
    reloj = Reloj()
    perfil = cargar_perfil(RAIZ / "entities" / "boe.yaml")
    return BoeAdapter(perfil, BoeApi(perfil.ritmo, origen.cliente(), reloj.leer, reloj.dormir))


def _textos(doc: RawDoc) -> tuple[str | None, str | None]:
    """El XML de verdad, y un PDF que dice lo mismo: el par coherente."""
    xml = texto_plano(doc.companions["xml"].decode("utf-8"))
    return xml, xml


def _incoherente(doc: RawDoc) -> tuple[str | None, str | None]:
    del doc
    return "un anuncio de licitación de obras que no tiene nada que ver", "resolución"


def _cosechar(origen: Origen, **kw: object) -> Cosecha:
    perfil = cargar_perfil(RAIZ / "entities" / "boe.yaml")
    reloj = Reloj()
    opciones: dict[str, object] = {
        "textos": _textos,
        "umbral_coherencia": perfil.umbral_coherencia,
        "actualizado_en": HOY,
        "reloj": reloj.leer,
    }
    opciones.update(kw)
    return cosechar(_adaptador(origen), desde=DIA, hasta=DIA, **opciones)  # type: ignore[arg-type]


def test_una_cosecha_limpia_acepta_los_dos_y_cuadra() -> None:
    """El caso base, y **el invariante sobre la cosecha entera**, no sólo el emparejado."""
    cosecha = _cosechar(Origen())

    assert cosecha.intentados == 2
    assert len(cosecha.aceptados) == 2
    assert cosecha.por_causa == {}
    assert cosecha.tasa_descarte == 0.0


def test_la_cosecha_no_se_construye_si_no_cuadra() -> None:
    """**`aceptados + descartes == intentados`, o no hay objeto.**

    Es la regla de oro 6 en el tipo de retorno: si no cuadrara, habría documentos
    que salieron de la cosecha sin aparecer en ningún lado, y la tasa publicada
    estaría calculada sobre una población que nadie declaró. Que sea imposible
    construir el resultado malo es más fuerte que comprobarlo al publicar.
    """
    with pytest.raises(ContractViolation) as capturado:
        Cosecha(
            intentados=10,
            aceptados=(),
            por_causa={"incoherente": 3},
            dias_sin_boletin=(),
            ritmo=Ritmo(None, None, 0),
            reintentos_agotados=0,
        )

    assert "no cuadra" in str(capturado.value)


def test_un_par_incoherente_se_descarta_con_su_causa_y_entra_en_la_tasa() -> None:
    """El descarte llega hasta la cifra publicada, con su causa del enum cerrado."""
    cosecha = _cosechar(Origen(), textos=_incoherente)

    assert cosecha.aceptados == ()
    assert cosecha.por_causa == {"incoherente": 2}
    assert cosecha.tasa_descarte == 1.0


def test_los_dias_sin_boletin_salen_del_denominador_y_se_cuentan_aparte() -> None:
    """*«Un día que no se pudo consultar no es un descarte.»*

    Si contaran como intentados, la tasa de descarte de una ventana con muchos
    domingos saldría inflada por el calendario — y sería **una propiedad del
    calendario disfrazada de propiedad del corpus**, que es lo que ADR-0030 prohíbe.
    """
    perfil = cargar_perfil(RAIZ / "entities" / "boe.yaml")
    adaptador = _adaptador(Origen())

    cosecha = cosechar(
        adaptador,
        desde=DIA,
        hasta=date(2026, 8, 5),
        textos=_textos,
        umbral_coherencia=perfil.umbral_coherencia,
        actualizado_en=HOY,
    )

    assert cosecha.intentados == 2, "los dos documentos del único día con boletín"
    assert cosecha.dias_sin_boletin == (date(2026, 8, 4), date(2026, 8, 5))


def test_lo_que_ya_esta_en_el_manifiesto_no_se_vuelve_a_bajar() -> None:
    """**ADR-0031, condición 4**, comprobada por tráfico y no por intención.

    Y entra igual en `aceptados`: **sigue siendo parte del corpus**. Si los
    heredados no contaran, reanudar cambiaría el denominador de la tasa.
    """
    origen = Origen()
    previo = Procedencia(
        external_id="BOE-A-2026-17075",
        fecha_sumario=DIA,
        seccion="1",
        url_pdf=PDF_URL,
        url_xml=XML_URL,
        sha256="da-igual",
        n_pages=3,
        strata=frozenset({"celdas-combinadas"}),
        fetched_at=datetime(2026, 8, 3, tzinfo=UTC),
        actualizado_en=HOY,
    )

    cosecha = _cosechar(origen, ya_en_manifiesto={previo.external_id: previo})

    assert cosecha.intentados == 2 and len(cosecha.aceptados) == 2
    assert cosecha.descargados_ahora == 1, "sólo el que faltaba"
    assert PDF_URL not in origen.pedidas, "el heredado no se volvió a pedir"


def test_la_tasa_es_del_corpus_y_no_del_proceso() -> None:
    """**ADR-0030, punto 5.** Dos corridas, la segunda arregla el fallo de la primera.

    Es el caso que decide si la cifra publicada es una propiedad del corpus o de
    cuántas veces alguien le dio a reintentar. Corrida 1: el XML de un documento no
    se puede bajar y agota reintentos → **50% de descarte**. Corrida 2, con el
    origen arreglado y el manifiesto de la 1 delante: el documento entra y la tasa
    final es **0%**, no un 25% promediado ni un 50% heredado.
    """
    roto = Origen()
    del roto.respuestas[XML_URL]

    primera = _cosechar(roto, reintentos=0)

    assert primera.por_causa == {"descarga": 1}
    assert primera.tasa_descarte == 0.5
    assert primera.reintentos_agotados == 1

    heredado = {p.external_id: p for p in primera.aceptados}
    segunda = _cosechar(Origen(), ya_en_manifiesto=heredado)

    assert segunda.intentados == 2
    assert segunda.por_causa == {}
    assert segunda.tasa_descarte == 0.0, "la del corpus, no la del proceso"
    assert segunda.descargados_ahora == 1, "el heredado no se rebajó"


def test_el_ritmo_se_publica_como_espaciado_y_no_como_n_partido_por_t() -> None:
    """Dos errores en uno, y el segundo lo cazó el piloto contra el BOE real.

    El primero es el método: con `N/T`, diez peticiones seguidas y una pausa larga
    dan el mismo número que once bien espaciadas.

    **El segundo es la UNIDAD.** `harvest` sólo ve documentos, y un documento del
    BOE son **dos** peticiones —PDF y XML—. Midiendo entre documentos el piloto
    publicó **1,99 s con 1 rps declarado**: el doble, y un umbral de 1 s lo habría
    dado por bueno con un ritmo real la mitad de lento. El número sale ahora de
    `BoeApi`, que es lo único que ve las peticiones sueltas.
    """
    cosecha = _cosechar(Origen())

    # El reloj falso avanza un segundo por PETICIÓN, y cada documento son dos.
    assert cosecha.ritmo.espaciado_mediano_s == 1.0, "por petición, no por documento"
    assert cosecha.ritmo.n_peticiones >= 4, "dos documentos, dos peticiones cada uno"


def test_con_menos_de_dos_peticiones_el_espaciado_es_none_y_no_cero() -> None:
    """Cero no es «no se pudo medir», y confundirlos publica un ritmo inventado."""
    assert harvest._ritmo(None, []) == Ritmo(None, None, 0)
    assert harvest._ritmo(None, [1.0]) == Ritmo(None, None, 1)


def test_la_cosecha_para_si_mas_del_cinco_por_ciento_agota_reintentos() -> None:
    """**La condición de parada, viva y en el código.**

    Seguir cosechando produciría mil documentos a los que les falta una parte
    desconocida por una causa que nadie ha mirado. Y para que la fracción signifique
    algo hay un suelo: sin él, **el primer documento que fallara pararía la
    cosecha** — 1 de 1 es el 100%.
    """
    cuenta = _cosecha._Contador(intentados=19, agotados=19)
    cuenta.vigila_parada()  # por debajo del suelo: no para, y no es un descuido

    cuenta = _cosecha._Contador(intentados=20, agotados=2)
    with pytest.raises(ParadaPorFallos) as capturado:
        cuenta.vigila_parada()

    assert "PARA" in str(capturado.value)
    assert capturado.value.exit_code == 4, "no es un resultado de medición: es el origen"


def test_por_debajo_del_umbral_la_cosecha_sigue() -> None:
    """La otra dirección: una puerta que parara siempre no dejaría cosechar nada."""
    _cosecha._Contador(intentados=100, agotados=5).vigila_parada()


def test_el_objetivo_corta_por_aceptados_y_no_por_intentos() -> None:
    """**El corte que garantiza el criterio aunque el descarte no sea el proyectado.**

    Dimensionar por intentos —«1.045 para 1.000 al 4%»— deja el corpus en 960 si el
    descarte sale al 8%, y volver a pedirle mil documentos más al origen no es
    gratis. Cortando por aceptados, el objetivo se cumple pase lo que pase con la
    tasa; lo que varía es cuánto de la ventana hace falta.
    """
    cosecha = _cosechar(Origen(), objetivo=1)

    assert len(cosecha.aceptados) == 1
    assert cosecha.intentados == 1, "no se pide ni un documento de más"


def test_los_bytes_solo_se_guardan_si_alguien_los_pide_y_solo_los_aceptados() -> None:
    """**Un corpus «descargado» que no está en disco no es un corpus** (§16).

    `harvest` no escribe: baja, comprueba y anota la procedencia. Quien quiera
    conservar los bytes pasa `guardar` — y se llama **sólo con los aceptados**,
    porque guardar un descartado dejaría en disco un documento que el manifiesto
    dice que no está, y el día que alguien recorra el directorio en vez del
    manifiesto tendría un corpus distinto del publicado.
    """
    guardados: list[str] = []

    def anotar(ref: DocRef, doc: RawDoc) -> None:
        del doc  # el test mira a QUIÉN se guarda, no qué bytes
        guardados.append(ref.external_id)

    limpia = _cosechar(Origen(), guardar=anotar)

    assert guardados == [p.external_id for p in limpia.aceptados]

    guardados.clear()
    _cosechar(Origen(), textos=_incoherente, guardar=anotar)

    assert guardados == [], "los descartados no se guardan"
