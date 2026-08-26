# Cómo se mide aquí

Un banco de pruebas es una máquina de producir números sobre el trabajo de otros. Lo
único que hace que esos números valgan algo es que **el que los produce no pueda
elegirlos**. Este documento es el conjunto de reglas que lo impiden, y cuatro casos
reales en los que se notó.

No hace falta conocer el proyecto para leerlo.

---

## Las seis reglas

**1 · Todo lo que se congela, se congela ANTES, y el orden se puede comprobar.**
Los casos de referencia, los planes de muestreo y las tablas transcritas a mano se
escriben y se sellan antes de la primera medición. No basta con decirlo: **el
compromiso va a git antes de medir**, para que el sello de tiempo lo guarde un
tercero y no el autor.

**2 · Toda barrera se ha visto ROJA.**
Un test que nunca ha fallado no es un test: es una afirmación. Cada comprobación de
este repo tiene su **control negativo** —se le da algo deliberadamente malo y se
exige que lo rechace— y, donde se puede, un **mutante**: se rompe el código a
propósito y se comprueba que la suite se cae. Un mutante que sobrevive es un agujero
medido, no un mutante mal escrito.

**3 · Un número derivado no se teclea.**
O lo emite el script que lo mide, o no se publica. Un porcentaje, una resta o una
suma escritos a mano se quedan viejos en silencio mientras el número del que salían
se actualiza. Hay un comando que los recalcula y está en la puerta.

**4 · Lo que NO se mide se publica igual de fuerte que lo que sí.**
Hay 102 límites numerados, cada uno con su fecha y el hito en que se descubrió. No son
una lista de disculpas: varias veces han sido la parte más útil del resultado. Un
banco que sólo publica lo que le sale bien mide su propia suerte.

**5 · Una afirmación falsa nunca es deuda.**
Se arregla el día que se detecta. Lo que sí puede esperar es la **cobertura que
falta**, y entonces se declara con su tamaño medido y sin prometer fecha: *«esto no
lo vigila nadie, son 7 de 18, costaría ~1 h 10 min»* es una frase cierta y
comprobable.

**6 · No se publica con el nombre que no se ha ganado.**
El nombre de una medida es parte de la medida. *«Tasa de alucinación»* afirma que el
error es del extractor — y eso es justo lo que la medición tenía que averiguar, no
suponer: la referencia dice «cero tablas» **en el XML**, no en el documento, así que la
cifra mezcla lo que el extractor inventa con lo que la fuente no marcó. Mientras esa
separación no esté hecha se publica como *«tasa de tabla no presente en la
referencia»*: más larga, más fea y cierta.

---

## Cuatro casos en los que la regla decidió algo

### Un número correcto y uno incorrecto, y la diferencia era dónde vivían

Un informe publicaba dos cifras del mismo párrafo: **1.213 celdas comparadas de un
total de 2.283**. Las dos parecían igual de sólidas.

La primera vivía en un fichero versionado que un script había escrito. La segunda
**no vivía en ninguna parte**: se había tecleado. Al intentar reconstruirla salían
2.301 o 2.281 según cómo se contara — y un tercero no podía saber cuál era la buena.

El arreglo no fue comprobarla mejor: fue **hacer que el programa la emitiera**. De
ahí sale la regla 3, y de ahí que un porcentaje sin denominador reproducible no se
publique aunque sea correcto.

### El mismo hito, dos congelaciones, y sólo una se podía auditar

Para medir si una verdad de referencia automática reproducía 30 tablas transcritas a
mano, hacían falta dos cosas congeladas antes de comparar: **el comparador** y **las
transcripciones**.

El comparador quedó atestiguado sin querer: sus ficheros entraron en git una hora
antes de que se publicara el número, así que cualquiera puede comprobar el orden. Las
transcripciones no: el commit que anunciaba su congelación contenía **un puntero a un
fichero que todavía no estaba en git**, y las huellas entraron en el mismo commit que
publicó el resultado.

Nada era falso. Pero *«se transcribió a ciegas antes de comparar»* pasaba a depender
de la palabra del autor, que es justo lo que las reglas existen para evitar. **El
mecanismo correcto ya se conocía y se había aplicado a nueve metros de distancia.**
Lo que faltaba no era la idea: era que fuera un paso obligatorio. Ahora lo es.

### La palanca que se iba a gastar valía 44 ms y estaba publicada como 285

La puerta de CI tiene un techo de tiempo. Cuando se acercó, había una palanca
apuntada para ganar margen: bajar los ejemplos de una suite de propiedades, *«ahorra
285 ms»*.

Antes de accionarla, se midió. **Ahorraba 44.** El 285 nunca se había medido: salía
de suponer que el coste escala con el número de ejemplos, y no escalaba. El coste
estaba en otro sitio.

Dos hitos después la puerta volvió a apretar y las opciones eran las de siempre:
subir el techo, gastar una palanca, reestructurar — **las tres son concesiones**.
Esta vez se miró primero dónde estaba el tiempo, y apareció algo que simplemente
estaba mal: un programa abriendo el mismo fichero ocho veces. Arreglado, el margen
volvió a ser mayor que antes de empezar.

La lección no es «mide antes de decidir». Es que **eso ya se había hecho una vez, y
no se había convertido en un paso**. Una comprobación que se hace cuando a uno se le
ocurre no es una comprobación: es suerte.

---

### Un canal compartido usado como si fuera propio

`pymupdf4llm` falló en **3 de 3** documentos, y el registro dijo `SALIDA_ILEGIBLE`. La
lectura natural es que el extractor está roto. No lo estaba: **el fallo era del arnés**.

La unidad de medida escribía su resultado en `stdout`. Y `stdout` no es suyo: lo comparte
con todo lo que importe. `pymupdf4llm` arrastra `rapidocr`, que imprime
`rapidocr_api using backend: rapidocr` y un bloque `=== Document parser messages ===`
**antes** de que la unidad llegue a escribir su JSON. El padre encontraba basura por
delante, no podía parsear, y anotaba un fallo del extractor.

**Es el mismo error que publicar un número en un documento que otro proceso también
escribe**, un nivel más abajo: el sitio donde dejas el resultado tiene que ser tuyo, o
lo que leas de vuelta no es lo que escribiste. El arreglo es de una línea de diseño —la
unidad recibe la ruta de su fichero de salida— y lo que compra es que
`SIN_RESULTADO` signifique **lo que dice**: que el proceso murió antes de escribir.

Y hay una segunda mitad. `stderr` **no** se tira: ahí escriben `rapidocr` y `camelot`
sus avisos, y sin él la causa de un fallo real se perdería. Un canal se comparte o no se
comparte; lo que no se puede es tratarlo de las dos maneras.

## Una regla más, y ésta es sobre quién publica

**Este repo no construye ni construirá un extractor propio.** Si lo hiciera, su
ranking valdría cero. Suena a precaución teórica: de los ocho bancos que cubren tablas
o parseo multilingüe, **tres los publica quien vende lo que el banco mide, y uno ni
siquiera está publicado**. Quién publica cada cual, con nombres y cifras:
[quién publica los bancos](quien-publica-los-bancos.md).

## Qué NO es esto

No es una promesa de que los números de este repo sean correctos. Es un conjunto de
mecanismos para que, cuando uno no lo sea, **se note** — y para que quien lo lea
pueda comprobarlo sin pedirle nada al autor.

Los números medidos están en [`RESULTS.md`](../RESULTS.md), cada uno con el comando
que lo reproduce. Lo que este proyecto **no** mide está en [`LIMITS.md`](../LIMITS.md).
El método de cada métrica, con su historial de correcciones, en
[`docs/metrics.md`](metrics.md).
