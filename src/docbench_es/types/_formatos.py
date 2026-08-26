"""§6.2 · Los cinco formatos canónicos, y cuáles de ellos pueden con `rowspan`.

Salen de `_invariantes.py` porque son **el vocabulario** y aquél son **las
comprobaciones**: dos responsabilidades, y juntas pasaban de 300 líneas.

Y porque el vocabulario tiene ahora una propiedad propia que hay que poder afirmar sola:
los dos grupos de spans **particionan** los canónicos. Lo hace cumplir
`tests/unit/test_types.py`, en las tres direcciones —que cubren todo, que no se solapan,
y que no clasifican nada que no sea canónico—.
"""

from __future__ import annotations

__all__ = ["FORMATOS_CANONICOS", "FORMATOS_CON_SPANS", "FORMATOS_SIN_SPANS"]

FORMATOS_CANONICOS = ("html", "markdown", "dataframe", "tei", "text")
"""Los cinco de §6.2. Un sexto valor es un conversor que nadie declaró."""

FORMATOS_SIN_SPANS = frozenset({"markdown", "text"})
"""Los que no pueden con `rowspan` por construcción del formato (ADR-0006)."""

FORMATOS_CON_SPANS = frozenset({"html", "dataframe", "tei"})
"""Los que sí pueden. **Lista POSITIVA, y enumerada a mano a propósito.**

Podría derivarse como `set(FORMATOS_CANONICOS) - FORMATOS_SIN_SPANS`, y sería el mismo
conjunto hoy y **el bug de mañana**: un sexto formato canónico entraría solo en la lista
de los que sí, o sea que lo desconocido se concedería spans por defecto. Enumerando las
dos, un formato sin clasificar no cae en ninguna y `test_types.py` se pone rojo pidiendo
que alguien decida. **Lo desconocido no se decide por defecto**, que es la misma regla
que ya hace cumplir `HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO`.
"""
