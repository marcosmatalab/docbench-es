# ADR-0018 · Un hueco de cola es legítimo; uno interior es fatal. Y se derivan

**Fecha:** 2026-08-22 · **Estado:** aceptada, implementada y **transcrita al manual**
(§6.2) en el mismo commit

## Contexto

§6.2 enuncia el segundo invariante de `CanonicalTable` así:

> la unión de celdas con sus spans cubre exactamente `n_rows x n_cols` **o declara
> los huecos**

Ese «o» **no es traducible a código tal como está escrito**, y no por una
ambigüedad de redacción: porque «declarar» no tiene referente en el modelo de
datos. `CanonicalTable` no tiene campo de huecos, §9.1 no nombra ninguna función
que los enumere y §6.2 no dice quién declara ni dónde. Heredar el «o» habría
significado que L2 se lo encontrara al escribir TEDS, que es el peor sitio posible
para decidirlo: allí ya hay una métrica encima.

Las dos lecturas dan resultados opuestos sobre corpus real, así que había que
elegir a sabiendas:

- Si un hueco es **siempre ilegal**, `validate` rechaza toda fila corta. Una `<tr>`
  con menos `<td>` que columnas tiene la tabla es HTML **legal** que el navegador
  pinta sin quejarse, y es cotidiana en el BOE. Con esa lectura, `from_html`
  fallaría sobre el corpus con el que hay que medir.
- Si un hueco es **siempre legal**, `validate` no caza nunca un conversor que
  coloca mal una celda, y la validación deja de proteger de lo único de lo que
  tiene que proteger.

## Decisión

**Un hueco en `(f,c)` es INTERIOR —y fatal— si alguna celda ORIGINA en la fila `f`
a la derecha de `c`. Si no, es un HUECO DE COLA: legítimo, informativo y
enumerado.**

La distinción no es de gusto: es **derivable de cómo colocan los formatos de
origen**. HTML y TEI rellenan de izquierda a derecha con un cursor que salta lo
ocupado, así que un hueco nunca puede quedar a la izquierda de una celda de su
propia fila. Si queda, la colocación está mal, y eso es un bug del conversor
disfrazado de tabla plausible que TEDS puntuaría como si fuera una tabla.

**Los huecos se DERIVAN, no se almacenan.** `holes(t)` los calcula desde `cells`.
No se añade campo a `CanonicalTable`.

**Lo que L2 hereda:** un hueco **no es una celda vacía**. `<tr><td>a</td></tr>` y
`<tr><td>a</td><td></td></tr>` son árboles distintos y TEDS los puntúa distinto.
`holes()` es lo que permite a L2 emitir celda **ausente** en vez de celda vacía.

De la misma regla —«qué puede producir un formato de origen»— salen dos hallazgos
más, asimétricos y por buen motivo: **`COLUMNA_VACIA` es fatal**, porque ningún
formato puede dejar una columna entera sin cubrir y significa que `n_cols` se
calculó de más; **`FILA_VACIA` es informativo**, porque `<tr></tr>` es HTML legal.

## La alternativa descartada, y su medición

**La lectura de la rejilla rellena:** *«un hueco es de cola si no hay ninguna
posición ocupada a su derecha, venga de donde venga la celda que la ocupa».*

Es la lectura natural de la frase de §6.2, y **rechaza HTML legal**. El caso:

```
fila 0:  A | B | C | D(rowspan=3)
fila 1:  E | F | G |   ↓
fila 2:  x |   |   |   ↓      ← (2,1) y (2,2) huecos; (2,3) ocupada por D
```

Las posiciones vacías tienen una posición ocupada a su derecha, pero por una celda
que **no origina en esa fila**. Con la lectura de la rejilla rellena, esta tabla es
fatal. Con la del origen, es válida y sus huecos son de cola.

**Medido, no argumentado.** Sobre el censo de esa familia —anchuras 2 a 5, filas 2
a 5, y todos los puntos de corte—, **la lectura del origen acepta las 40 y la de la
rejilla rellena rechazaría las 40**:

```bash
uv run python scripts/censo_invariantes.py
#   condición 1 · aceptadas ....... 40/40 (lectura del origen)
#   condición 1 · las rechazaría ... 40/40 (lectura de la rejilla rellena)
```

No es un caso raro: el sondeo del BOE midió que **el 42% de los documentos con tabla de las
secciones I+III traen `rowspan` > 1**. La lectura descartada queda escrita y
ejecutable en `tests/unit/test_canonical_huecos.py`, en un test que se cae el día
que alguien cambie la definición.

También se descartó **almacenar los huecos en un campo de `CanonicalTable`**. Un
campo puede desacordar con `cells`, y entonces `validate` tendría que comprobar la
declaración contra la realidad: dos fuentes de verdad sobre la misma tabla, que es
el mismo fallo que la regla de oro 8 persigue en el plano de los documentos. Una
función derivada no puede caducar.

## Cómo se decidió, que es la parte reutilizable

La decisión no se tomó leyendo el manual: se tomó **generando la forma primero**.
El plan de L1 llevaba una definición ambigua —«hueco con celda a su derecha»— y la
revisión hizo dos cosas por separado:

1. **Diagnosticó el falso positivo correctamente**, con el caso del `rowspan` que
   baja sobre una fila corta, y señaló que las dos lecturas dan veredictos
   opuestos sobre HTML real.
2. **Recomendó la lectura que causa ese mismo falso positivo**, la de la rejilla
   rellena.

Diagnóstico correcto, prescripción invertida. Y la condición que acompañaba a la
recomendación —*«genera EXPLÍCITAMENTE el caso antes de fijar la definición; si
`from_html` lo produce y `validate` lo rechaza, la definición está mal»*— es lo
que evitó que la inversión llegara al código: el censo dio **40 aceptadas contra
40 que la otra lectura rechazaría**, y eso no admite interpretación.

De haberse implementado la recomendación en vez de la condición, L1 habría
empotrado el falso positivo que la propia revisión identificó, y **no habría
aparecido hasta que L2 puntuara huecos sobre tablas reales del BOE**, con la
métrica ya encima.

Por eso la lectura descartada **no se borra**: vive como función ejecutable en
`tests/unit/test_canonical_huecos.py`, con un test que se cae el día que alguien
la reinstaure. Una alternativa que sólo está descrita en prosa hay que volver a
razonarla; una que está escrita como código se comprueba.

## Trade-off

Lo que se paga: **el conversor que pierde la última celda de una fila no se
detecta**, porque el resultado es indistinguible de una fila corta legítima. Es un
falso negativo real y aceptado a conciencia; lo cubre el test de ida y vuelta de
`from_html`, que sí compara contra la tabla original.

Lo que se compra: que `validate` no rechace corpus real. Un validador que rechaza
el 42% de los documentos donde `rowspan` importa no protege de nada: obliga a
desactivarlo.
