"""§9.1 · `from_tei`. `expresses_spans=True`: TEI sí lleva `rowspan`.

`<cell cols="2" rows="3">` es exactamente `colspan`/`rowspan`, así que GROBID
compite en el estrato de celdas combinadas. Marcarlo incapaz sería la injusticia
simétrica a la que evita ADR-0006.

**Seguridad de la entrada.** El TEI lo produce GROBID, que es un servicio
externo: un `<!DOCTYPE>` con entidades anidadas es la bomba de expansión clásica.
Se rechaza la entrada con DOCTYPE **antes de parsear**, en vez de meter
`defusedxml` en el núcleo puro. `xml.etree` no está en la lista de prohibidos de
`.importlinter`, pero su parser expande entidades internas.
"""

from __future__ import annotations

from xml.etree import ElementTree

from docbench_es.core.canonical._normalizar import normalize_cell_text
from docbench_es.core.canonical._rejilla import Colocador
from docbench_es.types import CanonicalTable


def _entero(elemento: ElementTree.Element, nombre: str) -> int:
    valor = (elemento.get(nombre) or "").strip()
    # `isascii()` NO sobra: "²".isdigit() es True y int("²") revienta.
    return int(valor) if valor.isascii() and valor.isdigit() else 1


def _sin_espacio_de_nombres(raiz: ElementTree.Element) -> None:
    """Quita el `{http://www.tei-c.org/ns/1.0}` de cada etiqueta.

    GROBID emite TEI con espacio de nombres y hay herramientas que lo emiten sin
    él. Normalizar la etiqueta evita tener que escribir las dos variantes en cada
    búsqueda, que es donde se cuela el caso que no se probó.
    """
    for elemento in raiz.iter():
        if isinstance(elemento.tag, str) and "}" in elemento.tag:
            elemento.tag = elemento.tag.split("}", 1)[1]


def from_tei(tei: str, *, page_span: tuple[int, int] = (1, 1)) -> list[CanonicalTable]:
    """Las `<table>` de un documento TEI, en orden.

    Caso degenerado: entrada vacía o sin tablas devuelve `[]`. Una entrada que no
    es XML válido lanza `ElementTree.ParseError`: eso es un fallo del extractor
    que lo produjo, y el extractor lo convierte en `failure_reason`, no en cero
    tablas silenciosas.
    """
    if not tei.strip():
        return []
    if "<!DOCTYPE" in tei:
        raise ValueError(
            "TEI con DOCTYPE: no se parsea. Las entidades de una entrada ajena "
            "son una bomba de expansion y el nucleo no lleva defusedxml"
        )
    raiz = ElementTree.fromstring(tei)  # el DOCTYPE se rechaza arriba
    _sin_espacio_de_nombres(raiz)

    tablas: list[CanonicalTable] = []
    for elemento in raiz.iter("table"):
        colocador = Colocador()
        for fila in elemento.findall("row"):
            colocador.nueva_fila()
            cabecera_de_fila = fila.get("role") == "label"
            for celda in fila.findall("cell"):
                colocador.colocar(
                    normalize_cell_text("".join(celda.itertext())),
                    is_header=cabecera_de_fila or celda.get("role") == "label",
                    rowspan=_entero(celda, "rows"),
                    colspan=_entero(celda, "cols"),
                )
        celdas, n_filas, n_cols = colocador.terminar()
        titulo = elemento.find("head")
        caption = normalize_cell_text("".join(titulo.itertext())) if titulo is not None else ""
        tablas.append(
            CanonicalTable(
                cells=celdas,
                n_rows=n_filas,
                n_cols=n_cols,
                page_span=page_span,
                caption=caption or None,
                expresses_spans=True,
                source_format="tei",
            )
        )
    return tablas
