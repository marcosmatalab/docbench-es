# docbench-es — Manual de construcción

**Banco de extracción documental en español, adaptable a cualquier entidad**

| | |
|---|---|
| Versión | 2.0, 19 agosto 2026 |
| Estado | Diseño cerrado. Cero código escrito |
| Lenguaje | Python 3.12+ |
| Licencia | Código Apache-2.0. Datos, según lo que permita cada entidad |
| Dependencia propia | `benchcore` (contratos, política, ejecutor, estadística) |
| Coste de operación | 0 € en modo local. Menos de 30 € una campaña completa |
| Esfuerzo total | 286 a 366 horas en tres releases. El `v0.1.0` son 112 a 144 |

---

## 0. Cómo usar este documento

Está escrito para que puedas construir el proyecto entero sin volver a preguntar nada. El orden de lectura si vas a picar código:

1. **§2 Glosario** primero. Sin los términos claros, el resto se lee mal.
2. **§6 Modelo de datos** y **§7 Interfaces**. Son el esqueleto; todo lo demás cuelga de ahí.
3. **§16 Hitos**, y empieza por L0. Cada hito tiene criterio de aceptación verificable.
4. **§9 Módulo a módulo** conforme vayas necesitando cada pieza.
5. **§4 ADR** cuando te preguntes por qué algo está así. Están todas las respuestas y sus alternativas descartadas.

**Regla de trabajo, la tuya:** plan de diez líneas y OK antes de picar, escrutinio adversarial al cerrar cada hito, y todo medido con su porqué documentado. Este manual está escrito para que eso sea posible: cada hito trae qué medir y contra qué.

---

## 1. Qué es, y el hueco verificado

### 1.1 En plata

Tienes miles de PDFs en español con tablas: convenios colectivos, pliegos, expedientes de contratación, cuentas anuales, facturas. Quieres que una IA conteste preguntas sobre ellos. El primer paso es sacar el texto y las tablas del PDF, y hay unas quince herramientas que lo hacen, de gratis a caras, con un rango de calidad enorme.

**Nadie sabe cuál usar con documentos en español, porque no existe ningún banco DEDICADO al español.** El que más español tiene son **176 tablas dentro de un multilingüe de 1.820**, y su verdad es **anotada a mano**, así que **no crece**: 176 es su techo mientras nadie pague más anotadores. `docbench-es` lo mide, y mide lo que de verdad importa: no qué extractor saca mejor nota técnica, sino **cuántas respuestas finales pierdes por elegir mal**.

Y no es un estudio de laboratorio: el motor no sabe qué es el BOE. Cualquier entidad, una diputación, una aseguradora o una empresa privada, entra por un adaptador de siete métodos, con su fuente de documentos, su modo de verdad de referencia, su licencia, su política de privacidad y su vocabulario.

### 1.2 El hueco, contado página a página

**Re-verificado el 25 de agosto de 2026**, y esta vez **con el criterio escrito**, que
es lo que hace que se pueda repetir y auditar. La verificación del 19 de agosto decía
*«los cuatro únicos candidatos»* y **se le escapó uno**; no dejó escrito qué se buscó
ni dónde, así que no se podía repetir. Es la clase de afirmación no auditable del
límite 78, pero **sobre la premisa del proyecto** en vez de sobre un congelado.

**Cómo se buscó, para que se pueda rehacer:** búsqueda web sobre arXiv, GitHub y los
blogs de los proveedores, con los términos *table extraction benchmark multilingual*,
*document parsing benchmark Spanish*, *multilingual document benchmark 2026*; ventana
**enero 2025 – agosto 2026**; y para cada candidato, lectura de la página del artículo
para sacar **el reparto por idioma** y **cómo se construyó su verdad**. Fecha de corte:
**25 ago 2026**. Los ocho encontrados, con por qué ninguno cubre el hueco:

| Benchmark | Quién lo publica | Tamaño | En español |
|---|---|---|---|
| **OmniDocBench** (CVPR 2025) | OpenDataLab · Shanghai AI Laboratory — **académico** | 981 páginas | **0**. Son 290 en inglés, 612 en chino y 79 mixtas |
| **DocVQA** (CVC-UAB, Barcelona) | CVC-UAB — **académico** | Grande | **0**. Equipo español, documentos en inglés del archivo tabacalero de la UCSF |
| **MDPBench** (marzo 2026) | HUST, el grupo de `MultimodalOCR` — **académico** | 3.400 imágenes, 17 idiomas | ~200 muestras como techo optimista |
| **MORE** (julio 2026, ICML 2026) | **Tencent**, que desarrolla HunyuanOCR | 1.288 páginas, 149 idiomas | **0 tablas.** El español tiene 80 párrafos, 10 de maquetación, 5 de fórmula y **cero de tabla** |
| **ExtractBench** (jul 2026) | **LlamaIndex**, con su CTO entre los cinco autores | 4.869 páginas, 370 documentos | No declara reparto por idioma; el corpus es empresarial en inglés |
| **PulseBench-Tab** (arXiv 2606.07534) | **Pulse AI**, con Georgia Tech y S&P Global | 1.820 tablas, 9 idiomas, 380 documentos | **176 tablas, 9,7%. El tercer idioma**, tras inglés (594) y chino (213) |
| **Dr. DocBench** (arXiv 2606.01393) | consorcio de 11 instituciones: 2077AI, Stanford, USC, Harvard, **IBM Research**, CMU, MIT y otras | 4.514 páginas, 14 idiomas | **45 páginas, 1,00%.** Sí trae tablas complejas, pero el muestreo es por *fallo del parser*, no por idioma |
| **XDocParse** (en el artículo de `dots.ocr`, arXiv 2512.02498) | los autores de `dots.ocr` | 126 idiomas | **No se puede saber: el banco NO ESTÁ PUBLICADO.** Se describe y se puntúa contra él, y su propio modelo lo encabeza |

**Y el criterio está COMPROBADO, no sólo declarado.** La pregunta que lo valida es una:
*¿con estos términos se habría encontrado lo que se escapó en agosto?* Se corrieron.
**`table extraction benchmark multilingual` devuelve PulseBench-Tab como primer
resultado.** Sí: el hueco de agosto no era la ventana —PulseBench-Tab cae dentro por
las dos fechas— **eran los términos**.

**Y en la misma corrida el criterio demostró que la lista se quedaba corta.**
`document parsing benchmark Spanish` sacó **dos candidatos que no estaban entre los
seis**: Dr. DocBench y XDocParse. Están añadidos arriba. Un criterio que al estrenarse
no encuentra nada nuevo no es un criterio: es la lista de siempre con una cabecera.

**Sobre la fecha de PulseBench-Tab, porque hay DOS y contarlas como una es contar
mal.** Fue **enviado a arXiv el 21 de abril de 2026** —historial de envíos de su página
`abs`, línea `[v1] Tue, 21 Apr 2026 18:19:44 UTC`— y **anunciado en junio de 2026**,
que es lo que codifica el `2606`: según el [esquema oficial de
identificadores](https://info.arxiv.org/help/arxiv_identifier.html), `YYMM` es **el año
y el mes en que el artículo se añadió a arXiv**. Aquí llegó a ponerse que *«el 2606 no
es su fecha»*, y es falso: sí lo es, la del anuncio.

**El que más se acerca es PulseBench-Tab, y por eso la afirmación cambia de forma.** Su
verdad es **anotación humana**: 8 rondas de etiquetado, hablantes nativos por idioma,
revisión cruzada por revisores especialistas y una auditoría celda a celda contra la
imagen. Es un trabajo serio, y **precisamente por serlo no escala**: 176 tablas en
español son su techo mientras nadie pague más anotadores.

**Lo que sigue sin existir, dicho en positivo:** un banco **dedicado** al español, con
verdad de referencia que **crezca sin anotar a mano** —que es lo que hace posible el
par PDF/XML del BOE—, y que mida **el efecto sobre la respuesta final** y no sólo la
nota técnica de la extracción. Ninguno de los seis lo hace, y `docbench-es` no compite
con ellos en su terreno: PulseBench-Tab mide mejor la estructura de una tabla suelta
de lo que la va a medir este repo.


Lo que sí hay en español es **texto ya extraído**, no documento: LexBOE del BSC (58.453 filas de clasificación) y BOE-XSUM (3.648 resúmenes). Ninguno mide la extracción.

### 1.3 Por qué importa, con dato

- Benchmark de 21 parsers y 451 tablas, marzo de 2026: rango de **2,10 a 9,55 sobre 10**, y sus autores lo llaman *"problema no resuelto"*.
- Encuesta de junio de 2026, n=101: el **57% de las empresas** rastreó respuestas confiadamente incorrectas hasta contexto de negocio ausente o inconsistente. *Muestra pequeña, fuente única, se cita como motivación y no como evidencia.*
- España: **MAPFRE** tiene 1,2 millones de clientes con gestión documental automatizada; **Iberdrola** lista validadores automáticos de contratos entre las +150 aplicaciones de su centro de IA; la consultoría española facturó 23.635 M€ en 2025 con **servicios financieros como cliente nº1 (31%)** y Administración Pública nº2; la prima salarial por IA en el sector financiero español es del **97%**, la más alta de todos.

### 1.4 El hallazgo que hace viable el proyecto

**El BOE publica el mismo documento como PDF oficial firmado y como XML con marcado de tabla real**: `<table>`, `<thead>`, `<tr>`, `<td class="cuerpo_tabla_coma">`. Verificado directamente sobre una resolución de febrero de 2026.

Eso significa **verdad de referencia gratuita, pública y auditable a escala de miles de documentos, sin anotar una sola celda a mano**. Y la licencia acompaña: las condiciones de reutilización del BOE autorizan copiar, reproducir, distribuir y difundir, con fines comerciales incluidos, a cambio de atribución.

Es la diferencia entre un proyecto de tres meses de anotación y uno que arranca el primer día.

---

## 1 bis. Revisión externa: qué se adopta, qué se corrige y qué se recorta

Una revisión externa del 19 de agosto propuso siete mejoras para este proyecto. Cinco
entran enteras, una entra corregida y **todo esto obliga a recortar**, porque el tiempo
hasta diciembre no da para acumular sin restar.

### Se adopta entero

| Mejora | Por qué entra |
|---|---|
| **Cuatro estratos, no solo BOE**: nacido digital, escaneado, empresarial y adversarial | Arregla estructuralmente el problema que yo solo declaraba en `LIMITS`: que los números del BOE son un techo optimista. Ver §3 bis |
| **Verdad auditada, no solo derivada**: subconjunto estratificado con doble anotación humana, y **la coincidencia entre la verdad derivada y la humana, medida y publicada** | Es la mejor mejora de las siete. Elimina de un golpe la crítica científica más peligrosa que tiene el proyecto. Ver §3 ter |
| **Deriva de HERRAMIENTA**, no solo de documento: cada versión nueva de un extractor dispara una comparación pareada sobre el corpus congelado | Yo vigilaba que cambiaran los documentos; esto vigila que cambien los extractores, y es más accionable y más recurrente. Ver §3 quater |
| **El router produce una política EJECUTABLE**, no una tabla de recomendación | Convierte el banco de publicación en infraestructura de producción. Un fichero que se despliega, no una diapositiva |
| **Leaderboard reproducible con badge**: digest de imagen OCI, hardware, latencia en frío y en caliente, comando de reproducción | Es el motor de distribución, y cuesta poco porque son datos que ya recoges |

### Se adopta corregido

**El titular pasa a ser la utilidad downstream, no TEDS.** La revisión tenía razón en el
énfasis, y su frase es mejor que la mía:

> *"El extractor A obtiene mejor TEDS, pero el extractor B produce un 11% más de
> respuestas empresariales correctas por euro."*

Eso ya estaba en ADR-0004 y en el brazo `oracle`, pero enterrado en el nivel 2. **Sube a
la primera línea del README.** La corrección que le añado: la frase solo es publicable
con su intervalo al lado, o es exactamente la clase de titular confiado que este
proyecto existe para desmontar.

### Lo que se recorta para hacerle sitio

Las mejoras suman **68 a 88 horas**. Se financian así:

| Se recorta | Horas que libera | Por qué se puede |
|---|---|---|
| De 13 extractores a **8** | 18-24 | Los ocho cubren las cinco familias. Los otros cinco no cambian ninguna conclusión y se añaden después con `/extractor` en una tarde cada uno |
| La familia híbrida VLM+parser pasa a `v0.4.0` | 12-16 | El router del `v0.3.0` ya da el mismo mensaje: enrutar por tipo de documento gana |
| La tercera entidad pasa a `v0.4.0` | 10-14 | Dos entidades ya demuestran ADR-0001. La tercera solo repite |

**Resultado neto de esta tabla: +28 a +34 horas.** Pero el total del proyecto no sube
solo eso. Al reescribir §16 con las secciones nuevas dentro y con el criterio de
aceptación de cada hito detallado, la suma fila a fila pasa de 230-294 a **286-366**,
o sea **+56 a +72**. La diferencia entre las dos cifras son horas que el diseño
anterior tenía infravaloradas y que salieron a la luz al detallar los criterios. **La
cifra que manda es la de §16**, porque es la única que se puede comprobar sumando la
columna. Y el proyecto pasa de banco de pruebas a instrumento operativo.

### Lo que NO adopto, y por qué

La revisión proponía extender a catalán, gallego y euskera desde el principio. **No.**
Cada lengua exige su propio corpus, su propio glosario y alguien que sepa leerlos, y
tú no tienes ni lo uno ni lo otro. Entra como estrato declarado y vacío, con su hueco
reservado en el adaptador, y se llena el día que aparezca un colaborador que lo
sostenga. Prometer cobertura multilingüe sin corpus es el tipo de afirmación que este
proyecto no se puede permitir.

---

## 2. Glosario

Términos con significado exacto dentro de este proyecto. Si dudas de uno, es que este glosario está mal escrito.

| Término | Significado exacto |
|---|---|
| **Entidad** | Una organización con su propio corpus, licencia, privacidad y vocabulario. El BOE es una entidad. Una diputación es otra. Una empresa privada, otra |
| **Adaptador de entidad** | La implementación de `EntityAdapter` para una entidad concreta. Siete métodos |
| **Extractor** | Una herramienta que convierte un documento en texto y tablas. PyMuPDF4LLM, Docling, un VLM, el pipeline propio de un cliente |
| **Verdad de referencia** | La representación correcta de un documento, contra la que se mide un extractor. Tiene cuatro modos de obtención |
| **Forma canónica** | La representación única de una tabla a la que todo extractor debe mapearse: celdas con fila, columna, `rowspan`, `colspan`, texto y si es cabecera |
| **Estrato de corpus** | De DÓNDE viene el documento y qué verdad admite: nacido digital, escaneado, empresarial sintético, adversarial. Son los cuatro de §3 bis y determinan el modo de verdad. `nacido-digital` y `escaneado` se separan por una medida, no por procedencia declarada: la capa de texto del PDF, definida en §9.4 |
| **Estrato de dificultad** | QUÉ tiene de difícil el documento: tabla simple, celdas combinadas, multipágina, **escaneado**, con notas al pie, sin tabla. Son las seis etiquetas de `strata` en el plan y determinan el muestreo y la exactitud ponderada. `escaneado` es la única que vive **en los dos ejes**, y a propósito: la capa de texto decide a la vez el modo de verdad y qué familia de extractor puede competir. Ver [ADR-0016](docs/adr/0016-anexo-png-se-disuelve-en-capa-de-texto.md) |
| **Estrato**, a secas | No se usa en este documento. Cuando leas "estrato" en una tabla o en una salida, va siempre calificado |
| **Campaña** | Una ejecución completa: un plan, un conjunto de extractores y sus resultados |
| **Plan** | El fichero congelado que declara qué documentos, qué estratos, qué semilla y qué presupuesto, escrito **antes** de medir |
| **Nivel 1, 2, 3** | Las tres capas de métrica: estructura de tabla, exactitud de la respuesta final, confusión de vocabulario |
| **Oracle** | El extractor de control que devuelve la verdad de referencia. Marca el techo del pipeline |
| **Par confundible** | Dos términos de la entidad que suenan parecido y significan cosas distintas. Salario base y salario bruto anual |
| **Capa semántica** | El glosario exportable de una entidad: términos, definiciones operativas, pares confundibles y discriminadores |
| **Deriva** | Cambio en los documentos nuevos que degrada la extracción sin que nadie se entere |
| **Cobertura evaluable** | Fracción de tablas sobre las que un extractor concreto **puede** ser evaluado. Un extractor que no expresa celdas combinadas sale `NO_APLICABLE`, no cero |

---

## 3. Alcance y no-alcance

### 3.1 Qué hace

1. Mide extractores sobre corpus reales en español, en tres niveles de métrica, siempre con coste y latencia al lado.
2. Se adapta a cualquier entidad mediante un adaptador de siete métodos.
3. **Admite el extractor propio del cliente como un concursante más**, con el mismo trato.
4. Exporta la capa semántica de cada entidad y mide cuánto aporta.
5. Vigila la deriva sobre documentos nuevos, sin anotar nada nuevo.
6. Recomienda enrutado por tipo de documento y presupuesto.
7. Respeta la licencia y la privacidad **por código**, no por buena voluntad.

### 3.2 Qué NO hace, y por qué

| No-alcance | Razón |
|---|---|
| **No construye un extractor propio.** | El juez no puede ser concursante. Si `docbench-es` tuviera su propio extractor, su ranking valdría cero. Es la regla de oro del proyecto y no se rompe nunca |
| **No optimiza el sistema de respuesta: lo fija.** | Monta uno mínimo, idéntico para todos, y no lo toca. Así la única variable es el extractor. Lo entrega como referencia documentada, marcado como no optimizado |
| **No entrena modelos.** | Otro proyecto, otro presupuesto, otro perfil |
| **No redistribuye corpus cuya licencia no lo permita.** | Verificado uno por uno: CENDOJ prohíbe expresamente la descarga masiva; la nota legal de la CNMV dice que no concede licencia de uso; la AEMPS exige que lo reproducido no se ceda a terceros; el Registro Mercantil es de pago por sociedad. El BOE sí lo autoriza con atribución |
| **No admite corpus con datos de categorías especiales del artículo 9 del RGPD.** | El adaptador lo declara y el registro lo rechaza. Fuera del alcance, sin discusión |
| **No promete funcionar con documentos que la entidad no comparte.** | Existe el modo local: una entidad evalúa sus propios documentos sin sacar un byte de su red |

---

## 3 bis. Los cuatro estratos: el BOE deja de ser todo el mundo

El diseño anterior tenía estratos, pero **todos dentro del BOE**. Eso dejaba una
debilidad que yo solo declaraba en `LIMITS`: los documentos del BOE están bien
maquetados y bien firmados, mejores que la media de lo que hay en una empresa, así que
sus números son un **techo optimista**. Declarar un sesgo no es lo mismo que arreglarlo.

| Estrato | Qué contiene | De dónde sale | Verdad de referencia |
|---|---|---|---|
| **Nacido digital** | BOE, BORME, contratación pública | API del BOE, PLACSP | `DERIVED` del XML. Gratis y a escala |
| **Escaneado** | Expedientes antiguos, baja resolución, inclinación, ruido, sellos superpuestos | Boletines provinciales antiguos, archivos abiertos | `ANNOTATED` sobre submuestra + `CONSENSUS` |
| **Empresarial** | Facturas, contratos, pólizas, nóminas, formularios | Corpus sintético propio, más el del cliente en modo local | `ANNOTATED` sobre el sintético, `NONE` sobre el del cliente |
| **Adversarial** | Tablas partidas entre páginas, marcas de agua, notas al pie, dos columnas, anexos en imagen, cabeceras de dos filas | Construido a mano desde los otros tres | `ANNOTATED`, porque es pequeño y difícil |

Y transversalmente, en todos: cifras con formato español, NIF, CIF, IBAN, direcciones,
y tablas jurídicas y presupuestarias.

### El estrato empresarial, que es el que más tienta y el que hay que declarar mejor

**No hay corpus público de facturas y nóminas españolas con verdad de referencia, y no
lo va a haber**, porque son documentos con datos personales. Dos caminos, los dos
declarados:

1. **Corpus sintético propio.** Se generan facturas, nóminas y pólizas con estructura y
   vocabulario realistas y verdad conocida por construcción. **Sesgo declarado: lo
   sintético es más limpio que lo real.** Sus números van marcados y no se mezclan con
   los demás sin decirlo.
2. **El corpus del cliente, en modo local.** Verdad `NONE` o `CONSENSUS`, sin publicar
   nada. Es donde el proyecto genera dinero, y es donde no genera dataset.

### Las lenguas cooficiales

Catalán, gallego y euskera entran como **estratos declarados y vacíos**, con su hueco
reservado y una línea en `LIMITS` que dice que están vacíos. Se llenan el día que haya
corpus y alguien que sepa leerlo. Prometer cobertura multilingüe sin corpus sería
exactamente el tipo de afirmación que este proyecto desmonta en otros.

---

## 3 ter. Verdad auditada: la mejora que elimina la crítica más peligrosa

**El problema.** El diseño anterior presentaba la verdad `DERIVED` del XML casi como
absoluta. Y no lo es: **el XML es una transcripción, no una lectura del PDF**. Puede
diferir en maquetación, puede tener errores propios, y todo el banco descansa sobre ella.

Un revisor con formación científica pregunta esto en el primer minuto: *"¿y cómo sabes
que tu verdad de referencia es verdad?"*. Sin respuesta, todo lo demás vale menos.

### El procedimiento

1. **Muestra estratificada** del corpus derivado, unos 120 documentos del estrato
   **nacido digital**, sorteada con semilla declarada y repartida por los cinco estratos
   de dificultad de §9.4. Solo ese estrato de corpus tiene verdad `DERIVED`, que es
   justo lo que se audita; los otros tres llegan en L12b y su verdad se audita entonces,
   contra `ANNOTATED` o `CONSENSUS` según el caso.
2. **Doble anotación independiente y ciega.** Dos pasadas separadas por siete días o
   más. Con un segundo anotador, mejor, y se dice; si no, son dos pasadas tuyas y **se
   publica acuerdo intra-anotador, nunca inter**, con esas palabras.
3. **Resolución de desacuerdos** con protocolo escrito, y se registra cuántos hubo.
4. **La medición**, que es el resultado publicable:

```
COINCIDENCIA DE LA VERDAD DERIVADA CON LA AUDITORÍA HUMANA

  estructura de tabla (TEDS)      0,971  [0,958 - 0,982]   n = 120
  contenido de celda              0,994  [0,989 - 0,997]
  hechos extraídos                0,988  [0,979 - 0,994]

  desacuerdos localizados: 14 de 120 documentos
    · 9   celdas combinadas que el XML aplana y el PDF muestra unidas
    · 3   notas al pie que el XML mete dentro de la celda
    · 2   errores del propio XML oficial

  LECTURA: la verdad derivada NO es perfecta. Su error está medido y acotado, y
  todos los resultados del banco heredan esa barra.
```

**Esa última línea es el activo.** Convierte la mayor debilidad del proyecto en un
resultado publicado, y contesta la pregunta incómoda antes de que nadie la haga.

### La calibración cruzada pasa a ser de tres puntos

Con esto hay tres verdades sobre el mismo subconjunto: **humana, derivada y por
consenso**. Eso permite publicar dos barras de error, no una:

- `DERIVED` frente a humana: cuánto se equivoca el XML.
- `CONSENSUS` frente a humana: cuánto se equivoca el consenso de extractores, que es
  **la barra que hereda cualquier entidad sin XML**, o sea casi todas.

Nadie ha publicado la segunda para documentos en español, y sale de una anotación de
120 documentos que hay que hacer de todos modos.

---

## 3 quater. Deriva de herramienta: el eje que faltaba

El diseño anterior vigilaba que cambiaran **los documentos**. Falta el otro eje, que es
más frecuente y más accionable: **también cambian los extractores**. Docling saca una
versión, Azure actualiza su modelo, marker cambia su heurística de tablas. Nadie se
entera hasta que un usuario reporta una respuesta rara.

```bash
docbench toolwatch --extractors docling,marker,vlm-api --corpus frozen-2026-Q4
```

Al detectar una versión nueva, ejecuta sobre el **corpus congelado** y compara
**pareado** con la versión anterior, con intervalos y **desglosado por estrato**:

```
Docling 3.7 → 3.8   ·   corpus frozen-2026-Q4   ·   460 documentos

  TEDS global                          +1,8  [+0,9 - +2,6]     mejora
  por ESTRATO DE CORPUS (§3 bis):
  ├ nacido digital                     +2,4  [+1,5 - +3,2]     mejora
  ├ escaneado                          +1,1  [-0,2 - +2,3]     sin efecto detectable
  ├ empresarial sintético              +0,6  [-1,0 - +2,2]     sin efecto detectable
  └ adversarial                        -0,4  [-2,1 - +1,3]     sin efecto detectable
  por ESTRATO DE DIFICULTAD (§9.4):
  └ tablas multipágina                 -7,3  [-9,1 - -5,4]     REGRESIÓN

  latencia  -14%      coste  sin cambios      tasa de fallo  0,4% → 0,4%

  DECISIÓN: NO MIGRAR para documentos presupuestarios ni convenios, que en este corpus
  son el 31% del volumen (1.803 de 5.745, ver el manifiesto) y están dominados por
  tablas multipágina. MIGRAR para el resto.
```

**Ese informe es el que justifica que alguien pague todos los meses.** Y el aviso que lo
hace honesto: **una mejora global puede esconder una regresión en un estrato**. Un
`+1,8 global` sin el `-7,3 de multipágina` habría llevado a migrar y a romper el caso de
uso que más importa. Por eso el desglose no es opcional: es la razón de ser del informe.

---

## 3 quinquies. El router produce una política ejecutable, no una recomendación

La diferencia entre publicar y ser infraestructura. `docbench route` deja de emitir una
tabla y emite un fichero que se despliega:

```yaml
# routing.yaml · generado por docbench route, campaña 2026-Q4
version: 1
generated_from: runs/2026-Q4/
substance_hash: 7f2a91c4bb08
generated_at: 2026-11-14

rules:
  - when: { kind: factura, scanned: true }
    extractor: vlm-api
    confidence_min: 0.92
    fallback: marker
    measured: { accuracy: 0.91, cost_eur: 0.012, n: 84, ci: [0.86, 0.95] }

  - when: { kind: convenio, born_digital: true, has_merged_cells: true }
    extractor: docling
    measured: { accuracy: 0.88, cost_eur: 0.000, n: 120, ci: [0.83, 0.92] }

  - when: { kind: "*", has_image_annex: true }
    extractor: vlm-api
    measured: { accuracy: 0.91, cost_eur: 0.012, n: 60, ci: [0.84, 0.96] }

  - when: { privacy: sensitive }
    extractor: marker
    execution: on_prem
    measured: { accuracy: 0.79, cost_eur: 0.000, n: 45, ci: [0.71, 0.86] }
    note: "peor exactitud, pero es la única opción cuando los datos no salen"

default:
  extractor: pymupdf4llm
  measured: { accuracy: 0.84, cost_eur: 0.000, n: 460, ci: [0.81, 0.87] }

summary:
  # accuracy enrutada = media ponderada por n de las cuatro reglas y el default:
  # (0.91*84 + 0.88*120 + 0.91*60 + 0.79*45 + 0.84*460) / 769 = 0.856
  routed:      { cost_eur_per_doc: 0.0021, accuracy: 0.856, n: 769 }
  best_single: { cost_eur_per_doc: 0.0120, accuracy: 0.93, extractor: vlm-api }
  verdict: "enrutar cuesta 5,7 veces menos y pierde 7,4 puntos"
```

**Cada regla lleva su medición y su intervalo dentro.** Eso es lo que impide que la
política se convierta en una heurística que alguien tocó a mano: si una regla no tiene
`measured`, `docbench route --validate` la rechaza.

---

## 3 sexies. Leaderboard reproducible y badge

Cada fila del leaderboard fija todo lo que hace falta para reproducirla:

| Campo | Ejemplo |
|---|---|
| Extractor y versión exacta | `docling 3.8.2` |
| Imagen OCI y digest | `ghcr.io/…@sha256:4a71…` |
| Hardware y aceleración | `x86_64, 8 vCPU, sin GPU` |
| Modelo OCR o VLM y snapshot | `—` o `gpt-x@2026-08-15` |
| Coste por documento | `0,000 €` |
| Latencia en frío y en caliente | `4,1 s / 1,3 s` |
| Tasa de fallo | `0,4%` |
| Cobertura evaluable | `0,71` |
| Licencia | `MIT` |
| Fecha y comando | `2026-11-14` · `docbench replay runs/2026-Q4/` |

Y el badge, que es el motor de distribución:

```
Docbench Verified · BOE Tables · TEDS 0,914 ± 0,008 · reproducido 2026-11-14
```

**La latencia en frío y en caliente por separado** es un detalle que casi ningún
benchmark publica y que cambia decisiones: un extractor que tarda cuatro segundos en el
primer documento y uno en los siguientes es perfectamente usable en lote e inservible
en interactivo.

---

## 4. Decisiones de arquitectura

Una por fichero en `docs/adr/`. Aquí el resumen con su alternativa descartada y su consecuencia.

### ADR-0001 · La entidad es un adaptador, el motor es común

**Decisión.** Todo lo que varía entre organizaciones vive detrás de `EntityAdapter`. El motor no sabe qué es el BOE.

**Alternativa descartada.** Un benchmark del BOE, más pequeño y más rápido de terminar.

**Trade-off.** Más superficie de diseño y una interfaz que hay que acertar. A cambio, el proyecto sirve para una diputación, para una aseguradora y para una empresa privada sin tocar el motor.

**Cómo se verifica que es cierto:** con la segunda entidad implementada, que es requisito de terminado (§18). Un `Protocol` bonito y un solo adaptador no prueban nada.

### ADR-0002 · Cuatro modos de verdad de referencia, declarados por adaptador

| Modo | Cómo se obtiene | Coste | Sesgo declarado |
|---|---|---|---|
| `DERIVED` | De una versión estructurada oficial del mismo documento. El XML del BOE | Cero | Es transcripción, no lectura del PDF: puede diferir en maquetación. Y solo existe donde el publicador se molestó |
| `ANNOTATED` | Anotación humana con protocolo, doble pasada ciega separada por 7 días o más | Alto en tiempo | Un solo anotador. El acuerdo intra no sustituye al inter, y se dice |
| `CONSENSUS` | Consenso de N extractores heterogéneos; solo se revisa a mano donde discrepan | Medio-bajo | **Hereda los errores comunes a todos.** Si los N leen mal la misma celda combinada, el consenso la da por buena |
| `NONE` | No hay | Cero | Solo permite medir consistencia, nunca exactitud. El motor se **niega** a emitir métricas de exactitud en este modo |

**La calibración cruzada, que es un resultado propio:** correr `CONSENSUS` sobre el corpus del BOE, donde también existe `DERIVED`, y publicar **cuánto se equivoca el consenso cuando hay verdad de verdad**. Ese número pone barra de error a todos los resultados por consenso en otras entidades. No lo tiene nadie y sale casi gratis.

### ADR-0003 · La licencia y la privacidad son código, no documentación

**Decisión.** `EntityAdapter.license()` y `.privacy()` devuelven declaraciones estructuradas, y el motor las hace cumplir en tiempo de ejecución.

**Las cuatro reglas que aplica el motor:**

1. `special_categories = True` → el adaptador **no se registra**.
2. `redaction_required` → la redacción corre **antes** de cualquier salida de red, y se registra la tasa por documento.
3. `may_send_to_third_party = False` → el motor **rechaza** cualquier extractor o modelo de respuesta que no sea local. La campaña no arranca.
   **Ojo: este campo mezcla dos preguntas** —si la *fuente* permite retransmitir, y si el *operador* tiene base legal para ese tratamiento— y sólo la primera la contesta la licencia. Sin respuesta a la segunda, el valor por defecto es el restrictivo: ver ADR-0037 y el límite 61.
4. `may_redistribute_content = False` → `publish` se niega a empaquetar contenido y publica en su lugar el manifiesto de hashes y el script de descarga.

**Trade-off.** Fricción al añadir adaptadores. A cambio, es utilizable por una entidad sin que su departamento jurídico tenga que auditar nada, que es la barrera real que hunde a la mayoría de proyectos de este tipo.

### ADR-0004 · Tres niveles de métrica, y el que importa es el segundo

**Decisión.** Se miden estructura, respuesta final y vocabulario. El titular del informe es la respuesta final.

**Alternativa descartada.** Medir solo fidelidad de tabla, que es lo que hace todo el mundo y es mucho más fácil.

**Trade-off.** Requiere construir un conjunto de preguntas con verificador, que es la mitad del trabajo. A cambio se contesta la única pregunta que le importa a quien paga: **cuántas respuestas pierdo al mes si elijo el barato**. Nadie publica esa cadena entera.

### ADR-0005 · Existe un extractor `oracle` y la capa 2 se reporta contra él

**El problema que resuelve.** El pipeline es `extractor → trocear → recuperar → responder`. Publicar solo la exactitud final mezcla el error del extractor con el del troceador, el del recuperador y el del modelo. El titular no tendría techo de referencia.

**Decisión.** El extractor `oracle` devuelve la verdad de referencia y corre por el mismo pipeline. Su exactitud es el techo alcanzable con extracción perfecta.

```
exactitud_absoluta(e) = aciertos(e) / preguntas
exactitud_relativa(e) = aciertos(e) / aciertos(oracle)
```

**Tres consecuencias, y las tres son buenas:**
1. El titular pasa a ser defendible: *"con extracción perfecta el sistema acierta el 91%; con el mejor extractor real, el 84%; con el más barato, el 68%. El hueco atribuible a la extracción es de 7 puntos frente al mejor extractor real, y de 23 frente al más barato. La plantilla de L10 publica el primero; el segundo va al lado, porque es el que decide un presupuesto."*
2. Si `oracle` saca exactitud baja, el problema está en el pipeline o en las preguntas, y **conviene enterarse antes de publicar**. Es el test de cordura del banco entero.
3. Solo existe donde hay `DERIVED`, o sea en el BOE, lo que refuerza su papel de banco de calibración.

### ADR-0006 · Forma canónica de tabla obligatoria, y `NO_APLICABLE` en vez de cero

**El problema.** TEDS está definido sobre un árbol HTML. Pero PyMuPDF4LLM y marker devuelven Markdown, Camelot devuelve DataFrames, Tesseract y PaddleOCR devuelven texto plano y GROBID devuelve TEI. **Convertir Markdown a HTML pierde `rowspan` y `colspan` por completo**, así que calcular TEDS sobre esa conversión penalizaría a esas familias justo en el estrato de celdas combinadas, que es el que se sobremuestrea y el que se declara titular. Sería una comparación amañada sin querer, que es la peor clase.

**Decisión.** Existe `CanonicalTable` y todos se mapean a ella. Y la regla que lo hace honesto: **si `expresses_spans` es `False`, ese extractor sale `NO_APLICABLE` en las tablas de ese estrato, no cero.** Se publica su cobertura evaluable junto a su nota.

**GriTS se retira** salvo para extractores que emitan geometría de celda, que son minoría. Y **TEDS se valida contra la implementación de referencia de PubTabNet** sobre sus propios casos, no "a ojo": TEDS no tiene valores intuibles.

### ADR-0007 · El coste va en todas las tablas, siempre

Ninguna métrica se publica sin su coste por documento y su latencia al lado. Hace imposible la comparación deshonesta, que es comparar un VLM frontier contra un parser local sin decir que uno cuesta doscientas veces más.

### ADR-0008 · El glosario es del adaptador, no del motor

**Alternativa descartada.** Un glosario global de términos administrativos españoles.

**Trade-off.** Cada entidad necesita que alguien escriba el suyo, que es trabajo de dominio. A cambio, es lo único que hace que la tercera capa signifique algo: el par confuso de una diputación no es el de una aseguradora, y un glosario global sería tan genérico que no atraparía nada.

### ADR-0009 · Muestreo estratificado declarado y congelado antes de medir

El plan, con sus estratos y sus tamaños, se publica **antes** de correr nada. Evita el fallo que hunde a estos benchmarks: que el 80% del corpus sean tablas triviales y el resultado diga que todos los extractores son buenos.

**Y el cálculo de tamaño de muestra es pareado (McNemar), no independiente**, porque todos los extractores procesan los mismos documentos. Con discordancia supuesta del 20% y diferencia a detectar de 0,05 salen unos **625 documentos**; el diseño no pareado, que sería el equivocado, exigiría del orden de 1.565 por brazo. La discordancia supuesta se declara antes y se comprueba después.

### ADR-0010 · El extractor del cliente entra como concursante, sin trato especial

Casi toda empresa con dos años de documentos tiene ya un pipeline propio. Su pregunta no es cuál es el mejor extractor del mundo, es **si el suyo es bueno o le están vendiendo humo**. Entra por entry point, pasa la suite de conformidad, y aparece en la tabla al lado de los de referencia. Incluida la marca `NO_APLICABLE` si su formato no expresa celdas combinadas. **Nada de trato especial por ser de quien paga.**

### ADR-0011 · `drift` no puede importar `truth`

La detección de deriva tiene que funcionar **sin verdad de referencia nueva**, o no es ejecutable en producción. El contrato de capas lo prohíbe por CI, así que la afirmación no se puede erosionar con el tiempo.

### ADR-0012 · `route` solo lee de `report`

La recomendación de enrutado se deriva de mediciones publicadas, nunca de una heurística escondida. Si alguien quiere discutir la recomendación, discute con los números que están al lado.

---

## 5. La dependencia `benchcore`

`benchcore` es una librería, no un proyecto del portfolio. Aporta el **contrato**, no las implementaciones.

### 5.1 Qué aporta

| Pieza | Qué es |
|---|---|
| `contracts` | Los cuatro `Protocol`: `DataSource`, `ComputeProvider`, `ExecutionBackend`, `OutputSink`, con sus `capabilities` |
| `registry` | Descubrimiento de plugins por entry points, con versión de API y rechazo de incompatibles |
| `conform` | La suite de conformidad que valida cualquier plugin, propio o de un cliente |
| `core.policy` | Egress restringido, redacción de PII, `fail_closed`, cruce entre lo que una fuente permite y lo que un proveedor hace |
| `runner` | Presupuesto duro con aborto, reanudación, caché por clave semántica, aleatorización por bloques |
| `core.bootstrap`, `core.power` | Bootstrap agrupado con BCa y caída a percentil, tamaño de muestra pareado y no pareado |
| `builtin` | `fs`, `openai-compatible`, `ollama`, `recorded`, y salidas `json`, `markdown`, `junit` |

### 5.2 Qué implementa este repo encima

Todo lo específico de plataforma entra **por el mismo contrato y la misma suite de conformidad que usaría un cliente**. Eso no es una concesión: es lo que hace creíble la promesa de extensibilidad.

| Adaptador | Eje | Para qué |
|---|---|---|
| `sharepoint`, `onedrive` | datos | Donde de verdad están los documentos en una empresa española |
| `azure-blob`, `s3`, `gcs`, `minio` | datos | Almacenamiento de objetos, con endpoint privado configurable |
| `alfresco`, `documentum` | datos | Gestores documentales de banca y seguros |
| `sftp`, `sql`, `http-api` | datos | Lo que sigue habiendo en media administración |
| `azure-openai`, `vertex`, `bedrock` | cómputo | Los VLM por API. Azure primero: supera el 80% de penetración en la empresa española |
| `vllm` | cómputo | VLM local para modo aislado |
| `docker`, `kubernetes` | ejecución | Cuando el cliente quiere que corra en su clúster |
| `onepager-pdf`, `xlsx`, `csv`, `teams`, `azure-devops` | salida | Lo que llega al comité y a su CI |

### 5.3 Los perfiles de entorno

Viven en `profiles/` de este repo, no en `benchcore`.

| Perfil | Datos | Cómputo | Ejecución | Salida |
|---|---|---|---|---|
| `laptop` | `fs` | `ollama` + `recorded` | `inproc` | `markdown` |
| **`airgap`** | `fs`, `sftp` | `vllm`, `ollama` | `docker` | `html`, `onepager-pdf` |
| `azure` | `sharepoint`, `azure-blob` | `azure-openai` | `kubernetes` | `azure-devops`, `teams`, `onepager-pdf` |
| `aws` | `s3` | `bedrock` | `docker` | `github-summary` |
| `gcp` | `gcs` | `vertex` | `kubernetes` | `github-summary` |
| `onprem` | `minio`, `sql` | `openai-compatible` (pasarela), `vllm` | `kubernetes` | `gitlab-report`, `onepager-pdf` |

---

## 6. Modelo de datos completo

Todo en **`src/docbench_es/types/`**, que **no importa nada del proyecto**. Todo congelado (`frozen=True`) salvo donde se diga.

> **Corregido respecto a la redacción original**, que decía `types.py`, un fichero. Las ~30 estructuras de esta sección salen unas 340 líneas con sus docstrings, y `CLAUDE.md` prohíbe pasar de 300: las dos reglas no se podían cumplir a la vez. `docbench_es.types` **sigue siendo la única superficie de import** —los submódulos son privados y un test lo hace cumplir—, así que nada de lo que dice esta sección cambia para quien la use. Ver [ADR-0013](docs/adr/0013-types-como-paquete.md).

> **Los campos de mapa se anotan `Mapping[K, V]`, no `dict[K, V]`.** `frozen=True` congela el *binding*, no el diccionario: con `dict` el modelo de datos era mutable por dentro y un test afirmaba que no. Cada dataclass con mapas llama a `congelar_mapas` en su `__post_init__`. Los `dict[...]` que aparecen abajo se leen como `Mapping[...]`. Ver [ADR-0014](docs/adr/0014-mapas-inmutables-en-el-modelo-de-datos.md).

### 6.1 Referencias y documentos

```python
@dataclass(frozen=True)
class DocRef:
    entity: str                  # id de la entidad
    external_id: str             # identificador en el sistema de origen
    published_on: date | None
    url: str | None
    kind: str                    # "convenio", "expediente", "cuentas", ...
    def key(self) -> str: ...    # entity + "/" + external_id, estable

@dataclass(frozen=True)
class RawDoc:
    ref: DocRef
    primary: bytes               # el documento tal cual, normalmente PDF
    primary_mime: str
    companions: dict[str, bytes] # {"xml": ..., "html": ...} si existen
    sha256: str                  # del primary
    fetched_at: datetime
    n_pages: int | None
```

### 6.2 La forma canónica de tabla

```python
@dataclass(frozen=True)
class CanonicalCell:
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    text: str = ""
    is_header: bool = False

@dataclass(frozen=True)
class CanonicalTable:
    cells: tuple[CanonicalCell, ...]
    n_rows: int
    n_cols: int
    page_span: tuple[int, int]        # primera y última página
    caption: str | None
    expresses_spans: bool             # False si el formato nativo no puede
    source_format: str                # "html", "markdown", "dataframe", "tei", "text"

    def cell_at(self, row: int, col: int) -> CanonicalCell | None: ...
    def is_wellformed(self) -> tuple[bool, list[str]]: ...
        # solapes, huecos, spans que salen del rango. Devuelve los problemas
```

**Invariantes que un test comprueba:** ninguna celda solapa con otra; la unión de celdas con sus spans cubre exactamente `n_rows × n_cols` o declara los huecos; ningún span sale del rango.

> **Transcrito de [ADR-0018](docs/adr/0018-hueco-de-cola-y-hueco-interior.md) y [ADR-0019](docs/adr/0019-los-invariantes-se-detectan-no-se-impiden.md), en L1.** El «o declara los huecos» de arriba **no era traducible tal como estaba escrito**: «declarar» no tenía referente, porque `CanonicalTable` no tiene campo de huecos ni §9.1 nombraba función que los enumerase. Se resuelve así:
>
> - **Hueco de cola** —ninguna celda ORIGINA en esa fila a la derecha del hueco— es **legítimo**: es la `<tr>` con menos `<td>`, HTML legal y cotidiana en el BOE. Se reporta como hallazgo informativo y `holes()` lo enumera.
> - **Hueco interior** —hay una celda originada en esa misma fila a su derecha— es **fatal**: ningún formato de origen puede producirlo, porque los cinco rellenan de izquierda a derecha.
> - Por la misma regla, **`COLUMNA_VACIA` es fatal** y **`FILA_VACIA` es informativo**: `<tr></tr>` es HTML legal, una columna entera sin cubrir no la produce ningún formato.
> - Los huecos se **derivan** con `core.canonical.holes()`, no se almacenan: un campo podría desacordar con `cells` y dejar dos fuentes de verdad.
> - Un hueco **no es una celda vacía**. Son árboles distintos y TEDS los puntúa distinto (L2).
>
> Y sobre `span < 1`: **se detecta, no se impide**. `is_wellformed()` lo reporta como `SPAN_MENOR_QUE_UNO` y la celda sigue siendo invisible para `cell_at`. Ningún `__post_init__` lo rechaza, porque si no se puede construir una tabla rota no se puede demostrar que se detecta, y ése es el criterio de aceptación de L1.
>
> **Dónde vive el algoritmo.** En `types/_invariantes.py`, junto a los datos que inspecciona, y `core.canonical.validate()` delega en el método público `is_wellformed()`. No es una preferencia: el contrato de capas pone `core` por encima de `types`, así que `types` no puede importar `core` ni con un import diferido —`lint-imports` lee el AST—. La alternativa era escribir la comprobación dos veces.

### 6.3 Extracción

```python
@dataclass(frozen=True)
class Extraction:
    extractor_id: str
    extractor_version: str
    doc_ref: DocRef
    text: str                        # texto plano, para recuperación
    tables: tuple[CanonicalTable, ...]
    native_format: str
    pages_processed: int
    cost: Cost                       # de benchcore.types
    latency_ms: int
    warnings: tuple[str, ...]
    failed: bool = False
    failure_reason: str | None = None   # de un enum cerrado, ver §6.9
```

### 6.4 Verdad de referencia

```python
TruthMode = Literal["DERIVED", "ANNOTATED", "CONSENSUS", "NONE"]

@dataclass(frozen=True)
class Fact:
    id: str
    doc_ref: DocRef
    path: str                # "tabla[2].fila[grupo 3].col[salario base].2026"
    value: str | float | date
    unit: str | None
    provenance: str          # de dónde salió exactamente

@dataclass(frozen=True)
class Truth:
    mode: TruthMode
    doc_ref: DocRef
    tables: tuple[CanonicalTable, ...]
    facts: tuple[Fact, ...]
    confidence: float | None      # solo en CONSENSUS y ANNOTATED
    n_annotators: int | None      # solo en ANNOTATED
    discordance_rate: float | None  # solo en CONSENSUS
    built_at: datetime
```

### 6.5 Preguntas y respuestas

```python
Verifier = Literal["exact", "numeric", "set", "date", "boolean", "span"]

@dataclass(frozen=True)
class Question:
    id: str
    entity: str
    doc_ref: DocRef
    text: str
    answer: str | float | date | frozenset[str] | bool
    verifier: Verifier
    tolerance: float | None          # obligatorio si verifier == "numeric"
    origin: Literal["template", "handwritten"]
    template_id: str | None
    trap: str | None                 # id del ConfusablePair, si es trampa
    difficulty: frozenset[str]       # estratos implicados
    requires_table: bool

@dataclass(frozen=True)
class AnswerResult:
    question_id: str
    extractor_id: str
    given: str
    correct: bool
    confidently_wrong: bool   # respondió mal sin señalar duda
    confused_with: str | None # id del par confundible, si aplica
    cost: Cost
    latency_ms: int
```

### 6.6 Glosario y capa semántica

```python
@dataclass(frozen=True)
class Term:
    key: str
    definition: str              # definición operativa, no de diccionario
    aliases: tuple[str, ...]
    not_to_confuse_with: tuple[str, ...]
    discriminator: str           # qué evidencia del documento lo distingue
    appears_in: tuple[str, ...]  # tipos de documento
    verified_on: date
    verified_by: Literal["human", "imported"]

@dataclass(frozen=True)
class ConfusablePair:
    id: str
    term_a: str
    term_b: str
    why_confused: str
    discriminator: str
    example_doc: DocRef | None
    trap_questions: tuple[str, ...]

@dataclass(frozen=True)
class Glossary:
    entity: str
    version: int
    updated: date
    terms: tuple[Term, ...]
    confusables: tuple[ConfusablePair, ...]
    def to_prompt_block(self) -> str: ...   # cómo se inyecta en el sistema de respuesta
```

### 6.7 Declaraciones de licencia y privacidad

```python
@dataclass(frozen=True)
class LicenseDecl:                 # de benchcore.types
    name: str
    may_redistribute_content: bool
    may_redistribute_derived: bool
    attribution: str | None
    source_url: str
    verified_on: date
    notes: str

@dataclass(frozen=True)
class PrivacyDecl:                 # de benchcore.types
    contains_personal_data: bool
    categories: frozenset[str]
    special_categories: bool       # art. 9 RGPD. True → no se registra
    lawful_basis: str | None
    redaction_required: bool
    redaction_profile: str | None
    may_send_to_third_party: bool  # False → prohibido todo lo que no sea local
    dpa_reference: str | None
```

### 6.8 Plan y campaña

```python
@dataclass(frozen=True)
class Stratum:
    name: str
    target: int
    found: int
    weight: float          # peso en la distribución real, para ponderar

@dataclass(frozen=True)
class SamplingPlan:
    version: int
    entity: str
    campaign: str
    strata: tuple[Stratum, ...]
    seed: int
    design: Literal["mcnemar_paired", "independent"]
    effect_to_detect: float
    assumed_discordance: float
    alpha: float
    target_power: float
    n_documents_required: int
    frozen_at: datetime
    doc_refs: tuple[DocRef, ...]     # los documentos concretos, ya sorteados

@dataclass(frozen=True)
class CampaignResult:
    campaign: str
    entity: str
    plan_hash: str
    extractors: tuple[str, ...]
    level1: dict[str, StructureMetrics]
    level2: dict[str, AnswerMetrics] | None
    level3: dict[str, GlossaryMetrics] | None
    costs: dict[str, Cost]
    started_at: datetime
    finished_at: datetime
    substance_hash: str


# ── Los agregados por nivel, y los tres objetos de salida ────────────────
# Se usan arriba y en §9. Van aquí para que §6 sea de verdad completo.

@dataclass(frozen=True)
class StructureMetrics:            # nivel 1, por extractor
    teds: float | None             # None = NO_APLICABLE, nunca 0
    teds_s: float | None
    cell_f1: float | None          # None = NO_APLICABLE, igual que teds
    evaluable_coverage: float      # sobre cuántas tablas se pudo calcular
    failures: Mapping[ExtractionFailure, int]   # enum cerrado como CLAVE, no str
    ci: tuple[float, float]
    n_documents: int

@dataclass(frozen=True)
class AnswerMetrics:               # nivel 2, por extractor
    accuracy: float
    accuracy_vs_oracle: float | None   # None donde no hay oracle
    by_verifier: dict[str, float]
    ci: tuple[float, float]
    n_questions: int
    n_documents: int               # la unidad de remuestreo

@dataclass(frozen=True)
class GlossaryMetrics:             # nivel 3, por extractor
    accuracy_with: float
    accuracy_without: float
    delta: float
    ci_delta: tuple[float, float]
    confusion_rate: dict[str, float]   # por par confundible

@dataclass(frozen=True)
class TedsReport:                  # salida de core.teds.teds_batch
    per_document: dict[str, float | None]
    aggregate: float | None
    evaluable_coverage: float
    not_applicable: tuple[str, ...]

@dataclass(frozen=True)
class GlossaryContribution:        # salida de glossary.contribution
    delta: float
    ci: tuple[float, float]
    n_documents: int
    by_stratum: dict[str, float]

@dataclass(frozen=True)
class RoutingPlan:                 # salida de route.recommend; se serializa a routing.yaml
    rules: tuple[RoutingRule, ...]
    default: RoutingRule
    summary: dict[str, float]
    generated_from: str
    substance_hash: str

@dataclass(frozen=True)
class RoutingRule:
    when: dict[str, object]
    extractor: str
    measured: dict[str, object]    # accuracy, cost_eur, n, ci. Obligatorio: sin él, `route --validate` rechaza la regla
    fallback: str | None = None
    execution: str | None = None
    note: str | None = None
```

`ProbeResult` viene de `benchcore.types`, igual que `Cost`, `LicenseDecl` y `PrivacyDecl`.

### 6.9 Errores, todos de enum cerrado

```python
class DocbenchError(Exception): ...

class AdapterError(DocbenchError): ...        # el adaptador falló
class PolicyViolation(DocbenchError): ...     # licencia o privacidad
class TruthUnavailable(DocbenchError): ...    # se pidió exactitud en modo NONE
class BudgetExceeded(DocbenchError): ...
class ContractViolation(DocbenchError): ...   # un plugin no cumple

ExtractionFailure = Literal[
    "timeout", "out_of_memory", "unsupported_format", "corrupt_pdf",
    "encrypted_pdf", "no_text_layer", "provider_error", "policy_blocked",
]
```

**`no_text_layer` usa el mismo umbral que el estrato `escaneado`** (§9.4): caracteres no blancos por página por debajo de `umbral_capa_texto`. Una sola definición para las dos cosas, porque son el mismo hecho medido: si no hay capa de texto, el documento va al estrato `escaneado` **y** un parser de texto falla con esa causa.

**Regla:** ningún error se traga. Un documento que falla se registra con su causa del enum y **se cuenta en el informe**. La tasa de fallo por extractor es un resultado, no un detalle de implementación.

---

## 7. Las interfaces

### 7.1 `EntityAdapter` — siete métodos

```python
class EntityAdapter(Protocol):
    id: str                     # "boe", "dip-cadiz", "acme-sa"
    display_name: str
    language: str               # "es", "es-ca", "es-gl", "es-eu"
    truth_mode: TruthMode
    benchcore_api: str          # "1.x". El registro rechaza incompatibles

    def discover(self, since: date, until: date, **filters) -> Iterable[DocRef]:
        """Qué documentos hay. NO descarga. Debe ser perezoso y paginable."""

    def fetch(self, ref: DocRef) -> RawDoc:
        """Baja el documento. Idempotente. Con caché por hash de contenido."""

    def truth(self, ref: DocRef) -> Truth | None:
        """La verdad de referencia si su modo la produce automáticamente.
        None en CONSENSUS, ANNOTATED y NONE."""

    def license(self) -> LicenseDecl: ...
    def privacy(self) -> PrivacyDecl: ...
    def glossary(self) -> Glossary: ...

    def strata(self, ref: DocRef, doc: RawDoc) -> frozenset[str]:
        """Etiquetas de dificultad. Se calculan sobre el documento ya bajado."""
```

**Contrato que verifica la suite de conformidad (§14):**
- `discover` no descarga: se mide el tráfico y debe ser el mínimo.
- `fetch` es idempotente: dos llamadas devuelven el mismo `sha256`.
- `truth` devuelve `None` si y solo si `truth_mode != "DERIVED"`.
- `license` y `privacy` son estables entre llamadas.
- `strata` es determinista para el mismo documento.
- Todos los errores son de los tipos declarados en §6.9.

**Quién lo registra, y por qué no `benchcore`.** `EntityAdapter` es un `Protocol`
nativo de `docbench`: `benchcore.contracts.Plugin` exige `capabilities()` y
`probe()`, y su `Capabilities.axis` es un literal cerrado sin `entidad` — pero la
razón de fondo es que **un eje de entidad tendría exactamente un consumidor, y
siempre**, y un contrato compartido con un solo consumidor está mal colocado
(ADR-0035). `sources/` sí son `DataSource`, que es un eje con dos consumidores
posibles.

Así que el descubrimiento es de este repo (ADR-0036): grupo de entry points propio
**`docbench.entity`**, la mecánica de `benchcore.registry` reusada tal cual —el
eje no se comparte, el apretón de manos de `benchcore_api` sí—, y **fallo cerrado
en carga**. Dos consecuencias que son contrato:

- **Descubrir no construye:** el registro devuelve la clase, no una instancia, así
  que `benchcore_api` tiene que ser **atributo de clase**. Un adaptador que lo
  asigne en `__init__` **no llega a cargarse**: el registro no ve versión y lo
  rechaza por «no declara `benchcore_api`».
- *«El registro rechaza»* un adaptador con `special_categories: true` (§14 y §19)
  **se implementa en L8**, en el punto donde el adaptador se construye con su
  perfil: que es donde existe la `PrivacyDecl`, porque vive en el perfil y no en
  la clase.

### 7.2 `Extractor`

```python
class Extractor(Protocol):
    id: str
    version: str
    kind: Literal["parser", "ocr", "vlm", "hibrido"]
    runs_locally: bool
    expresses_spans: bool        # si su formato nativo puede con rowspan/colspan
    benchcore_api: str

    def extract(self, doc: RawDoc, page_range: tuple[int,int] | None = None) -> Extraction: ...
    def cost_of(self, ex: Extraction) -> Cost: ...
    def probe(self) -> ProbeResult:
        """¿Está instalado? ¿Alcanzable? ¿Qué versión? Sin procesar nada."""
```

**Contrato:** `extract` nunca lanza salvo los errores del enum; si falla, devuelve `Extraction(failed=True, failure_reason=...)`. Las tablas devueltas cumplen los invariantes de `CanonicalTable`. `cost_of` es puro.

### 7.3 `AnswerEngine` — el pipeline de referencia

```python
class AnswerEngine(Protocol):
    id: str
    version: str
    def answer(self, question: Question, ex: Extraction,
               glossary: Glossary | None) -> AnswerResult: ...
```

Una sola implementación de serie, `reference`, **fija a propósito**: troceado por tabla y por sección, recuperación densa con un modelo declarado, prompt versionado, temperatura 0. Todo clavado y con hash. `glossary=None` es el brazo de control que mide cuánto aporta la capa semántica.

---

## 8. El árbol de ficheros, fichero a fichero

```
docbench-es/
├── README.md                  el número en la primera línea, quickstart, orden de lectura
├── RESULTS.md                 números medidos, fecha, versión y comando exacto
├── LIMITS.md                  qué NO mide y dónde se rompe
├── CHANGELOG.md
├── LICENSE                    Apache-2.0
├── Makefile                   fast · full · quickstart · test · lint · types · arch · bench · report
├── .python-version            3.12, para que CI y local analicen lo mismo
├── .importlinter              el contrato de capas. NO se puede llamar importlinter.ini
├── pyproject.toml             un solo paquete, entry points declarados
├── .pre-commit-config.yaml
├── .gitignore                 data/ y runs/ fuera
│
├── .github/workflows/
│   ├── fast.yml               lint + tipos + arquitectura + núcleo. Sin red. < 90 s
│   ├── full.yml               integración + contrato de adaptadores + Docker
│   └── nightly.yml            campaña completa, publica artefacto
│
├── docs/
│   ├── reading-order.md       5 min / 30 min / 2 h, con ficheros concretos
│   ├── metrics.md             cada métrica: fórmula, supuestos, caso degenerado
│   ├── entity-guide.md        cómo escribir un adaptador de entidad, con ejemplo entero
│   ├── extractor-guide.md     cómo conectar tu propio extractor
│   ├── glossary-guide.md      cómo construir la capa semántica de una entidad
│   ├── deployment.md          los seis perfiles y qué se pierde en cada uno
│   └── adr/
│       ├── 0001-entidad-es-adaptador.md
│       ├── 0002-cuatro-modos-verdad.md
│       ├── 0003-licencia-y-privacidad-son-codigo.md
│       ├── 0004-tres-niveles-de-metrica.md
│       ├── 0005-extractor-oracle.md
│       ├── 0006-forma-canonica-y-no-aplicable.md
│       ├── 0007-coste-siempre.md
│       ├── 0008-glosario-del-adaptador.md
│       ├── 0009-muestreo-pareado-mcnemar.md
│       ├── 0010-extractor-del-cliente.md
│       ├── 0011-drift-sin-verdad.md
│       └── 0012-route-solo-lee-report.md
│
├── profiles/
│   ├── laptop.yaml · airgap.yaml · azure.yaml · aws.yaml · gcp.yaml · onprem.yaml
│
├── src/docbench_es/
│   ├── __init__.py
│   ├── types/                 TODO el modelo de datos. No importa nada del proyecto
│   │                          (paquete, no fichero: ADR-0013. `types` es la unica
│   │                           superficie de import; los submodulos son privados)
│   ├── errors.py              la jerarquía de §6.9
│   │
│   ├── core/                  PURO: sin red, sin disco, sin proveedor, sin reloj
│   │   ├── canonical/           invariantes y los cinco conversores desde
│   │   │                        html/markdown/dataframe/tei/texto. PAQUETE, no
│   │   │                        fichero, por el limite de 300 lineas (ADR-0013);
│   │   │                        `core.canonical` sigue siendo la unica superficie
│   │   │                        de import. Las dataclasses NO viven aqui: viven en
│   │   │                        `types/`, y no por preferencia (ver abajo)
│   │   ├── teds.py              TEDS y TEDS-S sobre la forma canónica
│   │   ├── cellmatch.py         emparejado de celdas, exactitud celda a celda
│   │   ├── answer.py            los seis verificadores de respuesta
│   │   ├── weighting.py         ponderación por estrato a la distribución real
│   │   ├── confusion.py         detección de confusión de vocabulario
│   │   └── driftsig.py          las tres señales de deriva, como funciones puras
│   │
│   ├── entity/
│   │   ├── base.py              el Protocol y el perfil declarativo
│   │   ├── registry.py          el registro: grupo propio y rechazo en carga
│   │   ├── conformance.py       la suite que todo adaptador debe pasar
│   │   ├── _comprobaciones.py   sus aros, uno por método de §7.1
│   │   ├── boe.py               el de referencia, modo DERIVED
│   │   ├── boe_xml.py           el parseo del XML del BOE a forma canónica
│   │   ├── diputacion.py        plantilla para diputación o ayuntamiento
│   │   ├── privada.py           plantilla para entidad privada, corpus local
│   │   └── generico_pdf.py      una carpeta de PDFs sin más
│   │
│   ├── sources/                 adaptadores de datos sobre benchcore.contracts
│   │   ├── sharepoint.py · onedrive.py · azure_blob.py · s3.py · gcs.py
│   │   ├── minio.py · sftp.py · sql.py · http_api.py
│   │   ├── alfresco.py · documentum.py
│   │
│   ├── corpus/
│   │   ├── harvest.py           descarga con caché y reintentos
│   │   ├── pairing.py           emparejado PDF/XML con comprobación de coherencia
│   │   ├── manifest.py          el manifiesto con hashes, licencias y estratos
│   │   └── store.py             el almacén local de la campaña
│   │
│   ├── truth/
│   │   ├── derived.py           del XML oficial
│   │   ├── annotated.py         anotación con protocolo y doble pasada
│   │   ├── consensus.py         consenso de N extractores + revisión de discrepancias
│   │   ├── calibrate.py         CONSENSUS contra DERIVED, la barra de error
│   │   └── annotator/           la interfaz local de anotación (HTML + servidor mínimo)
│   │
│   ├── extract/
│   │   ├── base.py              el Protocol, el registro y la conformidad
│   │   ├── oracle.py            el brazo de control
│   │   │   LOS OCHO DE L5, uno por fichero, cubriendo las cinco familias:
│   │   ├── pymupdf4llm.py · pdfplumber.py    parser de texto
│   │   ├── camelot.py                        extractor de tablas
│   │   ├── docling.py · marker.py · unstructured.py   document-AI
│   │   ├── grobid.py                         TEI / científico
│   │   ├── tesseract.py                      OCR
│   │   │   LLEGAN EN L12, con el nivel 2:
│   │   ├── vlm_api.py           genérico sobre benchcore.ComputeProvider
│   │   └── vlm_local.py         vLLM u Ollama
│   │   (paddleocr.py, surya.py y hybrid.py se aplazan a `v0.4.0`: ver §16)
│   │
│   ├── ask/
│   │   ├── templates.py         generación de preguntas desde la verdad
│   │   ├── traps.py             las preguntas trampa, escritas a mano
│   │   ├── verify.py            aplicación de los seis verificadores
│   │   └── engine.py            AnswerEngine "reference", fijo y versionado
│   │
│   ├── glossary/
│   │   ├── model.py             carga, validación y versionado
│   │   ├── export.py            el artefacto .semantic.yaml
│   │   └── contribution.py      la métrica de cuánto aporta cargarlo
│   │
│   ├── sample/
│   │   ├── plan.py              construcción y congelado del plan
│   │   └── power.py             McNemar pareado, sobre benchcore.core.power
│   │
│   ├── reference/
│   │   ├── pipeline.py          el pipeline de medición, exportable
│   │   └── export.py            docbench export-pipeline
│   │
│   ├── drift/
│   │   ├── baseline.py          la línea base de rasgos estructurales
│   │   ├── shape.py             deriva de forma
│   │   ├── agreement.py         deriva de acuerdo entre extractores
│   │   ├── vocabulary.py        deriva de vocabulario
│   │   └── alert.py             la alerta con muestra para revisar
│   │
│   ├── route/
│   │   └── recommend.py         enrutado por tipo de documento y presupuesto
│   │
│   ├── report/
│   │   ├── tables.py · cards.py · curves.py
│   │   └── sinks/               onepager_pdf.py · xlsx.py · csv.py · html.py
│   │                                teams.py · azure_devops.py · github_summary.py
│   │
│   ├── publish/
│   │   ├── package.py           empaquetado que respeta la licencia
│   │   └── hf.py                subida a Hugging Face de lo redistribuible
│   │
│   └── cli/
│       ├── main.py
│       ├── entity.py · corpus.py · truth.py · ask.py · run.py
│       ├── report.py · route.py · drift.py · publish.py · toolwatch.py
│       ├── plugins.py · glossary.py · export_pipeline.py
│       └── conform.py · doctor.py · init.py · replay.py
│
├── tests/
│   ├── unit/                    espejo de src/, sin red. Objetivo: < 20 s
│   ├── contract/
│   │   ├── test_entity_contract.py     contra los cuatro adaptadores propios
│   │   └── test_extractor_contract.py  contra los ocho extractores
│   ├── hostile/
│   │   ├── test_adapter_restrictivo.py     publish debe abortar
│   │   ├── test_adapter_categorias.py      no debe registrarse
│   │   └── test_adapter_sin_terceros.py    campaña no arranca con extractor API
│   ├── fixtures/
│   │   ├── tablas/              tablas a mano con verdad conocida
│   │   ├── pubtabnet/           casos de referencia para validar TEDS
│   │   └── quickstart/          20 documentos reales del BOE, ~4 MB, versionados
│   ├── degradation/             extracciones degradadas a propósito
│   ├── drift/                   lotes con plantilla artificialmente distinta
│   ├── security/                fuga de credenciales en artefactos, logs y cachés
│   └── e2e/                     con red, solo en full
│
├── entities/                    YAML de entidades del cliente, uno por fichero
├── glosarios/                   los .semantic.yaml exportados por `glossary export`
├── scripts/                     descarga y utilidades citadas en el manifiesto
├── data/                        .gitignore  ← corpus descargado
└── runs/                        .gitignore  ← campañas y artefactos
```

> **Por qué `CanonicalCell` y `CanonicalTable` viven en `types/` y no en `core/canonical`, aunque esta sección las dibujara ahí.** No es que §6 sea normativo y §8 descriptivo: es que **§8 no es implementable bajo el contrato que el propio CI hace cumplir**. `Extraction` (§6.3) y `Truth` (§6.4) llevan las dos un campo `tables: tuple[CanonicalTable, ...]` —`types/_documento.py:89` y `types/_verdad.py:46`—, y el contrato de capas pone `core` **por encima** de `types : errors`. Si `CanonicalTable` viviera en `core/canonical`, `types` tendría que importar `core`: `lint-imports` en rojo y CI en rojo. Escrito en L1 para que no haya que volver a decidirlo.

### El contrato de capas

El fichero se llama **`.importlinter`**, no `importlinter.ini`: import-linter solo busca
`setup.cfg`, `.importlinter` y `pyproject.toml`, y con cualquier otro nombre responde
*"Could not read any configuration"* y el CI se pone rojo por el motivo equivocado.

Y los módulos de cada lista van **uno por línea**. Separados por comas, `configparser`
los lee como **un solo nombre de módulo** que no existe, y el contrato pasa en verde
para siempre.

Además, dentro de una capa `|` significa *independientes* —esos módulos no pueden
importarse entre sí— y `:` significa que sí pueden. Con `|` en la capa intermedia,
`route` no podría leer de `report`, que es justo lo que exigen ADR-0012 y §9.9.

```ini
[importlinter]
root_package = docbench_es
include_external_packages = True

[importlinter:contract:capas]
name = Las capas van hacia abajo, nunca hacia arriba
type = layers
# `exhaustive` pone el CI rojo si aparece un modulo nuevo sin ubicar en `layers`.
# OJO: configparser NO quita comentarios en linea. Este comentario va en su propia
# linea a proposito; escrito detras del valor, `exhaustive` valdria "true  # ...".
exhaustive = true
containers =
    docbench_es
layers =
    cli
    route
    publish : drift
    report
    reference
    ask : truth : extract : corpus : entity : sources : glossary : sample
    core
    types : errors

[importlinter:contract:nucleo-sin-mundo]
name = El nucleo es puro: no toca red, disco ni proveedores
type = forbidden
source_modules =
    docbench_es.core
forbidden_modules =
    docbench_es.extract
    docbench_es.entity
    docbench_es.corpus
    docbench_es.sources
    docbench_es.truth
    requests
    httpx
    urllib
    socket
    subprocess

[importlinter:contract:drift-sin-verdad]
name = La deteccion de deriva no puede depender de verdad de referencia nueva
type = forbidden
source_modules =
    docbench_es.drift
forbidden_modules =
    docbench_es.truth

[importlinter:contract:route-solo-report]
name = La recomendacion se deriva de mediciones publicadas
type = forbidden
source_modules =
    docbench_es.route
forbidden_modules =
    docbench_es.extract
    docbench_es.ask
    docbench_es.truth
```

**Los tres contratos prohibidos hacen cumplir tres afirmaciones del README:**

- `core` no toca el mundo: TEDS y los verificadores se prueban sin red y se pueden reejecutar sobre extracciones viejas con un motor nuevo.
- `drift` no importa `truth`: la deriva funciona sin anotar nada nuevo, o sea que es ejecutable en producción. Sin esta regla, en tres meses alguien mete una dependencia y la afirmación se cae sin que nadie se entere.
- `route` no importa nada que mida: la recomendación sale de números publicados, no de una heurística escondida.

---

## 9. Los módulos con lógica no obvia

Para cada uno: qué responsabilidad tiene, qué entra, qué sale, qué funciones públicas expone y qué invariantes mantiene.

### 9.1 `core.canonical` — la forma canónica

**Responsabilidad.** Convertir cualquier salida de extractor a `CanonicalTable` y validar sus invariantes. Es puro.

```python
# Los cinco conversores llevan `page_span` como parámetro de palabra clave:
# NINGUNO de los cinco formatos lleva número de página, así que lo pone quien
# llama. Un `page_span` inventado envenenaría el estrato `multipagina` (LIMITS 32).
def from_html(html: str, *, page_span: tuple[int, int] = (1, 1)) -> list[CanonicalTable]: ...
def from_markdown(md: str, *, page_span=(1, 1)) -> list[CanonicalTable]:
    """expresses_spans = False siempre. Markdown no tiene rowspan."""
def from_dataframe(dfs: Iterable[object], *, page_span=(1, 1)) -> list[CanonicalTable]:
    """expresses_spans = False: un DataFrame es una rejilla rectangular y no
    distingue «combinada» de «repetida». ADR-0006 ya lo dice al listar a Camelot
    entre los que pierden las celdas combinadas. Precio en LIMITS 35."""
def from_tei(tei: str, *, page_span=(1, 1)) -> list[CanonicalTable]:
    """expresses_spans = True: <cell cols= rows=> es rowspan/colspan."""
def from_text_heuristic(text: str, *, page_span=(1, 1)) -> list[CanonicalTable]:
    """Último recurso para OCR plano. expresses_spans = False.
    Marca confidence baja: es una heurística y se declara como tal."""
def validate(t: CanonicalTable) -> tuple[bool, list[str]]: ...
def holes(t: CanonicalTable) -> tuple[tuple[int, int], ...]:
    """Las posiciones sin cubrir. Es la mitad ejecutable del «o declara los
    huecos» de §6.2 (ADR-0018), y lo que L2 usa para emitir celda AUSENTE, que
    no es lo mismo que celda vacía."""
def normalize_cell_text(s: str) -> str:
    """Espacios, guiones suaves y caracteres invisibles. **NO toca los números**
    ni los acentos ni ningún glifo visible: ver ADR-0017, que corrige la
    redacción anterior de este docstring."""
```

> **Transcrito de [ADR-0017](docs/adr/0017-normalizacion-no-toca-los-numeros.md), en L1.** Este docstring decía *«Espacios, guiones suaves, **comas decimales, separadores de millares**»*, y eso se contradecía con la frase que venía justo detrás. Normalizar el separador decimal repararía en silencio al extractor que devuelve `1,234.56` donde la página dice `1.234,56`, que es **el fallo más específicamente español que existe en una tabla de números** y lo que distingue a este banco de una traducción. La equivalencia numérica no desaparece: vive en el verificador `numeric` de §9.3 y en `truth.derived` de L4, **con su tolerancia declarada**, que es una comparación explícita en vez de una reescritura silenciosa.
>
> La regla que sustituye a la redacción vieja: **sólo se toca lo invisible o la forma de composición Unicode; ningún glifo visible se altera ni se borra**, con una excepción enumerada y con test propio, la expansión de las siete ligaduras latinas. Son **seis normalizaciones aplicadas y seis rechazadas**, cada una con **a quién beneficia si me paso**, en `docs/metrics.md`. Un test de la puerta se pone rojo si una decisión del código no está documentada allí.
>
> **La consecuencia, para que no se lea como incoherencia:** el extractor que se equivoca de convención numérica queda penalizado **en dos niveles** —en TEDS con contenido (L2), porque la cadena difiere, y en el verificador `numeric` (L9), donde con tolerancia puede darse por bueno—. No es doble contabilidad: son dos preguntas distintas, *«¿transcribiste la celda?»* y *«¿el número es correcto?»*, y responderlas por separado es informativo.

> **`core.canonical` es un PAQUETE, no un fichero** (§8), por el límite de 300 líneas de `CLAUDE.md` y con el precedente de ADR-0013. La superficie de import no cambia. Y **`validate()` delega en `CanonicalTable.is_wellformed()`**, donde vive el algoritmo, porque el contrato de capas prohíbe que `types` importe `core`: ver la nota de §6.2.

**Invariante clave:** el `expresses_spans` de `CanonicalTable` lo fija el conversor según el formato de origen. El `expresses_spans` que declara un `Extractor` es solo una declaración: la suite de conformidad la contrasta contra lo que produce el conversor y **falla si el extractor miente**. Así ningún extractor puede declararse capaz de algo que su formato no permite.

### 9.2 `core.teds` — la métrica de estructura

```python
def teds(pred: CanonicalTable, gold: CanonicalTable) -> float: ...
def teds_struct(pred, gold) -> float:
    """TEDS-S: solo estructura, ignora el contenido de las celdas."""
def teds_batch(pairs) -> TedsReport: ...

def para_publicar(valor: float) -> float:
    """El SUELO de presentación: recorta a 0 un TEDS negativo. ADR-0023."""
```

> **Transcrito de [ADR-0023](docs/adr/0023-teds-negativo-suelo-al-publicar.md), en L2.** TEDS **no está acotado por cero** —la distancia se calcula con la raíz y el denominador cuenta sólo los descendientes—, y la referencia de PubTabNet devuelve el mismo negativo. El cálculo **no se toca**: recortar dentro de `teds()` rompería el criterio de aceptación de este mismo hito. El recorte es de **presentación**, vive en `para_publicar()` y se declara junto al número, incluido **cuántos se recortaron**. Requisito para L5 en `LIMITS.md` 46.

**Validación obligatoria:** contra la implementación de referencia de PubTabNet sobre sus propios casos, en `tests/fixtures/pubtabnet/`. Si no reproduce sus números, la implementación está mal. **No se valida "a ojo"**, porque TEDS no tiene valores intuibles.

> **Transcrito de [ADR-0020](docs/adr/0020-teds-compara-contenido-canonico.md) y [ADR-0021](docs/adr/0021-forma-canonica-del-arbol-de-teds.md), en L2.** *«Sus números»* hay que precisarlo, porque tal cual se lee mal y el hito no se podría cerrar.
>
> **La referencia no normaliza nada** —tokeniza la celda en caracteres sueltos y compara con Levenshtein— y **cuenta en el denominador el marcado inline dentro de las celdas**: 189 nodos `<b>`/`<i>`/`<sup>` en sus 20 casos, que `CanonicalTable` no guarda porque su modelo de celda es texto plano. Comparar mi TEDS sobre tablas canónicas contra sus valores sobre HTML crudo da **15 de 20 casos distintos** —media +0,0092, rango [−0,0342, +0,2070]—, y **en 10 de ésos la normalización no toca ni un texto**: la causa dominante es la forma del árbol, no normalizar.
>
> Por eso **el golden se genera dando a la referencia el MISMO contenido**: el render canónico de las mismas tablas. Los dos lados parten del mismo árbol y del mismo texto, así que una diferencia sólo puede venir del algoritmo, que es lo que esta sección manda validar. Resultado medido: **20 de 20 a cuatro decimales**. La diferencia contra el HTML crudo se publica en `RESULTS.md` con su descomposición, y el precio —que estos TEDS no son directamente comparables con los publicados en la literatura sobre PubTabNet— está en `LIMITS.md` 39.
>
> **La forma del árbol es una decisión con número** (ADR-0021): `<thead>` sólo con el prefijo máximo de filas de cabecera, `<tbody>` el resto, **todas las celdas `<td>` y nunca `<th>`** —la referencia no le lee los spans a un `<th>`—, `<td>` como hoja, y **el hueco no emite nodo**. Medido: un `<tbody>` de más o un `<th>` donde va un `<td>` cuestan **0,667** en una tabla de una celda.
>
> **Y dos casos degenerados donde manda §12 y no la referencia:** dos tablas vacías dan **1** —la referencia devuelve `0.0` para dos cadenas vacías y **revienta con `ZeroDivisionError`** ante `<table></table>`, porque divide por cero nodos—; una vacía y otra no dan **0**, que sí coincide.

### 9.3 `core.answer` — los seis verificadores

```python
def verify(q: Question, given: str) -> tuple[bool, str | None]:
    """Devuelve (acertó, id del par confundible si se confundió)."""
```

| Verificador | Regla |
|---|---|
| `exact` | Igualdad tras normalización declarada: mayúsculas, espacios, acentos no |
| `numeric` | Diferencia absoluta o relativa dentro de `tolerance`. Acepta coma y punto decimal, y separador de millares español |
| `set` | Igualdad de conjuntos tras normalizar cada elemento |
| `date` | Igualdad de fecha tras parsear formatos españoles: `12/03/2026`, `12 de marzo de 2026` |
| `boolean` | Sí/no, verdadero/falso, con sus variantes |
| `span` | El texto dado contiene la respuesta y no contiene ninguno de los distractores declarados |

**Detección de confusión:** si la respuesta dada coincide con el valor del *otro* término de un par confundible, se marca `confused_with`. Eso es lo que alimenta la métrica de nivel 3.

### 9.4 `entity.boe` y `entity.boe_xml`

**`discover`** llama a la API de sumarios del BOE por fecha, filtra por sección y por tipo, y devuelve `DocRef` perezosamente. No descarga.

**`fetch`** baja el PDF y el XML del mismo identificador. Comprueba coherencia: si el texto del XML y el texto extraído del PDF discrepan por encima de un umbral, **descarta el par y lo cuenta**. Un emparejado silenciosamente incorrecto envenena todo el benchmark.

**`truth`** parsea el XML a `CanonicalTable` y genera los `Fact` con plantillas sobre la matriz.

**`strata`** etiqueta: `tabla-simple`, `celdas-combinadas`, `multipagina`, `escaneado`, `con-notas-al-pie`, `sin-tabla`.

**`escaneado` frente a `nacido-digital`, y por qué no hay etiqueta `anexo-png`.** La frontera es **la capa de texto**, medida, no el número de imágenes. Se calcula sobre `RawDoc.primary`, que es lo que `strata` ya recibe:

```
caracteres_extraibles_por_pagina = caracteres_no_blancos(capa_de_texto) / n_pages
escaneado  ⇐ caracteres_extraibles_por_pagina < umbral_capa_texto   (por defecto 100)
nacido-digital ⇐ en caso contrario
```

El umbral vive en el perfil de la entidad (§10.1), no en el código, y **su reparto se publica**: qué proporción cae a cada lado y con qué valor. Es el mismo umbral que decide la causa de fallo `no_text_layer` de §6.9, para que un documento no pueda ser `nacido-digital` y hacer fallar a un extractor por falta de capa de texto a la vez.

**Por qué no se parte por número de imágenes**, que era la regla anterior (`anexo-png ⇐ sin <table> y con <img>`): el número de imágenes no determina nada. Un informe nativo con 40 gráficos tiene capa de texto perfecta y un escaneado de 3 páginas no tiene ninguna. Esa regla metía en el mismo estrato un documento de 8 páginas con una figura y un anexo de 136 páginas con 134 imágenes —medido en el sondeo del BOE de 22 ago 2026—, y en ellos **compiten familias de extractor distintas**: sin capa de texto un parser de texto no compite, y su cero no mide su calidad; con capa, un OCR se desperdicia. Un estrato que mezcla las dos poblaciones tiene una exactitud media que no describe a ninguna, y §12 la propaga a la ponderada.

**`privacy`** declara `contains_personal_data=True`, `redaction_required=False`, con la justificación escrita: publicidad legal previa. **La distinción se documenta en vez de darse por supuesta.**

### 9.5 `truth.consensus` y `truth.calibrate`

`consensus` corre N extractores heterogéneos, alinea sus tablas por posición y contenido, y marca cada celda como acordada o discordante. Solo lo discordante va a revisión humana. Publica siempre la **tasa de discordancia**, que es la medida de cuánto te puedes fiar del consenso.

`calibrate` es el resultado propio: corre `CONSENSUS` sobre el corpus del BOE, donde también hay `DERIVED`, y publica el error del consenso frente a la verdad de verdad. **Ese número es la barra de error de todos los resultados por consenso en cualquier otra entidad.**

### 9.6 `ask.templates` y `ask.traps`

`templates` genera preguntas desde `Truth.facts` con plantillas parametrizadas. Permite miles sin escribirlas. **Heredan el sesgo de la plantilla y son fáciles de forma sistemática**, y por eso se cuentan aparte.

`traps` son escritas a mano, una o varias por `ConfusablePair`. No se pueden generar, porque el punto es que suenan iguales.

### 9.7 `glossary.contribution` — la métrica que nadie tiene

```python
def measure_contribution(campaign, entity) -> GlossaryContribution:
    """Corre la capa 2 dos veces, idéntica salvo el glosario:
       - brazo A: AnswerEngine con glossary=None
       - brazo B: AnswerEngine con el glosario de la entidad
       Devuelve la diferencia en puntos con IC bootstrap sobre documentos."""
```

Es la primera cuantificación seria de lo que vale una capa semántica. Sale casi gratis, porque es una corrida más del mismo pipeline.

### 9.8 `drift` — las tres señales

Ninguna necesita verdad de referencia nueva. Por eso son ejecutables cada mes en casa de un cliente.

| Módulo | Señal | Cómo |
|---|---|---|
| `shape` | Deriva de forma | Distancia entre la distribución de rasgos estructurales (nº de tablas, celdas combinadas, densidad de texto, presencia de imágenes, páginas) de los documentos nuevos y la línea base |
| `agreement` | Deriva de acuerdo | Caída del acuerdo entre extractores independientes sobre los mismos documentos. Si antes coincidían y ahora no, algo cambió |
| `vocabulary` | Deriva de vocabulario | Aparición de términos fuera del glosario en posiciones donde antes había términos conocidos |

**Aviso que va en el informe:** la deriva de acuerdo detecta **cambio**, no empeoramiento. Podría ser que un extractor haya mejorado. Es un aviso para ir a mirar, no un veredicto.

### 9.9 `route.recommend`

```python
def recommend(campaign: CampaignResult, budget_per_doc: float) -> RoutingPlan:
    """Programación entera pequeña: maximiza exactitud esperada sujeto a
    coste medio por documento, con el enrutado a nivel de estrato."""
```

Solo lee de `report`. Devuelve la tabla de enrutado con su coste medio y su exactitud media frente a usar un solo extractor.

---

## 10. Formatos de fichero

### 10.1 Adaptador de entidad, declarativo

Para entidades que no necesitan código, solo configuración:

```yaml
# entities/cliente-expedientes.yaml
version: 1
id: cliente-expedientes
display_name: Expedientes de contratación · Cliente
language: es
truth_mode: CONSENSUS

source:
  kind: sharepoint
  site: https://cliente.sharepoint.com/sites/expedientes
  auth: entra-id
  filter: { extension: [pdf], modified_after: 2026-01-01 }

license:
  name: Interna Cliente
  may_redistribute_content: false
  may_redistribute_derived: true
  attribution: null
  source_url: interno
  verified_on: 2026-11-03
  notes: "Uso interno. No se publica ni el contenido ni el manifiesto de contenido."

privacy:
  contains_personal_data: true
  categories: [identificativos, profesionales]
  special_categories: false
  lawful_basis: interes_legitimo
  redaction_required: true
  redaction_profile: es-admin
  may_send_to_third_party: false     # ← apaga todos los extractores por API
  dpa_reference: CONTRATO-2026-114

glossary: ./glosarios/cliente.semantic.yaml

# `umbral_capa_texto` son caracteres no blancos por pagina (§9.4). Decide a la vez
# el estrato `escaneado` y la causa de fallo `no_text_layer` de §6.9: un solo numero
# para el mismo hecho medido. Por defecto 100.
umbral_capa_texto: 100

strata_rules:
  - { name: escaneado, when: "caracteres_extraibles_por_pagina < umbral_capa_texto" }
  - { name: celdas-combinadas, when: "tables_with_spans > 0" }
  - { name: multipagina, when: "max_table_page_span > 1" }
  - { name: sello-superpuesto, when: "images_overlapping_text > 0" }
```

### 10.2 Plan de muestreo, congelado antes de medir

```yaml
# runs/2026-Q4/plan.yaml
version: 1
entity: boe
campaign: 2026-Q4
frozen_at: 2026-10-01T08:14:22Z
seed: 20261001

# `weight` es la proporcion REAL del estrato en el corpus, o sea found/total.
# Total encontrado: 4210+890+340+95+210 = 5745. Los pesos suman 1,000 por construccion,
# y son los que usa la exactitud ponderada de §12 para deshacer el sobremuestreo.
# El ultimo absorbe el redondeo (210/5745 = 0,0366) para que la suma sea exactamente 1.
strata:
  tabla-simple:      { target: 120, found: 4210, weight: 0.733 }
  celdas-combinadas: { target: 120, found: 890,  weight: 0.155 }
  multipagina:       { target: 100, found: 340,  weight: 0.059 }
  escaneado:         { target: 60,  found: 95,   weight: 0.017 }
  con-notas-al-pie:  { target: 60,  found: 210,  weight: 0.036 }
  # `sin-tabla` se etiqueta pero NO se muestrea en nivel 1: sin tabla, TEDS no está
  # definido. Entra en nivel 2, donde sí hay pregunta y respuesta. Por eso `found`
  # aquí cuenta solo documentos con al menos una tabla.

# `doc_refs` es obligatorio en SamplingPlan (§6): es lo que hace que "congelado"
# signifique algo. Va aparte por tamaño, con su hash dentro del propio plan.
doc_refs_file: runs/2026-Q4/doc_refs.jsonl
doc_refs_sha256: 5b7e14a0c39d

power:
  design: mcnemar_paired
  effect_to_detect: 0.05
  assumed_discordance: 0.20
  alpha: 0.05
  target_power: 0.80
  n_documents_required: 625
  note: >
    La primera campaña es de PRECISIÓN, no de contraste. 460 documentos dan
    intervalos, no potencia para separar extractores parecidos. La discordancia
    real se mide y si sale distinta del 20% supuesto, se dice.

budget:
  max_eur: 25
  vlm_subsample: 120        # los VLM solo sobre esta submuestra estratificada
  level2_extractors: [oracle, docling, pymupdf4llm, vlm-api, marker]
```

### 10.3 Capa semántica exportable

```yaml
# glosarios/dip-cadiz.semantic.yaml
version: 3
entity: dip-cadiz
updated: 2026-11-04
terms:
  aplicacion_presupuestaria:
    definition: "Código orgánica-programa-económica que identifica la partida"
    aliases: [partida presupuestaria, aplicación]
    not_to_confuse_with: [partida]
    discriminator: "La aplicación lleva tres códigos; la partida coloquial suele ser solo la económica"
    appears_in: [presupuesto, modificación de crédito]
    verified_on: 2026-11-04
    verified_by: human
confusables:
  - id: credito-inicial-vs-definitivo
    term_a: crédito inicial
    term_b: crédito definitivo
    why_confused: "Están en columnas contiguas de la misma tabla"
    discriminator: "El definitivo incluye las modificaciones aprobadas hasta la fecha"
    example_doc: { entity: dip-cadiz, external_id: BOP-CA-2026-1234 }
    trap_questions: [q-0412, q-0418]
```

**Pares confundibles de partida, por tipo de entidad:**

| Entidad | Par | Por qué importa |
|---|---|---|
| BOE, convenio | `salario base` / `salario bruto anual` | Uno es la tabla, el otro incluye complementos y pagas. Confundirlos es un error del 20% o más |
| BOE, convenio | `vigencia del convenio` / `vigencia de las tablas` | No coinciden casi nunca. La tabla puede estar prorrogada con el convenio denunciado |
| BOE, convenio | `tabla de 2026` / `tabla revisada con atrasos` | La revisión sustituye a la publicada, y las dos están en el mismo BOE |
| Diputación | `crédito inicial` / `definitivo` / `disponible` | Tres números distintos en la misma tabla |
| Diputación | `fecha de adjudicación` / `de formalización` | Consecuencias de plazo distintas |
| Empresa | `importe neto de la cifra de negocios` / `facturación` | La primera es la partida contable; la segunda es coloquial |
| Empresa | `EBITDA` / `EBITDA ajustado` / `resultado de explotación` | Tres definiciones y solo una normalizada |

### 10.4 Manifiesto de campaña

Es lo que se publica cuando el contenido no se puede publicar.

```json
{
  "esquema": "docbench-es.manifiesto/1", "entidad": "boe",
  "plan_hash": "c3d80a17f42e…",
  "ventana": { "desde": "2026-03-09", "hasta": "2026-04-11" },
  "emparejado": { "intentados": 1043, "aceptados": 1000, "descartados": 43,
                  "por_causa": { "incoherente": 43 },
                  "tasa_descarte": 0.0412, "umbral_coherencia": 0.85 },
  "dias_sin_boletin": ["2026-03-15", "…"],
  "ritmo": { "espaciado_mediano_s": 1.0000851, "espaciado_minimo_s": 1.0000211,
             "n_espaciados": 2064 },
  "atribucion": "Basado en datos de la Agencia Estatal Boletín Oficial del Estado",
  "licencia_corpus": { "name": "Reutilización BOE", "may_redistribute_content": true,
                       "may_redistribute_derived": true, "source_url": "…" },
  "licencia_codigo": "Apache-2.0",
  "documentos": [
    { "external_id": "BOE-A-2026-4223", "sha256": "9c1f…", "n_pages": 34,
      "strata": ["celdas-combinadas", "multipagina"],
      "seccion": "1", "fecha_sumario": "2026-03-09",
      "url_pdf": "…", "url_xml": "…", "fetched_at": "2026-10-02T09:11:00Z",
      "actualizado_en": "2026-08-24" }
  ]
}
```

> **Transcrito de [ADR-0033](docs/adr/0033-el-manifiesto-nace-publicable.md), en
> L3.** Esta sección publicaba el manifiesto **mínimo**: suficiente para reproducir
> una campaña, insuficiente para **publicar el corpus**, que es lo que ADR-0033
> decide que tiene que poder hacerse sin re-cosechar. Lo que entra y por qué:
>
> | Añadido | Sin él |
> |---|---|
> | `seccion` y `fecha_sumario` por documento | la población del denominador **no se puede re-derivar sin volver al origen**, y volver seis meses después no devuelve lo mismo |
> | `actualizado_en` por documento | el manifiesto **no cumple la licencia** del BOE, que exige la fecha junto a la atribución |
> | `atribucion`, literal y dentro | una referencia a dónde leerla no es la atribución |
> | `licencia_corpus` **separada** de `licencia_codigo` | confundirlas es lo que hace impublicable un dataset: el código puede ser Apache-2.0 y el corpus estar sujeto a las condiciones del BOE |
> | `ventana`, `por_causa` y `umbral_coherencia` junto a la tasa | **ADR-0030**: una tasa sola es una propiedad del calendario disfrazada de propiedad del corpus, y está medido que entre ventanas va de 2,0% a 5,5% |
> | `ritmo` con su espaciado **medido** | «1 rps» declarado no es «1 rps cumplido» |
>
> **Y lo que se renombra**: `n_documents`/`n_discarded_pairing` pasan al bloque
> `emparejado` con su denominador `intentados` al lado, porque publicar los dos
> primeros sin el tercero deja la tasa sin población. `download_script` se cae: el
> comando de rehidratación vive en el README del corpus, que es donde alguien lo
> busca, y una ruta dentro del JSON se queda vieja sin que nada avise.
>
> **`plan_hash` se queda, y ahora tiene función**: es el `sha256` del `plan.yaml`
> congelado antes de cosechar, y `scripts/verificar_corpus.py --plan` lo comprueba.
> Sin él, el verificador compara contra *el fichero que le pases*, y nada ata el
> manifiesto a un plan concreto.

---

## 11. La interfaz de línea de comandos, completa

```bash
# ── PREPARACIÓN DEL ENTORNO ─────────────────────────────────────────
docbench init                          # detecta el entorno y escribe profile.yaml
docbench doctor                        # ¿alcanzo datos, modelos, clúster, salidas?
docbench doctor --profile azure.yaml
docbench plugins list                  # adaptadores y extractores descubiertos
docbench conform --entity <id>         # suite de conformidad de un adaptador
docbench conform --extractor <id>      # suite de conformidad de un extractor

# ── ENTIDADES ───────────────────────────────────────────────────────
docbench entity list
docbench entity show boe               # licencia, privacidad, modo de verdad, glosario
docbench entity doctor boe             # acceso, licencia, privacidad, y si da verdad

# ── CORPUS ──────────────────────────────────────────────────────────
docbench corpus plan --entity boe --from 2026-01-01 --to 2026-08-31 \
                     --filter convenios --strata-target celdas-combinadas=120 \
                     --seed 20261001 --out runs/2026-Q4/plan.yaml
docbench corpus fetch --plan runs/2026-Q4/plan.yaml    # con caché
docbench corpus manifest --campaign 2026-Q4
docbench corpus stats --campaign 2026-Q4               # distribución por estrato

# ── VERDAD DE REFERENCIA ────────────────────────────────────────────
docbench truth build --plan ... --mode DERIVED
docbench truth build --plan ... --mode CONSENSUS --extractors docling,pymupdf4llm,marker
docbench truth annotate --plan ... --pass 1            # abre el anotador local
docbench truth annotate --plan ... --pass 2            # segunda pasada ciega
docbench truth calibrate --campaign 2026-Q4 --against DERIVED

# ── PREGUNTAS ───────────────────────────────────────────────────────
docbench ask generate --campaign 2026-Q4 --templates convenios.yaml
docbench ask traps --glossary glosarios/boe.semantic.yaml
docbench ask validate --campaign 2026-Q4    # todo verificador debe discriminar

# ── MEDICIÓN ────────────────────────────────────────────────────────
docbench run --plan ... --level 1 --extractors all
docbench run --plan ... --level 2 --extractors oracle,docling,... --budget 25EUR --explain
docbench run --plan ... --level 2 --budget 25EUR
docbench run --plan ... --level 3
docbench run --plan ... --resume

# ── RESULTADOS ──────────────────────────────────────────────────────
docbench report --campaign 2026-Q4 --format md,html,json
docbench report --campaign 2026-Q4 --format onepager-pdf --language es
docbench route --campaign 2026-Q4 --budget-per-doc 0.005   # emite routing.yaml
docbench route --validate runs/2026-Q4/routing.yaml         # rechaza reglas sin `measured`
docbench glossary contribution --campaign 2026-Q4

# ── OPERACIÓN CONTINUA ──────────────────────────────────────────────
docbench drift baseline --campaign 2026-Q4
docbench drift check --entity <id> --since 2026-11-01
docbench drift watch --entity <id> --cron "0 6 * * 1"
docbench toolwatch --extractors docling,marker --corpus frozen-2026-Q4   # deriva de herramienta

# ── ENTREGA ─────────────────────────────────────────────────────────
docbench export-pipeline --out ./pipeline-referencia/
docbench publish --campaign 2026-Q4        # respeta licencias o falla
docbench replay runs/2026-Q4/              # reproducir sin credenciales ni gasto
```

### Banderas globales

| Bandera | Qué hace |
|---|---|
| `--explain` | Imprime qué adaptadores usará, cuántas llamadas, sobre qué datos y cuánto costará. **No ejecuta.** Es lo que un responsable de seguridad necesita ver para darte permiso |
| `--dry-run` | Estima el coste y aborta si excede el presupuesto |
| `--profile` | Perfil de entorno a usar |
| `--offline` | Fuerza solo local. Falla si algo requiere red |
| `--seed` | Semilla, para todo lo que sortee |
| `--resume` | Reanuda una campaña interrumpida |

### Códigos de salida

| Código | Significado |
|---|---|
| 0 | Todo bien |
| 1 | La medición terminó pero hay fallos por encima del umbral declarado |
| 2 | Violación de política: licencia o privacidad. **La campaña no arrancó** |
| 3 | Presupuesto excedido, abortado antes de gastar |
| 4 | Error de infraestructura: no alcanzo la fuente, el proveedor cayó |
| 5 | Contrato de plugin incumplido |
| 6 | `TruthUnavailable`: se pidió exactitud en una entidad con `truth_mode: NONE`. El motor se niega, no devuelve un número inventado |

Separar el 4 y el 2 del 1 es lo que evita que un equipo aprenda a ignorar el rojo.

---

## 12. Métricas: fórmula, supuestos y caso degenerado

Todo esto vive también en `docs/metrics.md`. Es donde un examinador con formación estadística va a buscar.

### Nivel 1 · Estructura

| Métrica | Fórmula | Supuesto | Caso degenerado |
|---|---|---|---|
| **TEDS** | Distancia de edición de árbol normalizada entre la tabla predicha y la real | Que ambas se pueden expresar como árbol de celdas | Tabla vacía: se define como 1 si las dos lo están, 0 si solo una |
| **TEDS-S** | Igual ignorando el contenido | Idem | Idem |
| **Exactitud de celda** | Celdas correctas / celdas de la verdad | Emparejado por posición tras alinear | Sin celdas: `NO_APLICABLE` |

> **Transcrito de [ADR-0025](docs/adr/0025-la-exactitud-de-celda-no-alinea.md), en L2.** *«Tras alinear»* hay que precisarlo, igual que *«sus números»* de §9.2: **el alineamiento es el de L1**, o sea la colocación canónica en la rejilla que hacen los cinco conversores resolviendo `rowspan`/`colspan`. `core.cellmatch` **no hace un segundo alineamiento**: no busca el desplazamiento que maximiza aciertos.
>
> **La consecuencia, dicha antes de que sorprenda:** una tabla desplazada una fila entera saca **0,0** con todas sus celdas bien transcritas. Es deliberado —en una tabla de importes la posición es el dato, y una columna de más cambia a qué concepto pertenece cada número— y el fallo **sí se mide, en TEDS**, que ve el cambio de forma del árbol. `cell_accuracy` es **exactitud posicional** y no se compara con cifras de la literatura que alinean. Precio en `LIMITS.md` 53.

> **Y `is_header` NO entra en la identidad de la celda**, también a propósito: decide el corte `<thead>`/`<tbody>` del árbol (ADR-0021), así que una cabecera mal marcada la penaliza TEDS. Medido sobre dos tablas que sólo difieren en el flag: `cell_accuracy` = **1,0**, `teds` = **0,5**. Meterlo en las dos sería contar el mismo fallo dos veces.
| **Tablas no detectadas** | Tablas de la verdad sin correspondencia | El emparejado es correcto | — |
| **Tablas partidas o fusionadas** | Recuento con su tipo | Idem | — |
| **Cobertura evaluable** | Tablas evaluables para ese extractor / tablas totales | `expresses_spans` es correcto | Si es 0, no se publica nota, solo `NO_APLICABLE` |

### Nivel 2 · Respuesta final

| Métrica | Fórmula | Supuesto | Caso degenerado |
|---|---|---|---|
| **Exactitud absoluta** | aciertos / preguntas | Los verificadores discriminan, comprobado en `ask validate` | Cero preguntas: no se publica |
| **Exactitud relativa** | aciertos(e) / aciertos(oracle) | `oracle` es el techo real del pipeline | Si `oracle` acierta 0, el pipeline está roto y **se aborta la publicación** |
| **Exactitud ponderada** | Suma sobre estratos de exactitud por peso | Los pesos reflejan la distribución real y están declarados | — |
| **IC** | Bootstrap BCa sobre **documentos**, no sobre preguntas | Las preguntas de un documento están correlacionadas | Varianza cero: cae a percentil y se marca `degenerado` |

**El detalle que un examinador bueno pregunta:** el bootstrap remuestrea documentos y arrastra sus preguntas. Remuestrear preguntas sueltas las trata como independientes e infla la precisión aparente.

> **Transcrito de [ADR-0034](docs/adr/0034-los-resultados-se-publican-por-banda-de-longitud.md),
> en L3.** **Además de por estrato, los resultados se publican por BANDA DE
> LONGITUD**, y las bandas se definen aquí, no cuando toque:
>
> | Banda | Páginas | % del BOE (n=600) | En un corpus de 1.000 |
> |---|---|---|---|
> | **corto** | 1 – 4 | 37,0% | ~370 |
> | **medio** | 5 – 12 | 47,8% | ~478 |
> | **largo** | 13 o más | 15,2% | ~152 |
>
> **En páginas absolutas y no en terciles del corpus**: un tercil es una propiedad
> del BOE, y «1 a 4 páginas» significa lo mismo en la carpeta de cualquiera. El eje
> existe para ser portable, así que definirlo por cuantiles propios lo haría inútil
> justo para el caso que lo justifica. Los cortes salen de las tres ventanas del
> sondeo: 4 es el percentil 33 y 13 está cerca del 87, o sea **n suficiente en las
> tres bandas para publicar con intervalo**.
>
> **Y la banda no sustituye al estrato**: lleva señal medida propia, porque la
> longitud predice fallos que el estrato no ve —un documento largo agota contextos
> y multiplica el coste— y el estrato predice fallos que la longitud no ve.
> **Se publican los dos ejes, no uno.** Lo consume `route`, en **L17**.

### Nivel 3 · Vocabulario

| Métrica | Fórmula | Supuesto | Caso degenerado |
|---|---|---|---|
| **Tasa de confusión por par** | Respuestas con `confused_with = par` / preguntas trampa de ese par | El discriminador del par está bien escrito | Sin trampas para ese par: `NO_APLICABLE` |
| **Confiadamente incorrecta** | Mal y sin señalar duda / total de mal | La señal de duda se detecta con patrones declarados | — |
| **Aportación del glosario** | exactitud(con glosario) − exactitud(sin) | Todo lo demás idéntico entre los dos brazos | IC que cruza cero: se publica que no hay efecto detectable |

### Deriva

| Señal | Fórmula | Supuesto |
|---|---|---|
| **Forma** | Distancia entre distribuciones de rasgos estructurales frente a la línea base | La línea base es representativa |
| **Acuerdo** | Caída del acuerdo entre extractores frente a la línea base | Los extractores son independientes entre sí |
| **Vocabulario** | Tasa de términos fuera del glosario en posiciones conocidas | El glosario está al día |

---

## 13. Adaptación al cliente

### 13.1 Su extractor entra como concursante

```toml
# pyproject.toml del cliente
[project.entry-points."docbench.extractor"]
pipeline-interno = "cliente_docs.bench:PipelineInterno"
```

```python
class PipelineInterno:
    id = "pipeline-interno"
    version = "3.2.0"
    kind = "hibrido"
    runs_locally = True
    expresses_spans = True
    benchcore_api = "1.x"

    def probe(self) -> ProbeResult: ...
    def extract(self, doc, page_range=None) -> Extraction:
        salida = mi_pipeline_de_siempre(doc.primary)     # su código, intacto
        return Extraction(
            extractor_id=self.id, extractor_version=self.version, doc_ref=doc.ref,
            text=salida.texto,
            # from_html devuelve list[CanonicalTable]: hay que aplanar, o `tables`
            # sale como tupla de listas y mypy --strict lo rechaza.
            tables=tuple(ct for h in salida.tablas_html for ct in canonical.from_html(h)),
            # RawDoc.n_pages es int | None y Extraction.pages_processed es int.
            native_format="html", pages_processed=doc.n_pages or 0,
            cost=Cost.zero(), latency_ms=salida.ms, warnings=(),
        )
    def cost_of(self, ex) -> Cost: ...
```

```bash
docbench conform --extractor pipeline-interno
docbench run --plan ... --extractors all,pipeline-interno
```

Y en la tabla su pipeline aparece **al lado de los ocho de referencia, con el mismo corpus, la misma métrica y el mismo intervalo**. Ese es un informe que un cliente paga.

### 13.2 El PDF de una página

```
EVALUACIÓN DE EXTRACCIÓN DOCUMENTAL · Cliente · noviembre 2026

  Vuestro pipeline actual acierta el 71% de las preguntas.
  El mejor extractor probado acierta el 89%.
  Enrutando por tipo de documento: 87% a 0,002 €/documento.

  [gráfico: exactitud frente a coste, con vuestro punto marcado]

  Recomendación
  1. Cambiar el extractor de documentos con tablas combinadas (34% del volumen)
  2. Mantener el actual para el resto: la diferencia no es significativa
  3. Cargar el glosario: sube 4 puntos más, sin coste

  Medido sobre 460 documentos vuestros entre el 3 y el 11 de noviembre.
  Reproducible con: docbench replay runs/2026-11-11/
```

Es la mitad del patrón *forward deployed* que el informe de mercado sitúa creciendo un 30% desde 2022: código que corre en producción del cliente **y conversación con el comité la misma tarde**.

### 13.3 Modo aislado

Con el perfil `airgap`, todo corre sin internet: extractores locales, respuesta en `ollama` o `vllm`, informe en HTML y PDF. **Se pierden los VLM frontier y el informe lo declara en su cabecera** en vez de dar números incompletos como si fueran completos.

---

## 14. Tests: qué se prueba y qué demuestra cada uno

| Nivel | Qué prueba | Qué demuestra | Criterio |
|---|---|---|---|
| **Unitario** | Conversores canónicos, verificadores, ponderación, política | Que el núcleo puro es correcto en aislamiento | < 20 s, sin red |
| **Invariantes de tabla** | `validate()` sobre tablas construidas con solapes, huecos y spans fuera de rango | Que la forma canónica no admite basura | 100% detectados |
| **TEDS contra PubTabNet** | Los casos de referencia | Que tu TEDS es TEDS | Coincidencia a 4 decimales |
| **Fixtures de tabla** | Tablas a mano: combinadas, multipágina, notas al pie, celdas vacías, tabla partida | Que las métricas se comportan como se espera en los casos difíciles | Determinista |
| **Contrato de entidad** | La suite contra los cuatro adaptadores propios | Que el contrato es implementable y uniforme, y que "el motor es agnóstico" es verificable | Obligatoria por adaptador |
| **Contrato de extractor** | La suite contra los ocho | Idem, y que `expresses_spans` se declara bien | Obligatoria |
| **Adaptador restrictivo** | Uno con `may_redistribute_content: False` | Que `publish` **aborta** | Obligatorio |
| **Adaptador con categorías especiales** | Uno con `special_categories: True` | Que el registro lo **rechaza** | Obligatorio |
| **Adaptador sin terceros** | Uno con `may_send_to_third_party: False` + extractor por API | Que la campaña **no arranca** | Obligatorio |
| **Fuga de credenciales** | Se busca cada secreto en artefactos, logs y caché | Que no aparece en ninguno | Cada PR |
| **Extractor `oracle`** | El brazo de control | Que el pipeline no es el cuello de botella | Antes de publicar nivel 2 |
| **Degradación de extracción** | Se borra una fila, se funden dos celdas, se rompe una cabecera | **Que TEDS y la exactitud son sensibles a los errores que dicen medir.** Sin esto, las métricas son números sin validar | Detección > umbral declarado |
| **Deriva sintética** | Se inyecta una plantilla artificialmente distinta en un lote | Que `drift` la detecta, **y con cuánto retraso** | Recuperación en < N documentos |
| **Consenso contra derivada** | `CONSENSUS` sobre el BOE | Que la barra de error del consenso es real y no inventada | Antes de publicar cualquier entidad sin XML |
| **Verificadores discriminan** | Cada `verify()` contra respuesta correcta e incorrecta | Que el denominador del nivel 2 no está envenenado | 100% |
| **Reproducibilidad** | Dos corridas con la misma semilla, extractores locales | Métricas idénticas | Bit a bit |
| **Regresión de quickstart** | Los 20 documentos versionados | Que ningún cambio mueve los números sin que te enteres | Cada PR |
| **Regresión de coste** | Estimado frente a real | Que `--dry-run` no miente | Aviso en CI |

**Los tres que más valora un examinador y que casi nadie tiene:** el de **degradación de extracción**, porque demuestra que tus métricas detectan lo que afirman; el de **deriva sintética**, porque convierte "detecto deriva" en "detecto deriva en N documentos, medido"; y los **tres adaptadores hostiles**, porque demuestran que la política es código y no una promesa.

---

## 15. CI

```text
fast:      lint (ruff) + tipos (mypy --strict) + arquitectura (import-linter)
           + unitarios del núcleo + invariantes + TEDS vs PubTabNet
           SIN red, SIN Docker.  Objetivo: < 90 s.  En cada PR
full:      contrato de entidad + contrato de extractor + los tres hostiles
           + fuga de credenciales + quickstart + degradación
           CON Docker.  Objetivo: < 12 min.  En cada PR
nightly:   campaña completa sobre el corpus congelado, publica artefacto
           y compara con la corrida anterior
```

El badge apunta a `fast`, pero **el titular del README es el número medido**, no el badge.

---

## 16. Hitos, con criterio de aceptación y horas

| Hito | Contenido | Criterio de aceptación verificable | Horas |
|---|---|---|---|
| **L0** | Esqueleto, canon, CI de tres trabajos, `types`, `errors`, contrato de capas | `make fast` en verde en menos de 90 s con el repo vacío de lógica | 8-10 |
| **L1** | `core.canonical` + invariantes + conversores desde los cinco formatos | Las tablas con solape, hueco y span fuera de rango se detectan al 100% | 12-16 |
| **L2** | `core.teds` + validación contra PubTabNet | Coincide a cuatro decimales con la referencia | 10-14 |
| **L3** | `entity.base` + conformidad + `entity.boe` + `boe_xml` + `corpus.harvest`/`pairing` | 1.000 documentos emparejados PDF/XML, con manifiesto y tasa de descarte | 16-20 |
| **L4** | `truth.derived` + fixtures de tabla | La verdad derivada reproduce las tablas a mano | 8-10 |

> **Transcrito de [ADR-0039](docs/adr/0039-la-adjudicacion-de-discrepancias-de-la-verdad.md),
> en L4.** El criterio de L4 **no tiene umbral y no dice qué pasa cuando la verdad
> derivada y la transcripción a mano discrepen** — y van a discrepar, porque las
> transcripciones las hace una persona y su tasa de error no es cero. Sin regla
> escrita, la salida cómoda es **ajustar el fixture hasta que pase**, que es la
> regla del fichero congelado del revés y aquí es peor: **el fixture ES el
> instrumento de medida del hito**. Las cuatro reglas, escritas antes de transcribir
> la primera tabla:
>
> 1. **Orden de sospecha: primero el código, segundo la transcripción.** Nunca
>    «ajusto el fixture y sigo».
> 2. **Cada discrepancia se adjudica una a una y su causa se publica**, con dos
>    valores posibles: *fallo del código* o *error de transcripción*. **Sólo el
>    primero habla del producto.**
> 3. **El número separa las TRES**: «N de 30 coinciden; de las M discrepancias, X
>    eran del código, Y errores de transcripción y Z de **frontera ambigua**». Un
>    30/30 obtenido corrigiendo fixtures vale cero; un 27/30 con las tres explicadas
>    vale mucho.
>
>    **La tercera categoría, FRONTERA DE TABLA AMBIGUA**, sale de que el renderizado
>    del PDF y el modelo del XML **no coinciden en qué cuenta como fila**: el PDF
>    parte lo que el XML tiene entero, duplica cabeceras al cambiar de página y deja
>    fuera del borde notas que el XML lleva dentro. **El criterio para decidirla no
>    es qué fuente es más cómoda, sino QUÉ ELECCIÓN PENALIZA A UN EXTRACTOR QUE
>    ACIERTA** — y como un extractor lee el PDF, meter dentro lo que se ve fuera le
>    quita puntos por acertar. **El mecanismo es el del límite 33**: se MARCA la fila
>    como no evaluable en vez de incluirla o excluirla a ojo.
> 4. **Si el código se arregla, se re-comparan LAS 30**, no sólo la que falló.
> 5. **La EVIDENCIA de una adjudicación viene del PDF, NUNCA del XML.** *(Añadida el
>    25 ago 2026, tras la primera comparación y antes de adjudicar ni una
>    discrepancia.)* Comprobar una discrepancia contra el XML **da por supuesto que
>    el XML acierta**, y el XML es lo que el hito mide: es la circularidad que la
>    regla de «transcribir del PDF» evita al principio, reintroducida al final.
>    Ante una discrepancia la única pregunta admisible es *¿qué pone el PDF?* Sólo
>    después se mira el XML crudo, y sólo para separar **defecto del origen** de
>    **fallo del código**.
>
> Y lo que sostiene que las transcripciones sean independientes: **se transcriben
> del PDF y no del XML** —del XML sería comparar el XML consigo mismo—, **se
> congelan con hash antes de la primera comparación**, y **se declara cuáles ya se
> habían inspeccionado** en vez de excluirlas, porque excluirlas sesgaría la muestra.
>
> **Y una precisión que L4 tuvo que aprender: «se congelan antes» sólo significa algo
> si el ORDEN lo puede comprobar un tercero.** En L4 no se podía —el commit que
> declaraba la congelación llevaba un puntero y cero hashes, y los 30 `sha256`
> entraron en el mismo commit que publicó el número—. Está declarado en `LIMITS.md`
> 78 y el mecanismo que lo cierra, para la próxima congelación, en
> [ADR-0041](docs/adr/0041-el-congelado-se-atestigua-con-un-digest-empujado.md): **al
> congelar, lo que va a git es el DIGEST, no el puntero**, en un commit que se empuja
> solo antes de medir.
| **L5** | `extract.base` + conformidad + **ocho** extractores locales + nivel 1 | Primera tabla de estructura con coste y cobertura evaluable. Ocho, no trece: los otros cinco entran después con `/extractor`, una tarde cada uno | 14-18 |
| **L6** | `sample` con McNemar + bootstrap agrupado | Plan congelado y publicado antes de la primera campaña seria | 8-10 |
| **L7** | Quickstart: 20 documentos versionados + `make quickstart` | De clone a tabla en menos de 3 minutos, sin red y sin gastar | 6-8 |

> **Transcrito de [ADR-0042](docs/adr/0042-l7-antes-que-l6-por-demostrabilidad.md), en
> L4.** **L7 se adelanta a L6: el orden pasa a ser `L5 → L7 → L6`.** Para la validez
> de una campaña seria L6 va antes; **para el artefacto, L7 vale mucho más**, porque
> es la diferencia entre que alguien lea que mides y que lo vea medir en su máquina en
> tres minutos. El intercambio es **gratis**, comprobado contra esta misma tabla: el
> criterio de L7 depende de **L5**, que le da los extractores, y **no depende de L6 en
> nada**.
>
> **Lo que no cambia:** **L6 entra antes de la primera campaña seria**, y adelantar L7
> **no** autoriza a publicar una comparación entre extractores sin plan de muestreo.
> Y el riesgo va declarado: un quickstart que funciona invita a leer sus números como
> resultados, así que **su salida lleva su límite en la cabecera** —20 documentos
> elegidos para caber en tres minutos, no para representar nada—, y eso es requisito
> de L7, no una nota.
| **L8** | Los tres adaptadores hostiles + cableado de `benchcore.core.policy` + fuga de credenciales | Los tres bloquean. Ningún secreto en ningún artefacto | 10-12 |
| **L8b** | **Verdad auditada**: 120 documentos con doble pasada ciega y la coincidencia derivada-humana medida | *"La verdad derivada coincide con la auditoría humana en X%, IC [a,b]"*. Elimina la crítica científica más peligrosa del proyecto | 20-26 |
| | **← aquí cierra `v0.1.0`** | | **112-144** |
| **L9** | `ask.templates` + `ask.traps` + `ask.verify` + `AnswerEngine` de referencia | Todo verificador discrimina; `ask validate` en verde | 16-20 |
| **L10** | `extract.oracle` + nivel 2. **El titular del proyecto** | *"Con extracción perfecta X; con el mejor real Y; el hueco atribuible es Z puntos"* | 12-16 |
| **L11** | `glossary` + nivel 3 + `glossary.contribution` | Publicado: *"cargar la capa semántica sube X puntos, IC [a,b]"* | 14-18 |
| **L12** | VLM por API + curva coste-exactitud. **La familia híbrida pasa a `v0.4.0`** | Frontera de Pareto publicada | 8-10 |
| **L12b** | **Los tres estratos que faltan**: escaneado, empresarial sintético y adversarial. Con ellos quedan completos los cuatro de §3 bis | Cada estrato con su verdad declarada y sus números publicados por separado | 16-20 |
| **L13** | Segunda entidad real, modo `CONSENSUS`. **Requisito, no opcional** | La interfaz aguanta sin tocar el motor. Es la única prueba de ADR-0001 | 16-20 |
| **L14** | `truth.calibrate` | Barra de error publicada para resultados por consenso | 8-10 |
| | **← aquí cierra `v0.2.0`** | | **90-114** |
| **L15** | `sources` de plataforma: SharePoint, Blob, S3, SFTP + perfiles | `doctor` valida los seis perfiles | 14-18 |
| **L16** | `reference.export` + `docbench export-pipeline` | Otro equipo lo ejecuta | 8-10 |
| **L17** | `route.recommend`, que emite **`routing.yaml` ejecutable** con la medición dentro de cada regla | `docbench route --validate` rechaza cualquier regla sin su `measured` | 10-12 |
| **L18** | `drift` con las tres señales + deriva sintética | *"Detecto un cambio de plantilla en N documentos, medido"* | 12-16 |
| **L19** | `report.sinks`: onepager-pdf, xlsx, Teams, Azure DevOps | Una página legible por un comité | 10-12 |
| **L20** | `entity.privada` en modo local + `publish` con licencias | Una entidad corre sin publicar nada | 6-8 |
| **L20b** | **`toolwatch`**: deriva de herramienta, comparación pareada por estrato | *"Docling 3.7→3.8: +1,8 global pero −7,3 en multipágina. NO MIGRAR para presupuestarios"* | 14-18 |
| **L20c** | **Leaderboard reproducible + badge** | Cada fila con digest OCI, hardware, latencia fría y caliente, y comando de reproducción | 10-14 |
| | **← aquí cierra `v0.3.0`** | | **84-108** |

### 16.1 Lo que se aplaza a `v0.4.0`

| Se aplaza | Horas que libera | Por qué se puede |
|---|---|---|
| De 13 extractores a 8 | 18-24 | Los ocho cubren las cinco familias. Los otros cinco no cambian ninguna conclusión |
| La familia híbrida VLM+parser | 12-16 | El router del `v0.3.0` ya da el mismo mensaje: enrutar por tipo gana |
| La tercera entidad | 10-14 | Dos ya demuestran ADR-0001. La tercera solo repite |
| Lenguas cooficiales | — | Estratos declarados y vacíos hasta que haya corpus y quien lo sostenga |

**Total: 286 a 366 horas** —112-144 + 90-114 + 84-108, y cada subtotal es la suma de
su tabla—, frente a las 230-294 del diseño anterior. El `v0.1.0` sube de 94-120 a
**112-144**: entran las 20-26 horas de la verdad auditada, que es lo que elimina la
crítica más peligrosa del proyecto y no puede esperar a un release posterior, y salen
las horas de los cinco extractores que pasan a `v0.4.0`.

Los tres releases, en orden, y cada uno es publicable por sí solo.

---

## 17. `LIMITS.md`

1. **La verdad `DERIVED` es transcripción, no lectura del PDF.** El XML puede diferir en maquetación. Se mide y publica la tasa de discordancia del emparejado.
2. **Un solo anotador en `ANNOTATED`.** Se publica acuerdo intra, nunca inter. No es lo mismo y no se presenta como si lo fuera.
3. **`CONSENSUS` hereda los errores comunes.** Por eso existe la calibración cruzada y por eso esos resultados llevan barra de error.
4. **Sesgo de corpus.** El BOE son documentos bien maquetados y firmados, mejores que la media de una empresa. **Los números del BOE son un techo optimista para cualquier otra entidad**, y se dice en la primera línea del informe.
5. **El estrato duro está sobremuestreado.** Se publican las dos cifras, la del estrato y la ponderada a la distribución real.
6. **Las preguntas por plantilla heredan el sesgo de la plantilla.** Son fáciles de forma sistemática. Las trampas se escriben a mano y se cuentan aparte.
7. **El sistema de respuesta está clavado y no optimizado.** Los resultados dicen qué extractor es mejor **con ese sistema**, no cuál es mejor en el mejor sistema posible para cada uno.
8. **Cobertura de idioma.** Castellano. Catalán, gallego y euskera solo si un adaptador los aporta, y no se extrapola.
9. **Riesgo de saturación.** Si el corpus resulta fácil, **eso es el resultado y se publica**, con el estrato duro como titular.
10. **La primera campaña es de precisión, no de contraste.** Con el presupuesto declarado no hay potencia para separar extractores parecidos. Se publica el efecto mínimo detectable.
11. **Extractores que no expresan celdas combinadas salen `NO_APLICABLE`, no cero**, y su nota va con su cobertura evaluable. No se comparan notas calculadas sobre subconjuntos distintos sin decirlo.
12. **En `--offline` faltan los VLM frontier.** El informe lleva cabecera diciéndolo.
13. **Este corpus NO sirve como corpus de `gonogo` nivel 2.** Sus verdades son automáticas, de máquina o de anotador único; `gonogo` exige etiquetas humanas por anotador con anotación múltiple.
14. **Datos personales.** Todos los corpus los contienen. Los de categorías especiales quedan fuera por diseño. Publicidad legal previa no equivale a ausencia de datos personales.
15. **La deriva de acuerdo detecta cambio, no empeoramiento.** Es un aviso para ir a mirar.
16. **El pipeline de referencia no está optimizado y lo dice en su cabecera.** Quien lo lleve a producción tendrá que ajustarlo, y los números no se transfieren a su versión ajustada.
17. **La ganancia del glosario se mide sobre las preguntas de este banco** y es específica de la entidad. No se extrapola.
18. **La redacción de PII es de patrones, no de comprensión.** Caza NIF, IBAN, correos, teléfonos y nombres del glosario. No lo caza todo.
19. **La verdad derivada NO es perfecta, y ahora su error está medido.** Se publica su coincidencia con la auditoría humana y todos los resultados heredan esa barra. Antes esto era una advertencia; ahora es un número.
20. **La auditoría humana es de un solo anotador salvo que se diga lo contrario.** Se publica acuerdo intra-anotador con esas palabras. No es lo mismo que inter y no se presenta como si lo fuera.
21. **El estrato empresarial es sintético.** Lo sintético es más limpio que lo real, así que sus números son otro techo optimista, marcado y no mezclado con los demás.
22. **Los estratos de lenguas cooficiales están vacíos.** Declarados y sin corpus. El proyecto no cubre catalán, gallego ni euskera, y decirlo así vale más que insinuar que sí.
23. **`toolwatch` detecta cambio entre versiones sobre el corpus congelado**, que puede no parecerse al corpus de un cliente concreto. La decisión de migrar es del cliente; el informe le da los números por estrato, no la decisión.
24. **Una mejora global puede esconder una regresión en un estrato.** Por eso el desglose por estrato no es opcional en ningún informe de deriva.

---

## 18. Criterio de terminado

1. **N documentos y M tablas** medidos, por entidad y por estrato.
2. **Exactitud de respuesta por extractor**, absoluta siempre y relativa al `oracle` en las entidades con verdad `DERIVED`; donde no hay `oracle`, la relativa sale `NO_APLICABLE`, con IC, ponderada y sin ponderar.
3. **La diferencia en puntos entre el mejor y el peor a igual coste**, que es la frase del CV.
4. **Tasa de confusión** por par confundible.
5. **Cuántos puntos aporta el glosario**, con IC. La primera cuantificación seria de lo que vale el contexto de negocio.
6. **La barra de error de `CONSENSUS`** medida contra `DERIVED`.
7. **La tabla de enrutado** con su coste medio y exactitud media.
8. **El retraso de detección de deriva**, medido con deriva sintética.
9. **Dos entidades** implementadas, una con verdad derivada y otra sin ella. **No opcional.**
10. **El pipeline de referencia ejecutado por alguien que no seas tú.**
11. CI verde, `LIMITS.md`, `RESULTS.md`, tres releases etiquetados, dataset publicado respetando licencias.

---

## 19. Riesgos

| Riesgo | Qué se hace |
|---|---|
| El XML del BOE es tan bueno que el benchmark satura | Se publica el estrato duro como titular y la distribución de dificultad desde el primer informe |
| Una entidad cambia su portal y el adaptador se rompe | El contrato tiene su suite; el manifiesto con hashes permite reproducir campañas viejas aunque la fuente desaparezca |
| Alguien publica antes un benchmark documental en español | Poco probable en cuatro meses. Si pasa, el diferencial pasa a ser el nivel 2, el glosario y la deriva, que es lo que nadie está haciendo |
| El presupuesto se va en los VLM | `--dry-run` obligatorio, VLM solo sobre submuestra estratificada, nivel 2 con 5 extractores y no 8 |
| Dudas legales al publicar | La licencia es código y hay un test. Las cuatro fuentes prohibidas están descartadas por escrito con la fecha en que se leyó su aviso |
| Un documento con categorías especiales entra sin querer | El adaptador lo declara y el registro lo rechaza. Hay un test con adaptador falso |
| El proyecto es grande y no cabe entero antes de diciembre | Tres releases, y el `v0.1.0` son 112 a 144 horas. Cada uno es publicable solo |

---

## 20. Cómo se cuenta en una entrevista

1. *"No existe ningún banco DEDICADO al español. El que más tiene son 176 tablas dentro de un multilingüe de 1.820, y su verdad es anotada a mano, así que no crece. OmniDocBench tiene 981 páginas y cero en español; MORE tiene 1.288 repartidas entre 149 idiomas y **cero tablas** en español. Verificado con criterio escrito el 25 de agosto de 2026; la lista y cómo se buscó están en §1.2."*

   > **Aquí ponía «lo comprobé uno por uno», en primera persona y sin fecha.** La comprobación del 19 de agosto tenía un hueco —se le escapó PulseBench-Tab— y no dejó escrito qué se buscó ni dónde, así que nadie podía repetirla. **La frase se queda sólo porque ahora hay un criterio detrás y una fecha de corte**; sin eso se habría retirado.
2. *"El BOE publica el mismo documento como PDF firmado y como XML con marcado de tabla real, así que la verdad de referencia sale gratis y a escala. Eso me deja gastar todo el esfuerzo en la capa que importa."*
3. *"Y la capa que importa no es cuánto acierta el parser, es cuántas respuestas finales pierdes al elegir mal. Por eso hay un extractor `oracle` que devuelve la verdad y marca el techo del pipeline: sin ese brazo de control, mi titular mezclaría el error del extractor con el del resto de la tubería."*
4. *"El motor no sabe qué es el BOE. Una diputación o vuestra empresa entran implementando siete métodos. Y si vuestros documentos no pueden salir de vuestra red, el adaptador lo declara y el motor se niega a llamar a ningún modelo por API: no es una advertencia en el README, la campaña no arranca."*
5. *"Vuestro pipeline actual entra como un concursante más y aparece en la tabla al lado de los ocho de referencia, con el mismo corpus y el mismo intervalo. Incluida la marca de no aplicable si su formato no expresa celdas combinadas. Sin trato especial."*

La cuarta y la quinta son las que convierten un proyecto de portfolio en una propuesta de trabajo.

---

## 21. El manifiesto de evidencia, y por qué esto son dos capas de una plataforma

La mejora estratégica más importante de la revisión externa, y la única que **no cuesta
casi nada** porque son datos que los dos proyectos ya recogen.

### La narrativa que une los dos repos

```
Documentos y trazas reales
        │
        ├─ docbench-es  ·  mide la ENTRADA: ¿qué extractor, con qué error, a qué coste?
        │
   agente o pipeline
        │
        ├─ gonogo  ·  valida el INSTRUMENTO: ¿el juez que dice que mejoró, lee?
        │
   decisión de despliegue firmada
        │
        └─ vigilancia y revalidación continua
```

> **Una plataforma independiente que valida toda la cadena de medición de un sistema de
> IA: los datos que entran, el sistema que actúa, el juez que lo evalúa y la decisión de
> desplegar.**

Eso no es marketing: es lo que sale de que los dos proyectos compartan el mismo
manifiesto y el mismo `benchcore`. Y **es lo que convierte dos repos sueltos en una
tesis**, que es lo que quieres que vea alguien que abre tu perfil.

### El manifiesto, idéntico en los dos

```yaml
evidence_manifest: reliability/1.0
produced_by: docbench@0.3.0
produced_at: 2026-11-14T09:22:00Z

input:
  corpus_or_source: <id>
  n_units: 460
  content_sha256: <hash del manifiesto de contenido>
  license: <declaración>
  privacy: <declaración>

tool:
  id: <extractor o juez>
  version: <exacta>
  image_digest: <sha256 de la imagen OCI, si aplica>
  config_sha256: <hash de la configuración completa>

environment:
  runtime: python 3.12.7
  hardware: x86_64 · 8 vCPU · sin GPU
  execution_backend: docker
  price_table: 2026-08
  fx_rate: 0.92

metrics:
  # `unit_of_analysis` es OBLIGATORIO: en docbench-es es `documento`; en gonogo es
  # `item` (parte del juez) o `ejecucion` (parte economica).
  - { name: <métrica>, value: 0.914, ci: [0.906, 0.922], n: 460,
      unit_of_analysis: documento, bootstrap: BCa, resamples: 10000 }

judge:                              # solo en gonogo, o cuando docbench use juez
  passport: <ruta o hash del pasaporte>
  verdict: APTO_CON_RESERVAS        # los tres valores son APTO / APTO_CON_RESERVAS / NO_APTO
  issued_at: 2026-11-02
  expires_at: 2026-12-02            # POSTERIOR a produced_at, o la decisión no vale

economics:
  cost_eur: 0.87
  cost_estimated: false
  latency_p50_ms: 1300

# `limitations` es OBLIGATORIO en el esquema: un manifiesto sin ese campo no valida.
limitations:
  - "estrato empresarial sintético: techo optimista"
  - "cobertura evaluable 0,71 para este extractor"

decision:
  # docbench-es emite RECOMENDACION; gonogo emite los tres veredictos de su ADR-0010.
  # El esquema admite los cuatro y cada proyecto declara cuáles produce.
  verdict: <RECOMENDACION | PROMOCIONA | NO_PROMOCIONA | NO_SE_PUEDE_DECIDIR>
  rationale: <una frase>

reproduce:
  command: "docbench replay runs/2026-11-14T09-22Z/"
  substance_hash: 7f2a91c4bb08
  requires_credentials: false
```

### Las tres propiedades que lo hacen valioso

1. **`limitations` es un campo obligatorio del esquema.** Un manifiesto sin
   limitaciones declaradas **no valida**. Es la única forma de que la honestidad no
   dependa de que alguien se acuerde.
2. **`reproduce.requires_credentials: false`.** Gracias al proveedor `recorded` y a los
   corpus congelados, un tercero verifica el resultado **sin credenciales y sin gastar**.
   Esa es la definición práctica de reproducible, y casi nadie la implementa.
3. **`unit_of_analysis` va dentro de cada métrica.** Documento en `docbench-es`, ítem o
   ejecución en `gonogo`. Es el campo que impide comparar dos números que se
   remuestrearon sobre unidades distintas, que es el error silencioso más común.

### La demostración conjunta, que es lo que se enseña en una entrevista

Diez pasos, todos reproducibles, todos con manifiesto:

1. Cargas 100 documentos reales.
2. `docbench` compara los extractores y mide el error de su propia verdad de referencia.
3. Emite `routing.yaml` con la mejor arquitectura por tipo de documento.
4. Un agente responde tareas sobre esos documentos con esa configuración.
5. `gonogo` compila ataques a partir de la rúbrica del juez y lo audita **sin etiquetas**.
6. Detecta que el juez puntúa por encima una respuesta larga y falsa que una corta y
   correcta.
7. Diagnostica la causa en la rúbrica y propone una variante, **sin estimar el impacto**.
8. Mides la variante en modo sombra y emites un pasaporte nuevo.
9. Calculas el coste por tarea resuelta con el juez ya validado.
10. Emites un acta de decisión firmada, con su manifiesto y su comando de reproducción.

**Ninguno de esos diez pasos necesita adopción externa ni un cliente.** Se pueden hacer
solo, con documentos públicos, en local, y grabarlo en un vídeo de cuatro minutos.

### Y lo honesto sobre el 10/10

La revisión externa decía que el 10 exige tres equipos externos usándolo, una
integración real y un benchmark reproducido por un tercero. **Tiene razón, y ese no es
tu objetivo.**

Eso no se consigue antes de diciembre, y perseguirlo te llevaría a optimizar para
estrellas en vez de para entrevistas. **El requisito es un artefacto medido,
reproducible y publicado**, y eso sí cabe. La adopción externa, si llega, es un premio.
