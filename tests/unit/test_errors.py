"""§6.9 y §11 · Qué demuestra cada test de este fichero."""

from __future__ import annotations

from typing import get_args

from benchcore.errors import BenchcoreError

from docbench_es import errors
from docbench_es.errors import (
    AdapterError,
    BudgetExceeded,
    ContractViolation,
    DocbenchError,
    PolicyViolation,
    TruthUnavailable,
)
from docbench_es.types import ExtractionFailure

# §11, literal. Si el manual cambia un código, este test se pone rojo y hay que
# venir aquí a cambiarlo a mano: es justo lo que se quiere.
CODIGOS_DEL_MANUAL = {
    DocbenchError: 1,
    PolicyViolation: 2,
    BudgetExceeded: 3,
    AdapterError: 4,
    ContractViolation: 5,
    TruthUnavailable: 6,
}

# §6.9, literal. Enum CERRADO, ocho causas, ni una más.
CAUSAS_DEL_MANUAL = {
    "timeout",
    "out_of_memory",
    "unsupported_format",
    "corrupt_pdf",
    "encrypted_pdf",
    "no_text_layer",
    "provider_error",
    "policy_blocked",
}


def test_un_except_del_motor_caza_lo_que_lance_el_plugin_de_un_cliente() -> None:
    """Demuestra que la promesa de extensibilidad no se rompe en los errores.

    El motor captura `BenchcoreError`, que es lo que puede lanzar el plugin de
    un cliente. Si las excepciones de este repo solo heredaran de
    `DocbenchError`, una violación de política lanzada por el motor escaparía
    de ese `except` y la campaña reventaría con traza en vez de con el código
    de salida 2. Las tres cuyo significado coincide heredan de las dos.
    """
    for clase in (PolicyViolation, BudgetExceeded, ContractViolation):
        assert issubclass(clase, DocbenchError)
        assert issubclass(clase, BenchcoreError)

    # Las dos que NO tienen equivalente en el contrato no lo fingen.
    for clase in (AdapterError, TruthUnavailable):
        assert issubclass(clase, DocbenchError)
        assert not issubclass(clase, BenchcoreError)


def test_la_tabla_de_codigos_de_salida_es_codigo_y_no_prosa() -> None:
    """Demuestra que separar el 2 y el 4 del 1 sobrevive al tiempo.

    §11 lo dice con todas las letras: *«separar el 4 y el 2 del 1 es lo que
    evita que un equipo aprenda a ignorar el rojo»*. «La medición salió peor de
    lo tolerado» (1), «la campaña no arrancó porque la licencia lo prohíbe» (2)
    y «se cayó el proveedor» (4) exigen tres reacciones distintas. Mientras esa
    tabla viva solo en un manual, el día que alguien añada un error nuevo lo
    dejará en el 1 por defecto y las tres se volverán la misma.
    """
    for clase, codigo in CODIGOS_DEL_MANUAL.items():
        assert clase.exit_code == codigo, f"{clase.__name__} debería salir con {codigo}"

    # Ningún código repetido: dos causas distintas no pueden salir iguales.
    codigos = [c.exit_code for c in CODIGOS_DEL_MANUAL]
    assert len(set(codigos)) == len(codigos)

    # Y ningún error del proyecto se queda fuera de la tabla.
    declarados = {getattr(errors, n) for n in errors.__all__}
    assert declarados == set(CODIGOS_DEL_MANUAL)


def test_el_enum_de_fallo_de_extraccion_esta_cerrado() -> None:
    """Demuestra que ningún fallo puede esconderse en un cajón de sastre.

    La tasa de fallo por extractor **es un resultado**, no un detalle de
    implementación. Un enum abierto, o uno con un `"other"` dentro, permitiría
    que un documento que revienta se registre como «otro» y desaparezca del
    informe, y con él la mitad mala de la nota de un extractor.
    """
    causas = set(get_args(ExtractionFailure))

    assert causas == CAUSAS_DEL_MANUAL
    assert not {c for c in causas if c in {"other", "otro", "unknown", "desconocido"}}
