"""§12 · Los DOS sellos, y qué hacer cuando no coinciden.

Una corrida y su informe son **dos actos separados en el tiempo**, y el segundo se puede
repetir sobre el primero meses después —es la promesa que protege «el núcleo es puro»:
regenerar la tabla sin volver a correr cuatro horas—. Así que hay dos árboles:

* el de la **corrida**, que dice de dónde salieron las EXTRACCIONES;
* el del **informe**, que dice de dónde salió la PUNTUACIÓN.

**Que sean el mismo es lo normal y no es obligatorio.** Lo obligatorio es que se sepa: un
informe que no dice sobre qué árbol puntuó deja un número que no se puede volver a atar a
un commit, y ésa es la clase de número que este repo llama irrepetible.

**Por qué no basta con imprimir el commit de la corrida**, que es lo que había antes: eso
contesta de dónde salieron las extracciones y **calla sobre quien las puntuó**, que es
precisamente la mitad que el informe controla.

Este módulo es **puro**: recibe los dos árboles ya leídos y no llama a `git`. Quien lo
llama es `cli.report`, que sí puede.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

__all__ = ["CAMPOS", "bloque", "difieren"]

CAMPOS = ("commit", "sucios", "huella")
"""Los tres que `extract.sello.arbol()` produce. Se comparan **los tres**: el commit solo
engaña sobre un árbol sucio, y el recuento de sucios engaña más fino."""


def difieren(
    corrida: Mapping[str, object], informe: Mapping[str, object]
) -> dict[str, tuple[object, object]]:
    """`{campo: (el de la corrida, el del informe)}` para los que no coinciden."""
    return {c: (corrida.get(c), informe.get(c)) for c in CAMPOS if corrida.get(c) != informe.get(c)}


def bloque(corrida: Mapping[str, object], informe: Mapping[str, object] | None) -> list[str]:
    """La procedencia, **dicha siempre**: coincidan los árboles o no."""
    if informe is None:
        return [
            "### Procedencia",
            "",
            "**El árbol del informe no se registró.** La tabla dice de dónde salieron las "
            "extracciones y **calla sobre quién las puntuó**, que es la mitad que el "
            "informe controla. Es un hueco, no una coincidencia.",
        ]
    cabeza = [
        "### Procedencia · los dos árboles",
        "",
        f"**Extracciones** — corrida de `{corrida.get('commit')}`, "
        f"{corrida.get('sucios')} ficheros sin commitear, huella `{corrida.get('huella')}`, "
        f"empezada {corrida.get('empezada')}.",
        "",
        f"**Puntuación** — informe de `{informe.get('commit')}`, "
        f"{informe.get('sucios')} ficheros sin commitear, huella `{informe.get('huella')}`.",
        "",
    ]
    movido = difieren(corrida, informe)
    if not movido:
        return [*cabeza, "**Mismo árbol en los dos.** El número se ata a un solo commit."]
    detalle = " · ".join(f"`{c}`: corrida {a!r} → informe {b!r}" for c, (a, b) in movido.items())
    return [
        *cabeza,
        f"**NO son el mismo árbol**, y se dice en vez de callarlo: {detalle}.",
        "",
        "Eso **no invalida la tabla**: invalida atarla a un commit solo. Las extracciones "
        "son del árbol de la corrida y la puntuación es del árbol del informe, y quien "
        "quiera reproducir esto necesita **los dos**. Para reproducirla exacta, el "
        "aritmético vive en `report.nivel1` y `core`, que son puros: se vuelve al commit "
        "del informe y se relanza `docbench report` sobre los mismos diarios.",
    ]
