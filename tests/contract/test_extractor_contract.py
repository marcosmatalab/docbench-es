"""§8 · La conformidad de **todos** los extractores registrados, contra documentos reales.

`.claude/rules/extractores.md` fija el criterio de terminado de un extractor en uno solo:
`docbench conform --extractor <id>` en verde. Esto es ese mismo aro corrido por el CI de
`make full`, y **sobre el registro**, no sobre una lista escrita a mano: el día que entre
`camelot` no hay que acordarse de añadirlo aquí.

**Por qué no está en `tests/unit`.** Necesita dos cosas que la puerta no tiene: el corpus
de L3 —361 MB, fuera de git, LIMITS 74— y el extra `extract-local`, que arrastra torch y
CUDA. Lo que sí corre en la puerta es la mitad que decide si un número está bien puesto:
las declaraciones, el aro del conversor y el conjunto (`tests/unit/test_pdfplumber.py`,
`tests/unit/test_conjunto.py`).

Y se salta con su razón dicha, no en silencio: un aro que no se ha corrido no es un aro
superado, que es la regla que la propia suite aplica con `NO_EJECUTADA`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from docbench_es.corpus.store import Almacen
from docbench_es.extract.conformance import comprobar
from docbench_es.extract.conjunto import cargar_conjunto
from docbench_es.extract.registry import descubrir

RAIZ = Path(__file__).resolve().parents[2]
PLAN = RAIZ / "runs" / "l5" / "conformidad.yaml"
MANIFIESTO = RAIZ / "runs" / "l3" / "manifiesto.json"
DOCS = RAIZ / "runs" / "l3" / "docs"
FIXTURES = RAIZ / "runs" / "l4" / "fixtures"

sin_corpus = pytest.mark.skipif(
    not (MANIFIESTO.exists() and DOCS.exists()),
    reason="el corpus de L3 no está en git (LIMITS 74): `uv run python scripts/cosechar_boe.py`",
)

REGISTRADOS = [r.name for r in descubrir()]


def test_hay_extractores_registrados() -> None:
    """El control negativo de la parametrización de abajo: con el grupo vacío, el
    parametrize recorrería cero casos y `make full` saldría verde sin comprobar nada."""
    assert REGISTRADOS, "el grupo `docbench.extractor` no trae ninguno"


@sin_corpus
@pytest.mark.parametrize("nombre", REGISTRADOS)
def test_el_extractor_pasa_la_suite_de_conformidad(nombre: str) -> None:
    """El mismo aro para el propio y para el ajeno. **Y con su denominador en el fallo.**"""
    from docbench_es.extract.registry import cargar

    clase = cargar(nombre)
    assert isinstance(clase, type), f"{nombre} no carga una clase"
    conjunto = cargar_conjunto(PLAN, Almacen(MANIFIESTO, DOCS), FIXTURES)
    informe = comprobar(clase(), conjunto.casos)
    detalle = "\n".join(
        f"    [{h.severidad}] {h.comprobacion}: {h.detalle}" for h in informe.hallazgos
    )
    assert informe.pasa, f"{informe}\n  conjunto: {conjunto}\n{detalle}"


@sin_corpus
def test_el_conjunto_de_conformidad_puede_producir_lo_que_declara() -> None:
    """Si el conjunto no trajera ni una celda combinada, TODO extractor saldría
    `SIN_EVIDENCIA` y el veredicto no discriminaría nada: un verde que no significa lo que
    parece. Se comprueba aquí porque necesita los PDF; su mitad versionada corre en la
    puerta, en `tests/unit/test_conjunto_conformidad.py`."""
    conjunto = cargar_conjunto(PLAN, Almacen(MANIFIESTO, DOCS), FIXTURES)
    assert conjunto.hay_ocasion, str(conjunto)
    assert len(conjunto.casos) >= 2
    assert sum(not c.trae_combinadas for c in conjunto.casos) >= 1, (
        "hace falta al menos uno SIN combinadas, o un extractor que las invente donde no "
        "las hay pasaría"
    )
