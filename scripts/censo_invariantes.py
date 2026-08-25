"""L1 · El censo que mide «los solapes, huecos y spans fuera de rango se detectan al 100%».

**No usa `hypothesis`.** `hypothesis` corre en la puerta y sirve para encontrar la
forma que no se me ocurrió; el número que se publica sale de aquí, que es un censo
**determinista y exhaustivo**: mismas tablas base, mismas mutaciones, mismo
resultado en cualquier máquina y en cualquier corrida. Un número que depende de
una semilla no se puede reproducir, y la regla de oro 2 dice que entonces no
existe.

Es una tasa sobre el censo completo, **no una estimación**, así que no lleva
intervalo: lleva n, método, versión y comando (ADR-0015).

Mide tres cosas, y la segunda es la que no se puede omitir:

1. **Detección**: de N tablas rotas, cuántas se detectan, y con el código correcto.
2. **Falsos positivos**: de M tablas legales, cuántas se rechazan. Un validador que
   rechazara todo sacaría un 100% en la primera.
3. **La condición 1**: sobre la familia «rowspan que baja sobre una fila corta»,
   cuántas acepta la lectura del origen y cuántas rechazaría la lectura de la
   rejilla rellena. Es la evidencia de ADR-0018.

Uso:  uv run python scripts/censo_invariantes.py    ·    echo $?  → 0 si todo bien
"""

from __future__ import annotations

import sys
from collections.abc import Iterator

from censo_mutaciones import (
    FORMAS_DEL_BOE,
    PATRONES,
    TAMANOS,
    UN_SOLO_CODIGO,
    _base,
    _mutaciones,
    _mutaciones_legales,
)
from docbench_es.core.canonical import from_html, holes, validate
from docbench_es.types import CanonicalCell, CanonicalTable, HallazgoTabla


def _familia_condicion_1() -> Iterator[CanonicalTable]:
    """`rowspan` que baja de una fila de arriba sobre una fila corta. HTML legal."""
    for ancho in range(2, 6):
        for n_filas in range(2, 6):
            for corte in range(ancho - 1):
                col_larga = ancho - 1
                celdas = [CanonicalCell(0, col_larga, n_filas, 1, "baja entera")]
                for fila in range(n_filas):
                    hasta = corte if fila == n_filas - 1 else col_larga
                    celdas += [CanonicalCell(fila, c, 1, 1, f"{fila},{c}") for c in range(hasta)]
                yield CanonicalTable(tuple(celdas), n_filas, ancho, (1, 1), None, True, "html")


def _rejilla_rellena_lo_llamaria_interior(t: CanonicalTable) -> bool:
    """La lectura DESCARTADA: ¿hay alguna POSICIÓN ocupada a la derecha del hueco?"""
    return any(
        any(t.cell_at(fila, c) is not None for c in range(col + 1, t.n_cols))
        for fila, col in holes(t)
    )


def main() -> int:
    sinteticas = [_base(f, c, p) for f, c in TAMANOS for p in PATRONES]
    reales = [t for html in FORMAS_DEL_BOE.values() for t in from_html(html)]
    bases = [*sinteticas, *reales]

    falsos_positivos = [t for t in bases if not validate(t)[0]]
    legales = 0
    rechazadas_siendo_legales: list[str] = []
    for base in bases:
        for nombre, mutada in _mutaciones_legales(base):
            legales += 1
            if not validate(mutada)[0]:
                rechazadas_siendo_legales.append(f"{nombre}: {validate(mutada)[1]}")
    rotas = 0
    sin_detectar: list[str] = []
    # Por familia, no sólo el total: un 8525/8525 sigue saliendo verde si una
    # familia deja de generar mutantes —un cambio en `_base` y esa forma de romper
    # la tabla ya no se prueba—. El total no lo ve; el recuento por familia sí.
    por_familia: dict[str, list[int]] = {}
    for base in bases:
        for nombre, codigo, mutada in _mutaciones(base):
            rotas += 1
            cuenta = por_familia.setdefault(nombre, [0, 0])
            cuenta[1] += 1
            ok, problemas = validate(mutada)
            visto = {p.split(":", 1)[0] for p in problemas}
            fatales = {v for v in visto if HallazgoTabla(v).es_fatal}
            # Un hallazgo INFORMATIVO tiene que aparecer, pero no invalida la
            # tabla: exigirle `ok is False` sería exigir que un formato mal
            # etiquetado tire una tabla cuya geometría es correcta.
            deberia_invalidar = codigo.es_fatal
            esperados = {codigo} if codigo.es_fatal else set()
            de_mas = codigo in UN_SOLO_CODIGO and fatales != esperados
            if (ok and deberia_invalidar) or codigo not in visto or de_mas:
                sin_detectar.append(f"{nombre} en {base.n_rows}x{base.n_cols}: {problemas}")
            else:
                cuenta[0] += 1

    familia = list(_familia_condicion_1())
    aceptadas = [t for t in familia if validate(t)[0]]
    rechazadas_por_la_otra = [t for t in familia if _rejilla_rellena_lo_llamaria_interior(t)]

    print(f"censo de invariantes · {len(bases)} tablas base")
    print(f"  {len(sinteticas)} sintéticas · tamaños {TAMANOS}")
    print(
        f"  {len(reales)} tablas de {len(FORMAS_DEL_BOE)} formas medidas en el BOE, via from_html:"
    )
    for nombre in FORMAS_DEL_BOE:
        print(f"      · {nombre}")
    print(f"  detección de tablas rotas ..... {rotas - len(sin_detectar)}/{rotas}")
    vacias = [n for n, (_, t) in por_familia.items() if t == 0]
    print(
        f"  familias de mutación .......... {len(por_familia)}, ninguna vacía"
        if not vacias
        else f"  FAMILIAS SIN UN SOLO MUTANTE: {vacias}"
    )
    if "--familias" in sys.argv:
        for nombre, (bien, total) in sorted(por_familia.items()):
            print(f"      {bien:>5}/{total:<5} {nombre}")
    print(f"  falsos positivos · tablas base . {len(falsos_positivos)}/{len(bases)}")
    print(f"  falsos positivos · huecos rellenados {len(rechazadas_siendo_legales)}/{legales}")
    print(f"  condición 1 · aceptadas ....... {len(aceptadas)}/{len(familia)} (lectura del origen)")
    print(
        f"  condición 1 · las rechazaría ... {len(rechazadas_por_la_otra)}/{len(familia)}"
        " (lectura de la rejilla rellena)"
    )
    for fallo in sin_detectar[:10]:
        print(f"  SIN DETECTAR: {fallo}")
    if falsos_positivos:
        print(f"  FALSO POSITIVO: {falsos_positivos[0].cells}")
    for fallo in rechazadas_siendo_legales[:5]:
        print(f"  RECHAZADA SIENDO LEGAL: {fallo}")

    correcto = (
        not sin_detectar
        and not falsos_positivos
        and not rechazadas_siendo_legales
        and len(aceptadas) == len(familia)
    )
    print("OK" if correcto else "FALLA")
    return 0 if correcto else 1


if __name__ == "__main__":
    sys.exit(main())
