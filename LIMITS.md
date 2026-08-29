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
    al tamaño de la entrada — y ahora hay TOPE DECLARADO.** Un HTML de 30 KB con
    mil `<td colspan="1000">` declara un millón de columnas y cuesta el millón.

    **Lo que L1 dio por cerrado se cerraba POR ACCIDENTE.** El caso de 60 bytes
    —`rowspan="65534" colspan="1000"`— no costaba nada porque el `rowspan` se
    salía de la tabla, `validate` lo declaraba `SPAN_FUERA_DE_RANGO` **fatal** y
    cortaba antes de recorrer la rejilla. O sea que la cota de coste era **un
    efecto colateral de un hallazgo**, no una decisión.

    **Implementar el estándar lo reabrió, y está medido.** Al terminar los grupos
    de filas (límite 65), esa celda pasa a estar *en rango* y la rejilla se
    materializa:

    | | `n_rows` x `n_cols` | `ok` | tiempo | memoria |
    |---|---|---|---|---|
    | `rowspan=4000 colspan=500` **sin** `<tbody>` | 1x500 | `False` | 0,000 s | 42 MB |
    | igual **con** `<tbody>` | 4000x500 | `True` | **0,507 s** | **287 MB** |

    Extrapolando linealmente a 65.534 x 1.000 = 65,5 M posiciones: **~16 s y ~9 GB
    desde 65 bytes de HTML**.

    **Ahora se cierra a propósito**, con `TOPE_AREA = 1.000.000` y el hallazgo
    fatal `AREA_EXCESIVA`. El número sale del corpus: la tabla más grande de las
    2.135 mide **3.309** posiciones (1103 x 3), o sea **302x de holgura**, y el
    tope queda **65x por debajo** del caso hostil. Coste en el tope, medido:
    **0,212 s y 151 MB**. Con sus dos controles: la tabla más grande del corpus
    pasa, y una que se pase sale fatal **nombrando el área**.

    **No es endurecimiento de seguridad: es la precondición para que la métrica se
    pueda calcular.** En L5 son ocho extractores sobre mil documentos, y un
    extractor es justo lo que produce spans basura. Se declara aquí y no se aplaza
    a los adaptadores hostiles de L8 porque **esta entrada llega por el adaptador
    de entidad, desde una fuente que no controlamos**.

    **Lo que sigue sin tope:** el número de tablas por documento y el número de
    documentos por campaña. El área de UNA tabla está acotada; el total de una
    campaña no.

65. **`n_rows` se CUENTA y `n_cols` se DERIVA, y esa asimetría se queda — medida y
    con la razón de no arreglarla.** El mismo defecto —un span que se sale de la
    tabla— tiene veredictos opuestos según el eje:

    | | qué pasa | `validate` |
    |---|---|---|
    | `colspan` que se sale | `n_cols` **crece** a la extensión | `HUECO_COLA`, **legal** |
    | `rowspan` que se sale | `n_rows` se queda en las `<tr>` vistas | `SPAN_FUERA_DE_RANGO`, **FATAL** |

    Reproducido con las dos formas, y con testigo en el corpus real:
    `BOE-A-2026-7172` t13 lleva un `<td colspan="2">` en una tabla cuyo
    `<colgroup>` declara 2 columnas, y sale legal creciendo a 3.

    **Y se decide NO derivar `n_rows`, con dos razones medidas:**

    1. **Reabre el límite 38**: derivarlo pone la celda desbordada en rango y
       cuesta **~9 GB desde 65 bytes**.
    2. **El estándar no la absuelve.** Su paso final dice *«if there exists a row
       or column in the table containing only slots that do not have a cell
       anchored to them, then this is a table model error»*. Aplicando la regla
       ENTERA, las dos tablas del BOE que disparaban el fatal siguen siendo *table
       model error*: crecen **y además** se condenan. El repo y el estándar
       coinciden en el veredicto y discrepan en la geometría y en el nombre.

    **Medir y decidir que no es un resultado, no una omisión.** Lo que queda es que
    el lado permisivo es el horizontal: el repo perdona por columnas lo que el
    estándar condena, y `COLUMNA_VACIA` no dispara nunca porque está definido sobre
    «posición cubierta» y no sobre «celda anclada». Convertir el paso final del
    estándar en hallazgo cerraría la asimetría **detectando más**, no perdonando
    más. **Precio estimado: ~2 h**, y el sitio natural es L5, que es donde los
    extractores empiezan a producir tablas raras.

67. **`truth.derived` NO genera los `Fact`, y §9.4 dice que sí.** Literal del
    manual: *«`truth` parsea el XML a `CanonicalTable` y **genera los `Fact` con
    plantillas sobre la matriz**»*. L4 entrega `Truth` con sus tablas y
    **`facts=()`**.

    **Se aplaza a L9, y la razón no es la prisa.** Un `Fact` lleva un `path` como
    `"tabla[2].fila[grupo 3].col[salario base].2026"` (§6.4), o sea que hay que
    saber **qué significa cada columna** — y eso sale del vocabulario y las
    plantillas de §9.6, que **son L9**. Generarlos ahora sería decidir el formato
    del `path` sin su consumidor y engordar la lista del límite 49: cosas escritas
    que nadie ha usado para producir nada.

    **Lo que hace que la desviación no sea silenciosa:** `facts` es una tupla
    **vacía**, no un valor inventado, así que quien la lea ve que no hay hechos en
    vez de creerse unos falsos. Y `ask.templates` (§9.6) es el único consumidor, o
    sea que hasta L9 **no hay nadie a quien le falte**.

    **Precio: ~3-4 h**, y va con L9 porque ahí están las plantillas. Si en L9 se
    decide otra cosa, esta entrada sobra y el barrido lo dirá.

66. **La coincidencia con la referencia de PubTabNet vale sobre SUS casos, no sobre
    los nuestros.** A partir del cierre de L3, la regla es:

    - **sobre los 20 casos propios de PubTabNet: coincidencia exacta**, a cuatro
      decimales, y eso es el criterio de aceptación de L2 y no se toca;
    - **sobre casos construidos por nosotros: coincidencia sólo donde los dos
      modelos coincidan**, porque la referencia trabaja sobre el árbol parseado y
      nosotros sobre la rejilla.

    Los **tres hallazgos sobre la métrica** son del mismo tipo y por eso van
    juntos: TEDS no acotado por cero, el `<tbody>` de más que la forma canónica
    borra a propósito, y el derrame de grupo de filas. **Ninguno es un fallo de
    esta implementación**, y ninguno toca los 20 golden.

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

    **MEDIDO en L3, y la respuesta es CERO.** `runs/censos/censo-boe-50.json`, 50
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

51. **La suite no está medida por mutación: el arnés cubre 218 de 692 tests.** Los
    **29 mutantes** apuntan a `canonical`, `types.clave`, `teds`, `cellmatch`, el
    árbol de TEDS, el lote, —desde el paso 2 de L5— **el instrumento que emite la
    tabla** —el emparejado, el recuento de fallos, la cobertura, la intersección, el
    delta y el `n/a`— y **el que emite la portada**, que es la primera pantalla del
    proyecto. Los **474 tests restantes** —`congelados_l4` (38), `extractor_contrato` (37), `canonical_texto_de_celda` (19),
    `barreras` (14), `extractor_arnes` (14), `harvest` (14), `verificar_corpus` (14),
    `aro_del_techo` (13), `extractor_conformidad` (13), `barreras_documentos` (12),
    `boe` (12), `metricas_regimen` (12), `pdfplumber` (12), `documentos_que_sostienen` (11),
    `dos_series` (11),
    `boe_api` (10), `camelot` (10), `diario` (9), `entity_conformance` (9),
    `entity_registry` (9), `guardianes_por_glob` (9), `pymupdf4llm` (9),
    `capas_permitidas` (8), `cli` (8), `manifest` (8), `pairing` (8), `corpus_store` (7),
    `corredor` (7), `docling` (7), `extract_registry` (7), `guardianes_l4` (7),
    `policy` (7), `types_invariantes` (7), `boe_xml` (6), `censo_capa_texto` (6),
    `conjunto` (6), `estimador_computo` (6), `types` (6), `ancla` (5),
    `comparar_verdad` (5), `conjunto_conformidad` (5), `datos_fuera_de_git` (5),
    `lecturas_repetidas` (5), `procedencia` (4), `sellar_xml` (4), `techo_fuente` (4),
    `errors` (3), `reglas_parseables` (3), `sin_consumidor` (3), `formatos_spans` (2),
    `limite_lineas` (2), `tope_area` (2)— **no tienen ningún
    mutante escrito contra su código**, así que «los 29 mueren» no dice nada sobre si
    esos tests cazarían un bug. **Y la fracción sin cubrir crece:**
    12,4% al cerrar L2, **68,0% hoy** — y 68 de los 463 entraron de golpe con
    `congelados_l4` (38), `guardianes_l4` (7), `guardianes_por_glob` (9),
    `documentos_que_sostienen` (11) y `reglas_parseables` (3), que son candados de
    fichero, de proceso, de glob y de sintaxis, no código con mutante posible: sus
    controles negativos viven dentro —se manipula un fixture y se exige que la huella
    deje de cuadrar, se le da al guardián de la re-congelación una huella movida sin
    corrección, y **se rompe el glob de un hook y se exige que el recuento lo
    delate**—.

    **Pero ésta no es la cifra que importa, y publicarla sola era un error.** Mide
    *el arnés*, no la protección: **689 de 692 tests protegidos por algo** —un
    mutante o un control negativo en su propio fichero— y **3 tests sin ningún
    control**. Las dos contabilidades, sus dos puntos y por qué van en direcciones
    distintas están en la deuda 7 de `ESTADO.md`; el criterio y lo que no verifica,
    en el límite 60. Algunos matan mutantes de rebote
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

    **Está medido, en las dos direcciones**, con un corpus de 35 frases que alguien
    escribiría en este repo, sacado de un escrutinio adversarial con un agente por
    familia de patrón: `uv run python scripts/cobertura_patrones.py --detalle`.

    | | |
    |---|---|
    | **falsos positivos** — prosa correcta leída como recuento | **0 de 13** |
    | **escapes** — recuento real que ningún patrón ve | **10 de 22** |

    Y el desglose, sin el cual las tasas de dos fechas no se pueden comparar: **8
    de 19** en el subcorpus anterior a la familia `reglas`, **2 de 3** en la
    familia nueva.

    **El precio de haber estrechado los patrones en `6ebf592` está medido y es
    cero.** `uv run python scripts/cobertura_patrones.py --anchos` revierte los
    nueve y da **4 falsos positivos de 13** y **9 escapes de 19** en ese mismo
    subcorpus, contra 0 y 8 hoy. Estrechar quitó cuatro rojos falsos sin costar
    cobertura.

    Las dos direcciones no pesan igual, y por eso el criterio es **estrechar el
    patrón ante la duda**: un falso positivo pone rojo un documento que no miente,
    y un candado que da rojos falsos deja de leerse —el argumento del límite 25—;
    un escape deja un hueco, que es lo que este límite declara. Los diez que se
    escapan son formas que ningún documento usa hoy: «el PLAN tiene N mutantes»,
    «mueren los N mutantes», «N/N», una fila de tabla, «cubre N de los M tests»,
    «quedan N tests fuera», «la suite tiene N tests en total», «hay N reglas en
    .claude/rules/», «las N reglas se cargan solas» y la que se cobró su pieza:
    **«Son N, y las cuatro casillas…»**, donde el sustantivo vive en el encabezado
    de la sección y no en la frase. Ésa **no la caza ningún juego de patrones**,
    ancho o estrecho: sin adyacencia no hay nada que mirar. Es una sub-familia
    distinta del resto y por eso se nombra aparte.

    **Y este límite dejó de ser teórico: tiene su primer caso REAL, medido.**
    `CLAUDE.md` decía que en `.claude/rules/` había **tres** ficheros, con
    **cuatro en el disco** desde el commit anterior —`entidad-corpus.md` entró con L3 y la frase
    no se tocó—. Ningún patrón hablaba de reglas, así que el guardián no lo vio; y
    **`CLAUDE.md` ni siquiera estaba en la lista de documentos que miraba**, que es
    el peor sitio posible para una cifra falsa: lo lee toda sesión antes que nada.
    Las dos mitades arregladas —el patrón y el documento— y con su control
    negativo en `test_claude_md_declara_cuantas_reglas_hay_de_verdad`, que exige
    que el patrón case en vez de conformarse con que el número cuadre.

    **Y está medido cómo se llegó ahí**: desincronizando a propósito una cifra en
    cada uno de los cuatro documentos, la primera versión cazó **2 de 4**, la
    segunda 3, y la cuarta hizo falta porque «no cubre la suite entera: 149 de 177»
    no se parecía a nada previsto. La que se publica caza **4 de 4**.

    **Lo que sí está cerrado es la forma peligrosa**: que un patrón deje de casar
    en todas partes y el test siga verde sin comparar nada.
    `test_cada_recuento_lo_caza_algun_patron_en_al_menos_dos_documentos` exige que
    cada recuento aparezca cazado en dos documentos como mínimo — salvo el de las
    reglas, que vive **sólo** en `CLAUDE.md` porque escribirlo en un segundo sitio
    crearía justo la copia que todo esto existe para evitar. Ése lleva su propio
    candado, que es más estrecho: exige el fichero concreto.

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
       lista los 22 mutantes por origen se ve incompleta de un vistazo; un
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
    `runs/censos/censo-boe-50.json`):

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
    `runs/censos/censo-boe-50.json`, n=50, tamaños tomados del campo `szBytes` que la
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

58. **La conformidad de entidad NO comprueba que `discover` no descargue.**
    §7.1 lo pide con esas palabras —*«no descarga: se mide el tráfico y debe ser el
    mínimo»*— y **medir tráfico exige red**, que es justo lo que la suite no tiene
    para poder vivir en la puerta (ADR-0032). Lo que sí comprueba es la condición
    observable sin red: que `discover` **sea perezoso**, o sea que no devuelva la
    ventana entera ya materializada.

    **Lo que se escapa:** un adaptador cuyo generador baje cada documento conforme
    va emitiendo su referencia **pasa la suite**. Es perezoso y descarga, y las dos
    cosas a la vez son posibles.

    **Dónde se cierra y a qué precio:** con un contador de tráfico alrededor del
    adaptador real, en `tests/e2e` —que es donde vive lo que necesita red—, con
    `entity.boe` delante. **~1 h**, y va con L3 o con L7. Hasta entonces la
    afirmación que este repo puede sostener es *«`discover` es perezoso»*, no
    *«`discover` no descarga»*, y así está escrita en el módulo.

59. **El barrido de referencias NO recorre `MANUAL.md` ni `HITOS.md`, y se salta
    un tipo de ruta.** `scripts/referencias.py` comprueba 103 referencias en los
    ficheros **operativos** —`pyproject.toml`, `Makefile`, `CLAUDE.md`,
    `ESTADO.md`, los workflows y las skills—. Dos huecos, los dos a propósito:

    - **`MANUAL.md` y `HITOS.md` quedan fuera.** Describen el proyecto terminado:
      su árbol está lleno de módulos que llegan en L5, L13 o L17 y que hoy están
      «rotos» todos. Meterlos daría **cien falsos positivos**, y un informe con
      cien falsos positivos no se lee — el argumento del límite 25.
    - **Una referencia sin extensión sólo se comprueba si su primer segmento
      existe en la raíz.** Sin esa regla, `actions/checkout` de un workflow entra
      como fichero roto. Lo que se paga: un directorio inventado bajo otro que
      tampoco existe se salta en silencio. **Con extensión sí se caza**, que es el
      caso común.

    Y una tercera cosa, que no es hueco sino peaje: **una ruta abreviada cuenta
    como rota**. `entity/base.py` en prosa —cuando el fichero vive en
    `src/docbench_es/entity/base.py`— sale en rojo, porque el barrido no adivina
    desde dónde es relativa. La respuesta por defecto es **escribir la ruta
    entera**, no declararla: es el mismo criterio que con los patrones del
    guardián de recuentos, se corrige la redacción antes que el instrumento.

    Y lo que el barrido no puede ver de ninguna forma: que una referencia apunte a
    un fichero que **existe pero no hace lo que el texto dice**. Comprobar que algo
    existe no es comprobar que la afirmación sobre ello sea cierta.

60. **«Protegido» se verifica por EXISTENCIA, no por fuerza.** La segunda
    contabilidad —449 de 452— cuenta como protegido el test cuyo fichero es suite
    objetivo de un mutante **o** declara un control negativo en
    `CONTROLES_NEGATIVOS`. De esa declaración,
    `test_cada_control_negativo_declarado_existe_de_verdad` comprueba por AST que
    **el test nombrado existe y que el fichero se colecta**. Si alguien lo renombra
    o lo borra, la puerta se pone roja.

    **Lo que ninguna comprobación puede decidir es si ese control es fuerte.** Que
    un test ejercite una entrada mala no demuestra que cazaría un cambio en el
    sujeto: eso lo demuestra un mutante, que es literalmente la definición del
    arnés. Por eso la cobertura del arnés **se sigue publicando al lado como
    submedida** en vez de sustituirse por ésta: la de arriba dice «hay algo», la de
    abajo dice «ese algo se ha probado contra una rotura real».

    Y las dos cuentan **tests** pero miden **ficheros**: un mutante al que mata un
    solo test «protege» en el recuento a los dieciocho de su suite, y un control
    negativo cuenta para todo su fichero. Es la misma unidad que usa el arnés desde
    L1, y por eso las dos series son comparables entre sí — pero ninguna de las dos
    dice «cada test está probado».

61. **`may_send_to_third_party` MEZCLA DOS PREGUNTAS, y el contrato no las
    separa.** El campo es un solo booleano de `benchcore.types.PrivacyDecl`, y
    dentro caben dos cosas distintas:

    | | La pregunta | Quién la contesta |
    |---|---|---|
    | **(a)** | ¿permite **la fuente** que se retransmita el documento? | el organismo, en su licencia |
    | **(b)** | ¿tiene **el operador** base legal para *ese* tratamiento —datos personales a un tercero, quizá fuera de la UE—? | el responsable del tratamiento, y depende de quién y desde dónde |

    Con un solo campo, **un `true` afirma las dos** y un `false` niega las dos. En
    el BOE la (a) es un sí documentado y la (b) no la ha contestado nadie: por eso
    ADR-0037 pone el campo en `false` — el valor restrictivo es el único que no
    afirma lo que no se sabe.

    **Por qué no se arregla partiéndolo en dos**, que es lo correcto: `PrivacyDecl`
    vive en `benchcore`, o sea otro repo y otro contrato, y ampliarlo con un solo
    consumidor es justo lo que ADR-0035 decide no hacer. **Precio estimado: ~1 h**
    —dos campos, la subida del menor de `API_VERSION`, y los dos perfiles— y **no
    se promete**: se declara con su tamaño. El momento natural es L12, cuando la
    pregunta (b) haya que contestarla de verdad.

    Mientras tanto, lo que el repo puede afirmar es *«la fuente lo permite y el
    operador no lo ha evaluado»*, y eso **no cabe en el campo**. Cabe aquí.

62. **El manifiesto pone hash al PDF y NO al XML: la mitad del par no está
    fijada.** `Procedencia.sha256` es el `sha256` del `primary` de §7.1 —el PDF—,
    y el XML viaja en `companions` sin hash propio, así que
    `scripts/verificar_corpus.py` puede comprobar byte a byte el PDF y del XML
    sólo puede decir **que está y que no está vacío**.

    **Qué se escapa exactamente:** un XML sustituido por otro XML válido no
    cambiaría el manifiesto, y el XML es *la verdad de referencia* contra la que
    se puntúa a todos los extractores. O sea que la mitad menos protegida del par
    es la mitad que decide quién gana.

    **LO APLAZADO ES EL ESQUEMA, NO LA CAPTURA.** Son dos cosas distintas y sólo
    una corría prisa:

    | | Qué es | Cuándo | Por qué |
    |---|---|---|---|
    | **Cambiar el esquema** | `Procedencia`, el manifiesto, `corpus.harvest` y la reanudación —que tendría que rellenar el hueco de los 25 del piloto— | **L4, ~40 min** | Toca cuatro sitios y no gana nada por hacerse hoy |
    | **Capturar el hash** | un script que recorre el directorio y escribe `runs/l3/xml_sha256.json` | **HECHO, al terminar la cosecha** | Lo que separa una captura buena de una mala es **el hueco entre la descarga y el hash** |

    Ese hueco es todo el argumento. Tomado al terminar la cosecha son **minutos**,
    sobre ficheros que acababa de escribir el propio código en la propia máquina.
    Tomado en L4 serían **días**, y un hash calculado sobre un fichero ya
    sustituido **lo bendice para siempre**: peor que no tenerlo, porque a partir de
    ahí la comprobación diría que todo cuadra.

    **La captura está hecha y fechada**: `runs/l3/xml_sha256.json`, 1.000 de 1.000,
    `tomado_en 2026-08-24T12:59:52Z`, sello `352a6f2+2` —los dos ficheros sucios
    son el propio script de captura y el `.gitignore`, ninguno toca el corpus—,
    `uv run python scripts/sellar_xml.py runs/l3/manifiesto.json`. Va **versionada**:
    su valor entero está en cuándo se tomó, y fuera de git eso es una afirmación de
    palabra.

    **En L4 ese fichero SE PLIEGA dentro del esquema, no se recalcula.** Si se
    recalcula, el hueco vuelve a ser de días y la captura de hoy no habrá servido
    de nada. Y no es una intención: `sellar_xml.py` **se niega a sobrescribir** una
    captura existente sin un `--refijar RAZON` que queda escrito dentro, con su
    control negativo en `test_sellar_xml.py`.

63. **La cosecha no guarda LA FECHA de un descarte, así que la ventana no se puede
    partir con lo que se guardó.** Los 1.000 aceptados llevan su `fecha_sumario` y
    los 43 descartes viven en un contador sin fecha, `Cosecha.por_causa`. La
    ventana de L3 **se eligió cruzando el equinoccio a propósito** para que la tasa
    no fuera de una sola época — y con lo que el manifiesto guarda, ese propósito
    no se podía cumplir.

    **El número existe igual, reconstruido, y el método se declara entero:**
    `scripts/desglose_ventana.py` vuelve a leer los sumarios con
    `BoeAdapter.discover` —el código de producción, no una copia— y reparte los
    `intentados` por día.

    **EL SUPUESTO, con estas palabras:** *«`BoeAdapter.discover` devuelve HOY los
    mismos ítems que devolvió durante la cosecha»*. No es gratis — **el BOE
    corrige y anula documentos**, y un sumario viejo puede no ser hoy lo que fue.
    Si un ítem se hubiera retirado o reordenado, la reconstrucción repartiría mal
    los descartes y el desglose sería falso sin avisar.

    **Lo que NO sostiene el supuesto, aunque lo parezca:** que los trozos sumen el
    total. `462 + 581 = 1.043`, `444 + 556 = 1.000`, `18 + 25 = 43`. **Las tres son
    identidades aritméticas**: el script parte por fecha dos conjuntos y calcula los
    descartes restando, así que los trozos suman el conjunto **pase lo que pase**.
    Cuadrarían igual con un ítem movido de día, que es exactamente la deriva que
    había que detectar.

    > **Esta entrada afirmaba lo contrario el mismo día en que se escribió**:
    > *«que las tres cuadren a la vez con un origen que hubiera derivado es tan
    > improbable que el cuadre ES la comprobación»*. Es falso, y lo encontró el
    > escrutinio adversarial del cierre. Se corrige en el acto y se anota en vez de
    > borrarse: una afirmación falsa nunca es deuda, y **la evidencia que se cita
    > para respaldar un supuesto es justo donde menos se mira**, porque llega ya
    > envuelta en la conclusión.

    **Lo que sí lo sostiene, y es lo que el script comprueba ahora:** que los
    **1.000 identificadores** aceptados sigan apareciendo entre los que el origen
    entrega hoy —un documento retirado o reordenado deja de estar—, y que **ningún
    día tenga más aceptados que intentados**, que sin comprobarlo daría descartes
    negativos y una tasa negativa sin protestar. Comprobado: **0 ausentes, 0 días
    torcidos**. Si falla, el script **no publica un desglose aproximado**: se cae.

    **Y la fecha de la lectura va dentro del artefacto**, `leido_en` en
    `runs/l3/desglose.json`, porque el supuesto se debilita con el tiempo: pegada a
    la cosecha vale mucho y seis meses después vale poco, y sin la fecha no se
    puede saber cuál de las dos es. Leído el **2026-08-24**, el mismo día que
    terminó la cosecha, y **dos veces con el mismo resultado**.

    Así, «reconstruido» deja de ser una debilidad y pasa a ser un método declarado:
    tiene un supuesto escrito, una comprobación que lo respalda y una fecha que
    dice cuánto vale.

    **El arreglo es el mismo cambio de esquema del límite 62**, así que van juntos:
    L4, **~30 min más**. Mientras tanto, cualquier cosecha futura hereda el hueco.


64. **El barrido de referencias medía LA MÁQUINA, no el repositorio — y su control
    negativo no podía verlo.** `scripts/referencias.py` comprobaba cada ruta con
    `Path.exists()`, o sea contra el árbol de trabajo de quien lo corre. Tres
    referencias existían en la máquina que lo escribió y en ningún clon:
    `.claude/.ultima-puerta` y `.claude/.congelados.sha256`, que crean los hooks al
    correr, y `runs/l3/docs`, que son los 362 MB ignorados. **La puerta estaba
    verde en local y roja en CI**, y se empujó así el commit de cierre de L3.

    **Lo que hace este caso distinto de un bug cualquiera es que la barrera tenía
    su control negativo y era bueno.** Probaba las dos direcciones —dice «no» ante
    una referencia rota, «sí» ante una que existe— y las dos pasaban. Lo que ningún
    control de veredicto puede ver es **de qué depende la respuesta**: una barrera
    con la lógica perfecta puede estar midiendo el disco de su autor.

    **Arreglado, no declarado:** las rutas se comprueban contra `git ls-files`, que
    es lo que recibe un clon; los artefactos de ejecución van en una tabla propia,
    `ARTEFACTOS`, con la **dirección de fallo contraria** —una entrada de ahí que
    aparezca en git también pone rojo—; y el control negativo nuevo inyecta el
    conjunto de lo versionado, así que no depende del disco de nadie.

    **Lo que queda como límite:** el barrido comprueba **rutas** contra git, pero
    los **módulos** siguen comprobándose con `importlib` y las **herramientas**
    mirando `.venv/bin`, o sea contra el entorno instalado. Un módulo que sólo
    exista en el entorno de quien lo corre —instalado a mano, no en `pyproject`—
    pasaría. No ha pasado, y el arreglo es correr el barrido en un entorno limpio,
    que es lo que hace CI. **Se declara en vez de arreglarse porque CI ya lo cubre**
    y duplicar la comprobación en local costaría un `uv sync` por barrido.
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

### L4 · 25 de agosto de 2026

65. **EL «CERO FALLOS DEL CÓDIGO» DE L4 TIENE DOS HUECOS MEDIDOS, Y UNO DE ELLOS
    ES EL BUG REAL DEL DÍA ANTERIOR.** L4 publica *cero discrepancias atribuibles al
    código* sobre 1.213 celdas. Ese cero tiene dos lecturas que desde fuera se leen
    igual —«el código reproduce el PDF» y «estos 30 fixtures no pueden ver un fallo
    del código»— así que se ha medido cuál es, rompiendo el código a propósito y
    contando: `uv run python scripts/mutar_el_instrumento.py`, resultado en
    `runs/l4/mutantes.json`.

    De **22** mutantes: **3 los ve el instrumento** (`roto` 25 de 25, `sin_tablas` 25
    de 25, `sin_spans` 4 de 25), **15 no llegan al sujeto** —TEDS, `cellmatch`,
    claves, recuentos y **los dos del normalizador**, medido con `settrace` sobre la
    derivación—, **1 no es medible fuera de pytest** (`recuentos_todo_vale`, que
    importa `conftest`), **1 es equivalente** (`n3_incompleta`, límite 68) y **2 se
    ejecutan y no los ve nadie**:

    | Mutante | mata | cambia | Por qué no lo ve, medido |
    |---|---|---|---|
    | `seccion_sin_cerrar` | 0 de 25 | 0 de 30 | **0 de 30** tablas tienen un `rowspan` de cabecera que DESBORDE la sección. Ver 66 |
    | `ok` (`comprobar` siempre ok) | 0 | 0 | **0 de 30** documentos tienen una tabla descartada por `FATAL`. Ver 67 |

    **Esta lista se publica corregida dos veces, y las correcciones importan más que
    la lista.** La primera versión contaba 23 mutantes —son 22—, daba
    `normalizador_agresivo` como «visto» y `normalizador_identidad` como «hueco»
    cuando **ninguno de los dos llega al código medido**, y explicaba el cero con una
    causa falsa. Ver 68. Las dos las encontró el escrutinio adversarial del cierre.

    **`mata` y `cambia` no son la misma cifra y hacen falta las dos.** Un fixture que
    ya tiene una discrepancia de frontera **no puede «dejar de coincidir»**, así que
    `mata` no lo puede contar nunca. Pero `cambia` mal medido es peor: comparaba el
    **mensaje formateado**, que lleva dentro el texto de la celda, así que un mutante
    que sólo cambiara el renderizado contaba como detectado sin detectar nada — y eso
    produjo el «cambia 3 de 30» falso de `normalizador_agresivo`. Ahora la identidad
    de una discrepancia es `(clase, posición)` y nunca su texto.

66. **La muestra de L4 es CIEGA al bug del grupo de filas, y está medido: 0 de 30.**
    `seccion_sin_cerrar` reintroduce el fallo que desplazaba los datos una columna
    con `validate` diciendo `ok=True`. Reintroducido, **las 30 `CanonicalTable` salen
    idénticas celda a celda**: no es que el comparador sea ciego —`test_comparar_
    verdad.py` demuestra que detecta una celda movida de columna— es que **ninguno
    de los 30 documentos tiene la forma que lo dispara**. 8 de 30 tienen algún span y
    2 tienen `rowspan>1` en cabecera, pero **0 tienen un `rowspan` de cabecera que
    desborde su sección**, que es la condición exacta.

    Consecuencia dura y hay que decirla así: **el «0 fallos del código» de L4 no dice
    nada sobre esa clase de fallo.** Lo que lo cubre es `tests/unit/test_grupo_de_
    filas.py`, donde el mismo mutante mata **2 de 2**; lo que NO lo cubre es la verdad
    de referencia. Cerrarlo pide un fixture elegido **por forma** y no por estrato, y
    eso cambia el diseño de la muestra: va a L8b, no aquí.

67. **L4 no puede decir nada sobre `validate`: 0 de 30 tablas se descartan.** El
    límite 30 avisaba de que `truth.derived` podía emitir una tabla `FATAL` desde el
    XML del BOE y dejar un documento sin verdad. En esta muestra **no pasa ni una
    vez**, así que la rama de descarte de `derivar` —y el `SIN_VERDAD` del
    comparador— **están sin ejercitar por el instrumento**. El comparador tiene el
    caso escrito, pero ningún dato real lo recorre.

68. **Los tres mutantes del normalizador no prueban nada sobre L4, y la primera
    explicación publicada de por qué era FALSA.** Se publicó que *«la misma función
    normaliza los dos lados, así que una mutación suya se cancela»*, citando el
    límite 52. **No es eso lo que pasa.** `_html.py` hace
    `from ._normalizar import normalize_cell_text`, o sea liga el nombre al importar;
    `normalizador_identidad` y `normalizador_agresivo` parchean
    `canonical.normalize_cell_text`, el atributo del **paquete**. Comprobado
    ejecutándolo: bajo el mutante, `canonical.normalize_cell_text('  a   b  ')`
    devuelve la cadena intacta y `from_html` sigue devolviendo `'a b'`. **Sólo se
    muta el lado del comparador, no el del sujeto.**

    El tercero, `n3_incompleta`, **sí llega** —parchea la constante
    `CATEGORIAS_DE_ESPACIO` del propio módulo, que se lee en cada llamada— pero es un
    **mutante equivalente en la salida**: quita `Zl` y `Zp`, y `normalize_cell_text`
    termina en `" ".join(s.split())`, que los considera espacio igualmente.
    Comprobado sobre las cuatro categorías —Zl, Zp, Zs, Cc—: la salida es idéntica
    con y sin mutante. **Ningún instrumento puede verlo por la salida de esa
    función**, así que llamarlo hueco acusaba al instrumento de no ver algo que no
    está.

    Y la mitad que sí es verdad y se mantiene: **`normalize_cell_text` no cambia ni
    una de las 1.213 celdas**, en ninguno de los dos lados. No hay un NBSP, ni un
    espacio de otra categoría, ni una forma NFD en toda la muestra. Así que aunque un
    mutante del normalizador llegara al sujeto, no habría nada que mover.

69. **El transcriptor humano AUTO-CORRIGE las erratas del original, y va en la
    dirección de penalizar al extractor que acierta. Medido: 1 de 1.213 celdas.** El
    BOE escribe `Catauña` en `BOE-A-2026-6957` —**en el PDF y en el XML, los dos
    formatos oficiales coinciden**— y al transcribir a mano se copió `Cataluña` sin
    darse cuenta. Si esa discrepancia se hubiera adjudicado como defecto del origen,
    habría entrado `Cataluña` en la verdad de referencia y **todo extractor que
    leyera el PDF fielmente habría perdido un punto por acertar**.

    Lo que lo impidió fue mirar el PDF, que es ADR-0039 regla 5. **La tasa es de una
    sola persona, una sola pasada y n = 1**: no es una estimación con intervalo, es
    un recuento sobre esta muestra, y su valor es señalar la dirección del sesgo, no
    cuantificarlo. Toca a la verdad `ANNOTATED` y a **L8b** tanto como a L4: una
    auditoría humana que corrija erratas del original mide su propia pulcritud, no
    la del extractor.

70. **Los 30 fixtures de L4 NO los protegía ninguno de los dos hooks, mientras el
    repo afirmaba «congeladas con hash».** Los globs de `guard-frozen.sh` y
    `stop-gate.sh` eran `tests/fixtures/{pubtabnet,tablas,quickstart}` y
    `*/plan.yaml`; los fixtures viven en `runs/l4/fixtures/`. Además **estaban en
    `.gitignore`**, así que ni siquiera entraban en el repo: «la verdad derivada
    reproduce 25 de 30» sólo lo podía comprobar quien transcribió — el mismo fallo
    que el manifiesto de L3 vino a arreglar, repetido un hito después.

    Arreglado el mismo día en las tres capas: glob en los dos hooks, salida del
    `.gitignore` —**46 KB**, y `entities/boe.yaml` declara `may_redistribute_content:
    true`— y, sobre todo, **el candado de verdad que pedía el límite 27**: un test de
    la puerta, `tests/unit/test_congelados_l4.py`, que compara los 30 contra un
    manifiesto **versionado**. Lo que queda del límite 27 sigue igual: la ventana del
    primer turno.

    **Y la primera versión de ese arreglo era falsa, que es peor que no arreglarlo.**
    El glob de `stop-gate.sh` era `runs/*/fixtures`, que como pathspec de git casa con
    el **directorio** y no con lo que hay dentro: `git ls-files -- 'runs/*/fixtures'`
    devuelve **0** ficheros y `'runs/*/fixtures/*'` devuelve 30. O sea que se publicó
    «arreglado en los dos hooks» con uno de los dos ciego, y las 6 correcciones se
    aplicaron sin que ningún hook las viera —`corregir_fixtures_l4.py` escribe con
    `write_text`, que `guard-frozen.sh` tampoco ve, porque su `matcher` es
    Write/Edit/NotebookEdit—. Encontrado por el escrutinio adversarial del cierre.

    **Y faltaba lo que de verdad hay que proteger: los MANIFIESTOS.** Los fixtures se
    comparan **contra** `congelacion.json`, `recongelacion.json` y
    `correcciones.json`, así que la forma barata de hacer pasar un fixture manipulado
    no es tocar el fixture, es tocar el manifiesto — y ésos no los cubría ninguno de
    los dos hooks. Ahora sí, los dos, comprobado invocándolos.

71. **Una de las 30 está CONTAMINADA y su coincidencia no prueba nada: es
    `BOE-A-2026-5979-t15`, y coincide.** Para desambiguar cuál de las dos tablas de
    2x4 del documento era, se miró el texto del XML **antes** de transcribir. El
    método limpio da la misma respuesta, **pero eso no deshace haber visto**: su
    coincidencia con la verdad derivada no es evidencia independiente.

    **El desglose exacto de los 25 que coinciden: 21 limpias + 1 contaminada + 3
    corregidas**, y **lo emite el comparador**, no lo deduce nadie:

    ```bash
    uv run python scripts/comparar_verdad.py --informe   # runs/l4/informe.json
    ```

    **Este límite se publicó primero con una horquilla —«21 o 22»— y eso era peor que
    el propio límite.** El razonamiento fue: `congelacion.json` dice
    `"contaminadas": 1` y ningún fixture llevaba la marca, luego no se puede saber si
    la contaminada está entre las 25 que coinciden o entre las 5 que fallan, luego
    horquilla. **Y estaba completamente determinado por dos artefactos que ya
    existían**: basta cruzar la identidad del fixture con el informe de discrepancias
    para ver que no aparece entre los 5, luego coincide, luego el 21 es exacto.

    > **La lección, y vale para cualquier cifra de este repo: antes de declarar algo
    > NO MEDIBLE, comprueba si es DERIVABLE de lo que ya está medido.** Una horquilla
    > que se puede cerrar y se publica abierta dice menos de lo que se sabe, y eso
    > también es una forma de no ser preciso.

    Cerrado en las tres capas, para que no haya que volver a atar cabos: el fixture
    lleva `contaminada: true` con su razón, `congelar_l4.py` distingue **anotación**
    de **corrección** —la anotación no toca ni una celda, y eso se comprueba contra
    `git show HEAD:`, no se promete— y el informe trae la columna. Lo que **sigue**
    siendo cierto: esa coincidencia no cuenta como evidencia, y por eso el número se
    publica siempre con los tres sumandos y nunca como «25 de 30» a secas.

72. **La partición de línea sólo muerde DENTRO de un token, y su primera frecuencia
    está medida: 3 de 30.** El límite 31 predijo la asimetría y dijo que medirla
    exigía verdad de referencia con palabras partidas, o sea L4. Aquí está: 3 de las
    30 tablas tienen una celda que el PDF parte y el XML no, **y las tres parten
    justo detrás de una barra**. La afinación que sale gratis: en `BOE-A-2026-5851`
    el PDF también parte tres veces dentro de otra celda, pero **entre frases, tras
    un punto**, donde el espacio es correcto igual — y esa celda coincide. **La
    partición sólo produce discrepancia cuando cae dentro de un token.** Sigue sin
    estar cuantificado el daño sobre la nota de un extractor: eso es L5.

73. **Las tres barreras que L4 estrena se cerraron SIN control negativo, y se
    publicó que sí lo tenían.** `corregir_fixtures_l4.py` (el guardián del PDF),
    `congelar_l4.py` (el de la re-congelación) y `mutar_el_instrumento.py` (el arnés)
    son barreras en el sentido exacto de la regla en firme del repo —*un módulo cuyo
    único trabajo es ponerse rojo trae su control negativo en el mismo hito*— y
    ningún test las tocaba. Peor: `RESULTS.md` llegó a publicar *«se ha comprobado
    que sabe decir que no»* con **tres afirmaciones sin comando, sin test y sin
    artefacto**, que es literalmente la frase que este repo no admite.

    Cerrado el mismo día con `tests/unit/test_guardianes_l4.py`. **Y el primer
    intento de cerrarlo también estaba mal**, del mismo modo que el control negativo
    de `test_congelados_l4.py`: re-implementaba la lógica del guardián dentro del
    test en vez de llamarla, así que probaba su propia copia. Se extrajo
    `congelar_l4.sin_respaldo` para poder llamarlo de verdad. **Un control negativo
    que no invoca al sujeto no es un control negativo**, y este cierre lo ha
    demostrado dos veces seguidas.

74. **El número del criterio de L4 NO es reproducible en un clon frío.** Los cuatro
    comandos que `RESULTS.md` publica necesitan `runs/l3/docs` —2.000 PDF y XML, 362
    MB, fuera del repo por peso— y dos de ellos necesitan además el binario
    **`pdftotext`** (`poppler-utils`), que no estaba declarado en ningún sitio. Un
    tercero puede rehacer la cosecha (~35 min a 1 rps, `runs/l3/README.md`) y
    entonces sí, pero **eso no es lo mismo que reproducirlo**: el BOE puede haber
    cambiado un documento, y el manifiesto lo diría.

    Lo que **sí** corre en un clon frío, y por eso es donde vive el candado: los 43
    tests de `test_congelados_l4.py` y `test_guardianes_l4.py` que sólo necesitan los
    fixtures y los manifiestos, que ya están en el repo. El único que se salta es el
    del guardián del PDF, **con `skipif` y su razón escrita** en vez de un verde que
    no significaría nada.

75. **La cobertura de la comparación es del 53,1%, no del 100%: 1.213 celdas de
    2.283.** Las 30 tablas suman 2.283 celdas ancladas; el umbral de ventana de
    `plan.yaml` deja 3 tablas transcritas sólo por su cabecera más su última fila. La
    **dimensión completa** sí se comprueba en las 30, que es lo que recupera parte de
    lo que la ventana no ve. Estaba en el docstring del comparador y **no en
    `RESULTS.md`**, que es donde hace falta: un «cero fallos sobre 1.213 celdas» sin
    esta cifra al lado sugiere que 1.213 es todo lo que hay.

    Y la otra mitad del mismo descuido: **«11 de 1.213 celdas» mezclaba unidades.**
    De las 11, dos eran de `DIMENSION` —una fila entera de más—, que no son celdas.
    Se publica separado: discrepancias de texto sobre celdas, discrepancias de
    estructura sobre tablas.

76. **El barrido de mutantes de L4 no prueba NADA sobre la normalización, y no hay
    mutante que lo arregle sin escribirlo.** De los tres mutantes que tocan
    `normalize_cell_text`, dos no llegan al sujeto y uno es equivalente en la salida
    (límite 68). Así que la pregunta *«¿vería este instrumento un normalizador roto?»*
    **sigue sin respuesta**, y el instrumento no puede contestarla por su cuenta.

    **Lo que costaría cerrarlo, medido y sin promesa:** un mutante nuevo que parchee
    `docbench_es.core.canonical._normalizar.normalize_cell_text` —el módulo, no el
    paquete— y su entrada en el `PLAN` de `matar.py` con la suite que tiene que
    matarlo. Es un fichero de ~15 líneas, pero **no es gratis**: `matar.py` exige que
    todo mutante muera, así que hay que comprobar antes contra qué suite muere, y
    `test_canonical_normalizar.py` importa el nombre **del paquete** en su línea 29,
    o sea que podría sobrevivir y poner el arnés en rojo. Estimado **40-60 min**,
    incluido el trabajo de averiguar qué suite lo mata. Va a L5, que es quien vuelve
    a tocar el camino de normalización con los ocho extractores.

    Mientras tanto lo que cubre la normalización es L1: `normalizador_agresivo`,
    `normalizador_identidad` y `n3_incompleta` mueren los tres en
    `tests/unit/test_canonical_normalizar.py` —13, 5 y 1 tests respectivamente— por
    la vía del paquete, que es la que ese fichero usa.

77. **UNA PROTECCIÓN QUE NO DICE CUÁNTO PROTEGE ES INDISTINGUIBLE DE NO PROTEGER
    NADA, y este repo tenía un guardián protegiendo cero ficheros.** Es el modo de
    fallo **por defecto** de cualquier protección basada en patrones: el glob no
    casa, el guardián **no se queja** —no tiene de qué— y su verde significa *«no hay
    nada que vigilar»* en vez de *«todo está bien»*. Desde fuera se leen igual.

    **El caso, medido.** `stop-gate.sh` llevaba `GLOBS=(… 'runs/*/fixtures')`, que
    como pathspec de git casa con el **directorio** y no con lo que hay dentro:
    `git ls-files -- 'runs/*/fixtures'` devuelve **0** y `'runs/*/fixtures/*'`
    devuelve 30. O sea que durante todo el hito el hook protegía cero de los 30
    fixtures mientras el límite 70 de este mismo fichero publicaba «arreglado en los
    dos hooks». Y `guard-frozen.sh`, que sí casaba, **tampoco los vio**: su `matcher`
    es `Write|Edit|NotebookEdit` y las correcciones se escribieron con `write_text`.

    **Es la hermana de la familia «comprobar en el entorno equivocado» (skill
    `cerrar`, paso 9), y es peor**: allí hay una medición real mal ubicada; aquí **no
    hay medición ninguna**, y el hueco es exactamente lo que no se mide.

    **El arreglo, aplicado a los dos hooks y obligatorio para cualquier barrera
    futura que use rutas**, en tres partes que no valen sueltas:

    | Parte | Qué aporta |
    |---|---|
    | el guardián **publica su conjunto** (`--cuantos`), con los mismos patrones con los que decide | hace visible el cero |
    | un test afirma que es **> 0** y que la lista **casa con lo esperado**, derivada del disco y no de una constante | hace que alguien lo mire, en cada `make fast` |
    | su **control negativo**: se rompe el glob y el test se cae **nombrando el patrón** | prueba que las dos primeras miden algo |

    En `tests/unit/test_guardianes_por_glob.py`, 8 tests. Y una cuarta comprobación
    que salió de escribirlo: **los dos hooks tienen que proteger el MISMO conjunto**.
    El límite 27 dice que son complementarios en las **vías** que cubren —uno ve
    Write/Edit, el otro el resultado al cerrar el turno—, no en el conjunto de
    ficheros; si divergen ahí hay una familia protegida a medias, que es esta misma
    clase de fallo un nivel más abajo. Hoy los dos protegen **41**.

    **Lo que sigue sin cubrirse:** que un congelado nuevo entre en el repo sin que
    nadie añada su glob. El test exige lo que hay, no lo que debería haber, así que
    una familia nueva **no ponría nada rojo** — la lista de obligatorios se deriva del
    disco para las familias ya declaradas, no para las que no existen todavía.

78. **EL ORDEN DEL CONGELADO DE L4 NO ESTÁ ATESTIGUADO POR GIT: nada en el
    repositorio ata las 30 transcripciones a un momento anterior a la primera
    comparación.** Es la otra mitad del límite 74 —aquél dice que el número no es
    **reproducible** en un clon frío; éste dice que el **orden** tampoco es
    **auditable**—. Tres comandos:

    ```bash
    git show --stat --format="" c4ac769                        # 1 fichero, 5 líneas
    git ls-tree -r --name-only c4ac769 | grep -c '^runs/l4/fixtures/'   # 0
    git log --oneline --diff-filter=A -- runs/l4/congelacion.json       # 988a0fe
    ```

    **El hecho.** `c4ac769` dice en su mensaje *«Las 30 tablas transcritas del PDF y
    congeladas con hash antes de la primera comparacion»*, y su contenido son **cinco
    líneas de `runs/l4/plan.yaml` y CERO hashes**: escribe un **puntero**
    —`congelacion: runs/l4/congelacion.json`— a un fichero que **todavía no está en
    git**, más una fecha y el sello de un commit anterior. Los 30 `sha256` entran en
    `988a0fe`, que es **el mismo commit que publica el 25 de 30** en `RESULTS.md`,
    `ESTADO.md` y `LIMITS.md`.

    Consecuencia: **lo único que sostiene «transcrito a ciegas antes de comparar» es
    un campo `congelado_en` dentro de un JSON escrito por la misma persona en el
    mismo commit.** `test_los_26_no_tocados_conservan_la_huella_de_antes_de_comparar`
    es correcto y vale lo que dice: comprueba la **coherencia interna** de un
    manifiesto cuya **procedencia no está atestiguada**. Impide la deriva posterior;
    **no establece el orden original**.

    **El contraste, y es la mitad del valor de este límite: el congelado del
    COMPARADOR sí está atestiguado, y por el mecanismo correcto.** `b0853f4` mete en
    git **los bytes** de ADR-0040, `comparar_verdad.py`, `truth/derived.py` y
    `test_comparar_verdad.py` a las 06:38, **una hora antes** de `988a0fe` (07:38).
    Ahí git no atestigua un hash: atestigua el **contenido**, que es más fuerte. Y el
    re-sello de `98a2df1` es del mismo estándar —motivo escrito, sello original
    conservado al lado en vez de sobrescrito, sólo añadidos, y un test que exige que
    los tres ficheros intactos sigan cuadrando con el original—.

    **Mismo hito, dos congelaciones, una atestiguada y la otra no — y la que no lo
    está es el instrumento sobre el que descansa el hito entero.** ADR-0039 abre con
    *«todo lo que dependa de su buena fe hay que sacarlo de su buena fe y meterlo en
    una regla previa»*: se aplicó al comparador y no al instrumento.

    **Y pesa más aquí que en cualquier otro número del repo.** El 1.000/1.000 de L3
    lo puede recomprobar un tercero contra el BOE; el *«transcrito a ciegas antes de
    comparar»* **no lo puede comprobar nadie** salvo que el compromiso esté en git.

    **Lo que NO se hace, y va escrito para que no se haga por inercia: no se mete
    ahora un digest en `runs/l4/plan.yaml`.** Escribir hoy el `sha256` de
    `congelacion.json` en un commit posterior **parece** un compromiso y no lo es, y
    sería exactamente la familia que este repo ya tiene declarada cinco veces —
    publicar como observado lo que no se observó. **L4 se declara, no se retoca.**

    **Se cierra en la PRÓXIMA congelación, que es L8b**, con el paso escrito en
    [ADR-0041](docs/adr/0041-el-congelado-se-atestigua-con-un-digest-empujado.md) y
    en la skill `cerrar`. Por qué L8b y no «algún día»: son **120 documentos con
    doble pasada ciega**, el hito más caro en horas de persona del release y **el que
    cierra `v0.1.0`**. Es el mismo modo de fallo con cuatro veces la muestra y con
    anotadores de por medio; si ahí el orden tampoco está atestiguado, **el número
    que cierra el release depende otra vez de la buena fe de quien lo produce**.

79. **EL GUARDIÁN DE RECUENTOS CUBRE UNA CLASE DE CINCO, Y NO DECÍA CUÁL.** Es el
    límite 77 aplicado al propio guardián: una protección que vigila un quinto del
    problema y no lo declara **se lee igual que una que lo vigila entero**. Los
    documentos publicados producen cinco clases de número y `test_recuentos.py`
    sincronizaba **una**:

    | Clase | Quién la vigilaba |
    |---|---|
    | recuentos (`166 de 376`) | el guardián |
    | porcentajes (`51,7%`) | **nadie** |
    | deltas y restas (`+136`, `-7,3 puntos`) | **nadie** |
    | sumas de una enumeración | **nadie** |
    | sellos (`0717b70 · 164 tests`) | **nadie**, y salían de una variable ya impresa |

    La auditoría en frío de `a0d85ed` encontró **doce números rotos**, once de esas
    cuatro clases, y **tres imposibles por construcción**: `304 de 321` publicado
    como 99,0% —es 94,70%, y 321−304 son 17, no 3—; una enumeración de **21**
    rotulada *«Son 22 mutantes, y ésta es su composición completa, sin sumas que
    cuadrar»*, tres líneas encima del recuadro que presume de haber arreglado ese
    mismo fallo; y un sello de **164 tests** junto a un control negativo de **166**,
    que salen de la **misma expresión** en `matar.py` y no pueden diferir.

    **Y el tercero no era un dígito mal copiado: eran dos corridas presentadas como
    una.** Reconciliado por ejecución: `seccion_sin_cerrar` entró en el `PLAN` en
    `525c71d` (17:34), `0717b70` es de las 13:27, y su suite objetivo tiene 2 tests.
    **164 + 2 = 166.** O sea que la corrida de `0717b70` midió **21** mutantes, no 22.
    La misma clase apareció en la fila de L2 de `ESTADO.md` y en dos tablas de
    `RESULTS.md` rotuladas «la de arriba» que no son la de arriba.

    **El censo dijo el tamaño antes de decidir el arreglo: 285 expresiones con forma
    derivada** en los cuatro documentos. A ese tamaño no se arregla a mano.

    **La regla que sale, y es toda la regla:**

    > **UN NÚMERO DERIVADO NO SE TECLEA. O lo emite el script que lo mide, o no se
    > publica.**

    El `1.213` de L4 estaba bien porque vive en `runs/l4/congelacion.json`. El
    `2.283` del mismo párrafo estaba mal porque **no vivía en ninguna parte**:
    reconstruirlo desde los fixtures da 2.301 o 2.281 según cómo se cuente. Se
    arregló haciendo que el comparador lo emitiera, no tecleándolo mejor.

    Lo cierra `scripts/derivadas.py`, en la puerta por `test_barreras_documentos.py`
    y como paso 8 de `/cerrar`. **Y su hueco va declarado, como el del límite 54:**
    comprueba la **aritmética interna** de lo publicado —que un porcentaje salga de
    su fracción, que una enumeración sume lo que dice— y **no** que los operandos
    sean ciertos. Un `304 de 321` con los dos números mal y el 94,7% bien pasa.

80. **README y CHANGELOG nunca estuvieron en el guion de `/cerrar`, y se notó a los
    33 commits.** `grep -i "readme\|changelog"` sobre la skill daba **cero**. Con
    cuatro hitos más cerrados, `README.md` seguía en el commit `645ccfe` —de L0—
    diciendo *«Hito L0 de 10 de la `v0.1.0`. Todavía no hay número»*, *«L1 a L8b
    pendientes»*, y publicando la puerta sobre `28186b9`. `CHANGELOG.md` se había
    quedado en L2, faltándole 22 commits, con su propia cabecera diciendo que cada
    entrada «se escribe al cerrarlo con `/cerrar`».

    **Y la ironía es el argumento:** el README contiene la frase *«en un repo que
    vende rigor, escribir en presente lo que no existe es el peor fallo posible, más
    grave que un bug»*, y hacía el reflejo exacto de esa frase.

    **El arreglo no fue actualizarlo**, porque un fichero que hay que acordarse de
    tocar se queda rancio otra vez y ya sabemos cuántos commits tarda: el titular y
    la tabla de estado del README **se derivan de `ESTADO.md`** entre marcas HTML
    (`scripts/estado_readme.py`), y lo hace cumplir la puerta. Lo que **no** se puede
    derivar son los ticks ✅/🕓 de «las cinco cosas»: eso es un paso a mano en
    `/cerrar`, dicho como tal.

81. **Entre el 12 y el 15% de `src/` no tiene productor ni consumidor, y está
    medido.** **14 de los 23 tipos declarados en `types/` no se construyen en ningún
    punto de `src/`** —`Stratum`, `SamplingPlan`, `StructureMetrics`, `AnswerMetrics`,
    `GlossaryMetrics`, `CampaignResult`, `GlossaryContribution`, `RoutingRule`,
    `RoutingPlan`, `Question`, `AnswerResult`, `Fact`, `Term`, `ConfusablePair`—, y
    `types/_campana.py` son **191 líneas de las que sólo `TedsReport` tiene
    productor**. Hay además **14 ficheros de tres líneas útiles o menos**.

    **Cinco defectos concretos que salieron con ello, y ésos SÍ se arreglaron en el
    acto**, porque eran afirmaciones falsas o código muerto y no cobertura pendiente:
    dos literales de cadena huérfanos —`entity/boe.py` y `corpus/pairing.py`, expresiones
    evaluadas y tiradas—, una rama inalcanzable en `corpus/harvest.py`, un
    `sin_urls` cuyo docstring afirmaba «se publican al lado de `intentados`» sin que
    nadie lo lea, y un `holes()` cuyo docstring decía «quien la usa es `validate`»
    cuando `validate` **no la llama**: pasa por `_invariantes._cobertura`, que es una
    **segunda implementación** de «posición cubierta», y **las dos difieren para
    tablas mal formadas**. Y el entry point `docbench` estaba declarado en
    `pyproject.toml` apuntando a un módulo que no existe: `uv run docbench --help`
    reventaba. **Retirado hasta L5**, que es quien escribe la CLI.

    **La poda queda como deuda con su tamaño, no como promesa:** ~600 líneas fuera
    sin perder funcionalidad, y vuelven cuando su hito las construya. Y hay tres
    implementaciones idénticas de `tasa_descarte` —`pairing.py`, `_cosecha.py`,
    `manifest.py`— en un repo cuyo propio `entity/boe.py` dice que **«dos copias del
    mismo dato no pueden divergir»**.

82. **`runs/l4/plan.yaml` está congelado y cita una ruta que ya no existe.** Los
    censos y sondeos —**50.517 líneas de JSON generado contra 4.468 de prosa**—
    vivían en `docs/`, así que de un vistazo el repo parecía tener 55.000 líneas de
    documentación escrita a mano. Se han movido a `runs/censos/`, que es donde viven
    los demás artefactos de medición.

    **El plan de L4 no se ha editado para arreglar la ruta**, y es deliberado: ese
    fichero es el instrumento de un hito cerrado y tocarlo por comodidad es
    exactamente lo que la regla del congelado prohíbe. Sigue diciendo
    `censo: docs/censo-corpus-1000.json`, y su `censo_sello: 525c71d` identifica el
    contenido igual de bien: `git show 525c71d:docs/censo-corpus-1000.json`. **Una
    ruta vieja en un fichero congelado se resuelve con un `git log`; un fichero
    congelado editado, no se resuelve.**

    Lo que sí queda sin cubrir: el barrido de referencias **no ve esa cita** —no
    recorre los `plan.yaml`— así que nadie se pondría rojo si mañana el sello
    también dejara de resolver. Declarado, no arreglado.

83. **UNA REGLA CONGELADA QUE NINGUNA MÁQUINA PODÍA LEER, Y SIETE MESES SIN QUE
    NADIE LO NOTARA.** `runs/l5/computo.yaml` —la regla de decisión de B5-bis,
    commiteada sola y **antes** de medir, que es lo único que la hace un
    pre-registro— **no parseaba como YAML**. Llevaba `de longitud: el coste de OCR`
    dentro de un escalar plano de una lista, y un `: ` ahí es un error de sintaxis.

    **Lo que esto convierte en falso**: nada de lo publicado, porque todavía no se
    había medido nada contra él. Lo que sí destruía es su función: un pre-registro
    vale porque **algo puede confrontarlo después**, y contra un fichero que no
    parsea ese algo no existe. Lo que quedaba era un comentario largo con extensión
    `.yaml`.

    **Cómo se descubrió**: no lo descubrió nadie leyéndolo. Lo descubrió el primer
    script que intentó abrir con un parser un fichero **hermano** suyo.

    **Arreglado, y el arreglo es el que se hace en un pre-registro**: se le han
    puesto tres marcadores `- >` y **no se le ha tocado una palabra** —comprobado
    comparando el texto parseado con el original—. Lo hace cumplir
    `tests/unit/test_reglas_parseables.py`, sobre **todo YAML versionado** y no sólo
    sobre `runs/`, con su control negativo dentro que reproduce **esta misma forma**
    de fallo: la primera versión del control usaba `- clave: valor` en UNA línea, que
    es un mapeo perfectamente válido, y **pasaba en verde contra un YAML sano**.

    Lo que queda sin cubrir: que un YAML parsee no dice que diga lo que debe. Nadie
    comprueba que `runs/l5/computo.yaml` tenga una clave `regla:`, ni que la regla
    que contiene sea la que se aplicó. Eso lo sostiene el cierre del hito, a mano.

84. **LA PUERTA NO TIPA LOS SCRIPTS HUÉRFANOS: 27 de 45.** `make fast` corre
    `mypy --strict src tests`. `scripts/` entra sólo por `mypy_path`, así que se tipa
    **lo que un test alcance** —directa o transitivamente— y nada más.

    **Las dos mitades, y hablan de subconjuntos distintos.** Un script que un test
    importa **sí** lo tipa la puerta, incluso a través de otro script: `informe_l4.py`
    no lo importa ningún test, pero sí `comparar_verdad.py`, y por ahí llega. Lo que
    la puerta **no** ve son los huérfanos, que nadie importa. Decir «la puerta no tipa
    `scripts/`» a secas es más grande que el hueco real.

    **Comprobado plantando el fallo en los dos sitios**, no deducido: se añadió
    `def _plantado() -> int: return "no soy un int"` al final de `scripts/informe_l4.py`
    —alcanzable— y de `scripts/termometro.py` —huérfano—. `mypy --strict src tests`
    cazó el primero y **no vio el segundo**.

    El reparto, con su comando: `uv run python scripts/huerfanos.py`. De **88** scripts,
    **30 son mutantes** —carga útil que se rompe a propósito, tiparlos no querría decir
    nada—, y de los **58** que quedan, **huérfanos: 24 de 58**. Entre ellos `derivadas.py`
    y `estado_readme.py`, o sea **los programas que comprueban los números derivados que
    se publican**. Y este mismo censo es uno de ellos: se cuenta a sí mismo.

    **Bajó de 26 a 24 con TRES scripts más, y no por casualidad:** los cinco que entran con
    la portada —`error_del_estimador.py`, `regla_reloj_l5.py` y `regla_portada.py`— los
    importan `tests/unit/test_barreras_documentos.py` y `tests/unit/test_portada.py`, así
    que nacen dentro de la puerta, y por el camino arrastran a `poblacion_l5.py`. Un
    instrumento que emite un número publicado entra tipado o no entra.

    La cifra la vigila `scripts/derivadas.py`, porque la primera versión de este límite
    publicó **22 de 36** y estaba vieja **seis días después de escribirla** — el propio
    trabajo de B5-bis añadió scripts. Un número derivado no se teclea, ni siquiera
    dentro de un límite que habla de otra cosa.

    **No está arreglado a propósito**: meter `scripts` entero en la puerta hoy la pondría
    roja por programas de un solo uso de hitos ya cerrados, y ésa es una tarde que no
    toca. Precio y fecha: con L5, cuando `scripts/` deje de ser un cajón y los que
    sobrevivan tengan consumidor.

85. **EL COSTE DE B5-bis SE MIDE DENTRO DE UN SOBRE TÉRMICO, ASÍ QUE EL RELOJ NO ES
    EL SUELO DE LA MÁQUINA.** La primera versión del cómputo corrió los cuatro
    extractores en un solo proceso sin límite de hilos: `docling` carga *torch*,
    *torch* cogió los 8 procesadores que WSL ve, y la CPU llegó a **85 °C** —dentro
    de especificación para un 9950X3D, Tjmax 95 y corte térmico 115, pero por encima
    de los 65 °C que el dueño de la máquina pidió al principio—. Desde entonces se mide
    con los hilos
    fijados, con `nice -n 19`, con pausas entre unidades y, cuando hay termómetro,
    con el proceso **parado por `SIGSTOP`** al pasar del techo. El sobre está
    declarado en `runs/l5/termica.yaml`.

    **El techo se relajó después a 90 °C de pico y 82 °C de media**, con su razón
    escrita: AMD documenta que el procesador está diseñado para funcionar a TJMax
    —~95 °C— de forma continua sin deterioro, y el silicio se frena solo antes de
    sufrir. 90/82 deja 5 °C de colchón sobre el punto donde el fabricante dice que
    puede vivir permanentemente. **Los 65 °C iniciales no eran un límite físico:
    eran una precaución sin dato.**

    **La consecuencia sobre los números**: los segundos de **reloj** de B5-bis no son
    el coste mínimo alcanzable en esta máquina, y **no se publican sin decir con
    cuántos hilos y con cuántas pausas se midieron**. Por eso la moneda primaria son
    los **segundos de CPU** —`ru_utime + ru_stime` del hijo vía `os.wait4`—, que no
    los altera ni el `SIGSTOP` ni el ciclo de trabajo.

    **Lo que NO acota, y es la mitad honesta**: sin HWiNFO publicando un sensor en
    `HKCU\Software\HWiNFO64\VSB`, desde WSL2 **no hay de dónde leer la temperatura**
    —`/sys/class/thermal/*/temp` vacío, `lm-sensors` ausente,
    `MSAcpi_ThermalZoneTemperature` sin respuesta: comprobado, no supuesto—. En ese
    caso el cómputo se declara `vigilado: false`, baja a 2 hilos y **no afirma ningún
    grado**. Tampoco se toca la frecuencia de boost, así que menos hilos no baja la
    temperatura de forma lineal: con pocos hilos el boost sube el voltaje por núcleo.

86. **NI `OMP_NUM_THREADS` NI `taskset` ACOTAN LA CARGA DE `pymupdf4llm`, Y EL PRIMER
    SOBRE TÉRMICO DECÍA QUE SÍ.** El gobernador de B5-bis fijaba los hilos por entorno
    y luego añadió `taskset -c 0-(n−1)` como «tope duro del sistema operativo». Las dos
    cosas fallan contra esta biblioteca, y **la primera versión de este límite lo habría
    dado por bueno sin mirarlo**.

    **Lo delató un número que el propio gobernador guarda**: `hilos_efectivos =
    cpu_s / trabajo_s` salió **4,2 y 5,3** con el entorno pidiendo 2. Sin ese campo,
    nadie se habría enterado.

    **Medido con tres instrumentos y con su control positivo**, porque «mi medida dice
    algo imposible» tiene dos explicaciones y hay que separarlas:

    | | |
    |---|---|
    | `os.wait4` | 12,89 s de CPU en 2,58 s de reloj = **4,99 núcleos**, con 2 en la máscara |
    | `/usr/bin/time -v` | **484% de CPU**, mismo caso — instrumento independiente, misma respuesta |
    | `top` | **600%** sobre el proceso, en vivo |
    | `/proc/PID/status` | `Cpus_allowed_list: 0-1` — pero ésa es la máscara de la **hebra líder** |
    | `/proc/PID/task/` | **45 hebras**. Las trabajadoras se reponen la afinidad una a una |
    | control positivo | 8 **procesos** girando bajo `taskset -c 0-1` dan **2,11**; sin `taskset`, **8,38**. `taskset` funciona; lo que no funciona es `taskset` contra una biblioteca que se repone la afinidad |

    **El arreglo, y es el único que aguanta**: `cgroup v2` con el controlador `cpu` existe
    en esta máquina pero `/sys/fs/cgroup` no es escribible sin root, así que el tope se
    hace con **ciclo de trabajo**: `SIGSTOP` una fracción de cada periodo, `SIGCONT` el
    resto. **No depende de cuántas hebras abra la biblioteca sino de cuánto rato se les
    deja correr.** Y no distorsiona el número publicado, porque el tiempo parado se resta
    en `trabajo_s` — comprobado: con ciclo, `pymupdf4llm` sobre 6 páginas da 2,6 s de
    trabajo; sin ciclo daba 2,6 s.

    **Su afirmación es falsable y se comprueba en cada informe**: `cpu_s / reloj_s ≤
    fracción × núcleos`, unidad por unidad, nombrando la que la incumpla.

    Lo que queda sin cubrir: el ciclo acota la **media**, no el pico instantáneo. Entre
    dos `SIGSTOP` la máquina puede ir a tope, y con `latido` de 20 ms y periodo de 2 s
    eso son ráfagas de hasta 1,2 s. Y sigue sin haber termómetro: sin HWiNFO no se afirma
    ningún grado. Ver `runs/l5/termica.yaml`.

87. **`pymupdf4llm` HACE OCR POR DEFECTO, Y ESO ES LA MAYOR PARTE DE SU COSTE.** Arrastra
    `rapidocr`, y en las corridas de B5-bis imprime `Using RapidOCR for OCR processing` y
    `OCR on page.number=…` sobre documentos **nacidos digitales**, que tienen capa de
    texto. De ahí sus 45 hebras y sus ~1,25 s de CPU por página, frente a los 0,045 de
    `pdfplumber`.

    **El coste que B5-bis publica de `pymupdf4llm` es el de su configuración por
    defecto**, y eso es lo correcto —es lo que le pasa a quien lo instala y lo llama—,
    pero **no es su coste mínimo**: quien desactive el OCR verá otro número. Se declara
    aquí porque un s/página sin decir esto invitaría a comparar peras con manzanas.

    No medido: cuánto baja el coste con el OCR desactivado, ni si la calidad de
    extracción cae al desactivarlo. Las dos preguntas son de L5, no de B5-bis.

88. **DOS TERCIOS DEL CORPUS NO TIENEN NI UNA TABLA, ASÍ QUE EL TEDS AGREGADO SE
    PROMEDIA SOBRE 338 DOCUMENTOS Y NO SOBRE 1.000.** Censo sobre la verdad de
    referencia, con su comando: `uv run python scripts/censo_tablas.py`. **338 de 1.000**
    tienen alguna tabla (33,8%), y hay **2.135** tablas en total.

    Y se concentran más que las páginas: los **38** documentos de más de 50 páginas son
    el 3,8% de los documentos, el 36,6% de las páginas y **el 43,0% de las tablas**, a
    **28,7 tablas por documento**. Un solo documento de esa banda tiene tantas tablas
    como 28 documentos cortos.

    **Lo que esto obliga a publicar**: el agregado va siempre con su n efectiva —338— y
    con los 662 `NO_APLICABLE` al lado. «El TEDS medio del corpus» sin eso daría por
    medida una población que no se midió. Y remata el descarte de la media por tabla:
    32 documentos, el 9,5% de los que puntúan, cargarían el 43% del peso. Ver
    `runs/l5/ponderacion.yaml`.

    Lo que **no** afecta: la estimación de coste. El censo que hay que procesar es 66%
    sin tablas, así que una muestra aleatoria del censo lo refleja bien — el coste de
    procesar un documento sin tablas también es coste.

89. **CATORCE VECES LOS HILOS NO COMPRARON NADA DE RELOJ Y COSTARON HASTA DOCE VECES
    LA CPU.** De 2 hilos por unidad a 28, mismos 27 documentos y mismas 108 unidades:
    el reloj total de los cuatro extractores sobre los 1.000 documentos pasó de
    **5,55 h a 5,95 h** —**subió**— mientras los segundos de CPU pasaban de 10,91 h a
    **67,61 h**. Por página, `docling` multiplicó su CPU por **12,03** para ir un 10%
    **más lento**.

    **La causa medida**: los hilos efectivos de `docling` pasaron de 1,48 a **13,77**.
    No estaba en su techo de paralelismo —eso era lo que decía el razonamiento
    pre-registrado, y era falso—: estaba topado, tenía hambre, y **no convierte esa CPU
    en velocidad**. Paralelismo de rendimiento negativo. Con grupos de hebras que
    esperan girando —OpenMP, ONNX Runtime, *torch*— una hebra bloqueada consume CPU sin
    hacer trabajo.

    **Lo que esto invalida de lo publicado**: nada, porque los dos números están
    publicados con su configuración al lado, que es para lo que se separaron las dos
    monedas. Lo que invalida es **el supuesto**, escrito en el pre-registro, de que los
    segundos de CPU son casi invariantes al número de trabajadores. No lo son.

    **La consecuencia para L5**: la configuración de pocos hilos es estrictamente mejor
    —mismo reloj, entre 4 y 12 veces menos CPU—, así que el paralelismo hay que buscarlo
    en **unidades concurrentes** y no en hilos por unidad. Eso está sin medir y sin
    predecir: es el experimento B, y su cuello no será la CPU sino la RAM, porque
    `docling` pica 4,4 GB por unidad y hay 47 GB.

    No medido: dónde está el óptimo de hilos por unidad. Se han medido **dos** puntos,
    2 y 28, y el de 2 puede no ser el mejor de los dos extremos ni del medio.

90. **LA DIRECCIÓN DEL SESGO POR EXCLUIR EL DOCUMENTO DE 309 PÁGINAS DEPENDE DE LOS
    HILOS, Y EL PRE-REGISTRO LO DIO POR FIJO.** `runs/l5/estimacion.yaml` afirmaba,
    antes de medir, que excluirlo sesga el total **al alza** —conservador— porque el
    coste por página baja con la longitud cuando hay un coste fijo por documento. Se
    escribió falsable y se comprobó con la pendiente de coste/página contra páginas en
    la banda `>50`.

    A **2 hilos** sale **−9,275e-05**: negativa, el argumento se sostiene.
    A **28 hilos** sale **+1,801e-02**: positiva, y **el argumento es falso** — el coste
    por página sube con la longitud, porque un documento largo pasa más tiempo dentro de
    las secciones paralelas donde está la contención.

    Así que la exclusión es conservadora **sólo en la configuración de pocos hilos**, y
    en la de muchos sesga a la baja, que es la dirección mala. No se arregla
    reinterpretando el argumento: se publica que **la dirección depende de la
    configuración**, y cada número va con la suya.

    Lo que queda sin cubrir: no se ha medido si hay una configuración en la que la
    pendiente sea cero, ni si el signo cambia de forma continua o de golpe.

91. **EL PUNTO DE CONTROL DE B5-bis SE MIDIÓ SIN SELLO DENTRO, Y EL SELLO EXISTÍA.**
    `Estado.guardar()` no escribía el campo `sellos` que `Estado` ya calculaba y que el
    informe ya imprimía: un parche por sustitución de texto **no encajó y se aplicó en
    silencio**. Es la segunda vez en la misma sesión —la primera fue `main()` en
    `unidad_computo.py`, que dejó la unidad esperando dos argumentos cuando el padre le
    pasaba tres— y las dos veces la causa fue la misma: reemplazar sin **afirmar** que
    el original encajaba.

    **Alcance real**: `runs/l5/computo_A_28hilos.json` no lleva su sello dentro. Sí lo
    lleva `runs/l5/computo_A_28hilos.log`, **impreso por el propio instrumento**
    —`sello: 810f705 · 28w · 28 trabajadores de 28 CPU`—, así que la procedencia está
    registrada y no reconstruida a mano. Arreglado para las corridas siguientes, con
    `assert` en el parche.

    Lo que queda sin cubrir: nada comprueba que un artefacto de medición lleve sello.
    Se detectó mirándolo, que es exactamente la clase de garantía que este repo no
    acepta para lo demás.

92. **LA PUERTA ESTUVO ROJA EN CI TRES COMMITS SEGUIDOS, Y LA CAUSA FUE INSTALAR
    DEPENDENCIAS PARA MEDIR.** `make fast` en un clon limpio daba **7 errores** de
    `mypy` sobre `scripts/unidad_computo.py`: `pdfplumber`, `pymupdf4llm`, `camelot`,
    `torch` y `docling.document_converter` no tienen stubs **y no están instalados**.

    ```bash
    git clone <repo> /tmp/frio && cd /tmp/frio
    uv sync --only-group dev && make fast; echo "rc=$?"     # rc=2
    ```

    **Aquí pasaba porque `extract-local` se instaló para correr B5-bis.** El workflow
    instala **sólo** el grupo `dev`, y a propósito: `--all-extras` arrastra torch, CUDA
    y OCR, varios GB, muy por encima del presupuesto de 90 s. Así que desde el momento
    en que se instalaron los extras había **una máquina donde la puerta pasa y ninguna
    otra**, y la puerta no declaraba de qué entorno dependía su resultado.

    **Es la segunda vez con esta forma**: el mensaje de `9db1be9` dice, con estas
    palabras, *«el barrido medía mi máquina, no el repositorio: la puerta estaba roja en
    cualquier clon»*. Entonces era `referencias.py`; ahora `mypy`. **La causa sí es
    nueva**: no es un guardián que mira mal, es que **medir cambió el entorno en el que
    se evalúa la puerta**.

    Y los `# type: ignore[import-untyped]` en línea **fallaban en las dos direcciones**:
    sobraban cuando la biblioteca estaba —`unused-ignore`— y no bastaban cuando no
    estaba. Un arreglo táctico que sólo funciona en un entorno es el mismo bug con otro
    signo.

    **Arreglado en las dos mitades, y comprobado en los dos entornos**:

    1. `[[tool.mypy.overrides]]` con `ignore_missing_imports` e `implicit_reexport` para
       las cinco bibliotecas opcionales. El resultado de la puerta deja de depender de
       qué extras haya. Verificado **con** extras (`rc=0`) y **sin** extras en un clon
       limpio (`rc=0`).
    2. **El entorno entra en la huella de la puerta.** `.claude/hooks/huella-puerta.sh`
       incluye ahora los nombres de lo instalado en `.venv`, así que un verde de un
       entorno deja de avalar un commit en otro. Es la misma familia que el número de
       trabajadores de `-n auto`: una cifra que depende de una condición no declarada no
       es reproducible.

    Lo que queda sin cubrir: **nadie mira CI**. Estos tres commits pasaron el aro local
    de `guard-commit.sh` con la puerta local verde y CI en rojo, y el aro no lo sabía
    porque miraba un entorno distinto. Ahora la huella los distingue, pero **seguir el
    resultado de CI sigue siendo una costumbre**, no un mecanismo.

93. **`@runtime_checkable` NO PUEDE COMPROBAR LO QUE EL REGISTRO NECESITA.** Comprobado
    en el intérprete: `isinstance(instancia, Extractor)` funciona y sí mira los
    atributos de dato, pero `issubclass(clase, Extractor)` lanza
    `TypeError: Protocols with non-method members don't support issubclass()`.

    Y el registro **no tiene instancia**: devuelve la clase precisamente para decidir sin
    construir, porque construir un extractor de document-AI carga modelos. Así que el
    único chequeo que el decorador habilita exige justo lo que el diseño evita. **No era
    falso: era inutilizable donde hacía falta**, que es el límite 77 otra vez y en el
    primer fichero de L5.

    **Arreglado** con `extract.base.cumple_la_forma(cls)`, que hace sobre la clase lo que
    `issubclass` habría hecho y **publica su denominador** —«9 miembros comprobados
    (6 declaraciones + 3 métodos)»—. `@runtime_checkable` se queda para donde sí hay
    instancia, y el test dice **sobre qué opera cada mitad**.

    Lo que `cumple_la_forma` **no** mira: los tipos. `kind = "parseador"` pasaría. Eso lo
    caza `mypy` en quien escribe el extractor, y la conducta la caza la conformidad.

94. **Y `ruff` TAMBIÉN DEPENDÍA DEL ENTORNO, PERO PEOR: LOS DOS EXIGÍAN FORMAS
    CONTRADICTORIAS.** Al comprobar el arreglo del límite 92 en un clon limpio apareció
    otro, de la misma familia y más grave. Con **la misma versión** (`ruff 0.16.4`), **el
    mismo `pyproject.toml`** —comprobado por `md5sum`— y **el mismo fichero byte a byte**
    —comprobado por `md5sum`—:

    | | `scripts/estimar_computo.py` |
    |---|---|
    | aquí | exige `censo_paginas` y `unidad_computo` **juntos** |
    | clon limpio | exige una **línea en blanco** entre los dos |

    **No había forma del código que pasara en los dos.** Comprobado en las dos
    direcciones: se puso la línea en blanco y entonces la puerta se ponía roja aquí. Eso
    es peor que el límite 92, donde al menos existía un arreglo táctico que funcionaba en
    un entorno.

    **La causa**: `ruff` **infiere** qué imports son de primera parte, y la inferencia
    depende de lo que resuelva. No estaba declarado. **Arreglado declarándolo**:
    `src = ["src", "scripts", "tests/unit"]` en `[tool.ruff]`. Con eso la clasificación
    es determinista y las dos máquinas dicen lo mismo. Reclasificó 24 imports.

    **Y de la reclasificación salió un choque con el congelado**, que se resolvió por
    donde manda la regla: `ruff` quiso reordenar el bloque de imports de tres ficheros
    **sellados** en `runs/l4/congelacion_comparador.json` —`comparar_verdad.py`,
    `truth/derived.py` y `test_comparar_verdad.py`—, y el candado lo cazó por **una línea
    en blanco**. El sello vale porque es a nivel de byte, así que una línea de más lo
    rompe igual que un cambio de lógica: eso es una propiedad, no un defecto. Se hizo
    `git checkout` de los tres y se les eximió `I001` con la razón escrita. **Re-sellar
    por comodidad es exactamente lo que el congelado prohíbe.**

    Lo que queda sin cubrir: **no se ha buscado la tercera**. `mypy` y `ruff` dependían
    del entorno; nadie ha comprobado si `pytest`, `lint-imports` o los guardianes de
    `scripts/` también. La puerta se ha verificado entera en los dos entornos —`rc=0` en
    ambos— pero eso es un resultado de hoy, no una propiedad garantizada.

95. **`expresa_spans` FALLABA ABIERTO, Y ABIERTO ERA LA DIRECCIÓN CARA.** La primera
    versión preguntaba `native_format not in FORMATOS_SIN_SPANS` sobre un `str` sin
    acotar, así que **el valor por defecto de lo desconocido era conceder spans**.
    Medido, no supuesto:

    | entrada | daba | por qué importa |
    |---|---|---|
    | `"markdow"` | `True` | una letra de menos |
    | `"Markdown"` | `True` | una mayúscula |
    | `"md"` | `True` | el mismo formato, otro nombre |
    | `""` | `True` | la cadena vacía |

    Y conceder spans indebidamente es **exactamente el modo de fallo que la función
    existe para impedir**: el extractor cobra un cero en el estrato de celdas combinadas
    —el que se sobremuestrea y se declara titular— *como si hubiera competido y
    perdido*, cuando lo que pasó es que su formato no llegaba. Un formato desconocido
    tragado como «sí puede» es un error tragado, y la regla de oro 6 lo prohíbe.

    No era remoto: `Extraction.native_format` es `str` a secas, así que nada impide una
    mayúscula en un adaptador de once líneas.

    **Arreglado en dos mitades.** Lista **positiva** `FORMATOS_CON_SPANS`, enumerada a
    mano —derivarla como el complemento sería el mismo fallo una capa arriba, porque un
    sexto formato canónico entraría solo en el grupo de los que sí—; y `expresa_spans`
    **levanta** ante cualquier formato fuera de `FORMATOS_CANONICOS`. Es la misma postura
    que este repo ya toma con `HallazgoTabla.SOURCE_FORMAT_DESCONOCIDO`: un formato que
    nadie declaró es una condición **detectada**, no un valor por defecto.

    **Por qué NO se tipó `native_format` como `Literal`**, que era la salida más limpia
    en apariencia: haría el caso imposible por construcción y con eso **desaparecería el
    chequeo en ejecución que el repo tiene puesto a propósito**. `source_format` es `str`
    *para que* `SOURCE_FORMAT_DESCONOCIDO` signifique algo, y el caso real es un formato
    que llega de fuera, no de código tipado.

    Lo que queda sin cubrir: nadie comprueba que `Extraction.native_format` y
    `CanonicalTable.source_format` coincidan. Un extractor podría declarar `html` y
    producir tablas con `source_format="markdown"`.

96. **EL CONTRASTE DE `expresses_spans` NO ES UNA IGUALDAD, Y TIENE CUATRO DESENLACES.**
    La regla obvia —exigir que lo declarado coincida con lo que el formato permite—
    **deja el incentivo al revés**: un extractor cuyo parser aplana los `rowspan` y lo
    declara honestamente con `False` fallaría por honesto, y le saldría más barato
    declarar `True` y cobrar el cero, que al menos pasa la suite.

    La corrección obvia es la desigualdad —`declarado ≤ permitido`— y **también se queda
    corta**. Este repo ya tenía la regla entera en `types._invariantes._spans_declarados`
    para `CanonicalTable`, con su razón escrita: *«declararse incapaz trayendo celdas
    combinadas también miente, y de esa se aprovecharía quien quisiera esconderse en
    NO_APLICABLE»*.

    | declarado | el formato | vio combinadas | veredicto |
    |---|---|---|---|
    | `True` | **no** permite | — | `CONTRADICCION` |
    | `False` | — | **sí** | `ESCONDIDO` |
    | `False` | permite | no | `SIN_EVIDENCIA` |
    | resto | | | `COHERENTE` |

    **`SIN_EVIDENCIA` no es un aprobado**, y por eso es un valor propio: si la muestra no
    traía ni un documento con celdas combinadas, no se distingue *«su parser las
    aplana»* de *«no le tocó ninguna»*. Es la tercera severidad que la suite de entidad
    ya usa —`NO_EJECUTADA`—: un aro por el que no se ha pasado no está superado.

    Escrito en `extract._spans.veredicto_de_spans` **antes de que exista la suite que lo
    aplica**, para que sea una decisión y no un cambio de criterio a toro pasado.

    Lo que queda sin cubrir: **cuántos documentos con celdas combinadas hacen falta**
    para que `SIN_EVIDENCIA` pase a ser un aprobado. Hoy basta con uno, y uno es poco;
    el número correcto no está medido y sale de la muestra de conformidad, que no existe.

97. **UN TEST DE LA CONFORMIDAD DEPENDÍA DEL CORPUS LOCAL, Y EL CORPUS NO SE
    VERSIONA.** `test_todos_los_elegidos_tienen_su_pdf` comprobaba que los cinco
    documentos del conjunto de conformidad tuvieran su PDF en `runs/l3/docs/`. Aquí
    pasaba; **en un clon limpio ponía la puerta roja**, porque los 1.000 PDF del corpus
    son documentos ajenos y no están en el repo.

    Es la misma familia que los límites 92 y 94 —`mypy` y `ruff` dependiendo del
    entorno— en su tercera aparición del día, y la encontró el mismo procedimiento:
    correr la puerta en un clon frío antes de empujar.

    **Arreglado con un salto explícito**, no con un borrado: si el corpus no está, el
    test se salta **diciendo que no es un aprobado** —*«NO se ha comprobado que los
    elegidos tengan PDF; no es un aprobado, es que aquí no se puede mirar»*—. Es la
    misma postura que `NO_EJECUTADA` en las suites de conformidad, trasladada a `pytest`.

    **Y el hueco es más pequeño de lo que esta entrada declaró primero.** La
    precondición eran **dos cosas metidas en un test**, y sólo una necesita el corpus:

    | | ¿se puede comprobar en CI? |
    |---|---|
    | el fixture del documento existe, sus spans son los declarados, su forma y sus páginas también | **sí** — sale de `runs/l4/fixtures/` y `runs/l3/manifiesto.json`, los dos versionados |
    | el PDF está en disco | no — son 1.000 documentos ajenos |

    Con las dos juntas, un cambio en la primera —alguien toca el conjunto, o un fixture
    deja de tener los spans que se le suponen— no lo cazaba nadie hasta que alguien
    corriera con corpus. **Partidas en dos tests**, la que sostiene el número publicado
    —*«veredictos que este conjunto puede producir»*— corre siempre.

    Y al partirlas apareció un tercero que se colaba: `cuadra` era sólo
    `declara == (spans > 0)`, así que **un fixture borrado daba `spans=0` y un documento
    declarado «sin combinadas» seguía cuadrando**. Un fichero desaparecido pasaba en
    silencio. Ahora `fixture_existe` va primero, con su control negativo.

    **Lo que queda sin cubrir es sólo esto**: en CI no se comprueba que los bytes del PDF
    estén. Si alguien mete un documento que no está en el corpus, CI seguirá verde y se
    enterará quien corra la conformidad de verdad — pero su forma declarada y sus spans
    sí se habrán comprobado antes.

98. **`dataframe` NO ESTABA EN `FORMATOS_SIN_SPANS`, Y EL AGUJERO APUNTABA A `camelot`.**
    `core.canonical._dataframe` pone `expresses_spans=False` **en su primera línea** y
    explica por qué —un `DataFrame` es una rejilla rectangular, y un `MultiIndex` se
    *pinta* como cabecera combinada pero el objeto no distingue «combinada» de
    «repetida»—. `types.FORMATOS_SIN_SPANS` decía `{"markdown", "text"}`.

    **Cuatro hitos con el código y la lista diciendo cosas distintas.** Medido:

    ```python
    CanonicalTable(..., expresses_spans=True, source_format="dataframe").is_wellformed()
    # -> (True, [])      ← la da por buena
    ```

    `_spans_declarados` existe para cazar exactamente esa mentira y no la cazaba, porque
    consultaba la lista y la lista estaba incompleta.

    **A quién le habría tocado**: `camelot` devuelve marcos y es **uno de los cuatro
    extractores de la campaña de los 616**. Declarándose capaz habría competido en el
    estrato de celdas combinadas —el que se sobremuestrea y se declara titular— cobrando
    ceros *como si hubiera competido y perdido*. Es el sesgo que `expresses_spans` existe
    para impedir, y LIMITS 35 ya dice que `camelot` tiene que salir `NO_APLICABLE` en el
    63% de las tablas.

    **Y yo lo propagué**: al escribir `FORMATOS_CON_SPANS` puse `dataframe` entre los que
    sí, copiándolo del complemento de una lista mala en vez de preguntarle al conversor.
    Dos tests míos afirmaban lo incorrecto por lo mismo.

    **Lo delató escribir el primer extractor** y preguntarse qué formato devuelve
    `pdfplumber`. No lo delató ningún guardián.

    **Arreglado en las dos mitades.** Las listas quedan `CON = {html, tei}` y
    `SIN = {markdown, dataframe, text}`; y `tests/unit/test_formatos_spans.py` **ejecuta
    los cinco conversores** sobre una tabla mínima y exige que lo que declaran coincida
    con lo que dice `types`. La lista deja de ser una copia que se puede quedar vieja y
    pasa a ser una afirmación comprobada. Con su control negativo: se restauran las
    listas viejas y el test se cae nombrando `dataframe`.

    Lo que queda sin cubrir: `tei` se da por capaz sin ejercitar una celda combinada de
    verdad —el test usa una tabla sin spans y sólo mira la bandera—, así que se comprueba
    que el conversor lo *declara*, no que lo *sepa hacer*.

99. **UN `page_range` INVÁLIDO ENTRA EN LA TASA DE FALLO DEL EXTRACTOR, Y ES UN ERROR
    DEL ARNÉS.** `Extractor.extract` **nunca lanza** —lo dice §7.2 y lo hace cumplir el
    aro `extract_no_lanza`—, así que un rango de páginas imposible (`(0, 5)`,
    `(7, 3)`) no puede salir por una excepción: sale como
    `Extraction(failed=True, failure_reason="provider_error")`.

    **El precio:** un error de quien LLAMA queda registrado como un fallo del
    extractor, y la tasa de fallo por extractor es un resultado publicado. Con dos
    extractores llamados con rangos distintos, la comparación se torcería.

    **Por qué no hay una causa mejor.** El enum de §6.9 es **cerrado** y sus ocho
    valores describen fallos del DOCUMENTO o del proveedor; ninguno dice «el llamador
    pidió algo imposible». Abrir el enum para esto sería peor: un enum con una casilla
    de «otro» deja de servir para contar.

    **Por qué hoy no contamina nada, medido:** la campaña de estructura de los 616
    llama con `page_range=None` —el documento entero— en el 100% de las unidades, así
    que el caso no puede dispararse. El rango existe para el muestreo por páginas de los
    documentos largos, que llega con L12b.

    **Cuándo hay que volver a mirarlo:** el día que una campaña use rangos. Entonces el
    corredor tiene que validarlos **antes** de llamar al extractor y contar un rango
    malo como error del plan, no como fallo del extractor.
    `tests/unit/test_pdfplumber.py::test_un_page_range_invalido_no_lanza_pero_queda_declarado_en_limits`

100. **LA BARRERA DE LOS CONVERSORES SIN VALIDAR CUBRE ESTE REPO, NO EL EXTRACTOR DE UN
    CLIENTE.** `tests/unit/test_sin_consumidor.py` recorre por AST **todo** `src/` y
    **todos** los `scripts/`, así que ve cualquier llamada literal a `from_markdown`,
    `from_tei` o `from_text_heuristic` en código de este repositorio.

    **Lo que cambió en L5:** ya existe `docbench_es.extract.registry`, o sea que los
    extractores se cargan por entry points. Eso **no** abre un agujero mientras vivan en
    `src/` —se recorren todos, se carguen como se carguen—, pero un extractor de un
    cliente vive en **su** paquete, y esta barrera no lo ve. Si ese extractor usara un
    conversor no validado, su número saldría igual y esta comprobación seguiría verde.

    **No es una regresión**: la barrera nunca cubrió código de terceros. Lo que cambia
    es que ahora hay una vía real por la que ese código entra, así que el límite se
    escribe en vez de darse por entendido.

    **Lo que sí protege el número publicado hoy**: los cuatro extractores de la campaña
    de los 616 son de este repo y están dentro del barrido.

101. **LA HUELLA DEL SELLO DE UNA CORRIDA NO VE EL CONTENIDO DE UN FICHERO SIN SEGUIR.**
    `extract.sello.arbol()` identifica el árbol con `commit`, `sucios` y una `huella` que
    es el `sha256` de `git status --porcelain` más `git diff HEAD`. Con eso, editar un
    fichero ya sucio —que **no mueve el recuento de sucios**— sí mueve la huella.

    **Lo que se le escapa:** el CONTENIDO de un fichero sin seguir. `git diff` no lo ve;
    `--porcelain` ve su nombre, así que un fichero nuevo se nota **al aparecer** y sus
    ediciones posteriores no. Un módulo nuevo sin `git add`, editado a mitad de campaña,
    pasaría por el mismo árbol.

    **Es el mismo hueco que `stop-gate.sh`** tiene con el fixture recién creado, y por la
    misma razón: lo que git no rastrea no tiene historia contra la que comparar. Y tiene
    la misma mitigación: `git add` antes de medir. `.claude/hooks/huella-puerta.sh` sí
    cubre el caso —incluye el contenido de los `.py` sin seguir— porque su trabajo es
    otro: comparar dos instantes seguidos, no describir un árbol en un fichero.

    **Cuándo importa de verdad:** poco, y hay que decirlo. La campaña de los 616 se corre
    sobre un árbol commiteado, donde `sucios` es 0 y el `commit` basta.

102. **LA PUERTA ESTUVO A 25,5 s —TRES VECES EL TECHO— DURANTE DIEZ COMMITS, Y NO LO VIO
    NADIE.** Medido en frío el 26 ago 2026, `uv run python scripts/medir_puerta.py
    --tandas 3 --por-tanda 3`, sello `b54ec82`, 14 CPU visibles, carga mediana 1,40:
    **n=9, mínimo 25.685, mediana 25.949, p90 27.611 ms**, σ=751, 0 descartadas. Techo
    8500 (ADR-0022): **margen −19.111 ms**.

    **No lo trajo el hito que lo encontró.** Medido en la misma máquina y en frío:
    `f89c5b6` (cierre de L4) da **mypy 3.576 ms** y `make fast` **9.399 ms**; `99be97d`
    —el commit ANTERIOR al primer extractor— ya daba **mypy 25.554 ms**. O sea que entró
    con B5-bis, que no fue un cierre de hito y por tanto **no re-midió la puerta**. El
    instrumento funcionaba: `medir_puerta.py` sale con código 1 cuando el p90 pasa del
    techo. Lo que faltó fue correrlo.

    **La causa, medida y no supuesta.** `mypy --strict src tests` parseaba **6.023
    ficheros**: 2.241 de `transformers`, 1.549 de `torch`, 146 de `huggingface_hub`, 140
    de `docling`. La cadena entra por una línea —`test_estimador_computo` →
    `estimar_computo` → `unidad_computo`, que importa `torch`, `docling` y `camelot`
    **dentro de funciones**, y mypy sigue esos igual que los de arriba—. `camelot` es
    quien arrastra `transformers`, lo cual **no se adivinó: se midió**, y de ahí la regla
    que queda escrita en `pyproject.toml`: la lista se decide mirando qué parsea mypy.

    **Y es la MISMA clase que ya mordió dos veces**: un resultado de la puerta que
    depende de si un extra está instalado. Con los extras, mypy analiza torch y compañía;
    sin ellos —CI— no. `follow_imports = "skip"` los deja en `Any`, que es exactamente lo
    que ya pasa en CI, así que **no relaja nada: iguala los dos entornos**.

    **Después del arreglo: mypy en frío 4.362 ms.** El número de la puerta entera va en
    `RESULTS.md` con su comando.

    **CERRADO EN EL MISMO HITO, y la corrección importa.** `make fast` registra ahora su
    duración y `guard-commit.sh` exige una medida **en frío** por debajo del techo para
    dejar commitear. En frío y no a secas: medido sobre `99be97d`, con la regresión
    dentro, `make fast` daba **30 259 ms en frío y 2 781 en caliente**, así que vigilar
    la duración de un `make fast` cualquiera **habría dejado pasar los diez commits
    igual**. Cuesta unos 7 s una vez por commit, `make frio`, y sus casos de rechazo
    tienen test con su control positivo delante.

    **Y lo que compara es el MÍNIMO de las corridas en frío de ese árbol, no la última**,
    porque la primera versión —la última— se descubrió inservible al usarla: seis
    corridas en frío del MISMO árbol dieron **6 367, 6 383, 6 819, 7 835, 9 236 y
    9 661 ms** sobre un árbol cuya serie de n=40 da p90 6 866. Una de cada tres se pasa
    del techo por contención de la máquina, y un aro que bloquea una de cada tres veces
    sin motivo se acaba sorteando. El mínimo es **optimista y lo declara**; lo que no
    puede esconder es lo único que este aro tiene que cazar: una regresión que multiplica
    TODAS las corridas.

    **Lo que sigue sin haber, y es lo que queda de este límite: nada vigila la
    TENDENCIA.** El aro compara contra un techo fijo. Entre la línea de corte y el cierre
    de L5 la puerta subió **852 ms de código** con 1 634 de margen: a ese ritmo, dos
    hitos más y el margen se acaba, y ningún guardián lo dirá hasta que ya haya pasado.

103. **`from_markdown` DEJABA EL MARCADO DENTRO DEL TEXTO DE LA CELDA — CERRADO EL MISMO
    DÍA, Y ANTES DE MEDIR NADA CON ÉL.** Medido sobre los cinco documentos del conjunto de
    conformidad, con `pymupdf4llm`, `uv run pytest tests/unit/test_canonical_texto_de_celda.py`:

    | | celdas con marcado | con `**` | con `<br>` |
    |---|---|---|---|
    | antes | **116 de 594 (19,5%)** | 86 | 54 |
    | después | **0 de 594** | 0 | 0 |

    Las mismas 594 celdas: no se perdió ni se inventó ninguna.

    **Qué era, y por qué no era un detalle de formato.** `from_html` lee el **texto del
    nodo** —un `<b>` desaparece solo y un `<br>` sale como espacio, comprobado— y
    `from_markdown` leía **la fuente**. Una **asimetría entre conversores del mismo repo**
    que aterrizaba sobre la nota del extractor: quien emite HTML cobraba texto limpio
    gratis y quien emite Markdown cobraba un cero en el 19,5% de sus celdas **por el
    formato de su salida**. Y la extracción era perfecta: quitando el marcado, las cadenas
    son idénticas a la verdad congelada.

    Es el mismo animal que un `expresses_spans` que miente —una comparación amañada sin
    querer— una capa más abajo, y **un sesgo sistemático entre familias**. Eso no se
    declara en un límite: se arregla.

    **Dónde fue el arreglo: en `from_markdown`, nunca en el extractor.** En el extractor
    sería normalizar a favor de uno. El principio que lo hace no arbitrario: **el conversor
    devuelve el TEXTO de la celda** — en Markdown `**x**` *es* el texto `x` con énfasis,
    igual que en HTML `<b>x</b>` *es* el texto `x`. No se añadió una normalización: se
    quitó una inconsistencia.

    **No es normalización, es parseo, y la distinción importa.** `NORMALIZACIONES` es el
    registro de lo que se le hace al texto **ya extraído**, igual para los cinco formatos.
    Sacar el texto del formato de origen lo hace cada conversor: `from_html` con un parser
    de HTML desde L1, `from_markdown` con la tabla `INLINE` desde hoy. La diferencia es que
    el de HTML es completo y el de Markdown es **un subconjunto declarado**, y por eso
    `INLINE` enumera lo que reconoce **y lo que no**.

    **Y lo que NO se toca, con su razón medida**: el énfasis pegado a una palabra
    —`a**b**`—, las etiquetas HTML que no sean `<br>`, y el énfasis cruzado. De los dos
    errores posibles, **no quitar marcado penaliza y se ve; quitar contenido corrompe y no
    se ve**. Sin el guardia que mira que un delimitador no toque a otro, `a**b**` salía
    `a*b*`: marcado a medias **y** contenido tocado.

    **Cómo se encontró y qué confirma.** `from_markdown` estaba en «Construido y NO
    VALIDADO» con L5 como su primer consumidor, y su primer consumidor le encontró un bug.
    Van **tres de los cinco conversores** —`from_html` en L2, `from_dataframe` con
    `pdfplumber`, `from_markdown` con `pymupdf4llm`— y **los tres los encontró el
    consumidor, ninguno un guardián**.

104. **`pymupdf4llm` HACE OCR SOBRE PÁGINAS QUE YA TIENEN CAPA DE TEXTO: ES COSTE, NO
    ALCANCE.** El censo lo resolvió, que era lo que faltaba.

    | medida | valor |
    |---|---|
    | páginas del corpus **sin** capa de texto | **0 de 10.298** |
    | pasadas de OCR de `pymupdf4llm` sobre los 12 del humo | **264 de 668 (39,5%)** |
    | pasadas de OCR de `pdfplumber` sobre los mismos 12 | **0** |
    | reloj sobre los 12 | 195,2 s contra 34,7 s — **5,6×** |

    Reproducir: `uv run python scripts/censo_capa_texto.py` para el censo, y la corrida
    del humo filtrando `OCR on page` para las pasadas.

    Instrumento del censo: **`pypdf`**, que `pyproject.toml` declara desde L3 como
    preparación de corpus y **no** como extractor del banco. Preguntarle a un concursante
    si el examen estaba en blanco no vale. Y su sesgo va en la dirección buena: `pypdf`
    extrae peor que `pymupdf`, así que «sin capa» es un **techo**; que dé **cero** cierra
    la pregunta sin margen.

    **Las dos explicaciones que había, y cuál era.** Si esas páginas no tuvieran capa de
    texto, `pymupdf4llm` estaría leyendo lo que `pdfplumber` no puede y la diferencia
    sería de **alcance**. La tienen todas. Así que es de **coste**, y de trabajo **peor**:
    el OCR de una página digital es peor que leer su capa.

    **Qué deja de ser un problema, y hay que decirlo.** El *cero falso* que temía la
    primera versión de este límite —`pdfplumber` perdiendo páginas escaneadas sin
    registrar fallo— **no se da en este corpus**: no hay páginas que perder. La decisión
    de contar la cobertura **por página** (`runs/l5/ponderacion.yaml`) sigue siendo la
    correcta por diseño, pero hoy no es lo que sostiene ninguna cifra.

    **Qué sigue siendo un problema.** La fila de coste de `pymupdf4llm` incluye OCR
    redundante, y **la fila no lo dice sola**. Va con su nota, o el 5,6× se lee como
    *«este parser es más lento»* cuando lo que pasa es *«este parser hace otra cosa
    además»*.

    **Lo que NO se hace: apagarlo.** `to_markdown` no expone una palanca documentada, y
    aunque la expusiera, apagarla sería configurar a un concursante. El banco mide la
    biblioteca **como viene**, y publica lo que hace.

    **Y el recuento no se puede hacer desde Python**: las líneas las escribe una capa en C
    directamente al descriptor 1, así que `contextlib.redirect_stdout` sólo capturó 3 de
    las 264. La cifra sale del log de la corrida, que es el instrumento honesto aquí.

105. **EL TECHO DE CI NO PUEDE SONAR: SU UMBRAL ESTÁ DENTRO DEL RUIDO DE SU PROPIO
    INSTRUMENTO.** Medido con los tres únicos puntos que hay, y **el tercero es el que lo
    dice**:

    | fecha | commit | ms | nota |
    |---|---|---:|---|
    | 2026-08-27 | `8b2def5` | 12.630 | primer punto |
    | 2026-08-27 | `804ee53` | 14.218 | primero con el instrumento definitivo |
    | 2026-08-27 | `59ccd53` | 18.044 | **la puerta NO cambió respecto al anterior** |

    Entre el segundo y el tercero sólo cambiaron comentarios, un documento y el paso que
    informa de los trabajadores: mismo código efectivo, **+3.826 ms**. Recorrido de la
    serie: **43%**. Y el techo de crecimiento de CI son **21.000 ms**, o sea un **16%**
    sobre el peor punto observado.

    **Un umbral del 16% sobre un instrumento cuyo ruido vale un 43% no distingue
    crecimiento de qué runner te tocó.** Es el límite 77 con otra cara —un guardián cuyo
    verde no significa lo que parece—, y esta vez sobre una máquina que **nadie controla**:
    el techo local vigila una máquina propia, en reposo y con protocolo; el de CI vigila
    una que cambia entre corridas y sobre la que no se puede imponer nada.

    **Se declara y NO se arregla ahora, y la razón es de prioridad, no de pereza.** El
    techo de CI es una alarma **secundaria**: la primaria es el aro local con su protocolo
    de mínimo en frío, y la **bloqueante** es el presupuesto de 90 s del manual, que sigue
    con 5× de margen. Las dos salidas conocidas —mediana de *k* corridas por push, que
    multiplica el tiempo de CI por *k*; o normalizar contra una carga de referencia
    cronometrada en el mismo trabajo, que es mecanismo nuevo— van a
    `docs/despues-de-la-tabla.md`.

    **Y los tres puntos no son un fracaso de la serie: son su primera medida.** Una serie
    que empieza midiendo su propio ruido empieza mejor que una que empieza midiendo el
    objeto y descubre el ruido cuando ya ha publicado.

106. **UN CONTROL PROTEGE CONTRA CONFUSIÓN DE VARIABLES; NO PROTEGE CONTRA UNA LÍNEA BASE
    QUE NO SE MIDIÓ.** Son dos aros distintos, y en el barrido de `-n` sólo había uno.

    El barrido estaba **bien diseñado**: orden rotado para que la deriva térmica no cayera
    siempre en el mismo brazo, predicción escrita antes, y el mismo árbol quieto. Y la
    predicción salió **falsa** de todas formas, por una razón que ningún control atrapa:
    **la línea base estaba supuesta**. El repo llevaba escrito que `-n auto` levanta un
    trabajador por CPU —14 aquí—, y `auto` levanta **7**. Nadie lo había comprobado.

    Con la línea base equivocada, el brazo «como está hoy» no era el que se creía, así que
    la comparación medía otra cosa desde antes de empezar. Un control cruzado, una
    aleatorización o más repeticiones **no habrían cambiado nada**: los tres protegen del
    ruido y de la confusión entre variables, y aquí el error estaba en la definición de una
    de ellas.

    **La regla que sale de aquí, y es el PASO 0 aplicado a las mediciones:** *antes de
    medir contra algo, mide qué es ese algo.* Es la misma forma que ya funciona con los
    conversores —*antes de escribir el extractor, pregúntale a su conversor qué declara*— y
    ha encontrado cuatro bugs en cuatro intentos.

    **Lo que queda sin cubrir:** ningún guardián lo hace cumplir. Es una regla de método,
    como *«primero el código, segundo el test, nunca el golden»*, y vive en el guion de
    quien mide. Un test no puede saber qué línea base debería haberse medido.

107. **QUÉ ORDENA EL ACUERDO DE RECUENTO: NO ESTÁ MEDIDO, Y LA LECTURA FÁCIL YA ESTÁ
    DESCARTADA.** El desglose por banda de páginas de L5 sale **no monótono** —100% con
    n=9, 30,6%, 20,2% y 46,9%—: el mínimo está en la banda intermedia y los documentos
    largos **recuperan**, con 28,7 tablas por documento, donde acertar el recuento exacto
    debería ser más difícil. Así que la banda de páginas **no es** el factor que ordena el
    acuerdo, y cuál lo es no se sabe.

    **El candidato, declarado y sin comprobar:** la **morfología de las tablas** en vez de
    la longitud del documento. Las de un presupuesto o un convenio de más de 50 páginas son
    grandes, regladas y de página completa, y ahí «¿esto es una tabla?» no admite duda; las
    de un documento de 11 a 50 son pequeñas y embebidas en prosa, y ahí la pregunta es
    genuinamente ambigua.

    **Cómo se decide, y con qué criterio escrito antes:** se cruza el acuerdo contra el
    **tamaño mediano de tabla en celdas** —`n_rows × n_cols` de la verdad derivada, mediana
    por documento— en vez de contra las páginas. Monótono deja el candidato en pie; tan no
    monótono como éste **lo descarta** y el factor sigue sin nombre. No hace falta volver a
    correr la campaña: `docbench report` ya deriva la verdad de los 616 documentos. Precio
    por analogía con el desglose por páginas, que es el mismo trabajo con otro eje: **menos
    de una hora**. El método, en [`docs/metrics.md`](docs/metrics.md).

    **Lo que NO se hace mientras tanto, y es el punto:** publicar el candidato como
    explicación. El 46,9% va sin explicar en [`RESULTS.md`](RESULTS.md) —*«se publica sin
    explicación en vez de con una inventada»*—, y un candidato con su cruce declarado es
    más honesto que una explicación, no un sustituto de haberlo medido.

108. **LA DIRECCIÓN DEL SESGO DE SUPERVIVENCIA NO ES PREDECIBLE, ASÍ QUE NO SE PUEDE
    CORREGIR: SÓLO EVITAR.** `runs/l5/emparejado.yaml` declaró el mecanismo **y su
    dirección** antes de ver un TEDS: un extractor que detecta mal falla el recuento en más
    documentos, ésos salen de su cuenta, *«cuanto peor detecta, más se le excluye, y mejor
    pinta lo que queda»*. La consecuencia comprobable es que al pasar al denominador común
    todas las notas bajan, y bajan más las de menos cobertura.

    **Medido en L5: dos de los cuatro deltas salen positivos**, y el más positivo es el del
    extractor de cobertura más baja —el que la predicción señalaba como el más inflado—. La
    tabla, en [`RESULTS.md`](RESULTS.md). Y la lectura contraria tampoco se sostiene: si la
    intersección fuera sin más «los documentos fáciles», subirían los cuatro, y dos bajan.

    **El mecanismo es real; lo que no era predecible es el signo.** Y eso es lo que
    convierte la cara a cara en un **denominador** en vez de un factor de corrección: un
    sesgo de dirección conocida se corrige con una fórmula; uno cuyo signo hay que mirar
    extractor por extractor sólo se evita midiendo a todos sobre el mismo conjunto.

    **Lo que sigue sin medirse, y es lo que hace de esto un límite:** *por qué* sube el que
    sube. La cara a cara pone a los cuatro sobre el mismo denominador y con eso basta para
    comparar, pero no dice qué tienen los 82 que hace subir a dos y bajar a otros dos. Sin
    eso, el delta de un extractor **no es extrapolable** a otra campaña ni a otro corpus:
    es un dato de ésta.

109. **LA PRIMERA TABLA DE L5 TAMPOCO ES REPRODUCIBLE EN UN CLON FRÍO, Y POR PARTIDA
    DOBLE.** Es el límite 74 un hito más adelante, y con un factor más. El comando que
    publica `RESULTS.md` —`uv run docbench report --campaign runs/l5/campana`— necesita
    dos cosas que no están en el repo: los **cuatro diarios de la campaña**, 143 MB de
    `.jsonl` que `.gitignore` deja fuera por peso, y **`runs/l3/docs`** —362 MB de PDF y
    XML—, porque la verdad se deriva en cada corrida en vez de guardarse.

    **Lo que sí es reproducible, y no es poco:** el aritmético. `report.nivel1`,
    `report.cara_a_cara` y `core` son puros y los cubre la suite, así que **sobre los
    mismos diarios** el informe sale idéntico —comprobado al añadir la columna `delta`:
    ninguna de las cifras publicadas se movió—. Lo que no se puede hacer en un clon frío
    es **conseguir los diarios** sin volver a correr las 2,30 h con el corpus delante.

    **Y lo que no se declara aquí es una promesa de arreglarlo.** Versionar 143 MB de
    diarios no cabe en un repo, y recortarlos a una muestra los haría dejar de ser la
    corrida que se publica. La salida conocida —los 20 documentos congelados de L7 y su
    tabla, que **sí** viajan en el repo— es lo que hace `make quickstart` reproducible, y
    ésa es la que este proyecto ya tiene planeada. Hasta entonces, quien quiera reproducir
    la tabla de L5 necesita esta máquina o rehacer la cosecha.

110. **UN CRITERIO PRE-REGISTRADO QUE NO NOMBRA LA COLUMNA QUE LO MIDE NO ES UN CRITERIO:
    ES UNA INTENCIÓN.** Y el fallo no lo caza la pre-registración, que es lo que lo hace
    un límite y no una anécdota.

    **Lo medido.** La deuda 7 de [`ESTADO.md`](ESTADO.md) escribió, antes de L5:
    *«L5 es el primero que puede subir el arnés en vez de bajarlo. Si no lo sube, deja de
    ser estructural y pasa a ser deterioro»*. Su tabla tiene **dos** columnas que se
    pueden llamar «el arnés»: un recuento y una fracción. En L5 fueron en direcciones
    **opuestas** —el recuento 166 → 208, la fracción 43,2% → 31,7%—, así que el criterio
    tiene una lectura que pasa y otra que falla, y **elegir la lectura ES elegir el
    criterio**, con los dos números ya delante.

    **Contra qué protege la pre-registración y contra qué no.** Protege contra elegir el
    criterio después de ver el dato. **No** protege contra un criterio con dos lecturas:
    ahí el dato llega antes que la decisión igualmente, sólo que la decisión se disfraza
    de interpretación. Es la forma del límite 106 —un control que protege de una cosa y
    se lee como si protegiera de todas— aplicada a la pre-registración en vez de a un
    experimento.

    **Lo que se hizo, y no es elegir la que salía bien:** el criterio se declaró
    **inválido para L5** y se publicaron **las dos lecturas** diciendo cuál falla. Y se
    dijo además que el texto **se inclina** hacia la fracción —*«en vez de bajarlo»* sólo
    tiene sentido si el referente venía bajando, y el recuento nunca bajó: 162, 166,
    166—, porque escudarse en la ambigüedad para no publicar el fallo sería la misma
    elección con otro traje.

    **La regla que sale, y su coste.** Un criterio pre-registrado nombra **la columna
    exacta y el comando que la calcula**. El de L6 ya está reescrito así en la deuda 7, y
    escribirlo obligó a que el comando existiera: `uv run python scripts/contabilidades.py`.
    Ese es el coste real de la regla — no es prosa más cuidadosa, es que **hace falta un
    comando por criterio**.

    **Lo que queda sin cubrir:** ningún guardián lo hace cumplir. Un test no puede saber
    si una frase en español tiene dos lecturas. Es una regla de método, como el PASO 0 del
    límite 106, y vive en el guion de quien pre-registra. Lo único mecanizable es lo que
    ya está hecho: que el comando que el criterio nombra **exista y diga la verdad**, y
    eso sí lo comprueba `tests/unit/test_recuentos.py`.

111. **EL TECHO DE LA PUERTA VIVÍA EN NUEVE SITIOS —OCHO DE ELLOS COPIAS VIVAS— Y SÓLO
    SE COMPROBABAN DOS. Y LOS DOS COMPROBADOS SE QUEDARON VIEJOS A LA VEZ.** Es la forma
    del límite 106 aplicada a una constante: un control protege contra que dos copias se
    separen; no protege contra que las dos estén viejas.

    | # | dónde vivía | quién lo comprobaba |
    |---|---|---|
    | 1 | `.claude/hooks/registrar-puerta.sh`, `TECHO=8500` | `test_aro_del_techo.py`, contra la 2 |
    | 2 | `scripts/medir_puerta.py`, `--techo` por defecto | idem, contra la 1 |
    | 3 | `tests/unit/test_aro_del_techo.py`, el **literal** en el `assert` | nadie: era el literal |
    | 4 | `.github/workflows/fast.yml`, `TECHO_MS` | **nadie**: un grep de su valor por `tests/` y `scripts/` daba cero |
    | 5 | la prosa de ADR-0022 | nadie |
    | 6 | `.claude/hooks/guard-commit.sh`, el `\|\| echo 8500` de reserva | nadie, y encima **fallaba abierto** |
    | 7 | `docs/metrics.md`, en presente y **con el valor de CI equivocado** | nadie |
    | 8 | `ESTADO.md`, tabla de decisiones, **idem** | nadie |
    | 9 | las órdenes `--techo N` de [`RESULTS.md`](RESULTS.md) | nadie, y **no es una copia viva**: es el comando de una medición ya hecha |

    **Ocho copias vivas y una histórica.** El primer censo de este límite decía **seis**, y
    el error iba **en la dirección que empequeñece el problema**: se escribió el mismo día
    en que se arreglaban las dos primeras, y contó las que se estaban tocando en vez de
    buscar las que no. Las 6, 7 y 8 salieron del escrutinio adversarial, no del censo.

    **La 6 es la peor de las nueve y no estaba ni en la cuenta:** `guard-commit.sh` leía el
    techo del hook y terminaba en `|| echo 8500`. Si la lectura fallaba, el guardián **se
    inventaba un techo y seguía en verde**. Un guardián que falla abierto es peor que no
    tenerlo, porque su verde se cree.

    **Lo que pasó, y es exactamente lo que el test no podía ver.** ADR-0022 fijó al cerrar
    L3 el techo de L4 en **9000 local y 21 000 en CI**. CI se movió a 21 000; el local se
    quedó en 8500 **en sus dos copias**, así que `_hook() == _instrumento() == 8500`
    siguió pasando **todo L5**. No se separaron entre ellas: se separaron **juntas** del
    documento que las fija. El docstring de ese test decía *«una copia sin comprobar es un
    bug esperando a que alguien mueva la otra»* — y el bug entró por el lado que sí
    comprobaba.

    **Y el hook atribuía mal quién lo hacía cumplir.** Decía que la coincidencia la exige
    `tests/unit/test_guardianes_por_glob.py`; la exigía `test_aro_del_techo.py`. Ese
    fichero **existe y hace otra cosa**, que es peor que si no existiera: quien comprueba
    que el fichero está ahí concluye que la afirmación es cierta. Es la clase de fallo que
    ese mismo fichero existe para cerrar.

    **Lo hecho, con su reparto:** una fuente única, [`.techos`](.techos). La **leen** el
    hook, `medir_puerta.py` y el workflow de CI, y los tres se comprueban **ejecutándolos**;
    **se comprueba contra ella** toda línea escrita en la forma canónica *«Techo vigente: N
    ms local · M ms en CI»*, por la regla R6 de `scripts/derivadas.py` y con su control
    negativo; y ni `test_aro_del_techo.py` ni el workflow llevan ya el literal.

    > **Tres cosas de este mismo párrafo eran falsas al escribirlo, y las encontró el
    > escrutinio adversarial del paso 4 el mismo día:**
    >
    > 1. **«`test_aro_del_techo.py` ya no lleva el literal».** Lo llevaba: `assert "25949"
    >    in razon and "8500" in razon`. Era la copia nº3 de esta misma tabla, declarada
    >    cerrada en la misma frase que la dejaba abierta.
    > 2. **«pasa a fallar cerrado».** El camino de fallo terminaba en `exit 1`, y un
    >    `PreToolUse` de Claude Code sólo bloquea con `exit 2` o con el JSON de denegación.
    >    O sea que decía «falla cerrado» y fallaba **abierto** — el mismo defecto que venía
    >    a arreglar, un nivel más abajo. `guard-frozen.sh` ya lo tenía bien.
    > 3. **El censo de seis se quedaba corto.** Había dos copias VIVAS más, en presente y
    >    con el valor de CI **equivocado**: `docs/metrics.md` y la tabla de decisiones de
    >    `ESTADO.md` publicaban *«20 000 en CI»* contra los 21 000 de la fuente. Las dos
    >    están ahora en forma canónica y las mira R6.
    >
    > Las tres tienen la misma forma: **declarar cerrado un agujero en el mismo texto que
    > lo describe**. Es lo que hace que este límite valga más que su arreglo.

    **Lo que queda sin cubrir, y se dice:** las órdenes `--techo N` de `RESULTS.md` **no
    se comprueban ni se reescriben**, y es deliberado — son el comando de una medición ya
    hecha, y cambiarlas al cambiar el techo falsificaría la reproducción de una serie
    pasada. **Una copia en prosa que no use la forma canónica sigue siendo invisible**, y
    no hay forma de arreglarlo con una expresión regular: para un `grep`, «el techo es
    8500» en presente y «el techo era 8500» de una nota histórica son la misma cadena. Y
    **ningún guardián obliga a re-justificar el techo a tiempo**: R6 comprueba que las
    líneas vivas coincidan con la fuente, no que alguien haya hecho las 40 corridas. Eso
    sigue siendo un paso de `/cerrar`, o sea una lista en markdown.

112. **EL TITULAR DE L5 SE PUBLICÓ CON LA ETIQUETA DE OTRA CUENTA, Y NINGÚN GUARDIÁN
    PODÍA VERLO PORQUE TODOS LOS FIXTURES ESTABAN EN EL PUNTO CIEGO.** Es la decisión B3
    —`NO_APLICABLE` no es cero— rota un nivel más arriba: aquí lo que se convirtió en
    desacuerdo no fue un cero, fue **un documento entero**.

    **Lo medido.** El titular decía *«sólo en 82 de los 338 documentos los cuatro
    coinciden en CUÁNTAS TABLAS HAY»*. Los cuatro coinciden en el recuento en **103**. El
    82 era la intersección de los que **PUNTUARON**, que exige además que alguna tabla del
    documento sea evaluable; los **21** de diferencia son documentos donde todos acertaron
    el recuento y al menos uno no pudo evaluar ni una tabla —la verdad trae celdas
    combinadas y él no expresa spans, regla de oro 4—. La misma confusión falseaba dos
    celdas de la tabla por bandas: 46 y 12 donde son 56 y 23.

    **Por qué ningún test lo cazaba, que es la parte que hay que aprender.** Los fixtures
    de `tests/unit/test_nivel1.py` —`PERFECTA`, `OTRA`, y las tablas de `_tabla()`— **no
    tienen ni una celda combinada**. En ese mundo, «acertar el recuento» y «puntuar» son
    literalmente el mismo conjunto, así que **ninguna aserción posible sobre esos fixtures
    podía distinguirlos**. No es que faltara un test: es que faltaba un **caso** en los
    datos de prueba, y un caso que falta no deja hueco visible en ninguna cobertura.

    **Lo hecho:** `CaraACara` publica ahora las dos intersecciones —`acuerdo_de_recuento`
    y `documentos`— con su diferencia (`no_aplicables`) como número publicado; el informe
    imprime las dos y dice que no son la misma; y entra el fixture `COMBINADA`, que existe
    **sólo** para que los dos conjuntos puedan diferir, con tres tests que lo exigen.

    **Lo que queda sin cubrir:** ningún guardián comprueba que un fixture cubra el espacio
    de casos que su módulo distingue. Es la misma familia que el límite 60 —lo que no se
    puede verificar es si el control es *fuerte*— y aquí con una vuelta de tuerca: el
    control era fuerte y el **dato** era ciego. Lo único que se puede hacer es lo que se ha
    hecho: cuando una distinción se descubre, entra su caso en el fixture y no sólo su
    aserción.

    **Y lo encontró un escrutinio adversarial, no un test.** Es la tercera vez en este
    repo —L1 con `holes`, L3 con los sellos, y ésta—, y las tres veces leyendo, no
    ejecutando.

113. **EL TITULAR DE L5 ES UNA FUNCIÓN DEL PANEL Y SÓLO SABE BAJAR: DOS VALORES CON
    PANELES DISTINTOS NO SON COMPARABLES.** Escrito el 28 ago 2026, **antes de que entre
    el quinto extractor** y por tanto antes de que el número se mueva. Después sería
    explicar una caída ya publicada.

    **La monotonía, con la palabra.** *«En 103 de 338 documentos los extractores coinciden
    con la referencia en cuántas tablas hay»* es una **intersección sobre tantos conjuntos
    como extractores tenga el panel**. Añadir uno **sólo puede bajarlo**: un documento que
    estaba dentro sigue exigiendo que acierten los cuatro de antes, **más el nuevo**. La
    condición se endurece y el conjunto encoge. **Es monótono por construcción, no por
    calidad.**

    **Lo que esto impide, y es lo que hace que sea un límite y no una curiosidad.** L5
    cierra con **cuatro** y los otros entran de uno en uno con `/extractor` (ADR-0046).
    Cuando entren, el titular **bajará**. Una serie con los dos valores se leería como que
    el corpus empeoró o como que la extracción va peor, y **sería la misma clase de fallo
    que este hito acaba de corregir** —un número con la etiqueta de otra cuenta— sólo que
    **diferido**: el error no estaría en el número de hoy sino en la comparación de mañana,
    cuando nadie tenga delante el contexto para verlo.

    **Las tres cosas que lo sostienen, y ninguna es una nota al pie:**

    | dónde | qué |
    |---|---|
    | la **etiqueta** | «N de 338 **sobre el panel de K**, con sus nombres». Sin panel, el número está incompleto |
    | el **instrumento** | `report.tables` imprime el panel y la frase de la monotonía; `runs/l5/informe.json` lo lleva en `acuerdo.panel`. Lo fija `tests/unit/test_tabla_nivel1.py` |
    | la **regla** | `runs/l5/emparejado.yaml`, bloque `el_titular_depende_del_panel`, con su fecha |

    **La única comparación legítima entre paneles**, y existe: recalcular el panel viejo
    sobre la corrida nueva. Se puede porque los diarios están y el aritmético es puro — es
    la misma promesa que protege «el núcleo se puede reejecutar sobre extracciones viejas».
    Lo que **no** vale es una flecha entre dos números con paneles distintos.

    **Lo que esto NO dice:** que el número no sirva. Es el titular del hito y dice cuánta
    base común hay para comparar **en este panel**. Lo que no admite es la flecha.

    **Y lo que queda sin cubrir:** ningún guardián impide escribir esa flecha. `derivadas.py`
    comprueba que las cifras publicadas salgan de `informe.json`; no puede saber si dos
    cifras de dos informes distintos se están comparando en una frase. Es una regla de
    método, como el límite 110, y vive en el guion de quien escribe la serie.

114. **UN NÚMERO PUBLICADO CON DOS REDONDEOS DISTINTOS NO SE LEE COMO UN ERROR: SE LEE
    COMO DOS MEDICIONES.** Y si las dos caen dentro de la incertidumbre declarada, no hay
    nadie a quien le chirríe. Escrito el 28 ago 2026, al construir la portada.

    **Lo medido.** El error del estimador de L5 estaba publicado **seis veces**: `+74,5%`
    en [`RESULTS.md`](RESULTS.md) tres veces, en la tabla de estimadores de
    [`ESTADO.md`](ESTADO.md) y en [`docs/metrics.md`](docs/metrics.md); `+74,6%` en la
    fila de L5 de `ESTADO.md`, escrita en el commit de cierre. **Ninguna de las seis salía
    de un fichero.**

    **No eran dos mediciones: era la misma división con el dividendo redondeado y sin
    redondear.** `scripts/poblacion_l5.py` emite **14.439,4 s**; publicarlo como «4,01 h»
    —que es como lo imprime, con dos decimales— y volver a segundos da 14.436, y ese
    redondeo, y sólo ése, baja el cociente de 74,558% a 74,516%. El divisor **ya iba sin
    redondear**: 8.272 s y no 2,30 h. Redondearlo también lo mueve —con 2,30 h saldría
    **+74,4%**, y con los dos redondeos **+74,3%**—, así que el número tenía cuatro
    lecturas defendibles y se publicaron dos.

    | operandos | cociente | publicado |
    |---|---:|---|
    | 14.439,4 s / 8.272 s | 74,558% | **+74,6%** — lo que emite el instrumento |
    | 14.436 s / 8.272 s | 74,516% | +74,5%, cinco veces |
    | 14.439,4 s / 8.280 s | 74,389% | +74,4%, nunca |
    | 14.436 s / 8.280 s | 74,348% | +74,3%, nunca |

    **Y lo que lo hace un límite y no una errata es la parte de la incertidumbre.**
    `docs/metrics.md` ya declaraba la resolución del pre-registrado: dos decimales de
    hora, ±18 s, **±0,2 puntos**. Las dos cifras publicadas distan 0,1 puntos, o sea que
    **las dos caían dentro de lo declarado**. Una discrepancia que cabe dentro de la
    barra de error no llama la atención de nadie: se lee como ruido, no como un fallo.
    Declarar la resolución es necesario y **no** basta — lo que hace falta es que la
    división se haga una sola vez, y no con la cifra publicada.

    **La dirección del error también importa, y va dicha:** redondear el dividendo
    empequeñece el fallo del estimador. La copia mala era la **optimista**, y era la que
    estaba cinco veces.

    **Lo hecho.** El número vive en [`runs/l5/reloj.json`](runs/l5/reloj.json), que emite
    `uv run python scripts/error_del_estimador.py --escribir`, con los dos operandos —el
    derivado y el medido, marcados como tales—, sus dos fórmulas y la cifra que **no** es
    el reloj: la suma de los `coste_ms` del informe, 8.267,5 s, que es `perf_counter`
    dentro de `extract` y daría **+74,7%**. La regla **R8** de `scripts/derivadas.py`
    compara contra ese fichero las **seis copias vivas y los ocho sitios donde aparece
    alguno de sus dos operandos**, con su control negativo en
    `tests/unit/test_barreras_documentos.py`; y un cuarto test recorre el instrumento
    entero y compara, para que el fichero tampoco pueda quedarse rancio.

    **Es el límite 111 aplicado a un porcentaje** —una cifra en N sitios comprobada en
    ninguno— y hereda su hueco declarado: R8 enumera las copias **por patrón**, así que
    una copia escrita de otra forma sigue siendo invisible. Lo que R8 sí hace, y R6
    también, es **decir «no aparece»** cuando un patrón deja de casar, en vez de callarse
    en verde.

    **Lo que queda sin cubrir.** El dato medido —8.272 s de `time`, n=1— **no se puede
    recomputar**: la campaña cuesta 2,30 h y no se vuelve a correr para mirarlo (límite
    109). Vive como constante declarada en `scripts/error_del_estimador.py`, con su
    método y su resolución, y ningún guardián puede comprobar que sea cierto. Lo único
    que se garantiza es que hay **una sola copia** y que todo lo demás se deriva de ella.

115. **LA PORTADA ELIGE CUATRO LÍMITES DE 115 Y CUATRO PUERTAS DE TREINTA Y DOS, Y ESA
    SELECCIÓN NO LA COMPRUEBA NADIE.** Escrito el 28 ago 2026, el día que entra la
    portada, y en el mismo commit que la construye.

    **Lo que sí está cubierto.** Ni una cifra de `docs/index.html` está tecleada: las 70
    salen de [`runs/l5/informe.json`](runs/l5/informe.json) o del censo del repo, van
    marcadas con `data-cifra` y las compara la regla R9 de `scripts/derivadas.py` **en
    tres direcciones** —la que no cuadra, la que falta y la que sobra— con su control
    negativo y su mutante. El **valor** de cada número está atado.

    **Lo que no lo está: la SELECCIÓN.** Qué cuatro límites se enseñan y cuáles no, qué
    cuatro puertas, qué bandas se destacan y qué frase se pone en el `caption` en vez de
    debajo. Son decisiones editoriales, tienen efecto sobre cómo se leen los números de
    arriba —ése es literalmente el criterio con el que se eligieron— y **ningún guardián
    puede evaluarlas**: no hay contra qué comparar «esto es lo que había que enseñar».

    **Y la dirección del sesgo es previsible, así que se dice.** Quien escribe una portada
    elige, sin querer, los límites que sabe explicar y las puertas que sabe defender. Los
    cuatro que están son el corpus, el error de la verdad, la tasa de tabla no presente y
    las familias que faltan; los que **no** están incluyen los que hablan de la propia
    portada —éste— y los 110 restantes. Un lector que se quede en la página se lleva
    **cuatro** y creerá que son los que importan.

    **Lo único que se hace, porque es lo único que se puede hacer:** decirlo en la propia
    página —«los que más cambian cómo se leen los números de arriba», que declara el
    criterio y por tanto que hubo uno— y poner `LIMITS.md` entero a un clic, con su
    recuento derivado al lado. Es la misma forma que el límite 60: lo que no se puede
    verificar es si el control es **el adecuado**, y entonces se publica el criterio en
    vez del veredicto.

    **Lo que NO es este límite:** una promesa de arreglarlo. No hay forma de derivar una
    selección editorial de un fichero, y fingir que la hay —«los cuatro más citados»,
    «los cuatro más recientes»— sería sustituir un criterio declarado por uno automático
    y peor, con la apariencia de estar medido. Ver también el límite 77: una protección
    que cubre una clase y no dice cuál se lee igual que una que las cubre todas.

116. **EL TECHO DE LA PUERTA SE FIJÓ CON UN MARGEN MÁS PEQUEÑO QUE LO QUE CUESTA UNA
    SOLA FUNCIONALIDAD, Y EL «INCREMENTO PROYECTADO» DE SU FÓRMULA NO ESTÁ MEDIDO.**
    Escrito el 29 ago 2026, al romperlo la primera cosa que entró después de fijarlo.

    **Lo medido.** Al cerrar L5 el techo bajó a **8200** con un p90 de **7845**: margen
    **355 ms**. La primera funcionalidad que entra después —la portada, con su paquete de
    siete módulos, tres scripts, dos reglas de `derivadas.py` y 18 tests— cuesta, medida
    **en parejas alternas contra un `git worktree` de `188a59f`** y con n=5, **+253 ms de
    `mypy` y +606 ms de `pytest`**. O sea que **el techo suena sin que nadie haya escrito
    una línea lenta**, que es la forma más rápida de enseñar a ignorar el color — lo mismo
    que el límite 105 dice del techo de CI, ahora en el local.

    **Y no es que la máquina se haya vuelto lenta**, que fue la primera lectura y era
    falsa: `372b82f` medido hoy da mediana **7656 ms** contra los **7722** que publicó
    entonces. **El árbol viejo reproduce.** Lo que engañó fue comparar listas de ficheros
    en vez de árboles, con n=4 y una máquina que da paradas de 27 s. La corrección está en
    [`RESULTS.md`](RESULTS.md) con las dos series enteras.

    **Dónde está el hueco, que es lo que lo hace un límite.** La fórmula de ADR-0022 es
    `p90 medido + incremento proyectado + una desviación`. El primer término se **mide**
    con 40 corridas y el tercero también. **El segundo es un juicio**, y nunca se ha
    medido cuánto cuesta un hito: se estimó en unos 240 ms al cerrar L5 y la primera
    entrada real vale **más del doble**. Un techo cuyo margen sale de un término no medido
    no acota el crecimiento: acota lo que a alguien le pareció que iba a crecer.

    **Lo que este límite NO dice:** que el techo sobre. Hizo exactamente lo que tenía que
    hacer —sonar—, y su paso 1 pagó: `--durations` encontró un defecto real, `paginas()`
    reparseando 520 KB **cinco veces**, y arreglarlo recuperó 418 ms de la mediana. Lo que
    no acota es el **término del medio**.

    **Lo que queda sin hacer, con su método y sin fecha.** Medir el incremento por hito en
    vez de proyectarlo: la serie ya existe —L3, L4 y L5 tienen su p90 con n=40 y su sello—
    y lo que falta es **atribuir** cada salto a lo que entró, que es lo que esta medición
    hace por primera vez y para una sola funcionalidad. Con tres puntos el término deja de
    ser un juicio. **Mientras tanto no se sube el techo**: ADR-0022 lo prohíbe después de
    romperlo, y elegir entre sus tres concesiones es un paso de `/cerrar`, no la salida
    cómoda del trabajo que acaba de romperlo.

117. **LA MISMA FORMA DE DEFECTO VA POR LA TERCERA, Y LAS TRES SE ENCONTRARON DESPUÉS DEL
    ROJO.** Cerrado con un aro el 29 ago 2026, después de tres apariciones y **dos
    anotaciones**.

    | Hito | Dónde | Veces | Cuánto valía |
    |---|---|---:|---|
    | L4 | `corregir_fixtures_l4.py`, `pdftotext` sobre los mismos bytes | **8** | 0,69 s → 0,36 s |
    | L5 | `huerfanos.reparto()`, el AST de `tests/` una vez por documento | **9** | 0,79 s → 0,17 s |
    | L7 | `censo_paginas.paginas()`, 520 KB de JSON por llamada | **5** | mediana de la puerta 8500 → 8082 |
    | L7 | `censo_tablas.tablas()`, mil XML donde bastaba leer el censo | **1.000** | 0,27 s → 4,2 ms |

    **La forma, que es la misma las cuatro veces:** una función pura que lee o parsea algo
    caro, llamada una vez por elemento de un bucle, sin cachear. Y **el consumidor
    midiendo donde bastaba leer**, que es la variante del cuarto.

    **Lo que lo convierte en límite y no en anécdota es que estaba anotado y no exigido.**
    `scripts/huerfanos.py` lleva escrito desde L5 *«cacheada, y por la misma razón que el
    `lru_cache` de `pdftotext` en L4»*. La recurrencia estaba **escrita dos veces y
    comprobada cero**. Es la frase de ADR-0022 sobre sí misma: *se hizo una vez, funcionó,
    y no se convirtió en paso*.

    **Y las cuatro las encontró `--durations` DESPUÉS de que el techo se pusiera rojo.**
    Un diagnóstico post mortem cuatro de cuatro es el daño hecho cuatro veces: el rojo
    llega cuando el trabajo ya está escrito y la atención está en otra parte.

    **Lo hecho: `scripts/lecturas.py`**, un contador que envuelve `Path.read_text`,
    `Path.read_bytes` y `subprocess.run` durante **una llamada** a un instrumento y anota
    `(qué, argumento)`. Si el mismo argumento sale dos veces, es esto y sale por su
    nombre. El alcance es **una llamada y no la suite**, que es la única definición que
    significa algo: dos tests que leen el mismo fixture no comparten nada.

    **Su control negativo no es un bucle de juguete: es el defecto real revivido.** El
    test le quita la caché a `censo_paginas` —exactamente como estaba— y exige que el
    contador vea las cinco lecturas del manifiesto dentro de una llamada a `reloj()`. Sin
    eso, *«el aro habría cazado los tres»* sería una afirmación sobre el pasado que nadie
    ha comprobado.

    **Lo que NO cubre, y son tres cosas:** los instrumentos que no estén en su tabla —el
    aro no descubre, mira—; los que necesitan datos fuera de git, entre ellos **el caso de
    L4**, que no se puede correr en la puerta, así que su forma queda cubierta y su caso
    no; y una lectura repetida **barata**, que sale igual. Esto último es a propósito: el
    umbral es «dos veces», no «dos veces y caro», porque *caro* depende de la máquina y
    *dos veces* no.

118. **UN TEST QUE DEGRADA EN SILENCIO ES PEOR QUE UN TEST ROTO, Y VA POR LA CUARTA.**
    Cerrado con una puerta el 29 ago 2026.

    **Lo medido.** `censo_tablas.tablas()` recorría `runs/l3/docs` —362 MB que el repo no
    versiona— y **devolvía `{}` cuando no estaban**. Sin corpus no fallaba: `poblacion_l5`
    repartía los 1.000 documentos como si ninguno tuviera tabla y emitía **otra
    predicción**. El test que la comprobaba habría pasado **en verde en un clon frío
    afirmando un número falso**.

    > El roto se ve. Éste afirma algo distinto de lo que dice afirmar, y lo afirma en
    > verde, que es el color que nadie audita.

    **Y es un patrón:** el barrido de referencias que medía la máquina de quien lo
    escribió, el `mypy` que no veía los huérfanos, el límite 109 con la primera tabla de
    L5 irreproducible en un clon, y éste.

    **Lo hecho: `scripts/fuera_de_git.py`**, una puerta única con las cinco raíces
    declaradas y su razón, que **lanza** con esa razón dentro en vez de devolver un vacío.
    `referencias.ARTEFACTOS` sale de esa misma lista —eran dos listas de lo mismo con
    redacciones distintas, el límite 111 en pequeño—. Y el consumidor que provocó todo
    dejó de necesitar el corpus: lee el censo **publicado y versionado**.

    **El criterio de quién debe pasar por la puerta se DERIVA, no se escribe a mano:** un
    script al que llega algún test puede degradar en verde, y ésos pasan; un huérfano no
    puede, porque nadie lo corre sin mirar su salida. Lo cruza `huerfanos.reparto()`, así
    que el día que un test alcance a uno de los seis declarados huérfanos, la puerta se
    pone roja. **Una tabla de excusas que nadie vuelve a cruzar con la realidad envejece
    igual que el número que vino a vigilar.**

    **La excepción, que enseña dónde está el límite:** `comparar_verdad.py` sí lo alcanza
    un test y **no** pasa por la puerta, porque su huella está **congelada** en el
    re-sello de L4 y tocarlo pone rojo `test_congelados_l4`. No le hace falta: su lectura
    lanza sola. Lo que la puerta le añadiría es la razón, no el fallo.

    **Lo que NO cubre.** El censo reconoce a un lector por **cómo nombra la raíz**, así
    que uno que la componga de otra forma es invisible — es el hueco declarado del límite
    111 aplicado aquí. Y quedan **nueve** ficheros fuera de la puerta: seis huérfanos y
    los **tres de la CLI**, que reciben la ruta de quien llama y fallan con su código de
    salida (§11). Los nueve van enumerados uno a uno, con su razón, en
    `tests/unit/test_datos_fuera_de_git.py`.

119. **LA ÚNICA EVIDENCIA DE REPRODUCIBILIDAD DEL REPO ES SOBRE EL ESTADÍSTICO QUE NO
    DECIDE.** Escrito el 29 ago 2026, restando dos números que llevaban cuatro días
    publicados uno encima del otro.

    **Lo medido, y no hizo falta medir nada nuevo.** `RESULTS.md` publica desde el 24 ago
    2026 dos series de 40 corridas del mismo día, bajo el título *«el protocolo reproduce
    a 10 ms»*. La sección demuestra lo que dice y lo argumenta bien — **sobre la
    mediana**. En esa misma tabla:

    | | serie A | serie B | diferencia |
    |---|---|---|---|
    | mediana | 6198 | 6208 | **10** |
    | p90 | 6262 | 6327 | **65** |

    **Las dos series difirieron 10 ms en la mediana y 65 ms en el p90.** Y **el techo se
    compara contra el p90**, no contra la mediana. La resta de la segunda fila **no se
    hizo nunca**.

    **Qué invalida, en concreto.** El 29 ago 2026 este repo publicó *«p90 8231 contra un
    techo de 8200: sigue sonando, y por 31 ms»*. **31 es menos de la mitad de 65.** No es
    que la alarma no suene: es que **con una sola serie no se puede afirmar que suene**.

    **Y tiene causa mecánica, no sólo aritmética.** El p90 de n=40 se estima con unas
    **cuatro** observaciones de la cola; la mediana usa las **cuarenta**. Un estimador de
    cola con cuatro puntos se mueve más que uno central con cuarenta, y eso no se arregla
    mirándolo mejor. **El proyecto eligió el estadístico conceptualmente correcto y validó
    el estable.** Son dos, y sólo uno tenía aval.

    **Esto NO es el límite 116**, aunque vivan pegados. El 116 dice que **el término del
    medio** de la fórmula del techo —el incremento proyectado— no está medido, y es
    verdad. Esto va debajo: **el primer término tampoco tiene medida de reproducibilidad
    en la forma en que se usa para decidir.**

    **Lo hecho, y es la mitad barata:** [ADR-0048](docs/adr/0048-el-techo-se-decide-con-dos-series.md)
    pasa el protocolo del cierre a **dos series de 40** —40 minutos una vez por hito
    contra los 20 de antes— y da el techo por roto **sólo si los dos p90 lo pasan**. El
    caso del medio —una por encima y otra por debajo— **no es verde y no es rojo**: sale
    con **código 3**, `NO CONCLUYENTE`, porque devolver el código del verde sería
    contestar con una moneda al aire una pregunta que el instrumento sabe que no ha
    resuelto. Lo prueba `tests/unit/test_dos_series.py` en las tres direcciones, y **R10**
    (`scripts/regla_reproducibilidad.py`) ata cada copia publicada de esa resta a la tabla
    de la que sale — incluidas las de los docstrings de los dos scripts, porque la sexta
    copia del error del estimador ya enseñó que el sitio da igual.

    **Lo que este límite NO dice, y son tres cosas.** No dice que la reproducibilidad del
    p90 *sea* 65 ms: **con n=2 no se publica una tasa, se publica el par**, y lo que se
    afirma es que *estas dos* series difirieron eso. No dice que haya que gatear sobre la
    mediana — **escondería la cola, que es justo lo que un techo existe para vigilar**; la
    respuesta a un estimador ruidoso es más evidencia sobre él, no cambiar a otro que mira
    otra cosa. Y no autoriza a mover el techo: sigue en **8200**, y ADR-0022 prohíbe
    subirlo después de romperlo.

    **Lo que queda sin hacer, con su método y sin fecha.** Medir de verdad la
    reproducibilidad del p90, que exige varias series y su intervalo. La cura ya no cuesta
    nada aparte: **cada cierre deja ahora dos p90 del mismo árbol el mismo día**, así que
    la serie se construye sola hito a hito. Con tres o cuatro puntos deja de ser una
    observación — y es el mismo dato que el límite 116 pide por otro camino.
