## Nivel 1 · estructura de tablas · L5

**ESTO NO ES UN RANKING.** No ordena a nadie y no se puede leer como si lo hiciera.

**Por qué no.** Poner a todos sobre el mismo denominador —que es lo que hace la cara a cara de abajo— es **necesario y no suficiente**: decir «A es mejor que B» exige la comparación pareada con su potencia, o sea McNemar y bootstrap agrupado por documento (ADR-0009), y eso es **L6**. Elegir aquí un umbral sería inventarse una potencia sin calcularla.

**Y por eso las filas van en orden alfabético, nunca por nota** —ni ésta ni la cara a cara—: ordenar por nota *es* ordenar, diga lo que diga el texto de al lado.

**Lo que esta tabla sí dice**, cada cosa con su denominador en la misma fila: en cuántos documentos cada extractor coincide con la referencia en **cuántas tablas hay**, sobre qué proporción de tablas es evaluable, **cuántas veces falla y por qué causa**, y cuánto tarda. La ordenación llega en L6.

**Y no es lo que hace el campo.** ExtractBench ordena catorce sistemas y PulseBench-Tab nueve, los dos **sin un solo intervalo de confianza**; comprobado con su comando y su cita en [`docs/quien-publica-los-bancos.md`](docs/quien-publica-los-bancos.md).

### Procedencia · los dos árboles

**Extracciones** — corrida de `819c06f`, 0 ficheros sin commitear, huella `01ba4719c80b6fe9`, empezada 2026-08-27T10:39:57.893229+00:00.

**Puntuación** — informe de `93ae494`, 22 ficheros sin commitear, huella `9d043629aace74a1`.

**Qué discrimina cada campo**, porque no es lo mismo y verlos juntos hace creer que la huella identifica el árbol: `commit` dice **qué** commit y es el único que separa un árbol limpio de otro; `sucios`, **cuántos** ficheros sin commitear; y `huella` separa **limpio de sucio** —y, si está sucio, qué diff—, así que sobre cualquier árbol limpio vale siempre `01ba4719c80b6fe9`. **Dos huellas iguales no dicen que sea el mismo árbol: dicen que los dos están limpios.**

**NO son el mismo árbol**, y se dice en vez de callarlo: `commit`: corrida '819c06f' → informe '93ae494' · `sucios`: corrida 0 → informe 22 · `huella`: corrida '01ba4719c80b6fe9' → informe '9d043629aace74a1'.

Eso **no invalida la tabla**: invalida atarla a un commit solo. Las extracciones son del árbol de la corrida y la puntuación es del árbol del informe, y quien quiera reproducir esto necesita **los dos**. Para reproducirla exacta, el aritmético vive en `report.nivel1` y `core`, que son puros: se vuelve al commit del informe y se relanza `docbench report` sobre los mismos diarios.

| extractor | versión | TEDS | TEDS-S | F1 celda | TEDS/pág. | cobertura evaluable | acuerdo de recuento | +/- tablas | fallos | latencia mediana |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `camelot` | 2.0.0+lattice+ad1 | 0,8684 | 0,8701 | 0,9343 | 0,8987 | 29,6% | 40,8% | +684/-22 | 0 | 854 ms |
| `docling` | 2.121.0+2h+ad1 | 0,9053 | 0,9150 | 0,8547 | 0,8984 | 38,0% | 40,5% | +671/-28 | 0 | 3613 ms |
| `pdfplumber` | 0.11.9+ad1 | 0,8699 | 0,8701 | 0,9425 | 0,9017 | 29,6% | 40,5% | +709/-22 | 0 | 404 ms |
| `pymupdf4llm` | 1.28.2+ad1 | 0,8936 | 0,9134 | 0,7372 | 0,9541 | 23,6% | 33,7% | +618/-111 | 0 | 2363 ms |

### Cara a cara · el mismo denominador para todos

**82 de 338** documentos (24,3%): aquéllos en los que **todos** los extractores PUNTUARON.

**Y ése no es el acuerdo de recuento, que son 103 de 338 (30,5%).** Los 21 de diferencia son documentos donde **todos acertaron el recuento** y al menos uno no pudo evaluar ni una tabla: la verdad trae celdas combinadas y él no expresa spans, así que sale `NO_APLICABLE` por la regla de oro 4. Publicarlos como desacuerdo sería la decisión B3 rota un nivel más arriba — «no se pudo medir» leído como «se midió y salió mal».

**Alfabético, no por nota.** El mismo denominador hace la comparación posible; no la resuelve.

| extractor | TEDS sobre la intersección | TEDS sobre su conjunto | delta |
|---|---:|---:|---:|
| `camelot` | 0,8581 | 0,8684 | -0,0104 |
| `docling` | 0,9354 | 0,9053 | +0,0301 |
| `pdfplumber` | 0,8599 | 0,8699 | -0,0100 |
| `pymupdf4llm` | 0,9375 | 0,8936 | +0,0440 |

**Por qué hace falta esta segunda cuenta.** La de arriba tiene un sesgo de supervivencia declarado (`runs/l5/emparejado.yaml`): un extractor que detecta mal falla el recuento en más documentos, ésos salen de SU cuenta, y su nota acaba calculada sobre **otro subconjunto, elegido por él mismo**.

**Y la columna `delta` es la razón por la que esto es un DENOMINADOR y no un factor de corrección.** `emparejado.yaml` declaró la dirección del sesgo antes de medir —cuanto peor detecta, mejor pinta lo que queda, o sea deltas negativos y más negativos cuanto menor la cobertura—. El signo que sale en esa columna es el medido, y se publica coincida o no con lo declarado: un sesgo de dirección conocida se corregiría con una fórmula; uno cuyo signo hay que mirar extractor por extractor sólo se evita midiendo a todos sobre el mismo conjunto.

**El delta no es una tercera medida**: es la resta de las dos columnas de al lado, o sea las mismas puntuaciones por documento con dos denominadores.

**Y este 103 es un dato en sí**: dice en cuántos documentos los 4 extractores coinciden con la referencia en algo tan básico como CUÁNTAS tablas hay.

**Y DÓNDE está el desacuerdo**, que es lo que lo convierte en diagnóstico:

| páginas | población | coinciden los 4 en el recuento | acuerdo |
|---|---:|---:|---:|
| una página | 9 | 9 | 100,0% |
| 2-10 | 183 | 56 | 30,6% |
| 11-50 | 114 | 23 | 20,2% |
| >50 | 32 | 15 | 46,9% |

**Esto no es un ranking.** Mismo denominador es necesario y no suficiente: decir «A es mejor que B» exige la comparación pareada con su potencia, que es lo que hace L6 (ADR-0009). Aquí van los números y su n; no se ordena a nadie.

### Coste · herramientas locales en español

**Máquina** (del sello de la corrida, no de la que informa): modelo de CPU **no registrado** (sello anterior al campo) · 14 CPU visibles · carga 1,39 al arrancar · **un solo proceso, secuencial**, un documento y un extractor cada vez.

**n = 616 documentos y 8733 páginas** — la campaña entera. **No es la n del TEDS**, que se cuenta sobre el conjunto evaluable de cada extractor y es más pequeña y distinta para cada uno. Por eso esto es un bloque y no dos columnas.

| extractor | s/página | s/documento | reloj total | euros |
|---|---:|---:|---:|---:|
| `camelot` | 0,125 | 1,77 | 0,303 h | 0,00 € |
| `docling` | 0,433 | 6,13 | 1,050 h | 0,00 € |
| `pdfplumber` | 0,059 | 0,83 | 0,143 h | 0,00 € |
| `pymupdf4llm` | 0,330 | 4,68 | 0,801 h | 0,00 € |

**Cero euros es un cero MEDIDO**, no un dato que falte: estos 4 corren en local y no gastan. Un `NO_APLICABLE` diría otra cosa.

**Alfabético, no por coste.** Por lo mismo que arriba: ordenar es ordenar, y el más barato no es el mejor mientras la calidad viva en otro eje.

**Agregado:** POR_DOCUMENTO —media por documento, sin ponderar—, que es el primario de `runs/l5/ponderacion.yaml`. `TEDS/pág.` es el secundario, ponderado por páginas: **los mismos TEDS con otros pesos**.

**Régimen:** CENSO. Los documentos con tabla son la población entera, no una muestra, así que **no llevan intervalo** (ADR-0015). Un IC degenerado sobre un censo mentiría sobre la naturaleza del número.

**Denominadores.** La población con tabla son **338** documentos y **2135** tablas de referencia. `cobertura evaluable` es sobre tablas; `acuerdo de recuento` es sobre documentos.

**Y `acuerdo de recuento` NO es el denominador del TEDS, aunque aquí ponía que sí.** Acertar el recuento es **necesario y no suficiente**: si además ninguna de las tablas emparejadas es evaluable —la verdad combina celdas y el extractor no expresa spans, regla de oro 4— el documento sale `NO_APLICABLE` y tampoco puntúa. El denominador real del TEDS de cada fila es su `n` de documentos puntuados, y la diferencia entre las dos cuentas está publicada en la cara a cara (`runs/l5/emparejado.yaml`).

**`+/- tablas` NO es una columna de calidad.** Cuenta el desacuerdo con la referencia, no la habilidad: uno que parte una tabla en tres encuentra más y uno que fusiona dos encuentra menos **y puede estar acertando**. Quien ordena es el TEDS contra la verdad, no el recuento.

**`n/a` no es cero.** Un `NO_APLICABLE` dice que no se pudo medir; un 0,00 diría que se midió y salió cero (decisión B3).
