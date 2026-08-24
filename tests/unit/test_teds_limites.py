"""§9.2 + §12 · Los casos límite de TEDS, cada uno con el número de la REFERENCIA.

Están en `tests/fixtures/pubtabnet/casos_limite.json`, congelado, y los calculó
la implementación de referencia de PubTabNet. No son casos suyos: salen de lo que
encontró `hypothesis` y de las decisiones de ADR-0021. Existen para que cada
afirmación de un docstring tenga detrás un número ajeno en vez de uno calculado
por el mismo código que se está validando.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docbench_es.core.canonical import from_html, validate
from docbench_es.core.teds import (
    SUELO_DE_PUBLICACION,
    para_publicar,
    teds,
    teds_struct,
)
from docbench_es.types import CanonicalCell, CanonicalTable

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "pubtabnet"
LIMITE: dict[str, dict[str, str | float]] = json.loads(
    (FIXTURES / "casos_limite.json").read_text(encoding="utf-8")
)
VACIA = CanonicalTable((), 0, 0, (1, 1), None, True, "html")
DIVERGENTE = "teds_negativo"
"""El único caso donde NO coincidimos con la referencia, y por un mecanismo
nombrado: ver `test_el_caso_del_derrame_de_grupo_diverge_de_la_referencia`. Sale
de la lista de coincidencias para que ésta siga significando lo que dice."""

CON_VALOR = sorted(k for k, v in LIMITE.items() if "teds" in v and k != DIVERGENTE)


@pytest.mark.parametrize("nombre", CON_VALOR)
def test_los_casos_limite_coinciden_con_la_referencia(nombre: str) -> None:
    """Demuestra que la coincidencia no se limita a los casos amables.

    Los 20 de PubTabNet son tablas de artículos científicos, todas bien formadas.
    Éstos son los bordes: un TEDS negativo, un `<tbody>` de más, un `<th>` donde
    va un `<td>`, y las tres variantes de hueco contra celda vacía. Si la
    coincidencia sólo se diera en el centro de la distribución, el criterio de L2
    estaría midiendo el caso fácil.
    """
    caso = LIMITE[nombre]
    pred = from_html(str(caso["pred"]))
    gold = from_html(str(caso["gold"]))
    assert pred and gold, "el caso tiene que traer tabla por los dos lados"

    assert round(teds(pred[0], gold[0]), 4) == round(float(caso["teds"]), 4)
    assert round(teds_struct(pred[0], gold[0]), 4) == round(float(caso["teds_s"]), 4)


def test_la_forma_canonica_borra_una_distincion_que_la_referencia_si_ve() -> None:
    """Demuestra el trade-off de ADR-0021 con sus dos números, y que es querido.

    `<table><tr>…` y `<table><tbody><tr>…` son la misma tabla. La referencia sobre
    el HTML crudo les da **0,666667**, porque para ella un `<tbody>` de más es un
    nodo de más. Pasadas por la forma canónica son idénticas y dan **1,000000**.

    Es el comportamiento que se quiere: un extractor no debe pagar por omitir un
    `<tbody>` que no cambia la tabla. Pero es una distinción que se pierde, y
    perderla a propósito hay que poder enseñarlo — de ahí los dos números en el
    fixture.

    Y la otra cara: `<th>` contra `<td>` **sí** sobrevive, porque la condición de
    cabecera viaja en `<thead>`. Los dos dan 0,666667.
    """
    caso = LIMITE["tbody_de_mas"]
    assert float(caso["referencia_sobre_el_crudo"]) == pytest.approx(0.666667, abs=1e-6)
    assert float(caso["teds"]) == 1.0

    cabecera = LIMITE["th_donde_va_td"]
    assert float(cabecera["teds"]) == pytest.approx(0.666667, abs=1e-6)
    assert float(cabecera["referencia_sobre_el_crudo"]) == pytest.approx(0.666667, abs=1e-6)


def test_teds_puede_ser_negativo_y_esta_medido() -> None:
    """**El hallazgo sobre la métrica**, no sobre esta implementación.

    TEDS no está acotado por cero. La distancia se calcula sobre los árboles con
    su raíz y el denominador cuenta sólo los descendientes, así que entre dos
    tablas suficientemente distintas la distancia se pasa del denominador.

    Importa porque §12 publica TEDS como nota y una nota negativa no se pondera
    igual que una entre 0 y 1: **L5 tiene que decidir si se recorta a cero al
    publicar, y decirlo**. Está en `LIMITS.md` 44. Recortarlo aquí sería apartarse
    de la referencia en silencio.

    **Lo que este test NO afirma ya es que coincidamos con la referencia en este
    caso.** Eso lo fija, con su valor y su mecanismo, el test de abajo.
    """
    caso = LIMITE[DIVERGENTE]
    assert float(caso["teds"]) < 0, "el fixture tiene que traer el caso negativo"
    pred, gold = from_html(str(caso["pred"]))[0], from_html(str(caso["gold"]))[0]
    assert teds(pred, gold) < 0, "sigue siendo negativo: el hallazgo aguanta"


def test_el_caso_del_derrame_de_grupo_diverge_de_la_referencia() -> None:
    """**Tercer hallazgo sobre la métrica, y el que fija una diferencia conocida.**

    Lo primero, porque es lo que sostiene todo lo demás: **los 20 golden sobre los
    casos propios de PubTabNet siguen coincidiendo a cuatro decimales.** La
    afirmación «esto es TEDS» no se toca y su evidencia tampoco. Lo que diverge es
    **un caso límite que construimos nosotros**.

    **El mecanismo, que es lo que hay que nombrar y no el síntoma:** no es que
    demos otro número. Es que **modelamos la REJILLA y la referencia modela el
    ÁRBOL parseado**, y para una tabla con derrame de grupo de filas —un `rowspan`
    de la última fila del `<thead>` que se mete en el `<tbody>`— esos dos objetos
    **no son el mismo**. El estándar termina el grupo avanzando hasta `yheight`,
    así que en la rejilla hay una fila implícita que en el árbol de etiquetas no
    existe. La referencia no la ve porque nunca construye una rejilla.

    **Y el objeto correcto PARA ESTE BANCO es la rejilla.** Lo que se mide es si
    el extractor reprodujo la ESTRUCTURA de la tabla, no su marcado: un extractor
    que acierta la rejilla tiene que puntuar 1,0 aunque escriba los `<tbody>` de
    otra forma. Ésa es la razón de existir de `CanonicalTable`, y es la misma por
    la que `tbody_de_mas` da 1,0 aquí y 0,666667 en la referencia.

    **El golden NO se toca**: el orden de sospecha es código, test, nunca el
    fichero congelado — y aquí el código está bien. Lo que cambia es la aserción.
    """
    caso = LIMITE[DIVERGENTE]
    pred, gold = from_html(str(caso["pred"]))[0], from_html(str(caso["gold"]))[0]

    nuestro = round(teds(pred, gold), 6)

    assert nuestro == -0.125, "la rejilla, con la fila implícita del derrame"
    assert float(caso["referencia_sobre_el_crudo"]) == pytest.approx(-0.142857, abs=1e-6)
    assert nuestro != round(float(caso["teds"]), 6), "diferencia CONOCIDA y explicada"
    # Y la razón, comprobable: el gold tiene una fila más en la rejilla que <tr>
    # escritos, que es exactamente la fila implícita que la referencia no ve.
    assert gold.n_rows == 4 and str(caso["gold"]).count("<tr") == 3


def test_dos_tablas_vacias_dan_uno_donde_la_referencia_revienta() -> None:
    """Demuestra el caso degenerado donde manda §12 y no la referencia.

    §12: *«Tabla vacía: se define como 1 si las dos lo están, 0 si solo una»*. La
    referencia **lanza `ZeroDivisionError`**, porque divide por un número de nodos
    que es cero, y eso está congelado en el fixture como prueba. Cuando el manual
    define un caso y la referencia no lo cubre, gana el manual.
    """
    assert "ZeroDivisionError" in str(LIMITE["dos_vacias"]["referencia"])

    assert teds(VACIA, VACIA) == 1.0
    assert teds_struct(VACIA, VACIA) == 1.0
    algo = from_html("<table><tr><td>a</td></tr></table>")[0]
    assert teds(VACIA, algo) == 0.0
    assert teds(algo, VACIA) == 0.0


def test_el_suelo_es_de_presentacion_y_el_calculo_no_se_toca() -> None:
    """**Fija la decisión de ADR-0023 para que L5 no la cambie en silencio.**

    Las dos mitades tienen que seguir siendo verdad a la vez:

    - `teds()` devuelve el número de la referencia, **negativo incluido**. Si
      alguien recortara ahí, este proyecto dejaría de reproducir la referencia y
      el criterio de aceptación de L2 pasaría a medir otra cosa.
    - `para_publicar()` recorta a 0, y **sólo eso**: no toca los valores que ya
      están en rango.

    Un TEDS negativo significa que convertir la predicha en la real cuesta más
    ediciones que nodos tiene la mayor de las dos, o sea que **la predicción es
    peor que no haber predicho nada** —la predicción vacía puntúa 0—.
    """
    caso = LIMITE[DIVERGENTE]
    pred, gold = from_html(str(caso["pred"]))[0], from_html(str(caso["gold"]))[0]
    crudo = teds(pred, gold)

    assert crudo < 0, "el cálculo NO se recorta"
    assert round(crudo, 6) == -0.125, "el nuestro, sobre la rejilla (ver la divergencia)"
    assert para_publicar(crudo) == 0.0, "al publicar sí"
    assert para_publicar(0.75) == 0.75, "y no toca nada más"
    assert SUELO_DE_PUBLICACION == 0.0

    # La predicción vacía puntúa 0: por eso el negativo es «peor que nada».
    assert teds(VACIA, gold) == 0.0
    assert crudo < teds(VACIA, gold)


def test_teds_no_comprueba_su_precondicion_y_el_numero_no_es_interpretable() -> None:
    """**Fija el contrato de `teds` sobre entrada inválida.** Es una precondición.

    `teds` declara en su docstring que asume tablas que pasan `validate()` sin
    hallazgos fatales, y que **no lo comprueba**. Este test fija las dos mitades:

    - con una tabla que `validate` rechaza, `teds` **no lanza** y devuelve un
      número —0,75 aquí, que parece una nota normal—;
    - ese número **no es interpretable**, y el nombre de este test es el sitio
      donde eso está escrito de forma que se lea al ejecutarlo.

    **Se cae si alguien decide en el futuro que `teds` valide**, que es el punto:
    esa decisión cambiaría la firma de §9.2 y el criterio de aceptación de L2, y
    tiene que ser deliberada en vez de colarse como una mejora.
    """
    buena = from_html("<table><tr><td>a</td><td>b</td></tr></table>")[0]
    solapada = CanonicalTable(
        cells=(CanonicalCell(0, 0, 1, 2, "a"), CanonicalCell(0, 1, 1, 1, "b")),
        n_rows=1,
        n_cols=2,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    ok, problemas = validate(solapada)
    assert ok is False and any(p.startswith("SOLAPE") for p in problemas)

    valor = teds(solapada, buena)
    assert isinstance(valor, float), "no lanza: devuelve un número"
    assert round(valor, 6) == 0.75, "y tiene aspecto de nota normal, que es el peligro"
