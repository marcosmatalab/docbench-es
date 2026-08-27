"""`StructureMetrics` no se puede construir mintiendo sobre su régimen. **ADR-0045.**

Este tipo se declaró en L0 y **nadie lo había rellenado nunca**. Su primer productor es el
nivel 1 de L5, y el PASO 0 sobre él —la misma pregunta que encontró lo de `dataframe`—
sacó dos defectos, los dos de la familia *«un número cuyo denominador o cuyo régimen no
viaja en el artefacto»*:

* **`ci` era obligatorio** sobre una población que es un **censo** —los 338 con tabla—, y
  ADR-0015 dice que un censo no es una estimación y va sin intervalo. El tipo obligaba a
  inventar un `(x, x)` o a quitar el intervalo de donde sí hace falta;
* **`teds` no decía cuál de los tres agregados era**, y `ponderacion.yaml` ya había
  decidido —antes de medir— que los tres dan números distintos.

Lo que estos tests fijan es la parte que no se puede olvidar: el objeto **incoherente no
se construye**. Es el mismo mecanismo que `Extraction` usa con `failed` y `failure_reason`,
y la dirección que importa es la segunda —`CENSO` con `ci`—, porque sin ella un intervalo
ausente y uno olvidado se leen igual.
"""

from __future__ import annotations

import pytest

from docbench_es.types import Agregado, Regimen, StructureMetrics


def _metricas(**cambios: object) -> StructureMetrics:
    base: dict[str, object] = {
        "teds": 0.87,
        "teds_s": 0.91,
        "cell_f1": 0.83,
        "evaluable_coverage": 0.37,
        "failures": {},
        "n_documents": 338,
        "agregado": "POR_DOCUMENTO",
        "regimen": "CENSO",
    }
    base.update(cambios)
    return StructureMetrics(**base)  # type: ignore[arg-type]


def test_un_censo_se_construye_sin_intervalo() -> None:
    """**El control positivo**, y es el caso de L5: los 338 con tabla son un censo."""
    m = _metricas()
    assert m.ci is None
    assert m.regimen == "CENSO"
    assert m.n_documents == 338


def test_una_muestra_se_construye_con_el_suyo() -> None:
    """El otro control positivo. Sin los dos, un tipo que levantara siempre pasaría."""
    m = _metricas(regimen="MUESTRA", ci=(0.81, 0.93))
    assert m.ci == (0.81, 0.93)


def test_una_muestra_sin_intervalo_no_se_construye() -> None:
    """Regla de oro 2: una estimación sin intervalo no se publica."""
    with pytest.raises(ValueError, match="MUESTRA"):
        _metricas(regimen="MUESTRA")


def test_un_censo_con_intervalo_tampoco() -> None:
    """**La dirección que no es obvia, y la que hace que `regimen` signifique algo.**

    Un lector que ve un intervalo asume incertidumbre muestral. Publicar un `(x, x)`
    degenerado sobre un censo no es un adorno: **miente sobre la naturaleza del número**.
    """
    with pytest.raises(ValueError, match="CENSO"):
        _metricas(ci=(0.87, 0.87))


def test_un_intervalo_del_reves_no_se_construye() -> None:
    with pytest.raises(ValueError, match="del revés"):
        _metricas(regimen="MUESTRA", ci=(0.93, 0.81))


def test_una_nota_sobre_cero_documentos_no_es_una_nota() -> None:
    """Si no se pudo medir, `teds` es `None` —NO_APLICABLE—, no un número sin población."""
    with pytest.raises(ValueError, match="0 documentos"):
        _metricas(n_documents=0)


def test_no_aplicable_sobre_cero_documentos_si_es_legitimo() -> None:
    """El complemento del anterior: un extractor al que no le tocó nada evaluable es
    `NO_APLICABLE` con población cero, y eso **sí** se construye."""
    m = _metricas(teds=None, teds_s=None, cell_f1=None, n_documents=0, evaluable_coverage=0.0)
    assert m.teds is None


def test_una_poblacion_negativa_no_se_construye() -> None:
    with pytest.raises(ValueError, match="negativas"):
        _metricas(n_documents=-1)


@pytest.mark.parametrize("agregado", ["POR_DOCUMENTO", "PONDERADO_POR_PAGINA", "POR_TABLA"])
def test_los_tres_agregados_de_ponderacion_yaml_son_construibles(agregado: str) -> None:
    """Los tres son legítimos y dan números distintos: los 38 largos pesan el 3,8% por
    documento y el 36,6% por página. Lo que el tipo impide es **no decir cuál**."""
    assert _metricas(agregado=agregado).agregado == agregado


def test_los_dos_vocabularios_no_se_confunden() -> None:
    """`Regimen` y `Agregado` contestan preguntas distintas —*sobre qué* y *cómo se
    promedió*—, y son dos `Literal` separados para que no se puedan cruzar."""
    from typing import get_args

    assert set(get_args(Regimen)) == {"CENSO", "MUESTRA"}
    assert set(get_args(Agregado)) == {"POR_DOCUMENTO", "PONDERADO_POR_PAGINA", "POR_TABLA"}
    assert not set(get_args(Regimen)) & set(get_args(Agregado))
