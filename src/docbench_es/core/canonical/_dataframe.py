"""§9.1 · `from_dataframe`. **`expresses_spans=False`**, y eso tiene precio.

Un `DataFrame` es una rejilla rectangular: no tiene `rowspan` ni `colspan`. Un
`MultiIndex` se PINTA como cabecera combinada, pero el objeto no distingue
«combinada» de «repetida», así que declararlo capaz sería declararlo capaz de
algo que no puede.

ADR-0006 ya lo dice al listar «Camelot devuelve DataFrames» entre los formatos
que pierden las celdas combinadas. **El precio, que va en LIMITS 35 como
requisito de L5 y no como recordatorio:** camelot sale `NO_APLICABLE` en el 63%
de las tablas de las secciones I+III, o sea con una cobertura evaluable en torno
al 37%, y su nota no se puede enseñar sin esa cobertura al lado.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import Protocol, runtime_checkable

from docbench_es.core.canonical._normalizar import normalize_cell_text
from docbench_es.types import CanonicalCell, CanonicalTable


@runtime_checkable
class MarcoDeDatos(Protocol):
    """La superficie mínima de un DataFrame: `columns` e `itertuples`.

    No se importa pandas: el núcleo es puro y no depende de nada del extra
    `extract-local`. Basta con la forma.

    **`index` va en la firma y no sobra.** `DataFrame.itertuples()` lleva
    `index=True` por defecto y devuelve el índice como primer elemento de cada
    tupla: una columna MÁS que `columns`. Sin pasar `index=False`, cada fila de
    datos se desplazaba una columna, el índice entraba como contenido y `n_cols`
    salía +1 — en TODAS las tablas de camelot, que es uno de los cuatro
    extractores de `make quickstart`. No lo cazaba ningún test porque pandas no
    está instalado en la puerta y el doble de test implementaba la variante sin
    índice. Encontrado en el escrutinio de L1.
    """

    @property
    def columns(self) -> Sequence[object]: ...

    def itertuples(self, index: bool = ...) -> Iterator[tuple[object, ...]]: ...


def _son_posiciones(etiquetas: list[object]) -> bool:
    """Si las etiquetas de columna son 0, 1, 2… o sea un `RangeIndex` de pandas.

    Se mira el tipo `int` y no el texto: una tabla con cabeceras `"0"`, `"1"`
    escritas de verdad en el documento son cadenas y no caen aquí.
    """
    return bool(etiquetas) and all(
        isinstance(e, int) and not isinstance(e, bool) and e == i for i, e in enumerate(etiquetas)
    )


def _texto(valor: object) -> str:
    """Un valor de celda a texto. `None` y `NaN` son celda VACÍA, no hueco.

    `NaN` se detecta con `valor != valor`, que es cierto sólo para él, para no
    importar numpy en el núcleo puro.
    """
    if valor is None or valor != valor:  # NaN es el unico distinto de si mismo
        return ""
    return normalize_cell_text(str(valor))


def from_dataframe(
    dfs: Iterable[object], *, page_span: tuple[int, int] = (1, 1)
) -> list[CanonicalTable]:
    """Una tabla por marco, con `columns` como fila de cabecera.

    Lanza `TypeError` si lo que llega no tiene la superficie de un marco: pasar
    una lista de listas es un error de programación del extractor, no un
    documento difícil, y tragárselo devolvería cero tablas y contaría el
    documento como «sin tablas».
    """
    tablas: list[CanonicalTable] = []
    for df in dfs:
        if not isinstance(df, MarcoDeDatos):
            raise TypeError(
                f"{type(df).__name__} no tiene la superficie de un DataFrame "
                f"(hacen falta `columns` e `itertuples`)"
            )
        # `camelot` devuelve marcos con `RangeIndex`: las etiquetas de columna son
        # 0, 1, 2… y NO están en el documento. Emitirlas como fila de cabecera
        # inventaría una fila de contenido en CADA tabla suya. Se declara que no
        # hay cabecera, que es lo único que de verdad se sabe. Ver LIMITS 36.
        etiquetas = list(df.columns)
        cabecera = None if _son_posiciones(etiquetas) else [_texto(c) for c in etiquetas]
        filas = [[_texto(v) for v in fila] for fila in df.itertuples(index=False)]
        todas = filas if cabecera is None else [cabecera, *filas]
        hay_cabecera = cabecera is not None
        celdas = tuple(
            CanonicalCell(row=f, col=c, text=texto, is_header=hay_cabecera and f == 0)
            for f, fila in enumerate(todas)
            for c, texto in enumerate(fila)
        )
        tablas.append(
            CanonicalTable(
                cells=celdas,
                n_rows=len(todas),
                n_cols=max((len(f) for f in todas), default=0),
                page_span=page_span,
                caption=None,
                expresses_spans=False,
                source_format="dataframe",
            )
        )
    return tablas
