"""Las barreras que vigilan los DOCUMENTOS, no el código.

Salen aparte de `test_barreras.py` porque aquél llegó a 328 líneas y la regla del
repo no admite ficheros por encima de 300 sin razón escrita. La partición no es
arbitraria: allí se comprueba que **el código** existe y que las referencias apuntan
a algo; aquí, que **los números y el estado publicados** salen de su fuente.

Las dos son de la misma familia —código cuyo único trabajo es ponerse rojo— y las dos
nacieron del mismo hallazgo: la auditoría en frío del cierre de L4.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _corre(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "python", script],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )


def test_las_derivadas_publicadas_salen_de_su_fuente() -> None:
    """**La quinta barrera, y cubre las cuatro clases que el guardián de recuentos no.**

    `test_recuentos.py` sincroniza **recuentos**. Los documentos publican además
    porcentajes, deltas, sumas de enumeraciones y sellos, y **ninguna de esas cuatro
    clases la vigilaba nadie**: la auditoría en frío de `a0d85ed` encontró doce
    números rotos, once de ellas.

    Un guardián que cubre una clase de cinco y no dice cuál cubre es el límite 77
    aplicado a sí mismo: se lee igual que uno que las cubre todas.
    """
    hecho = subprocess.run(
        ["uv", "run", "python", "scripts/derivadas.py", "--detalle"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )

    assert hecho.returncode == 0, hecho.stdout + hecho.stderr


def test_el_estado_del_readme_sale_de_estado_md() -> None:
    """**El README se quedó 33 commits rancio, y el arreglo no es actualizarlo.**

    Con cuatro hitos más cerrados seguía diciendo «Hito L0 de 10 de la v0.1.0.
    Todavía no hay número» y publicando la puerta sobre un commit de L0. Y el propio
    README contiene la frase *«en un repo que vende rigor, escribir en presente lo
    que no existe es el peor fallo posible, más grave que un bug»*.

    Un fichero que hay que **acordarse** de tocar se queda rancio otra vez, y ya
    sabemos cuántos commits tarda. Así que se **deriva** de `ESTADO.md` y esto lo
    hace cumplir: si `ESTADO.md` avanza y el README no, la puerta se pone roja.
    """
    hecho = subprocess.run(
        ["uv", "run", "python", "scripts/estado_readme.py"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )

    assert hecho.returncode == 0, hecho.stdout + hecho.stderr
