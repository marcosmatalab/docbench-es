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
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

import reglas_de_censo  # noqa: E402


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


def test_un_techo_vigente_que_no_cuadra_con_la_fuente_se_caza(tmp_path: Path) -> None:
    """**El control negativo de R6, la regla que cierra la quinta copia del techo.**

    La copia número cinco es prosa —la línea «techo vigente» de ADR-0022— y no puede
    LEER `.techos`, así que se comprueba contra él. Una comprobación que nadie ha visto
    en rojo no es una comprobación: aquí se le da un ADR con el número movido y se exige
    que lo diga, nombrando la clave que no cuadra.

    Y se comprueba **la otra dirección** en la misma función: con el número bueno, la
    regla calla. Sin eso, una regla que devolviera siempre un fallo pasaría este test.
    """
    fuente = reglas_de_censo._techos_de_la_fuente()
    bueno = tmp_path / "bueno.md"
    bueno.write_text(
        f"**Techo vigente: {fuente['TECHO_LOCAL_MS']} ms local · "
        f"{fuente['TECHO_CI_MS']} ms en CI.**\n",
        encoding="utf-8",
    )
    movido = tmp_path / "movido.md"
    movido.write_text(
        f"**Techo vigente: {fuente['TECHO_LOCAL_MS'] + 500} ms local · "
        f"{fuente['TECHO_CI_MS']} ms en CI.**\n",
        encoding="utf-8",
    )
    original = reglas_de_censo.ADR_TECHO
    try:
        reglas_de_censo.ADR_TECHO = bueno
        assert reglas_de_censo.techo_vigente_del_adr("", "RESULTS.md") == []
        reglas_de_censo.ADR_TECHO = movido
        rotas = reglas_de_censo.techo_vigente_del_adr("", "RESULTS.md")
        assert len(rotas) == 1, rotas
        assert "TECHO_LOCAL_MS" in rotas[0].que
        assert rotas[0].publicado == str(fuente["TECHO_LOCAL_MS"] + 500)
        assert rotas[0].calculado == str(fuente["TECHO_LOCAL_MS"])
    finally:
        reglas_de_censo.ADR_TECHO = original


def test_la_regla_del_techo_corre_una_sola_vez_y_no_por_documento() -> None:
    """No es una comprobación sobre el texto de nadie: es sobre un fichero fijo. Si
    corriera por documento, un mismo desajuste saldría nueve veces y el recuento de
    «derivadas rotas» diría nueve donde hay una."""
    assert reglas_de_censo.techo_vigente_del_adr("", "LIMITS.md") == []
    assert reglas_de_censo.techo_vigente_del_adr("", "ESTADO.md") == []
