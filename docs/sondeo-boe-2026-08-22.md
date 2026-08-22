# Sondeo del BOE · 22 de agosto de 2026

> **Qué es esto y qué NO es.** Un sondeo de usar y tirar para validar la premisa de
> §1.4 del manual **antes** de invertir las ~16-20 horas de L3. **No es L3 y no
> construye nada de L3**: no hay `DocRef`, no hay adaptador de entidad, y nada de
> `src/` importa el script. Se corrió con `scripts/sondeo_boe.py`.
>
> **Estos números NO van a [`RESULTS.md`](../RESULTS.md).** Un sondeo sobre 200
> documentos de 19 días no es una medición del corpus: no hay plan congelado, ni
> muestreo estratificado, ni verdad de referencia. Son una decisión de diseño, no
> un resultado publicable.
>
> **Son estimaciones sobre una muestra de documentos**, así que llevan intervalo,
> por la regla de oro 2 y [ADR-0015](adr/0015-alcance-de-la-regla-del-intervalo.md).
> Intervalos de Wilson al 95%. La unidad de muestreo es el documento, como manda la
> regla de oro 3.

## La respuesta, en tres líneas

**La premisa se sostiene, la mezcla de estratos es estable en el tiempo, y el
diseño de L3 es seguro con cualquier ventana** —pero sólo si `discover` filtra por
sección. Sobre el
BOE entero las tablas son el 12% y el `rowspan` una rareza; sobre las secciones de
disposiciones —I y III, que es donde §9.4 del manual dice que `discover` filtra—
las tablas son el 28% y **el 63% de ellas traen `rowspan` o `colspan` > 1**. El
emparejado PDF/XML es del **100%** sin un solo fallo, y la coherencia entre los dos
es tan alta que el umbral de descarte casi no muerde.

**Lo que cambia en L3:** el filtro por sección deja de ser una optimización y pasa
a ser parte de la definición del corpus. Sin él, tres de cada cuatro documentos
descargados son anuncios y edictos sin tabla.

**Lo que NO cambia:** la ventana temporal. Se midió sobre tres ventanas separadas
por once meses y **las proporciones no se mueven** —§6—. Lo que sí se mueve, y
mucho, es la **densidad**: agosto rinde 29 documentos por día publicado contra los
49 de octubre. Eso no afecta a la composición del corpus, sólo a cuántos días hay
que barrer.

---

## Condiciones del sondeo

Estampadas por el propio script en el JSON de salida, no escritas a mano.

| | |
|---|---|
| Ejecutado | 2026-08-22T17:56:17Z |
| Rangos consultados | `20251006–20251024`, `20260302–20260320`, `20260803–20260821` · 19 días naturales cada uno, todos ya cerrados |
| Semilla | `20260822` |
| Muestreo | `random.Random(semilla).sample` sobre el universo ordenado por identificador |
| Espera entre peticiones | 0,25 s |
| Versiones | Python 3.12.3 · httpx 0.28.1 · pypdf 6.16.1 |
| Plataforma | Linux 6.6.87.2 (WSL2), glibc 2.39 |
| Commit | `f846873`, árbol limpio salvo `scripts/` sin seguir |

**Códigos de salida de todo lo consultado.** 19 sumarios pedidos por ventana. En
agosto, **18 con HTTP 200 y uno con 404**; en otoño y primavera, **17 y dos 404**.
Los 404 caen todos en domingo. Van escritos porque un día que no se pudo consultar
tiene que verse, no desaparecer del denominador.

### Reproducción

Las **tres ventanas son rangos pasados y cerrados**, elegidos así a propósito: un
rango que aún no ha terminado deja de ser reproducible en cuanto el BOE publica un
día más.

```bash
for R in "20251006 20251024 otono-2025" \
         "20260302 20260320 primavera-2026" \
         "20260803 20260821 agosto-2026"; do
  set -- $R
  uv run --with httpx --with pypdf python scripts/sondeo_boe.py \
      --desde "$1" --hasta "$2" --n 200 --semilla 20260822 --secciones 1,3 \
      --cache /tmp/sondeo_boe --json "docs/sondeo-boe-$3.json"
done
```

El JSON crudo de las tres está commiteado al lado de estas notas:
[`otoño`](sondeo-boe-otono-2025.json), [`primavera`](sondeo-boe-primavera-2026.json),
[`agosto`](sondeo-boe-agosto-2026.json). Quitando `--secciones` sale la pasada de
todo el BOE. Con `--solo-licencia` se comprueba sólo el punto 5, que es lo que más
probablemente cambie con el tiempo.

---

## 1 · Tasa de emparejado PDF + XML

**100% [98–100], n=200, k=200. Cero fallos.** Ni uno solo de los documentos
muestreados dejó de tener las dos representaciones.

El enum cerrado de causas (`Causa`, en `scripts/sondeo_lib.py`) tiene diez entradas
—`sin_url_xml`, `sin_url_pdf`, `http_xml`, `http_pdf`, `red_xml`, `red_pdf`,
`xml_mal_formado`, `pdf_ilegible`, `pdf_sin_capa_texto`, `xml_sin_texto`— y
**ninguna se activó**. No es que no se contaran: es que no hubo.

> **Cuidado con leer esto como «el emparejado es gratis».** Lo que dice es que la
> API de sumarios **ya** trae `url_pdf` y `url_xml` en cada ítem: el emparejado no
> hay que inferirlo, viene dado. Lo que L3 tiene que resolver no es emparejar, sino
> **descartar** lo que no sirve, que es el punto 3.

### Un fallo del sondeo que merece quedar escrito

El recorrido del sumario perdía documentos, y el guardián que compara conjuntos de
identificadores contra un recorrido ciego lo cazó **tres veces seguidas**. La causa:
**el JSON del sumario mete a veces una clave `texto` entre un nivel y el siguiente,
y a veces no, en cualquier nivel** —visto en `seccion` (20260809) y en
`departamento` (20260817)—. La primera versión perdía 61 documentos de 2.847; la
segunda, 5; la tercera, 1. La cuarta cuadra: universo 2.829, que son exactamente los
2.847 del recorrido ciego menos los 18 sumarios diarios `BOE-S-*`, que no son
documentos.

**Para L3 esto es una advertencia concreta:** el `discover` del adaptador del BOE
necesita ese guardián, o publicará un censo incompleto sin enterarse.

---

## 2 · Tasa de tabla real, y de celdas combinadas

Es el número que decide el proyecto, y **depende por completo de la sección**.

| | Todo el BOE (n=50) | Secciones I y III (n=200) |
|---|---|---|
| Documentos con `<table>` | **12%** [6–24] | **28%** [23–35] |
| …de ésos, con `rowspan` o `colspan` > 1 | 50% [19–81] (n=6) | **63%** [50–74] (n=57) |
| …de ésos, con **`rowspan`** > 1 | 17% [3–56] (n=6) | **42%** [30–55] (n=57) |
| …de ésos, con `colspan` > 1 | 50% [19–81] (n=6) | 56% [43–68] (n=57) |
| Sobre la muestra entera, con celdas combinadas | 6% [2–16] | **18%** [13–24] |

**Sólo se cuentan `rowspan`/`colspan` con valor > 1.** Un `colspan="1"` no combina
nada, y contarlo inflaría justo la cifra que sostiene el proyecto.

**El `rowspan` no es una rareza donde importa: son 24 documentos de 57 con tabla.**
El span máximo visto es **33**. En 200 documentos hay 283 tablas.

Sobre todo el BOE, en cambio, el `rowspan` sí lo parecía: 1 documento de 6. Con n=6
el intervalo es [3–56], o sea que no permitía decidir nada. **Ése fue el motivo de
ampliar a n=200**, y la desviación respecto a los ~50 pedidos se declara aquí.

---

## 3 · Coherencia PDF/XML, y el umbral de descarte

Se miden dos cosas, porque responden a preguntas distintas: la **similitud de
secuencia** castiga el reordenamiento —que en una tabla importa— y la **contención**
responde a «¿está todo el XML dentro del PDF?», que es la pregunta de L3.

| | Mediana | Percentil 5 | Mínimo |
|---|---|---|---|
| Similitud de secuencia | 0,992 | 0,906 | 0,783 |
| Contención del XML en el PDF | 0,986 | 0,867 | 0,653 |

**A qué tasa descarta cada umbral** (n=200, secciones I y III):

| Umbral | Descarta por similitud | Descarta por contención |
|---|---|---|
| 0,70 | 0% [0–2] | 1% [0–4] |
| 0,80 | 1% [0–4] | 2% [1–5] |
| **0,85** | **2% [1–5]** | **5% [3–9]** |
| 0,90 | 5% [3–9] | 14% [10–19] |
| 0,95 | 18% [14–24] | 24% [18–30] |

**La recomendación para L3: similitud ≥ 0,85, y que el umbral viva en el perfil de
la entidad, no en el código.** Descarta un 2% [1–5], que es coste asumible, y deja
fuera la cola de documentos donde el PDF y el XML de verdad no dicen lo mismo. Subir
a 0,95 descartaría uno de cada cinco documentos buenos.

### La normalización, declarada

Es obligatorio declararla (regla de oro 7) porque una normalización agresiva es
hacer trampas en silencio a favor de la coherencia:

- Del PDF se **quitan las líneas de maquetación** que el XML no tiene: cabecera
  `BOLETÍN OFICIAL DEL ESTADO`, `Núm.`, `Sec.`, `Pág.`, el `cve:`, la URL, el
  depósito legal, el ISSN y el «Verificable en». Sin quitarlas la similitud bajaría
  por un motivo que no tiene que ver con el contenido.
- De los dos: NFKC, minúsculas y partido en palabras `\w+`.
- **Los acentos se conservan a propósito.** Quitarlos es normalización agresiva y
  aquí sólo serviría para inflar la similitud.
- La similitud de secuencia se calcula sobre los primeros 12.000 tokens.

---

## 4 · Estratos de dificultad, en bruto

Secciones I y III, n=200. Alimenta §3 bis y el plan de §10.2.

| Estrato | Proporción |
|---|---|
| `sin-tabla` | 71% [64–77] |
| `celdas-combinadas` | 18% [13–24] |
| `tabla-simple` | 10% [7–16] |
| `anexo-png` | 0,5% [0–3] |

**`multipagina` no se ha medido, y no se estima.** Exige saber si **una tabla**
cruza una página, y el XML del BOE no tiene páginas. Lo que sí se puede decir es la
cota: el 88% [83–92] de los documentos ocupa más de una página, y el 28% [22–34]
tiene tabla **y** más de una página. Eso es un límite superior de `multipagina`, no
una medida, y llamarlo de otro modo sería inventárselo. Mediana de 6 páginas por
documento, máximo 95.

### Rendimiento, para dimensionar L3

**Corregido con la ventana más densa.** La primera versión de estas notas daba
«~36 días» calculados sobre agosto, que es el mes más flojo del año: era una **cota
superior**, no una estimación. Con las tres ventanas medidas:

| Ventana | Universo (secc. I+III) | Días publicados | Densidad | Tasa `celdas-combinadas` | 1.000 docs | 120 `celdas-combinadas` |
|---|---|---|---|---|---|---|
| **otoño 2025** | 827 | 17 | **48,6 doc/día** | 34/200 = 17,00% | **21 días** (~4 semanas) | **15 días** |
| primavera 2026 | 802 | 17 | 47,2 doc/día | 23/200 = 11,50% | 22 días | 23 días |
| agosto 2026 | 524 | 18 | 29,1 doc/día | 36/200 = 18,00% | 35 días | 23 días |

Las dos últimas columnas se derivan así, y con la tasa **sin redondear**:
`densidad = universo / días`; `1.000 docs = ⌈1000 / densidad⌉`;
`120 celdas-combinadas = ⌈(120 / tasa) / densidad⌉`. En primavera, `120 / 0,1150 =
1.043` documentos y `1.043 / 47,2 = 22,1 → 23 días`. Usando el 12% redondeado
saldrían 21, y de ahí que la tasa vaya con su conteo.

**El número que vale para planificar es el de una ventana normal: 21-22 días de
publicación para los 1.000 documentos del criterio de L3**, o sea unas cuatro
semanas naturales. El rango entre ventanas es de 21 a 35 días, y el extremo alto es
agosto.

Agosto es peor por **densidad, no por composición**: tuvo 18 días publicados frente
a 17 de las otras dos ventanas, y aun así un 37% menos de documentos.

> **Detalle del calendario, medido y no supuesto:** el BOE **publica los sábados** y
> no los domingos. En las tres ventanas los únicos HTTP 404 caen en domingo. La
> excepción es el **domingo 9 de agosto de 2026**, que sí publicó (HTTP 200). Los
> «días publicados» de la tabla son los sumarios con HTTP 200, contados, no los días
> hábiles supuestos.

---

## 5 · La licencia, leída de primera mano

**Leída el 2026-08-22** en <https://www.boe.es/informacion/aviso_legal/index.php>,
HTTP 200, 36.293 bytes. La licencia es la aprobada por **Resolución de la Agencia
de 27 de junio de 2024**.

**El manual acierta, literalmente.** §1.4 dice que las condiciones «autorizan
copiar, reproducir, distribuir y difundir, con fines comerciales incluidos, a cambio
de atribución». El texto legal dice:

> «Las presentes condiciones permiten la reutilización de los documentos sometidos a
> ellas **para fines comerciales y no comerciales** […] La autorización de
> reutilización conlleva asimismo, la **cesión gratuita y no exclusiva** de los
> derechos de propiedad intelectual […] La autorización de reutilización incluye:
> **La copia, reproducción, distribución y difusión pública** de la información. La
> **modificación, adaptación, extracción, reordenación y combinación** de la
> información en orden a crear obras derivadas».

### Tres cosas que el manual NO recoge y L3 tiene que atender

1. **La atribución de una obra derivada lleva otra fórmula.** Para copia y difusión
   es *«Fuente de los datos: Agencia Estatal Boletín Oficial del Estado»*; pero para
   «modificación, adaptación, extracción, reordenación o combinación» —que es
   exactamente lo que hace este banco— la fórmula es **«Basado en datos de la
   Agencia Estatal Boletín Oficial del Estado»**. Es la que tiene que emitir el
   adaptador del BOE en `attribution`.
2. **Hay una exclusión.** Las obras de la Biblioteca Jurídica Digital quedan fuera y
   van bajo CC BY-NC-ND 4.0. No afecta al diario, pero el adaptador no debe tocarlas.
3. **Prohibición expresa:** no se puede reutilizar la información «de un modo que
   sugiera que tiene carácter oficial». Un banco que publica extracciones
   automáticas del BOE tiene que decir que no son el texto oficial.

> **Un fallo del propio sondeo, que queda escrito.** La primera versión del chequeo
> buscaba los infinitivos del manual —«copiar», «reproducir», «distribuir»,
> «difundir», «atribuci»— y daba **cinco falsos negativos**, porque el texto legal
> usa sustantivos («la copia, reproducción, distribución y difusión pública») y
> llama a la atribución «citarse la fuente». Un chequeo mal formulado es peor que no
> tenerlo: habría hecho saltar una alarma de licencia que no existía. Corregido, el
> modo `--solo-licencia` sale con código 0 y ningún término ausente.
>
> La primera URL probada, `https://www.boe.es/avisos_legales/`, da **404**. La buena
> se alcanza desde `/datosabiertos/`.

---

## 6 · ¿Se mueven las proporciones con la ventana temporal?

La pregunta no es cuánto vale cada proporción en otoño: es **si se mueven**. Si se
movieran, la ventana temporal sería un estrato más y habría que declararlo **antes**
de que L6 congele el plan de muestreo.

Tres ventanas de 19 días naturales, separadas por hasta once meses, todas con
`--n 200 --semilla 20260822 --secciones 1,3`. Rangos **pasados y cerrados**, así que
son reproducibles para siempre.

Cada celda lleva **el conteo al lado del porcentaje**, `%(k/n)`, para que todo lo
que sale de aquí —los pesos, el rendimiento— se pueda re-derivar sin volver al JSON.
Un porcentaje redondeado no basta: 12% y 11,50% dan 21 y 23 días de barrido.

| Métrica | otoño 2025 | primavera 2026 | agosto 2026 | ¿solapan? |
|---|---|---|---|---|
| Emparejado PDF+XML | 100% (200/200) [98–100] | 100% (200/200) [98–100] | 100% (200/200) [98–100] | **sí** |
| Con `<table>` | 31% (62/200) [25–38] | 28% (57/200) [23–35] | 28% (57/200) [23–35] | **sí** |
| …de ésos, con span > 1 | 55% (34/62) [43–67] | 40% (23/57) [29–53] | 63% (36/57) [50–74] | **sí** |
| …de ésos, con `rowspan` > 1 | 44% (27/62) [32–56] | 25% (14/57) [15–37] | 42% (24/57) [30–55] | **sí** |
| `celdas-combinadas` (sobre la muestra) | 17% (34/200) [12–23] | 11,5% (23/200) [8–17] | 18% (36/200) [13–24] | **sí** |
| `tabla-simple` | 14% (28/200) [10–19] | 17% (34/200) [12–23] | 10% (21/200) [7–16] | **sí** |
| `sin-tabla` | 64% (128/200) [57–70] | 66% (132/200) [59–72] | 71% (142/200) [64–77] | **sí** |
| `anexo-png` | 5,0% (10/200) [2,7–9,0] | 5,5% (11/200) [3,1–9,6] | 0,5% (1/200) [0,1–2,8] | **no** |
| Descarte a umbral 0,85 | 4% (9/200) [2–8] | 6% (11/200) [3–10] | 2% (4/200) [1–5] | **sí** |

Ventanas: otoño `20251006–20251024`, primavera `20260302–20260320`, agosto
`20260803–20260821`. n=200 en cada una, cero fallos en las tres.

### Ocho de nueve se solapan. La novena no sobrevive al examen

**`anexo-png` es la única que no solapa, y sólo en un par de tres.** Primavera
(11/200) contra agosto (1/200) no se tocan; otoño contra agosto sí, por un pelo
(2,74 frente a 2,78). Otoño contra primavera coinciden casi exactamente.

Mirar solapes de intervalos no basta aquí, porque el cuadro tiene **27
comparaciones por pares** (9 métricas × 3 pares) y a ese volumen aparecen
discrepancias por azar. Se contrasta con la **prueba exacta de Fisher**:

| Par | k/n | p |
|---|---|---|
| otoño vs primavera | 10/200 vs 11/200 | 1,000 |
| otoño vs agosto | 10/200 vs 1/200 | 0,011 |
| primavera vs agosto | 11/200 vs 1/200 | 0,0056 |

Con corrección de Bonferroni sobre las 27 comparaciones el umbral es 0,0019, y
**ninguna de las tres lo cruza**. Y hay un argumento más fuerte que el estadístico:
`anexo-png` y `sin-tabla` son **la misma población** partida por una prueba de
imagen —un documento sin `<table>`, con o sin `<img>`—. Sumados, las tres ventanas
son indistinguibles: **69% [62–75], 72% [65–77], 72% [65–77]**.

**No se declara como movimiento**, pero tampoco se entierra: los dos contrastes
apuntan en la misma dirección (agosto por debajo) desde dos ventanas independientes,
y eso es sugerente aunque no esté establecido. Queda escrito para que, si en L3
aparece otra vez, no se lea como un hallazgo nuevo.

### Y por qué, operativamente, da igual que se mueva

Aunque se moviera, **no cambiaría ni un peso del plan de muestreo**, porque el
`weight` de cada estrato en el `SamplingPlan` **no se hereda de este sondeo**: §10.2
lo define como `found / total` **medido sobre el corpus real de la campaña**, con
`found` contado en el censo completo, no estimado en una muestra de 200. El sondeo
dimensiona —cuántos días hay que barrer— y no pondera.

> **Esto va escrito porque el riesgo es concreto:** dentro de seis meses alguien lee
> «`anexo-png` 5%» en estas notas y lo mete como `weight: 0.05` en un `plan.yaml`.
> Sería un peso inventado sobre una ventana de 19 días, y §12 lo propagaría a la
> exactitud ponderada de todos los resultados. **Los pesos se miden sobre el corpus
> que se va a usar, siempre.**

### Un defecto del propio estrato, que L3 hereda

Al mirar qué son esos documentos, `anexo-png` resulta **no ser homogéneo**. En
otoño llevan de 1 a 14 imágenes y de 7 a 15 páginas; en primavera hay documentos de
**134 imágenes y 136 páginas** junto a otros de una sola imagen. La etiqueta mezcla
«un documento con una figura» con «un anexo escaneado de 136 páginas», que para un
extractor no son el mismo problema ni de lejos. **La regla `anexo-png` de §9.4
necesita un umbral**, y no es el número de imágenes: es si el PDF trae **capa de
texto**, que es lo que decide qué familia de extractor puede competir. Resuelto en
[ADR-0016](adr/0016-anexo-png-se-disuelve-en-capa-de-texto.md): `anexo-png` se
disuelve en `nacido-digital` y `escaneado`, medidos por caracteres extraíbles por
página. Se implementa en L3.

### La conclusión, para L6

**La mezcla de estratos se mantiene dentro de los intervalos, así que el diseño de
L3 es seguro con cualquier ventana, y la ventana temporal NO es un estrato.** Lo que
sí hay que declarar en el plan es otra cosa:

1. **La densidad varía 1,7×** entre agosto y octubre (29,1 contra 48,6 documentos
   por día publicado). No cambia la composición, pero sí cuántos días hay que
   barrer, y un plan que dimensione con agosto pedirá un 67% más de calendario del
   necesario.
2. **La ventana usada va escrita en el plan**, con sus fechas exactas y su densidad
   medida. No como estrato, sino como condición declarada — la misma lección que las
   cifras locales de `docs/metrics.md`.
3. **Este sondeo mira tres ventanas de 19 días.** No dice nada de enero, de junio ni
   de un cambio de gobierno. Que tres ventanas coincidan no demuestra que todas lo
   hagan.

---

## Lo que esto cambia en L3, y lo que no

**Se confirma y no hay que tocarlo:** la verdad de referencia sale del XML sin
anotar a mano; el emparejado viene dado por la API; la licencia permite el uso
comercial con atribución; hay `rowspan` de verdad, que es lo que distingue este
corpus de una colección de CSV.

**Cambia:**

1. **El filtro por sección es parte de la definición del corpus**, no una
   optimización. Sin él, el 88% de lo descargado no tiene tabla.
2. **`discover` necesita el guardián del recorrido**, o publicará un censo
   incompleto en silencio. El envoltorio `texto` del sumario aparece de forma
   irregular en varios niveles.
3. **El umbral de coherencia entra en el perfil de la entidad** con valor 0,85, y su
   tasa de descarte (2% [1–5]) es un resultado que hay que publicar, no un detalle.
4. **`attribution` del adaptador del BOE tiene que decir «Basado en datos de…»**,
   no «Fuente de los datos:…», porque el banco crea obra derivada.
5. **`multipagina` no se puede etiquetar desde el XML.** O se mide sobre el PDF, o
   el estrato se declara vacío. Es una decisión que L3 tiene que tomar explícitamente.
6. **`anexo-png` desaparece como estrato**, disuelto en `nacido-digital` y
   `escaneado` por capa de texto:
   [ADR-0016](adr/0016-anexo-png-se-disuelve-en-capa-de-texto.md).
7. **El plan de L6 declara su ventana con las fechas y la densidad medida**, no como
   estrato —no lo es— sino como condición. Dimensionar con agosto pide un 67% más de
   calendario del necesario.

## Lo que este sondeo NO mide

- **Tres ventanas de 19 días, no el año.** Se comprobó que las proporciones no se
  mueven entre octubre, marzo y agosto (§6), pero **no se ha mirado enero, ni junio,
  ni un año con cambio de gobierno o de legislatura**. Que tres ventanas coincidan no
  demuestra que todas lo hagan.
- **Nada sobre por qué agosto es un 37% menos denso.** Se mide que lo es; la causa
  —vacaciones, calendario administrativo, otra cosa— **no se ha investigado**.
- **La calidad del XML como verdad de referencia.** Que haya `<table>` no dice que
  la tabla sea correcta ni que coincida con lo que se ve en el PDF. Eso es L4 y L8b.
- **Nada sobre los otros tres estratos de corpus** de §3 bis.
- **`con-notas-al-pie`**, uno de los seis estratos de dificultad: no se ha intentado
  detectar.
