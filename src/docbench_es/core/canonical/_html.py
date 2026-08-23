"""§9.1 · `from_html`. `expresses_spans=True`: el formato sí puede con `rowspan`.

Con `html.parser` de la biblioteca estándar y **sin dependencias**: el núcleo es
puro y `.importlinter` le prohíbe hasta `http`. `html` es otro paquete y no está
en esa lista.

Las decisiones de extracción de texto se apoyan en las etiquetas que el sondeo
contó sobre 600 documentos del BOE. **Dos condiciones que hay que leer antes que
los números**, corregidas en el escrutinio de L1:

1. Son **apariciones en el documento COMPLETO**, no dentro de `<table>`:
   `sondeo_lib.py` cuenta sobre el XML entero. Cuántas caen dentro de una celda
   **no está medido** (LIMITS 33).
2. Son **cotas inferiores**: el sondeo guardaba `most_common(12)` por documento.

Con eso dicho, y sabiendo que sostienen una decisión de diseño y no un número
publicado:

- **`<p>`: 61.541**, más que `<td>` (41.902). De ésas, 29.535 en documentos que
  tienen alguna tabla. Las celdas llevan marcado de bloque dentro, así que los
  bloques separan con un espacio.
- **`<sup>` 219 y `<sub>` 574.** Las etiquetas inline **no** separan: si
  separasen, `m<sup>2</sup>` saldría `m 2`.
- **`<img>`: 489, y aquí la condición 1 muerde.** Sólo **21** están en documentos
  con alguna tabla; **468 están en documentos sin ni una `<table>`**, que es el
  estrato que ADR-0016 disolvió. Dentro de una celda un `<img>` no aporta texto,
  ni siquiera su `alt`, pero el «son 489» de la primera versión de este docstring
  medía otra cosa: el número honesto es 21, y ni siquiera ése es «dentro de una
  celda». El problema que la decisión abre sigue en LIMITS 33.
- **`<colgroup>` 626 contra `<table>` 631.** `n_cols` se deriva de las celdas y
  no del `<colgroup>`: creerse el `<colgroup>` permitiría declarar columnas que
  nadie usa. Se usa como oráculo en los tests, que es donde vale.
"""

from __future__ import annotations

from html.parser import HTMLParser

from docbench_es.core.canonical._normalizar import normalize_cell_text
from docbench_es.core.canonical._rejilla import Colocador
from docbench_es.types import CanonicalTable

BLOQUES = frozenset(
    {"p", "div", "br", "li", "ul", "ol", "dt", "dd", "h1", "h2", "h3", "h4", "h5", "h6", "pre"}
)
"""Separan con un espacio. `<p>a</p><p>b</p>` en una celda es «a b», no «ab»."""

SECCIONES = frozenset({"thead", "tbody", "tfoot"})
"""Delimitan el alcance de `rowspan="0"`, que es «hasta el final de la sección»."""


def _entero(atributos: list[tuple[str, str | None]], nombre: str) -> int:
    """El entero no negativo del estándar: si no lo es, vale 1.

    Un `rowspan="-3"` o `colspan="abc"` es basura del HTML de origen, no un fallo
    del extractor. Dejarla pasar tal cual emitiría `SPAN_MENOR_QUE_UNO` y el
    documento se contaría como fallo de quien lo extrajo. Seguir el estándar no
    es normalizar a la callada: es leer el formato.
    """
    for clave, valor in atributos:
        if clave == nombre and valor is not None:
            texto = valor.strip()
            # `isascii()` NO sobra: "²".isdigit() es True y int("²") revienta.
            # Y el BOE usa <sup>2</sup> a montones, asi que el superindice llega.
            return int(texto) if texto.isascii() and texto.isdigit() else 1
    return 1


class _Contexto:
    """Una `<table>` abierta. Hay una pila porque las tablas se anidan."""

    def __init__(self, indice: int) -> None:
        self.indice = indice
        self.colocador = Colocador()
        self.caption: list[str] = []
        self.celda: list[str] | None = None
        self.is_header = False
        self.rowspan = 1
        self.colspan = 1
        self.en_caption = False
        self.en_cabecera = False

    def abrir_celda(self, *, is_header: bool, rowspan: int, colspan: int) -> None:
        self.cerrar_celda()
        self.celda = []
        self.is_header = is_header
        self.rowspan = rowspan
        self.colspan = colspan

    def cerrar_celda(self) -> None:
        if self.celda is None:
            return
        self.colocador.colocar(
            normalize_cell_text("".join(self.celda)),
            is_header=self.is_header,
            rowspan=self.rowspan,
            colspan=self.colspan,
        )
        self.celda = None


class _LectorDeTablas(HTMLParser):
    """Recorre el HTML una vez y va cerrando tablas conforme aparecen sus `</table>`.

    Las tablas se reservan su hueco en `tablas` al ABRIRSE, así que el orden de
    salida es el orden de documento aunque estén anidadas.
    """

    def __init__(self, page_span: tuple[int, int]) -> None:
        super().__init__(convert_charrefs=True)
        self.page_span = page_span
        self.tablas: list[CanonicalTable | None] = []
        self._pila: list[_Contexto] = []

    @property
    def _ctx(self) -> _Contexto | None:
        return self._pila[-1] if self._pila else None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.tablas.append(None)
            self._pila.append(_Contexto(len(self.tablas) - 1))
            return
        ctx = self._ctx
        if ctx is None:
            return
        if tag in ("td", "th"):
            ctx.abrir_celda(
                # `<thead><td>` es una celda de CABECERA. No marcarla perdía la
                # condición en todo corpus que use esa forma —PubTabNet la usa
                # SIEMPRE— y `is_header` salía False en el 100% de las cabeceras.
                # Encontrado en L2, al construir el árbol de TEDS.
                is_header=tag == "th" or ctx.en_cabecera,
                rowspan=_entero(attrs, "rowspan"),
                colspan=_entero(attrs, "colspan"),
            )
        elif tag == "tr":
            ctx.cerrar_celda()
            ctx.colocador.nueva_fila()
        elif tag in SECCIONES:
            ctx.cerrar_celda()
            ctx.colocador.cerrar_seccion()
            ctx.en_cabecera = tag == "thead"
        elif tag == "caption":
            ctx.en_caption = True
        elif tag in BLOQUES and ctx.celda is not None:
            ctx.celda.append(" ")

    def handle_endtag(self, tag: str) -> None:
        ctx = self._ctx
        if ctx is None:
            return
        if tag == "table":
            ctx.cerrar_celda()
            celdas, n_filas, n_cols = ctx.colocador.terminar()
            caption = normalize_cell_text("".join(ctx.caption))
            self.tablas[ctx.indice] = CanonicalTable(
                cells=celdas,
                n_rows=n_filas,
                n_cols=n_cols,
                page_span=self.page_span,
                caption=caption or None,
                expresses_spans=True,
                source_format="html",
            )
            self._pila.pop()
        elif tag in ("td", "th", "tr"):
            ctx.cerrar_celda()
        elif tag in SECCIONES:
            ctx.cerrar_celda()
            ctx.colocador.cerrar_seccion()
            ctx.en_cabecera = False
        elif tag == "caption":
            ctx.en_caption = False
        elif tag in BLOQUES and ctx.celda is not None:
            ctx.celda.append(" ")

    def cerrar_lo_que_quede(self) -> None:
        """HTML sin cerrar: se cierra cada `<table>` abierta como si lo estuviera.

        Un `<table>` sin su `</table>` es HTML roto que el navegador pinta igual.
        Descartar esas tablas perdería documentos enteros y los contaría como
        «sin tablas», que es un número equivocado, no una ausencia de dato.
        """
        while self._pila:
            self.handle_endtag("table")

    def handle_data(self, data: str) -> None:
        ctx = self._ctx
        if ctx is None:
            return
        if ctx.en_caption:
            ctx.caption.append(data)
        elif ctx.celda is not None:
            ctx.celda.append(data)


def from_html(html: str, *, page_span: tuple[int, int] = (1, 1)) -> list[CanonicalTable]:
    """Todas las `<table>` del documento, en orden.

    `page_span` lo pone quien llama: el HTML no lleva páginas (LIMITS 32).

    Casos degenerados declarados: un documento sin `<table>` devuelve `[]`; una
    `<table>` sin filas devuelve **una tabla vacía**, no cero tablas, porque
    «detectó una tabla y está vacía» y «no detectó nada» son cosas distintas para
    la métrica *tablas no detectadas* de §12. Una tabla anidada sale como tabla
    aparte y su texto **no** se suma al de la celda que la contiene: contarlo dos
    veces inflaría la exactitud de celda de quien anida.
    """
    lector = _LectorDeTablas(page_span)
    lector.feed(html)
    lector.close()
    lector.cerrar_lo_que_quede()
    return [t for t in lector.tablas if t is not None]
