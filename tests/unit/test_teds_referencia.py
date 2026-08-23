"""§9.2 · El criterio de aceptación de L2: coincidir a cuatro decimales.

> *«Validación obligatoria: contra la implementación de referencia de PubTabNet
> sobre sus propios casos, en `tests/fixtures/pubtabnet/`. Si no reproduce sus
> números, la implementación está mal. No se valida "a ojo", porque TEDS no tiene
> valores intuibles.»* — §9.2

Los 20 casos son los de `src/sample_gt.json` y `src/sample_pred.json` del repo de
PubTabNet, y los valores los calculó **su** `metric.py` con APTED. Aquí se
compara contra un Zhang-Shasha escrito a mano: dos algoritmos distintos para el
mismo problema, y por eso la coincidencia dice algo.

`tests/fixtures/pubtabnet/` está **congelado**. Si uno de estos tests falla, el
orden de sospecha es: primero el código, segundo el test, **nunca el golden**.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docbench_es.core.teds import teds, teds_struct
from docbench_es.core.teds._arbol import a_html
from docbench_es.types import CanonicalCell, CanonicalTable

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "pubtabnet"
# `Any` no se usa en el proyecto (`disallow_any_explicit`), pero un JSON es
# exactamente eso: forma desconocida hasta que se lee. Se tipa en la frontera,
# una sola vez, en vez de esparcir `type: ignore` por cada acceso.
CASOS: dict[str, dict[str, object]] = json.loads(
    (FIXTURES / "casos.json").read_text(encoding="utf-8")
)


def _nota(caso: dict[str, object], render: str, metrica: str) -> float:
    """La nota congelada, estrechada en la frontera y no en cada uso.

    El tipo del JSON se declaró primero como `dict[str, dict[str, float]]`, que
    era falso: un caso trae además los dos renders en HTML, que son `str`. mypy lo
    cazó al comparar un `str` con un `dict` —`Non-overlapping equality check`— y
    eso es lo que pasa cuando el tipo de frontera se escribe por lo que se usa hoy
    en vez de por lo que el fichero tiene.
    """
    valores = caso[render]
    assert isinstance(valores, dict)
    return float(valores[metrica])


def _render(caso: dict[str, object], clave: str) -> str:
    valor = caso[clave]
    assert isinstance(valor, str)
    return valor


DECIMALES = 4


def _tabla(serializada: object) -> CanonicalTable:
    """Reconstruye la tabla congelada. Una tabla ausente es la tabla VACÍA.

    Ausente significa que el extractor no devolvió ninguna tabla para ese
    documento. Se representa como tabla vacía y no se salta el caso: saltarlo
    dejaría fuera de la medición justo al que peor lo hizo.
    """
    if serializada is None:
        return CanonicalTable((), 0, 0, (1, 1), None, True, "html")
    assert isinstance(serializada, dict)
    celdas = tuple(
        CanonicalCell(int(f), int(c), int(rs), int(cs), str(texto), bool(cab))
        for f, c, rs, cs, texto, cab in serializada["cells"]
    )
    return CanonicalTable(
        cells=celdas,
        n_rows=int(serializada["n_rows"]),
        n_cols=int(serializada["n_cols"]),
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )


def test_el_fixture_congelado_tiene_los_veinte_casos() -> None:
    """Demuestra que la medición se hace sobre lo que dice hacerse.

    Sin esto, un `casos.json` truncado a dos casos dejaría los tests en verde y
    el «coincide con la referencia» estaría medido sobre el 10% de la muestra.
    Un bucle sobre un fichero es tan bueno como el fichero.
    """
    assert len(CASOS) == 20
    assert all("canonico" in c for c in CASOS.values())
    assert (FIXTURES / "PROCEDENCIA.md").exists(), "un fixture sin procedencia no es un golden"


@pytest.mark.parametrize("clave", sorted(CASOS))
def test_teds_coincide_con_la_referencia_a_cuatro_decimales(clave: str) -> None:
    """**El criterio de aceptación de L2.**

    Demuestra que este TEDS es TEDS: reproduce el número de la implementación de
    referencia sobre sus propios casos. Un caso por test y no un bucle, para que
    el que falle diga cuál es sin tener que leer una traza.
    """
    caso = CASOS[clave]
    pred, gold = _tabla(caso["pred"]), _tabla(caso["gold"])

    assert round(teds(pred, gold), DECIMALES) == round(_nota(caso, "canonico", "teds"), DECIMALES)
    assert round(teds_struct(pred, gold), DECIMALES) == round(
        _nota(caso, "canonico", "teds_s"), DECIMALES
    )


@pytest.mark.parametrize("clave", sorted(CASOS))
def test_el_render_canonico_es_el_que_genero_el_golden(clave: str) -> None:
    """**Lo que el criterio de aceptación NO puede ver, y por eso hace falta esto.**

    El golden se generó dando a la referencia el render canónico de estas mismas
    tablas (ADR-0020). O sea que el número congelado es `f_ref(T(pred), T(gold))`
    y el nuestro es `f(T(pred), T(gold))`: **el mapeo `T` aparece en los dos
    lados y se cancela.** El criterio de aceptación valida Zhang-Shasha contra
    APTED y **nada más**; un error en `T` pasa invisible.

    No es teoría. Medido con dos mutantes de `_arbol.py`:

    | Mutante | Qué rompe | Sin este test | Con este test |
    |---|---|---|---|
    | invertir el orden de columnas de cada fila | el HTML de **los 20** | verde | 20 mueren |
    | meter en `<thead>` sólo la primera fila | el HTML de **6** de 20 | verde | 7 mueren |

    El fixture **ya guardaba** `html_canonico_gold` y `html_canonico_pred` desde
    que se creó, y **ningún test los miraba**. Esto los mira.

    **Lo que este test es, dicho sin adornos: un candado de regresión, no una
    validación.** Ata `a_html` a lo que era el día que se generó el golden; no
    demuestra que ese día estuviera bien. Eso último no lo puede dar este fixture
    —ver `LIMITS.md` 52— y por eso el límite existe.
    """
    caso = CASOS[clave]
    assert a_html(_tabla(caso["gold"])) == _render(caso, "html_canonico_gold")
    assert a_html(_tabla(caso["pred"])) == _render(caso, "html_canonico_pred")


def test_el_thead_es_el_prefijo_maximo_de_filas_de_cabecera() -> None:
    """La mitad de ADR-0021 que los 20 casos no alcanzan a probar.

    ADR-0021 punto 2 dice `<thead>` = **prefijo máximo** de filas de cabecera. Con
    una sola fila de cabecera, «prefijo máximo» y «la primera fila» dan lo mismo,
    así que el mutante que las confunde sobrevive a los 20 casos y también a las
    propiedades: `_estrategias.py` fija `is_header = fila == 0`, o sea que
    **ninguna estrategia puede generar `n_cabecera >= 2`**. Este caso a mano es
    el único sitio del repo donde esa rama se ejecuta.
    """
    dos_cabeceras = CanonicalTable(
        cells=(
            CanonicalCell(0, 0, text="grupo", is_header=True),
            CanonicalCell(1, 0, text="unidad", is_header=True),
            CanonicalCell(2, 0, text="dato"),
        ),
        n_rows=3,
        n_cols=1,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    assert a_html(dos_cabeceras) == (
        "<html><body><table>"
        "<thead><tr><td>grupo</td></tr>"
        "<tr><td>unidad</td></tr></thead>"
        "<tbody><tr><td>dato</td></tr></tbody>"
        "</table></body></html>"
    )


def test_los_casos_no_son_todos_unos() -> None:
    """Demuestra que el golden DISCRIMINA, que es lo que casi nunca se comprueba.

    Si los 20 casos valieran 1,0, un `teds` que devolviera siempre 1,0 pasaría el
    criterio de aceptación entero. La muestra tiene que contener fallos de
    verdad, y contenerlos repartidos: aquí van de 0,586 a 1,000.
    """
    valores = sorted(_nota(c, "canonico", "teds") for c in CASOS.values())
    assert min(valores) < 0.7, "sin casos malos, un TEDS constante pasaría"
    assert max(valores) == 1.0, "sin casos perfectos, no se comprueba el extremo bueno"
    assert len({round(v, 4) for v in valores}) == 15, "los valores tienen que estar repartidos"


def test_la_diferencia_con_el_html_crudo_esta_medida_y_no_es_cero() -> None:
    """Demuestra que la decisión de ADR-0020 tiene precio, y cuál.

    El golden se calcula sobre el render canónico y no sobre el HTML crudo de
    PubTabNet, porque la referencia no normaliza nada y no comparte la forma del
    árbol. Eso es una decisión, no una obviedad, y una decisión sin precio medido
    es una nota al pie: **15 de los 20 casos dan un número distinto**.

    Este test se cae el día que alguien «arregle» la diferencia haciendo que el
    golden se calcule sobre el original: entonces L2 mediría la convención en vez
    del algoritmo, y nadie se enteraría porque todo seguiría en verde.
    """
    difieren = [
        k
        for k, c in CASOS.items()
        if round(_nota(c, "canonico", "teds"), 6) != round(_nota(c, "original", "teds"), 6)
    ]
    assert len(difieren) == 15, f"medido en L2: 15 de 20. Ahora {len(difieren)}"


def test_las_celdas_de_una_fila_salen_en_orden_de_columna() -> None:
    """Segundo asesino de `arbol_orden_invertido`, que sólo tenía uno.

    La tabla de asesinos lo delató: el orden de columnas lo cazaba **únicamente**
    el censo de los 20 casos congelados, o sea una sola aserción sosteniendo la
    garantía. Y es la peor de las dependencias posibles, porque ese censo es un
    candado de regresión contra un fixture que salió de esta misma función
    (`LIMITS.md` 52): si el orden hubiera estado mal el día de la generación, el
    censo lo habría congelado mal y nadie lo sabría.

    Esto no depende del fixture. Es una tabla escrita a mano con textos que se
    ordenan solos, y afirma lo que ninguna propiedad de TEDS puede afirmar: que
    el render **no es simétrico** ante permutar las columnas.
    """
    t = CanonicalTable(
        cells=(
            CanonicalCell(0, 0, text="primera"),
            CanonicalCell(0, 1, text="segunda"),
            CanonicalCell(0, 2, text="tercera"),
        ),
        n_rows=1,
        n_cols=3,
        page_span=(1, 1),
        caption=None,
        expresses_spans=True,
        source_format="html",
    )
    html = a_html(t)
    assert html.index("primera") < html.index("segunda") < html.index("tercera"), (
        f"las celdas salen en otro orden que el de columna: {html}"
    )
