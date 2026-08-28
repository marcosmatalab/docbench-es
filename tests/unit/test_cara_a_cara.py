"""La cara a cara: **las mismas puntuaciones sobre el mismo denominador, y CUÁL es.**

Sale de `test_nivel1.py` porque aquél pasó de 300 líneas, y la costura cae donde tenía que
caer: allí se prueba lo que se mide **de cada extractor por separado**, y aquí lo único
que se puede decir **comparándolos**.

Y lo que estos tests fijan por encima de todo es **la distinción que costó el titular del
hito**: acertar el recuento y puntuar no son lo mismo, así que la intersección del acuerdo
y la intersección de los que puntúan son dos números y no uno. En L5 eran 103 y 82, y se
publicó el segundo con la etiqueta del primero. El fixture `COMBINADA` existe sólo para
que los dos conjuntos puedan diferir: sin una celda combinada en la verdad, ninguna
aserción posible los distingue.
"""

from __future__ import annotations

from benchcore.types import Cost

from docbench_es.report.cara_a_cara import cara_a_cara
from docbench_es.report.nivel1 import medir
from docbench_es.types import CanonicalCell, CanonicalTable, DocRef, Extraction


def _tabla(*textos: str, filas: int = 1) -> CanonicalTable:
    cols = len(textos) // filas
    return CanonicalTable(
        cells=tuple(
            CanonicalCell(row=i // cols, col=i % cols, text=t, is_header=i < cols)
            for i, t in enumerate(textos)
        ),
        n_rows=filas,
        n_cols=cols,
        page_span=(1, 1),
        caption=None,
        expresses_spans=False,
        source_format="dataframe",
    )


def _ex(ident: str, *tablas: CanonicalTable, latencia: int = 10) -> Extraction:
    return Extraction(
        extractor_id="x",
        extractor_version="1",
        doc_ref=DocRef(entity="boe", external_id=ident, published_on=None, url=None, kind="pdf"),
        text="t",
        tables=tablas,
        native_format="dataframe",
        pages_processed=1,
        cost=Cost(wall_ms=latencia),
        latency_ms=latencia,
        warnings=(),
    )


PERFECTA = _tabla("a", "b", "c", "d", filas=2)
OTRA = _tabla("e", "f", "g", "h", filas=2)

COMBINADA = CanonicalTable(
    cells=(
        CanonicalCell(row=0, col=0, text="a", is_header=True, rowspan=2),
        CanonicalCell(row=0, col=1, text="b", is_header=True),
        CanonicalCell(row=1, col=1, text="d", is_header=False),
    ),
    n_rows=2,
    n_cols=2,
    page_span=(1, 1),
    caption=None,
    expresses_spans=True,
    source_format="html",
)
"""La verdad con una celda COMBINADA. Contra un extractor que no expresa spans, su par
sale `NO_APLICABLE` por la regla de oro 4 — y ése es el caso que faltaba en todos los
fixtures de este fichero, y por eso el titular falso de L5 no lo cazó ningún test."""


def test_la_cara_a_cara_puntua_a_todos_sobre_la_interseccion() -> None:
    """**El sesgo de supervivencia, cerrado.** `bueno` acierta el recuento en los dos
    documentos; `malo` sólo en el fácil. Sobre su propio conjunto, `malo` sale PERFECTO;
    sobre la intersección, los dos se comparan sobre el mismo documento.
    """
    mala = _tabla("z", "z", "z", "z", filas=2)
    verdades = {"FACIL": (PERFECTA,), "DIFICIL": (PERFECTA,)}
    paginas = {"FACIL": 1, "DIFICIL": 1}
    bueno = medir([_ex("FACIL", PERFECTA), _ex("DIFICIL", mala)], verdades, paginas)
    malo = medir([_ex("FACIL", PERFECTA), _ex("DIFICIL", PERFECTA, OTRA)], verdades, paginas)

    assert malo.metricas.teds == 1.0, "sobre SU conjunto, el que detecta mal sale perfecto"
    assert bueno.metricas.teds is not None
    assert bueno.metricas.teds < 1.0, "y el que sí lo intenta, peor. Ése es el sesgo"

    cc = cara_a_cara({"bueno": bueno, "malo": malo})
    assert cc.documentos == ("FACIL",), "la intersección es donde los DOS acertaron"
    assert cc.teds["bueno"] == cc.teds["malo"] == 1.0
    assert cc.n == 1
    assert cc.poblacion == 2


def test_acertar_el_recuento_y_puntuar_no_son_lo_mismo() -> None:
    """**El fallo que publicó el titular de L5 con un número falso.**

    `D2` tiene UNA tabla en la verdad y el extractor devuelve UNA: el recuento **coincide**.
    Pero la verdad combina celdas y el extractor no expresa spans, así que el par no es
    evaluable y `teds_batch` devuelve `None`: el documento NO puntúa. Las dos cosas son
    ciertas a la vez, y llamarlas igual convierte un `NO_APLICABLE` en un desacuerdo.
    """
    verdades = {"D1": (PERFECTA,), "D2": (COMBINADA,)}
    paginas = {"D1": 1, "D2": 1}
    fila = medir([_ex("D1", PERFECTA), _ex("D2", PERFECTA)], verdades, paginas)

    assert fila.deteccion.con_recuento_igual == 2, "los dos recuentos coinciden"
    assert set(fila.con_recuento_igual) == {"D1", "D2"}
    assert set(fila.por_documento) == {"D1"}, "pero sólo D1 puntúa"
    assert fila.metricas.n_documents == 1
    assert len(fila.con_recuento_igual) == fila.deteccion.con_recuento_igual, (
        "el recuento y los nombres salen del mismo sitio o son dos fuentes de verdad"
    )


def test_la_cara_a_cara_publica_las_dos_intersecciones_y_no_las_confunde() -> None:
    """**El titular dice `n_acuerdo`; la comparación de TEDS usa `n`. No son el mismo.**

    Medido en L5 la diferencia eran 21 documentos de 103, o sea que publicar uno con la
    etiqueta del otro no es un matiz: es un 24,3% publicado donde había un 30,5%.
    """
    verdades = {"D1": (PERFECTA,), "D2": (COMBINADA,)}
    paginas = {"D1": 1, "D2": 90}
    uno = medir([_ex("D1", PERFECTA), _ex("D2", PERFECTA)], verdades, paginas)
    otro = medir([_ex("D1", PERFECTA), _ex("D2", OTRA)], verdades, paginas)

    cc = cara_a_cara({"uno": uno, "otro": otro}, paginas)
    assert cc.acuerdo_de_recuento == ("D1", "D2"), "los dos aciertan el recuento en los dos"
    assert cc.documentos == ("D1",), "pero sólo D1 lo puntúa todo el mundo"
    assert (cc.n_acuerdo, cc.n, cc.no_aplicables) == (2, 1, 1)
    assert "acuerdo de recuento en 2" in str(cc)


def test_el_desglose_por_banda_cuenta_acuerdo_de_recuento_y_no_puntuaciones() -> None:
    """La columna dice «coinciden los N en el recuento», así que eso es lo que cuenta.

    Contaba la intersección PUNTUADA, y por eso dos de las cuatro celdas publicadas en
    L5 —46 y 12— eran falsas para lo que su propia cabecera declaraba: son 56 y 23.
    """
    verdades = {"D1": (PERFECTA,), "D2": (COMBINADA,)}
    paginas = {"D1": 1, "D2": 90}
    uno = medir([_ex("D1", PERFECTA), _ex("D2", PERFECTA)], verdades, paginas)
    otro = medir([_ex("D1", PERFECTA), _ex("D2", OTRA)], verdades, paginas)
    cc = cara_a_cara({"uno": uno, "otro": otro}, paginas)

    assert cc.por_banda[">50"] == (1, 1), "D2 acuerda en el recuento aunque no puntúe"
    assert cc.por_banda["una página"] == (1, 1)


def test_la_cara_a_cara_publica_los_dos_denominadores_y_su_resta() -> None:
    """**El delta es lo que impide leer la intersección como una corrección del sesgo.**

    `runs/l5/emparejado.yaml` declaró la dirección antes de medir: pasar al denominador
    común baja la nota, y más la de quien menos cobertura tiene. Aquí sale **positivo**
    justo para el que detecta BIEN — su conjunto propio incluye el documento difícil y la
    intersección no—, así que el signo no está fijado por construcción. Por eso se publica
    medido en vez de suponerse.
    """
    mala = _tabla("z", "z", "z", "z", filas=2)
    verdades = {"FACIL": (PERFECTA,), "DIFICIL": (PERFECTA,)}
    paginas = {"FACIL": 1, "DIFICIL": 1}
    bueno = medir([_ex("FACIL", PERFECTA), _ex("DIFICIL", mala)], verdades, paginas)
    malo = medir([_ex("FACIL", PERFECTA), _ex("DIFICIL", PERFECTA, OTRA)], verdades, paginas)

    cc = cara_a_cara({"bueno": bueno, "malo": malo})
    assert cc.suyo == {"bueno": bueno.metricas.teds, "malo": malo.metricas.teds}
    subida = cc.delta("bueno")
    assert subida is not None and subida > 0, "el delta PUEDE salir positivo"
    assert cc.delta("malo") == 0.0
    assert cc.delta("no_lo_hay") is None, "sin los dos lados no hay resta, y no es 0,0"


def test_la_n_de_la_interseccion_se_publica_aunque_sea_cero() -> None:
    """Sin intersección **no hay empate: no hay comparación**, y eso es un resultado sobre
    la dificultad del corpus, no un fallo de la tabla."""
    verdades = {"A": (PERFECTA,), "B": (PERFECTA,)}
    paginas = {"A": 1, "B": 1}
    uno = medir([_ex("A", PERFECTA), _ex("B", PERFECTA, OTRA)], verdades, paginas)
    otro = medir([_ex("A", PERFECTA, OTRA), _ex("B", PERFECTA)], verdades, paginas)
    cc = cara_a_cara({"uno": uno, "otro": otro})
    assert cc.n == 0
    assert cc.teds == {}
    assert "NO HAY COMPARACIÓN" in str(cc)


def test_con_un_solo_extractor_la_interseccion_es_su_propio_conjunto() -> None:
    """Se calcula igual y su `n` lo dice: no aporta nada, y no finge aportarlo."""
    fila = medir([_ex("D1", PERFECTA)], {"D1": (PERFECTA,)}, {"D1": 1})
    cc = cara_a_cara({"solo": fila})
    assert cc.n == 1
    assert cc.teds == {"solo": 1.0}


def test_la_cara_a_cara_sin_extractores_no_revienta() -> None:
    cc = cara_a_cara({})
    assert (cc.n, cc.poblacion, cc.extractores) == (0, 0, ())


def test_el_acuerdo_se_desglosa_por_banda_de_paginas() -> None:
    """**Lo que convierte el titular en diagnóstico.** «Coinciden en el 24%» dice que hay
    un problema; el desglose dice si es de la herramienta o de la longitud del documento.

    Aquí los dos extractores coinciden en el corto y discrepan en el largo: el acuerdo
    sale 100% en la banda de una página y 0% en la de más de 50.
    """
    verdades = {"CORTO": (PERFECTA,), "LARGO": (PERFECTA,)}
    paginas = {"CORTO": 1, "LARGO": 90}
    uno = medir([_ex("CORTO", PERFECTA), _ex("LARGO", PERFECTA)], verdades, paginas)
    otro = medir([_ex("CORTO", PERFECTA), _ex("LARGO", PERFECTA, OTRA)], verdades, paginas)
    cc = cara_a_cara({"uno": uno, "otro": otro}, paginas)
    assert cc.por_banda["una página"] == (1, 1)
    assert cc.por_banda[">50"] == (0, 1)


def test_sin_paginas_el_desglose_sale_vacio_en_vez_de_inventarse_una_banda() -> None:
    """El desglose es información AÑADIDA, no parte del número: sin páginas la cara a cara
    sigue valiendo y `por_banda` no se inventa nada."""
    fila = medir([_ex("D1", PERFECTA)], {"D1": (PERFECTA,)}, {"D1": 1})
    assert cara_a_cara({"solo": fila}).por_banda == {}
