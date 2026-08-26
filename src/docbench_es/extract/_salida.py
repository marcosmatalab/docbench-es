"""Cómo se arma la `Extraction` que sale de un extractor, **buena o mala**.

Los ocho extractores de L5 rellenan los mismos once campos de §6.3 con las mismas reglas,
y esas reglas no son mecánicas: **la latencia y el coste de un documento que FALLA
también se cuentan** —los segundos que costó descubrir que no se podía leer se gastaron
igual, y descontarlos abarataría precisamente al extractor que más se cae—, y `failed`
va atado a una causa del enum cerrado. Escrito ocho veces, se escribe mal una.

Aquí van las tres decisiones juntas porque son **una sola**: qué sale de un extractor.
Separar «la causa» de «la extracción fallida» dejaría la mitad del contrato en cada sitio.

## El reloj se toma aquí y no en cada extractor

`arranque` es un `perf_counter()` que pasa el llamador, y la resta ocurre en un solo
sitio. Con cada extractor midiendo por su cuenta, la latencia publicada compararía relojes
que empiezan y acaban en puntos distintos — y la latencia es una columna de la tabla.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Final, Protocol

from benchcore.types import Cost

from docbench_es.types import Extraction

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Iterator

    from docbench_es.types import CanonicalTable, ExtractionFailure, RawDoc

__all__ = ["CAUSA_POR_EXCEPCION", "Identificado", "causa_de", "coste", "extraccion"]


class Identificado(Protocol):
    """Lo ÚNICO que la salida necesita del extractor: quién es y qué versión.

    No se pide el `Extractor` entero a propósito. Pedirlo obligaría a cualquier cosa que
    quiera armar una `Extraction` —un doble de test, un arnés de medida— a implementar
    `extract`, `cost_of` y `probe` para no usarlos, y un tipo que exige de más acaba
    sorteándose con un `cast`, que es peor que no tenerlo. Un `Extractor` de verdad lo
    cumple por construcción.
    """

    id: str
    version: str


CAUSA_POR_EXCEPCION: Final[dict[str, ExtractionFailure]] = {
    "PDFPasswordIncorrect": "encrypted_pdf",
    "PDFEncryptionError": "encrypted_pdf",
    "PDFSyntaxError": "corrupt_pdf",
    "PSSyntaxError": "corrupt_pdf",
    "PSEOF": "corrupt_pdf",
    "FileDataError": "corrupt_pdf",
    "_Cifrado": "encrypted_pdf",
    "MemoryError": "out_of_memory",
}
"""Excepción → causa del enum CERRADO de §6.9, **por nombre de clase**.

Por nombre y no importando `pdfminer.pdfparser.PDFSyntaxError`: esa ruta cambia entre
menores de `pdfminer.six`, y un extractor **no puede importar su biblioteca arriba** sin
tumbar el descubrimiento del grupo entero (ADR-0036). `pdfminer` lo comparten
`pdfplumber` y `camelot`, así que la tabla es de todos y no de uno. `FileDataError` es
de `pymupdf`, que envuelve los errores de MuPDF en una sola clase: la usan `pymupdf4llm`
y `marker`.
"""


def _cadena(exc: BaseException, tope: int = 6) -> Iterator[BaseException]:
    """La excepción y las que trae dentro, **de fuera adentro**.

    **Hace falta, y se descubrió midiendo.** `pdfplumber` envuelve TODO lo que sale de
    `pdfminer` en un `PdfminerException` propio, así que un PDF corrupto llegaba aquí como
    esa clase genérica y salía `provider_error`: la tabla de *fallo por causa* habría
    tenido **una sola columna** y ni un `corrupt_pdf`, con el enum cerrado funcionando y
    sin distinguir nada.

    Se recorre en anchura y de fuera adentro para que una clase puesta a mano en la tabla
    gane a la que trae dentro. `args` se mira además de `__cause__` y `__context__` porque
    el envoltorio de `pdfplumber` es literalmente `raise PdfminerException(e)`.
    """
    vistos: set[int] = set()
    pendientes = [exc]
    while pendientes and len(vistos) < tope:
        actual = pendientes.pop(0)
        if id(actual) in vistos:
            continue
        vistos.add(id(actual))
        yield actual
        dentro = (actual.__cause__, actual.__context__, *actual.args)
        pendientes += [d for d in dentro if isinstance(d, BaseException)]


def causa_de(exc: BaseException) -> ExtractionFailure:
    """La causa que le toca por su MRO **y por lo que traiga dentro**. Si no, `provider_error`.

    **Con su tipo y su mensaje en `warnings`**, siempre: la regla de oro 6 prohíbe
    tragarse un error, no obliga a tener un código propio para cada uno. Lo que no puede
    pasar es que un fallo desaparezca del informe, y con causa y detalle no desaparece.
    """
    for envuelta in _cadena(exc):
        for clase in type(envuelta).__mro__:
            causa = CAUSA_POR_EXCEPCION.get(clase.__name__)
            if causa is not None:
                return causa
    return "provider_error"


def coste(latency_ms: int) -> Cost:
    """Cero euros **MEDIDO** —no «no medido»— y el reloj de esa extracción.

    Un extractor local no gasta, y eso es un hecho, no una ausencia de dato.
    `Cost.unknown()` diría lo contrario y contaminaría el total de la campaña, que suma.
    """
    return Cost(wall_ms=latency_ms)


def extraccion(
    extractor: Identificado,
    doc: RawDoc,
    arranque: float,
    formato: str,
    *,
    texto: str = "",
    tablas: tuple[CanonicalTable, ...] = (),
    paginas: int = 0,
    avisos: tuple[str, ...] = (),
    causa: ExtractionFailure | None = None,
    detalle: str = "",
) -> Extraction:
    """La única `Extraction` que sale de un extractor de este banco.

    `extractor` entra como objeto y no como `(id, version)` sueltos para que la extracción
    no pueda decir ser de otro: es el aro `identificacion` de la conformidad, cumplido por
    construcción en vez de comprobado a posteriori.
    """
    ms = int((time.perf_counter() - arranque) * 1000)
    return Extraction(
        extractor_id=extractor.id,
        extractor_version=extractor.version,
        doc_ref=doc.ref,
        text=texto,
        tables=tablas,
        native_format=formato,
        pages_processed=paginas,
        cost=coste(ms),
        latency_ms=ms,
        warnings=((detalle, *avisos) if detalle else avisos),
        failed=causa is not None,
        failure_reason=causa,
    )
