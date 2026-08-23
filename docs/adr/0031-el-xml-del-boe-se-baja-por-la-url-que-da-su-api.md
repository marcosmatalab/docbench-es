# ADR-0031 · El XML del BOE se baja por la URL que da su propia API, con cinco condiciones

**Fecha:** 2026-08-23 · **Estado:** aceptada, con consulta al organismo en curso.
**No toca el manual**: §9.4 ya dice que `fetch` baja el PDF y el XML del mismo
identificador. Esto decide **por qué ruta** y **bajo qué condiciones**

## Contexto

Al preparar L3 se leyó el `robots.txt` del BOE **antes** de la primera petición de
cosecha, y apareció un conflicto que no estaba previsto en ningún sitio del repo.

**Fuente 1 — `https://www.boe.es/robots.txt`, leído el 2026-08-23, HTTP 200,
487.339 bytes, 13.897 líneas, un solo bloque `User-agent: *` y sin `Crawl-delay`.**
Línea 25, literal:

```
Disallow: /diario_boe/xml.php?
```

Ésa es **exactamente** la URL del XML: la fuente de toda la verdad `DERIVED`, y la
razón por la que el BOE es la entidad de referencia del proyecto.

**Fuente 2 — la documentación oficial de la API**,
`https://www.boe.es/datosabiertos/documentos/APIsumarioBOE.pdf`, leída el
2026-08-23, HTTP 200, 196.952 bytes. Especifica el campo, literal:

> `url_xml` — «URL de la versión XML en https://www.boe.es» — `CHAR(150)` —
> ejemplo: `https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-10761` —
> cardinalidad **`[1..1]`**

O sea que **el propio organismo documenta esa URL como campo obligatorio de su
API**. Comprobado además sobre el sumario real del 2026-08-03: los 205 ítems
traen `url_xml` apuntando ahí, y **no hay ninguna ruta alternativa** — el sumario
sólo entrega `url_pdf`, `url_html` y `url_xml`.

**Fuente 3 — las condiciones de reutilización**,
`https://www.boe.es/informacion/aviso_legal/`, leídas el 2026-08-22 (sondeo),
HTTP 200, 36.293 bytes; Resolución de la Agencia de 27 de junio de 2024. Literal:

> «Las presentes condiciones permiten la reutilización de los documentos sometidos
> a ellas **para fines comerciales y no comerciales** […] La autorización de
> reutilización incluye: **La copia, reproducción, distribución y difusión
> pública** de la información. La **modificación, adaptación, extracción,
> reordenación y combinación** de la información en orden a crear obras derivadas».

Y **no menciona ninguna restricción técnica sobre el método de obtención**.

## Decisión

**El XML se baja por la `url_xml` que entrega la API**, con las cinco condiciones
de más abajo, y con una consulta al organismo abierta en paralelo.

**El argumento, y qué lo sostiene.** `robots.txt` es una directiva de **indexación
para buscadores**, no un término de licencia. Lo dice su propio contenido: ese
`Disallow` convive con

```
Disallow: /diario_boe/txt.php?*lang=ca
Disallow: /diario_boe/txt.php?*lang=va
Disallow: /diario_boe/txt.php?*lang=gl
```

y catorce más por el estilo, que son **directivas de contenido duplicado**: sacan
del índice las *representaciones alternativas del mismo documento*. El XML es
exactamente eso: la representación alternativa del PDF y del HTML. No es una
prohibición de acceso; es una instrucción para que un buscador no indexe tres
veces el mismo boletín.

**Lo específico gana a lo general.** El mismo organismo publica (a) una API cuya
documentación oficial entrega esa URL como campo obligatorio y (b) una licencia
que autoriza expresamente extraer y crear obra derivada. Frente a eso, una
directiva genérica de indexación no es el instrumento que regula el acceso.

**Y no se elude ningún control.** La URL es pública, sin autenticación, sin muro,
sin token. No hay medida técnica que sortear.

## Las cinco condiciones, que no son adorno

Son lo que hace defendible el argumento. **Si alguna se rompe, el argumento se cae
entero**, no se debilita.

1. **DESCUBRIMIENTO SÓLO POR LA API.** Nunca siguiendo enlaces, nunca adivinando
   identificadores, nunca recorriendo el sitio. **Ésta es la que sostiene todo lo
   demás**: la defensa es *«soy cliente de una API documentada, no un rastreador»*,
   y enumerar ids o spiderear la convierte en falsa de golpe. Va como **invariante
   con test**, no como buena intención: toda URL que se pide tiene que venir de un
   campo del sumario, y el test se cae si aparece una construida.
2. **1 petición por segundo, sin paralelismo**, declarado en `entities/boe.yaml` y
   no en el código.
3. **`User-Agent` que identifique el proyecto** con la URL de su repositorio.
4. **Caché agresiva: nunca se vuelve a bajar lo que ya está en el manifiesto.**
5. **Atribución exacta, con las palabras de la licencia**: «Basado en datos de la
   Agencia Estatal Boletín Oficial del Estado», más la **fecha de última
   actualización**, en el manifiesto y en cualquier publicación del corpus.

## La consulta, que va en paralelo y no en lugar de

Se prepara un correo al BOE por el cauce de datos abiertos preguntando si el uso
de `url_xml` a través de la API, a 1 rps e identificado, es el uso previsto. **No
bloquea nada.** Y si contestan, **su respuesta vale más que este ADR** y lo
sustituye: va al repo con su fecha.

## Alternativas descartadas

**Usar `url_html` en vez de `url_xml`.** Está permitida por `robots.txt` y es la
salida cómoda. Se descarta porque **cambia lo que L3 y L4 son**: `boe_xml` existe
para parsear el XML oficial, que es lo que hace que la verdad sea `DERIVED` y
gratis. Sobre HTML la verdad dejaría de ser oficial y pasaría a ser otra
extracción más — el juez volvería a ser concursante, que es la regla de oro 1.

**Esperar a la respuesta del organismo antes de cosechar.** Descartada porque
bloquea el hito por tiempo indefinido sobre una consulta que puede no contestarse,
y porque las tres fuentes ya autorizan. La consulta mejora la evidencia; no es una
condición para actuar sobre ella.

**Cambiar de entidad de referencia.** Tumba medio manual y no resuelve nada: el
conflicto `robots.txt` contra API documentada lo tiene cualquier organismo con
portal de datos abiertos.

## Trade-off

Lo que se paga: **una directiva del origen dice literalmente que no**, y eso hay
que sostenerlo por escrito cada vez que alguien lo mire. Por eso el ADR cita las
tres fuentes literalmente y con su fecha y su tamaño en bytes, en vez de
resumirlas: quien discrepe tiene que discrepar con el texto, no con mi paráfrasis.

Lo que se compra: la verdad `DERIVED` a escala y gratis, que es la premisa
económica del proyecto entero. Y un precedente escrito para el siguiente adaptador
que se encuentre lo mismo, que serán casi todos.
