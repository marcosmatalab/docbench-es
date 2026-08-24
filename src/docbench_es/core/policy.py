"""§8.3 · La puerta de egress: **si la fuente prohíbe terceros, la campaña no arranca.**

> *«Si un adaptador declara `may_send_to_third_party: false`, el motor **rechaza**
> los extractores por API y la campaña no arranca. No es una advertencia.»*

Es la regla de oro 5 —la privacidad es código— en su forma ejecutable. Aquí no hay
avisos ni grados: o la combinación está permitida, o esto lanza `PolicyViolation`
con código de salida **2**, que es el que separa *«la medición salió peor de lo
tolerado»* de *«la campaña no llegó a arrancar porque la política lo prohíbe»*.

## Por qué esto vive aquí y no en `benchcore` todavía

§16 pone el motor de política en **`benchcore.core.policy`**, y L8 lo cablea. Ese
módulo **no existe** (deuda 1 de `ESTADO.md`: `benchcore` crece cuando su primer
consumidor se lo pide). Éste es ese consumidor pidiéndolo, y mientras tanto la
puerta vive del lado del consumidor: **una decisión de privacidad que no se puede
ejercitar es decorativa**, y ADR-0037 la toma hoy.

**Y tiene hito, no un «cuando exista»** (ADR-0037): **L8 incluye en su alcance
mover este módulo a `benchcore.core.policy`** —con su suite, subiendo el menor de
`API_VERSION`— y dejar aquí la llamada. Precio estimado **~1 h 30 min**, y por eso
el rango de L8 sube de 10-12 h a 11-14. Un aplazamiento sin hito nombrado acaba en
que nadie lo mueve y el manual diverge en silencio.

## Precondiciones declaradas

- **Es pura.** No conoce extractores ni adaptadores: recibe la declaración de
  privacidad y una lista de descriptores con `runs_locally`. Por eso vive en
  `core`, y por eso el contrato de capas la deja aquí sin abrir la puerta a que el
  núcleo importe `extract`.
- **Sólo mira el egress.** El rechazo de un adaptador con `special_categories`
  —§14 y §19— es del registro y su hito es **L8**. Meterlo aquí duplicaría la
  puerta en dos sitios que pueden divergir.
- **`runs_locally` se cree.** Es lo que el extractor declara de sí mismo; que sea
  cierto lo comprueba su suite de conformidad (§7.2), no esto. Un extractor que
  mintiera en ese campo pasaría esta puerta, y eso es un límite del contrato, no
  un fallo de aquí.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from benchcore.types import PrivacyDecl

from docbench_es.errors import PolicyViolation

__all__ = ["ExtractorDeclarado", "exigir_egress_permitido"]


@dataclass(frozen=True)
class ExtractorDeclarado:
    """Lo poco que la puerta necesita saber de un extractor: quién es y si es local.

    No es `Extractor`: si esto recibiera el `Protocol` entero, `core` tendría que
    importar `extract` y el núcleo dejaría de ser puro. La puerta necesita dos
    campos, así que pide dos campos.
    """

    id: str
    runs_locally: bool


def exigir_egress_permitido(
    privacidad: PrivacyDecl, extractores: Sequence[ExtractorDeclarado]
) -> None:
    """No devuelve nada: o pasa, o **lanza**. Ése es el punto.

    Devolver un booleano dejaría que alguien lo ignorara con un `if` mal escrito, y
    la diferencia entre una política y un aviso es exactamente ésa. El mensaje
    nombra **todos** los extractores que la rompen, no el primero: quien monta la
    campaña quiere quitarlos de una vez, no descubrirlos de uno en uno.
    """
    if privacidad.may_send_to_third_party:
        return
    fuera = sorted(e.id for e in extractores if not e.runs_locally)
    if not fuera:
        return
    raise PolicyViolation(
        f"la fuente declara `may_send_to_third_party: false` y la campaña pide "
        f"{len(fuera)} extractor(es) que no corren en local: {', '.join(fuera)}. "
        "La campaña NO arranca (§8.3, regla de oro 5). Quítalos del plan o usa una "
        "fuente cuya declaración lo permita — cambiar el perfil para que quepan es "
        "cambiar la respuesta a la pregunta, no resolverla"
    )
