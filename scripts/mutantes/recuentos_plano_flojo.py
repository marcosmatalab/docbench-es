"""`_plano` deja de colapsar los saltos de línea.

Una frase repartida en dos líneas deja de casar con un patrón de una línea, y así
se escapó `LIMITS.md` 51 la primera vez que se construyó esto: su «Los **18
mutantes** apuntan a…» está partido por el ancho de columna.
"""

import re


def pytest_collection_modifyitems(session: object, config: object, items: object) -> None:
    import test_recuentos

    test_recuentos._plano = lambda t: re.sub(r"[ \t]+", " ", t.replace("*", "").replace("`", ""))
