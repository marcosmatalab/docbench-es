"""Que el comparador de L4 **detecta las cuatro formas de estar mal**, no una.

`scripts/comparar_verdad.py` decide si la verdad derivada reproduce las 30 tablas
transcritas a mano. Su silencio se lee como «la verdad es correcta», que es la
frase con la que se cierra el hito: **es una barrera, y de las que más pesan**.

**Cuatro mutaciones y no una.** Un comparador que sólo mirase dimensiones pasaría
un fixture con todo el texto cambiado; uno que sólo mirase texto pasaría una tabla
con las celdas movidas de columna —que es **exactamente el bug que apareció hoy**
en `BOE-A-2026-7193`, donde los importes caían una columna a la derecha y `validate`
decía `ok=True`—. Cada mutación cubre una clase que las otras no ven.

**Y el aro en la dirección buena**, sin el cual las cuatro las pasaría un comparador
que dijera «no» a cualquier cosa. Mismo argumento que `siempre_ok` contra
`siempre_roto` en el arnés de mutantes.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from comparar_verdad import comparar  # noqa: E402

from docbench_es.types import CanonicalCell, CanonicalTable  # noqa: E402

FIXTURE: dict[str, object] = {
    "external_id": "PRUEBA",
    "tabla": 0,
    "alcance": "completa",
    "dimension": {"n_rows": 3, "n_cols": 2},
    "spans": [],
    "filas": [["Cabecera", "Euros"], ["Uno.", "1,00"], ["Dos.", "2,00"]],
}
"""Una tabla de tres por dos, con su verdad exacta abajo. Pequeña a propósito: lo
que hay que demostrar es qué detecta el comparador, no que aguante una tabla larga."""


def _verdad(*celdas: CanonicalCell, filas: int = 3, cols: int = 2) -> CanonicalTable:
    return CanonicalTable(celdas, filas, cols, (1, 1), None, True, "html")


BUENA = _verdad(
    CanonicalCell(0, 0, 1, 1, "Cabecera", True),
    CanonicalCell(0, 1, 1, 1, "Euros", True),
    CanonicalCell(1, 0, 1, 1, "Uno."),
    CanonicalCell(1, 1, 1, 1, "1,00"),
    CanonicalCell(2, 0, 1, 1, "Dos."),
    CanonicalCell(2, 1, 1, 1, "2,00"),
)


def test_una_verdad_identica_al_fixture_no_da_discrepancias() -> None:
    """**El aro en la dirección buena, y va primero.**

    Sin él, los cuatro de abajo los pasaría un comparador que devolviera una
    discrepancia ante cualquier entrada — y entonces el «N de 30» del hito sería
    un cero disfrazado de medición.
    """
    assert comparar(FIXTURE, BUENA) == []


def test_una_celda_con_el_texto_cambiado_se_detecta() -> None:
    """La clase obvia, y la que un comparador de dimensiones no ve."""
    mala = _verdad(
        CanonicalCell(0, 0, 1, 1, "Cabecera", True),
        CanonicalCell(0, 1, 1, 1, "Euros", True),
        CanonicalCell(1, 0, 1, 1, "Uno."),
        CanonicalCell(1, 1, 1, 1, "9,99"),
        CanonicalCell(2, 0, 1, 1, "Dos."),
        CanonicalCell(2, 1, 1, 1, "2,00"),
    )

    ds = comparar(FIXTURE, mala)

    assert [d.clase for d in ds] == ["TEXTO"]
    assert "'1,00'" in ds[0].detalle and "'9,99'" in ds[0].detalle


def test_una_celda_movida_de_columna_se_detecta() -> None:
    """**El bug de hoy, convertido en control.**

    En `BOE-A-2026-7193` los dos importes de la primera fila de tarifas caían en
    las columnas 3 y 4 y los de las demás en la 2 y la 3. La tabla estaba bien
    formada, `validate` decía `ok=True`, y **el contenido era el mismo**: un
    comparador que sólo mirase el conjunto de textos habría dicho que reproduce.
    """
    movida = _verdad(
        CanonicalCell(0, 0, 1, 1, "Cabecera", True),
        CanonicalCell(0, 1, 1, 1, "Euros", True),
        CanonicalCell(1, 1, 1, 1, "Uno."),
        CanonicalCell(1, 0, 1, 1, "1,00"),
        CanonicalCell(2, 0, 1, 1, "Dos."),
        CanonicalCell(2, 1, 1, 1, "2,00"),
    )

    ds = comparar(FIXTURE, movida)

    assert [d.clase for d in ds] == ["TEXTO", "TEXTO"], "las dos posiciones, no una"
    assert "(1, 0)" in ds[0].detalle and "(1, 1)" in ds[1].detalle


def test_una_fila_que_falta_se_detecta() -> None:
    """Una tabla a la que le falta la última fila **tiene el resto correcto**, así
    que sólo la ve quien compara posiciones y dimensión, no quien compara textos."""
    corta = _verdad(
        CanonicalCell(0, 0, 1, 1, "Cabecera", True),
        CanonicalCell(0, 1, 1, 1, "Euros", True),
        CanonicalCell(1, 0, 1, 1, "Uno."),
        CanonicalCell(1, 1, 1, 1, "1,00"),
        filas=2,
    )

    clases = [d.clase for d in comparar(FIXTURE, corta)]

    assert "DIMENSION" in clases
    assert clases.count("ESTADO") == 2, "las dos posiciones de la fila que falta"


def test_la_dimension_cambiada_se_detecta_aunque_el_contenido_cuadre() -> None:
    """La dimensión declarada es un dato, no una consecuencia.

    Ésta es la clase que salvó el hito: `n_rows` mal era el síntoma del grupo de
    filas sin cerrar, y el contenido de las primeras filas coincidía.
    """
    ancha = _verdad(*BUENA.cells, cols=3)

    ds = comparar(FIXTURE, ancha)

    assert [d.clase for d in ds] == ["DIMENSION"]
    assert "3x2" in ds[0].detalle and "3x3" in ds[0].detalle
