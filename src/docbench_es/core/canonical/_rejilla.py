"""El colocador fila a fila del estándar HTML. Lo comparten `from_html` y `from_tei`.

Los dos formatos que expresan spans colocan igual: un cursor por fila que avanza
de izquierda a derecha **saltando lo que ya ocupa un `rowspan` de arriba**. Es lo
que hace un navegador, y es lo que hace que un hueco sólo pueda aparecer al final
de una fila —de ahí la definición de hueco interior de ADR-0018.

**El colocador SÍ puede producir un solape, y lo hace a propósito.** El estándar
coloca la celda en el primer hueco libre de su PRIMERA columna y, si alguna de las
siguientes ya está ocupada, declara *table model error* y las celdas se pisan.
Este colocador hace lo mismo: no busca una ventana libre del ancho de la celda ni
la desplaza más allá, porque las dos cosas serían reparar en silencio un HTML
roto. El solape sale en `cells` y lo caza `validate()`. Corregido en el escrutinio
de L1: la primera versión de este docstring y el límite 30 afirmaban lo contrario.

**La ocupación se guarda por COLUMNA, no posición a posición.** `ocupada_hasta[c]`
es la primera fila libre de la columna `c`. Con un `set` de posiciones, un
`<td rowspan="65534" colspan="1000">` —60 bytes de HTML— materializaba 65 millones
de tuplas: 37 s y 7,5 GB para devolver una tabla de una celda. Así cuesta O(ancho)
por celda y O(columnas) de memoria, y el span absurdo se cuenta igual como
`SPAN_FUERA_DE_RANGO` cuando `validate` lo compara con las filas que había.
"""

from __future__ import annotations

from dataclasses import dataclass

from docbench_es.types import CanonicalCell

MAX_COLSPAN = 1000
"""Tope del estándar HTML. Un `colspan` mayor es basura, no una tabla ancha."""

MAX_ROWSPAN = 65534
"""Tope del estándar HTML."""

_SIN_CERRAR = -1
"""`rowspan="0"`: ocupa hasta el final de su sección, que aún no se conoce."""


@dataclass
class _Registro:
    """Una celda mientras se coloca. Mutable porque `rowspan=0` se resuelve al final."""

    fila: int
    col: int
    rowspan: int
    colspan: int
    texto: str
    is_header: bool


@dataclass(frozen=True)
class _Pendiente:
    """Una celda con `rowspan="0"`: baja hasta el final de su sección."""

    indice: int
    col: int
    colspan: int


class Colocador:
    """Acumula celdas fila a fila y devuelve la rejilla ya resuelta."""

    def __init__(self) -> None:
        self._ocupada_hasta: dict[int, int] = {}
        self._registros: list[_Registro] = []
        self._pendientes: list[_Pendiente] = []
        self._fila = -1
        self._cursor = 0

    @property
    def n_filas(self) -> int:
        """Las filas VISTAS, no la extensión de las celdas.

        Una `<tr></tr>` al final es HTML legal y cuenta como fila: por eso
        `n_rows` puede pasarse de donde llegan las celdas, y por eso `FILA_VACIA`
        es informativo y no fatal.
        """
        return self._fila + 1

    def _libre(self, col: int, fila: int) -> bool:
        hasta = self._ocupada_hasta.get(col, 0)
        return hasta != _SIN_CERRAR and hasta <= fila

    def cerrar_seccion(self) -> None:
        """`<thead>`, `<tbody>`, `<tfoot>`: resuelve los `rowspan="0"` abiertos."""
        for pendiente in self._pendientes:
            registro = self._registros[pendiente.indice]
            registro.rowspan = self._fila - registro.fila + 1
            for col in range(pendiente.col, pendiente.col + pendiente.colspan):
                self._ocupada_hasta[col] = self._fila + 1
        self._pendientes.clear()

    def nueva_fila(self) -> None:
        self._fila += 1
        self._cursor = 0

    def colocar(self, texto: str, *, is_header: bool, rowspan: int, colspan: int) -> None:
        """Coloca una celda en la primera posición libre a la derecha del cursor.

        `rowspan=0` es HTML legal y significa «hasta el final de la sección»: se
        anota como pendiente y se resuelve en `cerrar_seccion`. Cualquier otro
        valor menor que 1 —negativo, o basura que no era número— vale 1, que es
        lo que manda el estándar al parsear un entero no negativo.
        """
        if self._fila < 0:
            self.nueva_fila()  # <td> sin <tr>: el HTML tolerante lo permite
        ancho = min(max(colspan, 1), MAX_COLSPAN)
        hasta_el_final = rowspan == 0
        alto = 1 if hasta_el_final else min(max(rowspan, 1), MAX_ROWSPAN)

        while not self._libre(self._cursor, self._fila):
            self._cursor += 1
        col = self._cursor
        # Sólo se comprueba la PRIMERA columna, como el estándar: si las demás
        # están ocupadas, es un table model error y las celdas se pisan. Lo caza
        # `validate` como SOLAPE; repararlo aquí sería esconderlo.
        fin = _SIN_CERRAR if hasta_el_final else self._fila + alto
        for columna in range(col, col + ancho):
            if fin == _SIN_CERRAR or self._ocupada_hasta.get(columna, 0) != _SIN_CERRAR:
                self._ocupada_hasta[columna] = fin

        self._registros.append(_Registro(self._fila, col, alto, ancho, texto, is_header))
        if hasta_el_final:
            self._pendientes.append(_Pendiente(len(self._registros) - 1, col, ancho))
        self._cursor = col + ancho

    def terminar(self) -> tuple[tuple[CanonicalCell, ...], int, int]:
        """Devuelve `(celdas, n_rows, n_cols)`. `n_cols` se DERIVA de la extensión.

        Derivar `n_cols` en vez de creerse un `<colgroup>` es lo que hace
        imposible una `COLUMNA_VACIA`: no hay forma de declarar más columnas de
        las que se usan.
        """
        self.cerrar_seccion()
        celdas = tuple(
            CanonicalCell(
                row=r.fila,
                col=r.col,
                rowspan=r.rowspan,
                colspan=r.colspan,
                text=r.texto,
                is_header=r.is_header,
            )
            for r in self._registros
        )
        n_cols = max((c.col + c.colspan for c in celdas), default=0)
        return celdas, self.n_filas, n_cols
