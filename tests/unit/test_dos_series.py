"""La regla de decisión del techo, **y la resta que nadie había hecho**.

## El hallazgo, que estaba en una columna publicada cuatro días

`RESULTS.md` publicó dos series de 40 el 24 ago 2026 y tituló *«el protocolo reproduce a
10 ms»*. Los 10 ms son de la **mediana**. Los dos p90 de esa misma tabla —**6262 y
6327**— nunca se restaron: son **65 ms**, y **el techo se compara contra el p90**.

> Una discusión de **31 ms** de margen sobre un estimador cuya única diferencia observada
> entre series es de **65** no es una medición: es una moneda al aire.

## Qué se prueba aquí, y son dos cosas de la misma familia

1. **`veredicto()`, en las tres direcciones** (ADR-0048): las dos por encima rompen el
   techo; **una sola por encima NO es verde y NO es rojo**, es el código 3; ninguna es
   verde. La dirección del medio es la que este ADR añade, así que es la que hay que ver
   fallar antes de creérsela.
2. **R10**, la regla que ata cada resta publicada a la tabla de la que sale, con su
   control negativo y con su aviso de alcance cero.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

import regla_reproducibilidad as r10  # noqa: E402
from serie_puerta import NO_CONCLUYENTE, ROTO, Serie, comparacion, veredicto  # noqa: E402

TECHO = 8200


def _serie(*tiempos: int) -> Serie:
    """Una serie con los tiempos que se le den. Las cargas y las medianas por tanda no
    entran en ninguna decisión, así que se rellenan con lo mínimo que las hace válidas."""
    return Serie(tiempos, (1.0,) * len(tiempos), (float(min(tiempos)),), 0)


def _cuarenta(p90: int) -> Serie:
    """Cuarenta tiempos cuyo **37.º ordenado** es exactamente `p90`.

    Se construye la serie desde la convención, no al revés: si algún día alguien cambia
    `int(0,90·n)` por otra cosa, este ayudante deja de producir el p90 que promete y los
    tres tests de la decisión se caen a la vez. Es deliberado.
    """
    return _serie(*([p90 - 300] * 36 + [p90] + [p90 + 400] * 3))


def test_el_p90_sigue_siendo_el_37_de_40() -> None:
    """**La convención de ADR-0022, clavada.** Es conservadora —el percentil empírico
    92,5, un rango por encima del p90 por rango— y cambiarla haría incomparables L0 a L7.
    Un cambio silencioso aquí movería toda la serie histórica sin tocar ni un número."""
    serie = _serie(*range(1, 41))
    assert serie.p90 == 37, "ordenadas[int(0,90·40)] es el 37.º valor, no el 36.º"
    assert _cuarenta(8231).p90 == 8231


def test_las_dos_series_por_encima_del_techo_si_lo_rompen() -> None:
    """Cuando las dos miden por encima **no hay ambigüedad que declarar**: es rojo."""
    codigo, dictamen = veredicto((_cuarenta(8300), _cuarenta(8260)), TECHO)

    assert codigo == ROTO
    assert "8300" in dictamen and "8260" in dictamen, "los dos p90 van en el dictamen"
    assert "--durations" in dictamen, "y ANTES de las tres concesiones va el paso 1"


def test_una_sola_por_encima_no_es_verde_y_tampoco_es_rojo() -> None:
    """**El control negativo de la regla de decisión, y la razón de existir de ADR-0048.**

    Éste es exactamente el caso de hoy: p90 8231 contra techo 8200 en una serie, y la
    diferencia observada entre dos series del propio instrumento es 65. Devolver 0
    —«dentro»— o 1 —«roto»— sería contestar con una moneda al aire una pregunta que el
    instrumento sabe que no ha resuelto. Por eso hay un tercer código.
    """
    codigo, dictamen = veredicto((_cuarenta(8231), _cuarenta(8150)), TECHO)

    assert codigo == NO_CONCLUYENTE and codigo not in (0, ROTO)
    assert "NO CONCLUYENTE" in dictamen
    assert "1 de 2" in dictamen, "cuántas pasan, no sólo que discrepan"
    assert "81 ms" in dictamen, "la diferencia entre las series, restada: 8231-8150"
    assert "31 ms" in dictamen, "y el margen más pequeño contra el techo"
    assert "No se sube el techo" in dictamen


def test_ninguna_por_encima_es_verde() -> None:
    assert veredicto((_cuarenta(8000), _cuarenta(8100)), TECHO) == (0, "OK")


def test_una_sola_serie_diagnostica_pero_no_decide() -> None:
    """`--series 1` sigue siendo legal —para diagnosticar— y **lo dice en la salida**.

    Un instrumento que imprimiera la misma cara con n=1 y con n=2 mentiría por omisión:
    una serie no mide reproducibilidad de nada.
    """
    assert "no decide el techo" in comparacion((_cuarenta(8000),))

    codigo, dictamen = veredicto((_cuarenta(8231),), TECHO)
    assert codigo == ROTO, "una serie por encima sigue siendo un aviso"
    assert "NO decide el techo" in dictamen and "hacen falta dos" in dictamen


def test_la_comparacion_publica_el_par_y_nunca_una_tasa() -> None:
    """La disciplina de la sección que destapó esto, aplicada al instrumento: **con n=2
    no se publica una tasa, se publica el par.** «La reproducibilidad del p90 es 65 ms»
    es una afirmación sobre la próxima serie que nadie ha medido."""
    texto = comparacion((_cuarenta(6262), _cuarenta(6327)))

    assert "6262" in texto and "6327" in texto, "las dos, enteras"
    assert "65 ms en el p90" in texto, "y su resta hecha"
    assert "no se publica una tasa" in texto
    assert "Esto NO dice" in texto


def _repo(tmp_path: Path, tabla: str, prosa: str) -> None:
    (tmp_path / "RESULTS.md").write_text(tabla, encoding="utf-8")
    (tmp_path / "copia.md").write_text(prosa, encoding="utf-8")
    r10.RAIZ = tmp_path
    r10.CON_EL_PAR = ("RESULTS.md", "copia.md")
    r10._las_fuentes.cache_clear()


ETIQUETA = "24 ago 2026"
TABLA = (
    f"| {ETIQUETA} | serie A | serie B | diferencia |\n"
    "|---|---|---|---|\n"
    "| **mediana** | **6198** | **6208** | 10 |\n"
    "| p90 | 6262 | 6327 | 65 |\n"
    "\ntexto que no es tabla\n"
)


def test_una_resta_entre_series_que_no_sale_de_la_tabla_se_caza(tmp_path: Path) -> None:
    """**El control negativo de R10**, en las dos direcciones y sobre un repo de juguete.

    Una comprobación que nadie ha visto en rojo no es una comprobación. Y el caso malo no
    es inventado: es el número que se publicaría si alguien sincronizara una serie y
    dejara la resta detrás, que es la clase que `derivadas.py` existe para cazar.
    """
    original = r10.RAIZ, r10.CON_EL_PAR
    try:
        _repo(
            tmp_path,
            TABLA,
            f"las series del {ETIQUETA} difirieron **10 ms** en la mediana y **65 ms** en el p90",
        )
        assert r10.diferencias_entre_series("", "RESULTS.md") == [], "con la buena, calla"

        _repo(
            tmp_path,
            TABLA,
            f"las series del {ETIQUETA} difirieron **10 ms** en la mediana y **12 ms** en el p90",
        )
        rotas = r10.diferencias_entre_series("", "RESULTS.md")
        assert len(rotas) == 1 and (rotas[0].publicado, rotas[0].calculado) == ("12", "65")
        assert ETIQUETA in rotas[0].que, "la rota nombra la tabla de la que sale la resta"
        assert rotas[0].documento == "copia.md" and rotas[0].linea == 1
    finally:
        r10.RAIZ, r10.CON_EL_PAR = original
        r10._las_fuentes.cache_clear()


def test_r10_caza_tambien_la_copia_de_la_tabla_y_su_columna(tmp_path: Path) -> None:
    """La frase no es la única forma de divergir: **la tabla se copia entera** en el ADR
    que decide con ella. Una fila movida en la copia es la sexta copia del error del
    estimador otra vez, y el sitio da igual."""
    original = r10.RAIZ, r10.CON_EL_PAR
    try:
        frase = f"\nlas series del {ETIQUETA} difirieron 10 ms en la mediana y 65 ms en el p90\n"
        movida = TABLA.replace("| p90 | 6262 | 6327 | 65 |", "| p90 | 6262 | 6999 | 65 |")
        _repo(tmp_path, TABLA, movida + frase)
        rotas = r10.diferencias_entre_series("", "RESULTS.md")
        assert len(rotas) == 1 and rotas[0].que == f"copia de la fila `p90` de «{ETIQUETA}»"
        assert (rotas[0].publicado, rotas[0].calculado) == ("(6262, 6999)", "(6262, 6327)")

        # Y la otra mitad: la fila bien copiada con SU columna `diferencia` detrás. Es la
        # forma exacta del límite 55 —el dígito se sincroniza y la resta se queda vieja—
        # y una regla que sólo mirara las filas la dejaría pasar.
        vieja = TABLA.replace("| p90 | 6262 | 6327 | 65 |", "| p90 | 6262 | 6327 | 99 |")
        _repo(tmp_path, TABLA, vieja + frase)
        rotas = r10.diferencias_entre_series("", "RESULTS.md")
        assert len(rotas) == 1 and rotas[0].que == f"la columna `diferencia` de p90 en «{ETIQUETA}»"
        assert (rotas[0].publicado, rotas[0].calculado) == ("99", "65")
    finally:
        r10.RAIZ, r10.CON_EL_PAR = original
        r10._las_fuentes.cache_clear()


def test_r10_avisa_cuando_ya_nadie_escribe_la_frase(tmp_path: Path) -> None:
    """**Alcance cero se lee igual que verde**, y ése es el modo de fallo por defecto de
    toda regla de patrones: el día que la frase canónica se reescriba, R10 dejaría de
    proteger nada y su silencio pasaría por conformidad. Mismo aro que R6."""
    original = r10.RAIZ, r10.CON_EL_PAR
    try:
        _repo(tmp_path, TABLA, "aquí ya nadie escribe la resta de las dos series")
        rotas = r10.diferencias_entre_series("", "RESULTS.md")

        assert len(rotas) == 1 and rotas[0].publicado == "0 copias vistas", rotas
    finally:
        r10.RAIZ, r10.CON_EL_PAR = original
        r10._las_fuentes.cache_clear()


def test_r10_caza_una_frase_que_cita_una_tabla_que_no_existe(tmp_path: Path) -> None:
    """**La dirección que aparece cuando las tablas se multiplican**, y desde ADR-0048 se
    multiplican solas: un par por cierre. Una frase que nombra un par inexistente —porque
    la tabla se renombró, se movió a otro documento o nunca se llegó a publicar— es una
    resta sin fuente, que es exactamente lo que R10 existe para impedir."""
    original = r10.RAIZ, r10.CON_EL_PAR
    try:
        _repo(
            tmp_path,
            TABLA,
            "las series del 31 dic 2026 difirieron 1 ms en la mediana y 2 ms en el p90",
        )
        rotas = r10.diferencias_entre_series("", "RESULTS.md")

        assert len(rotas) == 1, rotas
        assert rotas[0].publicado == "31 dic 2026" and ETIQUETA in rotas[0].calculado
    finally:
        r10.RAIZ, r10.CON_EL_PAR = original
        r10._las_fuentes.cache_clear()


def test_r10_corre_una_sola_vez_y_no_por_documento() -> None:
    """Si corriera por documento, un mismo desajuste saldría nueve veces y el recuento
    de «derivadas rotas» diría nueve donde hay una."""
    assert r10.diferencias_entre_series("", "LIMITS.md") == []
    assert r10.diferencias_entre_series("", "ESTADO.md") == []


def test_las_tablas_de_la_fuente_siguen_donde_r10_las_busca() -> None:
    """**El aro de arriba, sobre el repo de verdad y no sobre uno de juguete.** R10 se
    apoya en cabeceras de markdown de `RESULTS.md`; si esas secciones se reescriben, la
    regla se queda sin fuente y hay que verlo aquí y no en un rojo raro."""
    fuentes = r10._las_fuentes()

    assert ETIQUETA in fuentes, sorted(fuentes)
    assert all(f for f in fuentes), "una tabla sin etiqueta no se puede atar a su frase"
    par = fuentes[ETIQUETA]
    assert set(par) == {"mediana", "p90"}, par
    assert par["p90"][1] - par["p90"][0] == 65, "las dos series publicadas, restadas"
    assert par["mediana"][1] - par["mediana"][0] == 10
