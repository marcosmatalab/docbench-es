"""El `Protocol` de extractor: que existe, qué exige, y qué NO puede exigir.

`extract/base.py` se escribe **antes que cualquier implementación**, que es la regla
del repo: contrato primero. Un `Protocol` sin test es una afirmación — describe algo y
nadie comprueba que describa lo que dice.

## Lo que este fichero afirma, y lo que deja explícitamente sin cubrir

**Afirma la FORMA, y sobre QUÉ opera cada mitad**, porque son dos caminos distintos y
el registro sólo puede usar uno:

* `isinstance(instancia, Extractor)` — necesita **una instancia**. Sirve donde ya hay
  extractor construido.
* `cumple_la_forma(clase)` — mira **la clase**, sin construir. Es lo que el registro
  necesita, porque `issubclass` contra un `Protocol` con atributos de dato lanza
  `TypeError`. Los dos se prueban aquí, y con el mismo impostor.

Y el puente a la puerta de egress traduce los dos campos que la puerta pide.

**NO afirma la CONDUCTA.** Que `extract` no lance, que `cost_of` sea pura y que
`expresses_spans` no mienta **no se pueden mirar sin ejecutar el extractor contra
documentos**, y eso es la suite de conformidad, que llega con el primer extractor real.
Se dice aquí porque un test de forma que no declara su alcance invita a leerlo como si
cubriera el contrato entero — y el contrato entero es justo lo que no cubre.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, get_type_hints

import pytest

from docbench_es.core.policy import ExtractorDeclarado, exigir_egress_permitido
from docbench_es.errors import ContractViolation, PolicyViolation
from docbench_es.extract.base import (
    DECLARACIONES,
    METODOS,
    Extractor,
    FamiliaExtractor,
    cumple_la_forma,
    descriptor,
    expresa_spans,
    veredicto_de_spans,
)
from docbench_es.types import FORMATOS_CANONICOS

if TYPE_CHECKING:  # pragma: no cover
    from benchcore.types import Cost, ProbeResult

    from docbench_es.types import Extraction, RawDoc

# Las listas se IMPORTAN de `base`, no se copian: una segunda enumeración de los
# miembros de §7.2 podría quedarse vieja y el test seguiría verde comprobando cinco.


class _Falso:
    """Un extractor de mentira. **No extrae nada**: existe para mirar la forma.

    No vive en `src/`, y eso es la regla de oro 1 en su forma más literal: este repo no
    construye extractores. Éste no compite, no se registra y no aparece en ninguna
    tabla — es un molde con la forma del hueco.
    """

    id = "falso"
    version = "0"
    # Anotado con el `Literal` a propósito: sin la anotación, mypy infiere `str` y
    # el molde deja de cumplir el `Protocol` **en tiempo de tipos** mientras lo
    # cumple en tiempo de ejecución. Las dos comprobaciones tienen que decir lo mismo.
    kind: FamiliaExtractor = "parser"
    runs_locally = True
    expresses_spans = False
    benchcore_api = "1.0"

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        raise NotImplementedError

    def cost_of(self, ex: Extraction) -> Cost:
        raise NotImplementedError

    def probe(self) -> ProbeResult:
        raise NotImplementedError


def sin(miembro: str, **extra: object) -> type:
    """Un impostor de `_Falso` **construido sin** ese miembro. Nunca heredándolo.

    ## Por qué esto es una función y no tres líneas repetidas

    Porque el atajo obvio —heredar de `_Falso` y `delattr` el miembro— **produce un
    impostor completo disfrazado de incompleto**: el atributo sigue en la clase base y
    `hasattr` lo encuentra. Cayó **tres veces en la misma sesión**, y un tropiezo que
    vuelve tres veces no se arregla acordándose: se arregla quitando la ocasión.

    Aquí no hay nada que recordar. Y el `assert` de abajo hace que un miembro mal
    escrito reviente en vez de construir un impostor al que no le falta nada — que es la
    otra forma de que este molde mienta.
    """
    assert miembro in vars(_Falso), f"`{miembro}` no está en `_Falso`: el molde está mal"
    miembros = {k: v for k, v in vars(_Falso).items() if not k.startswith("__")}
    del miembros[miembro]
    return type(f"Sin{miembro.title()}", (), {**miembros, **extra})


def test_el_molde_de_impostores_quita_de_verdad_lo_que_dice_que_quita() -> None:
    """**El control del mecanismo.** Sin esto, `sin()` podría devolver la clase entera y
    todos los controles negativos de abajo pasarían en verde sin comprobar nada — que es
    literalmente lo que pasaba con `delattr`."""
    assert hasattr(_Falso, "benchcore_api")
    assert not hasattr(sin("benchcore_api"), "benchcore_api")
    assert hasattr(sin("benchcore_api"), "id"), "quitó de más"


def test_el_protocol_declara_los_seis_miembros_y_los_tres_metodos() -> None:
    """§7.2 al pie de la letra. Si el manual gana un campo, esto se cae y lo nombra."""
    anotados = set(get_type_hints(Extractor))
    faltan = [n for n in DECLARACIONES if n not in anotados]
    assert not faltan, f"`Extractor` no declara {faltan}; §7.2 los exige"
    sin_metodo = [n for n in METODOS if not hasattr(Extractor, n)]
    assert not sin_metodo, f"`Extractor` no tiene {sin_metodo}"


def test_un_extractor_con_los_seis_miembros_cumple_la_forma() -> None:
    assert isinstance(_Falso(), Extractor)


@pytest.mark.parametrize("quitado", [*DECLARACIONES, *METODOS])
def test_al_que_le_falta_un_solo_miembro_no_cumple(quitado: str) -> None:
    """**El control negativo, miembro a miembro.**

    Sin esto, `isinstance` contra un `Protocol` podría estar mirando cero cosas y su
    verde significaría «no encontré nada» en vez de «cumple». Se quita uno cada vez
    porque quitar todos a la vez no distingue entre comprobar seis y comprobar uno.
    """
    assert not isinstance(sin(quitado)(), Extractor), f"le falta `{quitado}` y aun así pasa"


def test_el_puente_a_la_puerta_de_egress_traduce_los_dos_campos() -> None:
    """`core` no puede importar `extract`, así que la puerta recibe dos campos."""
    d = descriptor(_Falso())
    assert d == ExtractorDeclarado(id="falso", runs_locally=True)


def test_un_extractor_no_local_hace_saltar_la_puerta_por_el_puente() -> None:
    """**Regla de oro 5, de punta a punta.** Es lo que hace que el puente valga algo:
    no que traduzca, sino que lo traducido llegue a la puerta y ésta se niegue."""
    from benchcore.types import PrivacyDecl

    class _Remoto(_Falso):
        id = "remoto"
        runs_locally = False

    cerrada = PrivacyDecl(
        contains_personal_data=True,
        categories=frozenset(),
        special_categories=False,
        lawful_basis="interes legitimo",
        redaction_required=False,
        redaction_profile=None,
        may_send_to_third_party=False,
        dpa_reference=None,
    )
    with pytest.raises(PolicyViolation, match="remoto"):
        exigir_egress_permitido(cerrada, [descriptor(_Remoto())])

    import dataclasses

    abierta = dataclasses.replace(cerrada, may_send_to_third_party=True)
    exigir_egress_permitido(abierta, [descriptor(_Remoto())])  # no lanza


def test_cumple_la_forma_mira_la_clase_y_publica_su_denominador() -> None:
    """El camino que el registro sí puede usar: **sin construir nada**."""
    forma = cumple_la_forma(_Falso)
    assert forma.cumple
    assert len(forma.comprobados) == len(DECLARACIONES) + len(METODOS)
    assert "9 miembros comprobados" in str(forma), (
        f"un guardián que no dice sobre cuántas cosas mira no dice nada: {forma}"
    )


def test_un_extractor_que_declara_la_api_en_init_no_pasa_sobre_la_clase() -> None:
    """**El control negativo de `cumple_la_forma`, y la regla que hace posible el
    registro.** `descubrir no construye`: si `benchcore_api` se asigna en `__init__`, la
    clase no lo tiene y el registro no ve versión. Esto es lo que lo detecta, y es la
    diferencia real entre mirar la clase y mirar una instancia — sobre la INSTANCIA este
    impostor pasaría.
    """

    def _init(self: object) -> None:
        self.benchcore_api = "1.0"  # type: ignore[attr-defined]

    tarde = sin("benchcore_api", __init__=_init)

    forma = cumple_la_forma(tarde)
    assert not forma.cumple and forma.faltan == ("benchcore_api",), str(forma)
    # Y la mitad que lo hace significar algo: sobre la instancia, pasa.
    assert isinstance(tarde(), Extractor)


@pytest.mark.parametrize(
    ("formato", "espera"),
    [("html", True), ("tei", True), ("dataframe", True), ("markdown", False), ("text", False)],
)
def test_expresa_spans_se_deriva_del_formato_en_las_dos_direcciones(
    formato: str, espera: bool
) -> None:
    """**Regla de oro 4, en su origen.** `.claude/rules/extractores.md`: lo fija el
    conversor según el formato, no el extractor.

    Se afirma en las DOS direcciones —los tres que sí y los dos que no— porque una
    función que devolviera siempre `True` pasaría un test que sólo mirase HTML, y su
    consecuencia sería puntuar con un cero a quien no podía competir.

    Los cinco son `types.FORMATOS_CANONICOS` al completo: si aparece un sexto, este test
    no lo cubre y hay que decidir de qué lado cae.
    """
    assert set(FORMATOS_CANONICOS) == {"html", "tei", "dataframe", "markdown", "text"}, (
        "los formatos canónicos han cambiado: este test cubre cinco y hay que revisarlo"
    )
    assert expresa_spans(formato) is espera


@pytest.mark.parametrize("desconocido", ["markdow", "Markdown", "md", "MARKDOWN", "", "lo-que-sea"])
def test_un_formato_desconocido_no_concede_spans_por_defecto(desconocido: str) -> None:
    """**El control negativo del fallo abierto, que es el que importa aquí.**

    La primera versión preguntaba `not in FORMATOS_SIN_SPANS` sobre un `str` sin acotar,
    así que **todo lo desconocido concedía spans** — una letra de menos, una mayúscula,
    otro nombre para el mismo formato, la cadena vacía. Y conceder spans indebidamente es
    la dirección cara: el extractor cobra un cero en el estrato titular como si hubiera
    competido, cuando lo que pasó es que su formato no llegaba.

    Se prueban seis formas de equivocarse y no una, porque un solo caso no distingue
    «levanta ante lo desconocido» de «levanta ante esta cadena concreta».
    """
    with pytest.raises(ContractViolation, match="desconocido"):
        expresa_spans(desconocido)


@pytest.mark.parametrize(
    ("declarado", "formato", "emitio", "ocasion", "espera"),
    [
        (True, "markdown", False, True, "CONTRADICCION"),
        (True, "text", True, True, "CONTRADICCION"),
        (False, "html", True, True, "ESCONDIDO"),
        (False, "tei", True, False, "ESCONDIDO"),
        (False, "html", False, False, "SIN_EVIDENCIA"),
        (False, "tei", False, False, "SIN_EVIDENCIA"),
        (False, "html", False, True, "COHERENTE"),
        (True, "html", False, True, "COHERENTE"),
        (True, "dataframe", True, True, "COHERENTE"),
        (False, "markdown", False, False, "COHERENTE"),
    ],
)
def test_el_contraste_tiene_cuatro_desenlaces_y_no_dos(
    declarado: bool, formato: str, emitio: bool, ocasion: bool, espera: str
) -> None:
    """**La regla, afirmada antes de que exista la suite que la aplica.**

    Las tres casillas que una igualdad se comería son las que sostienen el incentivo:

    * `ESCONDIDO` — declararse incapaz **trayendo** celdas combinadas es refugiarse en
      `NO_APLICABLE`. Es la razón que `types._invariantes._spans_declarados` ya tenía
      escrita para `CanonicalTable`, y aquí se aplica al extractor entero.
    * `SIN_EVIDENCIA` — declararse incapaz sin que el conjunto ofreciera **ni una**
      celda combinada no es un aprobado: no distingue «su parser las aplana» de «no le
      tocó ninguna».
    * Y la que hace que el honesto pueda aprobar: **mismo caso con ocasión → COHERENTE**.
      Las dos filas de `html` con `emitio=False` sólo se diferencian en `ocasion`, y dan
      veredictos distintos. Sin ese dato, un extractor que de verdad aplana se quedaría
      en `SIN_EVIDENCIA` para siempre por hacer lo que declara.
    """
    assert veredicto_de_spans(declarado, formato, emitio, ocasion) == espera
