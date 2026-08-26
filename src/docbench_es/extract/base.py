"""§7.2 · El contrato que cumple todo extractor, y las tres cosas que declara de sí.

Un **extractor** responde a *«qué hay en este PDF»*. El motor no sabe nada de
`pdfplumber` ni de `docling`: sabe de `Extractor`. Y este repo **no escribe ninguno**
—regla de oro 1, el juez no puede ser concursante—, así que todos los que entren serán
envoltorios finos sobre bibliotecas ajenas. Medido en L5: **de 2 a 11 líneas útiles por
adaptador**.

Eso cambia lo que este contrato tiene que hacer. No está aquí para organizar código
propio: está aquí para que **ocho bibliotecas que no se parecen en nada compitan bajo
las mismas reglas**, y para que las reglas se puedan comprobar en vez de suponer.

## El contrato, en tres frases

1. **`extract` nunca lanza.** Un fallo viaja dentro de `Extraction`, con
   `failed=True` y una `failure_reason` del **enum cerrado** de §6.9. Un extractor que
   lanza se lleva por delante la campaña entera y, de paso, **borra del informe su
   propia tasa de fallo** — que es un resultado publicado, no un detalle. Regla de oro 6.
2. **Las tablas que devuelve cumplen los invariantes de `CanonicalTable`.** Sin solapes,
   sin huecos, sin spans fuera de rango. Lo comprueba `core.canonical`, no la buena fe.
3. **`cost_of` es pura.** Recibe una `Extraction` y devuelve su `Cost`. Ni red, ni
   reloj, ni estado: dos llamadas con la misma extracción dan el mismo coste, o el coste
   por éxito publicado no se puede reproducir.

## Las tres declaraciones, y por qué NINGUNA es decorativa

Cada una gobierna una decisión del motor que, sin ella, se tomaría a ojo.

| declaración | qué gobierna |
|---|---|
| `expresses_spans` | **Si su TEDS sale `NO_APLICABLE` en vez de cero.** Regla de oro 4 |
| `runs_locally` | **Si la campaña arranca** cuando la fuente prohíbe el egress. Regla de oro 5 |
| `kind` | La familia bajo la que se agrupa en la tabla, y con quién se le compara |

**`expresses_spans` es la que más daño hace si miente**, y en la dirección que no se ve.
Markdown y texto plano **no pueden** expresar `rowspan` por construcción del formato
(ADR-0006, y la lista está en `types.FORMATOS_SIN_SPANS`). Un extractor que devuelve
Markdown y declara `expresses_spans=True` cobraría un cero en el estrato de celdas
combinadas —que es el que se sobremuestrea y el que se declara titular— **como si
hubiera competido y perdido**, cuando lo que pasó es que el formato no llegaba. Eso no
es un extractor malo: es una comparación amañada sin querer, que es la peor clase.

Por eso **no se elige**: `.claude/rules/extractores.md` lo dice sin margen —*«lo fija el
conversor canónico según el formato de origen, no el extractor; un extractor no puede
declararse capaz de algo que su formato no permite»*—. `extract._spans.expresa_spans()`
lo deriva, y la conformidad contrasta contra el `native_format` que el extractor devuelve
**de verdad**, no contra el que dice que devuelve.

**Y el contraste NO es una igualdad**, que es la trampa fácil. La regla, con sus cuatro
desenlaces, está escrita en `veredicto_de_spans` **antes de que exista la suite que la
aplica**, para que sea una decisión y no un cambio de criterio a toro pasado. En una
línea: declararse por debajo del formato es legítimo, pero **sólo si los datos lo
confirman**; y no haber visto ni una celda combinada no confirma nada.

**`runs_locally` sí se cree**, y está declarado que sí: `core.policy` lo dice en su
propio docstring. La puerta de egress recibe descriptores, no extractores, porque el
núcleo no puede importar `extract`. Que la declaración sea cierta lo mira la suite de
conformidad; que se respete, la puerta. Un extractor que mintiera pasaría la puerta, y
**eso es un límite del contrato, no un fallo de la puerta**.

## Por qué hay un `cumple_la_forma` además de `@runtime_checkable`

**Porque el decorador no sirve para el caso que importa.** Comprobado en el intérprete:

    isinstance(instancia, Extractor)  ->  True/False, y sí mira los atributos de dato
    issubclass(clase, Extractor)      ->  TypeError: Protocols with non-method members
                                          don't support issubclass()

Y el registro **no tiene instancia**: devuelve la clase precisamente para decidir sin
construir nada, porque construir un extractor de document-AI carga modelos. Así que el
único chequeo que el decorador habilita exige justo lo que el diseño evita.

`@runtime_checkable` se queda —`isinstance` sirve donde sí hay instancia— y al lado va
`cumple_la_forma`, que hace sobre **la clase** lo que `issubclass` habría hecho. Y
**publica su denominador**: cuántos miembros miró, no sólo si pasó. Un guardián que dice
«verde» sin decir sobre cuántas cosas es indistinguible de uno que no mira ninguna.

## Lo que este módulo NO hace

**No comprueba nada.** Sólo describe. Quien comprueba es `extract.conformance`, y
correrlo es obligatorio por extractor: uno que no ha pasado por ahí no es un extractor
que cumple, es uno que todavía no se ha mirado. Mismo trato que `entity.conformance`.

Y **no descubre nada**: el registro llega con el primer extractor real, en su fichero,
para no escribir un mecanismo de carga antes de tener algo que cargar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal, Protocol, runtime_checkable

from docbench_es.core.policy import ExtractorDeclarado
from docbench_es.extract._spans import VeredictoSpans, expresa_spans, veredicto_de_spans

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from benchcore.types import Cost, ProbeResult

    from docbench_es.types import Extraction, RawDoc

__all__ = [
    "Extractor",
    "FamiliaExtractor",
    "Forma",
    "VeredictoSpans",
    "cumple_la_forma",
    "descriptor",
    "expresa_spans",
    "veredicto_de_spans",
]

FamiliaExtractor = Literal["parser", "ocr", "vlm", "hibrido"]
"""Las cuatro de §7.2. Ojo: **no son las cinco familias de §16.**

§16 agrupa por *tecnología del banco* —parser de texto, extractor de tablas,
document-AI, TEI/científico, OCR— para decir qué cubre la tabla de resultados. Esto
agrupa por *cómo se ejecuta*, que es lo que el motor necesita para tratarlos distinto:
un `vlm` necesita presupuesto y clave, un `parser` no. `camelot` y `pdfplumber` son
familias distintas en §16 y los dos son `parser` aquí.

Se dice porque son dos taxonomías con nombres parecidos sobre los mismos ocho objetos,
y confundirlas haría que la tabla de cobertura de familias contara mal.
"""


@runtime_checkable
class Extractor(Protocol):
    """Los tres métodos de §7.2 y las seis declaraciones que los acompañan.

    **Las declaraciones son atributos de CLASE, no de instancia**, y no es un detalle
    de estilo: el registro devuelve la **clase** para poder decidir sin construir nada
    —`probe()` cuesta, construir un extractor de document-AI carga modelos—. Un
    extractor que asigne `benchcore_api` en `__init__` no llega a cargarse: el registro
    no ve versión y lo rechaza. Es la misma regla que ya rige para `EntityAdapter`, y
    allí está medida en §7.1.
    """

    id: str
    version: str
    kind: FamiliaExtractor
    runs_locally: bool
    expresses_spans: bool
    benchcore_api: str

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        """Lo que hay en el documento. **Nunca lanza**: un fallo va en `Extraction`.

        `page_range` es medio abierto y en base 1, como el resto del proyecto. `None`
        es el documento entero, que es el caso de la campaña; el rango existe para el
        muestreo por páginas de los documentos largos.
        """
        ...

    def cost_of(self, ex: Extraction) -> Cost:
        """El coste de esa extracción. **Pura**: mismo argumento, mismo resultado."""
        ...

    def probe(self) -> ProbeResult:
        """¿Está instalado? ¿Alcanzable? ¿Qué versión? **Sin procesar nada.**

        Es lo que permite que una campaña se niegue a arrancar ANTES de gastar horas,
        en vez de descubrir a la mitad que a un extractor le falta un binario. Y es la
        razón de que no pueda extraer: si `probe` procesara un documento de prueba,
        arrancar la campaña costaría lo que cuesta el extractor más caro.
        """
        ...


DECLARACIONES: Final = (
    "id",
    "version",
    "kind",
    "runs_locally",
    "expresses_spans",
    "benchcore_api",
)
"""Los seis atributos de §7.2. Enumerados para poder decir **cuál** falta."""

METODOS: Final = ("extract", "cost_of", "probe")
"""Los tres métodos de §7.2."""


@dataclass(frozen=True)
class Forma:
    """El resultado de mirar la forma de una clase, **con su denominador**."""

    faltan: tuple[str, ...]
    comprobados: tuple[str, ...]

    @property
    def cumple(self) -> bool:
        return not self.faltan

    def __str__(self) -> str:
        veredicto = "cumple la forma" if self.cumple else f"le falta {', '.join(self.faltan)}"
        return (
            f"{veredicto} · {len(self.comprobados)} miembros comprobados "
            f"({len(DECLARACIONES)} declaraciones + {len(METODOS)} métodos)"
        )


def cumple_la_forma(cls: type) -> Forma:
    """Lo que `issubclass` habría hecho, **sobre la clase y sin construir nada**.

    Mira que las seis declaraciones estén y que los tres métodos sean invocables. Es
    deliberadamente barato: no ejecuta el extractor, no llama a `probe` y no toca disco.
    Lo que sí dice es que un extractor que asigna `benchcore_api` en `__init__` **no
    pasa** — y ésa es justamente la regla que hace posible descubrir sin construir.

    **Lo que NO mira, y hay que decirlo**: los tipos. `kind = "parseador"` pasaría por
    aquí. Eso lo caza `mypy` en quien escribe el extractor, y la conducta la caza
    `extract.conformance` ejecutándolo contra documentos. Aquí sólo está la forma.
    """
    faltan = [n for n in DECLARACIONES if not hasattr(cls, n)]
    faltan += [n for n in METODOS if not callable(getattr(cls, n, None))]
    return Forma(tuple(faltan), (*DECLARACIONES, *METODOS))


def descriptor(extractor: Extractor) -> ExtractorDeclarado:
    """El puente al guardián de egress de `core.policy`, en un solo sitio.

    `core` no puede importar `extract` —el núcleo es puro y lo fija `.importlinter`—,
    así que la puerta recibe `ExtractorDeclarado`, que son dos campos. Convertir aquí y
    no en cada llamador evita la copia que se queda vieja: el día que la puerta necesite
    un tercer campo, se cambia esta función y no seis sitios.
    """
    return ExtractorDeclarado(id=extractor.id, runs_locally=extractor.runs_locally)
