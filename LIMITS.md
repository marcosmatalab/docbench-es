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
