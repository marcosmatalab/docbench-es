"""`camelot` · extractor de tablas. **La tercera familia de §16, y la que no busca texto.**

## PASO 0, contestado ejecutando: qué declara su conversor

`read_pdf()` devuelve una `TableList`; cada `Table` trae un `DataFrame` en `.df` y su
número de página en `.page`. Conversor: `from_dataframe` → `expresses_spans=False` y
`source_format="dataframe"`, que está en `types.FORMATOS_SIN_SPANS`. Coinciden los tres.

**Y no estrena conversor**: `from_dataframe` lo validó `pdfplumber` dos días antes. De los
tres hallazgos de conversor de este hito, los tres salieron de ESTRENAR uno.

Comprobado sobre `BOE-A-2026-7446` —verdad congelada 3x8 con siete combinadas—: camelot
devuelve **3x8**, la misma forma que la verdad, con las combinadas aplanadas y su hueco
como celda vacía. Y **las etiquetas de columna de su marco son enteros posicionales**, así
que `from_dataframe` declara que no hay cabecera y **no inventa una fila** — comprobado,
0 celdas con `is_header`, que es justo lo que LIMITS 36 dice que hay que evitar.

## Las dos cosas que hay que pasarle a mano, y las dos son trampas

* **`pages="all"`.** El valor por defecto de `read_pdf` es `pages='1'`: sin esto, camelot
  lee **la primera página y nada más**, y la tabla de resultados diría que encuentra pocas
  tablas cuando lo que pasa es que sólo miró una página de cada documento.
* **`flavor="lattice"`**, que es el valor por defecto **y aun así se pasa explícito**,
  porque es una decisión de medición y no un detalle: `lattice` busca **líneas dibujadas**
  y `stream` agrupa por espacios en blanco. Sobre el BOE, cuyas tablas llevan líneas,
  `stream` encontraría más cosas **y más de ellas serían inventadas**. Elegir el flavor
  después de ver los números sería elegir el que conviene: queda congelado en
  `runs/l5/formatos.yaml`.
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
from docbench_es.extract._salida import causa_de, coste, extraccion
from docbench_es.extract._spans import expresa_spans
from docbench_es.extract.base import FamiliaExtractor

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from docbench_es.types import CanonicalTable, Extraction, RawDoc

__all__ = ["CamelotExtractor"]

FORMATO_NATIVO: Final = "dataframe"
"""Lo que hay en `Table.df`: una rejilla rectangular, sin `rowspan`."""

SABOR: Final = "lattice"
"""Busca líneas dibujadas. Congelado en `runs/l5/formatos.yaml`, no elegido a posteriori."""

VERSION_ADAPTADOR: Final = "1"
"""Sube cuando cambia LO QUE HACE ESTE FICHERO, no la biblioteca."""


def _version_biblioteca() -> str:
    """La instalada, **sin importar la biblioteca**: sólo sus metadatos."""
    try:
        return _instalada("camelot-py")
    except PackageNotFoundError:
        return "no-instalado"


class CamelotExtractor:
    """§7.2 sobre `camelot`. Las seis declaraciones son atributos de CLASE."""

    id = "camelot"
    version = f"{_version_biblioteca()}+{SABOR}+ad{VERSION_ADAPTADOR}"
    kind: FamiliaExtractor = "parser"
    runs_locally = True
    expresses_spans = expresa_spans(FORMATO_NATIVO)
    benchcore_api = "1.x"

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        """**Nunca lanza.** Un fallo viaja dentro, con su causa del enum cerrado.

        **No devuelve texto, y no es un descuido**: camelot busca tablas y nada más. Un
        `text` vacío aquí significa *«no es su trabajo»*, así que la regla de
        `no_text_layer` de los otros dos —sin texto y sin tablas, se declara fallo— **no
        se aplica**: un documento sin tablas es un resultado legítimo de este extractor,
        y contarlo como fallo inflaría su tasa con 662 documentos que no tienen ninguna.
        """
        arranque = time.perf_counter()
        salida = partial(extraccion, self, doc, arranque, FORMATO_NATIVO)
        if page_range is not None and (page_range[0] < 1 or page_range[1] <= page_range[0]):
            return salida(causa="provider_error", detalle=f"page_range={page_range}")
        try:
            tablas, paginas = _leer(doc.primary, page_range, doc.n_pages)
        except Exception as exc:
            return salida(causa=causa_de(exc), detalle=f"{type(exc).__name__}: {exc}"[:300])
        return salida(tablas=tuple(tablas), paginas=paginas)

    def cost_of(self, ex: Extraction) -> Cost:
        """Local: cero euros MEDIDO, y el reloj de esa extracción. **Pura.**"""
        return coste(ex.latency_ms)

    def probe(self) -> ProbeResult:
        """¿Está `camelot`? **Sin abrir ningún documento.**"""
        try:
            import camelot
        except ImportError as exc:
            return ProbeResult(component_id=self.id, status="NO_INSTALADO", detail=str(exc))
        detalle = f"camelot {getattr(camelot, '__version__', '?')} · flavor={SABOR}"
        return ProbeResult(component_id=self.id, status="OK", version=self.version, detail=detalle)


def _leer(
    pdf: bytes, page_range: tuple[int, int] | None, n_pages: int | None
) -> tuple[list[CanonicalTable], int]:
    """El único sitio que toca la biblioteca. Devuelve tablas y páginas miradas.

    `pages` es una CADENA en camelot —`"all"`, `"1-3"`—, así que el rango medio abierto y
    en base 1 del proyecto se traduce aquí y en un solo sitio.

    **Las páginas se cuentan de lo declarado, no de lo devuelto.** camelot sólo devuelve
    páginas CON tabla, así que contar sus resultados diría que un documento de 90 páginas
    tiene 2 — y `pages_processed` alimenta el coste por página.
    """
    import camelot

    if page_range is None:
        cuales, miradas = "all", (n_pages or 0)
    else:
        cuales, miradas = f"{page_range[0]}-{page_range[1] - 1}", page_range[1] - page_range[0]
    encontradas = camelot.read_pdf(
        io.BytesIO(pdf), pages=cuales, flavor=SABOR, suppress_stdout=True
    )
    tablas: list[CanonicalTable] = []
    for t in encontradas:
        pagina = int(getattr(t, "page", 1) or 1)
        tablas.extend(from_dataframe([t.df], page_span=(pagina, pagina)))
    return tablas, miradas
