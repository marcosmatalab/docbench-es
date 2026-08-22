"""§6 · Los invariantes de cada estructura del modelo de datos.

Separado de `test_types.py`, que cubre la forma del modelo —inmutabilidad y
superficie de import—, porque juntos pasaban de las 300 líneas de `CLAUDE.md`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from docbench_es.types import CanonicalCell, CanonicalTable, Cost, DocRef, Extraction, Glossary


def test_la_clave_de_documento_es_estable_y_distingue_documentos() -> None:
    """Demuestra que **el bootstrap puede agrupar por documento**.

    Las preguntas de un mismo documento están correlacionadas, así que lo que
    se remuestrea son documentos, nunca preguntas. Eso exige una clave estable
    entre instancias y entre corridas: sin ella, el intervalo de confianza sale
    demasiado estrecho y todo número publicado miente a favor del proyecto.
    """
    uno = DocRef("boe", "BOE-A-2026-1234", date(2026, 2, 1), None, "convenio")
    mismo = DocRef("boe", "BOE-A-2026-1234", None, "https://otra.url", "cuentas")
    otro = DocRef("boe", "BOE-A-2026-9999", date(2026, 2, 1), None, "convenio")

    assert uno.key() == mismo.key() == "boe/BOE-A-2026-1234"
    assert uno.key() != otro.key()


@st.composite
def _mismos_trozos_partidos_distinto(draw: st.DrawFn) -> tuple[tuple[str, str], tuple[str, str]]:
    """Dos `(entity, external_id)` DISTINTOS que salen de partir la misma cadena.

    La estrategia está dirigida a propósito, y esto no es un detalle de estilo:
    con `st.text()` libre hypothesis no encuentra la colisión ni en 2.000
    ejemplos, porque exige generar dos pares correlacionados entre sí. El test
    pasaba en verde contra el código roto, que es justo lo que
    `.claude/rules/tests.md` llama un test que sobra. Partiendo una misma cadena
    por dos sitios, **cada** ejemplo cae en la zona donde la inyectividad puede
    romperse, y con los 100 ejemplos por defecto la encuentra de forma
    repetible: `('', '/')` contra `('/', '')`.

    El alfabeto lleva `/` porque es el separador y `%` porque es el carácter de
    escape: si el escapado no fuera inyectivo, `%2F` y `/` colisionarían.

    **Lo que esta estrategia NO puede cazar, y hay que saberlo.** Los dos pares
    salen de partir **la misma cadena**, así que un campo es siempre prefijo del
    otro. Un fallo de inyectividad del ESCAPADO —`esc(a) == esc(c)` con `a ≠ c`—
    exige dos cadenas que no sean prefijo una de otra, y ésas no las genera
    nunca: esto prueba que el SEPARADOR no es ambiguo, no que el escapado sea
    inyectivo. Con `urllib.parse.quote` daba igual, porque el escapado era de
    biblioteca; desde que L1 lo escribió a mano —el contrato de capas prohíbe
    `urllib` en `core`—, es código del proyecto y necesita su propia prueba.
    Comprobado ejecutándolo: contra un escapado que sustituye `/` por `%2F` sin
    escapar antes el `%`, este fichero pasa 7 de 7. Lo cubre el censo exhaustivo
    de `test_types_clave.py`.
    """
    todo = draw(st.text(alphabet="ab/%", min_size=1, max_size=6))
    i = draw(st.integers(min_value=0, max_value=len(todo)))
    j = draw(st.integers(min_value=0, max_value=len(todo)))
    assume(i != j)
    return (todo[:i], todo[i:]), (todo[:j], todo[j:])


@given(par=_mismos_trozos_partidos_distinto())
def test_documentos_distintos_nunca_comparten_clave(
    par: tuple[tuple[str, str], tuple[str, str]],
) -> None:
    """Demuestra que `key()` es **inyectiva** sobre `(entity, external_id)`.

    Property-based y no de ejemplo a propósito: aquí un caso a mano no basta.
    `key()` es la unidad de remuestreo del bootstrap agrupado, y si dos
    documentos distintos colapsan en la misma clave, el remuestreo los trata
    como uno solo, el intervalo sale **más estrecho de lo que toca** y se
    publica un número que afirma más precisión de la que hay. Eso ataca a la vez
    la regla de oro 2 (todo número lleva su intervalo) y la 3 (se remuestrean
    documentos).

    El fallo real que motivó este test: sin escapar, `("boe", "A/B")` y
    `("boe/A", "B")` daban los dos `boe/A/B`. `external_id` es campo libre de
    cualquier adaptador de entidad, así que la separación no puede depender de
    que nadie meta una barra.
    """
    a, b = par
    assume(a != b)
    clave_a = DocRef(a[0], a[1], None, None, "x").key()
    clave_b = DocRef(b[0], b[1], None, None, "x").key()

    assert clave_a != clave_b, f"colisión: {a!r} y {b!r} comparten {clave_a!r}"


@given(entity=st.text(), external_id=st.text())
def test_la_clave_no_depende_de_los_campos_que_no_identifican(
    entity: str, external_id: str
) -> None:
    """Demuestra la otra mitad: la clave es **estable** pese al resto de campos.

    `published_on`, `url` y `kind` cambian entre corridas —una fuente reindexa,
    una URL se mueve— y si la clave dependiera de ellos, el mismo documento
    entraría dos veces en el remuestreo y el agrupamiento se rompería por el
    otro lado.
    """
    uno = DocRef(entity, external_id, date(2026, 2, 1), None, "convenio")
    otro = DocRef(entity, external_id, None, "https://otra.url", "cuentas")

    assert uno.key() == otro.key()


def test_cell_at_respeta_los_spans_y_declara_sus_casos_degenerados() -> None:
    """Demuestra que la posición de una celda combinada no se pierde.

    Una celda con `rowspan=2` ocupa dos filas: si `cell_at` solo mirase su
    esquina, la fila de abajo saldría vacía y TEDS penalizaría al extractor que
    SÍ expresó el span. Sería premiar al que no sabe hacerlo.
    """
    combinada = CanonicalCell(row=0, col=0, rowspan=2, colspan=1, text="Grupo 3")
    suelta = CanonicalCell(row=0, col=1, text="2026")
    tabla = CanonicalTable(
        cells=(combinada, suelta),
        n_rows=2,
        n_cols=2,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )

    assert tabla.cell_at(0, 0) is combinada
    assert tabla.cell_at(1, 0) is combinada, "el rowspan cubre la fila de abajo"
    assert tabla.cell_at(1, 1) is None, "hueco: None, y quien lo reporta es is_wellformed"
    assert tabla.cell_at(99, 99) is None, "fuera de rango: None, no IndexError"

    # Tercer caso degenerado, el que faltaba por declarar: span < 1. La celda no
    # cubre nada y desaparece, indistinguible de un hueco. Se fija aquí para que
    # nadie la "arregle" normalizando a 1 en silencio: eso convertiría un error
    # del conversor en una tabla plausible que TEDS puntuaría como buena.
    degenerada = CanonicalCell(row=0, col=0, rowspan=0, colspan=1, text="span cero")
    rota = CanonicalTable(
        cells=(degenerada,),
        n_rows=1,
        n_cols=1,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )

    assert rota.cell_at(0, 0) is None, "span 0 no cubre nada; lo reporta is_wellformed en L1"


def test_lo_que_no_esta_medido_todavia_no_pasa_en_verde() -> None:
    """Demuestra que el candado de L0 se ha cobrado su deuda, no que se ha quitado.

    L0 dejó `is_wellformed()` levantando `NotImplementedError` **a propósito**:
    devolver `(True, [])` habría hecho pasar en verde a cualquier tabla y el
    criterio de L1 —detectar solapes, huecos y spans fuera de rango al 100%— se
    habría cumplido trivialmente sin escribir una línea.

    En L1 el candado no se borra: **se sustituye por su forma fuerte**, que es la
    misma afirmación pero comprobable. Una tabla rota se rechaza de verdad, y la
    tabla vacía sigue siendo válida porque §12 define TEDS de dos tablas vacías
    como 1 y ese caso degenerado tiene que ser representable.

    `to_prompt_block()` sigue levantando: su hito es L11 y su candado sigue
    puesto. Que las dos mitades convivan aquí es lo que hace visible cuál está
    pagada y cuál no.
    """
    vacia = CanonicalTable((), 0, 0, (1, 1), None, False, "text")
    assert vacia.is_wellformed() == (True, [])

    rota = CanonicalTable(
        cells=(CanonicalCell(0, 0, rowspan=9),),
        n_rows=1,
        n_cols=1,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    ok, problemas = rota.is_wellformed()
    assert ok is False
    assert problemas and problemas[0].startswith("SPAN_FUERA_DE_RANGO")

    glosario = Glossary("boe", 1, date(2026, 8, 21), terms=(), confusables=())
    with pytest.raises(NotImplementedError):
        glosario.to_prompt_block()


def test_el_dinero_entra_al_modelo_en_decimal_y_el_cero_medido_existe() -> None:
    """Demuestra las dos reglas del coste en el punto donde entra al modelo.

    `Decimal` y no `float`, porque el titular del proyecto es un número de
    dinero y sumar cientos de miles de importes minúsculos en coma flotante
    acumula error. Y un extractor local cuesta cero **medido**, que no es lo
    mismo que «no se ha podido medir»: un informe que los confundiera
    publicaría un total más barato que la realidad.
    """
    extraccion = Extraction(
        extractor_id="pdfplumber",
        extractor_version="0.11.4",
        doc_ref=DocRef("boe", "BOE-A-2026-1234", None, None, "convenio"),
        text="",
        tables=(),
        native_format="text",
        pages_processed=3,
        cost=Cost.zero(),
        latency_ms=120,
        warnings=(),
    )

    # Se borra el tipo estático a propósito: lo que se comprueba es el tipo en
    # EJECUCIÓN. Python no hace cumplir las anotaciones, así que `Cost(eur=0.1)`
    # con un `float` corre sin protestar aunque mypy lo rechace, y es justo el
    # caso que la regla «nada de float para dinero» tiene que cazar.
    # El orden importa: comprobado `Decimal` primero, mypy estrecha el tipo y
    # declara inalcanzable la comprobación de `float`, que es justo la que hay
    # que hacer. Al revés, las dos se comprueban de verdad.
    importe: object = extraccion.cost.eur
    assert not isinstance(importe, float)
    assert isinstance(importe, Decimal)
    assert extraccion.cost.measured is True
    assert Cost.unknown().measured is False
    assert extraccion.failed is False
    assert extraccion.failure_reason is None


def test_un_fallo_sin_causa_no_se_puede_construir() -> None:
    """Demuestra la regla de oro 6 en el modelo de datos: **ningún error se traga**.

    `failed=True` sin `failure_reason` era construible, y es un documento caído
    que no puede salir en la tabla de tasa de fallo por causa: desaparece del
    informe, que es justo lo que la regla prohíbe. El sentido contrario también
    levanta, porque una causa con `failed=False` infla a la baja la tasa de fallo
    del extractor.
    """
    base = {
        "extractor_id": "pdfplumber",
        "extractor_version": "0.11.4",
        "doc_ref": DocRef("boe", "BOE-A-2026-1234", None, None, "convenio"),
        "text": "",
        "tables": (),
        "native_format": "text",
        "pages_processed": 0,
        "cost": Cost.zero(),
        "latency_ms": 10,
        "warnings": (),
    }

    with pytest.raises(ValueError, match="failure_reason"):
        Extraction(**base, failed=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="failed=False"):
        Extraction(**base, failed=False, failure_reason="timeout")  # type: ignore[arg-type]

    ok = Extraction(**base, failed=True, failure_reason="timeout")  # type: ignore[arg-type]
    assert ok.failure_reason == "timeout"
