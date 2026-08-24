"""Los siete métodos del BOE, contra un origen falso con la forma real. **Sin red.**

Aquí es donde el contrato de L3 deja de ser una promesa: la misma suite de
conformidad que pasan los adaptadores falsos la pasa **el adaptador de la entidad
de referencia**, y con ella las dos afirmaciones que el proyecto vende — que el
motor es agnóstico a la entidad, y que la verdad del BOE es `DERIVED`.

Dos barreras nacen aquí y llevan su control negativo en este mismo fichero:

- **`fetch` de un `DocRef` que no salió de `discover`** — la condición 1 de
  ADR-0031 llevada hasta el final. Su silencio se leería como «todo lo bajado vino
  de la API».
- **El perfil y la clase que no dicen lo mismo** — dos copias del mismo dato, que
  es el bug que este repo persigue en los documentos. En código se cierra igual.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from _boe_falso import PDF_URL, Origen, Reloj

from docbench_es.entity.base import cargar_perfil
from docbench_es.entity.boe import BoeAdapter
from docbench_es.entity.boe_api import BoeApi
from docbench_es.entity.conformance import comprobar
from docbench_es.errors import ContractViolation, PolicyViolation
from docbench_es.types import DocRef, Truth

RAIZ = Path(__file__).resolve().parents[2]
ETIQUETAS = frozenset(
    {"nacido-digital", "escaneado", "sin-tabla", "tabla-simple", "celdas-combinadas", "multipagina"}
)
"""Las del perfil del BOE. `comprobar` ya no las asume: sin ellas dice NO_EJECUTADA."""

DIA = date(2026, 8, 3)


def _adaptador(origen: Origen | None = None) -> BoeAdapter:
    o = origen or Origen()
    reloj = Reloj()
    perfil = cargar_perfil(RAIZ / "entities" / "boe.yaml")
    return BoeAdapter(perfil, BoeApi(perfil.ritmo, o.cliente(), reloj.leer, reloj.dormir))


def test_el_adaptador_del_boe_pasa_la_suite_de_conformidad() -> None:
    """**El criterio de §14, contra la entidad de referencia y no contra un falso.**

    Que los cuatro adaptadores falsos pasen demuestra que el contrato es
    implementable. Que lo pase el BOE —con su API, su XML y su verdad `DERIVED`—
    demuestra que el contrato es el que hace falta. Si esto se cae, se cae la
    afirmación de que el motor no sabe nada del BOE.
    """
    informe = comprobar(_adaptador(), desde=DIA, hasta=DIA, etiquetas_perfil=ETIQUETAS)

    assert informe.hallazgos == (), informe.resumen()
    assert informe.pasa
    assert informe.n_documentos == 2, "los dos de las secciones I y III"


def test_discover_filtra_por_seccion_y_tira_el_sumario_del_dia() -> None:
    """El filtro es del perfil porque **cambia la población**, no por comodidad.

    De los cuatro items del día entran dos: el `BOE-S-*` es el sumario y no un
    documento, y la sección V son anuncios que el perfil deja fuera. Sin este
    filtro, tres de cada cuatro documentos del BOE serían anuncios sin tabla y
    cualquier tasa publicada hablaría de otra población.
    """
    refs = list(_adaptador().discover(DIA, DIA))

    assert [r.external_id for r in refs] == ["BOE-A-2026-17075", "BOE-A-2026-17076"]
    assert all(r.entity == "boe" and r.published_on == DIA for r in refs)


def test_discover_es_perezoso_de_verdad() -> None:
    """Un `Iterable` que se consume a demanda, no una lista ya construida.

    Materializar una ventana de un año para quedarse con mil documentos es tráfico
    y memoria a cambio de nada. Se comprueba con el tráfico: **pedir el primero no
    puede haber pedido el sumario de todos los días del rango**.
    """
    origen = Origen()
    perezoso = _adaptador(origen).discover(DIA, date(2026, 8, 31))

    assert origen.pedidas == [], "llamar a discover no puede haber pedido nada todavía"
    next(iter(perezoso))
    assert len(origen.pedidas) == 1, "el primer documento sale del primer sumario"


def test_un_dia_sin_boletin_se_cuenta_aparte_y_no_para_la_cosecha() -> None:
    """Domingos y festivos. Confundirlos con un descarte **mueve el denominador**.

    El rango incluye días que el origen falso no sirve: la cosecha sigue y los
    días quedan anotados, que es lo que la regla de entidad exige — un día que no
    se pudo consultar no es un documento descartado.
    """
    adaptador = _adaptador()

    refs = list(adaptador.discover(DIA, date(2026, 8, 5)))

    assert len(refs) == 2
    assert adaptador.dias_sin_boletin == [date(2026, 8, 4), date(2026, 8, 5)]


def test_fetch_trae_el_pdf_como_primary_y_el_xml_al_lado() -> None:
    """El PDF es lo que se le da a un extractor; el XML es la verdad que lo juzga.

    Meterlos al revés invertiría el banco entero: se estaría midiendo al extractor
    contra lo que él mismo tendría que producir.
    """
    adaptador = _adaptador()
    ref = next(iter(adaptador.discover(DIA, DIA)))

    doc = adaptador.fetch(ref)

    assert doc.primary.startswith(b"%PDF") and doc.primary_mime == "application/pdf"
    assert doc.companions["xml"].startswith(b"<?xml")
    assert doc.n_pages == 3, "sale del sumario, sin abrir el PDF"
    assert doc.sha256 == adaptador.fetch(ref).sha256, "idempotente por sha256"


def test_fetch_de_una_ref_inventada_es_violacion_de_politica() -> None:
    """**La condición 1 hasta el final.** El caso que la barrera existe para parar.

    El `DocRef` de este test es correcto en todo: entidad, identificador con la
    forma del BOE, fecha real. Lo único que le falta es **haber salido de un
    sumario**, y eso es justo lo que ADR-0031 prohíbe suplir adivinando.
    """
    adaptador = _adaptador()

    with pytest.raises(PolicyViolation) as capturado:
        adaptador.fetch(
            DocRef(
                entity="boe",
                external_id="BOE-A-2026-17075",
                published_on=DIA,
                url=PDF_URL,
                kind="pdf",
            )
        )

    assert "ADR-0031" in str(capturado.value)


def test_la_misma_ref_saliendo_de_discover_si_se_baja() -> None:
    """El otro lado: sin esto, un `fetch` que lanzara siempre pasaría el de arriba.

    Mismo identificador y mismo adaptador que el test anterior. Lo único que
    cambia es que la referencia viene del sumario.
    """
    adaptador = _adaptador()
    ref = next(iter(adaptador.discover(DIA, DIA)))

    assert ref.external_id == "BOE-A-2026-17075"
    assert adaptador.fetch(ref).primary.startswith(b"%PDF")


def test_un_perfil_que_no_cuadra_con_la_clase_revienta_al_construir() -> None:
    """Dos copias del mismo dato no pueden divergir, y aquí se cierra en construcción.

    Los cinco atributos son de clase porque el registro los lee **sin instancia**
    (ADR-0036) y a la vez viven en el YAML porque §10.1 dice que las decisiones de
    la entidad van ahí. La comprobación es lo que impide que una campaña arranque
    con un adaptador que dice llamarse de dos formas distintas.
    """
    perfil = cargar_perfil(RAIZ / "entities" / "boe.yaml")
    otro = type(perfil)(**{**perfil.__dict__, "id": "no-es-el-boe"})

    with pytest.raises(ContractViolation) as capturado:
        BoeAdapter(otro)

    assert "no dicen lo mismo" in str(capturado.value)


def test_un_filtro_desconocido_revienta_en_vez_de_ignorarse() -> None:
    """Ignorar un filtro en silencio deja dos campañas midiendo poblaciones distintas.

    Y con el mismo nombre en el informe, que es lo que lo hace peligroso: nadie
    puede notarlo leyendo los resultados.
    """
    with pytest.raises(ContractViolation):
        list(_adaptador().discover(DIA, DIA, secciones=["5"]))


def test_la_verdad_del_boe_sale_del_xml_oficial_y_nunca_es_none() -> None:
    """El modo es `DERIVED`, así que **prometer verdad donde no la hay** sería mentir.

    El documento con `rowspan` trae su tabla; el que no tiene tablas trae **cero
    tablas**, que es una respuesta y no una ausencia. Los `facts` de §6.4 llegan en
    L4 con `truth.derived`, y por eso van vacíos y declarados, no inventados.
    """
    adaptador = _adaptador()
    con_tabla, sin_tabla = list(adaptador.discover(DIA, DIA))

    verdad = adaptador.truth(con_tabla)
    vacia = adaptador.truth(sin_tabla)

    # `truth` devuelve `object | None` en el Protocol, así que estrechar aquí no
    # es ceremonia: es la comprobación de que devuelve un `Truth` y no otra cosa.
    assert isinstance(verdad, Truth) and isinstance(vacia, Truth)
    assert len(verdad.tables) == 1
    assert verdad.mode == "DERIVED"
    assert len(vacia.tables) == 0


def test_los_estratos_salen_del_xml_y_son_deterministas() -> None:
    """Los cuatro que se pueden decidir sin extractor y sin páginas.

    `celdas-combinadas` para el que trae `rowspan="2"`. `escaneado` y `multipagina`
    no se emiten: el primero necesita la capa de texto del PDF y el segundo
    necesita páginas, que el XML no tiene. No se aproximan (ADR-0032).
    """
    adaptador = _adaptador()
    con_tabla, sin_tabla = list(adaptador.discover(DIA, DIA))

    combinadas = adaptador.strata(con_tabla, adaptador.fetch(con_tabla))
    plano = adaptador.strata(sin_tabla, adaptador.fetch(sin_tabla))

    assert combinadas == frozenset({"celdas-combinadas"})
    assert plano == frozenset({"sin-tabla"})
    assert combinadas == adaptador.strata(con_tabla, adaptador.fetch(con_tabla))


def test_la_licencia_y_la_privacidad_salen_del_perfil_sin_tocar() -> None:
    """Son código, no un README (regla de oro 5), y la atribución es literal.

    ADR-0031, condición 5: la atribución va **con las palabras de la licencia**.
    Reescribirla aquí sería redistribuir con una atribución que el organismo no ha
    autorizado.
    """
    adaptador = _adaptador()

    licencia = adaptador.license()
    privacidad = adaptador.privacy()

    assert (
        licencia.attribution == "Basado en datos de la Agencia Estatal Boletín Oficial del Estado"
    )
    assert licencia.may_redistribute_content is True
    assert privacidad.contains_personal_data is True
    assert privacidad.special_categories is False, "con esto en True no se registraría"
