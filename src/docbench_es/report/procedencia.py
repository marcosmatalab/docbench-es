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
engaña sobre un árbol sucio, y el recuento de sucios engaña más fino.

**Pero no discriminan lo mismo, y presentarlos juntos como «la huella del árbol» hace
creer que el tercero identifica el árbol.** No lo hace:

* `commit` — QUÉ commit. Es el único que distingue un árbol limpio de otro árbol limpio;
* `sucios` — CUÁNTOS ficheros sin commitear;
* `huella` — `sha256` del `status --porcelain` más el `diff HEAD`. Discrimina **limpio de
  sucio**, y cuando está sucio, **qué** diff. Sobre CUALQUIER árbol limpio vale siempre
  `01ba4719c80b6fe9`, que es `sha256("\n")[:16]`.

Sin decirlo, la salida se lee como una contradicción: dos árboles con la MISMA huella y
un «no son el mismo árbol» debajo. Los dos son limpios; el commit es lo que los separa."""


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
        "**Qué discrimina cada campo**, porque no es lo mismo y verlos juntos hace creer "
        "que la huella identifica el árbol: `commit` dice **qué** commit y es el único "
        "que separa un árbol limpio de otro; `sucios`, **cuántos** ficheros sin "
        "commitear; y `huella` separa **limpio de sucio** —y, si está sucio, qué diff—, "
        "así que sobre cualquier árbol limpio vale siempre `01ba4719c80b6fe9`. **Dos "
        "huellas iguales no dicen que sea el mismo árbol: dicen que los dos están "
        "limpios.**",
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
