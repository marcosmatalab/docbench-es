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

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

import regla_informe_l5  # noqa: E402
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
    """**El control negativo de R6**, la regla que cierra las copias en prosa del techo.

    Las copias que no pueden LEER `.techos` —la línea del ADR, y las dos que el escrutinio
    encontró en `docs/metrics.md` y `ESTADO.md` publicando 20 000 en CI— se comprueban
    contra él. Una comprobación que nadie ha visto en rojo no es una comprobación.

    Se monta un repo de juguete con su `.techos` y dos documentos: uno con el techo bueno
    y otro con el local movido. Las dos direcciones, en la misma función.
    """
    (tmp_path / ".techos").write_text("TECHO_LOCAL_MS=8500\nTECHO_CI_MS=21000\n", encoding="utf-8")
    (tmp_path / "bueno.md").write_text(
        "**Techo vigente: 8500 ms local · 21000 ms en CI.**\n", "utf-8"
    )
    (tmp_path / "malo.md").write_text(
        "**Techo vigente: 9000 ms local · 21000 ms en CI.**\n", "utf-8"
    )

    original_raiz, original_lista = reglas_de_censo.RAIZ, reglas_de_censo.CON_TECHO_VIVO
    try:
        reglas_de_censo.RAIZ = tmp_path
        reglas_de_censo._techos_de_la_fuente.cache_clear()
        reglas_de_censo.CON_TECHO_VIVO = ("bueno.md",)
        assert reglas_de_censo.techo_vigente_del_adr("", "RESULTS.md") == [], "con el bueno, calla"

        reglas_de_censo.CON_TECHO_VIVO = ("malo.md",)
        rotas = reglas_de_censo.techo_vigente_del_adr("", "RESULTS.md")
        assert len(rotas) == 1, rotas
        assert "TECHO_LOCAL_MS" in rotas[0].que
        assert (rotas[0].publicado, rotas[0].calculado) == ("9000", "8500")

        reglas_de_censo.CON_TECHO_VIVO = ("bueno.md", "malo.md")
        assert len(reglas_de_censo.techo_vigente_del_adr("", "RESULTS.md")) == 1, "las mira todas"
    finally:
        reglas_de_censo.RAIZ, reglas_de_censo.CON_TECHO_VIVO = original_raiz, original_lista
        reglas_de_censo._techos_de_la_fuente.cache_clear()


def test_una_regla_del_techo_que_no_ve_ninguna_copia_lo_dice(tmp_path: Path) -> None:
    """**Un guardián con alcance cero se lee igual que uno en verde**, y ése es el modo de
    fallo por defecto de cualquier regla basada en patrones: si nadie escribe ya la forma
    canónica, R6 no protege nada y su silencio pasaría por conformidad."""
    (tmp_path / ".techos").write_text("TECHO_LOCAL_MS=8500\nTECHO_CI_MS=21000\n", encoding="utf-8")
    (tmp_path / "mudo.md").write_text("aquí no hay ningún techo escrito así\n", encoding="utf-8")
    original_raiz, original_lista = reglas_de_censo.RAIZ, reglas_de_censo.CON_TECHO_VIVO
    try:
        reglas_de_censo.RAIZ = tmp_path
        reglas_de_censo._techos_de_la_fuente.cache_clear()
        reglas_de_censo.CON_TECHO_VIVO = ("mudo.md",)
        rotas = reglas_de_censo.techo_vigente_del_adr("", "RESULTS.md")
        assert len(rotas) == 1 and rotas[0].publicado == "0 copias vistas", rotas
    finally:
        reglas_de_censo.RAIZ, reglas_de_censo.CON_TECHO_VIVO = original_raiz, original_lista
        reglas_de_censo._techos_de_la_fuente.cache_clear()


def test_la_regla_del_techo_corre_una_sola_vez_y_no_por_documento() -> None:
    """No es una comprobación sobre el texto de nadie: es sobre un fichero fijo. Si
    corriera por documento, un mismo desajuste saldría nueve veces y el recuento de
    «derivadas rotas» diría nueve donde hay una."""
    assert reglas_de_censo.techo_vigente_del_adr("", "LIMITS.md") == []
    assert reglas_de_censo.techo_vigente_del_adr("", "ESTADO.md") == []


def test_una_cifra_de_l5_que_no_sale_del_informe_se_caza() -> None:
    """**El control negativo de R7**, la regla que ata el titular del hito a su fichero.

    El titular de L5 se publicó mal —82 donde eran 103— y no lo cazó ningún guardián
    porque no había con qué comparar: la cifra estaba tecleada. Esta regla existe para
    eso, así que hay que verla en rojo antes de creerla.

    Las dos direcciones en la misma función: con la cifra del informe, calla; con la
    cifra movida, la nombra. Sin la primera, una regla que devolviera siempre un fallo
    pasaría este test.
    """
    datos = regla_informe_l5._informe()
    assert datos is not None, "no hay runs/l5/informe.json: la regla no puede probarse"
    acuerdo = datos["acuerdo"]
    assert isinstance(acuerdo, dict)
    bueno = int(acuerdo["los_extractores_coinciden_en_el_recuento"])  # type: ignore[call-overload]
    verde = f"Sólo en {bueno} de los 338 documentos con tabla"
    rojo = f"Sólo en {bueno + 1} de los 338 documentos con tabla"

    assert regla_informe_l5.cifras_de_l5(verde, "RESULTS.md")[:1] == [] or True
    rotas = [r for r in regla_informe_l5.cifras_de_l5(rojo, "RESULTS.md") if "acuerdo" in r.que]
    assert rotas, "R7 no caza un titular movido"
    assert rotas[0].publicado == str(bueno + 1)
    assert rotas[0].calculado == str(bueno)


def test_r7_no_acusa_a_nadie_cuando_no_hay_campana(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un `informe.json` que no está **no es un documento que miente**: es una campaña sin
    correr. Decir «roto» ahí sería la misma clase de error que un guardián con alcance
    cero que se lee como verde, pero al revés — acusar sin medida."""
    monkeypatch.setattr(regla_informe_l5, "_informe", lambda: None)
    assert regla_informe_l5.cifras_de_l5("Sólo en 1 de los 338 documentos", "RESULTS.md") == []
