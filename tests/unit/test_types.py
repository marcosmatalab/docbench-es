"""§6 · La forma del modelo de datos: inmutabilidad y superficie de import.

No "que el código hace lo que hace": cada test convierte en contrato una
afirmación que hoy solo está escrita en el manual, y que sin test se cae en tres
meses sin que nadie se entere.

Los invariantes de cada estructura concreta viven en `test_types_invariantes.py`.
Están separados porque juntos pasaban de las 300 líneas que fija `CLAUDE.md`.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from docbench_es import types
from docbench_es.types import ExtractionFailure, StructureMetrics

RAIZ = Path(__file__).resolve().parents[2]
PAQUETE_TYPES = RAIZ / "src" / "docbench_es" / "types"


def _modulos_importados(fichero: Path) -> list[str]:
    """Los módulos que importa un fichero, tal cual se escriben en el `import`.

    Por AST y no por `grep`: este mismo fichero contiene la cadena
    `docbench_es.types._` dentro de un literal, y un `grep` se delataría a sí
    mismo. El AST solo ve los `import` de verdad.
    """
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    nombres: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            nombres.append("." * nodo.level + (nodo.module or ""))
    return nombres


def test_todo_el_modelo_de_datos_es_inmutable() -> None:
    """Demuestra que un resultado no se puede mutar DESPUÉS de medirlo.

    Es la base de que `substance_hash` y `plan_hash` signifiquen algo: si una
    `CampaignResult` admitiera asignación, el hash dejaría de atar el número
    publicado a lo que de verdad se midió.
    """
    encontrados = [n for n in types.__all__ if dataclasses.is_dataclass(getattr(types, n))]
    mutables = [n for n in encontrados if not getattr(types, n).__dataclass_params__.frozen]

    assert mutables == []
    # Exacto, no `>= 25`: con el suelo holgado se podían borrar tres estructuras
    # de `__all__` y el test seguía en verde diciendo que no faltaba ninguna.
    # Comprobado quitando `TedsReport`, `GlossaryContribution` y `RoutingPlan`.
    # 28 = las dataclasses de §6; las otras 4 entradas de `__all__` son alias de
    # tipo (`ExtractionFailure`, `TruthMode`…), que no son dataclass.
    assert len(encontrados) == 28, (
        f"§6 define 28 dataclasses y hay {len(encontrados)}: si es un cambio "
        f"querido, actualiza el número aquí y di por qué en el commit"
    )


def test_los_mapas_de_un_resultado_tampoco_se_pueden_mutar() -> None:
    """Demuestra la otra mitad de la inmutabilidad, la que `frozen` NO da.

    `frozen=True` solo impide reasignar el atributo. El test de arriba, tal como
    estaba, pasaba en verde mientras `m.failures["timeout"] = 999` funcionaba
    perfectamente, y casi todo lo publicable de §6.8 vive en un mapa: `level1`,
    `costs`, `failures`, `by_verifier`, `per_document`, `summary`. O sea que un
    `CampaignResult` "congelado" se podía reescribir entero sin tocar un atributo,
    y `substance_hash` dejaba de atar el número publicado a lo que se midió.
    """
    metricas = StructureMetrics(
        teds=0.91,
        teds_s=0.88,
        cell_f1=0.93,
        evaluable_coverage=0.75,
        failures={"timeout": 1},
        ci=(0.89, 0.93),
        n_documents=120,
    )

    with pytest.raises(TypeError):
        metricas.failures["timeout"] = 999  # type: ignore[index]
    with pytest.raises(TypeError):
        metricas.failures["inventado"] = 42  # type: ignore[index]

    assert dict(metricas.failures) == {"timeout": 1}

    # Y no es una vista del dict original: quien conserve la referencia de
    # construcción tampoco puede mutar el resultado por la espalda.
    original: dict[ExtractionFailure, int] = {"timeout": 1}
    otras = dataclasses.replace(metricas, failures=original)
    original["timeout"] = 999

    assert dict(otras.failures) == {"timeout": 1}


def test_el_agregado_de_fallos_solo_admite_causas_del_enum_cerrado() -> None:
    """Demuestra que el cajón de sastre no entra por el agregado que se publica.

    El enum `ExtractionFailure` es cerrado, pero `failures` estaba tipado
    `dict[str, int]`: `{"lo_que_sea": 3}` pasaba `mypy --strict` sin una queja,
    justo en la estructura cuyo contenido se publica como tasa de fallo por causa.
    Tiparlo con el `Literal` hace que mypy lo cace gratis, en análisis y no en
    runtime.
    """
    anotacion = StructureMetrics.__annotations__["failures"]

    assert "ExtractionFailure" in str(anotacion), (
        f"failures debe ir tipado con el enum cerrado, no con str: {anotacion}"
    )


def test_types_no_importa_nada_del_proyecto() -> None:
    """Demuestra la primera línea de §6: *«types no importa nada del proyecto»*.

    Hoy eso es una frase en un manual. Aquí es una puerta. El contrato de capas
    NO lo cubre: `types` está en la capa de abajo, así que import-linter le
    permitiría importar hacia arriba sin quejarse. Y el día que lo hiciera, el
    modelo de datos dejaría de poder releerse sin arrastrar medio motor detrás.
    """
    intrusos: dict[str, list[str]] = {}
    for fichero in sorted(PAQUETE_TYPES.glob("*.py")):
        ajenos = [
            m
            for m in _modulos_importados(fichero)
            if m.startswith("docbench_es") and not m.startswith("docbench_es.types")
        ]
        if ajenos:
            intrusos[fichero.name] = ajenos

    assert intrusos == {}


def test_nadie_de_fuera_importa_los_submodulos_privados_de_types() -> None:
    """Demuestra que `docbench_es.types` es la ÚNICA superficie de import.

    `types` es un paquete por el límite de 300 líneas (ADR-0013), no porque su
    reparto interno sea público. Si un módulo de fuera importara
    `docbench_es.types._campana`, mover una estructura de un submódulo a otro
    rompería a sus consumidores: la partición dejaría de ser un detalle interno
    y pasaría a ser API. Esto lo hace contrato en vez de convención.
    """
    culpables: dict[str, list[str]] = {}
    for fichero in sorted([*(RAIZ / "src").rglob("*.py"), *(RAIZ / "tests").rglob("*.py")]):
        if PAQUETE_TYPES in fichero.parents:
            continue
        privados = [
            m
            for m in _modulos_importados(fichero)
            if "docbench_es.types._" in m or (m.startswith(".") and "types._" in m)
        ]
        if privados:
            culpables[str(fichero.relative_to(RAIZ))] = privados

    assert culpables == {}
