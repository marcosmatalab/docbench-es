"""La versión corta: el bloque generado del `README.md`. **Mismo generador, dos salidas.**

Es el patrón que este repo ya usa con `scripts/estado_readme.py`, que deriva de
`ESTADO.md` el titular del README y el bloque de estado de `docs/reading-order.md`. La
razón es la misma y está medida: **el README se quedó 33 commits rancio** porque era un
documento que hay que acordarse de tocar.

**Qué sobrevive al recorte, y por qué esas cuatro cosas.** No es la página resumida: es
lo que un lector que no va a hacer clic tiene que saber para que el resto no le engañe.

1. el **titular con su panel**, porque sin panel el número está incompleto;
2. que las notas **no son comparables** y en qué rango se mueve la cobertura, porque es
   lo único que impide leer la tabla como un ranking;
3. la **errata**, tachada, porque es lo que distingue este repo de uno que publica
   números bonitos;
4. las **puertas**, porque la versión corta existe para llevar a la larga.

Lo que **no** entra: las bandas y el método. Los dos son buenos y los dos caben en la
página; meterlos aquí haría que el bloque creciera hasta ser la página otra vez, y el
tope de líneas de `tests/unit/test_documentos_que_sostienen.py` está justo para eso.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.portada._cifras import Cifra

__all__ = ["FIN", "INICIO", "bloque_corto"]

INICIO, FIN = "<!-- PORTADA:inicio -->", "<!-- PORTADA:fin -->"


def _puerta(v: Mapping[str, str]) -> str:
    """La puerta, **con la alarma dicha si suena**. Misma regla que en la página larga.

    El bloque corto es el que más se lee y el que menos espacio tiene, así que es donde
    más tienta dejar sólo el número bonito. Un p90 por encima de su techo escrito sin
    decirlo se lee como que está por debajo."""
    p90 = int(v["p90"].replace(".", ""))
    if p90 <= int(v["techo"].replace(".", "")):
        return f"puerta p90 **{v['p90']} ms** bajo un techo de **{v['techo']}**."
    return (
        f"puerta p90 **{v['p90']} ms** contra un techo de **{v['techo']}**: **la alarma"
        " está sonando** y el techo no se ha subido para callarla."
    )


def bloque_corto(c: Mapping[str, Cifra], pagina: str) -> str:
    """El bloque entre las dos marcas del README. **Ni una cifra tecleada, tampoco aquí.**

    `pagina` es el enlace a la portada larga: lo pone quien genera, porque depende de
    dónde se publique y no de ningún número.
    """
    v = {k: cifra.valor for k, cifra in c.items()}
    return "\n".join(
        [
            INICIO,
            f"> ## {v['titular']} · el titular de {v['hito']}",
            ">",
            f"> Documentos con tabla en los que los **{v['panel_n']}** extractores"
            f" —`{v['panel']}`— coinciden con la referencia en **cuántas tablas hay**:"
            f" el **{v['titular_pct']}**. **El panel va dentro de la etiqueta**, porque el"
            " número es una intersección y **sólo sabe bajar** al añadir un extractor: dos"
            " valores con paneles distintos no son comparables.",
            ">",
            f"> **Las notas de los {v['panel_n']} no son comparables entre sí**: cada TEDS"
            f" se calcula sobre lo que ese extractor pudo evaluar, y esa cobertura va de"
            f" **{v['cobertura_min']}** a **{v['cobertura_max']}**. Ordenarlas sería un"
            f" ranking falso; la comparación que vale es la cara a cara sobre los"
            f" **{v['cara_a_cara_n']}** que puntuaron todos, y ahí **el orden cambia**.",
            ">",
            f"> **Y este titular se publicó mal:** decía ~~{v['errata_antes']}~~ y son"
            f" **{v['errata_ahora']}**. Era otra cuenta —los que *puntuaron* todos—, y"
            f" ningún test podía verlo porque **ningún fixture tenía una celda"
            " combinada**. El commit falso sigue en la historia, con la corrección"
            " detrás.",
            ">",
            f"> **{v['mutantes']}** mutantes · **{v['limites']}** límites ·"
            f" **{v['adr']}** ADR · coste **{v['coste']}** medido, con la predicción del"
            f" reloj fallando **{v['error_estimador']}** · {_puerta(v)}",
            ">",
            f"> [**La portada entera, en diez minutos**]({pagina}) ·"
            " [`RESULTS.md`](RESULTS.md) · [`LIMITS.md`](LIMITS.md) ·"
            " [`runs/l5/informe.json`](runs/l5/informe.json). **Este bloque lo genera"
            " `uv run docbench portada`**: no se teclea.",
            FIN,
        ]
    )
