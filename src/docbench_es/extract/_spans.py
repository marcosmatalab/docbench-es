"""Si un formato puede con `rowspan`, y qué hacer cuando lo declarado no cuadra.

Va aparte de `base.py` porque son dos cosas: allí está **el contrato** —qué miembros
tiene un extractor— y aquí **una regla de medición** que se aplica a lo que devuelve.
Y porque `base.py` se pasó de 300 líneas al juntarlas, que es la regla de `CLAUDE.md`
avisando de lo mismo.

Las dos funciones de aquí tienen la misma postura y conviene decirla junta:
**lo desconocido no se decide por defecto.** Un formato que nadie clasificó levanta, y
una declaración que los datos no confirman sale `SIN_EVIDENCIA` y no `COHERENTE`.
"""

from __future__ import annotations

from typing import Literal

from docbench_es.errors import ContractViolation
from docbench_es.types import FORMATOS_CANONICOS, FORMATOS_CON_SPANS

__all__ = ["VeredictoSpans", "expresa_spans", "veredicto_de_spans"]


def expresa_spans(native_format: str) -> bool:
    """Si ese formato puede con `rowspan`/`colspan`. **Se deriva, no se declara.**

    Markdown y texto plano no pueden por construcción del formato (ADR-0006). Un
    extractor que ponga `expresses_spans=True` devolviendo Markdown no está siendo
    optimista: está pidiendo que se le puntúe un cero en el estrato de celdas
    combinadas como si hubiera competido.

    ## Por qué levanta ante un formato desconocido

    **La primera versión preguntaba `native_format not in FORMATOS_SIN_SPANS`, y eso
    FALLA ABIERTO en la dirección cara.** Medido, no supuesto:

        expresa_spans("markdow")    -> True    (una letra de menos)
        expresa_spans("Markdown")   -> True    (una mayúscula)
        expresa_spans("md")         -> True    (el mismo formato, otro nombre)
        expresa_spans("")           -> True    (la cadena vacía)

    O sea que el valor por defecto de lo desconocido era **conceder spans**, que es
    exactamente el modo de fallo que esta función existe para impedir. Y no era remoto:
    `Extraction.native_format` es `str` a secas, así que nada impide una mayúscula en un
    adaptador de once líneas escrito con prisa.

    Ahora lo desconocido **no se decide**: levanta. Es la misma postura que
    `HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO`, que este repo ya toma para
    `CanonicalTable.source_format` — un formato que nadie declaró es una condición
    detectada, no un valor por defecto.

    **Por qué NO se tipó `native_format` como `Literal`**, que era la otra salida: sería
    imposible por construcción y con eso desaparecería el chequeo en ejecución que el
    repo ya tiene puesto a propósito. `source_format` es `str` **para que**
    `SOURCE_FORMAT_DESCONOCIDO` signifique algo. Tiparlo mataría ese hallazgo y dejaría
    sin cubrir el caso real: un formato que llega de fuera, no de código tipado.
    """
    if native_format in FORMATOS_CON_SPANS:
        return True
    if native_format not in FORMATOS_CANONICOS:
        raise ContractViolation(
            f"formato nativo desconocido: {native_format!r}. Los canónicos son "
            f"{list(FORMATOS_CANONICOS)}. No se decide por defecto si puede con spans, "
            "porque el defecto que había —concederlos— es el error caro"
        )
    return False


VeredictoSpans = Literal["COHERENTE", "CONTRADICCION", "ESCONDIDO", "SIN_EVIDENCIA"]
"""Los cuatro desenlaces de contrastar lo declarado con lo que se ve. **No son dos.**"""


def veredicto_de_spans(
    declarado: bool, native_format: str, vio_celdas_combinadas: bool, hubo_ocasion: bool
) -> VeredictoSpans:
    """La regla del contraste, **escrita antes de que exista la suite que la aplica**.

    ## No es una igualdad, y tampoco es sólo una desigualdad

    La tentación es exigir `declarado == expresa_spans(formato)`. **Está mal**, y en la
    dirección que deja el incentivo al revés: un extractor cuyo parser aplana los
    `rowspan` y lo declara honestamente con `False` **fallaría por honesto**, y le
    saldría más barato declarar `True` y cobrar el cero, que al menos pasa la suite.

    La corrección obvia es la desigualdad —`declarado <= permitido`, más restrictivo
    vale, más permisivo no—, y **también se queda corta**. Este repo ya tenía la regla
    entera en `types._invariantes._spans_declarados`, para `CanonicalTable`, con su
    razón escrita: *«declararse incapaz trayendo celdas combinadas también miente, y de
    esa se aprovecharía quien quisiera esconderse en NO_APLICABLE»*. Declararse por
    debajo del formato es legítimo **sólo si los datos lo confirman**.

    ## Los cuatro desenlaces

    | declarado | el formato | emitió combinadas | hubo ocasión | veredicto |
    |---|---|---|---|---|
    | `True` | **no** permite | — | — | `CONTRADICCION` — pide competir donde no puede |
    | `False` | — | **sí** | — | `ESCONDIDO` — se refugia en `NO_APLICABLE` trayéndolas |
    | `False` | permite | no | **no** | `SIN_EVIDENCIA` — no se sabe |
    | `False` | permite | no | **sí** | `COHERENTE` — las aplana, y está comprobado |
    | resto | | | | `COHERENTE` |

    ## `hubo_ocasion` es el dato que separa al honesto del no medido

    **Sin él, un extractor que de verdad aplana los `rowspan` jamás podría aprobar**: se
    quedaría en `SIN_EVIDENCIA` para siempre por hacer lo que declara. `hubo_ocasion`
    dice si el conjunto de conformidad traía **al menos un documento con celdas
    combinadas en la verdad de referencia**. Con ocasión y sin emitirlas, el `False` está
    confirmado; sin ocasión, no se ha comprobado nada.

    **`SIN_EVIDENCIA` no es un aprobado**, y por eso es un valor propio y no `COHERENTE`:
    no distingue *«su parser las aplana»* de *«no le tocó ninguna»*. Es la tercera
    severidad que la suite de entidad ya tiene —`NO_EJECUTADA`—: un aro por el que no se
    ha pasado no está superado, y contarlo como aprobado sería publicar como observado
    algo que no se observó.

    Y de ahí sale una obligación sobre el conjunto: **se elige, no se toma**. Si no trae
    ni una celda combinada, TODO extractor sale `SIN_EVIDENCIA` y el veredicto no
    discrimina nada — una comprobación cuyo verde no significa lo que parece.

    Levanta si el formato es desconocido, por `expresa_spans`: lo desconocido no se
    decide por defecto ni aquí ni allí.
    """
    if declarado and not expresa_spans(native_format):
        return "CONTRADICCION"
    if not declarado and vio_celdas_combinadas:
        return "ESCONDIDO"
    if not declarado and expresa_spans(native_format) and not hubo_ocasion:
        return "SIN_EVIDENCIA"
    return "COHERENTE"
