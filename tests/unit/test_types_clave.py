"""§6.1 · `DocRef.key()` es inyectiva, y el escapado que la sostiene.

Fichero aparte porque lo que se prueba aquí es **la unidad de remuestreo del
bootstrap**. Si dos documentos distintos comparten clave, el remuestreo los trata
como uno solo, el intervalo de confianza sale más estrecho de lo que toca y todo
número publicado afirma más precisión de la que hay. Es el fallo que L0 encontró
y arregló.

**Por qué hacen falta estos tests además del de L0.** L1 cambió el escapado de
`urllib.parse.quote` a uno escrito a mano —el contrato de capas prohíbe `urllib`
en `core`, y `core` importa `types`—. Con `quote`, la inyectividad del escapado
era de biblioteca y se daba por buena; escrito a mano, es código del proyecto y
hay que demostrarla.

Y el test de L0 **no puede** demostrarla, por construcción y no por descuido: su
estrategia genera los dos pares partiendo **la misma cadena** por dos sitios, así
que uno es siempre prefijo del otro. Un fallo de inyectividad del escapado
—`esc(a) == esc(c)` con `a ≠ c`— exige dos cadenas que no son prefijo una de otra,
y ésas no las genera nunca. Comprobado ejecutándolo: contra un escapado que
sustituye `/` por `%2F` **sin escapar antes el `%`**, el test de L0 pasa en verde.

Por eso aquí el instrumento es un **censo exhaustivo** y no un sorteo: sobre un
alfabeto pequeño se generan TODAS las cadenas hasta una longitud y se comprueban
todas. No hay suerte de por medio, y el resultado es el mismo en cualquier
máquina.
"""

from __future__ import annotations

from itertools import product

from docbench_es.types import DocRef

# El separador `/`, el carácter de escape `%`, y **los caracteres con los que se
# escribe la propia secuencia de escape**: `2`, `5` y `F`. Los tres últimos son
# los que faltaban en el alfabeto de L0 y los que hacen falta para escribir
# `%2F` o `%25` a mano, que es como una cadena de entrada se disfraza de escape.
ALFABETO = "/%25Fa"


def _todas_las_cadenas(alfabeto: str, hasta: int) -> list[str]:
    return ["".join(p) for n in range(hasta + 1) for p in product(alfabeto, repeat=n)]


def _clave_de(campo: str) -> str:
    """El escapado visto desde fuera. `external_id=""` no aporta nada al final.

    Se mira por la API pública y no importando `_escapar`, porque
    `docbench_es.types` es la única superficie de import del modelo de datos
    (ADR-0013) y hay un test de L0 que lo hace cumplir también para los tests.
    """
    return DocRef(campo, "", None, None, "k").key()


def test_el_escapado_es_inyectivo_sobre_el_censo_completo() -> None:
    """Demuestra que ninguna cadena puede disfrazarse de secuencia de escape.

    El bug que esto caza —y que el test de L0 no puede cazar— es el del **orden**:
    si se sustituye `/` por `%2F` sin escapar antes el `%`, entonces la entrada
    literal `%2F` y la entrada `/` producen las dos `%2F` y son indistinguibles.

    Censo exhaustivo: todas las cadenas de hasta 3 caracteres sobre un alfabeto
    que incluye `/`, `%` y los caracteres con los que se escribe la secuencia de
    escape. `%2F` y `/` están los dos dentro, que es lo que hace que el censo
    discrimine.
    """
    cadenas = _todas_las_cadenas(ALFABETO, 3)
    claves = [_clave_de(s) for s in cadenas]

    assert "%2F" in cadenas and "/" in cadenas, "el censo tiene que contener el par que discrimina"
    assert len(set(claves)) == len(cadenas), "dos cadenas distintas con la misma clave"


def test_el_escapado_no_deja_ningun_separador_suelto() -> None:
    """Demuestra la otra mitad: la `/` que separa es la ÚNICA `/` de la clave.

    Sin esto, la inyectividad del escapado no bastaría: dos campos escapados sin
    barras se podrían recomponer de una sola manera, pero una barra superviviente
    dentro de un campo volvería a hacer ambigua la separación, que es el bug
    original de L0 en su otra cara.
    """
    for cadena in _todas_las_cadenas(ALFABETO, 3):
        assert _clave_de(cadena).count("/") == 1, f"{cadena!r} deja una barra suelta"


def test_la_clave_es_inyectiva_sobre_el_censo_completo_de_pares() -> None:
    """Demuestra lo que de verdad importa: **dos documentos, dos claves**.

    Es la propiedad de la que depende el bootstrap agrupado, y aquí se comprueba
    sobre un censo completo de pares `(entity, external_id)`, no sobre una
    muestra. Cubre a la vez los dos fallos posibles: que el escapado no sea
    inyectivo y que el separador sea ambiguo.
    """
    cadenas = _todas_las_cadenas("/%2F", 3)
    claves = {DocRef(e, x, None, None, "k").key() for e in cadenas for x in cadenas}

    assert len(claves) == len(cadenas) ** 2, (
        f"{len(cadenas) ** 2 - len(claves)} colisiones sobre {len(cadenas) ** 2} documentos"
    )


def test_la_clave_sigue_siendo_legible_para_un_identificador_real() -> None:
    """Demuestra que el escapado no se paga en legibilidad donde se usa de verdad.

    Los identificadores del BOE no llevan `%` ni `/`, así que su clave es la
    misma que antes del cambio de L1. Si el escapado los tocara, todas las claves
    del corpus cambiarían de forma y los manifiestos de campañas viejas dejarían
    de casar con los nuevos.
    """
    assert DocRef("boe", "BOE-A-2026-1234", None, None, "convenio").key() == "boe/BOE-A-2026-1234"
