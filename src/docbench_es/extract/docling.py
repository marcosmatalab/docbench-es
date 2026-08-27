"""`docling` · document-AI. **La tercera familia de §16 y el 63% del presupuesto.**

## PASO 0, contestado ejecutando y ANTES de escribir una línea

`convert()` devuelve un documento con `TableItem`s cuyas celdas traen `row_span` y
`col_span`, y cuyo `export_to_html()` emite **`rowspan` y `colspan` de verdad**. Conversor:
`from_html` → **`expresses_spans=True`**.

Medido sobre `BOE-A-2026-7446`, cuya verdad congelada de L4 declara **3x8 con siete celdas
combinadas**: docling devuelve **3x8 y siete combinadas**, y su HTML trae `rowspan="2"` y
`colspan="2"`. O sea que declararse capaz **no es optimismo aquí: es lo que hace**.

**Por qué antes y no después.** Es la clase exacta del agujero de `camelot` —declararse
capaz de spans y perderlos por el camino— sobre el extractor **más caro de la campaña**.
Y de propina, `from_html` es el **único conversor validado desde L1**.

**Lo que esto NO dice**: que los acierte. Dice que los **expresa**, que es lo único que
gobierna `expresses_spans`. Si los pone mal, sale en el TEDS, que es donde tiene que salir.

## Los hilos son parte de la versión publicada

`torch` levanta un pool por defecto, y el experimento A de B5-bis midió que subirlo cuesta
**entre 4 y 12 veces la CPU para el mismo reloj o peor** (LIMITS 89). El presupuesto de
**2,53 h** de este extractor sobre los 616 está medido en la configuración de **dos
hilos**, así que correr con otra haría incomparable el coste publicado con el
pre-registrado. Se fija aquí, y viaja en `version` como el `flavor` de camelot.

**Las variables de entorno se ponen al IMPORTAR este módulo**, no al extraer: OpenMP y BLAS
las leen cuando `torch` se carga. Ponerlas después no tiene efecto — medido en B5-bis, con
`hilos_efectivos` en 4,2 y el entorno pidiendo 2.
"""

from __future__ import annotations

import io
import os
import time
from functools import partial
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _instalada
from typing import TYPE_CHECKING, Final

from benchcore.types import Cost, ProbeResult

from docbench_es.core.canonical import from_html
from docbench_es.extract._salida import causa_de, coste, extraccion
from docbench_es.extract._spans import expresa_spans
from docbench_es.extract.base import FamiliaExtractor

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from docbench_es.types import CanonicalTable, Extraction, RawDoc

__all__ = ["HILOS", "DoclingExtractor"]

FORMATO_NATIVO: Final = "html"
"""`export_to_html()` emite `rowspan` y `colspan`. Comprobado, no supuesto."""

HILOS: Final = 2
"""La configuración en la que B5-bis midió el presupuesto de 2,53 h. Ver LIMITS 89."""

VERSION_ADAPTADOR: Final = "1"
"""Sube cuando cambia LO QUE HACE ESTE FICHERO, no la biblioteca."""

for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "TORCH_NUM_THREADS"):
    os.environ.setdefault(_var, str(HILOS))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _version_biblioteca() -> str:
    """La instalada, **sin importar la biblioteca**: sólo sus metadatos."""
    try:
        return _instalada("docling")
    except PackageNotFoundError:
        return "no-instalado"


class DoclingExtractor:
    """§7.2 sobre `docling`. Las seis declaraciones son atributos de CLASE."""

    id = "docling"
    version = f"{_version_biblioteca()}+{HILOS}h+ad{VERSION_ADAPTADOR}"
    kind: FamiliaExtractor = "hibrido"
    runs_locally = True
    expresses_spans = expresa_spans(FORMATO_NATIVO)
    benchcore_api = "1.x"

    def extract(self, doc: RawDoc, page_range: tuple[int, int] | None = None) -> Extraction:
        """**Nunca lanza.** Un fallo viaja dentro, con su causa del enum cerrado."""
        arranque = time.perf_counter()
        salida = partial(extraccion, self, doc, arranque, FORMATO_NATIVO)
        if page_range is not None and (page_range[0] < 1 or page_range[1] <= page_range[0]):
            return salida(causa="provider_error", detalle=f"page_range={page_range}")
        try:
            texto, tablas, paginas, avisos = _leer(doc.primary, page_range)
        except Exception as exc:
            return salida(causa=causa_de(exc), detalle=f"{type(exc).__name__}: {exc}"[:300])
        if not texto.strip() and not tablas:
            return salida(causa="no_text_layer", detalle=f"{paginas} páginas", paginas=paginas)
        return salida(texto=texto, tablas=tuple(tablas), paginas=paginas, avisos=avisos)

    def cost_of(self, ex: Extraction) -> Cost:
        """Local: cero euros MEDIDO, y el reloj de esa extracción. **Pura.**"""
        return coste(ex.latency_ms)

    def probe(self) -> ProbeResult:
        """¿Está `docling`? **Sin convertir ningún documento.**

        Importar `docling` no carga los modelos —eso pasa al construir el conversor—, así
        que esto sigue siendo barato, que es la razón de que `probe` exista.
        """
        try:
            import docling  # noqa: F401
        except ImportError as exc:
            return ProbeResult(component_id=self.id, status="NO_INSTALADO", detail=str(exc))
        detalle = f"docling {_version_biblioteca()} · {HILOS} hilos"
        return ProbeResult(component_id=self.id, status="OK", version=self.version, detail=detalle)


def _leer(
    pdf: bytes, page_range: tuple[int, int] | None
) -> tuple[str, list[CanonicalTable], int, tuple[str, ...]]:
    """El único sitio que toca la biblioteca. Devuelve texto, tablas, páginas y avisos.

    **El estado de la conversión se mira y se cuenta.** `docling` puede devolver
    `PARTIAL_SUCCESS` —parte del documento convertida y parte no— sin levantar. Eso no es
    un fallo del documento, pero tampoco es un éxito limpio: va como aviso, y un aviso
    aparece en el informe.
    """
    import torch

    torch.set_num_threads(HILOS)
    from docling.datamodel.base_models import DocumentStream
    from docling.document_converter import DocumentConverter

    fuente = DocumentStream(name="entrada.pdf", stream=io.BytesIO(pdf))
    if page_range is None:
        resultado = DocumentConverter().convert(fuente)
    else:
        resultado = DocumentConverter().convert(
            fuente, page_range=(page_range[0], page_range[1] - 1)
        )
    documento = resultado.document
    tablas: list[CanonicalTable] = []
    for t in documento.tables:
        pagina = next((p.page_no for p in (t.prov or []) if p.page_no), 1)
        tablas.extend(from_html(t.export_to_html(doc=documento), page_span=(pagina, pagina)))
    estado = str(getattr(resultado, "status", ""))
    avisos = () if estado.endswith("SUCCESS") and "PARTIAL" not in estado else (f"estado={estado}",)
    return documento.export_to_markdown(), tablas, len(documento.pages or {}), avisos
