"""Que el cliente del BOE cumple las cinco condiciones de ADR-0031. **Sin red.**

La condición 1 —*descubrimiento sólo por la API*— es **una barrera**: su único
trabajo es ponerse roja ante una URL que ningún sumario ha entregado. Y su silencio
se leería como «todo lo que bajamos vino de la API», que es exactamente la frase
que sostiene el argumento con el que este proyecto justifica bajar el XML del BOE.
Si esa frase deja de ser cierta, ADR-0031 se cae entero.

Por eso va con las **dos direcciones**: rechaza lo que nadie autorizó y acepta lo
que el sumario entregó. Un candado que dijera «no» a todo pasaría igual de verde.
"""

from __future__ import annotations

from datetime import date

import pytest
from _boe_falso import PDF_URL, SUMARIO_URL, XML_URL, Origen, Reloj

from docbench_es.entity._sumario import items_del_sumario, paginas_de, url_de
from docbench_es.entity.base import RitmoPeticion
from docbench_es.entity.boe_api import BoeApi
from docbench_es.errors import AdapterError, DocbenchError, PolicyViolation

RITMO = RitmoPeticion(rps=1.0, user_agent="docbench-es/0.1 (+https://example.org/repo)")
DIA = date(2026, 8, 3)


def _api(origen: Origen, reloj: Reloj | None = None) -> BoeApi:
    r = reloj or Reloj()
    return BoeApi(RITMO, cliente=origen.cliente(), reloj=r.leer, dormir=r.dormir)


def test_bajar_una_url_que_ningun_sumario_ha_dado_es_violacion_de_politica() -> None:
    """**La condición 1 de ADR-0031, ejecutable.** El caso que la barrera existe para parar.

    La URL de este test es **válida y real**: es exactamente la que el sumario
    acabaría dando. Y aun así se rechaza, porque lo que rompe el argumento no es
    que la URL esté mal formada — es **haberla obtenido sin pasar por la API**.
    Adivinar identificadores convierte «soy cliente de una API documentada» en
    falso de golpe, y ése es el único argumento que este proyecto tiene.
    """
    api = _api(Origen())

    with pytest.raises(PolicyViolation) as capturado:
        api.descargar(XML_URL)

    assert "ADR-0031" in str(capturado.value)
    assert capturado.value.exit_code == 2, "la campaña no arranca: es política, no un aviso"


def test_despues_del_sumario_esa_misma_url_si_se_baja() -> None:
    """El otro lado, sin el cual lo de arriba se conseguiría rechazándolo todo.

    Misma URL, mismo cliente. Lo único que cambia es que el sumario la ha
    entregado. Si este test no existiera, un `descargar` que lanzara siempre
    pasaría el test de arriba y rompería la cosecha entera.
    """
    api = _api(Origen())
    api.sumario(DIA)

    assert api.descargar(XML_URL).startswith(b"<?xml")
    assert XML_URL in api.autorizadas


def test_el_pdf_tambien_queda_autorizado_aunque_su_campo_sea_un_objeto() -> None:
    """La rareza que se habría llevado por delante la mitad de la cosecha.

    `url_xml` es una cadena y **`url_pdf` es un objeto** con `texto` dentro. Un
    autorizador que sólo mirase cadenas dejaría todos los PDF fuera de la lista, y
    el fallo **no aparecería al leer el sumario**: aparecería mucho después, al
    intentar bajar el primero, con un mensaje hablando de política.
    """
    api = _api(Origen())
    api.sumario(DIA)

    assert PDF_URL in api.autorizadas
    assert api.descargar(PDF_URL).startswith(b"%PDF")


def test_un_dia_sin_boletin_no_es_un_fallo_sino_una_ausencia() -> None:
    """Domingos y festivos. *«Un día que no se pudo consultar no es un descarte.»*

    Si el 404 fuera `AdapterError`, `discover` se moriría el primer domingo del
    rango y una cosecha de un mes no llegaría a la segunda semana.
    """
    api = _api(Origen(respuestas={}))

    assert api.sumario(DIA) is None


def test_cualquier_otro_codigo_si_es_un_fallo_de_infraestructura() -> None:
    """Un 500 no es un día sin boletín: es el origen caído, y se distingue.

    Código 4 y no 1: que no se pueda llegar al corpus **no es un resultado de
    medición**, y contarlo como tal convertiría una caída de red en una nota mala
    del extractor.
    """
    api = _api(Origen(respuestas={SUMARIO_URL: (500, b"")}))

    with pytest.raises(AdapterError) as capturado:
        api.sumario(DIA)

    assert isinstance(capturado.value, DocbenchError)
    assert capturado.value.exit_code == 4


def test_el_ritmo_se_respeta_entre_peticiones_y_no_es_una_pausa_al_final() -> None:
    """La condición 2, medida con un reloj falso: **espaciado entre INICIOS**.

    Un promedio sobre una ventana permitiría ráfagas, y una ráfaga es justo lo que
    un servidor ajeno nota. Con `rps=1`, la primera petición no espera y las
    siguientes esperan lo que falte para el segundo.
    """
    reloj = Reloj()
    api = _api(Origen(), reloj)

    api.sumario(DIA)
    api.descargar(XML_URL)
    api.descargar(PDF_URL)

    assert reloj.dormido == [1.0, 1.0], "la primera no espera; las otras dos, un segundo"


def test_no_hay_cache_y_esta_declarado() -> None:
    """Dos `descargar` de la misma URL son dos peticiones, y el módulo lo dice.

    No es un descuido: la caché necesita el manifiesto con los hashes, y el
    manifiesto es de `corpus`. Un módulo que cacheara sin saber lo que ya hay en
    disco daría dos respuestas distintas a la misma pregunta según el orden.
    """
    origen = Origen()
    api = _api(origen)
    api.sumario(DIA)

    api.descargar(XML_URL)
    api.descargar(XML_URL)

    assert origen.pedidas.count(XML_URL) == 2


def test_el_recorrido_del_sumario_encuentra_las_dos_formas_raras() -> None:
    """Los niveles colapsados a `dict` y la clave `texto` entre medias.

    Las dos están medidas sobre sumarios reales —20260809 y 20260817— y las dos
    hacen perder documentos si no se miran. El test las tiene juntas porque juntas
    aparecen en el origen.
    """
    api = _api(Origen())
    sumario = api.sumario(DIA)
    assert sumario is not None

    items = items_del_sumario(sumario)
    por_seccion = {str(i["_seccion"]) for i in items}

    assert len(items) == 4, "dos de la sección 1, uno de la 3 —que va bajo `texto`— y uno de la 5"
    assert por_seccion == {"1", "3", "5"}


def test_las_paginas_salen_del_sumario_sin_bajar_el_pdf() -> None:
    """`pagina_final - pagina_inicial + 1`. Mil peticiones menos, y es lo que
    alimenta la banda de longitud de ADR-0034."""
    api = _api(Origen())
    sumario = api.sumario(DIA)
    assert sumario is not None

    primero = items_del_sumario(sumario)[0]

    assert paginas_de(primero) == 3
    assert url_de(primero, "url_xml") == XML_URL
    assert url_de(primero, "url_pdf") == PDF_URL


def test_el_sumario_pide_json_porque_sin_eso_el_boe_devuelve_400() -> None:
    """**El bug que cazó la primera petición del piloto**, por una en vez de por dos mil.

    El endpoint del sumario responde **HTTP 400** si no se le manda
    `Accept: application/json` — medido contra el origen real el 24 ago 2026. Los
    documentos no lo llevan: son binarios y el servidor los sirve tal cual, y
    mandarlo daría igual o estorbaría.

    Es la clase de cosa que no se descubre leyendo la documentación de la API, y
    la razón de que el piloto vaya antes que la cosecha.
    """
    origen = Origen()
    api = _api(origen)

    api.sumario(DIA)
    api.descargar(PDF_URL)

    del_sumario, del_pdf = origen.cabeceras[0], origen.cabeceras[1]
    assert del_sumario["accept"] == "application/json"
    assert del_pdf.get("accept") != "application/json", "un PDF no es JSON"
    assert "docbench-es" in del_sumario["user-agent"], "y la identificación va en las dos"
