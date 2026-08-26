"""`pdfplumber` · parser de texto. **El primer extractor real del banco.**

Un envoltorio fino, que es lo único que este repo puede escribir (regla de oro 1: el juez
no puede ser concursante). Ni una heurística de detección de tablas: las pone la
biblioteca, y si son malas, malas salen.

## Lo primero que se comprueba al escribir un extractor: qué declara SU conversor

`page.extract_tables()` devuelve **rejillas rectangulares**, así que su conversor es
`from_dataframe`, y ése declara `expresses_spans=False` y `source_format="dataframe"`.

Esa pregunta no es retórica: **es la que encontró el agujero de cuatro hitos**
—`"dataframe"` faltaba en `types.FORMATOS_SIN_SPANS`, así que una tabla de marco podía
declararse capaz de `rowspan` y `is_wellformed()` la daba por buena—. Por eso aquí
`expresses_spans` **no se teclea**: sale de `expresa_spans(FORMATO_NATIVO)`. Quien copie
este fichero y cambie el formato no puede mentir por descuido, y quien invente uno no
llega a cargarse: `expresa_spans` levanta ante lo desconocido.

El precio está declarado y es alto: sin `rowspan`, `pdfplumber` sale `NO_APLICABLE` en el
estrato de celdas combinadas y su nota **no se enseña sin su cobertura evaluable al
lado**. Regla de oro 4.

## La biblioteca se importa DENTRO de las funciones, y no es pereza

El registro descubre por entry points y **falla cerrado** (ADR-0036): un módulo que
reventara al importarse tumbaría el descubrimiento **del grupo entero**, y
`extract-local` no se instala en la puerta —arrastra torch y CUDA—. Con el import
dentro, que la biblioteca falte es lo que `probe()` está para contestar.

## `version` lleva las dos versiones que mueven el número

`0.11.9+ad1`: biblioteca y adaptador. Con sólo la primera, cambiar los ajustes de
detección de tablas de aquí movería la tabla de resultados **sin mover ninguna versión
publicada**, y el número dejaría de ser atribuible.
"""

from __future__ import annotations

import io
import time
from functools import partial
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _instalada
from typing import TYPE_CHECKING, Final

from benchcore.types import Cost, ProbeResult

from docbench_es.core.canonical import from_dataframe
from docbench_es.extract._marco import Rejilla
from docbench_es.extract._salida import causa_de, coste, extraccion
from docbench_es.extract._spans import expresa_spans
from docbench_es.extract.base import FamiliaExtractor

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from docbench_es.types import CanonicalTable, Extraction, RawDoc

__all__ = ["PdfplumberExtractor"]

FORMATO_NATIVO: Final = "dataframe"
"""Lo que devuelve `extract_tables()`: una rejilla rectangular, sin `rowspan`."""

VERSION_ADAPTADOR: Final = "1"
"""Sube cuando cambia LO QUE HACE ESTE FICHERO, no la biblioteca."""


def _version_biblioteca() -> str:
    """La instalada, **sin importar la biblioteca**: sólo sus metadatos."""
    try:
        return _instalada("pdfplumber")
    except PackageNotFoundError:
        return "no-instalado"


class PdfplumberExtractor:
    """§7.2 sobre `pdfplumber`. Las seis declaraciones son atributos de CLASE."""

    id = "pdfplumber"
    version = f"{_version_biblioteca()}+ad{VERSION_ADAPTADOR}"
    kind: FamiliaExtractor = "parser"
    runs_locally = True
    expresses_spans = expresa_spans(FORMATO_NATIVO)
    benchcore_api = "1.x"

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        """**Nunca lanza.** Un fallo viaja dentro, con su causa del enum cerrado.

        Un `page_range` inválido sale `provider_error` en vez de levantar, y eso mete un
        error del arnés en la tasa de fallo del extractor: **LIMITS 99**. La campaña de
        los 616 no pasa rango, así que hoy no puede contaminar el número publicado.
        """
        arranque = time.perf_counter()
        salida = partial(extraccion, self, doc, arranque, FORMATO_NATIVO)
        if page_range is not None and (page_range[0] < 1 or page_range[1] <= page_range[0]):
            return salida(causa="provider_error", detalle=f"page_range={page_range}")
        try:
            texto, tablas, paginas, vacias = _leer(doc.primary, page_range)
        except Exception as exc:
            return salida(causa=causa_de(exc), detalle=f"{type(exc).__name__}: {exc}"[:300])
        if not texto.strip() and not tablas:
            return salida(causa="no_text_layer", detalle=f"{paginas} páginas", paginas=paginas)
        avisos = (f"{vacias} tablas sin una sola celda, descartadas",) if vacias else ()
        return salida(texto=texto, tablas=tuple(tablas), paginas=paginas, avisos=avisos)

    def cost_of(self, ex: Extraction) -> Cost:
        """Local: cero euros MEDIDO, y el reloj de esa extracción. **Pura.**"""
        return coste(ex.latency_ms)

    def probe(self) -> ProbeResult:
        """¿Está `pdfplumber`? **Sin abrir ningún documento.**"""
        try:
            import pdfplumber
        except ImportError as exc:
            return ProbeResult(component_id=self.id, status="NO_INSTALADO", detail=str(exc))
        detalle = f"pdfplumber {pdfplumber.__version__}"
        return ProbeResult(component_id=self.id, status="OK", version=self.version, detail=detalle)


def _leer(
    pdf: bytes, page_range: tuple[int, int] | None
) -> tuple[str, list[CanonicalTable], int, int]:
    """El único sitio que toca la biblioteca. Devuelve texto, tablas, páginas y vacías.

    `page_range` es **medio abierto y en base 1**, como el resto del proyecto. Se lee de
    `bytes` y no de una ruta: el documento ya está en memoria, y escribirlo a disco para
    volver a leerlo mediría el disco además del extractor.

    Una tabla sin una sola celda **se descarta y se cuenta**: dejarla pasar inflaría el
    recuento de tablas del informe con objetos que no contienen nada.
    """
    import pdfplumber

    textos: list[str] = []
    tablas: list[CanonicalTable] = []
    vacias = 0
    with pdfplumber.open(io.BytesIO(pdf)) as documento:
        paginas = documento.pages
        if page_range is not None:
            paginas = paginas[page_range[0] - 1 : page_range[1] - 1]
        for pagina in paginas:
            textos.append(pagina.extract_text() or "")
            rejillas = [Rejilla(tuple(tuple(f) for f in t)) for t in pagina.extract_tables()]
            en_pagina = (pagina.page_number, pagina.page_number)
            for tabla in from_dataframe(rejillas, page_span=en_pagina):
                if tabla.cells:
                    tablas.append(tabla)
                else:
                    vacias += 1
        return "\n".join(textos), tablas, len(paginas), vacias
