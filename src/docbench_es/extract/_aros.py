"""Los aros por los que pasa un extractor, uno por función. Los produce `conformance`.

Van aparte de `conformance.py` por lo mismo que `entity/_comprobaciones.py` va aparte de
`entity/conformance.py`: allí está **el orquestador y su informe**, y aquí **qué se
comprueba**. Juntos pasarían de 300 líneas y nadie encontraría nada.

Cada función devuelve `Hallazgo | None`: `None` es que ese aro se pasó. Ninguna lanza —
un aro que revienta se lleva por delante los que venían detrás, y quien está escribiendo
un extractor quiere ver **todo** lo que le falta de una vez.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docbench_es.extract.base import cumple_la_forma
from docbench_es.types import FORMATOS_CANONICOS, Hallazgo

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from docbench_es.types import Extraction, RawDoc

__all__ = [
    "aro_cost_of_es_pura",
    "aro_extract_no_lanza",
    "aro_forma",
    "aro_formato_canonico",
    "aro_la_extraccion_se_identifica",
    "aro_probe_no_procesa",
    "aro_tablas_bien_formadas",
    "formato_utilizable_desde",
    "spans_emitidos",
]


def aro_forma(extractor: object) -> Hallazgo | None:
    """Los nueve miembros de §7.2, **sobre la clase**. Sin esto el resto no se intenta."""
    forma = cumple_la_forma(type(extractor))
    if forma.cumple:
        return None
    return Hallazgo("forma", "FALLA", f"no cumple `Extractor`: {forma}")


def aro_probe_no_procesa(extractor: object) -> Hallazgo | None:
    """`probe()` contesta sin tocar un documento. **Y sin lanzar.**

    Es lo que permite que una campaña se niegue a arrancar antes de gastar horas. Un
    `probe` que lanza convierte «no está instalado» en una traza, y el motor no puede
    distinguirlo de un fallo de verdad.

    **Lo que este aro NO comprueba**: que de verdad no procese nada. Eso exigiría
    instrumentar el extractor o cronometrarlo, y un umbral de tiempo sería una medida de
    la máquina. Se comprueba que contesta; que no procese lo sostiene el contrato.
    """
    probe = getattr(extractor, "probe", None)
    if not callable(probe):
        return Hallazgo("probe", "FALLA", "`probe` no es invocable")
    try:
        resultado = probe()
    except Exception as e:
        return Hallazgo("probe", "FALLA", f"`probe()` lanzó {type(e).__name__}: {e}")
    if resultado is None:
        return Hallazgo("probe", "FALLA", "`probe()` devolvió None en vez de un ProbeResult")
    return None


def aro_extract_no_lanza(extractor: object, hostil: RawDoc) -> Hallazgo | None:
    """**El aro que más veces se va a caer**, y el que sostiene la tasa de fallo.

    Se le da un documento deliberadamente roto y se exige `Extraction(failed=True,
    failure_reason=<del enum>)`. Un extractor que lanza aquí se lleva por delante la
    campaña entera y **borra del informe su propia tasa de fallo**, que es un resultado
    publicado y no un detalle de implementación. Regla de oro 6.

    Un `failed=True` sin `failure_reason` no llega a construirse —`Extraction` lo ata en
    `__post_init__`—, así que aquí basta con exigir que no lance y que se declare fallida.
    """
    extract = getattr(extractor, "extract", None)
    if not callable(extract):
        return Hallazgo("extract_no_lanza", "FALLA", "`extract` no es invocable")
    try:
        ex = extract(hostil)
    except Exception as e:
        return Hallazgo(
            "extract_no_lanza",
            "FALLA",
            f"lanzó {type(e).__name__} ante un PDF corrupto en vez de devolver "
            f"Extraction(failed=True, failure_reason=...): {e}",
        )
    if not getattr(ex, "failed", False):
        return Hallazgo(
            "extract_no_lanza",
            "AVISO",
            "no lanzó, pero tampoco marcó `failed=True` ante un PDF corrupto: o lo "
            "procesó de verdad, o se tragó el error",
        )
    return None


def aro_la_extraccion_se_identifica(extractor: object, ex: Extraction) -> Hallazgo | None:
    """La `Extraction` dice de quién es y sobre qué. Sin eso no se puede agregar nada."""
    esperado = (getattr(extractor, "id", None), getattr(extractor, "version", None))
    visto = (ex.extractor_id, ex.extractor_version)
    if visto != esperado:
        return Hallazgo(
            "identificacion",
            "FALLA",
            f"la extracción dice ser de {visto} y el extractor declara {esperado}",
        )
    return None


def aro_formato_canonico(ex: Extraction) -> Hallazgo | None:
    """`native_format` es uno de los cinco. **Lo desconocido no se decide por defecto.**

    Si esto falla, el aro de spans no se puede correr: `expresa_spans` levantaría. Por
    eso es `FALLA` y no aviso — y por eso el orquestador marca el de spans como
    `NO_EJECUTADA` en vez de darlo por bueno.
    """
    if ex.native_format not in FORMATOS_CANONICOS:
        return Hallazgo(
            "formato_canonico",
            "FALLA",
            f"native_format={ex.native_format!r} no es de los canónicos {list(FORMATOS_CANONICOS)}",
        )
    return None


def aro_tablas_bien_formadas(ex: Extraction) -> Hallazgo | None:
    """Solapes, huecos y spans fuera de rango. Lo mira `CanonicalTable`, no la buena fe."""
    fatales = []
    for i, t in enumerate(ex.tables):
        ok, problemas = t.is_wellformed()
        if not ok:
            fatales.append(f"tabla {i}: {'; '.join(problemas)}")
    if fatales:
        return Hallazgo("tablas_bien_formadas", "FALLA", " · ".join(fatales))
    return None


def aro_cost_of_es_pura(extractor: object, ex: Extraction) -> Hallazgo | None:
    """Dos llamadas con la misma extracción dan el mismo coste.

    Si no lo fuera, el coste por éxito publicado no se podría reproducir: dependería de
    cuándo se preguntó. Dos llamadas no demuestran pureza —**se declara**: esto detecta
    lo que mira el reloj o un contador, no lo que mira la red una vez y cachea—.
    """
    cost_of = getattr(extractor, "cost_of", None)
    if not callable(cost_of):
        return Hallazgo("cost_of_pura", "FALLA", "`cost_of` no es invocable")
    try:
        primero, segundo = cost_of(ex), cost_of(ex)
    except Exception as e:
        return Hallazgo("cost_of_pura", "FALLA", f"`cost_of` lanzó {type(e).__name__}: {e}")
    if primero != segundo:
        return Hallazgo(
            "cost_of_pura",
            "FALLA",
            f"dos llamadas con la misma extracción dieron {primero} y {segundo}",
        )
    return None


def spans_emitidos(ex: Extraction) -> bool:
    """Si la extracción trae **alguna** celda combinada de verdad."""
    return any(c.rowspan > 1 or c.colspan > 1 for t in ex.tables for c in t.cells)


def formato_utilizable_desde(native_format: str) -> bool:
    """Si se puede preguntar por sus spans sin que `expresa_spans` levante.

    Toma la cadena y no la `Extraction` porque quien pregunta ya ha reducido todas las
    extracciones a un formato: preguntarlo por extracción escondería que un extractor
    devolvió formatos distintos entre documentos, que es un fallo aparte.
    """
    return native_format in FORMATOS_CANONICOS
