"""Los documentos que SOSTIENEN llevan tope de líneas. Los que ACUMULAN, no.

## La distinción, que es la lección entera del saneamiento de la portada

> **Un documento o ACUMULA o SOSTIENE, y no puede hacer las dos.**

**Los que ACUMULAN** —`RESULTS.md`, `LIMITS.md`, `ESTADO.md`, `CHANGELOG.md`,
`MANUAL.md`— son un diario: discuten con su propio pasado y crecen a cada hito. Su
tamaño es una **consecuencia**, y está bien que lo sea, porque ahí está su valor.

**Los que SOSTIENEN** —`README.md`, `docs/reading-order.md`,
`docs/como-se-mide-aqui.md`— son la primera pantalla de alguien que no va a volver.
Su tamaño es un **REQUISITO**.

**El README llevaba 33 commits pudriéndose porque era de la segunda clase y se estaba
usando como si fuera de la primera.** Nadie lo decidió: pasó. Y como en este repo una
regla que no es un test es una intención, aquí está el test.

**A los que acumulan NO se les pone tope, y se dice por qué:** un tope ahí sería el
error contrario —empujaría a recortar precisamente el registro que hace auditable cada
número—. Este fichero lo afirma en las dos direcciones, no sólo en una.

## Los topes, y de dónde salen

Del tamaño real el día que se saneó la portada, con holgura para que crezcan sin
mentir pero no para que vuelvan a ser lo que eran. Si uno se pasa, la respuesta por
defecto **no** es subir el tope: es sacar algo a su propio documento, que es lo que se
hizo con «las cinco cosas».
"""

from __future__ import annotations

from pathlib import Path

import pytest

from docbench_es.report.portada import FIN, INICIO

RAIZ = Path(__file__).resolve().parents[2]

SOSTIENEN = {
    "README.md": 80,
    "docs/reading-order.md": 80,
    "docs/como-se-mide-aqui.md": 150,
}
"""Documento -> tope de líneas. Medidos el 25 ago 2026 en 57, 52 y 108.

**`como-se-mide-aqui.md` pasó de 140 a 150 el 25 ago 2026, y con su razón**, porque
subir el tope es la respuesta NO por defecto y sólo vale después de haber sacado algo:

1. Primero se sacó lo que ACUMULA. El repaso de quién publica los ocho bancos crece
   cada vez que aparece uno nuevo, así que se fue a `docs/quien-publica-los-bancos.md`
   —28 líneas—. Eso es la regla funcionando.
2. Lo que quedó dentro y lo empujó son una **sexta regla** y un **cuarto caso**, los
   dos de la misma semana y los dos sostienen: no hay nada más ahí que acumule.

Si vuelve a pasarse, la respuesta por defecto sigue siendo sacar, no subir.
"""

ACUMULAN = (
    "RESULTS.md",
    "LIMITS.md",
    "ESTADO.md",
    "CHANGELOG.md",
    "MANUAL.md",
    # Entró con L5: el análisis de lo que se decidió NO hacer todavía, con sus números.
    # Acumula por construcción —cada decisión aplazada añade su párrafo— y por eso lo
    # dice en su propia cabecera. Sin esta línea, nada impediría ponerle un tope y
    # empezar a recortar justo el registro que explica por qué no se hizo algo.
    "docs/despues-de-la-tabla.md",
)


@pytest.mark.parametrize("nombre", sorted(SOSTIENEN))
def test_un_documento_que_sostiene_cabe_en_su_tope(nombre: str) -> None:
    """Si esto se pone rojo, la respuesta por defecto es SACAR algo, no subir el tope."""
    lineas = len((RAIZ / nombre).read_text(encoding="utf-8").splitlines())

    assert lineas <= SOSTIENEN[nombre], (
        f"`{nombre}` tiene {lineas} líneas y su tope son {SOSTIENEN[nombre]}."
        " Es un documento que SOSTIENE: su tamaño es un requisito, no una consecuencia."
        " Saca algo a su propio documento antes de subir el número"
    )


@pytest.mark.parametrize("nombre", ACUMULAN)
def test_un_documento_que_acumula_no_lleva_tope(nombre: str) -> None:
    """**El aro en la dirección contraria, y hace falta.**

    Sin esto, alguien podría «arreglar» un rojo del test de arriba metiendo un
    documento del diario en la lista de topes, y estaría recortando justo el registro
    que hace auditable cada número. Los dos errores son simétricos y sólo uno es
    obvio.
    """
    assert nombre not in SOSTIENEN, (
        f"`{nombre}` es un documento que ACUMULA: es un diario y su tamaño es una"
        " consecuencia. Ponerle tope empuja a borrar el registro, que es donde está su"
        " valor. Si hace falta acortarlo, se parte por hitos, no se recorta"
    )
    assert (RAIZ / nombre).exists()


TOPE_PORTADA = 18
"""Líneas del bloque `PORTADA` del README, marcas incluidas. Medido en 13 el 28 ago 2026.

**Un bloque GENERADO también necesita tope, y por una razón que los otros tres no
tienen:** nadie lo escribe, así que nadie nota que crece. Añadir una frase a
`report.portada._corto` cuesta lo mismo se publique donde se publique, y la versión corta
existe **precisamente** para ser corta: si crece hasta ser la página, el README vuelve a
ser lo que era y la portada larga deja de tener sentido.

Y el tope va sobre el bloque y no sólo sobre el README entero a propósito: con el tope
global se podría hacer sitio recortando lo escrito a mano, o sea pagando la generación
con la prosa. Los dos topes, y cada uno mide lo suyo.
"""


def test_el_bloque_generado_de_la_portada_cabe_en_su_tope() -> None:
    """La versión corta de la portada, acotada. Si esto se pone rojo, la respuesta por
    defecto es **sacar una frase**, que ya está en la página larga, no subir el número."""
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    i, j = texto.index(INICIO), texto.index(FIN) + len(FIN)
    lineas = len(texto[i:j].splitlines())

    assert lineas <= TOPE_PORTADA, (
        f"el bloque PORTADA tiene {lineas} líneas y su tope son {TOPE_PORTADA}."
        " Es la VERSIÓN CORTA: lo que no cabe ya está en `docs/index.html`."
        " Saca una frase de `report.portada._corto` antes de subir el número"
    )


def test_el_readme_lleva_las_marcas_de_los_dos_generadores() -> None:
    """**Dos generadores escriben en este fichero, y ninguno de los dos puede fallar en
    silencio.** `estado_readme.py` deriva el titular de `ESTADO.md`; `docbench portada`
    deriva la portada de `runs/l5/informe.json`. Si alguien borra un par de marcas al
    editar a mano, el generador aborta —y esto lo dice antes, con el nombre.
    """
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")

    faltan = [
        m
        for m in (INICIO, FIN, "<!-- ESTADO:inicio -->", "<!-- TITULAR:inicio -->")
        if m not in texto
    ]

    assert not faltan, f"el README perdió marcas de generador: {faltan}"
