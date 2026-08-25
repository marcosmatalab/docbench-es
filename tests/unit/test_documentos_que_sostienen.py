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

RAIZ = Path(__file__).resolve().parents[2]

SOSTIENEN = {
    "README.md": 80,
    "docs/reading-order.md": 80,
    "docs/como-se-mide-aqui.md": 140,
}
"""Documento -> tope de líneas. Medidos el 25 ago 2026 en 57, 52 y 108."""

ACUMULAN = ("RESULTS.md", "LIMITS.md", "ESTADO.md", "CHANGELOG.md", "MANUAL.md")


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
