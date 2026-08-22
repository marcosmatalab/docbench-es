"""§9.1 · `from_tei` y `from_text_heuristic`: el que SÍ expresa spans y el que no.

Separado de `test_canonical_conversores.py` por el límite de 300 líneas de
`CLAUDE.md`. Los dos comparten algo que no es casualidad: son los conversores de
los dos extractores que no leen PDF de la forma habitual —GROBID, que es un
servicio, y la familia OCR—, y los dos están en los extremos de lo que un formato
puede expresar.
"""

from __future__ import annotations

import pytest

from docbench_es.core.canonical import from_tei, from_text_heuristic, validate

TEI = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>
<table><head>Cuadro 1</head>
<row role="label"><cell cols="2">Retribuciones</cell></row>
<row><cell rows="2">Grupo 3</cell><cell>1.234,56</cell></row>
<row><cell>200,00</cell></row>
</table></body></text></TEI>"""

TEXTO_OCR = """
Grupo      Base        Complemento
3          1.234,56    200,00
4          1.100,00    150,00
"""


def test_tei_expresa_spans_porque_su_formato_puede() -> None:
    """Demuestra que TEI sí lleva `rowspan`, y que por eso GROBID compite.

    `<cell rows= cols=>` es exactamente `rowspan`/`colspan`. Marcar TEI como
    incapaz mandaría a GROBID a `NO_APLICABLE` en el 63% de los documentos con tabla del BOE
    sin motivo, que es la injusticia simétrica a la que ADR-0006 evita.
    """
    (t,) = from_tei(TEI)
    assert t.expresses_spans is True
    assert t.source_format == "tei"
    assert t.caption == "Cuadro 1"
    assert (t.n_rows, t.n_cols) == (3, 2)

    cabecera = t.cell_at(0, 0)
    assert cabecera is not None and cabecera.colspan == 2 and cabecera.is_header is True

    grupo = t.cell_at(1, 0)
    assert grupo is not None and grupo.rowspan == 2
    assert t.cell_at(2, 0) is grupo, "el rowspan baja"
    # La celda de la tercera fila se coloca a la DERECHA de lo que ya ocupa el
    # rowspan, como hace un navegador. Si el colocador no lo hiciera, saldría un
    # solape o un hueco interior, y los dos son fatales.
    resto = t.cell_at(2, 1)
    assert resto is not None and resto.text == "200,00"
    assert validate(t)[0] is True


def test_tei_rechaza_el_doctype() -> None:
    """Demuestra que el núcleo no expande entidades de una entrada ajena.

    El TEI lo produce GROBID, que es un servicio externo, y un `<!DOCTYPE>` con
    entidades anidadas es la bomba de expansión clásica. Se rechaza antes de
    parsear en vez de meter `defusedxml` en el núcleo puro.
    """
    with pytest.raises(ValueError, match="DOCTYPE"):
        from_tei('<!DOCTYPE t [<!ENTITY a "aaa">]><TEI><table></table></TEI>')


def test_el_heuristico_de_texto_es_deliberadamente_tonto() -> None:
    """Demuestra dónde está la frontera de la regla de oro 1.

    `from_text_heuristic` no lee PDF, así que no es un extractor. Pero es el juez
    haciendo detección de tablas por cuenta del concursante, y por eso se queda
    tonto a propósito: separadores fijos, cero inferencia de fusiones, y
    **devuelve lista vacía antes que inventarse una tabla**.
    """
    (t,) = from_text_heuristic(TEXTO_OCR)
    assert t.expresses_spans is False
    assert t.source_format == "text"
    assert (t.n_rows, t.n_cols) == (3, 3)
    celda = t.cell_at(1, 1)
    assert celda is not None and celda.text == "1.234,56"

    assert from_text_heuristic("una linea suelta sin columnas") == []

    # Este es el caso de anchuras inconsistentes DE VERDAD: dos filas seguidas,
    # una de tres columnas y otra de dos. La versión anterior de este test usaba
    # "a  b\nsolo una columna aqui\nc  d", que NO llega a esa rama: la línea del
    # medio parte el bloque en dos de una sola fila y los descarta el mínimo de
    # filas. Pasaba en verde por un motivo distinto del que decía, y habría
    # seguido pasando con la comprobación de anchuras borrada.
    assert from_text_heuristic("a  b  c\nd  e") == [], (
        "columnas inconsistentes: antes lista vacía que una tabla inventada"
    )
