"""Que `may_send_to_third_party: false` **bloquea de verdad**, y no es decorativo.

**Por qué este fichero existe hoy y no en L8.** ADR-0037 pone el campo del BOE en
`false`. Una decisión de privacidad cuya ruta de rechazo no se ejercita es una
decisión que nadie sabe si funciona — y ésta no volvería a mirarse hasta L12, que
es el primer hito con extractores por API. Ocho hitos de código muerto.

Es una barrera, así que va con **las dos direcciones**: bloquea la combinación
prohibida y **deja pasar** todo lo demás. Una puerta que dijera «no» a todo pasaría
igual de verde el primer test y rompería la campaña entera en el segundo.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from benchcore.types import PrivacyDecl

from docbench_es.core.policy import ExtractorDeclarado, exigir_egress_permitido
from docbench_es.entity.base import cargar_perfil
from docbench_es.errors import DocbenchError, PolicyViolation

RAIZ = Path(__file__).resolve().parents[2]

LOCAL = ExtractorDeclarado(id="pymupdf4llm", runs_locally=True)
OTRO_LOCAL = ExtractorDeclarado(id="camelot", runs_locally=True)
POR_API = ExtractorDeclarado(id="vlm-de-pago", runs_locally=False)
OTRO_API = ExtractorDeclarado(id="otro-vlm", runs_locally=False)

SIN_TERCEROS = PrivacyDecl(contains_personal_data=True, may_send_to_third_party=False)
CON_TERCEROS = PrivacyDecl(contains_personal_data=True, may_send_to_third_party=True)


def test_la_campana_no_arranca_con_un_extractor_por_api_y_la_fuente_cerrada() -> None:
    """**El caso que la puerta existe para parar**, y con su código de salida.

    El 2 no es cosmético: separa *«la medición salió peor de lo tolerado»* (1) de
    *«la campaña no llegó a arrancar porque la política lo prohíbe»*. Si los dos
    salieran con el mismo código, un equipo aprendería a ignorar el rojo — que es
    el argumento de §11 y del límite 25.
    """
    with pytest.raises(PolicyViolation) as capturado:
        exigir_egress_permitido(SIN_TERCEROS, [LOCAL, POR_API])

    assert capturado.value.exit_code == 2
    assert isinstance(capturado.value, DocbenchError)
    assert "vlm-de-pago" in str(capturado.value)


def test_los_nombra_a_todos_y_no_solo_al_primero() -> None:
    """Quien monta la campaña quiere quitarlos de una vez, no uno por corrida.

    Es el mismo criterio que la suite de conformidad: devolver todos los hallazgos
    en vez de lanzar en el primero.
    """
    with pytest.raises(PolicyViolation) as capturado:
        exigir_egress_permitido(SIN_TERCEROS, [POR_API, LOCAL, OTRO_API])

    mensaje = str(capturado.value)
    assert "otro-vlm" in mensaje and "vlm-de-pago" in mensaje
    assert "2 extractor" in mensaje


def test_con_la_fuente_cerrada_pero_todo_local_la_campana_arranca() -> None:
    """**La otra dirección.** Sin esto, una puerta que lanzara siempre pasaría el test
    de arriba y dejaría a L5 sin poder medir nada: sus ocho extractores son locales.
    """
    exigir_egress_permitido(SIN_TERCEROS, [LOCAL, OTRO_LOCAL])


def test_con_la_fuente_abierta_el_extractor_por_api_pasa() -> None:
    """La puerta mira **la declaración de la fuente**, no su propio gusto.

    Si bloqueara siempre lo remoto, no sería una política: sería una prohibición
    escrita en el código, y el campo del perfil no significaría nada.
    """
    exigir_egress_permitido(CON_TERCEROS, [LOCAL, POR_API])


def test_una_campana_sin_extractores_no_es_una_violacion() -> None:
    """Cero extractores es un plan vacío, que es un problema de otro sitio.

    Que esta puerta lo tratara como violación de política mandaría a alguien a
    revisar la privacidad de la fuente cuando lo que pasa es que el plan está mal.
    """
    exigir_egress_permitido(SIN_TERCEROS, [])


def test_un_perfil_que_se_olvida_del_campo_falla_cerrado(tmp_path: Path) -> None:
    """**No contestar la pregunta no puede valer como un sí.**

    `PrivacyDecl` trae `True` por defecto, y ese defecto es el permisivo. Aquí se
    invierte a propósito (ADR-0037): un perfil al que se le olvida el campo no ha
    dicho que sí — no ha dicho nada. Si el defecto fuera permisivo, la forma más
    fácil de abrir el egress de una entidad sería **olvidarse de declararlo**, que
    es justo lo contrario de lo que una puerta tiene que premiar.
    """
    yaml = (RAIZ / "entities" / "boe.yaml").read_text(encoding="utf-8")
    sin_campo = "\n".join(
        ln for ln in yaml.splitlines() if not ln.strip().startswith("may_send_to_third_party")
    )
    ruta = tmp_path / "sin-campo.yaml"
    ruta.write_text(sin_campo, encoding="utf-8")

    perfil = cargar_perfil(ruta)

    assert perfil.privacidad.may_send_to_third_party is False
    with pytest.raises(PolicyViolation):
        exigir_egress_permitido(perfil.privacidad, [POR_API])


def test_el_perfil_real_del_boe_rechaza_hoy_un_extractor_por_api() -> None:
    """**La decisión de ADR-0037, viva y ejercitada, no una línea en un YAML.**

    No usa una declaración inventada: carga `entities/boe.yaml` tal cual está en el
    repo. Si alguien pusiera el campo en `true` sin pasar por el ADR, este test se
    cae y le obliga a ir a leerlo — que es exactamente lo que se quiere de aquí a
    L12, cuando la decisión se revisa con el caso delante.
    """
    perfil = cargar_perfil(RAIZ / "entities" / "boe.yaml")

    assert perfil.privacidad.may_send_to_third_party is False, "ADR-0037: se revisa en L12"
    with pytest.raises(PolicyViolation):
        exigir_egress_permitido(perfil.privacidad, [POR_API])
    # Y los ocho extractores locales de L5 siguen pudiendo medir el BOE entero.
    exigir_egress_permitido(perfil.privacidad, [LOCAL, OTRO_LOCAL])
