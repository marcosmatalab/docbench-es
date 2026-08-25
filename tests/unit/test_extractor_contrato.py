"""El `Protocol` de extractor: que existe, qué exige, y qué NO puede exigir.

`extract/base.py` se escribe **antes que cualquier implementación**, que es la regla
del repo: contrato primero. Un `Protocol` sin test es una afirmación — describe algo y
nadie comprueba que describa lo que dice.

## Lo que este fichero afirma, y lo que deja explícitamente sin cubrir

**Afirma la FORMA**: los seis miembros de §7.2 están, un impostor al que le falte uno
no pasa por `isinstance`, y el puente a la puerta de egress traduce los dos campos que
la puerta pide.

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
from docbench_es.extract.base import Extractor, FamiliaExtractor, descriptor

if TYPE_CHECKING:  # pragma: no cover
    from benchcore.types import Cost, ProbeResult

    from docbench_es.types import Extraction, RawDoc

# Los seis de §7.2, para poder decir CUÁL falta y no sólo que algo falta.
DECLARACIONES = ("id", "version", "kind", "runs_locally", "expresses_spans", "benchcore_api")
METODOS = ("extract", "cost_of", "probe")


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
