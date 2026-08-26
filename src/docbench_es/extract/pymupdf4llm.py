"""`pymupdf4llm` · parser de texto que emite Markdown. **El segundo extractor real.**

## PASO 0, contestado ejecutando: qué declara su conversor

`to_markdown()` devuelve **Markdown GFM**, así que su conversor es `from_markdown`, que
declara `expresses_spans=False` y `source_format="markdown"` — y `"markdown"` está en
`types.FORMATOS_SIN_SPANS`. Coinciden los tres.

Comprobado sobre `BOE-A-2026-7446`, cuya verdad congelada de L4 dice **3x8 con siete
celdas combinadas**: `pymupdf4llm` devuelve **2x8 y ninguna combinada**. Eso **no es un
fallo**: es exactamente lo que `expresses_spans=False` significa. El formato no puede con
`rowspan`, la cabecera de dos niveles se aplana a una, y por eso su TEDS sale
`NO_APLICABLE` en el estrato de celdas combinadas y su nota no se enseña sin la cobertura
evaluable al lado. Regla de oro 4.

**`from_markdown` estrena consumidor aquí**, y eso es lo que la sección «Construido y NO
VALIDADO» de `ESTADO.md` predice que trae hallazgos. Trajo uno, medido y con número:
**116 de 594 celdas (19,5%) salen con marcado de Markdown dentro del texto** —86 con
`**` y 54 con `<br>`—, contra una verdad que dice `'Número'` donde esto dice
`'**Número**'`. Está en LIMITS 103, **no se ha tocado nada** y la decisión es del
usuario: repararlo aquí sería normalizar a favor de un extractor.

## Por qué lee de `bytes` y por páginas

`to_markdown` acepta un `pymupdf.Document`, y abrir desde `stream=` da **el mismo
resultado, comprobado**, que abrir desde una ruta: el documento ya está en memoria y
escribirlo a disco mediría el disco. Y se convierte con `page_chunks=True` para que el
`page_span` sea el de verdad y no `(1,1)` para todo — al precio, declarado, de que una
tabla que cruce página salga como dos.
"""

from __future__ import annotations

import time
from functools import partial
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _instalada
from typing import TYPE_CHECKING, Final

from benchcore.types import Cost, ProbeResult

from docbench_es.core.canonical import from_markdown
from docbench_es.extract._salida import causa_de, coste, extraccion
from docbench_es.extract._spans import expresa_spans
from docbench_es.extract.base import FamiliaExtractor

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from docbench_es.types import CanonicalTable, Extraction, RawDoc

__all__ = ["Pymupdf4llmExtractor"]

FORMATO_NATIVO: Final = "markdown"
"""Lo que devuelve `to_markdown()`. Markdown no tiene `rowspan`: ADR-0006."""

VERSION_ADAPTADOR: Final = "1"
"""Sube cuando cambia LO QUE HACE ESTE FICHERO, no la biblioteca."""


def _version_biblioteca() -> str:
    """La instalada, **sin importar la biblioteca**: sólo sus metadatos."""
    try:
        return _instalada("pymupdf4llm")
    except PackageNotFoundError:
        return "no-instalado"


class Pymupdf4llmExtractor:
    """§7.2 sobre `pymupdf4llm`. Las seis declaraciones son atributos de CLASE."""

    id = "pymupdf4llm"
    version = f"{_version_biblioteca()}+ad{VERSION_ADAPTADOR}"
    kind: FamiliaExtractor = "parser"
    runs_locally = True
    expresses_spans = expresa_spans(FORMATO_NATIVO)
    benchcore_api = "1.x"

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        """**Nunca lanza.** Un fallo viaja dentro, con su causa del enum cerrado.

        Un `page_range` inválido sale `provider_error` en vez de levantar: **LIMITS 99**,
        igual que en `pdfplumber`. La campaña de los 616 no pasa rango.
        """
        arranque = time.perf_counter()
        salida = partial(extraccion, self, doc, arranque, FORMATO_NATIVO)
        if page_range is not None and (page_range[0] < 1 or page_range[1] <= page_range[0]):
            return salida(causa="provider_error", detalle=f"page_range={page_range}")
        try:
            texto, tablas, paginas = _leer(doc.primary, page_range)
        except Exception as exc:
            return salida(causa=causa_de(exc), detalle=f"{type(exc).__name__}: {exc}"[:300])
        if not texto.strip() and not tablas:
            return salida(causa="no_text_layer", detalle=f"{paginas} páginas", paginas=paginas)
        return salida(texto=texto, tablas=tuple(tablas), paginas=paginas)

    def cost_of(self, ex: Extraction) -> Cost:
        """Local: cero euros MEDIDO, y el reloj de esa extracción. **Pura.**"""
        return coste(ex.latency_ms)

    def probe(self) -> ProbeResult:
        """¿Está `pymupdf4llm`? **Sin abrir ningún documento.**"""
        try:
            import pymupdf4llm
        except ImportError as exc:
            return ProbeResult(component_id=self.id, status="NO_INSTALADO", detail=str(exc))
        detalle = f"pymupdf4llm {getattr(pymupdf4llm, '__version__', '?')}"
        return ProbeResult(component_id=self.id, status="OK", version=self.version, detail=detalle)


def _leer(pdf: bytes, page_range: tuple[int, int] | None) -> tuple[str, list[CanonicalTable], int]:
    """El único sitio que toca la biblioteca. Devuelve texto, tablas y páginas.

    **El documento cifrado se declara, no se intenta.** `pymupdf.open` no levanta ante uno
    protegido: devuelve un documento con `needs_pass`, y convertirlo daría cero tablas —
    que se contaría como «no encontró nada» en vez de como lo que es. La tasa de fallo por
    causa es un resultado, y `encrypted_pdf` es una de sus filas.
    """
    import pymupdf
    import pymupdf4llm

    with pymupdf.open(stream=pdf, filetype="pdf") as documento:
        if documento.needs_pass:
            raise _Cifrado(f"{documento.page_count} páginas protegidas con contraseña")
        primera = 1 if page_range is None else page_range[0]
        ultima = (
            documento.page_count
            if page_range is None
            else min(page_range[1] - 1, documento.page_count)
        )
        indices = list(range(primera - 1, ultima))
        trozos = pymupdf4llm.to_markdown(
            documento, pages=indices, page_chunks=True, show_progress=False
        )
        textos: list[str] = []
        tablas: list[CanonicalTable] = []
        for i, trozo in enumerate(trozos):
            md = str(trozo["text"])
            textos.append(md)
            en_pagina = (primera + i, primera + i)
            tablas.extend(from_markdown(md, page_span=en_pagina))
        return "\n".join(textos), tablas, len(indices)


class _Cifrado(Exception):
    """Se traduce a `encrypted_pdf` por `CAUSA_POR_EXCEPCION`, como cualquier otra."""
