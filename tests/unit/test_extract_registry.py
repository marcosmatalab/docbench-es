"""El registro de extractores, y la regla que sostiene: **nadie importa su biblioteca.**

El descubrimiento falla CERRADO (ADR-0036): un módulo registrado que reviente al
importarse no tumba su propia línea, tumba **el grupo entero**. Y `extract-local` no se
instala en la puerta —arrastra torch y CUDA—, así que un `import pdfplumber` en el cuerpo
de un extractor dejaría a `docbench conform` sin poder listar nada en CI.

Eso está escrito en cada extractor y en `pyproject.toml`. Aquí se **ejecuta**, y por AST:
la máquina que corre esto **sí** tiene las bibliotecas instaladas, así que «importa y a ver
si peta» no demostraría nada. Lo que se mira es qué importa el módulo a nivel superior.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

from docbench_es.errors import ContractViolation
from docbench_es.extract.base import cumple_la_forma
from docbench_es.extract.registry import GRUPO, cargar, descubrir, nombres

RAIZ = Path(__file__).resolve().parents[2]

PROPIOS = ("docbench_es", "benchcore", "__future__")
"""Lo que un extractor SÍ puede importar arriba: el contrato y el modelo de datos."""


def _importados_arriba(ruta: Path) -> set[str]:
    """Los módulos que se importan al cargar el fichero. **No los de dentro de una
    función**, que son exactamente los que este proyecto exige."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    fuera: set[str] = set()
    for nodo in arbol.body:  # sólo el nivel superior: `for` sobre `body`, no `ast.walk`
        if isinstance(nodo, ast.Import):
            fuera.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            fuera.add(nodo.module.split(".")[0])
    return fuera


def test_el_grupo_trae_los_extractores_declarados_en_pyproject() -> None:
    """El registro descubre, y **dice cuántos**: un guardián sin denominador no vale."""
    registrados = nombres()
    assert "pdfplumber" in registrados, f"grupo {GRUPO}: {registrados}"
    assert len(registrados) == len(set(registrados)), f"nombres repetidos: {registrados}"


def test_ningun_extractor_registrado_importa_su_biblioteca_al_cargarse() -> None:
    """**La regla que hace posible que el grupo se descubra en la puerta.**

    Se recorren los módulos REGISTRADOS, no una lista escrita a mano: el día que entre
    `docling` con un `import torch` arriba, esto se pone rojo sin que nadie lo apunte.
    """
    culpables: dict[str, set[str]] = {}
    for registro in descubrir():
        modulo = sys.modules[
            type(registro.plugin).__module__
            if not isinstance(registro.plugin, type)
            else registro.plugin.__module__
        ]
        ruta = Path(str(modulo.__file__))
        ajenos = {
            m
            for m in _importados_arriba(ruta)
            if m not in PROPIOS and m not in sys.stdlib_module_names
        }
        if ajenos:
            culpables[registro.name] = ajenos
    assert culpables == {}, (
        f"un extractor importa su biblioteca al cargarse: {culpables}. Eso tumba el "
        f"descubrimiento del grupo ENTERO en cualquier entorno sin `extract-local`, "
        f"no sólo su propia línea. El import va dentro de la función; `probe()` es "
        f"quien contesta si la biblioteca está"
    )


def test_el_control_negativo_de_lo_anterior_detecta_un_import_arriba(tmp_path: Path) -> None:
    """Sin esto, `_importados_arriba` podría devolver siempre vacío y todo verde."""
    falso = tmp_path / "malo.py"
    falso.write_text("import pdfplumber\nfrom torch import nn\n", encoding="utf-8")
    assert _importados_arriba(falso) == {"pdfplumber", "torch"}
    dentro = tmp_path / "bueno.py"
    dentro.write_text("def f():\n    import pdfplumber\n    return pdfplumber\n", encoding="utf-8")
    assert _importados_arriba(dentro) == set()


def test_cargar_devuelve_la_clase_y_no_una_instancia() -> None:
    """**Descubrir no construye.** `docling` carga modelos de torch al construirse;
    listar los extractores disponibles no puede costar eso."""
    cargado = cargar("pdfplumber")
    assert isinstance(cargado, type), f"devolvió {type(cargado).__name__}"


def test_toda_declaracion_de_un_registrado_es_atributo_de_clase() -> None:
    """La consecuencia dura de lo anterior: en carga **no hay instancia que mirar**.

    Un extractor que asigne `benchcore_api` en `__init__` no es que se rechace tarde: es
    que no se le rechaza nunca. `cumple_la_forma` mira la clase, y aquí se le pasa lo que
    el registro entrega de verdad.
    """
    for registro in descubrir():
        forma = cumple_la_forma(
            registro.plugin if isinstance(registro.plugin, type) else type(registro.plugin)
        )
        assert forma.cumple, f"{registro.name}: {forma}"


def test_pedir_un_extractor_que_no_existe_lanza_el_error_del_proyecto() -> None:
    """Y **no** el de `benchcore`: si escapara tal cual, un `except DocbenchError` del
    motor no lo vería y la CLI saldría con traza en vez de con su código de salida."""
    with pytest.raises(ContractViolation) as caido:
        cargar("no-existe-este-extractor")
    assert "no-existe-este-extractor" in str(caido.value)
    assert "pdfplumber" in str(caido.value), "el error dice cuáles SÍ hay"


def test_los_dos_grupos_son_distintos() -> None:
    """Un adaptador de entidad registrado como extractor tiene que fallar, no colarse."""
    entidad = importlib.import_module("docbench_es.entity.registry")
    assert GRUPO != entidad.GRUPO
    assert "pdfplumber" not in [r.name for r in entidad.descubrir()]
