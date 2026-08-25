"""El tope de área de una tabla, con el número medido que lo fija.

Fichero aparte de `_invariantes.py` por el límite de 300 líneas, y la partición
sale sola: allí están **los invariantes** y aquí **la precondición de coste** que
hay que cumplir para poder comprobarlos.
"""

from __future__ import annotations

TOPE_AREA = 1_000_000
"""Área máxima —`n_rows` x `n_cols`— que se analiza. Por encima, `AREA_EXCESIVA`.

**No es endurecimiento de seguridad: es una precondición para que la métrica se
pueda calcular.** El coste de `comprobar` es proporcional al ÁREA de la rejilla y
no al tamaño de la entrada (límite 38), así que una tabla declarada de 65.534 x
1.000 —65 bytes de HTML— cuesta ~9 GB. En L5 son ocho extractores sobre mil
documentos, y **los extractores son justo lo que produce spans basura**: un span
grande y la campaña se queda sin memoria a mitad.

**El número sale del corpus, no del aire.** Sobre las 2.135 tablas de los 1.000
documentos de L3 (`runs/censos/censo-corpus-1000.json`):

| | área |
|---|---|
| mediana | 18 |
| media | 54 |
| **máxima real** | **3.309** (1103 x 3, `BOE-A-2026-5518` t0) |
| **tope** | **1.000.000** |

**La holgura es 302x** sobre la tabla más grande que el BOE ha producido, y se
elige así de amplia a propósito: el corpus es **una entidad y una ventana**, y las
tablas del BOE son estrechas —la mayor es 1103 x 3—. Otra entidad puede traer una
tabla ancha de verdad, y 1.000.000 admite 2.000 x 500, que no existe en ningún
documento real conocido. Por el otro lado, el tope está **65x por debajo** del
caso de 65,5 M posiciones que el límite 38 nombra, y su coste está medido: en el
tope, `comprobar` cuesta **0,212 s y 151 MB**.

**Y lo que pasa al pasarse va declarado**: no revienta ni trunca en silencio. Sale
`AREA_EXCESIVA`, que es **FATAL**, y esa tabla sale de la verdad de referencia como
cualquier otra fatal. Una tabla que se pasa de aquí es un *table model error* en la
práctica."""
