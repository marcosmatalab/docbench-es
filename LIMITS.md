# LIMITS · lo que docbench-es NO mide

> **Por qué existe este fichero.** Este proyecto vende rigor, y el rigor se nota
> más en lo que uno se niega a afirmar que en lo que afirma. Aquí va todo lo que
> queda fuera del alcance de una medición, y dónde se rompe cada supuesto.
>
> **Se escribe conforme se descubre.** Un límite que aparece construyendo se
> apunta el mismo día, no al final. Los números están en [`RESULTS.md`](RESULTS.md).

## Verdad de referencia

1. **La verdad `DERIVED` es transcripción, no lectura del PDF.** El XML oficial
   puede diferir en maquetación del PDF firmado. Se mide y se publica la tasa de
   discordancia del emparejado.
2. **Un solo anotador en `ANNOTATED`.** Se publica acuerdo **intra**-anotador,
   nunca inter. No es lo mismo y no se presenta como si lo fuera.
3. **`CONSENSUS` hereda los errores comunes** de los extractores que lo forman.
   Por eso existe la calibración cruzada y por eso esos resultados llevan barra
   de error.
19. 🕓 **L8b · La verdad derivada NO es perfecta, y su error todavía NO está
    medido.** A 21 de agosto de 2026 esto sigue siendo una advertencia, no un
    número: no hay verdad derivada (llega en L4) ni auditoría contra la que
    contrastarla (L8b). Cuando L8b cierre, se publicará su coincidencia con la
    auditoría humana y **todos** los resultados heredarán esa barra. Hasta
    entonces, cualquiera que use este repo debe asumir que el error de la verdad
    de referencia es **desconocido**.
20. 🕓 **L8b · La auditoría humana será de un solo anotador** salvo que se diga lo
    contrario, y se publicará acuerdo intra-anotador **con esas palabras**.
    Tampoco existe hoy.

## Corpus

4. **Sesgo de corpus.** El BOE son documentos bien maquetados y firmados, mejores
   que la media de una empresa. **Los números del BOE son un techo optimista para
   cualquier otra entidad**, y se dice en la primera línea del informe.
5. **El estrato duro está sobremuestreado.** Se publican las dos cifras: la del
   estrato y la ponderada a la distribución real.
9. **Riesgo de saturación.** Si el corpus resulta fácil, **eso es el resultado y
   se publica**, con el estrato duro como titular.
21. **El estrato empresarial es sintético.** Lo sintético es más limpio que lo
    real, así que sus números son otro techo optimista: marcado y no mezclado.
22. **Los estratos de lenguas cooficiales están vacíos.** Declarados y sin
    corpus. El proyecto no cubre catalán, gallego ni euskera, y decirlo así vale
    más que insinuar que sí.
8. **Cobertura de idioma:** castellano. Los demás solo si un adaptador los
   aporta, y no se extrapola.
14. **Datos personales.** Todos los corpus los contienen. Los de categorías
    especiales quedan fuera **por diseño**. Publicidad legal previa no equivale a
    ausencia de datos personales.
13. **Este corpus NO sirve como corpus de `gonogo` nivel 2.** Sus verdades son
    automáticas, de máquina o de anotador único; `gonogo` exige etiquetas humanas
    por anotador con anotación múltiple.

## Preguntas y métricas

6. **Las preguntas por plantilla heredan el sesgo de la plantilla.** Son fáciles
   de forma sistemática. Las trampas se escriben a mano y se cuentan aparte.
7. **El sistema de respuesta está clavado y no optimizado.** Los resultados dicen
   qué extractor es mejor **con ese sistema**, no cuál es mejor en el mejor
   sistema posible para cada uno.
11. **Extractores que no expresan celdas combinadas salen `NO_APLICABLE`, no
    cero**, y su nota va siempre con su cobertura evaluable. No se comparan notas
    calculadas sobre subconjuntos distintos sin decirlo.
17. **La ganancia del glosario se mide sobre las preguntas de este banco** y es
    específica de la entidad. No se extrapola.

## Diseño estadístico

10. **La primera campaña es de precisión, no de contraste.** Con el presupuesto
    declarado no hay potencia para separar extractores parecidos. Se publica el
    **efecto mínimo detectable**.

## Operación

12. **En `--offline` faltan los VLM frontier.** El informe lleva cabecera
    diciéndolo.
15. **La deriva de acuerdo detecta cambio, no empeoramiento.** Es un aviso para
    ir a mirar.
16. **El pipeline de referencia no está optimizado, y lo dice en su cabecera.**
    Quien lo lleve a producción tendrá que ajustarlo, y los números **no se
    transfieren** a su versión ajustada.
18. **La redacción de PII es de patrones, no de comprensión.** Caza NIF, IBAN,
    correos, teléfonos y nombres del glosario. No lo caza todo.
23. **`toolwatch` detecta cambio entre versiones sobre el corpus congelado**, que
    puede no parecerse al corpus de un cliente. La decisión de migrar es del
    cliente; el informe le da los números por estrato, no la decisión.
24. **Una mejora global puede esconder una regresión en un estrato.** Por eso el
    desglose por estrato no es opcional en ningún informe de deriva.

---

## Límites descubiertos construyendo

Los de arriba salen de §17 del manual y son de diseño. Los de aquí han aparecido
picando, y cada uno lleva la fecha y el hito en que se descubrió.

### L0 · 21 de agosto de 2026

25. **`full` y `nightly` no se ejecutan hasta L7.** Los dos trabajos nacen con
    `on: workflow_dispatch:` únicamente, porque `full = fast + quickstart` y
    `quickstart` necesita CLI (L5+), extractores (L5) y los 20 documentos
    congelados (L7). Consecuencia real, no cosmética: **hasta L7 no hay cobertura
    de CI del contrato de entidad, del contrato de extractor, de los tres
    adaptadores hostiles, de la fuga de credenciales ni de la degradación.** Se
    corren a mano o no se corren. El motivo de nacer dormidos en vez de rojos es
    que un rojo permanente durante ~90 horas enseña a ignorar el color.
26. **La única cobertura automática hoy es la puerta rápida.** 15 tests
    unitarios sobre el modelo de datos y los errores, dos de ellos
    property-based. Nada de lo que este repo
    promete medir está medido todavía: ver la cabecera de `RESULTS.md`.
27. **La protección de los ficheros congelados no es hermética: es prevención
    parcial más detección.** `guard-frozen.sh` es `PreToolUse` con matcher
    `Write|Edit|NotebookEdit`, así que **no ve** un `cat >`, un `sed -i`, un `mv`,
    un `rm` ni un `uv run python -c`. Esa vía la caza `stop-gate.sh` al cerrar el
    turno, por dos caminos: `git diff --diff-filter=MDRT HEAD` para lo que ya está
    en `HEAD`, y un manifiesto de huellas SHA-256 para el fixture recién creado
    que todavía no lo está. Verificado el 21 ago 2026 sobre los ocho estados
    (creado, creado+manipulado, `git add`, `AM`, commiteado, commiteado+
    manipulado, borrado, restaurado) y contra `sed -i`, `rm`, redirección y
    escritura desde Python.
    **Lo que sigue sin cubrirse**, y es un agujero real, no teórico: el cambio
    hecho **en el mismo turno en que el hook ve el fichero por primera vez**. La
    primera huella se toma como buena, porque a esas alturas «creado» y
    «creado y ya manipulado» son indistinguibles. Como el manifiesto vive en
    `.claude/`, está en `.gitignore` y es local, un clon nuevo vuelve a
    establecer la línea base desde cero. Tampoco hay nada equivalente en CI.
    Mitigación mientras tanto: los congelados van en el repo, así que un cambio
    commiteado aparece en la revisión del *diff* del hito. El cierre de verdad es
    un test de la puerta que compare los congelados contra un manifiesto de
    hashes **versionado y publicado**, no más hooks; se hace en L2, que es el
    primer hito que trae congelados de verdad.
28. **`full` no corre los ocho extractores: instala seis.** El extra
    `extract-local` son `pymupdf4llm`, `pdfplumber`, `camelot`, `docling`,
    `marker` y `unstructured`. Faltan `grobid`, que es un servicio Java y necesita
    su contenedor, y `tesseract`, que es un binario del sistema y cuyo cliente
    vive en el extra `ocr`. **Se cierra en L5**, que es quien escribe esos ocho
    extractores; hasta entonces el contrato de extractor no puede probarse contra
    los dos que faltan. Descubierto el 21 ago 2026 leyendo `full.yml` contra §8.
29. **El modelo de §6.8 no sabe expresar «un intervalo por métrica» ni el
    desglose por estrato. Se cierra en L5, y tiene precio.** Hoy
    `StructureMetrics` lleva cuatro números —`teds`, `teds_s`, `cell_f1`,
    `evaluable_coverage`— y **un solo** campo `ci`, que no dice de cuál de los
    cuatro es; `AnswerMetrics.by_verifier` publica seis exactitudes sin ningún
    intervalo; y `TedsReport.aggregate` es un agregado publicable sin campo de
    intervalo. Eso choca de frente con la regla de oro 2: *un número sin intervalo
    no se publica*. Además ni `StructureMetrics` ni `AnswerMetrics` tienen
    `by_stratum` ni cifra ponderada, cuando los límites 5 y 24 de este mismo
    fichero prometen que **se publican las dos cifras** y que el desglose por
    estrato *no es opcional en ningún informe*; `GlossaryContribution` sí lo
    tiene, los otros dos no.
    **Por qué no se arregla en L0 y por qué no duele todavía:** en L0 no hay una
    sola **métrica de calidad** medida, que es a lo que la regla 2 le exige
    intervalo; el único número publicado es un tiempo de puerta, que no es una
    estimación estadística y va con su rango observado. El primero que rellena
    `StructureMetrics` de verdad es **L5**, y ahí deja de ser teórico.
    **Lo que cuesta cerrarlo, para que no sea deuda escondida:** un `ci` por
    estimador —`ci_teds`, `ci_teds_s`, `ci_cell_f1`— o pasar a
    `ci: Mapping[str, tuple[float, float]]`; añadir `by_stratum` y la cifra
    ponderada a `StructureMetrics` y a `AnswerMetrics`; y como esto **se desvía
    de §6.8 del manual**, su ADR con la alternativa descartada, igual que el
    0013 hizo con `types` como paquete. Estimado: 2-3 horas dentro de L5, más el
    ADR.

### L1 · 22 de agosto de 2026

30. **`from_html` SÍ produce solapes, y el 100% de detección se mide sobre el
    censo mutado igualmente.** *(Corregido en el escrutinio de L1: este límite
    afirmaba lo contrario, y era falso.)* El colocador sigue el estándar —la celda
    va al primer hueco libre de su PRIMERA columna, y si alguna de las siguientes
    está ocupada es *table model error* y se pisan—, así que un HTML con ese error
    produce una `CanonicalTable` con `SOLAPE`, que es **fatal**. Dos consecuencias:
    **(a)** el censo sigue siendo el instrumento del número publicado, porque el
    solape que sale de HTML real es una sola forma y el censo cubre trece;
    **(b) en L4, `truth.derived` puede emitir una tabla FATAL desde el XML del
    BOE** y ese documento se quedaría sin verdad de referencia. Cuántos documentos
    del corpus tienen ese error **no está medido**, y hay que medirlo en L3 o L4
    antes de que decida por su cuenta qué entra en la verdad.
31. **La partición de línea no se deshace, y eso penaliza al extractor que
    conserva el salto.** `presu-\npuesto` es indistinguible de
    `económico-financiero`, así que R4 de `docs/metrics.md` deja el guion. Como
    N3 mapea el salto a espacio, la celda queda `presu- puesto`: el que **une** la
    palabra sale premiado frente al que **conserva** el salto de línea del PDF. La
    asimetría es real, va en una sola dirección y no está cuantificada. Medirla
    exige verdad de referencia con palabras partidas: L4.
32. **El `page_span` de los cinco conversores no está medido: lo pone quien
    llama.** Ninguno de los cinco formatos —HTML, Markdown, DataFrame, TEI,
    texto— lleva número de página, así que `page_span` es un parámetro con
    `(1,1)` por defecto. Hasta que L5 lo cablee desde el extractor, **cualquier
    número que dependa de `page_span` es el que le pasaron, no uno medido**, y el
    estrato `multipagina` —que el sondeo ya declaró no medido— sigue sin poderse
    calcular desde la forma canónica.
33. **La celda que sólo contiene `<img>` castiga al extractor que acierta, y hoy
    no se puede marcar.** El sondeo contó 489 `<img>`, pero **sobre el documento
    completo y no dentro de `<table>`**: sólo 21 están en documentos que tienen
    alguna tabla, y cuántos caen dentro de una celda **no está medido**. La
    decisión de L1 es que una imagen no aporta texto —ni su `alt`—, coherente con
    ADR-0016. Consecuencia: si la verdad dice `""` para esa celda, un extractor
    que **OCR-ee correctamente** su contenido produce texto donde la verdad dice
    vacío y **se le penaliza por acertar**. Es la misma forma que la regla de oro
    4: no es un fallo del extractor, es una **celda que no se puede evaluar contra
    esta verdad**, y debería salir marcada en vez de quedarse silenciosamente
    vacía. **Se cierra en L4**, que es donde vive la verdad derivada; `CanonicalTable`
    no tiene hoy dónde marcarlo, y el marcador correcto es de la verdad, no de la
    forma canónica.
34. **`from_markdown` no implementa el escapado de `\|` de GFM.** Una celda cuyo
    texto contenga una barra vertical escapada se parte en dos. En el corpus del
    BOE el Markdown no es formato de origen sino salida de extractor
    (pymupdf4llm, marker), así que el riesgo es que un extractor emita una barra
    dentro de una celda y salga penalizado por una limitación del conversor. No
    medido. Se cierra cuando L5 tenga salida real de esos dos extractores contra
    la que comprobarlo.
35. **REQUISITO DE L5, no recordatorio: la nota de un extractor sin spans no se
    puede publicar sin su cobertura evaluable al lado.** `from_dataframe` fija
    `expresses_spans=False`, así que camelot sale `NO_APLICABLE` en toda tabla
    con celdas combinadas, y lo mismo los extractores de Markdown (pymupdf4llm,
    marker) y de texto (tesseract). La regla de oro 4 dice que *«su nota va
    siempre con su cobertura evaluable»*. Una nota calculada sobre un subconjunto
    del corpus, presentada como si fuera del total, es exactamente el titular
    falso que este proyecto existe para no publicar. **El informe de L5 no puede
    poder enseñar una sin la otra**: no es una convención de redacción, es una
    condición sobre el objeto que emite el informe, y su test va en L5.
36. **Qué fracción de las TABLAS trae celdas combinadas no está medido, y por eso
    la cobertura evaluable de camelot no lleva número.** El sondeo midió
    documentos, no tablas: *«de los documentos con `<table>`, el 63% [50–74]
    traen span > 1»*, con **n=57 documentos**. En 200 documentos hay 283 tablas,
    así que el denominador de tablas existe pero nunca se contó. Una versión
    anterior de este fichero derivaba de ahí que *«la cobertura evaluable de
    camelot ronda el 37%»*: eso era una resta sobre otra población y encima
    publicada sin intervalo. **Retirado.** Se mide en L5, que es quien tiene las
    tablas una a una, o antes con un sondeo que cuente por tabla.
37. **`from_dataframe` no puede distinguir un `RangeIndex` de camelot de unas
    cabeceras numéricas de verdad más allá del tipo.** Si `columns` son los
    enteros `0, 1, 2…` se declara que **no hay cabecera**, porque emitirlos
    inventaría una fila de contenido en cada tabla de camelot —uno de los cuatro
    extractores de `make quickstart`—. Si fueran las cadenas `"0"`, `"1"`, sí se
    conservan. La regla es de tipo y no de texto, y un extractor que convirtiera
    sus cabeceras a entero perdería la fila de cabecera sin avisar. No medido: en
    L5, con salida real de camelot.
38. **El coste de `validate` y `holes` es proporcional al ÁREA de la rejilla, no
    al tamaño de la entrada.** Un HTML de 30 KB con mil `<td colspan="1000">`
    declara un millón de columnas y cuesta el millón. El caso desproporcionado
    —60 bytes que costaban 28 s y 7,5 GB, con `rowspan="65534" colspan="1000"`—
    está cerrado recortando a la tabla, pero la proporcionalidad con el área se
    mantiene y **no hay tope declarado**. Los adaptadores hostiles de L8 son el
    sitio donde esto se prueba a propósito.

### L2 · 22 de agosto de 2026

39. **Los TEDS de este proyecto NO son directamente comparables con los TEDS
    publicados en la literatura sobre PubTabNet.** El golden se calcula sobre el
    render canónico de las tablas y no sobre el HTML crudo (ADR-0020), porque la
    implementación de referencia no normaliza nada y cuenta en el denominador el
    marcado inline dentro de las celdas, que `CanonicalTable` no guarda. Medido
    sobre sus 20 casos: **15 de 20 dan un número distinto**, media +0,0092,
    rango [−0,0342, +0,2070]. Un paper que diga «TEDS 0,94 en PubTabNet» **no se
    puede poner al lado** de un número de aquí sin decir esto. Es un límite
    serio: la comparabilidad externa era una de las cosas que daba usar TEDS.
40. **De esos 15 casos, la parte atribuible a NORMALIZAR no está separada de la
    atribuible a la FORMA del árbol.** Se sabe que en **10 de los 15** la
    normalización no cambia ni un texto de celda, o sea que ésos son forma pura;
    en los otros 5 las dos causas van mezcladas y no se han descompuesto.
    Separarlas exigiría un conversor que devolviera el texto sin normalizar, que
    hoy no existe y que no se construye sólo para esto.
41. **`is_header` sobrevive de forma parcial al árbol de TEDS.** Sólo el
    **prefijo máximo** de filas de cabecera va a `<thead>` (ADR-0021): una fila
    de cabecera en mitad de la tabla acaba en `<tbody>` y su condición se pierde
    para la métrica. En el BOE las cabeceras van arriba, pero **cuántas tablas
    tienen cabeceras intercaladas no está medido**. Se mide en L3, que es quien
    trae el corpus.
42. **La distancia de edición es Zhang-Shasha, y su coste ESTÁ MEDIDO: no es
    inmediato.** `uv run python scripts/coste_teds.py`, mediana de 3, tablas sin
    spans:

    | Tabla | Celdas | Un `teds()` |
    |---|---|---|
    | 10×5 | 50 | 9 ms |
    | 20×8 | 160 | 101 ms |
    | 40×8 | 320 | 447 ms |
    | 60×10 | 600 | **1617 ms** |
    | 80×10 | 800 | **2979 ms** |
    | 100×10 | 1000 | **4712 ms** |

    **Este límite decía «para una tabla de documento es inmediato» y que el coste
    sólo se dispara con «miles de filas». Las dos cosas eran falsas y ninguna
    estaba medida.** A 100 filas —que no es hipotético: el sondeo del BOE midió
    `rowspan` de hasta 33— un solo par cuesta **4,7 s**, y el crecimiento es
    ~×2 cada 20 filas, o sea cuadrático en celdas como manda O(|a|·|b|·h²).

    **La consecuencia es de L5, y hay que decidirla allí con este número
    delante:** ocho extractores × miles de tablas a segundos por par no cabe en
    ningún presupuesto. Las salidas son tres, y ninguna es gratis: **tope de
    tamaño declarado** —y entonces las tablas grandes salen `NO_APLICABLE`, no
    cero—, **APTED** como la referencia, que es asintóticamente mejor pero mete
    una dependencia en el núcleo, o **paralelizar**, que no cambia el coste por
    par. **Lo que no vale es descubrirlo en L5 con la campaña corriendo.**

    Lo que sigue sin haber: **tope declarado y test de carga**. El caso hostil es
    de L8.
43. **`teds_batch` decide `NO_APLICABLE` mirando SÓLO si la verdad trae celdas
    combinadas y el extractor declara no expresarlas.** Es la regla de ADR-0006 y
    cubre el caso que importa, pero no cubre otros: un extractor que expresa
    spans y aun así no puede con una tabla multipágina se puntúa igual, con un
    cero que mide su formato y no su calidad. El resto de causas de
    `NO_APLICABLE` se descubren en L5, con extractores de verdad.
44. **TEDS puede salir NEGATIVO, y este proyecto no lo recorta.** La distancia se
    calcula sobre los árboles con su raíz y el denominador cuenta sólo los
    descendientes, así que entre dos tablas suficientemente distintas la
    distancia se pasa del denominador. Medido, y **la implementación de
    referencia devuelve exactamente lo mismo**: −0,142857 sobre el par congelado
    en `casos_limite.json`. La cota real es [−1, 1], no [0, 1]. Lo encontró
    `hypothesis`, no la revisión. **Consecuencia para L5:** §12 publica TEDS como
    nota y una nota negativa no se pondera igual que una entre 0 y 1; L5 tiene
    que decidir si se recorta a cero **al publicar** y decirlo en el informe.
    Recortarlo dentro de `core.teds` sería apartarse de la referencia en
    silencio, así que no se hace aquí.
45. **`from_html` no marcaba como cabecera un `<td>` dentro de `<thead>`, y eso
    era un fallo de L1 que L2 destapó.** PubTabNet escribe **todas** sus
    cabeceras así, o sea que `is_header` salía `False` en el 100% de las
    cabeceras de ese corpus. Arreglado en L2. En el BOE el efecto es menor
    —usa `<th>` 2.659 veces contra 596 `<thead>`—.

    **MEDIDO en L3, y la respuesta es CERO.** `docs/censo-boe-50.json`, 50
    documentos de las secciones I+III, `uv run python scripts/censo_boe_50.py`:

    | | |
    |---|---|
    | `<thead>` en el corpus | 68 |
    | `<th>` totales | 323 |
    | `is_header=True` que emite `from_html` | 323 |
    | **`<td>` dentro de `<thead>`** | **0** — las que viajaban sin marcar |
    | documentos con al menos uno | **0 / 50** [0,0–7,1]% |

    **Comparado por CONJUNTOS y no por totales**, que es lo que hace la afirmación
    válida: «323 = 323» sola no demuestra que sean las mismas celdas — un `<th>`
    sin marcar más un `<td>` dentro de `<thead>` marcado darían el mismo total.
    Medidos por separado, **los dos sumandos son 0**, así que la igualdad no
    escondía una compensación. (Hay 4 `<th>` **fuera** de `<thead>`, que se marcan
    igual antes y después del arreglo.)

    **Conclusión: el fallo que L2 destapó, donde afectaba al 100% de las cabeceras
    de PubTabNet, en el BOE no habría aparecido nunca.** El BOE escribe sus
    cabeceras con `<th>`, no con `<td>` dentro de `<thead>`. n=50; se re-mide sobre
    el corpus completo cuando exista.

### L2 · cierre · 23 de agosto de 2026

46. **REQUISITO DE L5: el suelo del TEDS negativo es de PRESENTACIÓN, y se
    publican LAS DOS CIFRAS.** TEDS puede salir negativo —medido, −0,142857, y la
    referencia devuelve lo mismo— y `core.teds` **no lo recorta nunca**. Quien
    publique:
    1. aplica `para_publicar()` **a los valores por documento Y al agregado**
       —mezclar escalas en la misma tabla es peor que cualquiera de las dos—;
    2. **publica también el agregado CRUDO, sin recortar, en su propia columna**.
       Recortar a 0 antes de agregar **sesga la media hacia arriba**, y decir
       cuántos se recortaron no basta para deshacer el sesgo: obliga al lector a
       fiarse del criterio. Con las dos columnas al lado, la objeción desaparece
       en vez de quedar contestada. Cuesta una columna;
    3. y dice **cuántos se recortaron**.

    Los valores crudos siguen además en el artefacto de la campaña. Ver
    [ADR-0023](docs/adr/0023-teds-negativo-suelo-al-publicar.md).
47. **`teds` declara una PRECONDICIÓN que no comprueba, y de ahí sale el
    requisito de L5.** *(Reescrito: la primera versión de este límite decía «L5
    valida antes de puntuar», que dejaba una suposición sobre un módulo de L2 en
    manos de un hito futuro — justo lo contrario del patrón que este proyecto
    acaba de escribir: **el módulo declara, el consumidor comprueba**.)*

    **Lo declarado**, en el docstring de `teds` y no en un comentario: asume que
    las dos tablas pasan `validate()` sin hallazgos fatales. **Lo que no
    comprueba**: nada de eso. Si la precondición no se cumple, devuelve un número
    igualmente y **ese número no es interpretable** — medido, una tabla con
    `SOLAPE` saca **0,75**, que tiene aspecto de nota normal. Hay un test que fija
    el contrato y que **se cae si alguien decide que `teds` valide**, porque eso
    cambiaría la firma de §9.2.

    **El requisito derivado, para L5:** quien puntúa valida antes, y cuenta las
    tablas que no pasan como lo que son —un fallo del extractor— en vez de
    dejarlas entrar en la media con una nota de aspecto normal.
48. **L2 no ha ejercitado casi nada de L1, y L3 tiene que saberlo.** El código de
    `core.teds` y `core.cellmatch` **no llama a ninguna función de
    `core.canonical`**: trabaja sobre `CanonicalTable` directamente. Lo único
    ejercitado de verdad, y sólo desde los tests, es **`from_html`** —sobre 20
    tablas reales de PubTabNet, que es lo que destapó el fallo de `is_header`—.
50. **«Mata SIEMPRE» es una estimación con n = 3, no una categoría.** La tabla de
    asesinos de `RESULTS.md` llama determinista a un test que mata en las 3
    repeticiones. Un test que mata con probabilidad p sale «SIEMPRE» con
    probabilidad p³: **a p = 0,9 eso es el 73% de las veces**. Medido sobre un
    caso real con `--reps 10`, `test_idempotente` mata a `normalizador_agresivo`
    **26 de 30**: p̂ = 0,867 con **Wilson 95% [0,703 – 0,947]**, o sea un
    **66% [35% – 85%]** de falso «determinista» por tanda.

    **Lo que este proyecto NO mide es la tasa de muerte de cada asesino.** Medirla
    con precisión útil costaría decenas de repeticiones por mutante. Lo que se
    hace en su lugar: publicar el n al lado de la tabla, y dejar `--reps` y
    `--solo` en el arnés para afinar un caso concreto cuando la diferencia entre
    las dos columnas no se explique sola.

51. **La suite no está medida por mutación: el arnés cubre 162 de 185 tests.** Los
    **21 mutantes** apuntan a `canonical`, `types.clave`, `teds`, `cellmatch`, el
    árbol de TEDS y el lote. Los **23 tests restantes** —`types_invariantes` (7),
    `ancla` (5), `types` (5), `errors` (3) y `sin_consumidor` (3)— **no tienen
    ningún mutante escrito contra su código**, así que «los 18 mueren» no dice
    nada sobre si esos tests cazarían un bug. Algunos matan mutantes de rebote
    cuando `--tabla` recorre la suite entera, y eso es daño colateral, no
    cobertura diseñada.

52. **El criterio de aceptación de L2 valida la DISTANCIA, no el mapeo
    `CanonicalTable → árbol`.** El golden se generó dando a la referencia el
    render canónico de las mismas tablas (ADR-0020), así que el número congelado
    es `f_ref(T(pred), T(gold))` y el nuestro `f(T(pred), T(gold))`: **`T`
    aparece en los dos lados y se cancela**. Lo que «20 de 20 a cuatro decimales»
    demuestra es que este Zhang-Shasha calcula lo mismo que APTED. No demuestra
    que `T` sea el árbol correcto.

    **Medido, no razonado.** Dos mutantes de `_arbol.py` contra el fixture
    congelado tal cual:

    | Mutante | Qué rompe | Antes | Ahora |
    |---|---|---|---|
    | `arbol_orden_invertido` | el HTML de **los 20** casos | 145 passed | **20 mueren** |
    | `arbol_thead_solo_la_primera` | el HTML de **6** de 20 | 145 passed | **7 mueren** |

    Y peor: regenerando el golden con la referencia real bajo esos mutantes,
    sigue verde. **Un error en `T` presente el día que se generó el golden sería
    invisible para siempre.**

    **Lo que se hizo:** `test_el_render_canonico_es_el_que_genero_el_golden` ata
    `a_html` a los campos `html_canonico_gold`/`html_canonico_pred` que el fixture
    **ya guardaba y nadie miraba**, más un caso a mano de dos filas de cabecera
    —`_estrategias.py` fija `is_header = fila == 0`, así que ninguna propiedad
    puede generar `n_cabecera >= 2`—.

    **Lo que sigue sin estar cubierto, y por eso esto es un límite y no un
    arreglo:** ese test es un **candado de regresión**, no una validación. Ata
    `a_html` a lo que era el día del golden; no demuestra que ese día fuera
    correcto. Validarlo de verdad exige comparar contra el HTML **original** de
    PubTabNet módulo las normalizaciones declaradas, y eso es trabajo de L5, que
    es quien trae extractores reales. Hasta entonces, el mapeo se sostiene sobre
    la revisión humana de ADR-0021 y sobre estos dos mutantes.

53. **La exactitud de celda NO alinea, y §12 dice «tras alinear».** Ver ADR-0025.
    Una tabla desplazada una fila entera saca **0,0** en `cell_accuracy` teniendo
    todas las celdas bien transcritas. La decisión está tomada y razonada, pero el
    número que publica el nivel 1 en L5 hereda ese supuesto: **`cell_accuracy` es
    exactitud POSICIONAL**, y comparar con la literatura que sí alinea no vale.

54. **La comprobación de recuentos sólo caza los FRASEOS PREVISTOS.**
    `tests/unit/test_recuentos.py` compara contra los documentos publicados con
    una tabla de patrones. Un número escrito de una forma que ningún patrón
    reconoce **no se comprueba**, y eso no se puede cerrar del todo porque el
    español no se enumera.

    **Está medido, en las dos direcciones**, con un corpus de 30 frases que alguien
    escribiría en este repo, sacado de un escrutinio adversarial con un agente por
    familia de patrón: `uv run python scripts/cobertura_patrones.py --detalle`.

    | | |
    |---|---|
    | **falsos positivos** — prosa correcta leída como recuento | **0 de 12** |
    | **escapes** — recuento real que ningún patrón ve | **7 de 18** |

    Las dos direcciones no pesan igual, y por eso el criterio es **estrechar el
    patrón ante la duda**: un falso positivo pone rojo un documento que no miente,
    y un candado que da rojos falsos deja de leerse —el argumento del límite 25—;
    un escape deja un hueco, que es lo que este límite declara. Los siete que se
    escapan son formas que ningún documento usa hoy: «el PLAN tiene 21 mutantes»,
    «mueren los 21 mutantes», «21/21», una fila de tabla, «cubre 160 de los 183
    tests», «quedan 23 tests fuera» y «la suite tiene 183 tests en total».

    **Y está medido cómo se llegó ahí**: desincronizando a propósito una cifra en
    cada uno de los cuatro documentos, la primera versión cazó **2 de 4**, la
    segunda 3, y la cuarta hizo falta porque «no cubre la suite entera: 149 de 177»
    no se parecía a nada previsto. La que se publica caza **4 de 4**.

    **Lo que sí está cerrado es la forma peligrosa**: que un patrón deje de casar
    en todas partes y el test siga verde sin comparar nada.
    `test_cada_recuento_lo_caza_algun_patron_en_al_menos_dos_documentos` exige que
    cada recuento aparezca cazado en dos documentos como mínimo.

    **Lo que queda como procedimiento y no como código**: el control negativo a
    mano —desincronizar una cifra por documento y comprobar que se caza— es un
    paso de `/cerrar`. Como todo paso manual, alguien puede saltárselo; ver el
    mismo argumento en ADR-0022 sobre el protocolo de las 40 corridas.

55. **EL GUARDIÁN SINCRONIZA NÚMEROS, NO AFIRMACIONES.** Y esto no se arregla con
    más regex: es la forma del problema, no un hueco de cobertura.

    Una cifra sólo significa algo **dentro de su frase**. El guardián ve el dígito
    y no la oración: cuando obliga a cambiar el dígito y la prosa de alrededor se
    queda vieja, el resultado es **un número correcto en una frase que se
    contradice sola** — y eso es **más difícil de detectar leyendo** que un número
    viejo en una frase coherente, porque el lector comprueba la cifra contra el
    resto del repo, la encuentra bien, y no vuelve sobre el razonamiento.

    **Ocurrió, y lo destapó una auditoría, no el guardián.** `RESULTS.md` decía:

    > «Son **21** mutantes, no 12: el escrutinio y el paso 2 de `/cerrar`
    > añadieron **seis** —los dos del árbol, el del lote, y las tres casillas…—»

    12 + 6 = **18**, no 21. El patrón `[Ss]on {_N} mutantes, no \d+` vio el dígito
    y lo subió de 18 a 21; la enumeración de al lado siguió nombrando seis y
    **nadie la tocó**. En el mismo barrido aparecieron otras dos: «dice que esos
    **18** huecos están tapados», a dos líneas de un «los **21** mutantes mueren»,
    un «bajó de 38 a 23» cuya causa ya sólo nombraba dos de los tres ficheros que
    habían salido de la lista, un «+316 ms» que restaba contra una mediana que el
    propio documento ya había sustituido, y un «la mediana no se movió» que era
    cierto cuando se escribió y dejó de serlo al remedir. **Cinco en un barrido**,
    y ninguna la vio el guardián.

    **Ningún patrón puede cazar esto**: exigiría entender que «añadieron seis» es
    una suma sobre «no 12», o sea leer la frase. Las dos mitigaciones son de
    escritura, no de código:

    1. **Cuando el guardián obligue a cambiar una cifra, se relee la frase entera,
       no sólo el dígito.** Es un paso de `/cerrar`.
    2. **Preferir enumeraciones exhaustivas a sumas y a restas.** Una tabla que
       lista los 21 mutantes por origen se ve incompleta de un vistazo; un
       «12 + 6» o un «bajó de 38 a 23» obliga al lector a una aritmética que no
       puede comprobar, y se queda viejo en silencio. Las tres frases se
       reescribieron así.

    **Este límite no se cierra.** Es el precio de que un guardián automático
    mantenga cifras dentro de prosa escrita a mano.

56. **`from_html` tiene dos defectos reproducidos que el BOE NO dispara: 0 de 50.**
    Los encontró el escrutinio al preparar L3 y los reproduje en árbol limpio:

    | Entrada | Qué sale | Por qué importa |
    |---|---|---|
    | `<td><![CDATA[Importe 1.234]]></td>` | celda `''` | **se traga el texto en silencio** |
    | `<x:table xmlns:x="urn:z">…` | **0 tablas** | el documento pasaría a contarse como `sin-tabla`: **no falla, RECLASIFICA** |

    El segundo es el peligroso: nada se pone rojo, y el estrato es un resultado
    publicado.

    **Medido antes de decidir arreglarlos**, sobre 50 documentos reales de las
    secciones I+III (`uv run python scripts/censo_boe_50.py`, censo versionado en
    `docs/censo-boe-50.json`):

    | | |
    |---|---|
    | XML con **CDATA** | **0 / 50** [0,0–7,1]% |
    | XML con prefijo de namespace **en `<table\|tr\|td\|th>`** | **0 / 50** [0,0–7,1]% |
    | XML con prefijo de namespace en cualquier etiqueta | 4 / 50 — existen, pero **fuera** de las tablas |

    **Así que NO se arreglan**, y eso es una decisión con número detrás, no
    pereza: arreglar un defecto que el corpus no dispara nunca es trabajo sin
    valor medido. **Lo que sí queda es la reproducción exacta de arriba**, para
    que el día que el intervalo se mueva —otra entidad, otra ventana— nadie tenga
    que volver a encontrarlos.

    **Y la condición de reapertura, escrita:** si un censo posterior encuentra
    **uno solo**, se arregla `from_html` **con su mutante en el `PLAN` de
    `matar.py`** antes de bajar un documento más. No después.

57. **El tamaño del corpus de L3 está medido, y el sondeo no lo había mirado.**
    `docs/censo-boe-50.json`, n=50, tamaños tomados del campo `szBytes` que la
    **propia API entrega en el sumario** — o sea sin bajar un solo PDF:

    | | mediana | media | máximo |
    |---|---|---|---|
    | PDF | 216 KB | 255 KB | 1.034 KB |
    | XML | **15 KB** | 29 KB | 380 KB |

    **La primera proyección de esta nota decía «≈ 277 MB» y estaba baja casi a la
    mitad.** Salía de multiplicar la media de los 50 en bruto por 1.000, y **esos
    50 no se parecen al corpus**: tienen **6,1 páginas de media** contra las **8,8**
    de los 600 del sondeo. Proyectar desde una muestra más ligera que la población
    subestima, y aquí subestimaba el doble.

    **Proyección corregida**, en dos pasos y con los dos declarados: **KB por
    página** del censo (n=50) × **distribución de páginas por estrato** del sondeo
    (n=600, tres ventanas):

    | | PDF | XML |
    |---|---|---|
    | por página | 58,3 KB | 3,7 KB |

    | Estrato | % natural | páginas (media) |
    |---|---|---|
    | `sin-tabla` | 67,0% | 5,9 |
    | `celdas-combinadas` | 15,5% | **14,7** |
    | `tabla-simple` | 13,8% | 11,2 |
    | `anexo-png` | 3,7% | **27,9** |

    | Mezcla de 1.000 documentos | Proyección |
    |---|---|
    | **no estratificada** (mezcla natural) | **533 MB** |
    | con `--strata-target celdas-combinadas=120` | **518 MB** |

    **Y el resultado va contra la intuición, por eso se mide:** sobremuestrear
    `celdas-combinadas` **no sube** el total, lo **baja** un poco — porque el
    objetivo de 120 sobre 1.000 es **12%, por debajo del 15,5% natural**. Lo que
    de verdad mueve el tamaño es `anexo-png`, con **27,9 páginas de media**.

    **Nada de esto es una medición.** Es una proyección de dos etapas —una tasa
    sobre n=50 aplicada a una distribución sobre n=600— y se publica con esa
    palabra. Cabe de sobra en cualquier caso, y `data/` ya está en `.gitignore`.
    El tamaño real se publica cuando el corpus exista, y entonces será un recuento.

49. **NO VALIDADOS: cuatro conversores y dos campos, con barrera de código.**
    `from_markdown`, `from_dataframe`, `from_tei` y `from_text_heuristic` están
    escritos y tienen tests propios, pero **nadie los ha usado para producir
    nada**. Lo mismo con los campos `page_span` —que además no está medido,
    límite 32— y `caption`: ninguna métrica los lee.

    **Ninguna cifra publicada puede pasar por ellos**, y no es una nota: lo
    impide `tests/unit/test_sin_consumidor.py` — **pero las dos mitades no tienen
    el mismo alcance, y decir que sí lo tienen era falso**:

    | Qué protege | Qué recorre |
    |---|---|
    | los cuatro **conversores** | `src/` entero y **todos** los `scripts/**.py` |
    | los dos **campos** (`page_span`, `caption`) | **cuatro ficheros**: `core/teds/*.py` y `core/cellmatch.py` |

    O sea que un módulo nuevo que leyera `caption` fuera de esos cuatro ficheros
    **pasaría por delante de la barrera sin ponerla roja**. La frase anterior decía
    que el recorrido de `src/` cubría las dos cosas, y no es cierto. Detectado al
    preparar L3, que es justo el hito que estrena módulos capaces de leerlos.

    **Ensanchar el test de los campos NO es de una línea**, y por eso va como deuda
    con su tamaño y no como arreglo: `core/canonical/_html.py` **escribe** los dos
    campos legítimamente, así que el test tendría que distinguir «los escribe» de
    «una métrica los lee», y eso es análisis de AST sobre el uso, no sobre el
    nombre. Precio estimado **~45 min**, y **no se promete**: lo que se hace ahora
    es no afirmar una cobertura que no existe. Una prohibición que se comprueba
    leyendo es una prohibición que se rompe sin que nadie se entere.

    **Su primer consumidor real es L5**, con los ocho extractores: `pymupdf4llm` y
    `marker` emiten Markdown, `camelot` DataFrames, `grobid` TEI y `tesseract`
    texto plano. Ese día el test se cae y obliga a quitarlos de la lista **a
    mano**, que es el momento exacto en que hay que decidir si ya están validados.
