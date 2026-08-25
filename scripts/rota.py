"""`Rota`: una derivada publicada que no sale de su fuente.

Vive en su propio fichero —y son doce líneas— porque la usan `derivadas.py` y
`reglas_de_censo.py`, y si viviera en cualquiera de los dos el otro tendría que
importarlo, cerrando un círculo. Un tipo compartido por dos módulos no pertenece a
ninguno de ellos.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rota:
    """Una derivada que no sale de su fuente. **Con la cuenta, no sólo el veredicto.**"""

    documento: str
    linea: int
    que: str
    publicado: str
    calculado: str
