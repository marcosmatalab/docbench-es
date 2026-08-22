"""Congelar de verdad los mapas de un `dataclass(frozen=True)`.

`frozen=True` solo impide **reasignar** un atributo. No dice nada de lo que hay
dentro: un `dict` de campo sigue siendo mutable, así que un `CampaignResult`
"congelado" se podía reescribir entero sin tocar un solo atributo::

    m.failures["timeout"] = 999      # frozen=True no se entera

Eso vacía la afirmación sobre la que se apoyan `substance_hash` y `plan_hash`:
que un resultado no se puede mutar DESPUÉS de medirlo. Y casi todo lo publicable
de §6.8 vive en `dict` —`level1`, `costs`, `failures`, `by_verifier`,
`per_document`, `summary`—, o sea justo los números.

La solución es envolver en `MappingProxyType` al construir. Por eso los campos se
anotan `Mapping[...]` y no `dict[...]`: el tipo dice la verdad sobre lo que se
puede hacer con ellos, y mypy rechaza en tiempo de análisis el `m.failures[k] = v`
que antes solo fallaba en runtime.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType


def congelar_mapas(obj: object) -> None:
    """Sustituye todo campo `dict` de `obj` por una vista de solo lectura.

    Se llama desde el `__post_init__` de cada dataclass que tenga mapas. Usa
    `object.__setattr__` porque la propia dataclass está congelada.

    Copia el `dict` antes de envolverlo a propósito: `MappingProxyType` es una
    **vista**, no una copia, así que sin el `dict(v)` quien conservara una
    referencia al diccionario original seguiría pudiendo mutar el resultado por
    la espalda.
    """
    for campo in dataclasses.fields(obj):  # type: ignore[arg-type]
        valor = getattr(obj, campo.name)
        if isinstance(valor, dict):
            object.__setattr__(obj, campo.name, MappingProxyType(dict(valor)))
