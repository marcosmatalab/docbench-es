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
