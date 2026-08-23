# RESULTS · docbench-es

> **La regla de este fichero.** Un número que no se puede reproducir no existe.
> Toda **estimación** lleva su intervalo; todo número que **no** es una estimación
> —un tiempo, un recuento, una tasa sobre el censo completo— lleva su método y su
> incertidumbre declarada: n, rango y resolución del instrumento. **Una cifra
> desnuda no se admite en ninguno de los dos casos.** Es la regla de oro 2 de
> `CLAUDE.md`, acotada en [ADR-0015](docs/adr/0015-alcance-de-la-regla-del-intervalo.md).
>
> **Aquí van los números. El método va en [`docs/metrics.md`](docs/metrics.md)**:
> qué mide cada ventana, con qué resolución, de dónde sale cada incertidumbre y el
> historial de correcciones. Lo que el proyecto NO mide, en
> [`LIMITS.md`](LIMITS.md).

## Lo que todavía NO hay aquí, dicho antes que lo que sí

> **NO VALIDADOS, y ninguna cifra de este fichero pasa por ellos.**
> `from_markdown`, `from_dataframe`, `from_tei` y `from_text_heuristic` están
> escritos y **nadie los ha usado para producir nada**; lo mismo los campos
> `page_span` y `caption`. Su primer consumidor real es L5. Lo hace cumplir
> `tests/unit/test_sin_consumidor.py`, que lo comprueba **por AST** sobre `src/`
> y sobre los scripts que producen números publicados. Ver LIMITS 49.

**No hay ni un solo número de exactitud, de TEDS ni de coste.** A 22 de agosto de
2026, con L0 cerrado, hay esqueleto, modelo de datos y puerta de CI: ni corpus, ni
verdad de referencia, ni extractores. Cualquier número de calidad que apareciera
aquí estaría inventado. **El único número publicado hoy es un tiempo.**

| Número | Hito | Qué dirá |
|---|---|---|
| Primera tabla de estructura, con coste y cobertura evaluable | L5 | Qué extractor reconstruye mejor las tablas, cada métrica con su IC |
| **El titular**: hueco atribuible a la extracción | L10 | *"Con extracción perfecta X, IC [a,b]; con el mejor real Y, IC [c,d]; el hueco es Z puntos, IC [e,f]"* |
| Cuánto aporta la capa semántica | L11 | *"Cargar el glosario sube X puntos, IC [a,b]"* |

---

## L0 · Tiempo de la puerta rápida

Criterio: `make fast` en verde en menos de 90 s (§15 del manual). Es una de las
tres partes del criterio de L0; las otras dos —el control negativo y que
`lint-imports` encuentre `.importlinter`— no son números y están en
[`docs/metrics.md`](docs/metrics.md) y el [`CHANGELOG.md`](CHANGELOG.md).

### En el runner de GitHub · corrida del commit del cierre, `28186b9`

| Medida | Valor | Rango observado (n=4) | Resolución | Presupuesto | Margen |
|---|---|---|---|---|---|
| **`make fast`, el paso `la puerta`** | **4,43 s** | 3,41 – 4,43 s | ~0,1 s | **90 s** | **20×** |
| Job `fast` completo | 11 s | 10 – 14 s | 1 s | — | — |
| *Run* completo | 15 s | 14 – 18 s | 1 s | — | — |

**Sólo la primera fila es el criterio de L0.** El valor publicado es el de la
corrida del commit del cierre; el rango, el de las cuatro corridas que han corrido
este código. Qué mide cada fila, de dónde sale cada resolución y por qué el margen
de hoy no será el de L5: [`docs/metrics.md`](docs/metrics.md).

| Corrida | Commit | `make fast` | Job | Run | Ventana cruda (apertura → cierre) |
|---|---|---|---|---|---|
| [`32572385551`](https://github.com/marcosmatalab/docbench-es/actions/runs/32572385551) | `78ee8f0` | 3,41 s | 11 s | 16 s | `12:13:10.2845181Z` → `12:13:13.6938054Z` |
| [`32572585111`](https://github.com/marcosmatalab/docbench-es/actions/runs/32572585111) | `4e4ea0b` | 3,62 s | 10 s | 14 s | `12:17:28.7904222Z` → `12:17:32.4119044Z` |
| [**`32572683716`**](https://github.com/marcosmatalab/docbench-es/actions/runs/32572683716) | **`28186b9`** | **4,43 s** | **11 s** | **15 s** | `12:19:45.6204105Z` → `12:19:50.0508128Z` |
| [`32575381380`](https://github.com/marcosmatalab/docbench-es/actions/runs/32575381380) | `3a6b9d7` | 4,28 s | 14 s | 18 s | `13:18:23.8046256Z` → `13:18:28.0860583Z` |

**Mínimo 3,41 · mediana 3,95 · máximo 4,43 s · n=4.** La más lenta tarda **≈1,3×**
lo que la más rápida. La dispersión va como **razón entre extremos**, no como un
`±`: la mediana con n=4 es inestable —añadir esta cuarta corrida la movió de 3,62 a
3,95 s— y un `±` anclado a ella se movería con ella. **Léase el rango, no el
centro.**

- **Qué entra en la muestra, y hasta cuándo.** Las corridas de todo commit cuyo
  árbol de código sea idéntico al de `28186b9`. Los cuatro se diferencian sólo en
  markdown, y ningún `.md` entra en lo que mide la puerta. **Corte: 22 ago 2026.**
  El criterio es de inclusión, no de conveniencia: la muestra crece con cada commit
  de documentación, y una corrida que caiga fuera del rango se añade igual.
- **Fecha:** las cuatro el 2026-08-22 · **máquina:** runner estándar de GitHub,
  `ubuntu-latest`, 4 vCPU · **conclusión:** `success` en las cuatro.
- **Lo que ha cambiado desde `28186b9` fuera de markdown**, y por qué no afecta:
  `Makefile` —sólo el objetivo `clean`, que `make fast` no ejecuta— y `.gitignore`.
  Se comprueba con `git diff --name-only 28186b9 HEAD | grep -v '\.md$'`, que los
  nombra, y con `git diff 28186b9 HEAD -- Makefile`, que enseña que el objetivo
  `fast` es idéntico.
- **Reproducción** de las ventanas (las crudas están arriba porque los logs
  caducan) y de las columnas de job y run:
  ```bash
  for R in 32572385551 32572585111 32572683716 32575381380; do
    gh run view "$R" --repo marcosmatalab/docbench-es \
      --json createdAt,updatedAt,jobs \
      -q '"run \(.createdAt)->\(.updatedAt) job \(.jobs[0].startedAt)->\(.jobs[0].completedAt)"'
    JID=$(gh run view "$R" --repo marcosmatalab/docbench-es \
          --json jobs -q '.jobs[0].databaseId')
    gh api "repos/marcosmatalab/docbench-es/actions/jobs/$JID/logs" \
      | grep -E '##\[group\]Run make fast|\[100%\]'
  done
  ```
- La corrida comprueba además que el pin de Python se cumple: imprime
  `esperado=3.12 real=3.12`.

### En local · no sustituye al del runner

| Medida | Mediana | Rango observado (n=10) | Fecha |
|---|---|---|---|
| `make fast` en frío | **1742 ms** | 1715 – 1872 ms | 2026-08-22 |
| `make fast` en caliente | **723 ms** | 697 – 752 ms | 2026-08-22 |

En frío: `1750 1737 1752 1737 1747 1717 1715 1872 1732 1771`. En caliente:
`730 697 711 727 719 715 704 727 752 750`.

**Condición de máquina: en reposo**, `load average` 0,05. Se declara porque
importa: una tanda anterior tomada mientras corrían agentes de verificación en la
misma máquina dio una mediana 44 ms distinta. Ver [`docs/metrics.md`](docs/metrics.md).

- **Máquina:** AMD Ryzen 9 9950X3D, 8 vCPU asignadas a WSL2, 31 GB RAM ·
  Ubuntu 24.04.3 LTS sobre WSL2 (kernel 6.6.87.2) · Python 3.12.3 · uv 0.12.0.
  Medido dentro de WSL, en shell nativa.
- **Reproducción:**
  ```bash
  for i in $(seq 10); do
    make clean >/dev/null 2>&1; rm -rf .import_linter_cache
    s=$(date +%s%N); make fast >/dev/null 2>&1 || { echo "PUERTA EN ROJO"; break; }
    e=$(date +%s%N); echo "$(( (e - s) / 1000000 )) ms"
  done
  ```
  El `||` no es decoración: `make` para en el primer paso que falla, así que una
  puerta rota da un tiempo **menor**, no mayor. Sin comprobar el código de salida,
  el bucle publicaría ese número como si fuera bueno.
- Qué entra y qué no en «en frío», qué sobrevive aún, y por qué estas cifras no se
  comparan con las del runner: [`docs/metrics.md`](docs/metrics.md).

---

## L1 · Detección de tablas mal formadas, y el coste en la puerta

Criterio del manual (§16, fila L1): *«Las tablas con solape, hueco y span fuera de
rango se detectan al 100%»*.

### El número: 8.525 / 8.525 detectadas, 0 / 45 falsos positivos

| Medida | Valor | n | Método | Incertidumbre |
|---|---|---|---|---|
| **Tablas rotas detectadas** | **100%** (8.525 de 8.525) | 8.525 | Censo determinista y exhaustivo de mutaciones | **Ninguna: no es una estimación.** Es una tasa sobre el censo completo, así que no lleva intervalo (ADR-0015). Cero aleatoriedad: mismo resultado en cualquier máquina |
| **Falsos positivos · tablas base** | **0%** (0 de 45) | 45 | Las mismas tablas base, sin mutar | Idem |
| **Falsos positivos · huecos rellenados** | **0%** (0 de 3) | 3 | Mutaciones que NO rompen: crecer un span hacia un hueco de cola | Idem |
| **Condición 1 · aceptadas** | 40 de 40 | 40 | Familia «rowspan sobre fila corta», anchuras 2–5 × filas 2–5 × todos los cortes | Idem |
| **Condición 1 · las rechazaría la lectura descartada** | **40 de 40** | 40 | Idem, evaluando la lectura de la rejilla rellena | Idem |

**Las dos primeras filas van juntas o no significan nada.** Un validador que
rechazara toda tabla sacaría un 100% en la primera y un 100% de falsos positivos
en la segunda. La detección sin su control negativo no es detección: es pesimismo.

**Qué cubre el censo, y por qué el cero de falsos positivos pesa.** 45 tablas
base, y **no todas son sintéticas**:

- **36 sintéticas** = 9 tamaños × 4 patrones de combinación (celdas sueltas, fila
  larga, columna larga y bloque 2×2). Los tamaños incluyen **2×33 y 33×2**, porque
  33 es el span máximo que midió el sondeo del BOE y un validador que sólo
  funcionase con tablas pequeñas mediría su 100% sobre el caso fácil.
- **9 tablas de 8 formas REALES**, medidas en el sondeo sobre 600 documentos y
  metidas al censo **a través de `from_html`**, no construidas a mano: fila corta,
  `rowspan="0"` con `<thead>`/`<tbody>`, `<colgroup>` con `<col span>`, `<p>` y
  `<sup>` dentro de la celda, `<img>` como único contenido, `<caption>`, tabla
  anidada y el span 33. Un «cero falsos positivos» sobre una rejilla que no
  contuviera las formas del corpus afirmaría bastante menos de lo que suena.

**Meter las formas reales cambió el censo, y para bien.** Sobre una tabla con
hueco de cola, crecer un `colspan` **rellena el hueco** en vez de solapar, y la
tabla resultante es legal: es lo que se vería si la celda tuviera de verdad ese
span. El censo las contaba como «tendría que detectarse», o sea le pedía a
`validate` que rechazara HTML válido. Ahora son un control negativo aparte —la
fila «huecos rellenados» de la tabla—, que es lo que son. Sin las formas reales,
ese error del censo no habría aparecido.

Sobre cada base se aplican 17 familias de mutación —solape por `colspan` y por
`rowspan`, celda duplicada, **el solape del estándar que sale de HTML real**, span
fuera de rango por las dos caras, `rowspan` y `colspan` a 0, −1 y −7, posición
negativa, celda del medio borrada, `n_cols` inflado, dimensión negativa, celdas en
una tabla de cero filas, `page_span` invertido, `source_format` de fuera de los
cinco y `expresses_spans` mentido—, y **cada una tiene que salir con el código del
enum que le corresponde**, no sólo con un `False`. Los nueve códigos fatales y los
tres informativos quedan ejercitados; los dos que faltaban —`DIMENSION_INCOHERENTE`
y `SOURCE_FORMAT_DESCONOCIDO`— los añadió el escrutinio.

**Y para cinco familias se exige el conjunto EXACTO de códigos fatales, no la
pertenencia.** Un defecto de un solo sitio tiene que dar un solo código: la tasa
de tablas mal formadas por extractor de L5 se calcula por código, así que un
`colspan=0` que emitiera además `HUECO_INTERIOR` y `COLUMNA_VACIA` la inflaría y
la correlacionaría consigo misma. Lo hacía, y salió en el escrutinio.

- **Reproducción:**
  ```bash
  uv run python scripts/censo_invariantes.py; echo "codigo de salida: $?"
  ```
  El código de salida no es decoración: el script devuelve 1 si algo no se detecta
  o si hay un falso positivo, y sin comprobarlo un fallo se leería como un éxito.
- **Lo que este número NO cubre**, y está en [`LIMITS.md`](LIMITS.md) 30: los
  solapes se miden sobre el **censo mutado, no sobre HTML real**, porque
  `from_html` no puede producir un solape: el colocador desplaza a la derecha,
  como un navegador.

### La condición 1: la lectura descartada rechazaría el 100% del HTML legal

Las dos últimas filas de la tabla son el mismo censo mirado con las dos
definiciones posibles de «hueco interior». Sobre la familia donde un `rowspan`
baja de una fila de arriba y ocupa una columna a la derecha de donde se corta una
fila corta —HTML legal, que el navegador pinta sin quejarse—, **la lectura del
origen acepta las 40 y la lectura de la rejilla rellena rechazaría las 40**. Es la
evidencia de [ADR-0018](docs/adr/0018-hueco-de-cola-y-hueco-interior.md), y no es
un caso raro: el 42% de los documentos con tabla de las secciones I+III del BOE traen
`rowspan` > 1.

### Los dos mutantes: qué mata cada uno

La suite tiene que caerse contra las dos formas de estar roto. Recuentos reales:

| Suite | Sana | Contra `siempre_ok` | Contra `siempre_roto` |
|---|---|---|---|
| Invariantes y huecos (17) | 17 pasan | **11 fallan** | **14 fallan** |
| Normalización (18) | 18 pasan | **6 fallan** (identidad) | **12 fallan** (agresivo) · **1** (N3 incompleta) |
| Conversores (27) | 27 pasan | **25 fallan** (sin tablas) | **4 fallan** (ignora spans) |
| Clave de documento (4) | 4 pasan | **2 fallan** (sin escapar) | **2 fallan** (escapado en mal orden) |

- **Reproducción:** `uv run python scripts/mutantes/matar.py; echo $?` — devuelve 1
  si algún mutante sobrevive. Los nueve mutantes están versionados en
  `scripts/mutantes/`, porque la regla de oro 2 no distingue entre tipos de
  número: un recuento que sólo existe en el portapapeles de quien lo midió no se
  puede reproducir.

**Estos recuentos son un SUELO, no un valor fijo, y la diferencia importa.** Las
suites llevan tests de `hypothesis`, que sortea: un mutante que sólo caza una
propiedad muere unas veces y otras no. Medido, borrando `.hypothesis` entre
corridas: el mutante que devuelve N3 a `Cc ∪ Zs` —la regresión de U+2028— muere
en **1 test las cinco corridas** y en **2 sólo una de cada cinco**. El que muere
siempre es el determinista, que recorre los 1,1 millones de codepoints; la
propiedad lo caza **una vez de cada cinco**, porque tiene que sortear U+2028 entre
todo Unicode.

Es la justificación medida de por qué el test determinista se añadió **además** de
la propiedad, y no en su lugar: la propiedad **encuentra** lo que no se te ocurre
—encontró U+2028— pero **no sirve de candado**. El candado tiene que ser
determinista o el día que alguien reintroduzca el fallo, cuatro de cada cinco
veces la puerta se pondrá verde.

La última fila es la que costó un test nuevo. El escapado de `DocRef.key()` pasó
de `urllib.parse.quote` a uno escrito a mano —el contrato de capas prohíbe
`urllib` en `core`, y `core` importa `types`—, así que la inyectividad dejó de ser
de biblioteca y pasó a ser código del proyecto. **El test de L0 no puede
demostrarla**: genera los dos pares partiendo la misma cadena, así que uno es
siempre prefijo del otro y un fallo del escapado le queda fuera del alcance por
construcción. Medido: contra un escapado que sustituye `/` por `%2F` sin escapar
antes el `%` —y que colisiona de verdad, `esc("%2F") == esc("/")`— **el fichero de
L0 pasa 7 de 7**. Lo cubre ahora un censo exhaustivo sobre todas las cadenas de
hasta 3 caracteres del alfabeto `/%25Fa`, en `tests/unit/test_types_clave.py`.

El mutante agresivo del normalizador —quita acentos, pliega mayúsculas y repara el
separador decimal anglosajón— es el que importa: **es literalmente la trampa
silenciosa que prohíbe la regla de oro 7**, y la suite lo mata en 13 tests.

### El coste en la puerta

| Medida | Valor | Rango observado (n=10) | Resolución | Presupuesto | Margen |
|---|---|---|---|---|---|
| `make fast` en frío, local | **3829 ms** (mediana) | 3713 – 3875 ms | 1 ms (`date +%s%N`) | 90 s | **24×** |

L0 medía 1742 ms con el mismo método y la misma máquina: **L1 añade 2090 ms**, y
el reparto está medido, no repartido a ojo:

| Trozo | Coste | Cómo se midió |
|---|---|---|
| `mypy --strict` tipando ahora también `tests/` | **+1284 ms** | 1820 ms (`src tests`) − 536 ms (`src`), media de n=3 en frío, borrando `.mypy_cache` entre corridas |
| Los 67 tests nuevos y las 17 propiedades de `hypothesis` | **~806 ms** | El resto, por diferencia |

El test que recorre los 1,1 millones de codepoints Unicode cuesta **60 ms**
(`--durations`), o sea que no es él: el coste está repartido entre las
propiedades de `hypothesis`, que corren a 100 ejemplos. **Se sigue como
serie, no como dato suelto**, y con la regla escrita de qué se toca si algún día
aprieta —`--max-examples` por suite, nunca borrar tests—:
[`docs/metrics.md`](docs/metrics.md).

**Condición de máquina, declarada:** `load average` 0,93 al terminar la tanda,
contra el 0,05 de L0. **NO está en reposo**, y se dice porque L0 midió que la
condición mueve la mediana algunas decenas de ms —en la dirección contraria a la
intuitiva, además—. Una tanda anterior de esta misma sesión, con carga 0,18, dio
mediana 3832 ms: 3 ms de diferencia, dentro del rango de las dos. (Una tanda intermedia de esta misma sesión se tomó con 0,23–0,35 y dio
2742 ms para una puerta que entonces no tipaba los tests; no se publica porque no
es la misma puerta, no por la carga.)

**El número del runner de GitHub para L1 no está medido.** El criterio de §15 —90
s— es sobre el runner, y ahí no se puede medir sin una corrida de CI de este
commit. El local es 2,3× más rápido que el runner según la relación medida en L0;
extrapolando daría ~6,3 s, pero **eso es una extrapolación, no una medición**, y no
se publica como si lo fuera. Se mide en el PR.

- **Máquina y método:** los mismos que L0, ver [`docs/metrics.md`](docs/metrics.md).
- **Reproducción:** el bucle de L0, con su `||` que descarta las corridas en rojo.
  En la tanda publicada, **0 corridas descartadas**. En una tanda anterior de esta
  misma sesión se descartaron **10 seguidas con `rc=2`**, con una mediana de 64,5
  ms: **43 veces más rápida que la real**, porque `make` para en el primer paso
  que falla. Sin comprobar el código de salida, el fallo se habría publicado como
  la mejor noticia del hito. La causa y la regla que deja, en
  [`docs/metrics.md`](docs/metrics.md).

---

## L2 · TEDS validado contra PubTabNet

Criterio del manual (§16, fila L2): *«Coincide a cuatro decimales con la
referencia»*. §9.2 lo concreta: *«contra la implementación de referencia de
PubTabNet sobre sus propios casos»*.

### El número: 20 de 20 a cuatro decimales

| Medida | Valor | n | Población | Método |
|---|---|---|---|---|
| **Casos que coinciden a 4 decimales** | **20 de 20** (TEDS **y** TEDS-S) | 20 | **Los 20 casos propios de PubTabNet**: `src/sample_gt.json` y `src/sample_pred.json` de su repo. Tablas de artículos científicos, no del BOE | Golden calculado por **su** `metric.py` con APTED; comparado contra un Zhang-Shasha escrito a mano aquí |
| Coincidencia real | a **6 decimales** en los 20 | 20 | Idem | Idem |
| **Casos límite que coinciden** | **6 de 6** | 6 | Casos escritos a mano, no de PubTabNet: TEDS negativo, hueco/celda vacía en sus tres combinaciones, `<tbody>` de más, `<th>` por `<td>` | Idem, en `casos_limite.json` |

**No es una estimación**: es un recuento sobre el censo completo de casos
disponibles, así que **no lleva intervalo** (ADR-0015). Lleva su n, su población y
su comando.

- **Reproducción:**
  ```bash
  uv run pytest tests/unit/test_teds_referencia.py tests/unit/test_teds_limites.py -q; echo $?
  ```
  Y para regenerar el golden desde cero, con red:
  ```bash
  uv run --with apted --with distance --with lxml python scripts/pubtabnet_golden.py
  ```
  Determinista: regenerado dos veces en la sesión de L2, mismo SHA-256.

**El golden discrimina**, que es lo que casi nunca se comprueba: los 20 valores
van de **0,5883 a 1,0000**, con **15** valores distintos a cuatro decimales. Si fueran
todos unos, un `teds` que devolviera siempre 1,0 pasaría el criterio entero, y hay
un test que lo impide.

### Qué NO dice este número, y es la parte importante

**El golden se calcula sobre el render canónico de las tablas, no sobre el HTML
crudo de PubTabNet** (ADR-0020). La referencia no normaliza nada y cuenta en el
denominador el marcado inline dentro de las celdas —189 nodos `<b>`/`<i>`/`<sup>`
en sus 20 casos—, que `CanonicalTable` no guarda. Comparando contra sus valores
sobre el HTML crudo:

| Medida | Valor | Población |
|---|---|---|
| Casos idénticos | 5 de 20 | Los 20 casos de PubTabNet |
| **Casos que difieren** | **15 de 20** | Idem |
| …de ésos, **sólo por FORMA del árbol** (la normalización no toca ni un texto) | **10** | Idem |
| …de ésos, forma **y** normalización mezcladas, sin separar | 5 | Idem |
| Diferencia media (canónico − original) | **+0,0092** | Idem |
| Mediana | −0,0005 | Idem |
| Rango | [−0,0342, +0,2070] | Idem |

**La causa dominante no es normalizar: es la forma del árbol.** Sin descomponerlo
se habría atribuido a la normalización, que era la sospecha de partida.

El precio está en `LIMITS.md` 39: **estos TEDS no son directamente comparables con
los publicados en la literatura sobre PubTabNet.**

### Dos hallazgos sobre la métrica, no sobre esta implementación

| Hallazgo | Medido | La referencia |
|---|---|---|
| **TEDS puede ser NEGATIVO** | **−0,142857** sobre el par congelado en `casos_limite.json` | Devuelve **exactamente lo mismo**. El rango real es [−1, 1], no [0, 1] |
| **La referencia revienta con dos tablas vacías** | `ZeroDivisionError` | §12 define ese caso como **1**, y §12 gana. Congelado en el fixture como prueba |

El negativo lo encontró `hypothesis`, no la revisión: un test afirmaba
`0 <= teds <= 1` y era falso. **Consecuencia para L5**, en `LIMITS.md` 44: §12
publica TEDS como nota, y una nota negativa no se pondera igual.

### Hueco contra celda vacía: la distinción de L1, medida

| Predicción contra la misma verdad completa | TEDS | TEDS-S |
|---|---|---|
| Con **celda vacía** | 0,857143 | **1,000000** |
| Con **hueco** | 0,857143 | **0,857143** |

En TEDS-S la distinción es nítida. En TEDS completo coinciden contra la tabla
completa —borrar un nodo cuesta 1 y renombrar una celda vacía también—, y la
distinción aparece **cuando la verdad es la que tiene el hueco**, que es el caso
del BOE con sus filas cortas: ahí quien reproduce el hueco saca 1,0.

**Corrección a L1:** `core.teds` **no llama a `holes()`**, y hay un test que lo
comprueba por AST. La distinción se respeta por construcción del árbol. La
justificación de L1 —«`holes()` es lo que L2 usa»— era optimista y queda
corregida en ADR-0018, en el código y aquí.

### El mapeo `CanonicalTable → árbol`, que el criterio de aceptación NO valida

El criterio de L2 —**20 de 20 a cuatro decimales**— demuestra que este
Zhang-Shasha calcula lo mismo que APTED. **No demuestra que el árbol sea el
correcto**, porque el golden se generó dando a la referencia el render canónico
de las mismas tablas: `T` aparece en los dos lados y se cancela. Medido con dos
mutantes de `_arbol.py` contra el fixture congelado:

| Mutante | Qué rompe del HTML | Antes del cierre | Ahora |
|---|---|---|---|
| `arbol_orden_invertido` | **los 20** casos | 145 passed | **20 tests + 1 a mano** |
| `arbol_thead_solo_la_primera` | **6** de 20 | 145 passed | **7 tests** |

Y regenerando el golden con la referencia real bajo esos mutantes, **seguía
verde**: un error presente el día de la generación sería invisible para siempre.
Tapado con un candado de regresión —los campos `html_canonico_*` que el fixture ya
guardaba y nadie miraba— más dos casos a mano. Lo que sigue sin validarse, en
`LIMITS.md` 52.

`uv run pytest tests/unit/test_teds_referencia.py -q` → **46 passed**

### Lo que ninguna propiedad puede ver

| Mutante | Propiedades que lo cazan |
|---|---|
| `arbol_orden_invertido` | **0 de 6** de `test_teds_propiedades.py` |
| `arbol_thead_solo_la_primera` | **0 de 24** propiedades de todo el repo |

**No es que falten propiedades: es que un invariante no puede ver un reetiquetado
consistente.** Rango, simetría y «una tabla contra sí misma vale 1» se siguen
cumpliendo si `T` cambia igual en los dos lados. La única que sí lo ve —
`test_mover_la_frontera_de_la_cabecera_cambia_la_estructura`— **perturba un solo
lado**, y para existir hizo falta arreglar la estrategia:

| | `n_cabecera >= 2` alcanzado |
|---|---|
| `_estrategias.py` como estaba (`is_header = fila == 0`) | **0 de 300** — inalcanzable |
| con el sorteo de 0 a 2 | **11 de 300** — alcanzable, pero ~1 caso por suite |
| `tabla_con_dos_filas_de_cabecera` | **300 de 300**, a propósito |

Y con las dos primeras el mutante **sobrevivía**. Sólo la tercera lo mata.

### El coste de TEDS por tamaño de tabla

`uv run python scripts/coste_teds.py`, mediana de 3, tablas sin spans. **No es una
estimación**: son tiempos, con su n y su resolución (ms).

| Tabla | Celdas | Un `teds()` |
|---|---|---|
| 10x5 | 50 | 9 ms |
| 20x8 | 160 | 101 ms |
| 40x8 | 320 | 447 ms |
| 60x10 | 600 | **1617 ms** |
| 80x10 | 800 | **2979 ms** |
| 100x10 | 1000 | **4712 ms** |

`_distancia.py` y el límite 42 afirmaban que «para una tabla de documento es
inmediato» y que sólo se dispara con «miles de filas». **Las dos cosas eran falsas
y ninguna estaba medida.** La consecuencia es de L5 y está escrita en el límite 42
con sus tres salidas.

### El censo de invariantes, ahora por familia

`uv run python scripts/censo_invariantes.py --familias`

| | |
|---|---|
| detección de tablas rotas | **8525 / 8525** |
| familias de mutación | **20, ninguna vacía** |
| falsos positivos sobre las 45 tablas base | **0 / 45** |
| falsos positivos sobre mutaciones LEGALES | **0 / 3** |

El desglose por familia es nuevo y no es cosmético: **un 8525/8525 sale verde
igual si una familia deja de generar mutantes**. El total no lo ve; el recuento
por familia sí, y el censo se pone rojo si alguna queda a cero.

### Los mutantes

**Son 18**, y las cuatro casillas de `siempre_ok` × `siempre_roto` están completas
sobre las dos funciones que L2 construye. `siempre_roto` no es simetría decorativa:
es el único que caza al test que sólo afirma la mitad tranquilizadora —«esto BAJA
la nota»—, que un 0,0 constante satisface entero.

| Función | `siempre_ok` | falla en | `siempre_roto` | falla en |
|---|---|---|---|---|
| `teds` / `teds_struct` | `teds_siempre_uno` | **18 de 54** | `teds_siempre_cero` | **34 de 65** |
| `cell_accuracy` / `cell_f1` | `cellmatch_siempre_ok` | **3 de 7** | `cellmatch_siempre_roto` | **6 de 7** |

Y los cuatro sutiles, que son los que justifican el hito:

| Suite | Mutante | Se cae en |
|---|---|---|
| TEDS referencia (23) | `teds_cuenta_la_raiz` — el denominador incluye la raíz | 13 |
| TEDS referencia (44) | `arbol_orden_invertido` — el árbol emite las columnas al revés | 20 |
| TEDS referencia (44) | `arbol_thead_solo_la_primera` — `<thead>` no es el prefijo máximo | 7 |
| TEDS lote (7) | `batch_sobrescribe` — la última tabla pisa a las demás | 3 |
| cellmatch (7) | `cellmatch_por_pertenencia` | 2 |

**Los dieciocho mutantes del repo mueren**, con control negativo **0 de 149**.
`uv run python scripts/mutantes/matar.py; echo $?`

`teds_cuenta_la_raiz` es el que justifica el hito: mueve **todos** los TEDS un
poco hacia arriba, en todos los casos, y **sólo lo caza comparar con la
referencia**. Ninguna propiedad ni ninguna gráfica lo vería.

### El alcance de esa afirmación, con su n y su agregación

La conclusión anterior salió de **un** mutante, así que se midieron **los 12, tres
repeticiones en frío cada uno**, con `uv run python scripts/mutantes/matar.py --tabla`.

**Control negativo primero: el árbol SIN mutar da 0 muertes de 149 tests.** Sin
ese cero la tabla no valdría nada — cada «muerte» podría ser un fallo de fondo de
la suite y no el mutante. Lo comprueba el propio arnés antes de empezar y aborta
si no es cero.

**El arnés no cubre la suite entera: 149 de 177.** El control negativo y
`matar.py` sin argumentos corren la **unión de las suites objetivo** del `PLAN`.
Los **28 restantes** —`test_types_invariantes` (7), `test_ancla` (5),
`test_recuentos` (5), `test_types` (5), `test_errors` (3) y
`test_sin_consumidor` (3)— quedan fuera
porque **no hay ningún mutante escrito contra su código**: el enum de errores, las
invariantes de tipos y las barreras por AST. Así que «los 18 mutantes mueren» dice
que **esos 18** huecos están tapados, **no** que la suite esté medida. Algunos de
esos 28 sí matan mutantes cuando `--tabla` recorre la suite entera, pero eso es
daño colateral, no cobertura diseñada.

**Bajó de 38 a 28** porque `test_teds_limites` y `test_teds_batch` **ya tienen
mutante**: los añadió este cierre.

**Las dos columnas son dos agregaciones distintas sobre las 3 repeticiones**, y la
diferencia es información: **SIEMPRE** es la intersección —muere en las tres— y
**ALGUNA VEZ** es la unión. *Un asesino intermitente no es un asesino*: depende de
que un sorteo de `hypothesis` salga bien.

**Son 18 mutantes, no 12**: el escrutinio y el paso 2 de `/cerrar` añadieron seis
—los dos del árbol, el del lote, y las tres casillas que faltaban de
`siempre_ok` × `siempre_roto` sobre las dos funciones que L2 construye—.

| Mutante | Lo matan SIEMPRE | Lo matan ALGUNA VEZ | Intermitente, con su tasa |
|---|---|---|---|
| `sin_tablas` | 41 | 41 | — |
| `roto` | 24 | 24 | — |
| `ok` | 14 | 14 | — |
| `teds_siempre_uno` | 12 | 12 | — |
| `sin_spans` | 11 | 11 | — |
| `teds_siempre_cero` | 10 | 10 | — |
| `normalizador_agresivo` | 8 | **9** | `test_idempotente` 2/3 |
| `teds_cuenta_la_raiz` | 8 | 8 | — |
| `normalizador_identidad` | 6 | **7** | la propiedad de normalización 1/3 |
| `cellmatch_siempre_roto` | 6 | 6 | — |
| `arbol_thead_solo_la_primera` | 3 | 3 | — |
| `cellmatch_siempre_ok` | 3 | 3 | — |
| `clave_sin_escapar` | 3 | 3 | — |
| `arbol_orden_invertido` | 2 | 2 | — |
| `batch_sobrescribe` | 2 | **3** | la propiedad del lote 2/3 |
| `cellmatch_por_pertenencia` | 2 | 2 | — |
| `clave_orden_malo` | 2 | 2 | — |
| `n3_incompleta` | **1** | 1 | — |

**La columna de la derecha la escribe el arnés solo**, y es la que faltaba: sin
ella, dos corridas de la misma tabla daban columnas distintas y no había forma de
saber por qué. Aquí se ve que las tres diferencias tienen nombre y tasa.

> **Léase la columna SIEMPRE como lo que es: una estimación Bernoulli con n = 3,
> no una categoría.** Un asesino que mata con probabilidad p sale clasificado como
> «SIEMPRE» con probabilidad p³. La p medida aquí —`test_idempotente`— es
> **26 de 30**, o sea **p̂ = 0,867, Wilson 95% [0,703 – 0,947]**, y la tasa de mala
> clasificación derivada es **p̂³ = 66%, con intervalo [35% – 85%]**.
>
> **Ese intervalo es el número honesto, y el 66% solo era el punto.** Va con
> intervalo porque es una ESTIMACIÓN sobre 30 corridas aleatorias, no un censo
> (regla de oro 2, ADR-0015): 30 sorteos de `hypothesis` no fijan una tasa. Lo que
> se puede afirmar es que la columna se equivoca **entre un tercio y cinco sextos
> de las veces** para un asesino de esta p — que sigue siendo demoledor para la
> palabra «SIEMPRE», y por eso el aviso está aquí y no sólo en el
> [límite 50](LIMITS.md). Para afinar un caso concreto:
> `uv run python scripts/mutantes/matar.py --tabla --reps 10 --solo EL_MUTANTE`.

**La afirmación, recontada contra esta tabla:** sobre los 18 mutantes existentes,
la propiedad de normalización **no es la única asesina de ninguno**; es asesina
**determinista** de `normalizador_agresivo` —donde además hay otros ocho— y
aparece **esporádicamente** sobre otros dos, `n3_incompleta` y
`normalizador_identidad`, **1 de 3 en tandas distintas**. Así que «participa en
dos» era corto y «participa en tres» sería largo: participa en uno de forma
estable y asoma en otros dos según el sorteo, y **la tabla de una sola tanda no
puede decir en cuántos**. Ése es el contenido real del límite 50.

Esa fila de `normalizador_identidad` es, además, la demostración de que el arreglo
del arnés funciona: la línea `1/3` que va debajo la puso `--tabla` solo, y sin ella
esta tabla habría vuelto a tener dos columnas distintas sin decir por qué.

### Los dos errores que costó llegar a esa tabla

> **Uno: la cifra decía «participa en dos» y la tabla de al lado no lo dejaba
> comprobar.** No era falsa, pero la tabla sólo daba recuentos, así que el lector
> sólo podía verificar el intermitente y contaba uno. El fallo fue publicar una
> afirmación que la tabla de al lado no permitía comprobar. Corregido con la
> columna de la derecha y con la agregación puesta en la cabecera.

> **Dos, y éste sí era una cifra mal contada: el arnés contaba una línea `FAILED`
> por PARÁMETRO.** Al reescribir `--tabla` para publicar las dos agregaciones se
> perdió el colapso por corrida, así que un test parametrizado sumaba una vez por
> caso: `test_teds_coincide_con_la_referencia_a_cuatro_decimales` contaba **39**
> —13 casos × 3 corridas— en vez de 3, no cumplía `n == 3` y **salía de la columna
> SIEMPRE aunque mate en las tres**. Afectaba a cinco filas. Corregido con un
> `set` por corrida, y el porqué está escrito en el propio `matar.py`.

### Reconciliación con la tabla anterior, porque las dos están publicadas

Alguien va a comparar las tres versiones, así que van las tres, con las columnas
puestas siempre en el mismo orden **SIEMPRE / ALGUNA VEZ**:

| Mutante | A · primera | B · con el bug de recuento | C · buena, la de arriba |
|---|---|---|---|
| `sin_tablas` | 37 / 37 | 36 / 38 | **39 / 39** |
| `roto` | 24 / 24 | 23 / 24 | **24 / 24** |
| `ok` | 13 / 13 | 13 / 14 | **14 / 14** |
| `teds_siempre_uno` | 9 / 9 | 8 / 10 | **10 / 10** |
| `teds_cuenta_la_raiz` | 7 / 7 | 6 / 8 | **8 / 8** |
| `normalizador_agresivo` | 9 / 9 | 8 / 9 | **9 / 9** |
| `cellmatch_por_pertenencia` | 1 / 1 | 1 / 1 | **2 / 2** |
| `n3_incompleta` | 1 / 2 | 1 / 1 | **1 / 1** |
| `normalizador_identidad` | 6 / 6 | 6 / 6 | **6 / 7** |

**La respuesta a «otra pregunta o error de recuento» es: error de recuento, y
estaba en la tabla nueva, no en la vieja.** La cabecera de A decía literalmente
«nº tests que lo matan / de ésos, SIEMPRE», o sea **las mismas dos agregaciones**:
no era otra pregunta. A y C coinciden en todo salvo en los tests añadidos entre
una y otra —+2 en `sin_tablas`, +1 en `ok`, `teds_siempre_uno` y
`teds_cuenta_la_raiz`, y el segundo asesino de `cellmatch`—. **B queda superada
por C.**

**Y el 8 de B tiene nombre y aritmética**: de los nueve asesinos de
`normalizador_agresivo`, `test_r4_los_numeros_llegan_intactos` está parametrizado
con **7 casos**, así que contaba 7 × 3 = **21**, distinto de 3, y quedaba fuera de
SIEMPRE. Nueve menos ése son ocho. No hacía falta ninguna hipótesis sobre la
propiedad de normalización.

**Lo que la investigación destapó de paso, y que no es el bug:** medido con
`--reps 10`, `test_idempotente` —otro de los nueve— mata **7/10, 9/10 y 10/10** en
tres tandas de diez, o sea **26 de 30**, p̂ ≈ 0,87. Con esa p, una tanda de tres
lo llama «SIEMPRE» el **66%** de las veces, Wilson 95% [35% – 85%]. **La columna SIEMPRE no es una
categoría, es una estimación con n = 3**, y por eso el n va publicado a su lado y
`--reps` existe.

Reproducción: `uv run python scripts/mutantes/matar.py --tabla` ·
`… --tabla --reps 10 --solo normalizador_agresivo` lista **todos** los asesinos
con su tasa, que es lo que permite afirmar el 10 de 10 de la propiedad en vez de
deducirlo de una ausencia.

### El punto único de fallo que queda, y qué se hizo con el otro

La tabla los delata: un mutante al que mata **un solo test** es una garantía
sostenida por una sola aserción.

| Mutante | Único asesino | Qué se hizo |
|---|---|---|
| `cellmatch_por_pertenencia` | `test_una_celda_repetida_no_cuenta_dos_veces` | **Segundo asesino añadido**: `test_la_exactitud_no_puede_pasar_de_uno`, con otra forma de tabla y mirando la cota superior de la tasa en vez del recuento. Ahora lo matan 2 |
| `arbol_orden_invertido` | `test_el_render_canonico_es_el_que_genero_el_golden` | **Apareció al añadirlo**, y era la peor dependencia posible: su único asesino es un candado contra un fixture que salió de esa misma función (límite 52). **Segundo asesino añadido**: `test_las_celdas_de_una_fila_salen_en_orden_de_columna`, a mano y sin fixture. Ahora lo matan 2 |
| `n3_incompleta` | `test_n3_cubre_exactamente_lo_que_split_considera_espacio` | **Se intentó y NO se pudo.** Sigue en 1, y se declara |

**Por qué `n3_incompleta` no puede tener un segundo asesino de texto**, medido:
`str.split()` **también** considera espacio a U+2028 y U+2029, así que
`"a\u2028b"` da `"a b"` con N3 correcta **y** con N3 mutada. El daño queda
enmascarado en todo caso de texto; sólo lo ve un test que consulte la **categoría
declarada** en vez del texto resultante. Las dos aserciones que se añadieron
documentan el comportamiento pero **no sirven de candado**, y así está escrito en
el propio test para que nadie las cuente como cobertura.

**El arnés recorre la tabla en cada cierre**: `matar.py --tabla` es un paso de
`/cerrar`, así que el punto único que queda está vigilado en vez de guardado.

### El coste en la puerta

| Medida | Valor | Rango (n=10) | Presupuesto | Margen |
|---|---|---|---|---|
| `make fast` en frío, local, **tanda 1** | **5440 ms** | 5187 – 5497 ms | **6000 ms** (fijado para L2) | 560 ms |
| `make fast` en frío, local, **tanda 2** | **5473 ms** | 5330 – 5616 ms | Idem | **527 ms** |

**Dos tandas no caracterizan la distribución**, y al cerrar L2 se midió en serio:
**40 corridas en frío, 10 tandas de 4**, `make clean` —que borra `.hypothesis`—
antes de cada una, cero descartadas por código de salida.

| | Al detectar el problema | **Al cerrar**, con los tests nuevos |
|---|---|---|
| mínimo | 5382 | 5463 |
| **mediana** | 5517 | **5604** |
| **p90** | 5801 | **5728** |
| máximo | 5858 | 5775 |
| desviación típica | 134 (CV 2,4%) | 76 |
| medianas por tanda | 5459 – 5691 | 5539 – 5661 |

Las dos con el mismo protocolo, ahora ejecutable en una orden:
`uv run python scripts/medir_puerta.py --techo 8500; echo $?` — devuelve 1 si el
p90 pasa del techo.

**Remedido al cerrar, con la suite ya en 177 tests** (n=40 en 10 tandas en frío,
0 descartadas):

| | ms |
|---|---|
| mínimo | 5140 |
| mediana | **5593** |
| p90 | **5933** |
| máximo | 6048 |
| desviación típica | 286 |
| medianas por tanda | 5304 – 5820 |

**Margen en el p90 sobre el techo de 8500: 2567 ms.** Y el dato que confirma el
diagnóstico de ADR-0022: la suite pasó de **145 a 177 tests** —+32, o sea +22%— y
la mediana se movió de 5604 a **5593**, o sea **nada**. Lo que domina es el
arranque del proceso, no los tests, exactamente como decía la condición de parada
número 2. La σ sube de 76 a 286 y **no sé por qué**: es estado de la máquina, y la
carga no se registró (deuda de L3, `medir_puerta.py` debería anotarla).

**Lo que cuesta el comprobador de recuentos, aislado del estado de la máquina**
(`pytest tests/unit` con y sin `--ignore=tests/unit/test_recuentos.py`, mediana de
3 corridas en frío):

| | ms |
|---|---|
| con el comprobador | 3960 |
| sin él | 3790 |
| **coste** | **170 ms** |

Se mide así y no comparando medianas de `make fast` entre commits porque **la
mediana se movió 395 ms entre dos tandas de distinto tamaño** —5593 con n=40,
5988 con n=12— y atribuir eso al mecanismo sería el mismo error que atribuir a la
suite la bajada de σ de 134 a 76. Aislar los dos lados en la misma corrida es lo
único que separa el coste del ruido.

> **La σ baja de 134 a 76 y eso NO se atribuye a la suite.** Añadir cuatro tests
> no reduce la dispersión de un tiempo; si acaso la sube. La bajada es **estado
> de la máquina entre las dos tandas**, y **no sé qué cambió**: las dos se
> tomaron con minutos de diferencia en el mismo equipo, la primera con
> `load average` 0,19–0,41 y de la segunda no se registró la carga. No se
> reconstruye a posteriori, así que se deja escrito que no se sabe en vez de
> inventarle una causa. Lo que sí queda es una regla: `medir_puerta.py` debería
> registrar la carga junto al tiempo — **deuda de L3**.

**El p90 consumía el 97% del techo de 6000**: 199 ms de margen, o sea 1,5
desviaciones típicas. Eso no es margen, es estar dentro por suerte. El techo pasa
a **8000 ms local / 20 000 ms en CI** por [ADR-0022](docs/adr/0022-el-techo-de-la-puerta.md),
que además fija **qué pasa al romperse**: el techo **avisa**, y lo que **bloquea**
es el presupuesto de 90 s del manual. Proyección escrita allí: **6000 no aguanta
L3 en ningún escenario**, ni siquiera en el más optimista.

Contra los 90 s de §15 el margen es de **16×** (90 000 / 5604 = 16,1). Aquí decía
**17×**, que salía de dividir por la mediana vieja; ADR-0022 publica 16× y una
cifra del mismo margen no puede salir distinta en dos documentos. Reparto medido de los pasos, en
frío:

| Paso | Coste |
|---|---|
| `pytest tests/unit` (145 tests) | ~3800 ms |
| `mypy --strict src tests` | 1614 ms |
| `lint-imports` | 132 ms |
| `ruff check` + `ruff format --check` | 102 ms |

**Se declaró presupuesto de ejemplos en las ocho suites de propiedad**, que antes
heredaban el 100 por defecto sin decirlo: 100 en las dos que protegen la
normalización y la clave de documento, 60 en los invariantes, 50 y 30 en el resto.

> **CORREGIDO al cerrar L2.** Este párrafo publicaba que bajar la suite de
> normalización de 100 a 50 ejemplos ahorraba **~285 ms**, y decía que estaba
> medido. **No lo estaba: era una estimación** sacada de suponer que el coste de
> un test escala con `max_examples` partiendo de que `test_r1` cuesta 570 ms.
> Medido de verdad —media de 5 corridas en frío por presupuesto— la suite cuesta
> **990 ms a 100, 946 a 50 y 935 a 25**: la palanca vale **44 ms**, no 285,
> porque el coste lo domina el arranque del proceso (~900 ms), no los ejemplos.
> Y también se midió lo otro, que no se puede suponer: contra el mutante que
> reintroduce la regresión de U+2028, la propiedad la caza **0 de 15** veces a
> 100 ejemplos —Wilson 95% [0,000 – 0,204]— y **2 de 15** a 50 —[0,037 – 0,379]—.
> **Los dos intervalos se solapan casi enteros**, y eso es lo que permite decir
> «ruido» en vez de «bajar ejemplos caza más»: sin ellos, 0 contra 2 se lee como
> una mejora del doble. Ver
> [ADR-0022](docs/adr/0022-el-techo-de-la-puerta.md).
