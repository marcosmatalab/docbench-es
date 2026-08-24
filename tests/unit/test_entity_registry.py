"""§7.1 · Que un adaptador de entidad **de fuera** tiene por dónde entrar.

Lo que estos tests demuestran no es que el registro funcione: es que **la promesa
de extensibilidad tiene camino**. L13 —segunda entidad real, requisito y no
opcional— es *«la única prueba de ADR-0001»* según §16, y esa prueba consiste en
registrar un adaptador que el motor no conoce. Si el camino de registro no se
prueba hoy, en L13 se descubre que no existe **con el `Protocol` ya publicado**.

## Por qué una distribución falsa y no un `monkeypatch`

El adaptador falso se registra **escribiendo una distribución de verdad** —un
directorio `*.dist-info` con su `entry_points.txt`— en un directorio temporal que
se mete en `sys.path`. Es el camino real de `importlib.metadata`.

Parchear `entry_points` sería más corto y **probaría el parche**: dejaría sin
comprobar justo lo que puede estar mal —el nombre del grupo, el formato del entry
point, y que la mecánica de `benchcore.registry` sirve para un eje que no es
suyo—. Y ese último punto es el riesgo declarado de ADR-0036: si `benchcore`
metiera un `isinstance(..., Plugin)` dentro de `discover()`, los adaptadores de
entidad dejarían de cargar. Con esta forma, ese día el rojo sale aquí, en la
puerta, y no en L13.

Sin red, sin disco del proyecto y sin instalar nada: `tmp_path` y `sys.path`.
"""

from __future__ import annotations

from typing import get_args, get_type_hints

import pytest
from _adaptadores_falsos import AdaptadorCarpeta
from _adaptadores_rotos import ConstruirTocaElMundo, SinVersion, VersionEnInit, VersionIncompatible
from benchcore.contracts import AXES, Plugin
from benchcore.errors import BenchcoreError
from benchcore.types import Capabilities
from conftest import Registrar

from docbench_es.entity.base import EntityAdapter
from docbench_es.entity.boe import BoeAdapter
from docbench_es.entity.registry import cargar, descubrir
from docbench_es.errors import ContractViolation, DocbenchError


def test_un_adaptador_de_fuera_entra_por_su_entry_point(registrar: Registrar) -> None:
    """Demuestra que L13 tiene por dónde entrar, y que el grupo es el que se publica.

    El adaptador no vive en `docbench_es`: vive en un paquete de fuera, que es el
    caso que importa. Un descubrimiento por convención —escanear
    `docbench_es/entity/*.py`— pasaría todos los tests de los adaptadores propios
    y fallaría exactamente aquí.
    """
    registrar("carpeta-de-fuera", "_adaptadores_falsos:AdaptadorCarpeta")

    encontrados = {reg.name: reg.plugin for reg in descubrir()}

    # `boe` también está: es del repo y entra por el mismo grupo, que es
    # justamente lo que este fichero demuestra un test más abajo.
    assert encontrados["carpeta-de-fuera"] is AdaptadorCarpeta
    assert cargar("carpeta-de-fuera") is AdaptadorCarpeta
    # Y lo que se registró cumple los siete métodos de §7.1 al construirlo.
    assert isinstance(AdaptadorCarpeta(), EntityAdapter)


def test_el_descubrimiento_no_construye_el_adaptador(registrar: Registrar) -> None:
    """Demuestra que *«descubrir no construye»* es código y no una intención.

    `ConstruirTocaElMundo.__init__` lanza. Si el registro instanciara lo que
    carga, este test se caería con esa `AssertionError` — que es justo lo que le
    pasaría a `docbench entity list` con un adaptador real, cuyo `__init__` pide
    un perfil y abre ficheros.
    """
    registrar("toca-el-mundo", "_adaptadores_rotos:ConstruirTocaElMundo")

    registrados = {reg.name: reg.plugin for reg in descubrir()}

    assert registrados["toca-el-mundo"] is ConstruirTocaElMundo
    with pytest.raises(AssertionError):
        ConstruirTocaElMundo()


@pytest.mark.parametrize(
    ("nombre", "clase", "trozo"),
    [
        ("sin-version", SinVersion, "no declara"),
        ("mayor-incompatible", VersionIncompatible, "2.x"),
        ("en-init", VersionEnInit, "no declara"),
    ],
    ids=["sin-version", "mayor-incompatible", "declarada-en-init"],
)
def test_el_rechazo_por_version_ocurre_al_cargar(
    registrar: Registrar, nombre: str, clase: type, trozo: str
) -> None:
    """Demuestra que un adaptador incompatible para la campaña antes de gastar nada.

    Los tres casos fallan **cerrado**, y el tercero es el que ADR-0036 nombra:
    declarar `benchcore_api` en `__init__` no retrasa el rechazo, **impide la
    carga**, porque en carga no hay instancia que mirar. El mensaje habla
    entonces de una versión ausente y no de la que el adaptador creía declarar.
    """
    registrar(nombre, f"_adaptadores_rotos:{clase.__name__}")

    with pytest.raises(ContractViolation) as capturado:
        list(descubrir())

    assert trozo in str(capturado.value)


def test_lo_que_lanza_el_registro_lo_cazan_los_dos_except(registrar: Registrar) -> None:
    """Demuestra que el error no se escapa del `except` del motor ni de su código.

    `benchcore.errors.IncompatibleApi` **no** hereda de `DocbenchError`: si el
    registro la dejara pasar tal cual, un `except DocbenchError` no la vería y la
    CLI saldría con traza en vez de con su código de salida. Por eso se traduce.
    Y sigue siendo un `BenchcoreError`, que es lo que caza el motor cuando lo que
    revienta es el plugin de un cliente.
    """
    registrar("mayor-incompatible", "_adaptadores_rotos:VersionIncompatible")

    with pytest.raises(DocbenchError) as capturado:
        list(descubrir())

    assert isinstance(capturado.value, BenchcoreError)
    assert capturado.value.exit_code == 5


def test_el_adaptador_del_boe_entra_por_el_mismo_camino_que_uno_de_fuera() -> None:
    """Demuestra que el camino propio y el ajeno son **el mismo camino**.

    `boe` se registra por su entry point en `pyproject.toml`, igual que se
    registraría el adaptador de un cliente. Si hubiera un atajo privilegiado para
    los propios, la suite sólo probaría el que nadie de fuera usa — y L13
    descubriría en su primer día que el camino ajeno no funciona.

    Este test decía antes que el grupo estaba vacío, y era cierto **hasta que
    `entity/boe.py` existió**. Que se cayera al registrarlo es el comportamiento
    correcto: la afirmación de ayer dejó de ser verdad y algo tenía que decirlo.
    """
    registrados = {reg.name: reg.plugin for reg in descubrir()}

    assert registrados == {"boe": BoeAdapter}
    assert cargar("boe") is BoeAdapter


def test_un_grupo_sin_adaptadores_no_es_un_error() -> None:
    """Demuestra que cero registrados es una respuesta, no un fallo.

    Si el descubrimiento tratara el vacío como error, un proyecto recién clonado
    —o un grupo que todavía no tiene a nadie, como `docbench.extractor` hasta L5—
    tendría la puerta roja sin que nada esté mal.
    """
    assert list(descubrir("docbench.grupo-que-no-existe")) == []


def test_el_eje_de_entidad_sigue_sin_existir_en_benchcore() -> None:
    """Fija la PREMISA de ADR-0035, no su conclusión.

    ADR-0035 decide que `EntityAdapter` viva aquí por una razón de diseño —el eje
    tendría exactamente un consumidor— y no porque `benchcore` no lo admita. Pero
    el hecho de que hoy no lo admita **también se afirma**, y una afirmación sobre
    otro repo se queda vieja sin avisar.

    Si `benchcore` añade el eje algún día, esto se pone rojo y el ADR se revisa
    **con el hecho delante**, en vez de seguir escrito con un argumento que ya no
    describe la realidad. Que se ponga rojo no significa que la decisión cambie:
    significa que hay que volver a mirarla.
    """
    ejes = get_args(get_type_hints(Capabilities)["axis"])

    assert ejes == ("datos", "computo", "ejecucion", "salida")
    assert "entidad" not in AXES
    # Y los siete métodos de §7.1 no son los de un `Plugin`: sin `capabilities()`
    # ni `probe()`, un adaptador de entidad no lo es ni por casualidad.
    assert not isinstance(AdaptadorCarpeta(), Plugin)
