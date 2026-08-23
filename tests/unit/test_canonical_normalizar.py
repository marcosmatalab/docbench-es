"""§9.1 · `normalize_cell_text`: una por normalización, y las seis que NO se hacen.

*«Una normalización agresiva es una forma silenciosa de hacer trampas a favor de
un extractor.»* Lo peligroso de este fichero no son los tests de lo que se hace:
son los de lo que **no** se hace. Una normalización que se cuela sin test no
rompe nada — hace que todos los números salgan un poco mejor, en la dirección
tranquilizadora, y nadie se entera.

Por eso hay dos capas: seis tests de ejemplo, uno por normalización aplicada, y
dos propiedades que acorralan a la función entera para que no pueda crecer.

**Presupuesto de ejemplos: 100**, el más alto de la suite y a propósito. Aquí
viven las propiedades que impiden que `normalize_cell_text` crezca —«no toca
ningún glifo visible», «los acentos sobreviven»— y son las que atrapan la trampa
silenciosa de la regla de oro 7. Es también la suite más cara: `test_r1` cuesta
**570 ms**, más que ningún otro test. Si algún día hay que recortar la puerta,
bajarla a 50 ahorra ~285 ms y **es lo último que se toca**, no lo primero.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from docbench_es.core.canonical import NORMALIZACIONES, normalize_cell_text
from docbench_es.core.canonical._normalizar import (
    CATEGORIAS_DE_ESPACIO,
    LIGADURAS,
    _sin_espacios_invisibles,
)

EJEMPLOS = 100


CUALQUIER_TEXTO = st.text(
    alphabet=st.characters(codec="utf-8"),
    max_size=40,
)


def test_n1_compone_los_acentos_que_ya_estan() -> None:
    """Demuestra que una diferencia de CODIFICACIÓN no cuenta como error.

    Un PDF cuyo CMap devuelve `e`+U+0301 dice «é» en la página igual que otro que
    devuelve U+00E9. Sin NFC, el primero fallaría toda comparación de celda por
    un detalle de la fuente, no de la extracción.
    """
    descompuesta = "café"
    assert len(descompuesta) == 5
    assert normalize_cell_text(descompuesta) == "café"
    assert len(normalize_cell_text(descompuesta)) == 4


def test_n2_borra_los_invisibles_y_reconstruye_la_palabra() -> None:
    """Demuestra que el guion BLANDO se borra, y por qué eso no es R5.

    U+00AD es marcado invisible que significa literalmente «aquí se puede partir
    la palabra»: borrarlo devuelve la palabra que la página muestra. Un guion de
    verdad más un salto de línea es otra cosa, es ambiguo, y ése es R5, que no se
    toca. La diferencia es que uno es explícito y el otro hay que adivinarlo.
    """
    assert normalize_cell_text("presu\u00adpuesto") == "presupuesto"  # guion blando
    assert normalize_cell_text("\ufeffTOTAL\u200b") == "TOTAL"  # BOM y ZWSP


def test_n3_los_espacios_raros_se_mapean_pero_nunca_se_borran() -> None:
    """Demuestra la decisión que protege al separador de millares.

    El NBSP se convierte en espacio normal, **no desaparece**. Si desapareciera,
    `1 234` pasaría a `1234` y le estaría regalando el separador de millares al
    extractor que lo perdió, que es exactamente el fallo que R4 existe para poder
    medir. La víctima declarada de N3 es la otra mitad: el NBSP deja de
    distinguirse de un espacio normal.
    """
    # U+2028 y U+2029 son `Zl` y `Zp`, NO `Zs`, y la primera versión de N3 los
    # dejaba fuera. Estas dos líneas documentan el comportamiento, pero **NO
    # sirven de candado**, y merece la pena saber por qué: `str.split()` también
    # los considera espacio, así que parte igual con N3 correcta que con N3
    # mutada y el daño queda ENMASCARADO a nivel de texto. Se intentó usarlas
    # como segundo asesino determinista de `n3_incompleta` y no funcionó.
    # Quien lo caza es `test_n3_cubre_exactamente_lo_que_split_considera_espacio`,
    # que consulta la CATEGORÍA declarada en vez del texto resultante.
    assert normalize_cell_text("a\u2028b") == "a b", "U+2028 LINE SEPARATOR"
    assert normalize_cell_text("a\u2029b") == "a b", "U+2029 PARAGRAPH SEPARATOR"
    assert normalize_cell_text("1\u00a0234,56") == "1 234,56"
    assert normalize_cell_text("1\u202f234") == "1 234"
    assert normalize_cell_text("Nombre\nApellidos") == "Nombre Apellidos"


def test_n4_y_n5_colapsan_y_recortan() -> None:
    """Demuestra que el interlineado del PDF no es contenido de la celda."""
    assert normalize_cell_text("   Base    de   cotización \t ") == "Base de cotización"
    assert normalize_cell_text("") == ""
    assert normalize_cell_text(" \u00a0\t\n ") == "", "sólo espacios: cadena vacía, declarado"


def test_n6_expande_las_siete_ligaduras_y_solo_esas() -> None:
    """Demuestra la ÚNICA normalización que toca un carácter visible.

    Va por tabla enumerada y no por NFKC. La página dice «oficina» y el XML del
    BOE —que en L4 es la verdad de referencia— también: es el CMap de la fuente
    el que devuelve el glifo de ligadura. Expandirla alinea al extractor con la
    verdad; no expandirla penalizaría por un artefacto tipográfico.
    """
    assert normalize_cell_text("oﬁcina") == "oficina"
    assert normalize_cell_text("a\ufb00b") == "affb"  # U+FB00 -> ff
    assert len(LIGADURAS) == 7
    for ligadura, expansion in LIGADURAS.items():
        assert normalize_cell_text(ligadura) == expansion


@settings(max_examples=EJEMPLOS)
@given(s=CUALQUIER_TEXTO)
def test_r1_los_acentos_y_la_enye_sobreviven_siempre(s: str) -> None:
    """Demuestra que NUNCA se quitan diacríticos, sobre entrada arbitraria.

    Es la línea que no se cruza. Quitar acentos sería un regalo directo a la
    familia OCR sobre escaneado, y perder diacríticos es EL fallo específico del
    español que este banco existe para medir. Un test de ejemplo no bastaría:
    property-based para que no haya un rincón del espacio de entradas donde se
    cuele.
    """
    salida = normalize_cell_text(s)
    for letra in "áéíóúüñÁÉÍÓÚÜÑ":
        if letra in unicodedata.normalize("NFC", s):
            assert letra in salida, f"se perdió {letra!r}"


@pytest.mark.parametrize(
    "crudo",
    ["1.234,56", "1,234.56", "1 234,56", "-0,5", "12,00 €", "3.000.000", "2024-2026"],
)
def test_r4_los_numeros_llegan_intactos(crudo: str) -> None:
    """**La decisión más cara del hito, hecha test.**

    `1,234.56` es formato anglosajón donde la página dice `1.234,56`: es un fallo
    real, específico del español y publicable. Si `normalize_cell_text` lo
    reparara, el banco perdería la capacidad de detectar el único fallo que
    justifica que sea un banco EN ESPAÑOL y no una traducción. Eso no es
    normalizar, es borrar la medición.
    """
    assert normalize_cell_text(crudo) == crudo


def test_r6_no_es_nfkc() -> None:
    """Demuestra que la composición es NFC y no NFKC, con el caso que duele.

    NFKC convertiría `m²` en `m2`. En una tabla de superficies eso no es
    normalizar el texto: es cambiar el dato, y encima en la dirección que hace
    que dos celdas distintas parezcan iguales.
    """
    assert normalize_cell_text("m²") == "m²"
    assert normalize_cell_text("½") == "½"
    assert unicodedata.normalize("NFKC", "m²") == "m2", "si esto cambia, revisa el razonamiento"


@settings(max_examples=EJEMPLOS)
@given(s=CUALQUIER_TEXTO)
def test_no_toca_ningun_glifo_visible_salvo_las_ligaduras(s: str) -> None:
    """**La propiedad que impide que esta función crezca.**

    La secuencia de caracteres visibles a la entrada y a la salida es la misma,
    salvo la expansión de las siete ligaduras. Cualquier normalización futura que
    toque un glifo —quitar un acento, cambiar una comilla, reescribir un
    separador decimal— rompe este test aunque su autor no escriba ninguno.

    Es la diferencia entre confiar en que nadie meta una normalización agresiva y
    que el repo no lo permita.
    """
    esperado = "".join(LIGADURAS.get(c, c) for c in _sin_espacios_invisibles(s))
    assert _sin_espacios_invisibles(normalize_cell_text(s)) == esperado


@settings(max_examples=EJEMPLOS)
@given(s=CUALQUIER_TEXTO)
def test_idempotente(s: str) -> None:
    """Demuestra que el número no depende de cuántas capas atravesó el texto.

    Si normalizar dos veces diera algo distinto que normalizar una, la misma
    celda puntuaría distinto según por dónde hubiera pasado, y la métrica
    mediría la forma del pipeline en vez de la del extractor.
    """
    una = normalize_cell_text(s)
    assert normalize_cell_text(una) == una


def test_las_doce_decisiones_estan_documentadas() -> None:
    """Demuestra que «toda normalización se documenta» no es una promesa.

    La regla de oro 7 dice que toda normalización va documentada. Esto la hace
    cumplir: si alguien añade una normalización a `NORMALIZACIONES` y no la
    escribe en `docs/metrics.md`, la puerta se pone roja. Y cubre también las
    RECHAZADAS, que es donde vive el peligro: la que se cuela mañana entra por el
    hueco de una que hoy dice «NO se hace» sin que nadie lo lea.
    """
    metrics = Path(__file__).resolve().parents[2] / "docs" / "metrics.md"
    texto = metrics.read_text(encoding="utf-8")
    assert len(NORMALIZACIONES) == 12, "seis aplicadas y seis rechazadas"
    for n in NORMALIZACIONES:
        assert f"**{n.codigo}**" in texto, f"{n.codigo} sin documentar en docs/metrics.md"
        assert n.nombre in texto, f"{n.codigo} ({n.nombre}) sin su nombre en docs/metrics.md"


def test_n3_cubre_exactamente_lo_que_split_considera_espacio() -> None:
    """Demuestra que N3 no puede BORRAR un carácter creyendo que lo mapea.

    La última línea de `normalize_cell_text` usa `str.split()`, que tiene su
    propia definición de espacio. Si Python considerase espacio un carácter que
    N3 no ha mapeado a U+0020, `split()` lo **borraría** en vez de mapearlo, y
    borrar **une dos tokens que no estaban unidos** — que es exactamente lo que
    N3 promete no hacer y lo que regalaría un separador de millares.

    Pasó de verdad: `Zl` y `Zp` —U+2028 y U+2029— no son `Zs` y estaban fuera de
    la primera versión. Lo encontró el test de propiedad de arriba, no la
    revisión. Esto lo convierte en imposible: recorre **todo el espacio de
    codepoints**, así que no depende de que un sorteo dé con el caso.
    """
    fuera_de_n3 = [
        f"U+{c:04X} {unicodedata.category(chr(c))}"
        for c in range(0x110000)
        if chr(c).isspace() and unicodedata.category(chr(c)) not in CATEGORIAS_DE_ESPACIO
    ]
    assert fuera_de_n3 == [], "split() los borraría; N3 tiene que mapearlos"

    categorias_vistas = {unicodedata.category(chr(c)) for c in range(0x110000) if chr(c).isspace()}
    assert set(CATEGORIAS_DE_ESPACIO) == categorias_vistas, (
        "N3 declara categorías que no contienen ningún espacio: la declaración sobra"
    )
