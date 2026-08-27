"""El nivel 1: **la aritmética de la tabla, sin corpus y sin bibliotecas.**

Lo que estos tests fijan son las tres decisiones pre-registradas, no que sepa sumar:

* **el emparejado** (`runs/l5/emparejado.yaml`): por orden, y sólo cuando los recuentos
  coinciden. Con N≠M el documento sale `NO_APLICABLE`, **nunca 0,00**;
* **los dos agregados** (`runs/l5/ponderacion.yaml`): primario por documento, secundario
  ponderado por páginas — los mismos TEDS con otros pesos;
* **la cobertura evaluable NO es la de `teds_batch`**. Aquélla se cuenta sobre los pares
  que le llegan, y los documentos con recuento distinto **no llegan**: tomarla diría que
  la cobertura es alta porque lo que no cuadra se quedó fuera de la cuenta.

Y el que cierra el aviso de la tabla del humo: **contar tablas no es calidad**, así que la
columna es de ACUERDO con la referencia y lleva la verdad dentro.
"""

from __future__ import annotations

from dataclasses import replace

from benchcore.types import Cost

from docbench_es.report.nivel1 import cara_a_cara, medir
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


def test_un_documento_que_cuadra_puntua_y_uno_que_no_sale_no_aplicable() -> None:
    """**La regla entera de `emparejado.yaml` en un test.** El segundo documento devuelve
    dos tablas contra una de la verdad: no puntúa, y su discrepancia se cuenta."""
    fila = medir(
        [_ex("D1", PERFECTA), _ex("D2", PERFECTA, OTRA)],
        {"D1": (PERFECTA,), "D2": (PERFECTA,)},
        {"D1": 1, "D2": 1},
    )
    assert fila.metricas.teds == 1.0, "D1 es idéntica a su verdad"
    assert fila.metricas.n_documents == 1, "sólo puntúa D1"
    assert fila.deteccion.documentos == 2
    assert fila.deteccion.con_recuento_igual == 1
    assert fila.deteccion.tablas_de_mas == 1
    assert fila.deteccion.tablas_de_menos == 0
    assert fila.deteccion.acuerdo == 0.5


def test_el_documento_que_no_cuadra_no_cuenta_como_cero() -> None:
    """Decisión B3. Si contara como 0,00, el TEDS de arriba sería 0,5 en vez de 1,0 — y
    diría «la mitad de mal» donde lo que pasa es «no se pudo comparar»."""
    con_fallo = medir(
        [_ex("D1", PERFECTA), _ex("D2", PERFECTA, OTRA)],
        {"D1": (PERFECTA,), "D2": (PERFECTA,)},
        {"D1": 1, "D2": 1},
    )
    solo_bueno = medir([_ex("D1", PERFECTA)], {"D1": (PERFECTA,)}, {"D1": 1})
    assert con_fallo.metricas.teds == solo_bueno.metricas.teds == 1.0


def test_la_cobertura_se_cuenta_sobre_todas_las_tablas_de_la_verdad() -> None:
    """**No sobre los pares que llegan a `teds_batch`.** Aquí la verdad tiene 3 tablas y
    sólo 1 se pudo emparejar: la cobertura es 1/3, no 1/1."""
    fila = medir(
        [_ex("D1", PERFECTA), _ex("D2", PERFECTA)],
        {"D1": (PERFECTA,), "D2": (PERFECTA, OTRA)},
        {"D1": 1, "D2": 1},
    )
    assert fila.deteccion.tablas_de_la_verdad == 3
    assert abs(fila.metricas.evaluable_coverage - 1 / 3) < 1e-9


def test_el_agregado_secundario_pondera_por_paginas() -> None:
    """Los mismos TEDS con otros pesos. Con un documento perfecto de 90 páginas y otro
    malo de 1, el primario y el ponderado **tienen que separarse** — y esa separación es
    un resultado, no un problema."""
    mala = _tabla("z", "z", "z", "z", filas=2)
    fila = medir(
        [_ex("LARGO", PERFECTA), _ex("CORTO", mala)],
        {"LARGO": (PERFECTA,), "CORTO": (PERFECTA,)},
        {"LARGO": 90, "CORTO": 1},
    )
    assert fila.teds_por_pagina is not None
    assert fila.metricas.teds is not None
    assert fila.teds_por_pagina > fila.metricas.teds, "el largo es el perfecto y pesa 90"


def test_un_documento_sin_paginas_conocidas_no_se_cuela_con_peso_cero() -> None:
    """Se salta, y al saltarse sale del numerador **y** del denominador. Meterlo con peso
    0 sería medirlo como si no valiera nada en vez de no medirlo."""
    fila = medir([_ex("D1", PERFECTA)], {"D1": (PERFECTA,)}, {})
    assert fila.teds_por_pagina is None


def test_los_fallos_se_cuentan_por_causa_y_no_se_pierden() -> None:
    """La tasa de fallo por extractor es un resultado publicado. Regla de oro 6."""
    roto = replace(_ex("D3"), failed=True, failure_reason="corrupt_pdf")
    fila = medir([_ex("D1", PERFECTA), roto], {"D1": (PERFECTA,)}, {"D1": 1})
    assert dict(fila.metricas.failures) == {"corrupt_pdf": 1}
    assert fila.n_extracciones == 2


def test_el_regimen_y_el_agregado_salen_declarados() -> None:
    """ADR-0045: la población con tabla es un censo, así que **sin intervalo**, y el
    agregado primario es por documento. Los dos viajan dentro de la métrica."""
    m = medir([_ex("D1", PERFECTA)], {"D1": (PERFECTA,)}, {"D1": 1}).metricas
    assert (m.regimen, m.agregado, m.ci) == ("CENSO", "POR_DOCUMENTO", None)


def test_sin_ninguna_tabla_evaluable_la_nota_es_no_aplicable_y_no_cero() -> None:
    """Un extractor al que no le cuadró ni un documento no saca 0,00: saca `n/a`."""
    fila = medir([_ex("D1", PERFECTA, OTRA)], {"D1": (PERFECTA,)}, {"D1": 1})
    assert fila.metricas.teds is None
    assert fila.metricas.n_documents == 0
    assert fila.metricas.evaluable_coverage == 0.0


def test_un_documento_sin_tablas_en_la_verdad_no_entra_en_la_poblacion() -> None:
    """Los 662 sin tabla no puntúan y no bajan la nota de nadie: su falso positivo es
    otra medida, con otro denominador y otro régimen (ADR-0045)."""
    fila = medir([_ex("D1", PERFECTA), _ex("D9", OTRA)], {"D1": (PERFECTA,), "D9": ()}, {"D1": 1})
    assert fila.deteccion.documentos == 1
    assert fila.metricas.teds == 1.0


def test_medir_es_puro_y_dos_llamadas_dan_lo_mismo() -> None:
    """Sin esto, «el núcleo se puede reejecutar sobre extracciones viejas» sería una
    frase: la tabla tiene que salir igual del mismo diario, hoy y dentro de un año."""
    entrada = ([_ex("D1", PERFECTA)], {"D1": (PERFECTA,)}, {"D1": 1})
    assert medir(*entrada).metricas == medir(*entrada).metricas


# ─────────────────────────────── la cara a cara ──────────────────────────────


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
