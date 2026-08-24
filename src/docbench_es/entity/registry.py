"""§7.1 y §13.1 · Quién descubre un adaptador de entidad. **Decidido en ADR-0036.**

`EntityAdapter` no es un eje de `benchcore` (ADR-0035), así que el descubrimiento
es problema de este repo. Y no es un problema aplazable: **L13 —segunda entidad
real, requisito y no opcional— es la única prueba de ADR-0001**, y esa prueba
consiste en registrar un adaptador que el motor no conoce. Sin vía de registro, el
`Protocol` que L3 publica no tiene por dónde entrar.

## El grupo es propio; la mecánica es prestada

```toml
# pyproject.toml de quien trae su entidad
[project.entry-points."docbench.entity"]
mi-organismo = "mi_paquete.bench:MiAdaptador"
```

`benchcore.registry.discover` **no comprueba el eje, ni exige `Plugin`, ni llama a
`capabilities()`**: recorre un grupo de entry points, carga, y exige
`benchcore_api` con mayor compatible. O sea que el eje no se comparte pero **el
apretón de manos de versión sí**, y se reusa tal cual. Copiarlo aquí serían dos
implementaciones del mismo saludo divergiendo, y dos convenciones que aprender
para dos grupos del mismo proyecto.

**El camino propio y el ajeno son el mismo camino.** `boe` entra por donde entra
el adaptador de un cliente. Si hubiera un atajo privilegiado, la suite de
conformidad sólo probaría el que nadie de fuera usa.

## Las dos reglas que este módulo hace cumplir

**Falla CERRADO.** Un entry point que no se puede importar, o que no declara
`benchcore_api`, o que declara un mayor incompatible, **aborta el descubrimiento
con su causa**. Tragárselo produciría una campaña con menos concursantes de los
que el informe afirma — la regla de oro 6 rota por omisión.

**Descubrir no construye.** Se devuelve **lo que carga el entry point** —la clase,
no una instancia—. Es la misma regla que *«`discover` no descarga»*: listar
entidades no puede abrir ficheros ni tocar la red, y una instancia necesitaría su
`PerfilEntidad`, que es de quien monta la campaña y no del catálogo.

De ahí sale una consecuencia dura que la conformidad comprueba: **`benchcore_api`
tiene que ser atributo de clase.** Un adaptador que lo asigne en `__init__` no es
que se rechace tarde — es que **no se le rechaza nunca**, porque en carga no hay
instancia que mirar.

## Lo que NO está aquí

La puerta de política. §14 y §19 dicen que *«el registro rechaza»* un adaptador con
`special_categories: true`, y eso necesita la `PrivacyDecl`, que vive en el perfil
y no en la clase. Va donde el adaptador se construye con su perfil, y su hito es
**L8 · Política**, con su test hostil. Lo que sí queda fijado: esa puerta es de
`docbench`. `benchcore.registry` no sabe qué es una `PrivacyDecl`.

Y la conformidad. Aquí se comprueba la **versión**; que el objeto cumpla los siete
métodos lo comprueba `entity.conformance`, igual que en `benchcore` el registro y
`conform` son dos cosas.

Nota de vocabulario: lo que se devuelve es el `Registration` de `benchcore`, con
sus campos `group`, `name` y `plugin`. **No se envuelve en un tipo propio con los
nombres de aquí**: sería una traducción que mantener a cambio de estética, y quien
traiga un adaptador ya lee esos nombres en el registro de extractores.
"""

from __future__ import annotations

from collections.abc import Iterator

from benchcore.errors import ContractViolation as _BenchcoreContractViolation
from benchcore.registry import Registration, discover, load

from docbench_es.errors import ContractViolation

__all__ = ["GRUPO", "Registration", "cargar", "descubrir"]

GRUPO = "docbench.entity"
"""El grupo de entry points de los adaptadores de entidad.

Separado de `docbench.extractor` a propósito: son dos contratos distintos y un
adaptador de entidad registrado como extractor tiene que fallar, no colarse.
"""


def _traducir(exc: _BenchcoreContractViolation) -> ContractViolation:
    """Relanza como error de este proyecto. **No amplía la jerarquía de §11.**

    `IncompatibleApi` hereda de la `ContractViolation` de `benchcore`, no de
    `DocbenchError`. Si escapara tal cual, **un `except DocbenchError` del motor no
    la vería** y la CLI saldría con traza en vez de con su código de salida. Y no
    se añade un séptimo código: §11 tiene seis, y una incompatibilidad de versión
    **es** una violación de contrato — la 5.
    """
    return ContractViolation(str(exc))


def descubrir(grupo: str = GRUPO) -> Iterator[Registration]:
    """Los adaptadores de entidad registrados, en orden por nombre.

    Perezoso, como el de `benchcore`: el error de un adaptador roto sale **mientras
    se itera**, no al llamar. Quien recorra esto tiene que dejar que suba.
    """
    try:
        yield from discover(grupo)
    except _BenchcoreContractViolation as exc:
        raise _traducir(exc) from exc


def cargar(nombre: str, grupo: str = GRUPO) -> object:
    """Carga un adaptador por nombre. **Devuelve la clase, no una instancia.**

    Lanza si no existe: pedir una entidad que no está registrada es un error del
    plan, no un motivo para correr una campaña sobre otro corpus.
    """
    try:
        return load(grupo, nombre)
    except _BenchcoreContractViolation as exc:
        raise _traducir(exc) from exc
