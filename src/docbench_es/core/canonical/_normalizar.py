"""§9.1 · `normalize_cell_text`, y la lista de lo que hace y de lo que NO hace.

> *«Una normalización agresiva es una forma silenciosa de hacer trampas a favor
> de un extractor.»* — §9.1 del manual

La regla que decide qué entra y qué no, y de la que sale todo lo demás:

> **Sólo se toca lo invisible o la forma de composición Unicode. Ningún glifo
> visible se altera ni se borra.** Una excepción, enumerada y con test propio: N6.

Lo importante es que **no normalizar también tiene víctima**. Cada decisión de
las doce de abajo beneficia a alguien, se tome en la dirección que se tome, y por
eso las seis rechazadas van declaradas con nombre igual que las seis aplicadas.
Una normalización que no está escrita aquí no existe: `NORMALIZACIONES` es lo que
lee `docs/metrics.md` y lo que comprueba un test de la puerta.

**EL ALCANCE DE ESE REGISTRO, dicho para que no se lea de más.** Aquí está lo que se
le hace al texto **ya extraído**, y es lo mismo para los cinco formatos. **Sacar el
texto del formato de origen NO es normalización: es parseo**, y lo hace cada
conversor — `from_html` con un parser de HTML desde L1, así que un `<b>` desaparece
solo y un `<br>` sale como espacio; `from_markdown` con su tabla `INLINE`, así que
`**x**` sale como `x`. Que este registro no los liste no es un hueco: es que no son
suyos. Lo que sí obliga la regla de oro 7 es que cada conversor enumere lo que
reconoce, y el de Markdown lo hace en `INLINE` **incluido lo que NO reconoce**.

La distinción hizo falta escribirla el día que `from_markdown` se puso a la par de
`from_html` (LIMITS 103): sin ella, «quito el `**`» parece una normalización nueva y
no registrada, cuando es exactamente lo contrario — quitar una inconsistencia entre
dos conversores del mismo repo.

**La decisión más cara del hito es R4: aquí NO se tocan los números** (ADR-0017,
que contradice el docstring de §9.1 y se transcribió al manual en el mismo
commit). Consecuencia que hay que leer entera para que no parezca incoherencia:
un extractor que devuelve `1,234.56` donde la página dice `1.234,56` **queda
penalizado en dos niveles**. En TEDS con contenido (L2), porque la cadena de la
celda es distinta. Y en el verificador `numeric` (L9), donde con su tolerancia
declarada el número puede darse por bueno. No es doble contabilidad: son dos
preguntas distintas —*«¿transcribiste la celda?»* y *«¿el número es correcto?»*—
y responderlas por separado es informativo, porque un extractor puede acertar la
segunda fallando la primera. Lo que sería una sola pregunta mal hecha es
repararlo aquí y publicar las dos como si estuvieran bien.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

CATEGORIAS_DE_ESPACIO = ("Cc", "Zs", "Zl", "Zp")
"""Las cuatro categorías que N3 mapea a U+0020.

`Zl` y `Zp` —U+2028 LINE SEPARATOR y U+2029 PARAGRAPH SEPARATOR— **no son `Zs`**,
y estaban fuera de la primera versión de N3. Las encontró el test de propiedad
`test_no_toca_ningun_glifo_visible_salvo_las_ligaduras`, y el fallo era del tipo
peor de este repo: la declaración decía `Cc` y `Zs`, y el código las borraba de
todas formas porque `str.split()` sí las considera espacio. Declarada una cosa y
hecha otra.

Comprobado ejecutándolo, y hay un test que lo hace cumplir: estas cuatro
categorías son **exactamente** las de todo carácter con `str.isspace()`. Esa
igualdad es lo que hace segura la última línea de `normalize_cell_text`: si
`split()` considerase espacio algo que N3 no ha mapeado, lo BORRARÍA en vez de
mapearlo, y borrar une dos tokens que no estaban unidos.
"""

LIGADURAS = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "st",
    "ﬆ": "st",
}
"""Las siete formas de presentación latinas de U+FB00 a U+FB06, una a una.

Tabla explícita y **nunca** NFKC: comprobado ejecutándolo, NFKC convertiría
además `m²`→`m2`, `½` en dos caracteres y el NBSP en espacio. En una tabla de superficies eso
no es normalizar, es cambiar el dato.
"""


@dataclass(frozen=True)
class Normalizacion:
    """Una decisión sobre el texto de una celda, con su víctima declarada.

    `victima` no es documentación de cortesía: es el campo que obliga a nombrar a
    quién beneficia la decisión antes de tomarla. Una normalización cuyo
    beneficiario no se sabe nombrar es una que no se ha pensado.
    """

    codigo: str
    nombre: str
    que_hace: str
    victima: str
    aplicada: bool


NORMALIZACIONES = (
    Normalizacion(
        "N1",
        "composicion NFC",
        "compone los acentos que YA están; no añade ni quita ninguno",
        "al extractor cuyo PDF trae e+U+0301 en vez de é, por el CMap de la fuente",
        aplicada=True,
    ),
    Normalizacion(
        "N2",
        "borrado de invisibles",
        "borra la categoria Cf: guion blando U+00AD, ZWSP, ZWNJ, ZWJ, U+2060 y BOM",
        "a quien filtra BOM o ZWSP. Si un extractor mete un ZWSP dentro de una cifra, "
        "al unir queda 1234 y le regalo el separador de millares",
        aplicada=True,
    ),
    Normalizacion(
        "N3",
        "espacios a U+0020",
        "mapea Cc, Zs, Zl y Zp a espacio normal: tabulador, salto, NBSP, U+202F, "
        "U+2009, U+2028 y U+2029. Se MAPEAN, nunca se borran",
        "el NBSP como separador de millares español pierde su identidad, y el salto "
        "de linea dentro de celda deja de ser marca semantica. Borrarlos en vez de "
        "mapearlos uniria tokens que no estaban unidos, o sea inventar contenido",
        aplicada=True,
    ),
    Normalizacion(
        "N4",
        "colapso de espacios",
        "una carrera de espacios pasa a uno solo",
        "a quien conserva el interlineado del PDF. El heuristico de texto parte "
        "columnas ANTES de normalizar, porque alli la anchura del hueco ES la columna",
        aplicada=True,
    ),
    Normalizacion(
        "N5",
        "recorte de extremos",
        "quita el espacio del principio y del final",
        "a todos por igual: ningun extractor gana con esto",
        aplicada=True,
    ),
    Normalizacion(
        "N6",
        "expansion de ligaduras",
        "expande las siete ligaduras latinas U+FB00-U+FB06 por tabla explicita",
        "a los parsers con ToUnicode que filtra el glifo de ligadura. Es la UNICA "
        "que toca un caracter visible, y por eso va enumerada y con test propio",
        aplicada=True,
    ),
    Normalizacion(
        "R1",
        "quitar acentos",
        "NO se hace",
        "seria un regalo directo a la familia OCR sobre escaneado. Perder diacriticos "
        "es EL fallo especifico del español que este banco existe para medir",
        aplicada=False,
    ),
    Normalizacion(
        "R2",
        "plegar mayusculas",
        "NO se hace aqui; se hace en core.answer (§9.3, L9), a nivel de respuesta",
        "esconderia el destrozo all-caps del OCR y borraria una señal de cabecera",
        aplicada=False,
    ),
    Normalizacion(
        "R3",
        "comillas tipograficas y guiones a ASCII",
        "NO se hace: son glifos visibles, y U+2212 es categoria Sm",
        "beneficiaria al extractor con ToUnicode roto. El destrozo de comillas y "
        "guiones correlaciona con el manejo de fuentes, que es lo que separa una "
        "extraccion buena de una mala",
        aplicada=False,
    ),
    Normalizacion(
        "R4",
        "coma decimal y separador de millares",
        "NO se hace. La equivalencia numerica es del verificador numeric (§9.3) y de "
        "truth.derived (L4), con su tolerancia declarada",
        "repararia en silencio al extractor que devolvio 1,234.56 en formato "
        "anglosajon, que es un fallo real, especifico del español y publicable",
        aplicada=False,
    ),
    Normalizacion(
        "R5",
        "deshacer la particion de linea",
        "NO se hace: presu-\\npuesto es indistinguible de economico-financiero",
        "al colapsar el salto (N3) queda 'presu- puesto', lo que penaliza al que "
        "CONSERVA el salto frente al que lo une. Asimetria declarada en LIMITS 31",
        aplicada=False,
    ),
    Normalizacion(
        "R6",
        "NFKC",
        "NO se hace: comprobado que convierte m2 y 1/2 y el NBSP",
        "en una tabla de superficies, cambiar m² por m2 es cambiar el dato",
        aplicada=False,
    ),
)

APLICADAS = tuple(n for n in NORMALIZACIONES if n.aplicada)
RECHAZADAS = tuple(n for n in NORMALIZACIONES if not n.aplicada)


def normalize_cell_text(s: str) -> str:
    """El texto de una celda, normalizado con las seis de `APLICADAS` y ninguna más.

    Orden: N1 → N6 → N2 → N3 → N4 → N5. La composición va primero para que la
    tabla de ligaduras y las categorías Unicode miren siempre la misma forma.

    Idempotente por construcción, y hay un test de propiedad que lo afirma: si no
    lo fuera, el mismo texto puntuaría distinto según cuántas veces hubiera pasado
    por aquí, y la métrica dependería del número de capas del pipeline.

    Caso degenerado declarado: la cadena vacía y la de sólo espacios devuelven
    `""`. Eso hace que una celda vacía y una celda con un NBSP sean iguales, que
    es lo que se quiere: la diferencia entre celda vacía y hueco la lleva
    `holes()`, no el texto.
    """
    s = unicodedata.normalize("NFC", s)
    if any(c in LIGADURAS for c in s):
        s = "".join(LIGADURAS.get(c, c) for c in s)
    fuera: list[str] = []
    for c in s:
        categoria = unicodedata.category(c)
        if categoria == "Cf":
            continue  # N2: invisible, se borra
        fuera.append(" " if categoria in CATEGORIAS_DE_ESPACIO else c)  # N3
    # N4 y N5 en una pasada. `split()` SIN argumento a propósito: `split(" ")`
    # conserva las cadenas vacías entre espacios consecutivos y no colapsa nada.
    return " ".join("".join(fuera).split())


def _sin_espacios_invisibles(s: str) -> str:
    """Lo que N2, N3, N4 y N5 no pueden cambiar: la secuencia de glifos visibles.

    Se usa desde los tests de propiedad. Vive aquí y no allí porque define, en
    código, qué significa exactamente «no toca lo visible», y esa definición es
    parte del contrato de `normalize_cell_text`, no del test que lo comprueba.
    """
    compuesta = unicodedata.normalize("NFC", s)
    fuera = ("Cf", *CATEGORIAS_DE_ESPACIO)
    return "".join(c for c in compuesta if unicodedata.category(c) not in fuera)
