"""§14 · Que el contrato de entidad es **implementable, uniforme y comprobable**.

Los cuatro adaptadores falsos de ADR-0032 pasan por el mismo aro, y el cuarto —el
de carpeta, sin API y sin verdad— es el que decide qué puede exigir el contrato:
si mañana alguien lo endurece de forma que una carpeta de PDFs no pueda cumplirlo,
se cae un test aquí, en la puerta, y no un hito dentro de dos meses.

**La otra mitad, que es la que valida la suite:** `AdaptadorRoto` incumple cinco
aros a propósito. Sin él, una suite que no comprobara nada saldría igual de verde,
y *«el motor es agnóstico a la entidad»* volvería a ser una frase de folleto con
tests al lado. Es el mismo argumento que los tests de degradación de §14.

Sin red: los cuatro falsos leen de un `dict`.
"""

from __future__ import annotations

from datetime import date

import pytest

from _adaptadores_falsos import AdaptadorAnotado, AdaptadorCarpeta, AdaptadorDerivado
from _adaptadores_rotos import AdaptadorRoto, SinVersion, VersionSoloEnInstancia
from conftest import Registrar
from docbench_es.entity.conformance import comprobar
from docbench_es.entity.registry import cargar

ETIQUETAS = frozenset(
    {"nacido-digital", "escaneado", "sin-tabla", "tabla-simple", "celdas-combinadas", "multipagina"}
)
"""Lo que declararía un perfil. **Se pasa siempre y explícitamente**: desde el
cierre de L3 `comprobar` ya no tiene valor por defecto, porque `None` dejaba
`pasa` en True habiendo omitido el aro del subconjunto sin decirlo."""

DESDE = date(2026, 1, 1)
HASTA = date(2026, 12, 31)
"""La ventana que cubre los tres documentos de la carpeta falsa."""


@pytest.mark.parametrize(
    "adaptador",
    [AdaptadorCarpeta(), AdaptadorDerivado(), AdaptadorAnotado()],
    ids=["carpeta-sin-verdad", "derivado-con-verdad", "anotado-sin-verdad"],
)
def test_los_tres_adaptadores_bien_escritos_pasan_sin_un_solo_hallazgo(
    adaptador: object,
) -> None:
    """Demuestra que el contrato es **implementable por los tres modos de verdad**.

    El de carpeta es el que aprieta: `truth_mode = NONE`, glosario vacío, cero
    tráfico y dos etiquetas de estrato. Que pase el mismo aro que el `DERIVED` es
    exactamente lo que §14 pide demostrar — que el contrato es uniforme y no una
    plantilla escrita alrededor del BOE.
    """
    informe = comprobar(adaptador, desde=DESDE, hasta=HASTA, etiquetas_perfil=ETIQUETAS)

    assert informe.hallazgos == (), informe.resumen()
    assert informe.pasa
    assert informe.n_documentos == 3


def test_el_adaptador_roto_se_cae_por_los_cinco_aros_que_rompe() -> None:
    """Demuestra que la suite DETECTA, que es lo que la valida.

    Cinco incumplimientos y cinco comprobaciones en rojo. Si mañana alguien borra
    una comprobación por descuido, este test dice **cuál** falta en vez de pasar
    en verde con una suite más floja.
    """
    informe = comprobar(AdaptadorRoto(), desde=DESDE, hasta=HASTA, etiquetas_perfil=ETIQUETAS)

    fallos = {h.comprobacion for h in informe.hallazgos if h.severidad == "FALLA"}

    assert fallos == {
        "discover perezoso",
        "fetch idempotente",
        "fetch íntegro",
        "truth sii DERIVED",
        "strata determinista",
    }, informe.resumen()
    assert not informe.pasa


def test_una_ventana_sin_documentos_no_cuenta_como_aprobado() -> None:
    """Demuestra que «no se ha comprobado» no se publica como «cumple».

    Es la familia de fallos que este repo persigue: **publicar como observado algo
    que no se observó**. Sin documentos, `fetch`, `truth` y `strata` no se han
    ejercitado, así que el informe lo dice y `pasa` es `False` — un aro por el que
    no se ha pasado no está superado.
    """
    informe = comprobar(
        AdaptadorCarpeta(),
        desde=date(2030, 1, 1),
        hasta=date(2030, 12, 31),
        etiquetas_perfil=ETIQUETAS,
    )

    (sin_ejecutar,) = [h for h in informe.hallazgos if h.severidad == "NO_EJECUTADA"]

    assert sin_ejecutar.comprobacion == "documentos"
    assert not informe.pasa
    assert informe.n_documentos == 0


def test_la_version_declarada_solo_en_la_instancia_la_caza_la_suite() -> None:
    """Demuestra que el error de ADR-0036 se diagnostica **aquí y no en el registro**.

    En el registro, un `benchcore_api` que sólo existe en la instancia se rechaza
    con *«no declara `benchcore_api`»*, que es cierto y confuso a la vez: quien lo
    escribió está mirando la línea donde lo declara. La suite sí tiene instancia
    con la que comparar, así que puede decir qué pasa de verdad.
    """
    informe = comprobar(
        VersionSoloEnInstancia(), desde=DESDE, hasta=HASTA, etiquetas_perfil=ETIQUETAS
    )

    (hallazgo,) = [h for h in informe.hallazgos if h.comprobacion == "benchcore_api"]

    assert hallazgo.severidad == "FALLA"
    assert "clase" in hallazgo.detalle
    assert not informe.pasa


def test_lo_que_ni_siquiera_tiene_la_forma_dice_que_le_falta() -> None:
    """Demuestra que el primer mensaje es útil, no un `AttributeError`.

    Quien está escribiendo su adaptador quiere la lista de lo que le falta de una
    vez —que es por lo que la suite devuelve hallazgos en vez de lanzar en el
    primero—, y no descubrir un método por corrida.
    """
    informe = comprobar(SinVersion(), desde=DESDE, hasta=HASTA, etiquetas_perfil=ETIQUETAS)

    (hallazgo,) = informe.hallazgos

    assert hallazgo.comprobacion == "forma"
    assert "benchcore_api" in hallazgo.detalle
    assert "discover" in hallazgo.detalle
    assert not informe.pasa


def test_el_contrato_no_exige_etiquetas_concretas_pero_si_que_esten_en_el_perfil() -> None:
    """Demuestra la fila más dura de ADR-0032, en sus dos mitades.

    **No se puede exigir** un conjunto fijo de etiquetas: `celdas-combinadas`,
    `multipagina` y `sin-tabla` exigen ver tablas, y ver tablas exige un extractor
    que el núcleo no puede importar. Lo que **sí** se exige es que lo que emita
    esté declarado en el perfil: un estrato que nadie declaró no se puede ponderar
    en el informe, así que sería una etiqueta que no llega a ninguna tabla.
    """
    completo = comprobar(
        AdaptadorCarpeta(),
        desde=DESDE,
        hasta=HASTA,
        etiquetas_perfil=frozenset({"nacido-digital", "escaneado"}),
    )
    incompleto = comprobar(
        AdaptadorCarpeta(),
        desde=DESDE,
        hasta=HASTA,
        etiquetas_perfil=frozenset({"nacido-digital"}),
    )

    assert completo.pasa, completo.resumen()
    assert not incompleto.pasa
    assert {h.comprobacion for h in incompleto.hallazgos} == {"strata dentro del perfil"}


def test_un_adaptador_registrado_por_entry_point_pasa_la_suite(registrar: Registrar) -> None:
    """Demuestra el camino ENTERO: registro y contrato encajan.

    Es el que cierra el círculo de ADR-0036. Los tests del registro prueban que un
    adaptador de fuera se descubre; éste prueba que lo que se descubre **sirve**:
    se carga por su nombre, se construye con lo que traiga, y pasa el mismo aro
    que los propios. Sin esto, L13 podría descubrir un adaptador que el motor no
    sabe usar.
    """
    registrar("carpeta-de-fuera", "_adaptadores_falsos:AdaptadorCarpeta")

    clase = cargar("carpeta-de-fuera")

    # Lo que se descubre es la CLASE, no una instancia (ADR-0036): construirla es
    # de quien monta la campaña, porque es quien tiene el perfil.
    assert isinstance(clase, type)
    informe = comprobar(clase(), desde=DESDE, hasta=HASTA, etiquetas_perfil=ETIQUETAS)

    assert informe.pasa, informe.resumen()
