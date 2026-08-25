"""Los tres guardianes que L4 estrena, cada uno visto ROJO. Y el colocador con spans.

## Por qué existe este fichero

La regla en firme del repo: **un módulo cuyo único trabajo es PONERSE ROJO trae su
control negativo en el MISMO hito**. Código de producción que está mal se delata en
lo que produce; una barrera que está mal **se delata con silencio**, que se lee igual
que ir bien.

L4 estrena tres barreras y las tres se cerraron sin control:

| Barrera | Qué impide |
|---|---|
| `corregir_fixtures_l4.respalda_el_pdf` | corregir un fixture con algo que el PDF no dice |
| `congelar_l4` | re-congelar una huella que cambió sin corrección registrada |
| `mutar_el_instrumento._clave` | contar como «detectado» un cambio de presentación |

Y `RESULTS.md` llegó a publicar *«se ha comprobado que sabe decir que no»* **sin
comando, sin test y sin artefacto**, que es exactamente la frase que este repo no
admite. Detectado en el escrutinio adversarial del cierre de L4.

## Lo que NO se puede probar aquí, y va declarado

`respalda_el_pdf` necesita `runs/l3/docs/*.pdf`, que **no está en el repo** —son 362
MB— y el binario `pdftotext`. Así que su control negativo **no puede correr en la
puerta**: se salta con su razón, en vez de dar un verde que no significa nada. Ver
`LIMITS.md` 74.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from comparar_verdad import colocar  # noqa: E402
from congelar_l4 import sin_respaldo  # noqa: E402
from mutar_el_instrumento import _clave  # noqa: E402

# ---------------------------------------------------------------- el colocador
# `comparar_verdad.colocar` es, según su propio docstring, «lo más importante del
# fichero»: está escrito a mano para NO cancelar un error de colocación contra
# `_rejilla`. Y los 5 controles de `test_comparar_verdad.py` lo ejercitan **sólo con
# `spans: []`**, cuando 8 de los 30 fixtures llevan spans. Un colocador sin probar
# es la pieza que decidiría mal en silencio.


def test_el_colocador_del_comparador_salta_lo_que_ocupa_un_rowspan() -> None:
    """La regla del estándar: la celda va a la primera columna libre a la derecha.

    Con un `rowspan=2` en (0,0), la celda que abre la fila 1 **no** puede caer en la
    columna 0. Un colocador que no lo salte pone los datos una columna a la
    izquierda — que es la misma familia del bug del grupo de filas.
    """
    filas = [["cabecera", "A"], ["B"], ["C", "D"]]
    spans = [{"row": 0, "col": 0, "rowspan": 2, "colspan": 1}]

    rejilla, textos = colocar(filas, spans)

    assert textos[(0, 0)] == "cabecera"
    assert textos[(1, 1)] == "B", "la fila 1 empieza en la columna 1, no en la 0"
    assert (1, 0) in rejilla and (1, 0) not in textos, "(1,0) está cubierta, no anclada"
    assert textos[(2, 0)] == "C", "en la fila 2 el rowspan ya no cubre"


def test_el_colocador_del_comparador_avanza_el_cursor_con_un_colspan() -> None:
    """Un `colspan=2` ocupa dos columnas: la siguiente celda va a la tercera."""
    filas = [["ancha", "detrás"]]
    spans = [{"row": 0, "col": 0, "rowspan": 1, "colspan": 2}]

    rejilla, textos = colocar(filas, spans)

    assert textos[(0, 0)] == "ancha"
    assert (0, 1) in rejilla and (0, 1) not in textos
    assert textos[(0, 2)] == "detrás", "el cursor tiene que haber saltado dos"


# ------------------------------------------------- la identidad de una discrepancia


def test_la_identidad_de_una_discrepancia_ignora_el_texto_de_la_celda() -> None:
    """**El control del hallazgo que puso mal la tabla de mutantes publicada.**

    `cambia` comparaba el detalle formateado, que lleva dentro el texto de la celda.
    Con eso, un mutante que sólo cambiara cómo se renderiza el texto contaba como
    detectado: `normalizador_agresivo` salía «cambia 3 de 30» sin detectar nada.
    """
    antes = _clave("TEXTO", "(4, 0): a mano 'Serós', la verdad 'Seròs'")
    solo_cambia_el_texto = _clave("TEXTO", "(4, 0): a mano 'seros', la verdad 'seros'")
    otra_posicion = _clave("TEXTO", "(5, 0): a mano 'Serós', la verdad 'Seròs'")
    otra_clase = _clave("ESTADO", "(4, 0): a mano ancla, la verdad hueco")

    assert antes == solo_cambia_el_texto, "el texto NO es parte de la identidad"
    assert antes != otra_posicion, "la posición SÍ lo es"
    assert antes != otra_clase, "la clase también"


def test_una_discrepancia_sin_posicion_no_se_confunde_con_otra() -> None:
    """`DIMENSION` no lleva posición. Colapsarla con un `-` no puede hacer que dos
    clases distintas den la misma clave."""
    assert _clave("DIMENSION", "a mano 25x4, la verdad 26x4") != _clave("SIN_VERDAD", "-")


# ------------------------------------------------------- el guardián de re-congelar


def test_re_congelar_aborta_sin_correccion_registrada(
    tmp_path: Path,
) -> None:
    """**El guardián de `congelar_l4.py`, visto rojo.**

    Es el que impide que «re-congelar» sea «tapar un cambio»: si una huella se movió
    y no hay una corrección con evidencia del PDF que la explique, no escribe nada.
    Aquí se le da exactamente ese caso.
    """
    antes = {"a.json": "0" * 64, "b.json": "1" * 64}
    ahora = {"a.json": "0" * 64, "b.json": "2" * 64}  # b cambió

    coladas, mentirosas = sin_respaldo(antes, ahora, con_evidencia=set())

    assert coladas == ["b.json"], "un cambio sin corrección tiene que salir a la luz"
    assert mentirosas == []
    # Y las otras dos direcciones, porque un guardián que sólo dice «no» no sirve:
    assert sin_respaldo(antes, ahora, {"b.json"}) == ([], []), "con su corrección, pasa"
    assert sin_respaldo(antes, antes, {"b.json"}) == ([], ["b.json"]), (
        "una corrección registrada que no movió ninguna huella también aborta:"
        " es un registro que miente sobre lo que hizo"
    )


@pytest.mark.skipif(
    not (RAIZ / "runs" / "l3" / "docs").is_dir(),
    reason="necesita runs/l3/docs, que son 362 MB y NO están en el repo. LIMITS 74",
)
def test_el_guardian_del_pdf_rechaza_una_correccion_que_el_pdf_no_respalda() -> None:
    """**El guardián de `corregir_fixtures_l4.py`, visto rojo**, cuando hay corpus.

    Los cuatro casos son los que `RESULTS.md` afirmaba sin comando: un acento
    inventado, «corregir» a lo mismo que ya había, puntos de más, y —el que más
    importa— **corregir una discrepancia de FRONTERA**, donde el PDF respalda la
    transcripción y no la verdad. Si ese último se aceptara, «corregir con
    evidencia» sería «ajustar hasta que pase».
    """
    from corregir_fixtures_l4 import respalda_el_pdf

    malos = [
        ("BOE-A-2026-6957", "Ayuntamiento de Serós (Lleida).", "Ayuntamiento de Serôs (Lleida)."),
        ("BOE-A-2026-6957", "Ayuntamiento de Serós (Lleida).", "Ayuntamiento de Serós (Lleida)."),
        ("BOE-A-2026-6204", "...", "...."),
        (
            "BOE-A-2026-5851",
            "Técnico Desarrollo Nuevo Producto/Métodos/ Mantenimiento.",
            "Técnico Desarrollo Nuevo Producto/Métodos/Mantenimiento.",
        ),
    ]
    for ident, puse, corregido in malos:
        ok, _ = respalda_el_pdf(ident, puse, corregido)
        assert not ok, f"el guardián acepta una corrección sin respaldo: {corregido!r}"

    bueno, _ = respalda_el_pdf(
        "BOE-A-2026-6957", "Ayuntamiento de Serós (Lleida).", "Ayuntamiento de Seròs (Lleida)."
    )
    assert bueno, "el aro en la dirección buena: la corrección real sí se acepta"


def test_las_seis_correcciones_registradas_son_las_que_dice_el_manifiesto() -> None:
    """Que el artefacto y el manifiesto no se puedan contradecir en silencio."""
    correcciones = json.loads(
        (RAIZ / "runs" / "l4" / "correcciones.json").read_text(encoding="utf-8")
    )
    recongelacion = json.loads(
        (RAIZ / "runs" / "l4" / "recongelacion.json").read_text(encoding="utf-8")
    )

    assert correcciones["n"] == len(correcciones["correcciones"]) == 6
    assert len(recongelacion["cambiados"]) == 4, "3 correcciones + 1 anotación"
    assert len(recongelacion["por_correccion_con_evidencia"]) == 3
    assert len(recongelacion["por_anotacion_sin_tocar_la_transcripcion"]) == 1
    assert recongelacion["intactos"] == 26
