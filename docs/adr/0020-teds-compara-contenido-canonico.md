# ADR-0020 · TEDS compara el contenido CANÓNICO, y el golden se genera sobre él

**Fecha:** 2026-08-22 · **Estado:** aceptada, implementada y **transcrita al manual**
(§9.2) en el mismo commit

## Contexto

§9.2 manda validar TEDS *«contra la implementación de referencia de PubTabNet
sobre sus propios casos»* y añade: *«Si no reproduce sus números, la
implementación está mal»*.

Al leer esa implementación —`src/metric.py` del repo de PubTabNet, Apache-2.0—
aparece el problema, y no es un detalle:

- **La referencia no normaliza absolutamente nada.** Tokeniza cada celda en
  **caracteres sueltos** (`list(node.text)`) y compara con Levenshtein sobre esa
  lista, normalizando por la longitud del más largo.
- **Este proyecto sí normaliza**, y lo decidió en ADR-0017: seis normalizaciones
  aplicadas por el conversor antes de que el texto llegue a `CanonicalTable`.
- **Y la referencia cuenta nodos que este proyecto no tiene.** El denominador es
  `len(table.xpath(".//*"))`, o sea todos los descendientes de `<table>`
  **incluido el marcado inline dentro de las celdas**. En los 20 casos de
  PubTabNet hay **189 nodos inline dentro de `<td>`** —`<b>`, `<i>`, `<sup>`—
  que la referencia cuenta y que `CanonicalTable` no guarda, porque su modelo de
  celda es texto plano.

Medido sobre los 20 casos: comparar mi TEDS sobre las tablas canónicas contra los
valores de la referencia sobre su HTML crudo da **15 de 20 casos distintos**, con
diferencias de hasta 0,207. Si el golden fuera ése, L2 no se podría cerrar, y no
por un bug de TEDS.

## Decisión

**El golden se genera dando a la implementación de referencia el MISMO contenido
que ve este código**: el render canónico de las mismas tablas
(`core.teds.a_html`). Los dos lados parten del mismo árbol y del mismo texto, así
que **una diferencia sólo puede venir del algoritmo**, que es lo que §9.2 manda
validar. Resultado: **20 de 20 a cuatro decimales**, y de hecho a seis.

TEDS, por tanto, **compara el texto canónico de la celda** —el que sale de las
seis normalizaciones de L1— y no el crudo. Es coherente con el resto del
proyecto: si TEDS usara un texto distinto del que usan `cellmatch`, `truth` y los
verificadores, habría **dos nociones de «contenido de celda»** en el mismo
proyecto, que es la avería de las dos fuentes de verdad en otro plano.

**La diferencia contra el HTML crudo no se esconde: se mide y se publica** en
`RESULTS.md`, con su descomposición, que es lo que la hace interpretable:

| | |
|---|---|
| Casos idénticos | 5 de 20 |
| Casos que difieren | **15 de 20** |
| …de ésos, con la normalización **sin tocar ni un texto** de celda | **10** — o sea que toda su diferencia es de **forma del árbol** |
| …de ésos, con la normalización cambiando algún texto | 5 — mezcla de forma y normalización, **no separadas** |
| Diferencia media (canónico − original) | +0,0092 |
| Mediana | −0,0005 |
| Rango | [−0,0342, +0,2070] |

**La causa dominante no es normalizar: es la forma del árbol.** Eso es lo que el
número dice, y sin descomponerlo se habría atribuido a la normalización.

## Alternativa descartada

**Que TEDS compare el texto crudo, sin normalizar, para coincidir con la
referencia sobre su HTML original.**

Se descarta por tres razones, en orden de peso:

1. **Rompería ADR-0017 por la puerta de atrás.** El proyecto decidió que un BOM,
   un NBSP o una ligadura no son fallos de extracción. Si TEDS los contara como
   fallos, la decisión estaría tomada en el papel y deshecha en la métrica que
   más pesa del nivel 1.
2. **Exigiría que `CanonicalTable` guardara el marcado inline** para reproducir
   el denominador, o los números seguirían sin coincidir aunque no se normalizara
   nada: 10 de los 20 casos difieren **sin que la normalización toque nada**.
   Guardar el marcado inline es rediseñar §6.2 para satisfacer a un validador.
3. **Mediría la convención en vez del algoritmo.** El criterio de aceptación de
   L2 existe para responder *«¿tu TEDS es TEDS?»*. Comparando sobre contenidos
   distintos, un fallo no distinguiría entre «el algoritmo está mal» y «el texto
   no es el mismo», que son dos cosas y sólo una es la que L2 tiene que cerrar.

## Trade-off

Lo que se paga: **los TEDS de este proyecto no son directamente comparables con
los TEDS publicados en la literatura sobre PubTabNet**. Un paper que diga «TEDS
0,94 en PubTabNet» no se puede poner al lado de un número de aquí sin decir esto.
Va a `LIMITS.md` como límite 39, y es un límite serio: la comparabilidad externa
era una de las cosas que daba TEDS.

Lo que se compra: que el número mida al extractor y no al juego de caracteres
invisibles que arrastre su salida, y que una sola noción de «contenido de celda»
gobierne todo el proyecto.
