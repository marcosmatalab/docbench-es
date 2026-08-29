"""Cuántos documentos del corpus tienen tablas, y dónde están.

    uv run python scripts/censo_tablas.py

Cuenta `<table` en el XML de referencia de cada documento de `runs/l3/`. **No es una
medida de calidad de nada**: es el censo de la población sobre la que L5 va a puntuar,
y sale de la verdad de referencia, no de un extractor.

## El número que cambia la forma de la tabla de L5

**Sólo un tercio del corpus tiene alguna tabla.** Los otros dos tercios no puntúan:
salen `NO_APLICABLE`, nunca 0,00 (decisión B3). Así que la n efectiva del TEDS agregado
no son 1.000 documentos.

Y las tablas se concentran **más** que las páginas: los 38 documentos de más de 50
páginas son el 3,8% de los documentos, el 36,6% de las páginas y **el 42,9% de las
tablas**. Es lo que hace que la pregunta de con qué se pondera el agregado no sea
retórica; está decidida en `runs/l5/ponderacion.yaml`.
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_paginas import DEL_COSTE, paginas, repartir  # noqa: E402
from fuera_de_git import exige  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"
# `<table` seguido de espacio o de `>`: así no cuenta `<tablero` ni nada que empiece igual.
TABLA = re.compile(r"<table[\s>]")


PUBLICADO = RAIZ / "runs" / "l5" / "censo_tablas.json"


@lru_cache(maxsize=1)
def _contadas() -> tuple[tuple[str, int], ...]:
    """Los mil XML, contados UNA vez por proceso. Misma razón que `censo_paginas`.

    **Y ahora LANZA si el corpus no está.** Antes devolvía `{}`: sin los 362 MB de
    `runs/l3/docs` no fallaba, repartía los 1.000 documentos como si ninguno tuviera
    tabla y `poblacion_l5` emitía **otra predicción**. Un test que la comprobara habría
    pasado en verde en un clon frío afirmando un número falso. Ver `fuera_de_git.py`.
    """
    exige(DOCS)
    fuera: list[tuple[str, int]] = []
    for ident in paginas():
        xml = DOCS / f"{ident}.xml"
        if xml.exists():
            fuera.append(
                (ident, len(TABLA.findall(xml.read_text(encoding="utf-8", errors="replace"))))
            )
    return tuple(fuera)


def tablas() -> dict[str, int]:
    """`external_id` → número de tablas en su XML de referencia. **Mide, desde los XML.**

    Es el INSTRUMENTO, y necesita el corpus. Quien sólo necesita el censo **ya medido**
    llama a `publicado()`, que lee el artefacto versionado y por tanto corre en un clon
    frío. La diferencia importa: si un consumidor mide en vez de leer, arrastra 362 MB de
    dependencia sin necesitarla y su test se salta donde no hacía falta.
    """
    return dict(_contadas())


@lru_cache(maxsize=1)
def publicado() -> dict[str, int]:
    """El censo tal y como quedó publicado en `runs/l5/censo_tablas.json`. **En git.**

    Lo emite `main()` de este mismo fichero desde los XML; esto sólo lo lee. Que los dos
    coincidan lo comprueba `tests/unit/test_datos_fuera_de_git.py` **cuando el corpus
    está**, y se salta con su razón cuando no — que es el sitio donde un salto vale: en
    la comprobación del artefacto, no en el consumidor.
    """
    datos = json.loads(exige(PUBLICADO).read_text(encoding="utf-8"))
    return {str(k): int(v) for k, v in datos["por_documento"].items()}


def main() -> int:
    cuenta = tablas()
    if not cuenta:
        print(f"  no hay XML en {DOCS.relative_to(RAIZ)}")
        return 1
    con = [i for i, n in cuenta.items() if n > 0]
    total = sum(cuenta.values())
    print(
        f"\n  {len(cuenta)} XML · {len(con)} con al menos una tabla "
        f"({100 * len(con) / len(cuenta):.1f}%) · {total} tablas\n"
    )
    print(
        f"  {'banda':<8} {'docs':>5} {'con tabla':>11} {'tablas':>8} {'% tablas':>9} "
        f"{'tablas/doc con':>15}"
    )
    for nombre, b in repartir(DEL_COSTE).items():
        suyos = [i for i in b.documentos if i in cuenta]
        conw = [i for i in suyos if cuenta[i] > 0]
        n = sum(cuenta[i] for i in suyos)
        print(
            f"  {nombre:<8} {len(suyos):5d} {len(conw):5d} "
            f"({100 * len(conw) / len(suyos):4.1f}%) {n:8d} {100 * n / total:8.1f}% "
            f"{n / max(1, len(conw)):15.1f}"
        )
    print(
        f"\n  LA n EFECTIVA DEL TEDS AGREGADO SON {len(con)} DOCUMENTOS, no {len(cuenta)}: "
        f"los otros\n  {len(cuenta) - len(con)} salen NO_APLICABLE y no puntúan. "
        "Ver runs/l5/ponderacion.yaml."
    )
    (RAIZ / "runs" / "l5" / "censo_tablas.json").write_text(
        json.dumps(
            {
                "con_tabla": len(con),
                "documentos": len(cuenta),
                "tablas": total,
                "por_documento": cuenta,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
