"""El conjunto de conformidad declara qué veredictos puede producir, y es verdad.

## La clase de fallo que este fichero cierra

`veredicto_de_spans` devuelve `SIN_EVIDENCIA` cuando un extractor declara
`expresses_spans=False`, su formato sí permite spans y **no hubo ocasión** de
demostrarlo. Si el conjunto de conformidad no trajera ni una celda combinada, **todo
extractor saldría `SIN_EVIDENCIA` para siempre**: la suite correría, saldría verde, y su
verde no significaría lo que parece.

Es el límite 77 —*una protección que no dice cuánto protege es indistinguible de no
proteger nada*— aplicado a un conjunto de datos en vez de a un glob. Y la respuesta es
la misma: **el conjunto publica su denominador** y un test afirma que no es cero.

## Y la declaración se contrasta contra la verdad CONGELADA

«Trae celdas combinadas» no es una opinión de quien escribió el YAML: son los `spans` de
un fixture de `runs/l4/fixtures/`, que está congelado y no se puede tocar para que
salgan los números. Si alguien mete en la lista de «con combinadas» un documento que no
las tiene, esto se cae nombrándolo.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from conjunto_conformidad import conjunto, veredictos_posibles  # noqa: E402


def test_lo_declarado_cuadra_con_la_verdad_congelada_de_l4() -> None:
    """Documento a documento, y nombrando al que no cuadre. **Corre SIEMPRE.**

    Todo lo que compara sale de ficheros **versionados** —los fixtures congelados de L4
    y `runs/l3/manifiesto.json`—, así que esto se puede comprobar en cualquier clon y en
    CI. Es la mitad que sostiene el número publicado *«veredictos que este conjunto puede
    producir»*; la otra mitad, los bytes del PDF, es la única que no se puede.

    Cubre cuatro cosas y no una: que el fixture **exista**, que los spans cuadren con lo
    declarado, que la forma declarada sea la real, y que las páginas sean las del
    manifiesto. Las tres últimas son números tecleados en un YAML, y un número tecleado
    se queda viejo.
    """
    elegidos = conjunto()
    assert elegidos, "el conjunto está vacío: no protegería nada"
    descuadran = [e.por_que_no() for e in elegidos if not e.cuadra]
    assert not descuadran, "\n  " + "\n  ".join(descuadran)


def test_un_fixture_que_desaparece_no_pasa_en_silencio() -> None:
    """**El control negativo del caso que se colaba.**

    Antes, `cuadra` era sólo `declara == (spans > 0)`. Un fixture borrado daba `spans=0`,
    así que **un documento declarado «sin combinadas» seguía cuadrando** aunque su
    fichero de verdad ya no existiera. La comprobación no comprobaba.

    Aquí se fabrica ese caso exacto y se exige que `cuadra` sea falso y que el motivo
    nombre el fichero.
    """
    real = next(e for e in conjunto() if not e.declara_combinadas)
    huerfano = replace(real, fixture_existe=False, spans_en_la_verdad=0)

    assert not huerfano.cuadra, "un fixture que no existe no puede cuadrar"
    assert huerfano.tabla in huerfano.por_que_no()
    assert "no existe" in huerfano.por_que_no()


def test_todos_los_elegidos_tienen_su_pdf() -> None:
    """Un documento sin PDF no se puede ejecutar, así que su aro no se corre — y un aro
    que no se corre no está superado. Saldría `NO_EJECUTADA`, no un aprobado.

    **Este test SE SALTA donde no está el corpus, y eso incluye CI.** Los PDF de
    `runs/l3/docs/` no se versionan —son 1.000 documentos ajenos— así que en un clon
    limpio no existen. Lo descubrió el clon frío: sin el salto, la puerta se ponía roja
    en cualquier máquina que no fuera la que cosechó el corpus, que es exactamente la
    clase de fallo que los límites 92 y 94 cerraron para `mypy` y `ruff`.

    Un salto **no es un aprobado**, y por eso el mensaje lo dice: en CI esta
    precondición no se comprueba, y quien vaya a correr la conformidad de verdad la
    comprueba en su máquina, que es donde está el corpus.
    """
    elegidos = conjunto()
    if not (RAIZ / "runs" / "l3" / "docs").is_dir():
        pytest.skip(
            "sin corpus en runs/l3/docs: NO se ha comprobado que los elegidos tengan PDF. "
            "No es un aprobado, es que aquí no se puede mirar"
        )
    sin_pdf = [e.ident for e in elegidos if not e.pdf]
    assert not sin_pdf, f"elegidos sin PDF en runs/l3/docs: {sin_pdf}"


def test_el_conjunto_puede_producir_escondido_o_no_discrimina_nada() -> None:
    """**El candado de la clase.**

    `ESCONDIDO` es la casilla que sólo el conjunto puede habilitar: hace falta que el
    documento traiga celdas combinadas para que un extractor pueda emitirlas y delatarse.
    Sin ella, un extractor que se refugia en `NO_APLICABLE` pasa la suite.

    Y su reverso: con ocasión, un `False` honesto se puede **confirmar**. Sin ella, ese
    extractor se queda en `SIN_EVIDENCIA` para siempre por hacer lo que declara.
    """
    posibles = veredictos_posibles(conjunto())
    assert "ESCONDIDO" in posibles, (
        f"el conjunto no puede producir ESCONDIDO: {sorted(posibles)}. Ningún documento "
        "trae celdas combinadas en la verdad de referencia, así que el veredicto de "
        "spans no discrimina nada y su verde no significa lo que parece"
    )
    assert "SIN_EVIDENCIA" not in posibles, (
        "con el conjunto entero SIN_EVIDENCIA no debería ser alcanzable; que lo sea "
        "significa que el conjunto se ha degradado"
    )


def test_un_conjunto_sin_combinadas_lo_dice_en_vez_de_callarselo() -> None:
    """**El control negativo.** Se le quitan los documentos con combinadas y se exige que
    el propio conjunto declare que ya no puede emitir `ESCONDIDO`.

    Sin este control, `veredictos_posibles` podría devolver siempre las cuatro casillas y
    el test de arriba pasaría en verde sin comprobar nada.
    """
    elegidos = conjunto()
    sin_ocasion = [e for e in elegidos if e.spans_en_la_verdad == 0]
    assert sin_ocasion, "el molde del control está mal: no hay ninguno sin combinadas"
    posibles = veredictos_posibles(sin_ocasion)
    assert "ESCONDIDO" not in posibles, f"dice que puede y no puede: {sorted(posibles)}"
    assert "SIN_EVIDENCIA" in posibles, "sin ocasión, SIN_EVIDENCIA es el desenlace"
