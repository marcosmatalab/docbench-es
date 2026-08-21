# Pack de prompts · docbench-es

Uno por hito. **Copia y pega literal.** Los hitos van en orden y cada uno cierra con
`/cerrar`, que trae escrutinio adversarial obligatorio.

El bucle es siempre el mismo:

```
/hito L<n>        → lee el manual, propone plan de 10 líneas, PARA
   (das OK)
   (Claude Code pica)
/verificar        → dice qué falla y dónde, sin arreglar
/cerrar L<n>      → criterio de aceptación + adversarial + RESULTS + ESTADO + commit
```

---

## L0 · Esqueleto

```
/hito L0

Monta el esqueleto completo: pyproject con uv, ruff, mypy --strict, import-linter,
pytest; el árbol de src/docbench_es/ con TODOS los paquetes vacíos y su __init__.py,
incluidos types.py y errors.py, porque el contrato de capas va con `exhaustive = true`
y un paquete sin ubicar pone el CI rojo; tests/ con unit, contract, hostile, security,
degradation, drift, fixtures y e2e, y un test de humo por directorio (`pytest` sobre un
directorio sin tests devuelve código 5 y pondría `make fast` en rojo por colección
vacía); los ficheros de raíz README.md, RESULTS.md, LIMITS.md, CHANGELOG.md y LICENSE;
y el CI de tres trabajos: fast.yml, full.yml y nightly.yml.

Nada de lógica todavía. El criterio tiene tres partes:

1. `make fast` en verde en menos de 90 segundos con el repo vacío.
2. Si meto a mano un import prohibido (por ejemplo `import httpx` en core/), `make
   arch` se pone rojo. Compruébalo y enséñame la salida.
3. `uv run lint-imports` encuentra el fichero de contrato. Se llama `.importlinter`:
   con el nombre `importlinter.ini` responde "Could not read any configuration" y el
   CI se pondría rojo por el motivo equivocado.

Escribe también docs/reading-order.md con las tres rutas de 5 min, 30 min y 2 h,
aunque de momento apunten a ficheros vacíos.
```

---

## L1 · La forma canónica

```
/hito L1

Implementa src/docbench_es/core/canonical.py: CanonicalCell, CanonicalTable, los cinco
conversores (from_html, from_markdown, from_dataframe, from_tei,
from_text_heuristic), validate() y normalize_cell_text().

Antes de la implementación quiero los tests de propiedad con hypothesis sobre los
invariantes: ninguna celda solapa con otra, ningún span sale del rango, la cobertura
de la matriz es coherente o los huecos están declarados.

Y la regla que no se puede relajar: expresses_spans lo fija el CONVERSOR según el
formato de origen, nunca el extractor. from_markdown y from_text_heuristic devuelven
False siempre.

Documenta CADA normalización de texto que apliques y por qué. Una normalización
agresiva es una forma silenciosa de favorecer a un extractor.
```

---

## L2 · TEDS

```
/hito L2

Implementa core/teds.py con teds(), teds_struct() y teds_batch().

Primero trae a tests/fixtures/pubtabnet/ un conjunto de casos de la implementación de
referencia con sus valores publicados. Ese directorio queda CONGELADO: el hook lo
bloquea. Si el test falla, el fallo está en mi código.

El criterio es coincidencia a cuatro decimales con la referencia. No valides "a ojo":
TEDS no tiene valores intuibles y esa es justamente la razón de que exista este hito.

Añade también core/cellmatch.py para la exactitud celda a celda.
```

---

## L3 · El BOE

```
/hito L3

Implementa entity/base.py con el Protocol EntityAdapter y entity/conformance.py con la
suite que todo adaptador debe pasar. Después entity/boe.py y entity/boe_xml.py, y
corpus/harvest.py, corpus/pairing.py y corpus/manifest.py.

El orden importa: license() y privacy() antes que nada, después truth_mode, y solo
entonces discover() y fetch().

Dos cosas críticas del emparejado PDF/XML: si el texto de los dos discrepa por encima
de un umbral declarado, DESCARTA el par y CUÉNTALO. Un emparejado silenciosamente
incorrecto envenena el benchmark entero. Y publica esa tasa de descarte en el
manifiesto.

Criterio: 1.000 documentos emparejados, con manifiesto y con la tasa de descarte
publicada.
```

---

## L4 · Verdad derivada

```
/hito L4

Implementa truth/derived.py: del XML del BOE a CanonicalTable y a Fact.

Antes, construye a mano en tests/fixtures/tablas/ un conjunto de tablas difíciles con
su verdad conocida: celdas combinadas, tabla partida entre dos páginas, notas al pie,
celdas vacías, cabecera de dos filas.

Criterio: la verdad derivada reproduce esas tablas construidas a mano.
```

---

## L5 · Extractores y nivel 1

```
/hito L5

Implementa extract/base.py con el Protocol Extractor y la suite de conformidad.
Después, uno por uno y UN FICHERO CADA UNO, los OCHO que cubren las cinco familias:
pymupdf4llm y pdfplumber (parser de texto), camelot (tablas), docling, marker y
unstructured (document-AI), grobid (TEI) y tesseract (OCR).

Usa /extractor para cada uno. Ninguno por encima de 150 líneas.

Después el nivel 1 de métricas y la primera tabla de resultados, con coste, latencia y
cobertura evaluable por extractor.

Recuerda: quien no expresa spans sale NO_APLICABLE en el estrato de celdas combinadas,
no cero, y su nota va siempre acompañada de su cobertura.
```

---

## L6 · Muestreo

```
/hito L6

Implementa sample/plan.py y sample/power.py.

El cálculo es PAREADO (McNemar), no independiente, porque todos los extractores
procesan los mismos documentos. Declara la tasa de discordancia supuesta y comprueba
después la real.

El plan se congela y se publica ANTES de medir. El hook bloquea la edición de
plan.yaml precisamente para eso.

Y escribe en el propio plan la nota honesta: la primera campaña es de PRECISIÓN, no de
contraste. Con el presupuesto declarado no hay potencia para separar extractores
parecidos, y eso se dice antes, no después.
```

---

## L7 · Quickstart

```
/hito L7

Trae 20 documentos reales del BOE a tests/fixtures/quickstart/, unos 4 MB, con su
plan congelado. Implementa `make quickstart`.

Criterio: de clone a una tabla de TEDS por extractor en menos de 3 minutos, SIN RED y
sin gastar un euro.

Y añade el test de regresión de quickstart al CI: si esos 20 documentos mueven sus
números entre commits sin que yo haya tocado la métrica, algo se ha roto.
```

---

## L8 · Política

```
/hito L8

Implementa el cumplimiento de licencia y privacidad, y los tres adaptadores hostiles
en tests/hostile/:

1. Uno con may_redistribute_content: false → `publish` debe ABORTAR.
2. Uno con special_categories: true → el registro debe RECHAZARLO.
3. Uno con may_send_to_third_party: false más un extractor por API → la campaña NO
   ARRANCA.

Los tres bloquean, no avisan.

Y el test de fuga de credenciales: busca el valor de cada secreto en todos los
artefactos, logs y cachés generados. Cero apariciones. Este test va en cada PR.

Con esto NO cierra todavía v0.1.0: falta L8b, la verdad auditada. En el commit final: etiqueta v0.1.0, actualiza RESULTS.md con
todos los números del release, y escribe el README con el número en la primera línea.
```

---

## L8b · La verdad auditada

```
/hito L8b

Este es el hito que elimina la crítica científica más peligrosa del proyecto: "¿y cómo
sabes que tu verdad de referencia es verdad?".

Implementa truth/annotator/ (interfaz local de anotación, HTML + servidor mínimo) y el
protocolo de doble pasada ciega:

1. Muestra estratificada de unos 120 documentos del estrato NACIDO DIGITAL, sorteada
   con semilla declarada y repartida por los estratos de dificultad. Solo ese estrato
   tiene verdad DERIVED, que es justo lo que se audita.
2. Dos pasadas independientes y ciegas, separadas por siete días o más. Si el segundo
   anotador soy yo mismo, se publica ACUERDO INTRA-ANOTADOR, nunca inter, con esas
   palabras exactas.
3. Resolución de desacuerdos con protocolo escrito, y se registra cuántos hubo.
4. La medición publicable: "la verdad derivada coincide con la auditoría humana en X%,
   IC [a,b]", con su comando de reproducción.

Criterio de aceptación: ese número está en RESULTS.md con su intervalo y su comando, y
la frase sobre acuerdo intra frente a inter está en LIMITS.md.

Con esto SÍ cierra v0.1.0. En el commit final: etiqueta v0.1.0, actualiza RESULTS.md
con todos los números del release, y escribe el README con el número en la primera
línea.
```

---

## Y a partir de aquí

L9 a L14 son `v0.2.0`, **incluido L12b** (los tres estratos que faltan: escaneado,
empresarial sintético y adversarial). L15 a L20c son `v0.3.0`, **incluidos L20b**
(`toolwatch`, la deriva de herramienta) **y L20c** (leaderboard reproducible + badge).
Los tres son adopciones enteras de la revisión externa y no se recortan.

Están en la tabla de hitos de `MANUAL.md` con su criterio de aceptación y sus horas.
El bucle es el mismo.

**El hito que define el proyecto es L10.** Es el primer número que nadie más tiene:
*"con extracción perfecta el sistema acierta X; con el mejor extractor real, Y; el
hueco atribuible a la extracción es de Z puntos"*.
