"""**MUTANTE.** El delta entre los dos denominadores es 0,0000 para todos.

El `siempre_ok` de la columna que se añadió al descubrir que la dirección del sesgo de
supervivencia no era predecible (LIMITS 108). Un delta constante de cero dice «pasar al
denominador común no le cuesta nada a nadie», que es la conclusión más tranquilizadora
posible y la que haría innecesaria la cara a cara entera.

También se traga la otra mitad: `delta()` devuelve `None` cuando falta uno de los dos
lados, y un 0,0 en su lugar publicaría «no le cuesta nada» donde lo que pasa es que no se
midió — el `NO_APLICABLE` contra el 0,00 otra vez, un nivel más abajo.

Sólo lo mata un test que exija un delta **con signo** distinto de cero, o que compruebe
que sin los dos lados no hay resta.
"""

from __future__ import annotations

from docbench_es.report import cara_a_cara as modulo


def _sin_coste(self: modulo.CaraACara, extractor: str) -> float | None:
    return 0.0


modulo.CaraACara.delta = _sin_coste  # type: ignore[method-assign]
