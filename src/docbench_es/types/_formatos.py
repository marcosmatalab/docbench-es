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

FORMATOS_SIN_SPANS = frozenset({"markdown", "dataframe", "text"})
"""Los que no pueden con `rowspan` por construcción del formato (ADR-0006).

**`dataframe` faltaba aquí, y era un agujero que apuntaba a `camelot`.** Un `DataFrame`
es una rejilla rectangular: no tiene `rowspan` ni `colspan`, y un `MultiIndex` se
*pinta* como cabecera combinada pero el objeto no distingue «combinada» de «repetida».
`core.canonical._dataframe` lo dice en su primera línea y pone `expresses_spans=False`,
pero esta lista no lo incluía, así que **una tabla con `source_format="dataframe"` podía
declararse capaz y `is_wellformed()` la daba por buena** —comprobado—. Y `camelot`, que
devuelve marcos, está en la campaña de los 616: habría competido en el estrato de celdas
combinadas cobrando ceros en vez de salir `NO_APLICABLE`.
"""

FORMATOS_CON_SPANS = frozenset({"html", "tei"})
"""Los que sí pueden. **Lista POSITIVA, y enumerada a mano a propósito.**

Podría derivarse como `set(FORMATOS_CANONICOS) - FORMATOS_SIN_SPANS`, y sería el mismo
conjunto hoy y **el bug de mañana**: un sexto formato canónico entraría solo en la lista
de los que sí, o sea que lo desconocido se concedería spans por defecto. Enumerando las
dos, un formato sin clasificar no cae en ninguna y `test_types.py` se pone rojo pidiendo
que alguien decida. **Lo desconocido no se decide por defecto**, que es la misma regla
que ya hace cumplir `HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO`.

**Y las dos listas no son la última palabra: la tienen los cinco conversores.**
`expresses_spans` lo fija el conversor, así que estas constantes son una *afirmación
sobre lo que hacen*, y una afirmación se comprueba: `test_canonical_conversores.py`
ejecuta los cinco sobre una tabla mínima y exige que coincidan. Sin ese test, esta lista
y el código podían decir cosas distintas — y durante cuatro hitos las dijeron.
"""
