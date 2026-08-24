"""Que las dos barreras de L3 **se ponen rojas**, que es su único trabajo.

**La regla que obliga a que esto exista hoy y no en L4** (deuda 7 de `ESTADO.md`):

> Un módulo cuyo único trabajo es PONERSE ROJO —una barrera— trae su control
> negativo en el MISMO hito. El resto se cierra a plazos, con su precio.

Código de producción que está mal se delata en lo que produce. Una barrera que
está mal **se delata con silencio**, y el silencio se lee igual que ir bien. Las
dos de aquí lo demuestran:

- **`scripts/referencias.py`.** Su silencio se lee como *«no hay referencias
  rotas»*, y es el paso 8 de `/cerrar`: si dejara de funcionar, cada cierre
  publicaría un cero que nadie ha comprobado.
- **El guardia del árbol de `medir_puerta.py`.** Su silencio se lee como *«el
  árbol no se movió»*, y es lo único que impide volver a las mediciones
  contaminadas, que ya se cobraron dos piezas.

**Las dos direcciones, siempre.** Un candado que dice «no» a todo pasa igual de
verde que uno que funciona: es el argumento de `siempre_ok` por `siempre_roto` del
paso 2 de `/cerrar`, aplicado aquí. Así que cada barrera se prueba **rechazando lo
malo y aceptando lo bueno**.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_corpus import columnas_declaradas  # noqa: E402
from medir_puerta import _huella_arbol, _lo_que_se_movio, movimiento  # noqa: E402
from referencias import analizar  # noqa: E402


def _fuente(tmp_path: Path, texto: str) -> list[Path]:
    """Una fuente falsa con el contenido que quiera el test.

    Las rutas de dentro se comprueban contra el repo DE VERDAD —que es lo que hace
    el barrido—; lo falso es sólo el documento que las menciona.
    """
    fichero = tmp_path / "FUENTE.md"
    fichero.write_text(texto, encoding="utf-8")
    return [fichero]


def test_el_barrido_dice_que_no_ante_una_referencia_rota(tmp_path: Path) -> None:
    """Demuestra que el cero del paso 8 de `/cerrar` significa algo.

    Sin esto, un barrido que hubiera dejado de extraer rutas —un regex que casa
    con nada— publicaría **0 rotas** en cada cierre y se leería como «todo en
    orden». Es la peor forma de fallar de un candado: en verde.
    """
    fuentes = _fuente(tmp_path, "Mira `src/docbench_es/entity/no_existe.py`, que no existe.\n")

    _, rotas, sin_excusa, _ = analizar(fuentes, declaradas={})

    assert [r.valor for r in rotas] == ["src/docbench_es/entity/no_existe.py"]
    assert len(sin_excusa) == 1


def test_el_barrido_dice_que_si_cuando_la_referencia_existe(tmp_path: Path) -> None:
    """El otro lado, sin el cual lo de arriba se conseguiría rechazándolo todo.

    Es el mismo argumento que `siempre_roto` en el arnés de mutantes: un detector
    que sólo se ha visto decir «no» no ha demostrado que sepa decir «sí».
    """
    fuentes = _fuente(tmp_path, "Mira `src/docbench_es/entity/registry.py`, que sí existe.\n")

    referencias, rotas, sin_excusa, _ = analizar(fuentes, declaradas={})

    assert [r.valor for r in referencias] == ["src/docbench_es/entity/registry.py"]
    assert rotas == [] and sin_excusa == []


def test_una_declaracion_que_ya_no_hace_falta_tambien_pone_rojo(tmp_path: Path) -> None:
    """Demuestra que la excusa caduca sola, que es lo que la separa de una amnistía.

    `DECLARADAS` es la lista de tareas de L3. Si una entrada pudiera quedarse ahí
    después de que su fichero exista, el barrido tendría **su propia afirmación
    vieja dentro** — el mismo bug que persigue, una capa más adentro.
    """
    fuentes = _fuente(tmp_path, "Mira `src/docbench_es/entity/registry.py`.\n")

    _, _, _, sobran = analizar(fuentes, declaradas={"lo/que/sea.py": "ya no hace falta"})

    assert sobran == ["lo/que/sea.py"]


def test_el_guardia_del_arbol_ve_un_fichero_nuevo(tmp_path: Path) -> None:
    """Demuestra la DETECCIÓN sobre un repo de verdad, no sobre una cadena inventada.

    El repo es temporal a propósito: comprobarlo sobre éste exigiría ensuciarlo a
    mitad de una suite, que es justo lo que la barrera prohíbe. `git init` y un
    fichero sin seguir bastan — un fichero recién creado es el caso que importa,
    porque es el estado de todo lo que estrena un hito.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    antes = _huella_arbol(tmp_path)
    (tmp_path / "aparecido.txt").write_text("a mitad de la serie\n", encoding="utf-8")
    ahora = _huella_arbol(tmp_path)

    assert antes != ahora
    assert "+ ?? aparecido.txt" in _lo_que_se_movio(antes, ahora)
    # Y la estabilidad, sin la cual «distinto» no significaría nada: dos lecturas
    # seguidas del mismo árbol tienen que dar la misma huella.
    assert _huella_arbol(tmp_path) == ahora


def test_el_guardia_aborta_la_serie_y_dice_que_se_movio() -> None:
    """Demuestra el cableado: que de «se movió» sale un aborto con su causa.

    La detección y la decisión son dos cosas, y esto prueba la segunda sin correr
    cuarenta veces `make fast`. Antes de este test, el guardia estaba verificado
    **a mano una vez** — el estado que el paso 4 de `/cerrar` llama insuficiente.
    """
    quieto = movimiento("abc\n M RESULTS.md", "abc\n M RESULTS.md", corrida=3, tanda=1)
    movido = movimiento("abc\n M RESULTS.md", "abc\n M RESULTS.md\n?? nuevo.py", corrida=3, tanda=1)

    assert quieto is None
    assert movido is not None
    assert "corrida 3" in movido and "?? nuevo.py" in movido
    assert "DESCARTA ENTERA" in movido


def test_las_dos_barreras_siguen_siendo_las_que_el_repo_ejecuta() -> None:
    """Que lo probado aquí es lo que corre de verdad, y no una copia que divergió.

    Los tests de arriba llaman a funciones importadas; nada garantiza por sí solo
    que el **comando** publicado siga usándolas. Esto lo ata: el barrido real
    termina en verde y su salida trae las tres líneas que `/cerrar` manda pegar.
    """
    salida = subprocess.run(
        ["uv", "run", "python", "scripts/referencias.py"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )

    assert salida.returncode == 0, salida.stdout + salida.stderr
    assert "referencias comprobadas por ejecución" in salida.stdout
    assert "SIN EXCUSA ......... 0" in salida.stdout


def test_una_cita_a_un_adr_que_no_existe_pone_rojo(tmp_path: Path) -> None:
    """**El caso real que obligó a escribir esta comprobación.**

    `ADR-0030` estaba citado en tres documentos —uno de ellos otro ADR, otro un
    módulo de `src/`— y **no existía en ningún commit de ninguna rama**. Una cita
    a una decisión que nadie puede ir a leer es peor que una ruta rota: la ruta se
    nota al abrirla y la cita **se cree**, porque tiene número y parece que hay un
    documento detrás.
    """
    fuentes = _fuente(tmp_path, "Como decidió ADR-9999, esto se hace así.\n")

    _, rotas, sin_excusa, _ = analizar(fuentes, declaradas={})

    assert [(r.tipo, r.valor) for r in rotas] == [("adr", "9999")]
    assert len(sin_excusa) == 1


def test_una_cita_a_un_adr_que_si_existe_pasa(tmp_path: Path) -> None:
    """El otro lado. Y los 0001 a 0012 pasan aunque no tengan fichero: están
    **reservados** a §4 del manual y se transcriben cuando llega su hito, así que
    citarlos antes es legítimo y no es una cita rota."""
    fuentes = _fuente(tmp_path, "ADR-0033 fija los cuatro requisitos, y ADR-0002 el modo.\n")

    _, rotas, _, _ = analizar(fuentes, declaradas={})

    assert rotas == []


# --------------------------------- el barrido medía la máquina, no el repositorio
# El control negativo de arriba prueba el VEREDICTO de la barrera: que dice «no»
# ante algo que no existe y «sí» ante algo que existe. Lo que NO probaba es de
# QUÉ depende esa respuesta. `_existe_ruta` miraba el sistema de ficheros, o sea
# el árbol de trabajo de quien lo corre, así que una referencia a algo que existe
# en local y no está versionado le salía verde a su autor y roja a todo clon.
# Pasó: `.claude/.ultima-puerta`, `.claude/.congelados.sha256` y `runs/l3/docs`
# pusieron CI roja con la puerta ya empujada. Estos dos tests son ese fallo.


def test_una_ruta_que_existe_en_local_pero_no_esta_versionada_pone_rojo(tmp_path: Path) -> None:
    """**El fallo del cierre de L3, convertido en test.**

    La ruta existe en el disco de quien corre esto —se crea aquí mismo— y no está
    en el conjunto de lo versionado. Un barrido que mire el disco la da por buena;
    uno que mire lo que recibe un clon, no. Es la diferencia entre comprobar el
    repositorio y comprobar la máquina.
    """
    artefacto = tmp_path / "artefacto.json"
    artefacto.write_text("{}", encoding="utf-8")
    fuentes = _fuente(tmp_path, "Lo escribe el hook: `.claude/.ultima-puerta`.\n")

    _, rotas, sin_excusa, _ = analizar(
        fuentes, declaradas={}, artefactos={}, en_git=frozenset({"CLAUDE.md"})
    )

    assert [r.valor for r in rotas] == [".claude/.ultima-puerta"]
    assert len(sin_excusa) == 1, "existe en local, pero un clon no la recibe"


def test_un_artefacto_de_ejecucion_que_si_esta_en_git_tambien_pone_rojo(tmp_path: Path) -> None:
    """La dirección contraria de `ARTEFACTOS`, y no es simetría decorativa.

    Declarar «esto no debe estar versionado» y no comprobarlo dejaría la tabla como
    una amnistía: excusaría la ausencia y callaría ante la presencia. Un artefacto
    commiteado por descuido —una caché, un manifiesto de huellas, 362 MB de PDF— es
    un problema, y el sitio donde se ve es el mismo sitio donde se declaró que no
    debía estar.
    """
    fuentes = _fuente(tmp_path, "El corpus vive en `runs/l3/docs`.\n")

    _, _, sin_excusa, _ = analizar(
        fuentes,
        declaradas={},
        artefactos={"runs/l3/docs": "los bytes no se versionan (ADR-0038)"},
        en_git=frozenset({"runs/l3/docs"}),  # ...pero alguien los commiteó
    )

    assert [r.valor for r in sin_excusa] == ["runs/l3/docs"]


def test_un_artefacto_declarado_y_ausente_de_git_pasa(tmp_path: Path) -> None:
    """El aro en la dirección buena, sin el cual los dos de arriba los pasaría un
    barrido que dijera «no» a cualquier artefacto."""
    fuentes = _fuente(tmp_path, "El corpus vive en `runs/l3/docs`.\n")

    _, rotas, sin_excusa, _ = analizar(
        fuentes,
        declaradas={},
        artefactos={"runs/l3/docs": "los bytes no se versionan (ADR-0038)"},
        en_git=frozenset({"CLAUDE.md"}),
    )

    assert [r.valor for r in rotas] == ["runs/l3/docs"], "rota sí: un clon no la tiene"
    assert sin_excusa == [], "pero declarada, y con su razón"


# ----------------------------------------- el detector de coherencia del colgroup
# La tercera barrera de esta sesión, y la que habría cazado sola el fallo del grupo
# de filas: el documento DECLARA sus columnas en `<colgroup>` y `from_html` las
# DERIVA de la extensión de las celdas, sin mirar ese `<colgroup>` jamás. Dos
# caminos independientes sobre el mismo fichero, así que cuando discrepan una de
# las dos está mal — y no hace falta mirar una rejilla a mano para verlo.


def test_el_detector_del_colgroup_caza_la_discrepancia() -> None:
    """**El fallo de `BOE-A-2026-7193`, en cinco líneas.**

    La tabla declaraba 4 columnas y `from_html` producía 5 porque no terminaba el
    grupo de filas, y `validate` la daba por buena: los importes de la primera
    fila de tarifas caían en columnas distintas que los de las demás. Un `ok=True`
    sobre datos en la celda equivocada es la peor forma de fallar de este repo, y
    esto lo convierte en una cifra.
    """
    declara_cuatro = "<colgroup><col/><col/><col/><col/></colgroup>"

    assert columnas_declaradas(f"<table>{declara_cuatro}<tr><td>a</td></tr></table>") == 4


def test_col_span_cuenta_lo_que_declara_y_no_uno() -> None:
    """`<col span="3">` son tres columnas, no una.

    Contarlo como una daría una discrepancia en toda tabla que use la forma corta:
    un detector con falsos positivos deja de leerse, que es el mismo argumento por
    el que el barrido de referencias exige cero.
    """
    assert columnas_declaradas('<table><colgroup><col/><col span="3"/></colgroup></table>') == 4


def test_sin_colgroup_es_none_y_no_cero() -> None:
    """El aro que evita que el detector grite contra media tabla del mundo.

    Sin `<colgroup>` el documento **no ha declarado nada**, y eso no es «declara
    cero columnas»: confundirlos convertiría toda tabla sin `<colgroup>` en una
    discrepancia. Es la misma distinción que `None` contra `""` en el emparejado.
    """
    assert columnas_declaradas("<table><tr><td>a</td><td>b</td></tr></table>") is None
