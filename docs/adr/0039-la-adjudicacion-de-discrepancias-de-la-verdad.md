# ADR-0039 · Qué pasa cuando la verdad derivada y la transcripción a mano discrepan

**Fecha:** 2026-08-24 · **Estado:** aceptada, **escrita ANTES de transcribir la
primera tabla**. **Amplía §16**, que da el criterio de L4 sin umbral y sin regla de
adjudicación

## Contexto

El criterio de aceptación de L4, literal de §16: *«La verdad derivada reproduce las
tablas a mano»*. **No tiene umbral y no dice qué pasa cuando discrepen.** Y van a
discrepar, por una razón que no tiene nada que ver con el código:

**Las 30 transcripciones las hace UNA persona, y la tasa de error de una persona
transcribiendo tablas no es cero.** Un solo desliz da 29/30 y el hito «falla» por
algo que no habla del producto.

**Y el fallo que de verdad importa es el otro.** Sin regla escrita, la salida
cómoda ante una discrepancia es **ajustar el fixture hasta que pase**. Eso es la
regla del fichero congelado del revés —*«si un test falla contra un fichero
congelado, el fallo está en el código»*— y aquí es peor que en cualquier otro
sitio, **porque el fixture ES el instrumento de medida del hito**. Un instrumento
que se ajusta hasta que el resultado salga bien no mide nada.

La asimetría que lo decide: **el que elige la muestra, el que transcribe y el que
escribe el código son la misma persona.** Todo lo que dependa de su buena fe hay
que sacarlo de su buena fe y meterlo en una regla previa.

## Decisión

**Cuatro reglas, y se escriben antes de mirar la primera tabla.**

### 1. El orden de sospecha: PRIMERO EL CÓDIGO, SEGUNDO LA TRANSCRIPCIÓN

Ante una discrepancia, la primera hipótesis es que **el código está mal**. La
segunda, que la transcripción está mal. **Nunca «ajusto el fixture y sigo».**

Es el mismo orden que `.claude/rules/tests.md` ya fija para los golden —*«primero
el código, segundo el test, NUNCA el golden file»*— aplicado al único instrumento
de L4.

### 2. Cada discrepancia se ADJUDICA una a una, delante del usuario, y su causa se publica

No hay adjudicación en lote ni en silencio. Cada una se lleva a la conversación con
la tabla delante, y sale con **una de dos causas, que son hechos distintos**:

| Causa | Qué significa | Qué se hace |
|---|---|---|
| **fallo del código** | `truth.derived` produce algo que el documento no dice | se arregla el código, con su test |
| **error de transcripción** | la persona copió mal una celda | se corrige el fixture **con su razón escrita** |

**Sólo la primera habla del producto.** Confundirlas es lo que convierte un
instrumento en un espejo.

### 3. El número publicado SEPARA las dos

No se publica «30 de 30». Se publica:

> **N de 30 coinciden.** De las M discrepancias, **X eran del código** —arregladas,
> con su test— y **Y eran errores de transcripción**, corregidos con su razón.

**Un 30/30 que salió corrigiendo fixtures vale cero. Un 27/30 con las tres
explicadas vale mucho**, porque dice exactamente qué encontró el instrumento.

### 4. Si el código se arregla, se RE-COMPARAN LAS 30

No sólo la que falló. Un arreglo cambia el comportamiento de todo el conversor, y
las otras 29 se compararon contra la versión anterior. Comparar sólo la que falló
publicaría 30 resultados de los que 29 son de otro código.

Es la misma razón por la que el arnés de mutantes recorre la suite entera y no sólo
la suite objetivo del mutante.

## Lo que sostiene que las transcripciones sean independientes

**Se transcriben del PDF, no del XML.** La verdad se deriva del XML, así que
transcribir del XML sería comparar el XML consigo mismo y el criterio pasaría por
construcción.

**Se transcriben las 30 de una sentada y se congelan con hash ANTES de correr la
comparación ni una vez.** El sello de la congelación va al plan. Si se pudiera
comparar, corregir y volver a comparar, la transcripción dejaría de ser
independiente en la segunda vuelta.

**Y se declara cuáles ya se habían visto.** Cuatro tablas del corpus se inspeccionaron
a mano durante el arreglo del grupo de filas —`BOE-A-2026-7193`, `BOE-A-2026-7172`,
`BOE-A-2026-5542` y `BOE-A-2026-6080`—. Si alguna cae en la muestra **no se
excluye**, porque excluirla sesgaría la selección estratificada; se **declara al
lado del número**, que es información que quien lo lea necesita para pesarlo.

## Alternativas descartadas

**Poner un umbral —«28 de 30 basta»— y no adjudicar.** Es lo que parece práctico y
es lo que hace inútil el instrumento: un umbral sin adjudicación convierte dos
fallos del código en «dentro de tolerancia», que es justo lo que no se puede
tolerar cuando lo que falla es la verdad de referencia.

**Transcribir dos veces con separación temporal, como el modo `ANNOTATED`.** Es más
riguroso y mide el acuerdo intra-anotador. Se descarta **por coste**: son otras 2,5
h y L4 tiene 8-10 en total. Se declara: **el acuerdo intra-anotador de estas 30
transcripciones NO está medido**, y por eso la causa «error de transcripción» se
adjudica caso a caso en vez de estimarse.

**Que otra persona transcriba.** Es la solución correcta y no está disponible.
Queda escrito como lo que cerraría el hueco de verdad.

## Trade-off

Lo que se paga: **la adjudicación es lenta y es manual**, y no se puede automatizar
sin volver a meter en el código la decisión que se le está quitando.

Lo que se compra: que el número de L4 signifique algo. Y que la respuesta a *«¿por
qué salió 30 de 30?»* no pueda ser nunca *«porque fui ajustando»*.
