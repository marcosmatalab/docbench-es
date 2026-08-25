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
from docbench_es.errors import PolicyViolation
from docbench_es.extract.base import (
    DECLARACIONES,
    METODOS,
    Extractor,
    FamiliaExtractor,
    cumple_la_forma,
    descriptor,
    expresa_spans,
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
    # Se CONSTRUYE sin el miembro. Quitárselo a una subclase con `delattr` no vale:
    # el miembro sigue heredado y `hasattr` lo encuentra igual. La primera versión de
    # este test hacía eso y pasaba en verde contra impostores completos.
    assert quitado in vars(_Falso), f"{quitado} no está en `_Falso`: el molde está mal"
    miembros = {k: v for k, v in vars(_Falso).items() if k != quitado and not k.startswith("__")}
    cojo = type("Cojo", (), miembros)
    assert not isinstance(cojo(), Extractor), f"le falta `{quitado}` y aun así pasa"


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

    # Construido SIN el miembro, no heredándolo y borrándolo: `del` sobre una subclase
    # deja el atributo de la base intacto. Es la TERCERA vez en esta sesión que ese
    # atajo produce un impostor completo disfrazado de incompleto.
    def _init(self: object) -> None:
        self.benchcore_api = "1.0"  # type: ignore[attr-defined]

    miembros = {k: v for k, v in vars(_Falso).items() if not k.startswith("__")}
    del miembros["benchcore_api"]
    tarde = type("_Tarde", (), {**miembros, "__init__": _init})

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
