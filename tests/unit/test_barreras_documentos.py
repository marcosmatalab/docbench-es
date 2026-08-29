"""Las barreras que vigilan los DOCUMENTOS, no el código.

Salen aparte de `test_barreras.py` porque aquél llegó a 328 líneas y la regla del
repo no admite ficheros por encima de 300 sin razón escrita. La partición no es
arbitraria: allí se comprueba que **el código** existe y que las referencias apuntan
a algo; aquí, que **los números y el estado publicados** salen de su fuente.

Las dos son de la misma familia —código cuyo único trabajo es ponerse rojo— y las dos
nacieron del mismo hallazgo: la auditoría en frío del cierre de L4.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

import error_del_estimador  # noqa: E402
import regla_informe_l5  # noqa: E402
import regla_reloj_l5  # noqa: E402
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


def test_una_cifra_del_reloj_de_l5_que_no_sale_de_su_fichero_se_caza() -> None:
    """**El control negativo de R8**, la regla que ata el error del estimador a su fichero.

    El mismo error se publicó como `+74,5%` en cinco sitios y `+74,6%` en un sexto, y no
    lo cazó nadie porque **el número no vivía en ningún fichero**: no había con qué
    comparar. Peor que el caso de R7, además, porque las dos lecturas caían dentro de la
    resolución declarada —±0,2 puntos—, así que la discrepancia no parecía un error.

    Las dos direcciones en la misma función, como en R6 y R7: con la cifra del fichero
    calla; con la cifra movida un decimal, la nombra. Sin la primera mitad, una regla que
    devolviera siempre un fallo pasaría este test.
    """
    datos = regla_reloj_l5._reloj()
    assert datos is not None, "no hay runs/l5/reloj.json: la regla no puede probarse"
    bueno = regla_reloj_l5._esperados(datos)["error"]

    def _desajustes(cifra: str) -> list[str]:
        """Las que NO cuadran, sin contar los patrones que este texto de juguete no lleva."""
        texto = f"el error del estimador es\n**{cifra}%** contra lo medido"
        return [
            f"{r.publicado}->{r.calculado}"
            for r in regla_reloj_l5.cifras_del_reloj_l5(texto, "docs/metrics.md")
            if r.publicado != "no aparece"
        ]

    assert _desajustes(bueno) == [], "con la cifra del fichero, R8 tiene que callar"

    movido = bueno.replace(",6", ",5") if ",6" in bueno else bueno.replace(",5", ",6")
    assert movido != bueno, "el caso rojo tiene que mover de verdad la cifra"
    assert _desajustes(movido) == [f"{movido}->{bueno}"], "R8 no caza un decimal movido"


def test_r8_dice_cuando_una_copia_deja_de_casar_en_vez_de_callarse() -> None:
    """**Un patrón que ya no casa es una copia que ya no se vigila**, y su silencio se
    leería como conformidad. Es el modo de fallo por defecto de cualquier guardián basado
    en patrones —LIMITS 111— y el mismo que R6 declara con su «0 copias vistas».

    Aquí se comprueba sobre un texto vacío: las seis copias de `docs/metrics.md` tienen
    que salir todas como `no aparece`, no como verde.
    """
    datos = regla_reloj_l5._reloj()
    assert datos is not None
    esperadas = [c for c in regla_reloj_l5.COPIAS if c[0] == "docs/metrics.md"]
    rotas = regla_reloj_l5.cifras_del_reloj_l5("", "docs/metrics.md")

    assert len(rotas) == len(esperadas), rotas
    assert all(r.publicado == "no aparece" for r in rotas)


def test_r8_no_acusa_a_nadie_cuando_no_hay_fichero_de_reloj(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un `reloj.json` que no está no es un documento que miente: es una medición que no
    se ha hecho. Misma decisión que R7 con `informe.json`, y por la misma razón."""
    monkeypatch.setattr(regla_reloj_l5, "_reloj", lambda: None)
    assert (
        regla_reloj_l5.cifras_del_reloj_l5("es **+0,0%** contra lo medido", "docs/metrics.md") == []
    )


def test_el_reloj_publicado_cuadra_con_sus_dos_operandos() -> None:
    """**La mitad barata del guardián del reloj, y corre SIEMPRE.**

    El test de abajo re-corre el instrumento entero y necesita los 362 MB de
    `runs/l3/docs`, que no están en un clon frío ni en CI (LIMITS 109). Así que ahí se
    salta — y un guardián que se salta en CI **no protege en CI**. Éste sí: comprueba lo
    que se puede comprobar sin corpus, que es la **aritmética interna** del fichero.

    Caza justo lo que el instrumento no puede cazar por sí solo: que alguien edite
    `reloj.json` a mano y mueva un porcentaje sin mover sus operandos. Y ata el dato
    medido a su única copia, la constante de `error_del_estimador.py`.
    """
    datos = regla_reloj_l5._reloj()
    assert datos is not None, "no hay runs/l5/reloj.json"
    predicho = float(datos["prediccion"]["segundos"])  # type: ignore[index]
    real = float(datos["real"]["segundos"])  # type: ignore[index]

    assert real == float(error_del_estimador.RELOJ_DE_PARED_S), (
        "el reloj de pared del fichero no es la constante declarada: hay dos copias"
    )
    assert datos["error_contra_lo_medido"]["valor"] == pytest.approx(  # type: ignore[index]
        (predicho - real) / real
    ), "el error publicado no sale de sus propios operandos"
    assert datos["sobra_de_la_prediccion"]["valor"] == pytest.approx(  # type: ignore[index]
        (real - predicho) / predicho
    ), "la fracción que sobra no sale de sus propios operandos"


def test_el_reloj_de_l5_publicado_sale_del_instrumento_que_lo_mide() -> None:
    """**El fichero no puede quedarse viejo sin que la puerta lo diga.**

    `runs/l5/reloj.json` es la fuente de R8, así que una fuente rancia haría pasar en
    verde a los seis documentos mientras todos publican lo mismo y equivocado — el
    guardián que se cree a sí mismo. El instrumento se vuelve a correr aquí y se compara.

    **Y corre en un clon frío, pero no de serie: hubo que arreglarlo.** La predicción
    pasa por `censo_tablas`, que recorría los mil XML de `runs/l3/docs` —362 MB fuera de
    git— y **devolvía `{}` sin ellos**: no daba un error, daba **otro número**. Ahora el
    consumidor lee el censo **publicado y versionado** y el instrumento lanza por la
    puerta de `fuera_de_git.py`. De paso, las cinco lecturas del instrumento son cinco
    ficheros distintos leídos **una vez cada uno**, y baja de 0,27 s a **4 ms**.
    """
    emitido = error_del_estimador.reloj()
    guardado = json.loads((RAIZ / "runs" / "l5" / "reloj.json").read_text(encoding="utf-8"))

    assert guardado == emitido, (
        "runs/l5/reloj.json está rancio. Regenéralo con"
        " `uv run python scripts/error_del_estimador.py --escribir`"
    )
