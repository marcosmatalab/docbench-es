"""§6.2 · Los invariantes de `CanonicalTable`, y el enum cerrado de sus fallos.

**Por qué esto vive en `types` y no en `core.canonical`, que es donde §9.1 pone
`validate()`.** El contrato de capas de `.importlinter` pone `core` POR ENCIMA de
`types : errors`, así que `types` no puede importar `core` —y no vale ni con un
import diferido dentro de la función, porque `lint-imports` lee el AST—. Pero
§6.2 exige que `CanonicalTable.is_wellformed()` exista como método. Las dos cosas
sólo son compatibles de una manera: el algoritmo vive aquí, junto a los datos que
inspecciona, y `core.canonical.validate()` es la puerta pública que §9.1 manda,
delegando. La alternativa —escribir la comprobación dos veces— dejaría dos
fuentes de verdad sobre la misma tabla. Ver ADR-0019.

**Fatal contra informativo.** No todo hallazgo invalida: `<tr></tr>` es HTML legal
y una fila corta es cotidiana en el BOE. Lo que separa las dos listas no es el
gusto, es **qué puede producir un formato de origen**: lo que ningún formato puede
generar es un bug del conversor disfrazado de tabla plausible, y sale fatal.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para el tipado; en runtime sería circular
    from docbench_es.types._tabla import CanonicalCell, CanonicalTable

FORMATOS_CANONICOS = ("html", "markdown", "dataframe", "tei", "text")
"""Los cinco de §6.2. Un sexto valor es un conversor que nadie declaró."""

FORMATOS_SIN_SPANS = frozenset({"markdown", "text"})
"""Los que no pueden con `rowspan` por construcción del formato (ADR-0006)."""


class HallazgoTabla(StrEnum):
    """El enum cerrado de lo que le puede pasar a una tabla canónica.

    Cerrado y no cadenas libres por lo mismo que `ExtractionFailure`: un hallazgo
    que no se puede contar no aparece en ningún informe, y la tasa de tablas mal
    formadas por extractor es un resultado de L5, no un detalle de implementación.
    """

    # ── Fatales: ningún formato de origen puede producirlos ──────────────
    SOLAPE = "SOLAPE"
    SPAN_FUERA_DE_RANGO = "SPAN_FUERA_DE_RANGO"
    SPAN_MENOR_QUE_UNO = "SPAN_MENOR_QUE_UNO"
    POSICION_NEGATIVA = "POSICION_NEGATIVA"
    DIMENSION_INCOHERENTE = "DIMENSION_INCOHERENTE"
    HUECO_INTERIOR = "HUECO_INTERIOR"
    COLUMNA_VACIA = "COLUMNA_VACIA"
    PAGE_SPAN_INVALIDO = "PAGE_SPAN_INVALIDO"
    EXPRESSES_SPANS_IMPOSIBLE = "EXPRESSES_SPANS_IMPOSIBLE"
    # ── Informativos: legales, pero se declaran siempre ──────────────────
    HUECO_COLA = "HUECO_COLA"
    FILA_VACIA = "FILA_VACIA"
    SOURCE_FORMAT_DESCONOCIDO = "SOURCE_FORMAT_DESCONOCIDO"

    @property
    def es_fatal(self) -> bool:
        """Si invalida la tabla. Los informativos se reportan con `ok=True`."""
        return self not in _INFORMATIVOS


_INFORMATIVOS = frozenset(
    {
        HallazgoTabla.HUECO_COLA,
        HallazgoTabla.FILA_VACIA,
        HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO,
    }
)


def _di(codigo: HallazgoTabla, detalle: str) -> str:
    """El formato de un hallazgo: `CODIGO: detalle`.

    §9.1 fija la firma en `list[str]`, así que el código va **dentro** de la
    cadena y no en un objeto aparte. Con el prefijo, los tests afirman sobre el
    enum y no sobre la prosa, que es lo que hace que cambiar un mensaje no rompa
    la suite.
    """
    return f"{codigo}: {detalle}"


def _cabecera(t: CanonicalTable, problemas: list[str]) -> None:
    """Lo que se puede comprobar sin mirar ni una celda."""
    if t.source_format not in FORMATOS_CANONICOS:
        problemas.append(
            _di(
                HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO,
                f"{t.source_format!r} no es uno de los cinco de §6.2",
            )
        )
    primera, ultima = t.page_span
    if primera < 1 or ultima < primera:
        problemas.append(
            _di(
                HallazgoTabla.PAGE_SPAN_INVALIDO,
                f"page_span={t.page_span}: es (primera, última) y va en 1 o más",
            )
        )
    if t.n_rows < 0 or t.n_cols < 0:
        problemas.append(
            _di(HallazgoTabla.DIMENSION_INCOHERENTE, f"{t.n_rows}x{t.n_cols}: negativa")
        )
    elif t.cells and (t.n_rows < 1 or t.n_cols < 1):
        problemas.append(
            _di(
                HallazgoTabla.DIMENSION_INCOHERENTE,
                f"{len(t.cells)} celdas en una tabla de {t.n_rows}x{t.n_cols}",
            )
        )


def _colocar(
    t: CanonicalTable, problemas: list[str]
) -> tuple[dict[tuple[int, int], int], dict[int, int], int]:
    """Estampa cada celda en la rejilla y caza lo que no cabe o se pisa.

    Devuelve la rejilla, la columna de origen más a la derecha por fila, y
    **cuántas celdas hubo que descartar** por no poder colocarlas.
    """
    rejilla: dict[tuple[int, int], int] = {}
    ultimo_origen: dict[int, int] = {}
    descartadas = 0
    for i, celda in enumerate(t.cells):
        if not _celda_sana(celda, t, i, problemas):
            descartadas += 1
            continue
        for fila in range(celda.row, celda.row + celda.rowspan):
            for col in range(celda.col, celda.col + celda.colspan):
                previa = rejilla.get((fila, col))
                if previa is not None:
                    problemas.append(
                        _di(
                            HallazgoTabla.SOLAPE,
                            f"celdas {previa} y {i} se pisan en ({fila},{col})",
                        )
                    )
                else:
                    rejilla[fila, col] = i
        ultimo_origen[celda.row] = max(ultimo_origen.get(celda.row, -1), celda.col)
    return rejilla, ultimo_origen, descartadas


def _celda_sana(celda: CanonicalCell, t: CanonicalTable, i: int, problemas: list[str]) -> bool:
    """Posición y spans de una celda suelta. `False` si no se puede estampar."""
    if celda.row < 0 or celda.col < 0:
        problemas.append(
            _di(HallazgoTabla.POSICION_NEGATIVA, f"celda {i} en ({celda.row},{celda.col})")
        )
        return False
    if celda.rowspan < 1 or celda.colspan < 1:
        problemas.append(
            _di(
                HallazgoTabla.SPAN_MENOR_QUE_UNO,
                f"celda {i}: rowspan={celda.rowspan}, colspan={celda.colspan}. "
                f"No cubre ninguna posición y es invisible para cell_at",
            )
        )
        return False
    if celda.row + celda.rowspan > t.n_rows or celda.col + celda.colspan > t.n_cols:
        problemas.append(
            _di(
                HallazgoTabla.SPAN_FUERA_DE_RANGO,
                f"celda {i} llega a ({celda.row + celda.rowspan},"
                f"{celda.col + celda.colspan}) en una tabla de {t.n_rows}x{t.n_cols}",
            )
        )
        return False
    return True


def _spans_declarados(t: CanonicalTable, problemas: list[str]) -> None:
    """La regla que no se relaja: `expresses_spans` lo fija el formato de origen.

    Se caza en las dos direcciones. Declararse capaz sin serlo es la que
    beneficia al extractor —pasa de `NO_APLICABLE` a competir en el estrato
    titular—, pero declararse incapaz trayendo celdas combinadas también miente, y
    de esa se aprovecharía quien quisiera esconderse en `NO_APLICABLE`.
    """
    combinadas = [i for i, c in enumerate(t.cells) if c.rowspan > 1 or c.colspan > 1]
    if combinadas and not t.expresses_spans:
        problemas.append(
            _di(
                HallazgoTabla.EXPRESSES_SPANS_IMPOSIBLE,
                f"expresses_spans=False con celdas combinadas: {combinadas}",
            )
        )
    if t.expresses_spans and t.source_format in FORMATOS_SIN_SPANS:
        problemas.append(
            _di(
                HallazgoTabla.EXPRESSES_SPANS_IMPOSIBLE,
                f"expresses_spans=True desde {t.source_format!r}, que no puede con rowspan",
            )
        )


def _cobertura(
    t: CanonicalTable,
    rejilla: dict[tuple[int, int], int],
    ultimo_origen: dict[int, int],
    problemas: list[str],
) -> None:
    """Huecos, filas vacías y columnas vacías sobre la rejilla ya estampada.

    **La definición de hueco interior, que es la decisión de ADR-0018.** Un hueco
    en `(f,c)` es INTERIOR si alguna celda **origina en la fila `f`** a la derecha
    de `c`. No vale mirar si la POSICIÓN de la derecha está ocupada: puede estarla
    por un `rowspan` que baja de una fila de arriba, y eso es HTML legal que el
    navegador pinta sin quejarse. Con un 42% de tablas del BOE con `rowspan`, esa
    otra lectura rechazaría corpus real.

    Los mensajes van agregados por fila —uno por fila, no uno por posición—
    porque con `colspan` de hasta 33 una tabla ancha generaría cientos de líneas
    idénticas. Las posiciones exactas las da `huecos()`, que es lo que consume L2.
    """
    for fila in range(t.n_rows):
        cola: list[int] = []
        interiores: list[int] = []
        cubiertas = 0
        for col in range(t.n_cols):
            if (fila, col) in rejilla:
                cubiertas += 1
            elif col < ultimo_origen.get(fila, -1):
                interiores.append(col)
            else:
                cola.append(col)
        if cubiertas == 0:
            problemas.append(
                _di(HallazgoTabla.FILA_VACIA, f"fila {fila} sin una sola posición cubierta")
            )
            continue
        if interiores:
            problemas.append(
                _di(
                    HallazgoTabla.HUECO_INTERIOR,
                    f"fila {fila}, columnas {interiores}: hueco a la izquierda de una "
                    f"celda que origina en esa misma fila",
                )
            )
        if cola:
            problemas.append(
                _di(HallazgoTabla.HUECO_COLA, f"fila {fila}, columnas {cola}: fila corta")
            )
    for col in range(t.n_cols):
        if not any((fila, col) in rejilla for fila in range(t.n_rows)):
            problemas.append(
                _di(
                    HallazgoTabla.COLUMNA_VACIA,
                    f"columna {col} sin una sola celda: n_cols se calculó de más",
                )
            )


def comprobar(t: CanonicalTable) -> tuple[bool, list[str]]:
    """Los invariantes de §6.2. `ok` es False si hay algún hallazgo FATAL.

    Determinista: cabecera, celdas en el orden de `cells`, y la rejilla en orden
    de fila y columna. Dos corridas sobre la misma tabla dan la misma lista.
    """
    problemas: list[str] = []
    _cabecera(t, problemas)
    rejilla, ultimo_origen, descartadas = _colocar(t, problemas)
    _spans_declarados(t, problemas)
    if not descartadas:
        # **No se analiza la cobertura de una rejilla cuyas celdas no se han
        # podido colocar.** Con una celda descartada —span degenerado, fuera de
        # rango o posición negativa— no se sabe qué área ocupaba, así que todo
        # hueco, fila vacía o columna vacía que salga es una consecuencia de ese
        # defecto y no un hallazgo propio. Un solo `colspan=0` llegaba a producir
        # cuatro códigos: se arregla el span, se vuelve a validar y salen los que
        # queden. Un defecto, un código. Encontrado en el escrutinio de L1.
        _cobertura(t, rejilla, ultimo_origen, problemas)
    ok = not any(HallazgoTabla(p.split(":", 1)[0]).es_fatal for p in problemas)
    return ok, problemas
