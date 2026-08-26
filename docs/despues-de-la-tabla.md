# Después de la tabla

Lo que se decidió **no hacer todavía**, con el análisis y los números que lo sostienen,
para que no se pierda y para que no abra alcance con L5 sin cerrar.

> **Este documento ACUMULA, así que NO lleva tope de líneas.** La distinción es la de
> `tests/unit/test_documentos_que_sostienen.py`: los que SOSTIENEN —`README.md`,
> `docs/reading-order.md`, `docs/como-se-mide-aqui.md`— son la primera pantalla de quien
> no va a volver y su tamaño es un **requisito**; los que ACUMULAN discuten con su propio
> pasado y su tamaño es una **consecuencia**. Éste es de los segundos, y el test lo afirma
> en las dos direcciones para que nadie «arregle» un rojo poniéndole un tope.

**Por qué un fichero y no seis.** Cada apartado de aquí acabará en su sitio —un ADR, un
hito de `MANUAL.md` §16, un límite—, pero repartirlos **hoy** sería tocar los documentos
normativos con L5 a medias. Viven juntos y declarados como aparcados hasta que la tabla
exista; al cerrar L5 se distribuyen.

**Nada de esto se ha ejecutado.** Escrito el **26 de agosto de 2026**.

> **TODOS LOS NÚMEROS DE OTROS BANCOS VAN MARCADOS COMO CITADOS.** No se han medido aquí
> y no se pueden reproducir con un comando de este repo, así que no son resultados de
> `docbench-es` y no entran en `RESULTS.md`. La regla de la casa —todo número publicado
> lleva su comando— se cumple diciendo de dónde sale cada uno, no fingiendo que es propio.

---

## 1 · La curva coste-exactitud con presupuesto real

### El encuadre, que es lo que decide todo lo demás

**No es un ranking: es una curva.** El titular no es *«quién gana»* sino:

> **¿CUÁNTO HAY QUE PAGAR PARA SUPERAR LO GRATIS?**

Esa pregunta no la ha contestado nadie para el español. Y cambia lo que son los
extractores locales de L5: dejan de ser «la mitad de abajo del campo» y pasan a ser **la
línea base contra la que se mide lo que cuesta dinero**. Es la misma medición con otra
historia, y la segunda es la que se comparte.

### El presupuesto es 20 € como máximo, y el objetivo es cero

Va escrito como **restricción de diseño**, no como limitación que disculpar. Un banco que
sólo se puede reproducir con tarjeta de crédito no es reproducible.

#### Tramo 0 € — y es el que hay que agotar primero

* **los locales de L5**, ya medidos (`RESULTS.md`, sección de B5-bis);
* **VLM locales en la RTX 5080**: 16 GB dan para modelos cuantizados. *(Citado de
  ExtractBench: los auto-alojados no van mal — Qwen3.6 35B **87,33** y NuExtract3
  **82,35**.)* Su coste entra como **tiempo de GPU, no como factura**, así que encaja con
  `runs_locally=True` y con el *sin red y sin gastar* del quickstart.

Es lo único que de verdad contesta a *«por mí no gastaría nada»*.

#### Tramo ~20 € — sobre muestra estratificada REDUCIDA, no sobre los 616

Con **25 documentos ricos en spans** y una media supuesta de **15 páginas por documento**
→ **~375 páginas**. *(La media del corpus entero es 8,7 páginas/documento; 15 es más alta
porque los ricos en spans son más largos. El supuesto es comprobable contra el censo de
páginas antes de comprometer un euro.)*

| extractor por API | $/página *(citado)* | × 375 páginas |
|---|---|---|
| GPT-5.4 Nano | 0,0021 | **0,79 $** |
| Gemini 3.5 Flash | 0,0100 | **3,75 $** |
| LlamaExtract Cost-Effective | 0,0100 | **3,75 $** |
| LlamaExtract Agentic | 0,0312 | **11,70 $** |
| | | **19,99 $** |

Cuatro puntos de pago más el tramo gratis: **eso ya es una curva.**

#### Fuera de presupuesto, y se publica el precio

| extractor | $/página *(citado)* | × 375 páginas |
|---|---|---|
| Claude Code (Opus 4.8) | 0,1617 | 60,64 $ |
| Codex (GPT-5.5) | 0,2783 | 104,36 $ |
| Reducto Deep Extract | 0,3444 | 129,15 $ |

*«No se midió Reducto porque sobre esta muestra cuesta 129 $»* es una frase honesta y
útil. **Publicar el precio de lo que NO se midió es un dato, no una excusa** — y es la
misma regla que ya rige aquí para los estratos vacíos y para las familias que faltan.

### El dato que conviene guardar ahora, porque desmonta un supuesto del sector

*(Citado de ExtractBench.)*

| | $/página | nota |
|---|---|---|
| Reducto Deep Extract | 0,3444 | 90,44 |
| LlamaExtract Agentic Plus | 0,0811 | **95,59** |

**Cuatro veces más caro, cinco puntos por debajo.** El precio no compra exactitud, y eso
es exactamente lo que **una curva enseña y un ranking no**.

### Lo que NO hay que hacer, escrito para que no vuelva

* **NO elegir las páginas «porque son difíciles».** Eso es seleccionar sobre el resultado,
  y es el ataque que haría cualquiera. Se estratifica por lo que el documento **ES**
  —spans, cruce de página, longitud—, **nunca** por lo que el extractor **HACE** con él, y
  se re-pesa hacia la población. Es la regla que ya se aplicó al elegir la ventana de L3
  sobre el tramo con más descarte de los tres medidos.
* **NO comparar independiente con n pequeña.** Con σ≈0,25 en TEDS, n=25 da ±0,10, y el
  campo está apretado entre 0,85 y 0,96: la mitad de los pares saldrían indistinguibles.
  La comparación tiene que ser **PAREADA** —los mismos documentos por todos— y analizada
  como tal. Es para lo que existe **L6**, con McNemar y bootstrap agrupado por documento.
* **La integración por API NO es un envoltorio de 2 a 11 líneas.** Auth, reintentos,
  límites de tasa y contabilidad de coste. Ahí es donde se fueron las 111.142 líneas del
  `src/` de ExtractBench *(citado)*. **Estímalo antes de comprometer horas**, y estímalo
  con el patrón de este repo: pre-registro con su intervalo, no una corazonada.

**Va a L12**, que ya existe en §16 con esta finalidad. **No es un hito nuevo.**

---

## 2 · Los agentes de código: un GENERADOR, no un extractor

### Una distinción que el sector no hace, y que hay que escribir

La palabra *«agéntico»* cubre **tres mecanismos que no se parecen**, y los bancos los
ponen en la misma tabla:

| qué es | mecanismo |
|---|---|
| LlamaExtract Agentic | parseo + esquema + troceado agéntico |
| Reducto Agentic OCR | detección de maquetación → VLM por bloque → **multipasada** con bucle de auto-corrección *(«un bucle de revisión automatizado sobre los datos parseados», sus palabras)* |
| Codex · Claude Code | **escriben código** que extrae |

**Y la diferencia que importa: sólo el tercero deja un artefacto congelable.** El bucle de
Reducto ocurre **dentro de su API en cada llamada** — no se puede congelar, sólo medir
muchas veces y publicar la varianza. Un agente que escribe un script deja **un fichero**
que se puede hashear, leer y volver a correr.

### El encuadre, que es lo que lo convierte en experimento

> **Un agente que escribe código de extracción no es un extractor: es un GENERADOR de
> extractores.** Y un generador no se mide como un extractor — se mide por si lo que
> produce **generaliza**.

### El experimento

1. el agente escribe código sobre un **conjunto de desarrollo**;
2. **se congela el código con su `sha256`** → a partir de ahí es un extractor normal:
   determinista, inspeccionable y reproducible por cualquiera;
3. se mide sobre un **conjunto reservado** que no ha visto;
4. **la diferencia entre los dos es el hallazgo.**

Si la brecha es grande, *«los agentes ganan a los modelos»* es en parte artefacto de haber
visto los datos. Si es pequeña, generalizan de verdad y es un resultado gordo. **Las dos
respuestas valen; hoy no se sabe cuál es.**

### Por qué nadie lo ha hecho

ExtractBench publica Codex con **93,57** y Claude Code con **87,09** *(citados)* como
**números únicos, sin varianza y sin artefacto**. Para algo que no es determinista, eso es
un agujero metodológico — y **no pueden cerrarlo, porque nunca congelaron el código**.

Aquí sí se puede: muestreo estratificado, conjuntos congelados con hash, y la costumbre de
declarar la contaminación — que ya se ejerció en L4 con `BOE-A-2026-5979-t15`.

### Lo que hay que declarar ANTES de intentarlo

Va escrito hoy aunque se haga dentro de un año:

* **LA FUGA.** Si el código se congela de una corrida sobre la muestra y luego se mide
  sobre **esa misma** muestra, el agente vio las respuestas. Desarrollo y reservado tienen
  que ser **disjuntos**, y el reservado no lo puede haber visto **nunca**.
* **La contaminación se declara como en L4**: si un conjunto se tocó, se marca, y su
  coincidencia no cuenta como evidencia independiente.
* **El coste es tiempo de agente**, un puñado de corridas — **no** es por página. Eso lo
  pone al alcance del presupuesto de arriba, justo al revés que medirlos como extractores
  sobre el corpus entero.
* **Un agente congelado entra en la tabla como «el código que este agente escribió»**,
  nunca como «el agente». La fila nombra **el artefacto y su hash**, no el producto.

### Y una propiedad que nadie más puede ofrecer

**Si el código está congelado, se puede LEER.** ¿Escribió algo general, o se ajustó a lo
que vio? Esa pregunta es contestable **sólo aquí**.

Esto **no es un extractor más**: es un hito propio, y probablemente un artículo corto.
Queda anotado **con su nombre y sin hito asignado**. Se decide cuándo, después de la tabla.

---

## 3 · El resto de lo aparcado

Juntos, con una línea cada uno, para que no haya cuatro sitios donde buscar.

* **CUERPO además de tablas** *(v0.2.0)* — el XML del BOE ya lo trae, así que es métrica
  nueva sobre corpus **ya descargado**. **No TEDS**: distancia de edición normalizada o F1
  de palabras.
* **DIAGRAMAS** — estrato declarado y **vacío** en L12b. El XML dice que hay un `<img>`
  —489 medidos, 21 en documentos con tabla— y **no dice qué hay dentro**. Sin verdad
  derivada, la única salida es anotación humana.
* **MULTILINGÜE con EUR-Lex** — un adaptador, no un proyecto: mismo documento en 24
  idiomas, con Formex XML y PDF, API CELLAR. Lo valioso **no es la cobertura**: es que es
  **corpus paralelo**, y separa *«el idioma es más difícil»* de *«los documentos son más
  difíciles»* — que es lo que PulseBench-Tab no puede hacer con 9 idiomas y documentos
  distintos en cada uno. **Sondeo previo obligatorio**, como se hizo con el BOE.
* **MODELO DE EXTRACCIÓN PROPIO — NO**, y queda escrito como **descartado con su razón**:
  rompe la regla de oro 1 —el juez no puede ser concursante— y además los modelos
  especializados están perdiendo *(citado: NuExtract3 **82,35**, y **37,72** en documento
  largo, contra **95,59 / 94,41** de un sistema)*.
* **EL ENRUTADOR de L17** es el modelo que **sí** cabe en la 5080: un clasificador sobre
  longitud, densidad de tablas, spans y capa de texto. **No extrae: elige.**
* **El número de trabajadores de `pytest -n auto`** — la hipótesis es que hay un **mínimo
  por debajo de 14**, porque cada trabajador de xdist importa la suite entera (~900 ms
  medidos en L2, y dominan) y porque la 3D V-Cache del 9950X3D vive en **un solo CCD**,
  así que con 14 trabajadores algunos caen en núcleos sin caché apilada y **el reloj lo
  fija el más lento**. Se mide en 20 minutos: `-n 4, 6, 8, 10, 14`, tres corridas en frío
  cada una, con la predicción escrita antes. **Candidato a lo primero después de la
  tabla**, y con una consecuencia doble: margen de puerta gratis, y `-n auto` deja de ser
  un valor por defecto para pasar a ser **un número medido con su condición de máquina
  declarada**.

---

**Nada de esto se ejecuta.** Se escribió una vez, con fecha, y se vuelve cuando exista la
tabla.
