"""Los DOS sellos: de qué árbol salieron las extracciones y de cuál la puntuación.

Una corrida y su informe son **dos actos separados en el tiempo**, y el segundo se repite
sobre el primero meses después. Imprimir sólo el commit de la corrida contesta de dónde
salieron las EXTRACCIONES y calla sobre quién las PUNTUÓ, que es la mitad que el informe
controla.

Y hay una trampa de lectura que estos tests fijan: **los tres campos del sello no
discriminan lo mismo.** `huella` es el `sha256` del diff, así que vale `01ba4719c80b6fe9`
para **cualquier** árbol limpio. Dos huellas iguales no dicen que sea el mismo árbol.
"""

from __future__ import annotations

from docbench_es.report.procedencia import bloque, difieren

LIMPIO = "01ba4719c80b6fe9"
CORRIDA = {"commit": "819c06f", "sucios": 0, "huella": LIMPIO, "empezada": "2026-08-27T10:39:57Z"}


def test_dos_arboles_limpios_distintos_comparten_huella_y_los_separa_el_commit() -> None:
    """**El caso que se lee como una contradicción**, y que pasó de verdad: la tabla decía
    huella `01ba…` en los dos lados y «NO son el mismo árbol» debajo.

    `huella` discrimina **limpio de sucio**, no un commit de otro. Es correcto y es
    justamente lo que hay que decir, porque presentar los tres campos juntos hace creer
    que el tercero identifica el árbol.
    """
    informe = {"commit": "8b2def5", "sucios": 0, "huella": LIMPIO}
    assert difieren(CORRIDA, informe) == {"commit": ("819c06f", "8b2def5")}
    texto = "\n".join(bloque(CORRIDA, informe))
    assert "NO son el mismo árbol" in texto
    assert "Dos huellas iguales no dicen que sea el mismo árbol" in texto, texto
    assert "el único que separa un árbol limpio de otro" in texto


def test_el_mismo_arbol_en_los_dos_se_dice_igual() -> None:
    """La procedencia se publica **siempre**, no sólo cuando hay discrepancia: si sólo
    apareciera al fallar, su ausencia se leería como «no se miró»."""
    texto = "\n".join(bloque(CORRIDA, dict(CORRIDA)))
    assert "Mismo árbol en los dos" in texto
    assert not difieren(CORRIDA, dict(CORRIDA))


def test_sin_arbol_del_informe_se_dice_que_es_un_hueco_y_no_una_coincidencia() -> None:
    """Un informe sin su propio sello no es un informe sobre el árbol de la corrida: es un
    informe que no dice sobre qué árbol puntuó."""
    texto = "\n".join(bloque(CORRIDA, None))
    assert "no se registró" in texto
    assert "Es un hueco" in texto


def test_un_arbol_sucio_si_mueve_la_huella() -> None:
    """Lo que `huella` SÍ hace, para que el test de arriba no se lea como que no sirve:
    con el árbol sucio distingue un diff de otro, que es para lo que existe."""
    sucio = {"commit": "8b2def5", "sucios": 3, "huella": "ffff0000ffff0000"}
    assert set(difieren(CORRIDA, sucio)) == {"commit", "sucios", "huella"}
