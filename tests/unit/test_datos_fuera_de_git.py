"""Los datos que no están en git se leen por UNA puerta, y esa puerta LANZA.

## El fallo que cierra, y va por la cuarta

`censo_tablas.tablas()` recorría `runs/l3/docs` —362 MB que el repo no versiona— y
**devolvía `{}` cuando no estaban**. Sin corpus no fallaba: `poblacion_l5` repartía los
1.000 documentos como si ninguno tuviera tabla y emitía **otra predicción**. El test que
la comprobaba habría pasado **en verde** en un clon frío afirmando un número falso.

> **Un test que degrada en silencio es peor que un test roto.** El roto se ve; éste
> afirma algo distinto de lo que dice afirmar.

Es un patrón, no un caso: el barrido de referencias que medía la máquina de quien lo
escribió, el `mypy` que no veía los huérfanos, el límite 109 con la primera tabla de L5
irreproducible en un clon, y éste.

## Los tres aros, y por qué hacen falta los tres

1. **la puerta lanza** — con la razón de por qué el dato no está en git dentro;
2. **el consumidor no degrada** — `tablas()` en rojo sin corpus, no `{}`;
3. **quién NO pasa por la puerta es un número**, no una impresión, y el criterio de quién
   debe pasar **se deriva** —lo alcanza un test, luego puede degradar en verde— en vez de
   escribirse a mano una excusa por fichero.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

import censo_tablas  # noqa: E402
import fuera_de_git  # noqa: E402
from huerfanos import reparto  # noqa: E402

SIN_PUERTA_DECLARADOS = {
    "scripts/comparar_verdad.py": (
        "SELLADO: su huella está congelada en el re-sello de L4 y tocarlo pone rojo"
        " `test_congelados_l4`. Y no le hace falta: lee el XML con `read_text`, que"
        " **ya lanza** si no está. La puerta añade la razón, no el fallo"
    ),
    "scripts/computo_l5.py": "huérfano: su salida la lee una persona, no un test",
    "scripts/evidencia_pdf.py": "huérfano: idem, y su salida ES la evidencia que se mira",
    "scripts/falsos_positivos_l5.py": "huérfano: idem",
    "scripts/humo_l5.py": "huérfano: idem",
    "scripts/muestra_l5.py": "huérfano: idem",
    "scripts/ubicar_tabla.py": "huérfano: idem",
    "src/docbench_es/cli/conform.py": "la CLI: la ruta la da quien llama, y falla con su código",
    "src/docbench_es/cli/report.py": "la CLI: comprueba el sello y sale con 4 (§11)",
    "src/docbench_es/cli/run.py": "la CLI: idem",
}
"""Fichero -> por qué NO pasa por la puerta. **El hueco, enumerado y con denominador.**

El criterio no es una opinión: **un script al que llega algún test puede degradar en
verde**, y ésos tienen que pasar por la puerta. Un huérfano no puede — nadie lo corre sin
mirar su salida.

**Y lo que el aro comprueba no es que HAYA una razón, sino que la razón siga siendo
cierta.** Se cruza contra `huerfanos.reparto()`: el día que un test alcance a uno de los
seis declarados huérfanos, esto se pone rojo. Una tabla de excusas que nadie vuelve a
cruzar con la realidad envejece igual que el número que vino a vigilar.

`comparar_verdad.py` es la excepción que enseña dónde está el límite: **sí** lo alcanza un
test y **no** pasa por la puerta, porque su huella está congelada en el re-sello de L4 —
tocarlo pone rojo `test_congelados_l4`—. Y no le hace falta: su lectura lanza sola.
"""


def test_la_puerta_lanza_con_la_razon_dentro(tmp_path: Path) -> None:
    """**El aro 1.** Un `FileNotFoundError` pelado dice «no está»; éste dice además **por
    qué no está y qué hacer**, que es lo que separa un dato ausente de un fichero
    perdido."""
    with pytest.raises(fuera_de_git.FaltaElDato) as caso:
        fuera_de_git.exige(RAIZ / "runs" / "l3" / "docs" / "no-existe.xml")

    assert "runs/l3/docs" in str(caso.value)
    assert "362 MB" in str(caso.value), "la razón declarada tiene que viajar en el mensaje"
    assert "no aquí devolviendo un vacío" in str(caso.value)
    assert fuera_de_git.exige(tmp_path) == tmp_path, "y con el dato delante, lo devuelve"


def test_el_censo_de_tablas_no_degrada_sin_corpus(monkeypatch: pytest.MonkeyPatch) -> None:
    """**El aro 2, y es el control negativo del fallo REAL**, no de uno inventado.

    Con `runs/l3/docs` fuera, `tablas()` devolvía `{}` — un censo vacío que se lee como
    una medida. Ahora lanza. Las dos direcciones: con el corpus movido, rojo; y
    `publicado()`, que lee el artefacto versionado, sigue contestando.
    """
    monkeypatch.setattr(censo_tablas, "DOCS", RAIZ / "no-hay-corpus")
    censo_tablas._contadas.cache_clear()
    try:
        with pytest.raises(fuera_de_git.FaltaElDato):
            censo_tablas.tablas()

        assert len(censo_tablas.publicado()) == 1000, "el censo PUBLICADO no necesita corpus"
    finally:
        censo_tablas._contadas.cache_clear()


def test_todo_script_que_alcanza_un_test_pasa_por_la_puerta() -> None:
    """**El aro 3, con su denominador y con el criterio DERIVADO.**

    Un guardián que enumera excusas a mano envejece: nadie vuelve a mirar la lista. Aquí
    la lista se comprueba contra `huerfanos.reparto()`, que dice qué scripts alcanza algún
    test — o sea **quién puede degradar en verde**—. El día que un test alcance a uno de
    los declarados, esto se pone rojo pidiendo la puerta.
    """
    alcanzables = set(reparto()[0])
    censo = fuera_de_git.censo()
    sin_puerta = censo["sin pasar por la puerta"]

    assert censo["por la puerta"], "nadie pasa por la puerta: el censo no está midiendo nada"
    assert set(sin_puerta) == set(SIN_PUERTA_DECLARADOS), (
        "la lista de los que no pasan por la puerta se ha movido y no está declarada:"
        f" {sorted(set(sin_puerta) ^ set(SIN_PUERTA_DECLARADOS))}"
    )
    mintiendo = [
        f
        for f in sin_puerta
        if f.startswith("scripts/")
        and Path(f).stem in alcanzables
        and SIN_PUERTA_DECLARADOS[f].startswith("huérfano")
    ]
    assert not mintiendo, (
        f"{mintiendo} están declarados como huérfanos y **los alcanza un test**, así que"
        " pueden degradar en VERDE. Métele `exige()` a su lectura, o cambia la razón por"
        " la de verdad — que es lo que este aro comprueba: no que haya una razón, sino"
        " que la razón siga siendo cierta"
    )


def test_el_censo_ve_a_quien_no_pasa_por_la_puerta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**El control negativo del aro 3.** Un censo que clasificara todo como «por la
    puerta» pasaría los tres tests de arriba y no protegería nada. Se le planta un lector
    que nombra una raíz y no importa la puerta, y tiene que verlo."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "scripts" / "malo.py").write_text('D = RAIZ / "runs" / "l3" / "docs"\n', "utf-8")
    (tmp_path / "scripts" / "bueno.py").write_text(
        'from fuera_de_git import exige\nD = exige(RAIZ / "runs" / "l3" / "docs")\n', "utf-8"
    )
    monkeypatch.setattr(fuera_de_git, "RAIZ", tmp_path)

    censo = fuera_de_git.censo()

    assert censo["sin pasar por la puerta"] == ["scripts/malo.py"]
    assert censo["por la puerta"] == ["scripts/bueno.py"]


@pytest.mark.skipif(
    not (RAIZ / "runs" / "l3" / "docs").is_dir(),
    reason="sin los 362 MB de runs/l3/docs no se puede re-medir el censo (LIMITS 109)",
)
def test_el_censo_publicado_no_esta_rancio() -> None:
    """**Y AQUÍ SÍ vale saltarse el test sin corpus**, que es el punto de todo esto.

    El consumidor no se salta: lee el artefacto versionado y corre siempre. Lo que se
    salta es la comprobación de que ese artefacto **sigue siendo lo que miden los XML**,
    que es lo único que de verdad necesita el corpus. Un salto arriba, en la
    comprobación; ninguno abajo, en el consumidor.
    """
    censo_tablas._contadas.cache_clear()

    assert censo_tablas.tablas() == censo_tablas.publicado(), (
        "runs/l5/censo_tablas.json no coincide con los XML."
        " Regenéralo: uv run python scripts/censo_tablas.py"
    )
