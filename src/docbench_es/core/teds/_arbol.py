"""El árbol sobre el que se calcula TEDS, y su render a HTML.

TEDS no está definido sobre `CanonicalTable`: está definido sobre **el árbol HTML
de una tabla**, y la implementación de referencia de PubTabNet lo construye con
unas reglas concretas que aquí se reproducen exactamente, porque de ellas depende
el número:

- La raíz es `<table>`. **No cuenta** para la normalización: la referencia usa
  `len(table.xpath(".//*"))`, o sea los DESCENDIENTES.
- Un `<td>` es una **hoja**: lleva `colspan`, `rowspan` y su contenido tokenizado,
  y no se baja a sus hijos.
- Cualquier otro nodo lleva sólo su etiqueta, y `colspan`/`rowspan` a `None`.
- El contenido de una celda son sus **caracteres sueltos**, no la cadena: la
  referencia hace `list(node.text)` y compara con Levenshtein sobre esa lista.

**La forma canónica del HTML es una decisión, no una obviedad** (ADR-0021).
`CanonicalTable` no guarda `<thead>`/`<tbody>` ni distingue `<th>` de `<td>`, y
las tres cosas mueven el número: medido contra la referencia, un `<tbody>` de más
cuesta 0,333 en una tabla de una celda y un `<th>` donde va un `<td>` cuesta lo
mismo. Así que la forma se fija aquí y **el mismo render es el que se le da a la
referencia** cuando se generan los golden: lo que se valida es el algoritmo, no
la convención.
"""

from __future__ import annotations

from dataclasses import dataclass

from docbench_es.types import CanonicalCell, CanonicalTable


@dataclass(frozen=True)
class Nodo:
    """Un nodo del árbol de TEDS. `contenido` sólo lo llevan los `td`."""

    tag: str
    colspan: int | None
    rowspan: int | None
    contenido: tuple[str, ...] | None
    hijos: tuple[Nodo, ...]


def _celdas_por_fila(t: CanonicalTable) -> list[list[CanonicalCell]]:
    """Las celdas que ORIGINAN en cada fila, de izquierda a derecha.

    Un hueco es la **ausencia de un `<td>`**, exactamente como en el HTML de
    PubTabNet: una `<tr>` con menos celdas. Por eso no hace falta `holes()` para
    construir el árbol —el hueco no es un nodo que haya que omitir, es un nodo
    que nunca existió—, y por eso hueco y celda vacía puntúan distinto sin que
    TEDS tenga que saber nada de huecos.
    """
    filas: list[list[CanonicalCell]] = [[] for _ in range(max(t.n_rows, 0))]
    for celda in t.cells:
        if 0 <= celda.row < t.n_rows:
            filas[celda.row].append(celda)
    for fila in filas:
        fila.sort(key=lambda c: c.col)
    return filas


def _filas_de_cabecera(filas: list[list[CanonicalCell]]) -> int:
    """Cuántas filas van en `<thead>`: el prefijo máximo de filas de cabecera.

    Prefijo y no «todas las que sean cabecera» porque HTML exige `<thead>` antes
    de `<tbody>`: una fila de cabecera que apareciera en medio de la tabla no se
    puede mover sin cambiar el orden, y cambiar el orden cambiaría el árbol. Esa
    fila se queda en `<tbody>`, declarado y con test.
    """
    n = 0
    for fila in filas:
        if not fila or not all(c.is_header for c in fila):
            break
        n += 1
    return n


def a_arbol(t: CanonicalTable, *, solo_estructura: bool = False) -> Nodo:
    """El árbol de TEDS de una tabla canónica.

    `solo_estructura` vacía el contenido de todas las celdas, que es lo que hace
    TEDS-S: dos celdas con texto distinto pasan a ser idénticas y sólo se compara
    la forma de la rejilla.
    """
    filas = _celdas_por_fila(t)
    n_cabecera = _filas_de_cabecera(filas)

    def _tr(fila: list[CanonicalCell]) -> Nodo:
        celdas = tuple(
            Nodo(
                tag="td",
                colspan=c.colspan,
                rowspan=c.rowspan,
                contenido=() if solo_estructura else tuple(c.text),
                hijos=(),
            )
            for c in fila
        )
        return Nodo(tag="tr", colspan=None, rowspan=None, contenido=None, hijos=celdas)

    secciones: list[Nodo] = []
    if n_cabecera:
        secciones.append(Nodo("thead", None, None, None, tuple(_tr(f) for f in filas[:n_cabecera])))
    if filas[n_cabecera:]:
        secciones.append(Nodo("tbody", None, None, None, tuple(_tr(f) for f in filas[n_cabecera:])))
    return Nodo("table", None, None, None, tuple(secciones))


def n_nodos(nodo: Nodo) -> int:
    """Los DESCENDIENTES de la raíz, que es lo que normaliza la referencia.

    La raíz `<table>` no cuenta: `len(table.xpath(".//*"))` devuelve los
    descendientes. Contarla daría un denominador distinto y todos los números
    saldrían movidos.
    """
    return sum(1 + n_nodos(h) for h in nodo.hijos)


def _escapar(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def a_html(t: CanonicalTable) -> str:
    """La tabla en el HTML canónico de este proyecto, envuelto en `<html><body>`.

    Es lo que se le da a la implementación de referencia al generar los golden.
    El envoltorio no es decoración: la referencia hace `xpath('body/table')` y
    **devuelve 0.0 si no lo encuentra**, o sea que sin él todos los casos
    saldrían cero y el fixture parecería lleno de tablas rotas.

    Todas las celdas salen como `<td>`, nunca `<th>`: la referencia trata `<th>`
    como un nodo cualquiera —se baja a sus hijos y no le lee los spans—, así que
    un `<th>` cuesta un renombrado entero frente a un `<td>`. La condición de
    cabecera viaja en `<thead>`, que es como la escribe PubTabNet.
    """
    filas = _celdas_por_fila(t)
    n_cabecera = _filas_de_cabecera(filas)

    def _tr(fila: list[CanonicalCell]) -> str:
        celdas = "".join(
            "<td{}{}>{}</td>".format(
                f' colspan="{c.colspan}"' if c.colspan != 1 else "",
                f' rowspan="{c.rowspan}"' if c.rowspan != 1 else "",
                _escapar(c.text),
            )
            for c in fila
        )
        return f"<tr>{celdas}</tr>"

    partes = []
    if n_cabecera:
        partes.append("<thead>" + "".join(_tr(f) for f in filas[:n_cabecera]) + "</thead>")
    if filas[n_cabecera:]:
        partes.append("<tbody>" + "".join(_tr(f) for f in filas[n_cabecera:]) + "</tbody>")
    return f"<html><body><table>{''.join(partes)}</table></body></html>"
