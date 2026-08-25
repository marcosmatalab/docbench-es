# METRICS · docbench-es

> **Qué es este fichero.** El **método**. Para cada número que
> [`RESULTS.md`](../RESULTS.md) publica: qué mide exactamente, con qué
> instrumento, con qué resolución, qué incertidumbre arrastra y de dónde sale esa
> incertidumbre. `RESULTS.md` lleva los números; aquí está por qué se pueden
> creer, y qué habría que hacer para desmentirlos.
>
> §8 del manual lo describe como *«cada métrica: fórmula, supuestos, caso
> degenerado»*, y §12 dice que es *«donde un examinador con formación estadística
> va a buscar»*. Hoy la única métrica medida es un tiempo, así que el fichero
> empieza pequeño. Crece con cada hito: TEDS en L2, exactitud y kappa en L5 y L8b.
>
> Al final está el **historial de correcciones del método**: cada vez que una
> cifra publicada estuvo mal, qué se dijo, por qué era falso y qué la sustituyó.

---

## L0 · El tiempo de la puerta rápida

### Qué mide cada una de las tres filas

`RESULTS.md` publica tres tiempos para la misma corrida y **no son intercambiables**.
De fuera hacia dentro:

| Fila | Qué abarca | Instrumento | Resolución |
|---|---|---|---|
| *Run* | Encolado + job + pasos `Post` | API de Actions (`createdAt` → `updatedAt`) | 1 s |
| Job `fast` | Los cinco pasos: `checkout`, `setup-uv`, `uv sync`, el chequeo del pin y la puerta | API de Actions (`startedAt` → `completedAt`) | 1 s |
| **`make fast`** | **Sólo el paso `la puerta`** | Marcas de tiempo del log del job | ~0,05 s |

**Sólo la tercera es el criterio de aceptación de L0.** Las otras dos se publican
porque las tres se han confundido antes —ver el historial— y porque un lector que
mire el badge verá el run, no el paso.

### La ventana del paso, y sus dos fronteras

`make fast` no tiene un cronómetro propio en CI. Se mide por la distancia entre
dos líneas del log del job:

- **abre** `##[group]Run make fast`
- **cierra** el `[100%]` que imprime `pytest`

Ninguna de las dos cae exactamente donde empieza y acaba el proceso, y las dos
desviaciones van en sentidos distintos. Medidas en las **cuatro** corridas:

| Frontera | Desfase medido (n=4) | Efecto |
|---|---|---|
| `##[group]` → `##[endgroup]`, cuando la shell arranca de verdad | 2,3 – 4,7 ms | la ventana **sobra** por ahí |
| `[100%]` → siguiente línea del log | 43 – 91 ms | la ventana **falta** por ahí |

> La línea siguiente al `[100%]` **no** es `Post job cleanup`, como decía una
> versión anterior de esta tabla: es el aviso `Node 20 is being deprecated…` que
> emite el runner, y `Post job cleanup` viene después. Las dos van a ~0,1 ms una de
> otra, así que las cifras no cambian; pero en la sección que define el método, la
> marca tiene que ser la que es.

De ahí la incertidumbre: el valor real está entre unos **0,005 s por debajo** y lo
que mida la cola de esa corrida **por encima**. Para `28186b9`, cuya cola son
69,7 ms sobre un valor medido de 4,4304 s, eso es **[4,426 s; 4,500 s]**.

**No es un suelo**, aunque casi: la ventana también sobra un poco por el arranque.

### Por qué el número va con dos decimales

La banda de incertidumbre de una sola medición es de **decenas de milisegundos**
—entre 43 y 91 ms según la corrida—, así que el método resuelve **del orden de
0,1 s**. Publicar `4,4304 s` afirmaría 0,1 ms: **tres órdenes de magnitud** más
fino de lo que el método aguanta.

> Se da como orden de magnitud a propósito. Este multiplicador se ha escrito de
> tres formas distintas —«setecientas veces», «quinientas»— porque el resultado
> depende de contra qué se divida: la cola del peor caso, la resolución declarada
> o la banda de la corrida concreta. Un número que cambia según cómo se derive no
> debe publicarse con dos cifras; el orden de magnitud es estable y basta para lo
> que la frase afirma.

Se publica **4,43 s**. El segundo decimal ya está dentro del ruido y **no debe
leerse como valor absoluto**; se conserva sólo porque las diferencias entre
corridas (0,2 – 1,0 s) superan la incertidumbre en un orden de magnitud, así que
sí sirve para ordenarlas.

### Los estadísticos derivados, y por qué llevan una sola cifra

De las cuatro corridas salen una razón entre extremos y dos desviaciones respecto a
la mediana. **Son estadísticos de tres medidas que ya traen su propia
incertidumbre**, y propagarla los ensancha:

Se publica **sólo la razón entre extremos, ≈1,3×**, y con una cifra. Las
desviaciones respecto a la mediana no se publican, y la razón es la que sigue.

**La mediana es inestable a este n.** Con las tres corridas del cierre era 3,62 s;
al entrar la cuarta pasó a **3,95 s**. Una desviación anclada a ella se movía de
−5,9% / +22% a −14% / +12% sin que cambiara ni una sola medición. **La razón entre
extremos no depende del centro**, y por eso es la que se publica.

**Y por qué nunca se escribe «±30%».** El `±` anuncia simetría alrededor de un
centro que aquí ni es estable ni describe lo observado: sobre la mediana de hoy
serían 2,77 – 5,14 s, y el rango real es 3,41 – 4,43 s.

### Qué entra en la muestra

No vale «las corridas del hito»: vale **toda corrida cuyo árbol de código sea
idéntico al de `28186b9`**, byte a byte. Hoy son cuatro —`78ee8f0`, `4e4ea0b`,
`28186b9` y `3a6b9d7`—, que sólo se diferencian en ficheros `.md`, y ningún `.md`
entra en lo que mide la puerta: `ruff` mira los `.py` y
`pyproject.toml`, `mypy --strict` sólo `src/`, `lint-imports` el grafo de paquetes
y `pytest` sólo `tests/unit`. Se comprueba, no se argumenta:

```bash
git diff --name-only 78ee8f0 28186b9 | grep -v '\.md$'   # no imprime nada
```

Ese mismo diff cubre los commits **posteriores** a `28186b9`, con una salvedad que
hay que decir en voz alta: desde entonces sí han cambiado dos ficheros que no son
markdown, el `Makefile` y el `.gitignore`. El del `Makefile` toca **sólo el
objetivo `clean`**, que `make fast` no ejecuta; se comprueba con
`git diff 28186b9 HEAD -- Makefile`. O sea que el comando ya no imprime nada: hoy
imprime esos dos nombres, y lo que sostiene la afirmación es mirar el diff, no que
la salida esté vacía.

La cuarta corrida se incorporó **después** de publicar el rango con n=3, y cae
fuera de él en las columnas de job (14 s contra 10–11) y de run (18 s contra
14–16). Se añadió igual: el criterio es de inclusión, no de conveniencia, y dejar
fuera una observación que lo cumple porque ensancha el rango es la misma clase de
sesgo que sostener el mínimo de la muestra. **La muestra crece con cada commit de
documentación**, así que el rango publicado lleva su fecha de corte.

**Con este n no se calcula un intervalo de confianza y no se da ninguno.** Lo que se
publica es el rango observado —mínimo y máximo—, declarado como tal. Un tiempo no
es una estimación sobre una muestra de documentos: no hay población de la que se
muestree. Ver la regla de oro 2 de `CLAUDE.md` y [ADR-0015](adr/0015-alcance-de-la-regla-del-intervalo.md).

### La causa de la dispersión no se ha medido

Entre la corrida más rápida y la más lenta hay un ~30% sobre código idéntico. Son
runners compartidos y no se controla lo que corre al lado, pero **eso es una
hipótesis, no una medición**, y aquí no se atribuye.

### El margen contra el presupuesto es el de hoy, no una promesa

Los 90 s de §15 son el presupuesto de `fast.yml` **entero**, y hoy la puerta está
casi vacía: no hay motor, ni CLI, ni extractores, ni corpus. El 20× de hoy no será
el de L5. La puerta va a crecer y el margen a encogerse.

### Qué cubre exactamente ese tiempo

`ruff check` (36 ficheros) + `ruff format --check` (35) + `mypy --strict src` (24)
+ `lint-imports` (4 contratos, 32 ficheros, 42 dependencias) + `pytest tests/unit`
(15 tests, dos property-based con `hypothesis`). Sin red y sin Docker.

**Los cuatro recuentos son distintos y es correcto**, no un descuadre: `ruff
check` suma `pyproject.toml` a los 35 `.py`, `ruff format` sólo los `.py`, `mypy`
sólo `src/`, y `lint-imports` recorre el grafo de paquetes —que es el del paquete
`docbench_es`, así que `scripts/` no entra en él ni en el de `mypy`, pero sí en los
de `ruff`. Comprobados con
`uv run ruff check . -v`; los de `mypy` y `lint-imports` coinciden con los que
imprime la corrida `32572683716`.

### El control negativo: un tiempo en verde no demuestra nada

Que la puerta sea rápida no demuestra que detecte algo. Lo que lo demuestra es
romperla a propósito: con `import httpx` metido a mano en `core/`, el contrato
`nucleo-sin-mundo` pasa a **BROKEN** y `make arch` sale en rojo. La salida literal
está en el registro de L0 del [`CHANGELOG.md`](../CHANGELOG.md).

Detalle que importa: **`httpx` ni siquiera está instalado**. El contrato es
análisis estático sobre el AST, así que detecta el import prohibido aunque el
paquete no exista.

### La reproducción caduca, y por eso las ventanas van escritas

El desglose por pasos sale de `gh api .../actions/jobs/$JID/logs`, porque
`gh run view --json` **no da tiempos por paso**. GitHub retiene esos logs un
tiempo limitado, y a este repo ya le pasó: el número del pack de arranque no se
pudo desglosar porque su log había expirado, y hubo que publicar el job como cota
superior. Por eso `RESULTS.md` publica **las marcas de tiempo crudas de las tres
corridas**: cuando los logs expiren, el comando dejará de imprimir nada y las
marcas serán lo único que quede.

---

## El número local: por qué no sustituye al del runner

El número que vale es el del runner, porque es el reejecutable por cualquiera. El
local está para saber qué se siente al desarrollar aquí.

**Instrumento distinto, y mejor.** El cronómetro es `date +%s%N` justo antes y
justo después de `make fast`: mide el proceso entero, no dos líneas de un log, así
que **no tiene la frontera difusa de CI**. Queda un sesgo sistemático y siempre al
alza —el `fork`/`exec` de `make` y de los dos `date`—, de unos pocos ms: un orden
de magnitud por debajo del rango observado.

**Qué significa "en frío" aquí.** `make clean` —que borra `.pytest_cache`,
`.mypy_cache`, `.ruff_cache`, `.hypothesis` y la cobertura— más borrar
`.import_linter_cache`, antes de cada corrida. **No** incluye `uv sync`, que en CI
también queda fuera del paso medido.

**Lo que sigue sobreviviendo, y por qué no se corrige.** El `__pycache__` del
proyecto y el `.venv` entero siguen ahí entre corridas, y el runner nace sin
ninguno de los dos. O sea que el «frío» local **no es el frío del runner**. No se
persigue esa paridad porque el local no es el número publicado: lo que se necesita
de él es que sea estable y comparable consigo mismo, y eso sí lo es.

**Por qué no se comparan las dos cifras.** El local es ~2,3× más rápido que el
runner (1,74 s contra 3,95 s de mediana). La diferencia no se atribuye a ninguna
causa: son máquinas distintas y no se ha medido el reparto.

**La condición de la máquina se declara, porque se midió que importa.** Las cifras
publicadas son con la máquina **en reposo** (`load average` 0,05). Una tanda
anterior de n=10, tomada mientras corrían en la misma máquina los 51 agentes del
escrutinio adversarial, dio mediana **1697,5 ms** (rango 1650 – 1783) contra los
**1742 ms** (1715 – 1872) de la tanda en reposo. Son 44,5 ms de diferencia entre
medianas con rangos que se solapan: **entre tandas hay más variación de la que
sugiere el rango de una sola tanda**, y por eso la condición va escrita y no
supuesta. La cifra publicada es la de reposo porque es la reproducible: un lector
puede dejar su máquina quieta, no puede reproducir «mientras corrían 51 agentes».

**La puerta se cronometra dentro de WSL**, en shell nativa, **nunca** por
`wsl.exe`. Se sospechó que las cifras locales estuvieran infladas por invocarla
desde Windows, pagando el arranque del contenedor en cada llamada. Se midió el
21 ago 2026, sobre el árbol de L0 a medio cerrar —por eso estas cifras no cuadran
con las publicadas hoy: no son la misma versión del código—; lo que se comparaba
es la **diferencia entre vías**:

| Vía | En caliente (mediana, n=3) |
|---|---|
| Shell nativa dentro de WSL | 0,56 s |
| `wsl.exe -d Ubuntu -- bash -lc 'make fast'` | 0,68 s |
| `wsl.exe -d Ubuntu -- true` (sólo el arranque) | 0,16 s |

`wsl.exe` cuesta **~0,15 s por llamada**. Si la cifra de entonces lo hubiera
incluido habría salido ~0,70 s en caliente, no 0,56 s: **no estaba inflada**.
Queda como regla de método, no como anécdota.

---

## L1 · Las normalizaciones de `normalize_cell_text`, una a una

> §9.1 del manual: *«CADA normalización va documentada: una normalización agresiva
> es una forma silenciosa de hacer trampas a favor de un extractor.»* Esta sección
> es esa documentación, y **un test de la puerta la hace cumplir**:
> `test_las_doce_decisiones_estan_documentadas` compara esta tabla contra la tupla
> `NORMALIZACIONES` del código y se pone rojo si una decisión no está aquí.

La regla de la que sale todo lo demás:

> **Sólo se toca lo invisible o la forma de composición Unicode. Ningún glifo
> visible se altera ni se borra.** Una excepción, enumerada y con test propio: N6.

**No normalizar también tiene víctima**, así que las seis rechazadas van
declaradas igual que las seis aplicadas. Comando que lo reproduce:

```bash
uv run python -c "from docbench_es.core.canonical import NORMALIZACIONES as N; [print(n.codigo, n.nombre, '|', n.victima) for n in N]"
```

### Las seis que SÍ se aplican, en orden N1 → N6 → N2 → N3 → N4 → N5

| | Nombre | Qué hace | A quién beneficia si me paso |
|---|---|---|---|
| **N1** | composicion NFC | Compone los acentos que **ya están**. No añade ni quita ninguno | Al extractor cuyo PDF devuelve `e`+U+0301 en vez de `é` por el CMap de la fuente. Es una diferencia de codificación, no de extracción |
| **N6** | expansion de ligaduras | Expande las siete ligaduras latinas U+FB00–U+FB06 por **tabla explícita** | A los parsers cuyo `ToUnicode` filtra el glifo de ligadura. **Es la única que toca un carácter visible.** La página dice «oficina» y el XML del BOE —la verdad de L4— también |
| **N2** | borrado de invisibles | Borra la categoría `Cf`: guion blando U+00AD, ZWSP, ZWNJ, ZWJ, U+2060, BOM | A quien filtra BOM o ZWSP. **Víctima:** un ZWSP dentro de una cifra (`1<ZWSP>234`) se une a `1234` y le regala el separador de millares |
| **N3** | espacios a U+0020 | Mapea `Cc`, `Zs`, `Zl` y `Zp` a espacio normal: tabulador, salto, NBSP, U+202F, U+2009, y los separadores de línea y de párrafo U+2028/U+2029. **Se mapean, nunca se borran** | **Víctima:** el NBSP como separador de millares español pierde su identidad, y el salto de línea dentro de celda deja de ser marca semántica. Borrarlos en vez de mapearlos uniría tokens que no estaban unidos, o sea inventar contenido |
| **N4** | colapso de espacios | Una carrera de espacios pasa a uno solo | A quien conserva el interlineado del PDF. **Orden crítico:** `from_text_heuristic` parte columnas *antes* de normalizar, porque allí la anchura del hueco **es** la columna |
| **N5** | recorte de extremos | Quita el espacio inicial y final | A todos por igual |

Categorías comprobadas ejecutando `unicodedata`, no de memoria: U+00AD, U+200B–D,
U+2060 y U+FEFF son `Cf`; NBSP, U+202F y U+2009 son `Zs`; TAB, NEL y U+000C son
`Cc`; **U+2028 y U+2029 son `Zl` y `Zp`**, que no son `Zs`; **U+2212 MINUS es
`Sm`**, o sea glifo visible, y por eso cae del lado de R3.

**Las cuatro categorías de N3 son exactamente las de `str.isspace()`, y hay un
test que lo hace cumplir.** No es un detalle: la última línea de
`normalize_cell_text` usa `str.split()`, así que un carácter que Python considere
espacio y N3 no haya mapeado se **borraría** en vez de mapearse, y borrar une dos
tokens que no estaban unidos. `Zl` y `Zp` faltaban en la primera versión: las
encontró el test de propiedad, no la revisión.

### Las seis que NO se aplican, y quién ganaría si se aplicaran

| | Nombre | Por qué no |
|---|---|---|
| **R1** | quitar acentos | Regalo directo a la familia OCR sobre escaneado. Perder diacríticos es **el** fallo específico del español que este banco existe para medir. §9.3 ya dice «acentos no» para el verificador `exact` |
| **R2** | plegar mayusculas | Escondería el destrozo *all-caps* del OCR y borraría una señal de cabecera. Se hace en `core.answer` (§9.3), a nivel de respuesta, no de celda |
| **R3** | comillas tipograficas y guiones a ASCII | Son glifos visibles. Beneficiaría al extractor con `ToUnicode` roto, y el destrozo de comillas y guiones correlaciona con el manejo de fuentes, que es justo lo que separa una extracción buena de una mala |
| **R4** | coma decimal y separador de millares | **La decisión más cara del hito** ([ADR-0017](adr/0017-normalizacion-no-toca-los-numeros.md)). Repararía en silencio al extractor que devolvió `1,234.56` donde la página dice `1.234,56` |
| **R5** | deshacer la particion de linea | `presu-\npuesto` es indistinguible de `económico-financiero`: heurística con tasa de falso positivo que L1 no puede medir. Ver límite 31 |
| **R6** | NFKC | Comprobado ejecutándolo: convierte `m²` en `m2`, parte `½` en dos caracteres y el NBSP en espacio. En una tabla de superficies eso es cambiar el dato |

### La consecuencia de R4 que hay que leer entera

Un extractor que devuelve `1,234.56` donde la página dice `1.234,56` **queda
penalizado en dos niveles**: en TEDS con contenido (L2), porque la cadena de la
celda es distinta, y en el verificador `numeric` (L9), donde con su tolerancia
declarada el número **puede darse por bueno**.

No es doble contabilidad. Son dos preguntas distintas —*«¿transcribiste la
celda?»* y *«¿el número es correcto?»*— y responderlas por separado es
informativo, porque un extractor puede acertar la segunda fallando la primera.
Lo que sería una sola pregunta mal hecha es repararlo en la normalización y
publicar las dos como si estuvieran bien.

---

## L1 · Cuándo un hueco es legítimo, y cómo se mide la detección

**El criterio**, que resuelve el «o declara los huecos» de §6.2
([ADR-0018](adr/0018-hueco-de-cola-y-hueco-interior.md)): un hueco en `(f,c)` es
**interior** —y por tanto fatal— si alguna celda **origina en la fila `f`** a la
derecha de `c`. Si no, es un **hueco de cola**: legítimo, informativo, y
enumerado por `holes()`.

**La lectura descartada, y por qué**, que es lo que distingue un criterio medido
de una opinión: la alternativa era mirar si la *posición* de la derecha está
ocupada, viniera de donde viniera la celda que la ocupa. Rechaza HTML legal —el
caso de un `rowspan` que baja de una fila de arriba sobre una fila corta— y está
medido: sobre el censo de esa familia, **la lectura de la rejilla rellena rechaza
el 100% de las tablas legales que la lectura del origen acepta**. El número y su
comando están en [`RESULTS.md`](../RESULTS.md).

**Cómo se mide el 100% de detección.** No con `hypothesis`, que sortea: con un
**censo determinista y exhaustivo** de tablas mutadas, `scripts/censo_invariantes.py`.
Es una tasa sobre el censo completo, no una estimación, así que **no lleva
intervalo**: lleva n, método, versión y comando (ADR-0015). El censo mide las dos
direcciones, y la segunda es la que no se puede omitir:

1. **Detección**: de N tablas rotas por mutación, cuántas se detectan.
2. **Falsos positivos**: de M tablas legales, cuántas se rechazan. Un validador
   que rechazara todo sacaría un 100% en la primera.

`hypothesis` corre además en la puerta, con otro papel: encontrar la forma que no
se me ocurrió. Los dos números publicados salen del censo.

---

## L2 · TEDS: qué mide, contra qué se valida y qué NO dice

**La fórmula**, copiada de la implementación de referencia:

    TEDS = 1 - distancia_de_edición(pred, gold) / max(nodos(pred), nodos(gold))

donde `nodos` son los **descendientes** de `<table>` —no cuenta la raíz— y la
distancia se calcula sobre los árboles **con** su raíz. Esa asimetría no es un
descuido de nadie: es la fórmula publicada, y es la razón de que **TEDS pueda
salir negativo**.

**El coste de edición**, línea a línea del `CustomConfig` de la referencia:
borrar o insertar un nodo cuesta 1; renombrar cuesta 1 si cambia la etiqueta, el
`colspan` o el `rowspan`; entre dos `td` de la misma forma con algún contenido,
cuesta la distancia de Levenshtein entre sus contenidos **normalizada por el más
largo**; y entre dos `td` los dos vacíos, 0.

**El algoritmo aquí es Zhang-Shasha, no APTED.** Los dos resuelven el mismo
problema de forma exacta, así que dan el mismo número; APTED es más rápido y
Zhang-Shasha cabe en un fichero sin añadir dependencia al núcleo puro. **Que den
el mismo número no se supone: es el criterio de aceptación de L2**, y sale 20 de
20 a cuatro decimales.

### Contra qué se valida, exactamente

Los 20 casos son **los de PubTabNet**: `src/sample_gt.json` y `src/sample_pred.json`
de su repo, tablas de artículos científicos. **No son tablas del BOE**, y eso
importa para leer el número: lo que valida es *«¿tu TEDS es TEDS?»*, no *«¿tu TEDS
funciona sobre el corpus español?»*. Lo segundo no lo puede contestar L2, porque
el corpus llega en L3.

El golden lo calcula **su** `metric.py` con APTED, sobre el **render canónico** de
las mismas tablas (ADR-0020). Los dos lados ven el mismo contenido y la misma
forma, así que una diferencia sólo puede venir del algoritmo.

### La incertidumbre de este número

**No tiene intervalo, y no por descuido**: no es una estimación. Es un recuento
—20 de 20— sobre el censo completo de casos disponibles, y el cálculo es
determinista: sin aleatoriedad, sin semilla, mismo resultado en cualquier máquina.
Lo que sí lleva es su **población**: los 20 casos propios de PubTabNet, más 6
casos límite escritos a mano.

Lo que **no** cubre, y está en `LIMITS.md` 39 a 45: la comparabilidad con la
literatura, la descomposición forma/normalización en 5 de los 15 casos que
difieren, `is_header` intercalado, el coste de Zhang-Shasha en tablas enormes, el
recorte del TEDS negativo al publicar, y cuántas cabeceras del BOE viajaban sin
marcar antes del arreglo de `<thead><td>`.

### Historial de este número

**El primer intento comparaba contra el HTML crudo y no cerraba.** 15 de 20 casos
daban distinto, con diferencias de hasta 0,207. La causa no era un bug de TEDS:
la referencia no normaliza nada y cuenta el marcado inline de las celdas. Se
resolvió comparando sobre el mismo contenido (ADR-0020) y midiendo la diferencia
aparte, que es lo que está publicado en `RESULTS.md`.

**Un test afirmaba `0 <= teds <= 1` y era falso.** Lo encontró `hypothesis` en una
corrida de la puerta, no la revisión. La cota real es [−1, 1] y la referencia
devuelve el mismo −0,142857.

**`from_html` no marcaba como cabecera un `<td>` dentro de `<thead>`.** Era un
fallo de L1 que sólo se vio al construir el árbol de TEDS: en PubTabNet **todas**
las cabeceras tienen esa forma, así que `is_header` salía `False` en el 100% de
ellas. Arreglado en L2; los golden se regeneraron después del arreglo.

---

## El tiempo de la puerta es una SERIE, no un dato por hito

Dos puntos ya son una serie. Se sigue de hito en hito en la misma tabla, con el
mismo método y la misma máquina, porque lo que interesa no es el valor de hoy
sino **la pendiente**.

| Hito | Mediana | Rango (n=10) | Tests | Qué añadió |
|---|---|---|---|---|
| L0 | 1742 ms | 1715 – 1872 | 15 | Modelo de datos y errores |
| L1 | 3829 ms | 3713 – 3875 | 82 | Invariantes, cinco conversores, 17 propiedades de `hypothesis` y `mypy --strict` sobre `tests/` |
| L2 | **5604 ms** (n=40, p90 5728, σ=76) | 5140 – 6048 | 185 | TEDS y su validación contra los 20 casos de PubTabNet, `cellmatch`, y el presupuesto de ejemplos declarado en las ocho suites |
| L3 | **7400 ms** (n=40, p90 7505, σ=100) | — | 321 | `entity`, `corpus`, los tres adaptadores y el barrido de referencias. Sello `1600137` |
| L4 | **7842 ms** (n=40, p90 8006, σ=124) | 7529 – 8051 | 374 | `truth.derived`, los 30 fixtures, los candados de congelado y de glob. Sello `f89c5b6` |

**El techo es 8500 ms local / 20 000 en CI** (ADR-0022), y no aparecía en esta tabla
pese a ser el número contra el que se lee la última columna.

> **CORREGIDO en la auditoría en frío de `a0d85ed`, y son dos cosas.** Primera: la
> tabla **decía en presente** que la serie *«se sigue de hito en hito»* y **se paró
> en L2**, con L3 y L4 cerrados. Segunda, y peor: **la fila de L2 mezcla dos
> series** — la mediana y el p90 vienen de una corrida de n=40 y el rango está
> rotulado `n=10`, y ninguno de los dos cuadra con el `mediana 5593, p90 5933, σ=286`
> que publica `ESTADO.md` para el mismo hito, ni con el `5920 ms` del remedido
> posterior. **Son tres mediciones distintas de L2 repartidas entre dos documentos**,
> y cuál describe qué no se puede reconstruir desde los artefactos: la fila se deja
> como está, marcada, en vez de elegir la combinación que cuadre. **Lo que lo cierra
> es el sello**, que L3 y L4 sí llevan.

**+2090 ms con 67 tests más**, y el reparto **medido**: **+1284 ms** son
`mypy --strict` tipando ahora también `tests/` —1820 ms contra 536 ms, media de
n=3 en frío— y los **~806 ms** restantes son los tests y sus 17 propiedades de
`hypothesis`. Sobra margen: el presupuesto son 90 s y es del runner, no del local.

Que el mayor trozo del crecimiento sea el tipado y no los tests importa para la
decisión de mañana: si algún día aprieta, lo primero que hay que mirar es la
caché de `mypy` en CI, no los ejemplos de `hypothesis`.

**En L2 se hizo eso, y con número.** `mypy --strict src tests` cuesta **1614 ms**
en frío y **124 ms** en caliente, así que la caché de CI ahorra ~1490 ms por
corrida; entró en `fast.yml`. `hypothesis` **no** se cachea a propósito: su base
guarda lo ya explorado, así que cachearla haría que CI buscase menos, y el verde
de CI vale justo porque nace limpio.

**Y se declaró presupuesto de ejemplos en las ocho suites de propiedad**, que
hasta L2 heredaban el 100 por defecto sin decirlo.

**La palanca de `max_examples` no existe, y esto es una corrección de método.**
Se publicó que bajar la suite de normalización de 100 a 50 ahorraba ~285 ms,
presentado como medido cuando era una estimación por regla de tres. Medido:
**990 ms a 100, 946 a 50, 935 a 25** — media de 5 corridas en frío por
presupuesto. La palanca vale **44 ms**. El coste lo domina el arranque del
proceso, no los ejemplos, y **el error fue suponer que un test escala con su
`max_examples`**. Regla que deja: antes de publicar una palanca, se acciona y se
mide; una palanca estimada es un plan de contingencia que no existe.

**Cuando se acerque al presupuesto, el arreglo es `--max-examples` por suite,
NUNCA borrar tests.** Se escribe ahora, con 24× de margen, y no el día que
apriete: ese día la tentación será quitar el test lento, que es el que más
encuentra. `hypothesis` corre hoy a 100 ejemplos por defecto y las 17 propiedades
de la suite son lo que más cuesta; bajarlas a 50 en las baratas y dejarlas
altas en las que de verdad buscan —la de ida y vuelta de `from_html` y la de «no
toca ningún glifo visible»— recorta tiempo sin recortar cobertura. Y si aun así
no cupiera, lo que se mueve de sitio es la suite lenta a `full`, con su límite
declarado en `LIMITS.md`. **Un test borrado no aparece en ningún número.**

### La puerta en caliente busca MENOS que en frío, y eso hace más fuerte el verde de CI

`hypothesis` guarda en `.hypothesis/` lo que ya ha explorado. Eso acelera las
corridas repetidas —vuelve a probar primero los contraejemplos que ya encontró—
pero tiene una consecuencia que conviene tener escrita: **una puerta en caliente
explora menos espacio nuevo que una en frío**. Dos corridas verdes seguidas en
local no son dos búsquedas: la segunda parte de lo que la primera dejó hecho.

No es teórico. **El fallo de U+2028 de L1 lo encontró la propiedad
`test_no_toca_ningun_glifo_visible_salvo_las_ligaduras` después de que `make
clean` borrara la base**, no en ninguna de las corridas anteriores, que habían
pasado en verde con la misma implementación. `Zl` y `Zp` llevaban ahí desde que se
escribió N3.

**La buena noticia, y es la que hay que sacar de aquí:** el runner de CI **nace
limpio siempre**, sin `.hypothesis`, sin `.mypy_cache` y sin `.ruff_cache`. O sea
que **CI explora más que un local en caliente, y su verde es el más fuerte de los
dos**. Cuando local y CI discrepen, la sospecha por defecto va contra el local.

De ahí salen dos reglas de método que ya estaban a medias en este fichero y aquí
quedan juntas:

- **Medir en frío no es sólo por el tiempo**: es lo único que garantiza que la
  búsqueda empieza de cero. La misma orden que hace comparable el cronómetro
  —`make clean`— es la que hace válida la exploración.
- **Un verde en caliente no cuenta como búsqueda.** Antes de dar por bueno un test
  de propiedad sobre código recién tocado, se corre en frío al menos una vez.

---

## Por qué la regla del código de salida existe: los 60 ms de L1

El mejor ejemplo que va a dar este proyecto, y salió midiendo, no razonando.

Al remedir la puerta en L1, la primera tanda de n=10 dio esto:

```
61 ms  rc=2      69 ms  rc=2      62 ms  rc=2
63 ms  rc=2      85 ms  rc=2      73 ms  rc=2
76 ms  rc=2      56 ms  rc=2
49 ms  rc=2      66 ms  rc=2
```

**Mediana 64,5 ms contra los 2742 ms reales: 43 veces más rápida.** Sin mirar el
código de salida, la línea publicada habría sido *«L1 baja la puerta de 1742 ms a
64 ms»*, y **el fallo habría parecido la mejor noticia del hito**. Es la forma
exacta que tiene un error de medición de mentir en la dirección tranquilizadora:
`make` para en el primer paso que falla, así que **una puerta rota siempre da un
tiempo MENOR, nunca mayor**.

**La causa, para que no quede como anécdota.** `ruff` clasifica
`docbench_es.core.canonical` como primera parte o como tercera según **si el
módulo existe en disco**. Mientras L1 no lo había creado, el import iba al bloque
de terceros y `ruff` lo daba por bueno; al crearlo, el orden correcto cambió, pero
**la caché de `ruff` seguía sirviendo el veredicto viejo**. El primer `make clean`
del bucle de medición la borró, y desde ahí `ruff check` empezó a fallar. O sea
que el fallo no lo introdujo la medición: **lo destapó**, porque medir en frío es
lo único que borra la caché.

Las diez corridas se descartaron, se arregló el orden del import, y la tanda buena
es la publicada en [`RESULTS.md`](../RESULTS.md). Regla que queda:

> Toda medición comprueba el código de salida **y** se toma en frío. Lo que falló
> no entra en la muestra, y una caché que sobrevive entre corridas puede estar
> tapando justo lo que se está midiendo.

---

## Historial de correcciones del método

Cada vez que una cifra publicada estuvo mal. `RESULTS.md` se lee como la verdad de
hoy; esto es cómo se llegó a ella.

**Sobre qué corrida se publicaba.** La primera tabla citaba la corrida
`32482756941` del commit `e32c846`, que es el **pack de arranque**, no L0. Se
sustituyó al cerrar el hito por `32572683716` / `28186b9`.

**El run publicado como si fuera `make fast`, en dos etapas.** La primera tabla
daba los **12 s** del *run* completo como el tiempo de la puerta. Corregida a
medias después: pasó a publicar el **job**, 10 s, «cota superior» con margen 9×,
porque el log de aquella corrida ya había expirado. Sólo al cerrar el hito, con un
log vivo, se pudo sacar el paso de verdad.

> Esa frase estuvo mal escrita hasta el 22 ago 2026: decía «los **16 s** del run»,
> que es el run de `32572385551` —la corrida nueva—, no lo que llegó a publicarse.
> Se actualizó el número de la tabla y se arrastró a la frase histórica sin
> comprobarla. Verificable con `git show 78ee8f0:RESULTS.md`.

**El mínimo de la muestra sostenido como *el* número.** Se publicó 3,41 s, la
corrida de `78ee8f0`. Cuando se publicó era la única que había, así que la
elección fue honesta; lo que no lo era es haberla mantenido después, cuando ya
existían las tres y esa resultaba ser la más rápida. Sostener el mínimo de una
muestra como el resultado es el sesgo que `RESULTS.md` existe para evitar.

**«Sin intervalo porque es n=1».** Mientras se publicó una sola corrida, el
fichero declaraba que no daba intervalo por tener n=1. Al ver que los tres commits
del cierre corren un árbol idéntico, las tres pasaron a ser repeticiones de una
misma medición.

**Llamar «intervalo» a un rango.** El apartado se tituló «El intervalo: n=3», y
con tres puntos no se calcula un IC. Es un **rango observado**. En la misma
corrección se acotó el alcance de la regla del intervalo: ver
[ADR-0015](adr/0015-alcance-de-la-regla-del-intervalo.md).

**«±30%», que anuncia una simetría que no hay.** Corregido a razón entre extremos.

**`4,4304 s`, precisión falsa.** Cuatro decimales sobre una frontera de decenas de
ms. Se publica `4,43 s`.

**Tres errores de la propia corrección, cazados antes de publicarla.** (a) Decía
que 0,1 ms es «setecientas veces» más fino que el método; contra la resolución
declarada de 0,05 s son **quinientas** — el 700 salía de los 0,07 s del peor caso
de la frontera, que es otra cosa. (b) Llamaba **suelo** a lo medido; no lo es,
porque la ventana también sobra por el arranque. (c) Publicaba los estadísticos
derivados con tres cifras significativas.

**La tabla local que se leía como imposible.** Redondeada a dos cifras, la mediana
en frío salía «1,00 s» y el máximo también «1,00 s». Va en milisegundos y en crudo
desde entonces.

**Por qué subió el número local dentro del propio hito.** De 958 / 564 ms a
1095 / 720 ms: L0 creció al cerrarse con cinco tests más —dos property-based, que
ejecutan 100 casos cada uno—, dos módulos más y los `__post_init__` que congelan
los mapas.

**El «en frío» local no lo era: `make clean` no borraba `.hypothesis`.** La base de
ejemplos y las cachés de constantes de `hypothesis` sobrevivían a todas las
corridas «en frío», mientras el runner nacía sin ellas. Se arregló el `Makefile`
—`clean` ya la borra— y se volvió a medir: la mediana en frío pasó de **1095 ms a
1742 ms**. Corregido el 22 ago 2026; es la razón de que la comparación
local/runner pasara de ~3,3× a ~2,3×.
>
> **Cuánto valía la caché, medido directamente y no por diferencia de medianas.**
> El escrutinio adversarial cronometró el paso responsable por separado:
> `uv run pytest tests/unit -q --no-header` tarda **368–384 ms con `.hypothesis/`
> presente y 953–1026 ms sin ella**. Son ~615 ms, y esa es la cifra que vale,
> porque no mezcla condiciones de máquina como sí lo haría restar dos medianas
> tomadas en tandas distintas.
>
> La cifra **en caliente** apenas se movió (720 → 723 ms), como cabía esperar: en
> caliente la base de `hypothesis` está presente igual que antes.

**Los recuentos de la puerta subieron al entrar `scripts/`.** El sondeo del BOE
añadió dos ficheros Python fuera de `src/`: `ruff check` pasó de 34 a 36 y
`ruff format` de 33 a 35. `mypy --strict src` y `lint-imports` no se mueven, porque
uno mira `src/` y el otro el grafo del paquete `docbench_es`. Anotado el 22 ago 2026
al añadir `scripts/sondeo_boe.py`.

**Los 28 ficheros de `lint-imports` atribuidos a `mypy`.** Los cuatro recuentos de
la puerta son distintos a propósito, y una versión de esa línea se los cruzaba.

**El rango se publicó con n=3 dejando fuera una corrida que cumplía el criterio.**
La corrida `32575381380`, del commit `3a6b9d7`, corre el mismo código —sólo cambia
markdown— y existía cuando se publicó el rango. Se había decidido no incorporarla
por no perseguir cada corrida nueva, pero eso confunde dos cosas: **cuál es el
número publicado** —el del commit del cierre, y ahí la decisión era correcta— con
**qué observaciones entran en la muestra**, donde el único criterio legítimo es la
identidad del código. Al incorporarla, el job y el run se salieron del rango
publicado (14 s contra 10–11, y 18 s contra 14–16) y la mediana del paso se movió
de 3,62 a 3,95 s. Es exactamente por eso por lo que había que incorporarla.

**La frontera de cierre se identificó mal.** La tabla de desfases decía que la
línea siguiente al `[100%]` es `Post job cleanup`; es el aviso `Node 20 is being
deprecated…` del runner, y `Post job cleanup` viene después. Las dos van a ~0,1 ms
una de otra, así que ninguna cifra cambia, pero la marca que define el método tiene
que ser la que es. Con n=4 la cola medida es de 43 a 91 ms, no de 43 a 70.

**El comando que probaba que los commits posteriores no invalidan el número dejó de
probarlo.** `git diff --name-only 28186b9 HEAD | grep -v '\.md$'` se publicó con la
nota «no imprime nada». Al arreglar el `Makefile` dejó de ser cierto: hoy imprime
`Makefile` y `.gitignore`. La afirmación sigue en pie —el objetivo `fast` no cambia—
pero ahora hay que sostenerla mirando el diff, no la ausencia de salida. Un comando
cuyo resultado esperado es «nada» se rompe en silencio.

## L4 · «La verdad derivada reproduce las tablas a mano»: qué mide y qué no

**Qué es el número.** Cuántas de 30 tablas del corpus, transcritas a mano **del PDF**,
reproduce celda a celda la `CanonicalTable` que `truth.derived` saca **del XML**. No
es una estimación estadística: es un **recuento exhaustivo sobre las 30 elegidas**,
así que no lleva intervalo (ADR-0015). Lleva su n, su método y su incertidumbre
declarada, que es lo que la regla de oro 2 exige de un recuento.

**Qué se compara, con qué resolución.** Posición a posición sobre la rejilla, con los
tres estados de L1 —celda anclada, posición cubierta por un span, hueco— más la
dimensión completa. La resolución es **una celda**: no hay medias ni parciales. Las
reglas de qué cuenta como «reproduce» están en **ADR-0040**, congeladas antes de la
primera comparación; la normalización es exactamente la del pipeline
(`normalize_cell_text`) y **nada más**.

**El denominador tiene tres formas y las tres se publican**, porque miden cosas
distintas: fixtures con alguna discrepancia (5 de 30), discrepancias (5), y la
densidad **separada por unidad** — 3 discrepancias de texto sobre 1.213 celdas y 2 de
estructura sobre 30 tablas. Publicar sólo una es lo que hace que un número suene
mejor de lo que es; **mezclar las unidades en la tercera es lo que hacía la primera
versión de este documento**, que ponía «5 de 1.213 celdas» contando como celdas dos
discrepancias de `DIMENSION`, que son una fila entera de más.

**Y el 1.213 no es el total: las 30 tablas suman 2.283 celdas ancladas.** El umbral
de ventana deja 3 tablas transcritas sólo por su cabecera y su última fila, así que
la comparación cubre el **53,1%**. La dimensión completa sí se comprueba en las 30.
Límite 75.

### De dónde sale la incertidumbre de este número

No de un remuestreo —no lo hay— sino de **cuatro cosas declaradas**, cada una con su
cifra:

| Fuente | Cifra | Dónde |
|---|---|---|
| un solo transcriptor, una sola pasada; **el acuerdo intra-anotador NO está medido** | — | ADR-0039, alternativa descartada |
| el transcriptor **auto-corrige erratas del origen** | 1 de 1.213 | límite 69 |
| un fixture **contaminado**: se miró el XML para desambiguar | 1 de 30 | límite 71 |
| 3 fixtures **corregidos** tras adjudicar: coinciden, pero no son evidencia independiente | 3 de 30 | `runs/l4/correcciones.json` |

Por eso el número se publica siempre desglosado: **21 limpias + 1 contaminada + 3
corregidas**, y nunca «25 de 30» a secas. **El desglose sale de `runs/l4/informe.json`,
que emite el propio comparador** (`--informe`), no de cruzar artefactos a mano.

**Se publicó primero como horquilla —«21 o 22»— y era un error de método, no de
aritmética**: se declaró no medible algo que estaba **completamente determinado por
dos artefactos que ya existían**. La regla que sale de ahí, y aplica a cualquier
cifra: *antes de declarar algo NO MEDIBLE, comprueba si es DERIVABLE de lo que ya
está medido.* Límite 71.

### Qué NO dice este número, y está medido

**«Cero discrepancias atribuibles al código» no significa «el código no falla».**
Significa que **estos 30 fixtures no vieron fallar el código**, y cuánto vale eso se
ha medido rompiendo el código a propósito: `scripts/mutar_el_instrumento.py`. De
**22** mutantes: 3 los ve el instrumento, 15 no llegan al sujeto, 1 no es medible
fuera de pytest, 1 es equivalente en la salida y **2 se ejecutan sin que nadie los
note** — `seccion_sin_cerrar`, que es el bug real del día anterior, y `ok`. Cada
hueco lleva su diagnóstico con número: 0 de 30 tablas con la forma que dispara ese
bug y 0 de 30 descartadas por `FATAL`. Límites 65 a 68.

**El alcance se mide sólo durante la DERIVACIÓN**, no durante la comparación. Que un
mutante toque al comparador no es alcance, es contaminación: la primera versión
trazaba las 30 comparaciones enteras y por eso daba por alcanzados los dos mutantes
del normalizador, que **no llegan a `from_html`** — parchean el atributo del paquete
y `_html.py` liga el nombre del módulo al importar.

**La medida `mata` sola es engañosa y por eso van dos.** Un fixture que ya tiene una
discrepancia de frontera **no puede «dejar de coincidir»**, así que `mata` no lo
puede contar nunca; `cambia` mira los 30 y detecta que el conjunto de discrepancias
se mueve.

**Historial de este número, y tiene dos vueltas.** La primera versión sólo tenía
`mata`. La segunda añadió `cambia` **comparando el mensaje formateado**, que lleva
dentro el texto de la celda: con eso `normalizador_agresivo` salía «cambia 3 de 30»
—las 3 discrepancias de frontera de siempre, con el texto en minúsculas— y se
publicó como *«el instrumento lo ve»*. **La versión vieja tenía razón y la corrección
introdujo el error.** La tercera compara `(clase, posición)` y **nunca el texto**, con
su test en `tests/unit/test_guardianes_l4.py`. Las tres se dicen, porque la segunda
se publicó.

### Cómo se adjudica una discrepancia, y por qué el método importa más que el número

**La evidencia sale del PDF, nunca del XML** (ADR-0039 regla 5, escrita antes de
adjudicar ni una). Comprobar contra el XML da por supuesto que el XML acierta, que es
lo que se mide: toda discrepancia saldría «error de transcripción» por construcción.
La prueba es mecánica y no depende de dónde se busque —se buscan **las dos versiones
enteras** en la capa de texto, `scripts/evidencia_pdf.py`—, con una tercera prueba a
nivel de **palabra suelta** para las cadenas de un solo token, donde la de subcadena
no decide: `'...'` está contenido en cualquier línea de puntos de relleno.

**Historial de correcciones de este método.** La primera versión de `evidencia_pdf.py`
anclaba la búsqueda en el prefijo común de las dos versiones y **falló en 2 de las
11**: `'Ayuntamiento de'` cayó en otro ayuntamiento de la misma tabla y `'...'` en una
línea de relleno. Un ancla que puede caer en el sitio equivocado no es evidencia; se
sustituyó por la búsqueda de la cadena entera, que no tiene ese modo de fallo.
