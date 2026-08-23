"""El ancla de un documento publicado aparece EXACTAMENTE UNA VEZ, o no se edita.

**La clase de fallo que mata, no el caso.** Editar `RESULTS.md` por búsqueda de
texto —`s.index("### El coste en la puerta")`— tiene dos formas de salir mal, y
sólo una se ve:

| El ancla aparece | Qué hace `s.index` | Se nota |
|---|---|---|
| **más de una vez** | corta por la PRIMERA y **duplica** | sí: el texto sale dos veces |
| **cero veces** | revienta; con `find()`, da -1 y **borra** | **no**: nadie echa en falta |

En L2 pasó la primera: «### El coste en la puerta» era también un encabezado de
L1, anterior al punto de corte, y se duplicaron ~230 líneas. Se cazó porque
duplicar es la mitad visible. La otra mitad —borrar— no se caza leyendo, y por eso
la comprobación no puede ser «revisa el resultado» sino **una precondición que
aborta antes de escribir**.

    from ancla import unica          # scripts/ en el PYTHONPATH
    corte = unica(s, "### Los mutantes")

**Quién tiene que usarlo:** todo script que edite un documento publicado
—`RESULTS.md`, `LIMITS.md`, `ESTADO.md`, `CHANGELOG.md`, `docs/metrics.md`— por
búsqueda de texto. Hoy **ningún script versionado lo hace**: el que rompió
`RESULTS.md` era un script de un solo uso, y ésos son justo los que nadie revisa.
Por eso esto vive en el repo y no en un scratchpad, y por eso `tests/unit/
test_ancla.py` lo fija: para que el de un solo uso tenga de dónde importarlo.
"""

from __future__ import annotations


def unica(texto: str, ancla: str) -> int:
    """Índice de `ancla`, exigiendo que aparezca **una sola vez**. Si no, aborta."""
    veces = texto.count(ancla)
    if veces != 1:
        raise SystemExit(f"el ancla {ancla!r} aparece {veces} veces, no 1: no se edita nada")
    return texto.index(ancla)
