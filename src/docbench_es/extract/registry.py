"""§7.2 y §13.1 · Quién descubre un extractor. **El mismo mecanismo que el ajeno.**

`base.py` decía *«no descubre nada: el registro llega con el primer extractor real, en su
fichero»*. Éste es ese fichero, y llega con `pdfplumber`.

Es el gemelo de `entity/registry.py` y comparte con él lo que importa: **la mecánica es
prestada de `benchcore.registry`** —recorre un grupo de entry points, carga, y exige
`benchcore_api` con mayor compatible— y **el grupo es propio**. Copiar el apretón de manos
de versión serían dos implementaciones del mismo saludo divergiendo.

## Las dos reglas que hace cumplir, y aquí muerden más que en `entity`

**Falla CERRADO.** Un entry point que no se puede importar aborta el descubrimiento con su
causa. Tragárselo produciría una campaña con **menos concursantes de los que el informe
afirma**, que es la regla de oro 6 rota por omisión — y en un banco comparativo, un
concursante que desaparece en silencio cambia todas las medias.

**Descubrir no construye.** Se devuelve la CLASE. `docling` y `marker` cargan modelos de
torch al construirse; listar los extractores disponibles no puede costar eso. De ahí la
consecuencia que `cumple_la_forma` comprueba: **las seis declaraciones son atributos de
clase**, porque en carga no hay instancia que mirar.

## Por qué esto obliga a que los extractores importen su biblioteca DENTRO

Consecuencia directa de fallar cerrado: `extract-local` no está instalado en la puerta, así
que un `import pdfplumber` en el cuerpo de un módulo registrado **tumbaría el grupo entero
en CI** — no sólo su propia línea. Está escrito en cada extractor, y se comprueba en
`tests/unit/test_extract_registry.py` **sin la biblioteca delante**.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from benchcore.errors import ContractViolation as _BenchcoreContractViolation
from benchcore.registry import Registration, discover, load

from docbench_es.errors import ContractViolation

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Iterator

__all__ = ["GRUPO", "Registration", "cargar", "descubrir", "nombres"]

GRUPO = "docbench.extractor"
"""El grupo de entry points de los extractores.

Separado de `docbench.entity` a propósito: son dos contratos distintos, y un adaptador de
entidad registrado como extractor tiene que fallar, no colarse.
"""


def _traducir(exc: _BenchcoreContractViolation) -> ContractViolation:
    """Relanza como error de este proyecto. **No amplía la jerarquía de §11.**

    `IncompatibleApi` hereda de la `ContractViolation` de `benchcore`, no de
    `DocbenchError`: si escapara tal cual, un `except DocbenchError` del motor no la vería
    y la CLI saldría con traza en vez de con su código de salida.
    """
    return ContractViolation(str(exc))


def descubrir(grupo: str = GRUPO) -> Iterator[Registration]:
    """Los extractores registrados, en orden por nombre. Perezoso, como el de `benchcore`:
    el error de uno roto sale **mientras se itera**, no al llamar."""
    try:
        yield from discover(grupo)
    except _BenchcoreContractViolation as exc:
        raise _traducir(exc) from exc


def cargar(nombre: str, grupo: str = GRUPO) -> object:
    """Carga un extractor por nombre. **Devuelve la clase, no una instancia.**

    Lanza si no existe: pedir un extractor que no está registrado es un error del plan, no
    un motivo para correr una campaña con un concursante menos.
    """
    try:
        return load(grupo, nombre)
    except _BenchcoreContractViolation as exc:
        raise _traducir(exc) from exc


def nombres(grupo: str = GRUPO) -> list[str]:
    """Los nombres registrados. **El denominador de todo lo que diga la CLI.**"""
    return [r.name for r in descubrir(grupo)]
