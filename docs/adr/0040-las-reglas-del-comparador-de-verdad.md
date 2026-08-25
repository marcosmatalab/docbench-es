# ADR-0040 · Qué cuenta como «reproduce», congelado antes de la primera comparación

**Fecha:** 2026-08-24 · **Estado:** aceptada, **escrita ANTES de correr el
comparador ni una vez**. No toca el manual: §16 dice *«reproduce las tablas a
mano»* y esto define qué significa

## Contexto

Yo escribí los fixtures. Yo escribí el código que se mide. Y ahora escribo **qué
cuenta como reproducir**. Las tres cosas.

**Si corro el comparador, veo 22 de 30, y añado una regla que lo sube a 27, he
afinado el instrumento contra la respuesta.** No haría falta mala fe: bastaría con
que cada regla nueva pareciera razonable mirándola una a una. Y nadie se enteraría,
empezando por mí.

Por eso las reglas se escriben y se congelan **antes**, con su razón, una por una.

## La regla de la que salen todas las demás

> **El comparador normaliza EXACTAMENTE lo que normaliza el pipeline, y nada más:
> `core.canonical.normalize_cell_text`.**

**Por qué ésa y no una lista propia.** Lo que el banco mide es lo que llega a la
métrica, y a la métrica llega texto pasado por `normalize_cell_text`. Un comparador
que normalizara **más** estaría midiendo algo que el banco no mide, y declararía
«reproduce» sobre una verdad que en la campaña real puntuaría distinto. Uno que
normalizara **menos** inventaría discrepancias que ningún extractor sufriría.

Y `normalize_cell_text` ya tiene su ADR —el **0017**— con la decisión más
importante de todas ya tomada: **sólo se toca lo invisible o la forma de
composición Unicode; ningún glifo visible se altera ni se borra.**

## Las reglas, una a una, con lo que decide cada una

| # | Cuestión | Decisión | De dónde sale |
|---|---|---|---|
| 1 | **espacios** | colapsados a uno, y los de cualquier categoría Unicode valen lo mismo | N3–N5 de ADR-0017. Ya declarado en cada fixture |
| 2 | **mayúsculas** | **se comparan tal cual**. `Optativa` ≠ `OPTATIVA` | N1–N6 no tocan el caso. Y el caso es dato: el BOE escribe los registros mercantiles en mayúsculas a propósito |
| 3 | **el punto final** de `Optativa.` | **significativo**. `Optativa.` ≠ `Optativa` | Ningún glifo visible se borra. Y el punto distingue una frase de una etiqueta |
| 4 | **guion corto contra largo**, y las comillas | **distintos**. `-` ≠ `–`, `"` ≠ `«` | Ídem. Son glifos visibles distintos, y el BOE usa `–` como separador de línea en cabeceras |
| 5 | **acentos** | **significativos**, pero `é` compuesto y `e`+tilde combinante son **iguales** | N1 normaliza a NFC. La diferencia visible se conserva; la de codificación, no |
| 6 | **el símbolo del euro** | tal cual, es un glifo | Ídem |
| 7 | **NÚMEROS** | **NO se tocan.** `1.599,26` ≠ `1 599,26` | **ADR-0017 entero.** Ver abajo |
| 8 | **celda vacía contra celda ausente** | **NO son lo mismo**, y el comparador las distingue | Ver abajo |

### La 7, que es la que más costaría no haber decidido antes

`normalize_cell_text` **no toca el separador de millares ni el decimal**, y ADR-0017
explica por qué con todas las letras: un extractor que devuelve `1,234.56` donde la
página dice `1.234,56` **ha aplicado la convención anglosajona a un documento
español**, y ése es *«el único fallo que justifica que este banco sea en español»*.
Repararlo sería borrar la medición.

**Y el caso ya está en la muestra, transcrito antes de decidir esto.** En
`BOE-A-2026-6941` t1 el propio BOE mezcla separadores dentro de la misma tabla:
`1.604,84` en una fila y `1 599,26` en la siguiente. Lo transcribí fielmente porque
es lo que se ve.

**Con la regla 7, eso es una diferencia si la verdad derivada dice otra cosa.** Y se
decide **antes de contar cuántas veces pasa**, que es la única forma de que la
decisión no dependa del resultado.

### La 8, que es lo que L1 construyó y no se puede perder aquí

Una **celda vacía** es una celda que existe y su texto es `""`. Una **celda
ausente** es un hueco: no hay celda. **TEDS-S las puntúa 1,000000 contra 0,857143**
—medido en L1— así que un comparador que las confundiera perdería exactamente la
distinción que justifica `holes()`.

El comparador compara **posición a posición**: en cada `(fila, columna)` hay una
celda anclada, una posición cubierta por un span, o un hueco. Los tres estados son
distintos.

## El colocador del comparador es INDEPENDIENTE, a propósito

Para saber en qué columna cae cada celda anclada de un fixture hay que colocarlas.
**El comparador NO usa `core.canonical._rejilla`.**

**La razón es el límite 52**: si el fixture se coloca con el mismo código que coloca
la verdad, un error de colocación **se cancela en los dos lados** y la comparación
sale verde sobre dos tablas igualmente mal construidas. Es exactamente lo que pasó
hoy con el grupo de filas: la colocación estaba mal y nada lo veía.

Son ~20 líneas —la regla del estándar: primera columna libre a la derecha del
cursor, saltando lo ocupado— escritas aparte y a mano. **Si discrepan, eso es un
hallazgo, no un fallo del comparador.**

## Qué pasa si después de correr hace falta cambiar una regla

**Se cambia, se dice, y se re-comparan las 30** —igual que si se arregla el código—
**pero la versión anterior y su número se publican igual.** Es el mismo criterio con
el que se publicaron las tres tablas de mutantes A/B/C: un número que se corrige se
publica corregido, y el que desaparece es el que este repo prohíbe.

## Alternativas descartadas

**Comparar sin normalizar nada.** Produciría discrepancias por un NBSP invisible que
ningún extractor sufriría, porque en la campaña real el texto llega normalizado.
Mide un pipeline que no existe.

**Normalizar «un poco más» —mayúsculas, el punto final— para que el número salga
mejor.** Es la trampa que este ADR existe para impedir, y la razón de que esté
fechado antes de la primera corrida.

## Trade-off

Lo que se paga: **el número va a salir más bajo** que con reglas laxas, y algunas
discrepancias serán por un guion. Cada una hay que mirarla.

Lo que se compra: que «reproduce» signifique lo mismo aquí que en la campaña de L5,
donde se puntúa a ocho extractores con estas mismas reglas.
