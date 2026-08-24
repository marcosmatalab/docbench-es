"""Que un par PDF/XML incoherente **se descarta y se cuenta**. Las dos mitades.

> *«Un emparejado silenciosamente incorrecto envenena todo el benchmark.»*

El descarte es una barrera: su trabajo es rechazar. Y su silencio se leería como
«todos los pares eran buenos», que es la forma exacta que tiene un corpus
envenenado de parecer sano. Por eso va con las dos direcciones —descarta lo malo,
acepta lo bueno— y con el invariante de que **nada se pierde por el camino**.

El umbral no está aquí: vive en el perfil de la entidad, y está medido sobre n=600
en tres ventanas. Estos tests usan 0,85 porque es el del BOE, no porque el módulo
lo sepa.
"""

from __future__ import annotations

from docbench_es.corpus.pairing import coherencia, contar, juzgar, normalizar

UMBRAL = 0.85

XML = "Resolución de 3 de agosto de 2026 por la que se convocan pruebas selectivas."
PDF_IGUAL = (
    "BOLETÍN OFICIAL DEL ESTADO\n"
    "Núm. 186 Martes 4 de agosto de 2026 Sec. III. Pág. 100\n"
    "Resolución de 3 de agosto de 2026 por la que se convocan pruebas selectivas.\n"
    "cve: BOE-A-2026-17075 Verificable en https://www.boe.es\n"
)
PDF_OTRO = "Anuncio de licitación de obras de conservación en la carretera N-340, lote 2."
PDF_CASI = PDF_IGUAL.replace("pruebas selectivas", "pruebas selectivas de acceso libre")
"""Casi el mismo: el PDF trae tres palabras que el XML no. Es el caso realista —el
XML y el PDF del BOE difieren en maquetación, no en contenido— y es el único con el
que se puede ver si el umbral discrimina, porque el par idéntico da 1,0 y acepta
con cualquier umbral."""


def test_un_par_que_dice_lo_mismo_se_acepta_aunque_el_pdf_traiga_maquetacion() -> None:
    """La normalización declarada, funcionando: la cabecera del PDF no hunde el par.

    Las líneas que se quitan —`BOLETÍN OFICIAL DEL ESTADO`, `Núm.`, `Sec.`, `Pág.`,
    el `cve:`, la URL— son maquetación que el XML no tiene. Sin quitarlas la
    similitud bajaría por un motivo que no tiene nada que ver con el contenido, y
    se descartarían pares buenos.
    """
    veredicto = juzgar(PDF_IGUAL, XML, umbral=UMBRAL)

    assert veredicto.acepta and veredicto.causa is None
    assert veredicto.coherencia.similitud > UMBRAL


def test_un_par_que_no_dice_lo_mismo_se_descarta_con_su_causa() -> None:
    """**El caso que la barrera existe para parar.**

    Si este par entrara, la verdad `DERIVED` saldría de un XML que habla de otra
    cosa, y la nota del extractor mediría el desajuste del par en vez de su
    calidad. La causa es del enum cerrado: `incoherente`, no un `otro`.
    """
    veredicto = juzgar(PDF_OTRO, XML, umbral=UMBRAL)

    assert not veredicto.acepta
    assert veredicto.causa == "incoherente"
    assert veredicto.coherencia.similitud < UMBRAL


def test_la_falta_y_el_vacio_no_se_confunden_con_la_incoherencia() -> None:
    """Tres causas distintas, y el orden importa para el diagnóstico.

    Un par sin XML **no es un par incoherente**: decir que lo es mandaría a alguien
    a revisar el umbral cuando el problema es que la descarga no llegó. Es la misma
    distinción que separa «día sin boletín» de «origen caído».
    """
    assert juzgar(PDF_IGUAL, None, umbral=UMBRAL).causa == "sin_xml"
    assert juzgar(None, XML, umbral=UMBRAL).causa == "sin_pdf"
    assert juzgar(PDF_IGUAL, "   ", umbral=UMBRAL).causa == "xml_sin_texto"
    assert juzgar("   ", XML, umbral=UMBRAL).causa == "pdf_sin_texto"


def test_el_umbral_manda_y_por_eso_vive_en_el_perfil() -> None:
    """El mismo par, dos umbrales, dos veredictos. Por eso el número no está en el código.

    Está medido lo que cuesta moverlo: a 0,85 se descarta el 4,00% del BOE y a
    0,95, uno de cada cinco documentos buenos. Un número con esa consecuencia no
    puede vivir escondido en una función.
    """
    flojo = juzgar(PDF_CASI, XML, umbral=0.10)
    duro = juzgar(PDF_CASI, XML, umbral=0.999)

    assert flojo.acepta
    assert not duro.acepta and duro.causa == "incoherente"


def test_el_recuento_cuadra_siempre_y_por_eso_nada_se_traga() -> None:
    """**El invariante que hace cierta la regla de oro 6.**

    `aceptados + descartes de todas las causas == n_pares`. Si no cuadrara, habría
    documentos que salieron del emparejado sin aparecer en ningún lado — que es
    exactamente la forma que tiene un descarte de desaparecer del denominador y de
    la tasa que se publica.
    """
    veredictos = [
        juzgar(PDF_IGUAL, XML, umbral=UMBRAL),
        juzgar(PDF_OTRO, XML, umbral=UMBRAL),
        juzgar(PDF_IGUAL, None, umbral=UMBRAL),
        juzgar(PDF_IGUAL, XML, umbral=UMBRAL),
    ]

    censo = contar(veredictos)

    assert censo.n_pares == 4
    assert censo.n_aceptados == 2
    assert censo.por_causa == {"incoherente": 1, "sin_xml": 1}
    assert censo.n_aceptados + censo.n_descartados == censo.n_pares
    assert censo.tasa_descarte == 0.5


def test_un_lote_vacio_no_revienta_y_su_tasa_es_cero() -> None:
    """Cero pares es un estado válido de un día sin documentos, no una división por cero."""
    censo = contar([])

    assert censo.n_pares == 0 and censo.tasa_descarte == 0.0


def test_la_normalizacion_conserva_los_acentos_a_proposito() -> None:
    """Quitarlos es agresivo y aquí sólo serviría para **inflar la similitud**.

    Toda normalización se documenta (regla de oro 7) porque una agresiva es hacer
    trampas en silencio, y aquí las trampas irían siempre en la misma dirección:
    descartar menos pares de los que habría que descartar.
    """
    assert normalizar("Resolución NÚM", quitar_ruido=False) == ["resolución", "núm"]
    # Y el ruido sólo se quita del lado del PDF, que es el que lo lleva.
    assert normalizar("Núm. 186 uno", quitar_ruido=True) == []
    assert normalizar("Núm. 186 uno", quitar_ruido=False) == ["núm", "186", "uno"]


def test_los_tokens_viajan_con_la_similitud() -> None:
    """Una similitud de 0,9 entre dos textos de 30 palabras y entre dos de 8.000 no
    son el mismo hecho, y sin el tamaño nadie puede distinguirlas leyendo."""
    medida = coherencia(PDF_IGUAL, XML)

    assert medida.tokens_xml == len(normalizar(XML, quitar_ruido=False))
    assert medida.tokens_pdf > 0
