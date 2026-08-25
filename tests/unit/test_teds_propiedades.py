"""§9.2 · Las propiedades de TEDS, y su sensibilidad a la degradación.

Los golden de `test_teds_referencia.py` demuestran que este TEDS **es** TEDS.
Esto demuestra otra cosa: que **se comporta como una métrica** y que **detecta lo
que dice detectar**. Lo segundo es lo que §14 llama test de degradación y lo que
llama *«sin esto, las métricas son números sin validar»*.

**Presupuesto de ejemplos declarado**, que exige `/cerrar`: `max_examples=30` en
las propiedades de este fichero. Es bajo a propósito —cada ejemplo construye dos
árboles y corre una distancia de edición cuadrática— y va escrito aquí para que
la suite no crezca hasta que alguien se queje. Si algún día hace falta más
búsqueda, se sube este número y se remide la puerta, no se quita el tope.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from _estrategias import tabla_completa, tabla_con_dos_filas_de_cabecera
from docbench_es.core.teds import teds, teds_struct
from docbench_es.core.teds._arbol import a_arbol, n_nodos
from docbench_es.types import CanonicalCell, CanonicalTable

EJEMPLOS = 30


def _sin(t: CanonicalTable, i: int) -> CanonicalTable:
    return CanonicalTable(
        cells=tuple(c for j, c in enumerate(t.cells) if j != i),
        n_rows=t.n_rows,
        n_cols=t.n_cols,
        page_span=t.page_span,
        caption=t.caption,
        expresses_spans=t.expresses_spans,
        source_format=t.source_format,
    )


@settings(max_examples=EJEMPLOS)
@given(t=tabla_completa())
def test_una_tabla_contra_si_misma_vale_uno(t: CanonicalTable) -> None:
    """Demuestra el extremo bueno de la escala, sobre tablas arbitrarias.

    Es el control que ningún golden puede dar: los 20 casos de PubTabNet traen
    **seis** unos, pero todos con la misma forma de tabla. Si `teds` devolviera
    0,999 para una tabla contra sí misma en alguna forma concreta —por ejemplo
    con `rowspan` largos—, el extractor perfecto nunca sacaría un 1 y el techo
    del banco estaría torcido sin que nadie lo viera.
    """
    assert teds(t, t) == 1.0
    assert teds_struct(t, t) == 1.0


@settings(max_examples=EJEMPLOS)
@given(t=tabla_completa(), otra=tabla_completa())
def test_esta_en_el_rango_y_es_simetrica(t: CanonicalTable, otra: CanonicalTable) -> None:
    """Demuestra el rango REAL de TEDS, que **no es [0,1]**, y su simetría.

    La primera versión de este test afirmaba `0 <= teds <= 1`. Es falso, y lo
    encontró `hypothesis`: TEDS **puede salir negativo**. La distancia de edición
    se calcula sobre los árboles CON su raíz y el denominador cuenta sólo los
    DESCENDIENTES, así que entre dos tablas muy distintas la distancia puede pasar
    del denominador. Comprobado contra la implementación de referencia, que
    devuelve exactamente el mismo **-0,142857**: no es un bug de aquí, es la
    fórmula publicada.

    La cota inferior real es -1: en el peor caso la distancia es `n_a + n_b`, o
    sea `1 - (n_a+n_b)/max(n_a,n_b) >= -1`.

    La simetría importa por otro motivo: el manual llama a los argumentos `pred` y
    `gold`, y si el orden cambiara el número, invertir un par por descuido en L5
    daría una tabla de resultados distinta sin que nada fallara.
    """
    valor = teds(t, otra)
    assert -1.0 <= valor <= 1.0
    assert valor == teds(otra, t)
    assert -1.0 <= teds_struct(t, otra) <= 1.0


@settings(max_examples=EJEMPLOS)
@given(t=tabla_completa(), otra=tabla_completa())
def test_la_estructura_nunca_puntua_peor_que_el_contenido(
    t: CanonicalTable, otra: CanonicalTable
) -> None:
    """Demuestra que TEDS-S es una cota superior de TEDS, y por qué eso se espera.

    TEDS-S ignora el contenido: dos celdas con texto distinto pasan a ser
    idénticas, así que cualquier coste de renombrado por texto desaparece y
    ninguno aparece. Si alguna vez TEDS-S saliera POR DEBAJO de TEDS, sería señal
    de que `solo_estructura` está cambiando la forma del árbol además del
    contenido, que es un bug que ningún golden cazaría porque los golden
    comparan cada métrica por separado.

    Comprobado además sobre los 20 casos reales de PubTabNet, donde se cumple.
    """
    assert teds_struct(t, otra) >= teds(t, otra) - 1e-12


@settings(max_examples=EJEMPLOS)
@given(t=tabla_completa(), semilla=st.integers(min_value=0, max_value=999))
def test_borrar_una_celda_baja_la_nota(t: CanonicalTable, semilla: int) -> None:
    """**El test de degradación de §14.** Demuestra que la métrica es SENSIBLE.

    Se degrada la tabla a propósito —se borra una celda— y TEDS tiene que
    bajar. Sin esto, TEDS podría ser una función que devuelve casi 1 siempre y
    todos los extractores saldrían buenos: *«sin esto, las métricas son números
    sin validar»*.

    La cota es estricta: no basta con «no sube», tiene que BAJAR. Una métrica que
    empata ante una celda perdida no distingue al extractor que se come una fila.
    """
    if len(t.cells) < 2:
        return
    degradada = _sin(t, semilla % len(t.cells))
    assert teds(degradada, t) < 1.0
    assert teds_struct(degradada, t) < 1.0


@settings(max_examples=EJEMPLOS)
@given(t=tabla_completa(), semilla=st.integers(min_value=0, max_value=999))
def test_romper_el_texto_baja_teds_pero_no_teds_s(t: CanonicalTable, semilla: int) -> None:
    """Demuestra que las dos métricas miden cosas DISTINTAS, no la misma dos veces.

    Se cambia el texto de una celda sin tocar la rejilla: TEDS baja porque el
    contenido cambió, TEDS-S se queda en 1,0 porque la estructura es la misma. Si
    las dos se movieran igual, publicar las dos sería publicar el mismo número
    dos veces, y §12 las presenta como dos filas de la tabla de nivel 1.
    """
    if not t.cells:
        return
    i = semilla % len(t.cells)
    c = t.cells[i]
    celdas = list(t.cells)
    celdas[i] = CanonicalCell(c.row, c.col, c.rowspan, c.colspan, c.text + "XYZ", c.is_header)
    rota = CanonicalTable(
        tuple(celdas), t.n_rows, t.n_cols, t.page_span, t.caption, True, t.source_format
    )
    assert teds(rota, t) < 1.0
    assert teds_struct(rota, t) == 1.0


@settings(max_examples=EJEMPLOS)
@given(t=tabla_completa())
def test_el_denominador_son_los_descendientes_de_table(t: CanonicalTable) -> None:
    """Demuestra el detalle del que depende cada número: qué se cuenta.

    La referencia normaliza por `len(table.xpath(".//*"))`, o sea los
    DESCENDIENTES de `<table>`, sin contar la raíz. Contar la raíz movería todos
    los TEDS del proyecto hacia arriba, poco y en todos, que es la clase de error
    que no se ve en ninguna gráfica.
    """
    # Rederivado aquí a mano, sin llamar a las privadas de `_arbol`: si el test
    # usara la misma función que el código, los dos compartirían el error.
    por_fila = [[c for c in t.cells if c.row == f] for f in range(t.n_rows)]
    cabecera = 0
    for fila in por_fila:
        if not fila or not all(c.is_header for c in fila):
            break
        cabecera += 1
    secciones = (1 if cabecera else 0) + (1 if por_fila[cabecera:] else 0)
    esperado = secciones + t.n_rows + len(t.cells)  # <thead>/<tbody> + <tr> + <td>

    assert n_nodos(a_arbol(t)) == esperado


@settings(max_examples=EJEMPLOS)
@given(t=tabla_con_dos_filas_de_cabecera())
def test_mover_la_frontera_de_la_cabecera_cambia_la_estructura(t: CanonicalTable) -> None:
    """**La propiedad que faltaba, y el paso 3 de `/cerrar` que la encontró.**

    Las otras seis propiedades de este fichero son invariantes de TEDS —rango,
    simetría, una tabla contra sí misma vale 1—, y un invariante **no puede ver un
    reetiquetado consistente del árbol**: si `T` cambia igual en los dos lados,
    todos se siguen cumpliendo. Medido: bajo el mutante que mete en `<thead>` sólo
    la primera fila, **24 propiedades pasan en verde**; bajo el que invierte el
    orden de columnas, **las 6 de este fichero pasan**.

    Ésta es distinta porque **perturba un solo lado**: mueve la frontera
    cabecera/cuerpo en la predicha y no en la real. Si `<thead>` es el prefijo
    máximo, quitar la última fila de cabecera **cambia el árbol**; si alguien lo
    reduce a «la primera fila», deja de cambiarlo y esto se cae.

    Hizo falta además **ampliar la estrategia**: `_estrategias.py` fijaba
    `is_header = fila == 0`, así que `n_cabecera >= 2` era inalcanzable. Ahora se
    sortea entre 0 y 2, y llega en **11 de 300** ejemplos.
    """
    cabeceras = [c for c in t.cells if c.is_header]
    assert len({c.row for c in cabeceras}) >= 2, "la estrategia TIENE que dar dos filas de cabecera"

    ultima = max(c.row for c in cabeceras)
    movida = CanonicalTable(
        cells=tuple(
            CanonicalCell(
                c.row, c.col, c.rowspan, c.colspan, c.text, c.is_header and c.row != ultima
            )
            for c in t.cells
        ),
        n_rows=t.n_rows,
        n_cols=t.n_cols,
        page_span=t.page_span,
        caption=t.caption,
        expresses_spans=t.expresses_spans,
        source_format=t.source_format,
    )
    assert teds_struct(movida, t) < 1.0, (
        "mover una fila de <thead> a <tbody> cambia el árbol: si no lo cambia, "
        "el <thead> no es el prefijo máximo que manda ADR-0021"
    )
