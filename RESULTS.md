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

  > **El 33 llevaba una etiqueta falsa: «el máximo observado en el sondeo».** Es el
  > máximo de **una** ventana. Recomputado sobre las tres (n=600,
  > `docs/sondeo-boe-*.json`): otoño **59**, agosto 33, primavera 22. El censo
  > mantiene la forma de 33 —cambiarla movería este mismo 8.525— y **la distancia
  > hasta 59 queda declarada como cobertura que falta**, no escondida detrás de la
  > etiqueta. Detectado al preparar L3.

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

**Son 22 mutantes, no 18**: los tres de `recuentos` entraron con el guardián de
números y esta línea no se actualizó entonces. Las cuatro casillas de `siempre_ok`
× `siempre_roto` están completas sobre las dos funciones que L2 construye.
`siempre_roto` no es simetría decorativa: es el único que caza al test que sólo
afirma la mitad tranquilizadora —«esto BAJA la nota»—, que un 0,0 constante
satisface entero.

**Sello de las dos tablas: `099e452+29 · 164 tests`**, que lo imprime la propia
corrida de `uv run python scripts/mutantes/matar.py` (24 ago 2026). El `+29` son
los ficheros sin commitear: **esta medición no es reproducible desde ningún
commit**, y quien la lea tiene derecho a saberlo antes de compararla con la suya.

| Función | `siempre_ok` | falla en | `siempre_roto` | falla en |
|---|---|---|---|---|
| `teds` / `teds_struct` | `teds_siempre_uno` | **19 de 56** | `teds_siempre_cero` | **34 de 67** |
| `cell_accuracy` / `cell_f1` | `cellmatch_siempre_ok` | **3 de 7** | `cellmatch_siempre_roto` | **6 de 7** |

Y los cuatro sutiles, que son los que justifican el hito:

| Mutante | Se cae en |
|---|---|
| `teds_cuenta_la_raiz` — el denominador incluye la raíz | 13 de 45 |
| `arbol_orden_invertido` — el árbol emite las columnas al revés | 21 de 45 |
| `arbol_thead_solo_la_primera` — `<thead>` no es el prefijo máximo | 7 de 45 |
| `batch_sobrescribe` — la última tabla pisa a las demás | 3 de 7 |
| `cellmatch_por_pertenencia` | 2 de 7 |

> **Estas cifras NO las vigila ningún guardián, y se mueven solas. Por eso llevan
> sello.** El denominador es la suite objetivo del mutante, así que **crece cada
> vez que alguien añade un test** — sin que el mutante cambie ni empeore. La
> versión anterior de estas dos tablas publicaba `18 de 54`, `34 de 65` y `20`,
> medidos con una suite más pequeña, y **L3 entero las estuvo publicando sin que
> nadie pudiera saberlo leyendo**: la fecha no delata que la suite ha crecido, el
> commit sí. Se re-miden en cada cierre (paso 2 de `/cerrar`) y el sello las hace
> honestas entre medias.
>
> **Y el numerador tampoco es constante:** las suites llevan `hypothesis`, que
> sortea. Dos corridas con el **mismo `src/` y los mismos 163 tests** dieron
> `normalizador_identidad` en 5 y en 6, y `n3_incompleta` en 2 y en 1. Lo que se
> exige es **«muere»**, no «muere en N tests»: estas cifras son un **suelo**, no
> una constante.

**Los veintiún mutantes de esa corrida mueren**, con control negativo **0 de 164** —
mismo sello, misma línea, ver la corrección de más abajo—.
`uv run python scripts/mutantes/matar.py; echo $?`

`teds_cuenta_la_raiz` es el que justifica el hito: mueve **todos** los TEDS un
poco hacia arriba, en todos los casos, y **sólo lo caza comparar con la
referencia**. Ninguna propiedad ni ninguna gráfica lo vería.

### El alcance de esa afirmación, con su n y su agregación

La conclusión anterior salió de **un** mutante, así que se midieron **los 12, tres
repeticiones en frío cada uno**, con `uv run python scripts/mutantes/matar.py --tabla`.

**Control negativo primero: el árbol SIN mutar da 0 muertes de 166 tests.** Sin
ese cero la tabla no valdría nada — cada «muerte» podría ser un fallo de fondo de
la suite y no el mutante. Lo comprueba el propio arnés antes de empezar y aborta
si no es cero.

**El arnés no cubre la suite entera: cubre 166 de 561 tests.** El control negativo y
`matar.py` sin argumentos corren la **unión de las suites objetivo** del `PLAN`.
Los **395 tests restantes** —`test_congelados_l4` (38), `test_barreras` (14), `test_barreras_documentos` (2),
`test_harvest` (14), `test_verificar_corpus` (14), `test_boe` (12),
`test_boe_api` (10), `test_entity_conformance` (9), `test_entity_registry` (9),
`test_capas_permitidas` (8), `test_manifest` (8), `test_pairing` (8),
`test_guardianes_l4` (7), `test_guardianes_por_glob` (9), `test_documentos_que_sostienen` (8), `test_policy` (7),
`test_types_invariantes` (7), `test_boe_xml` (6), `test_ancla` (5),
`test_comparar_verdad` (5), `test_types` (6), `test_sellar_xml` (4),
`test_estimador_computo` (6), `test_extractor_contrato` (37), `test_extractor_conformidad` (13),
`test_conjunto_conformidad` (5), `test_formatos_spans` (2), `test_errors` (3), `test_sin_consumidor` (3),
`test_reglas_parseables` (3), `test_limite_lineas` (2) y `test_tope_area` (2)— quedan fuera
porque **no hay ningún mutante escrito contra su código**: el enum de errores, las
invariantes de tipos y las barreras por AST. Así que «los 22 mutantes mueren» dice
que **esos 22** huecos están tapados, **no** que la suite esté medida. Algunos de
esos 218 sí matan mutantes cuando `--tabla` recorre la suite entera, pero eso es
daño colateral, no cobertura diseñada.

**Han ido saliendo tres ficheros de esta lista** conforme se les escribía mutante:
`test_teds_limites` (`teds_siempre_cero`), `test_teds_batch` (`batch_sobrescribe`)
y `test_recuentos` (los tres `recuentos_*`). Se nombran en vez de publicar la
resta: un «bajó de 38 a 23» obliga al lector a fiarse de una aritmética que no
puede comprobar, y **se queda viejo en silencio** en cuanto entra el siguiente.

**Las dos columnas son dos agregaciones distintas sobre las 3 repeticiones**, y la
diferencia es información: **SIEMPRE** es la intersección —muere en las tres— y
**ALGUNA VEZ** es la unión. *Un asesino intermitente no es un asesino*: depende de
que un sorteo de `hypothesis` salga bien.

**Son 22 mutantes**, y esta es su composición completa, sin sumas que cuadrar:

| De dónde salen | Cuáles |
|---|---|
| **L0 y L1** (9) | `ok`, `roto`, `normalizador_identidad`, `normalizador_agresivo`, `n3_incompleta`, `sin_tablas`, `sin_spans`, `clave_sin_escapar`, `clave_orden_malo` |
| **L2, el hito** (3) | `teds_siempre_uno`, `teds_cuenta_la_raiz`, `cellmatch_por_pertenencia` |
| **El escrutinio adversarial** (3) | `arbol_orden_invertido`, `arbol_thead_solo_la_primera`, `batch_sobrescribe` |
| **El paso 2 de `/cerrar`** (3) | `teds_siempre_cero`, `cellmatch_siempre_ok`, `cellmatch_siempre_roto` |
| **La auditoría en frío del guardián** (3) | `recuentos_todo_vale`, `recuentos_sin_claude`, `recuentos_plano_flojo` |
| **El arreglo del grupo de filas** (1) | `seccion_sin_cerrar` |

> **Aquí ponía «Son 21 mutantes, no 12: … añadieron seis», y 12 + 6 = 18.** El
> guardián de recuentos había actualizado el dígito de 18 a 21 —porque el patrón
> `[Ss]on {_N} mutantes, no \d+` lo ve— y **la enumeración de al lado siguió
> nombrando seis**. El número quedó correcto dentro de una frase que se
> contradecía sola, que es más difícil de ver leyendo que un número viejo en una
> frase coherente. Ver `LIMITS.md` 55. La tabla de arriba sustituye la suma por
> una enumeración exhaustiva: si falta uno, se ve sin restar.

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

**La afirmación, recontada contra esta tabla:** sobre los 22 mutantes existentes,
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

| Mutante | A · primera | B · con el bug de recuento | C · buena, **de aquel día** |
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

> **CORREGIDO en la auditoría en frío de `a0d85ed`: la columna C decía «la de
> arriba» y NO es la de arriba.** `sin_tablas` sale **39** aquí y **41** en la tabla
> de asesinos de más arriba; `teds_siempre_uno` **10** contra 12;
> `normalizador_agresivo` **9/9** contra 8/9. Son **tres corridas** sobre suites de
> tamaños distintos, y las dos tablas se escribieron en el **mismo commit** con una
> rotulada como si fuera la otra. La prosa de este párrafo sólo cuadra con C, que es
> la de **aquel día**; la de arriba es posterior y más grande.
>
> **Es la misma clase que el sello de L3 y que la fila de L2**: dos mediciones de
> momentos distintos presentadas como una. El sello existe justo para esto —`sello:
> <commit> · N tests`— y estas tablas no lo llevan. **Que lo lleven es trabajo de
> L5**, y va con su precio: re-correr `--tabla` con `--reps 3` sobre el árbol actual
> son ~10 minutos de máquina, más el sello. No se hace hoy porque re-correrlo ahora
> daría una cuarta columna sin resolver cuál de las tres describía qué, que es
> exactamente el lío que hay que deshacer.

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

### La línea base de L3, con n=40 y la carga registrada

`uv run python scripts/medir_puerta.py --techo 8500`, 40 corridas en frío en 10
tandas, cero descartadas:

| | ms |
|---|---|
| mínimo | 5801 |
| **mediana** | **6004** |
| **p90** | **6134** |
| máximo | 6238 |
| desviación típica | **83** |
| medianas por tanda | 5931 – 6081 |
| **carga de la máquina** | mediana **0,93**, rango 0,50–1,11 |

**Margen hasta el techo de 8500: 2366 ms sobre el p90.** Ése es el presupuesto que
L3 puede gastar en la puerta.

> **La carga se registra desde esta tanda**, y cierra la deuda que llevaba cuatro
> cierres apuntada. La desviación típica de este mismo protocolo ha ido **134, 76,
> 286, 73 y 83**, y hasta hoy la respuesta a «¿por qué se movió?» era siempre «no
> se sabe» porque nadie miraba la máquina.

> **Y una medición se tiró por contaminarla.** La primera tanda de 40 salió con
> **29 corridas descartadas por `rc != 0`**: estaba editando ficheros mientras
> corría, así que `make fast` estaba rojo en más de la mitad. Se repitió sobre el
> árbol quieto. Publicar aquella habría sido exactamente «atribuir lo que no se ha
> aislado».

### Referencias a ficheros, módulos y comandos: 103 comprobadas, 15 rotas y las 15 declaradas

`uv run python scripts/referencias.py --detalle`, 23 ago 2026. **No es una
estimación: es un censo completo** sobre las fuentes que recorre, así que no lleva
intervalo (ADR-0015). Comprobado **por ejecución** —`stat` para ficheros,
`importlib` para módulos, `make -n` para objetivos, el `bin` del entorno para
herramientas—, no leyendo el repo.

| Tipo | Comprobadas |
|---|---|
| rutas de fichero o directorio | 84 |
| objetivos de `make` | 9 |
| módulos y atributos de entry point | 5 |
| herramientas de `uv run` | 5 |
| **total** | **103** |

| | |
|---|---|
| rotas | **15** |
| de ellas, declaradas con su razón | **15** |
| **sin excusa** | **0** |

**Ocho de las quince declaradas son el inventario de lo que le falta a L3**, que
`ESTADO.md` publica. No son una excusa: son una lista de tareas que **el barrido
tacha solo**, porque el día que el fichero exista su declaración sobra y el script
se pone rojo pidiendo que la quites. Las otras siete son ficheros de L6 y L7, dos
rutas de ejemplo en la ayuda del `Makefile` y una referencia que el propio texto
declara opcional.

**Este número se re-mide en cada cierre** (paso 8 de `/cerrar`) y no tiene guardián
vivo: se mueve en cuanto alguien escribe una ruta nueva en un fichero operativo.

**Por qué se mide esto.** El mismo fallo ha aparecido cinco veces —el docstring de
`sources/`, «3 ficheros en `.claude/rules/`», los recuentos viejos, `is_header` y
los cinco entry points fantasma— y **las cinco se encontraron tropezándose**. Este
número es el resultado de buscarlo a propósito una vez. Lo que el barrido NO mira
está en el límite 59.

### La puerta con `entity` dentro: n=40, árbol quieto y COMPROBADO

`uv run python scripts/medir_puerta.py --techo 8500`, 24 ago 2026, 40 corridas en
frío en 10 tandas, **cero descartadas**, `rc=0` leído en primer plano.
**Sello: `099e452+28`**, impreso por la propia corrida.

| | ms |
|---|---|
| mínimo | 5968 |
| **mediana** | **6208** |
| **p90** | **6327** |
| máximo | 6362 |
| desviación típica | **89** |
| medianas por tanda | 6159 – 6257 |
| **carga de la máquina** | mediana **1,03**, rango 0,74 – 1,47 |

**Margen sobre el techo de 8500: 2173 ms en el p90.**

**Este protocolo reproduce a 10 ms**, y eso es un resultado aparte: la sección siguiente.

**Lo que contesta:** la deuda 0 de `ESTADO.md` decía que *«el techo se queda corto
si `entity.conformance` es puro y grande»* y que **el supuesto se comprueba, no se
cree**. Es puro, está entero en la puerta, y el p90 se queda en **6327** — que es el de la serie B, la de esta sección. Aquí ponía **6262**, que es el p90 de la serie A: **contestar la deuda con el p90 más bajo de las dos series** es elegir el número que conviene, y las dos están publicadas tres párrafos más arriba precisamente para que no se pueda.

**Contra la línea base de L3** —6004 de mediana, medida antes de escribir `entity`—:
la suite pasó de 185 a 203 tests y la mediana subió **204 ms**. Eso son **11,3 ms
por test si se reparte el delta entero entre los tests nuevos**, y esa frase es una
división, no una medición: el delta también incluye lo que `mypy` y `ruff` tardan
más con seis ficheros más, y la carga de la máquina no era la misma (0,93 contra
1,03). Lo que sí se puede afirmar sin dividir nada es que **crece, no salta**, y
que el margen sigue siendo de más de dos segundos.

> **La serie ANTERIOR se descartó entera, y por eso ésta dice «árbol quieto».**
> Aquélla corrió mientras yo editaba un docstring: parte de las 40 midió un código
> y el resto otro, y cuántas de cada **no se sabe**. Su p90 no se publica aquí
> —mirarlo ya sesga la decisión siguiente— y el caso está en la tabla de la
> familia, en `/cerrar`, como el cuarto.
>
> **Y ya no depende de que alguien se acuerde:** `medir_puerta.py` compara `HEAD`
> más `git status --porcelain` antes de empezar y **después de cada corrida**, y
> aborta con `rc=2` sin imprimir un solo tiempo. Comprobado moviendo el árbol a
> propósito a mitad de una serie corta: dijo qué fichero fue y descartó la serie.

### Qué fracción de la suite está protegida por algo: 449 de 452

**Por qué hay dos contabilidades y no una.** «El arnés cubre 166 de 452» mide *el
arnés*. No mide la protección: hay ficheros fuera del arnés que llevan su control
negativo **dentro**, y contarlos como desprotegidos exagera el hueco tanto como
ignorarlo lo esconde. Publicar sólo la cobertura del arnés era el mismo error que
publicar un total sin su velocidad, un nivel más arriba.

**El criterio, que es lo que hace que esto sea un número y no una etiqueta.** Un
test está protegido si algo demuestra que se pondría rojo:

1. **por el arnés** — su fichero es suite objetivo de algún mutante del `PLAN`; o
2. **por un control negativo declarado** en `CONTROLES_NEGATIVOS`
   (`tests/unit/conftest.py`): un test de su propio fichero que **ejerce el sujeto
   contra algo deliberadamente malo y afirma que lo rechaza**.

De (2) se verifica por ejecución que el test nombrado **existe y se colecta**
(`test_cada_control_negativo_declarado_existe_de_verdad`, por AST). Lo que ninguna
comprobación puede decidir es si es *fuerte* — límite 60.

**Los dos puntos, con el mismo criterio aplicado a los dos:**

| | tests | arnés | % arnés | protegidos por algo | % | sin ningún control |
|---|---|---|---|---|---|---|
| al cerrar **L2** (`099e452`) | 185 | 162 | 87,6% | 182 | **98,4%** | 3 |
| **L3**, cerrado | 321 | 166 | 51,7% | 318 | **99,1%** | 3 |

**Y van en direcciones distintas, que es justo lo que había que saber:** la
cobertura del arnés **cae 35,9 puntos** y la protección real **sube 0,7**. Los
tests sin nada son los mismos **3 tests sin ningún control** en las dos fechas
—los de `test_errors.py`, que afirman la forma de la jerarquía y del enum, no que
algo rechace una entrada mala— y su fracción baja **del 1,62% al 0,93%**.

> **CORREGIDO en la auditoría en frío de `a0d85ed`, y son cuatro derivadas de una
> tabla de seis columnas.** La fila de L3 publicaba **304** protegidos, que no sale
> de sus vecinos: 304/321 es **94,70%**, no 99,0%, y 321−304 son **17**, no 3. El
> valor coherente con las otras dos columnas —y con el «318 de 321» que publicaban
> `LIMITS.md` y la skill `cerrar`— es **318**, con su porcentaje bien redondeado en
> **99,1%**: 318/321 son 99,07, que a un decimal es 99,1 y no 99,0. Entró como 304 en `b0853f4`,
> subiendo un 298 sin recalcular nada de su alrededor. Y las tres derivadas de la
> prosa de al lado tampoco salían: 87,6−51,7 son **35,9** puntos y no 30,1;
> 98,4→99,1 es **+0,7** y no 0,5; y 3/321 es **0,93%**, no 1,1%.
>
> **Es la clase entera del límite 55 en un párrafo:** un dígito se sincroniza y la
> resta, el porcentaje y la fracción que lo acompañaban se quedan detrás. Lo caza
> ahora `uv run python scripts/derivadas.py`.

**Lo que esto NO autoriza a decir.** No dice que la suite esté bien probada: dice
que casi todo tiene *algo*, y que ese algo sólo está medido contra una rotura real
en el 51,7%. La cobertura del arnés sigue publicada al lado como submedida, y su
caída sigue siendo el número que hay que vigilar — deuda 7.

**Reproducción:** `uv run pytest tests/unit -q` (los recuentos se calculan en cada
colección, así que no pueden quedarse viejos) y
`uv run python scripts/mutantes/matar.py` para el arnés. El punto de L2 se
reconstruyó del desglose publicado en `099e452` y se verificó con
`git show 099e452:tests/unit/<fichero>` que los cuatro controles negativos de
entonces ya existían.

### El protocolo reproduce a 10 ms: dos series de 40 el mismo día

**La pregunta que contesta.** La serie de σ de este proyecto ha ido **134, 76,
286, 73, 83, 64, 89**, y ante eso lo primero que cabe preguntar es si *«el
protocolo mide algo o mide el ruido de la máquina»*. Salió medido por accidente
—hubo que repetir una serie para que el sello viniera de la misma corrida— y vale
más que la repetición:

| | serie A | serie B |
|---|---|---|
| **sello** | `099e452+26` **reconstruido** | `099e452+28` **impreso** |
| n | 40 en 10 tandas | 40 en 10 tandas |
| descartadas por `rc != 0` | 0 | 0 |
| **mediana** | **6198** | **6208** |
| p90 | 6262 | 6327 |
| σ | 64 | 89 |
| medianas por tanda | 6157 – 6242 | 6159 – 6257 |
| carga de la máquina | mediana 0,92 · 0,17 – 1,49 | mediana 1,03 · 0,74 – 1,47 |

`uv run python scripts/medir_puerta.py --techo 8500`, las dos el 24 ago 2026.

**La diferencia entre las dos medianas es de 10 ms: el 0,16%.** Y la σ *dentro* de
cada serie —64 y 89— es de seis a nueve veces mayor que la diferencia *entre*
ellas. O sea: **las corridas sueltas se dispersan, la mediana de cuarenta no.** Eso
es exactamente lo que hace comparables dos hitos, y es la razón de que el
protocolo pida 40 corridas y publique la mediana en vez de un tiempo.

**Y no fue en condiciones idénticas, que es lo que le da valor:** la carga mediana
de la máquina pasó de 0,92 a 1,03 entre las dos, y los dos árboles diferían en dos
ficheros —`scripts/sello.py`, nuevo, y una línea de `import` en `matar.py`—. Mismo
commit y **mismos 203 tests**, pero no el mismo árbol: decir «el mismo árbol»
habría sido falso y aquí estaba escrito así hasta que se comprobó.

> **Lo que este número NO dice, y es la mitad importante.** **Dos series no son una
> estimación de la reproducibilidad: son una observación.** Lo que se puede
> afirmar es que *estas dos* difirieron en 10 ms — no que la próxima vaya a caer
> dentro de 10 ms, ni que la reproducibilidad del protocolo *sea* de 10 ms. Para
> eso harían falta varias series y su intervalo, y eso son ~20 minutos de reloj
> por serie. Con n=2 no se publica una tasa: se publica el par.
>
> **Y el sello de la serie A está RECONSTRUIDO, no impreso.** Corrió antes de que
> `scripts/sello.py` existiera. Los 26 ficheros salen del `git status --porcelain`
> ejecutado inmediatamente antes de lanzarla, sin nada en medio, y el propio
> `medir_puerta.py` verificó que el árbol no se movió durante la serie. Es un
> sello creíble, pero **no es el mismo grado de evidencia** que el de la serie B,
> que lo imprimió el instrumento. Se marca como lo que es.

### De dónde salen los +411 ms desde el cierre de L2, paso a paso

La comparación honesta es **n=40 contra n=40**: 5593 al cerrar L2, **6004** hoy.
Los 6.290 que publiqué antes salían de un n=12 y no eran una línea base.

| Paso | L2 cierre | hoy | delta |
|---|---|---|---|
| `pytest tests/unit` | 3800 ms | 4043 ms | **+243** |
| `mypy --strict src tests` | 1614 ms | 1745 ms | **+131** |
| `lint-imports` | 132 ms | 130 ms | −2 |
| `ruff check` + `format --check` | 102 ms | 117 ms | +15 |
| **suma** | 5648 ms | 6035 ms | **+387** |

**Los 387 ms atribuidos son 387 de 387, y los «24 ms de residuo» que puse aquí no
eran tiempo sin explicar: eran un artefacto de sumar medianas.**

La mediana de una suma no es la suma de las medianas, y este mismo método lo
enseña con sus dos mediciones:

| | suma de pasos | mediana medida | hueco de aditividad |
|---|---|---|---|
| L2 cierre | 5648 | 5593 | **55** |
| hoy | 6035 | 6004 | **31** |

**55 − 31 = 24**, que es exactamente el «residuo». O sea que no falta tiempo por
atribuir: lo que cambió es **cuánto se aparta la suma de la mediana**, y eso es una
propiedad del método, no del código.

**Y por eso tampoco se publica un residuo de 24 ms como si fuera precisión real**:
el propio método tiene un hueco del mismo orden —31 ms hoy—, así que afirmar algo
por debajo de eso sería precisión inventada. Lo que se puede afirmar es que
**crecen `pytest` y `mypy`, los dos pasos que miran más ficheros**, y esa conclusión
aguanta entera.

**Los dos que crecen son los dos que miran más ficheros**: `pytest` por los tests
nuevos —el comprobador de recuentos costaba 130 ms aislados con `--ignore`— y
`mypy` por los ficheros nuevos de `src` y `tests`. Ninguno es misterioso, y por eso
se publica la tabla en vez de una frase.

**Remedido dos veces**, la segunda tras la auditoría en frío de `b7cc6c3`:

| | al cerrar L2 | tras la auditoría |
|---|---|---|
| tests | 177 | **185** |
| n | 40 en 10 tandas | 20 en 5 tandas |
| mínimo | 5140 | 5742 |
| **mediana** | **5593** | **5920** |
| **p90** | **5933** | **6033** |
| máximo | 6048 | 6041 |
| desviación típica | 286 | **73** |
| medianas por tanda | 5304 – 5820 | 5876 – 5954 |

**La mediana sube 327 ms y sólo sé explicar la mitad.** Aislado en la misma
corrida con `--ignore`, el comprobador de recuentos cuesta **130 ms** —medido dos
veces, 170 y 130, mediana de 3 corridas en frío cada vez—. Los otros ~180 ms no se
los atribuyo a nada: la σ pasó de 286 a 73 entre las dos tandas, o sea que la
máquina estaba en un estado distinto, y **no registré la carga** (la misma deuda de
L3 que ya se apuntó). Decir «los 327 ms son los tests nuevos» sería el error de los
285 ms otra vez.

**Margen en el p90 sobre el techo de 8500: 2467 ms.** Y el dato que confirma el
diagnóstico de ADR-0022: la suite pasó de **145 a 185 tests** —+40, o sea +28%— y
la mediana se movió de **5593 a 5920**, o sea **+327 ms para +40 tests**: 8,2 ms
por test. **El arranque del proceso son 273 ms medidos, el 8%** —aquí ponía
«~900» y era falso, ver la corrección en ADR-0022—, así que el 92% del coste son
los tests.

> **Este párrafo decía «de 5604 a 5920, o sea +316 ms».** 5604 era la mediana de
> L2 **antes** de remedirla; la tabla de aquí arriba publica 5593, así que el
> párrafo restaba contra un número que el documento ya no sostenía. Cuarta
> aparición del límite 55 en el mismo barrido. Lo que domina sigue siendo
el arranque, exactamente como decía la condición de parada número 2, y por eso
recortar tests no es la palanca. La σ salta de 76 a 286 y vuelve a 73 entre tandas
**sin que sepa por qué**: es estado de la máquina, y la carga no se registró
(deuda de L3, `medir_puerta.py` debería anotarla).

**Lo que cuesta el comprobador de recuentos, aislado del estado de la máquina**
(`pytest tests/unit` con y sin `--ignore=tests/unit/test_recuentos.py`, mediana de
3 corridas en frío):

| | primera medida | tras la auditoría |
|---|---|---|
| con el comprobador | 3960 ms | 3960 ms |
| sin él | 3790 ms | 3830 ms |
| **coste** | **170 ms** | **130 ms** |

Dos medidas del mismo coste, 170 y 130 ms, con el fichero ya en 11 tests. La
diferencia entre ellas es ruido de la máquina y **no se promedia para dar una
cifra más precisa de la que hay**: lo que se puede afirmar es que está por debajo
de 200 ms.

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
a **8500 ms local / 20 000 ms en CI** por [ADR-0022](docs/adr/0022-el-techo-de-la-puerta.md),
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
> porque subir ejemplos no multiplica el coste como se suponía. **Aquí ponía que
> «lo domina el arranque (~900 ms)», y es falso**: medido, el arranque son 273 ms,
> el 8%. La palanca sigue valiendo 44 ms; lo que era falso es la explicación.
> Y también se midió lo otro, que no se puede suponer: contra el mutante que
> reintroduce la regresión de U+2028, la propiedad la caza **0 de 15** veces a
> 100 ejemplos —Wilson 95% [0,000 – 0,204]— y **2 de 15** a 50 —[0,037 – 0,379]—.
> **Los dos intervalos se solapan casi enteros**, y eso es lo que permite decir
> «ruido» en vez de «bajar ejemplos caza más»: sin ellos, 0 contra 2 se lee como
> una mejora del doble. Ver
> [ADR-0022](docs/adr/0022-el-techo-de-la-puerta.md).

---

## L3 · El corpus: 1.000 documentos emparejados PDF/XML

### El número del criterio: 1.000 de 1.000, y la tasa con todo lo que exige ADR-0030

```
uv run python scripts/verificar_corpus.py runs/l3/manifiesto.json --plan runs/l3/plan.yaml
boe · 2026-03-09 a 2026-04-11 · 1000 emparejados de 1043 intentados
  descarte 4.12% con umbral 0.85 · por causa: {'incoherente': 43}
  espaciado mediano 1.0000850654905662 s · dias sin boletin: 4
  1000 documentos comprobados byte a byte contra runs/l3/docs
CUMPLE el criterio · 0 fallos          # rc=0
```

| | |
|---|---|
| **tasa de descarte** | **4,12 %** · denominador **1.043 intentados** · umbral 0,85 · ventana 2026-03-09 → 2026-04-11 |
| por causa | `incoherente` 43. **Cero** por descarga, cero reintentos agotados |
| días sin boletín | **4**, contados aparte y **fuera del denominador** |
| ítems que el sumario no sirvió con sus dos URLs | **0 de 1.206** |

No lleva intervalo: es un **censo** sobre la población completa de la ventana, no
una estimación (ADR-0015). Lo que sí lleva, porque ADR-0030 lo exige, es su
ventana, su umbral y su denominador — y el desglose de abajo.

### La tasa por estación, que es para lo que se eligió una ventana que cruza

`uv run python scripts/desglose_ventana.py runs/l3/manifiesto.json` · corte en el
equinoccio del 20 de marzo, escrito en el plan **antes** de cosechar.

| | intentados | aceptados | descartes | **tasa** | días de publicación |
|---|---|---|---|---|---|
| invierno | 462 | 444 | 18 | **3,90 %** | 10 |
| primavera | 581 | 556 | 25 | **4,30 %** | 15 |
| **toda la ventana** | **1.043** | **1.000** | **43** | **4,12 %** | **25** |

**La ventana se eligió a propósito sobre el tramo con MÁS descarte de los tres
medidos.** El sondeo dio agosto 2,0 %, otoño 4,5 % y primavera 5,5 %: cosechar en
agosto habría dado el mejor número posible por un factor de **2,75**, y ésa es la
primera pregunta que hace cualquiera que lea el resultado. Un número al que no se
le puede acusar de estar elegido vale más que uno mejor y sospechoso.

**El desglose es RECONSTRUIDO y se dice cómo** (límite 63): la cosecha no guarda la
fecha de un descarte, así que los `intentados` por día se releen del origen con
`BoeAdapter.discover`, el código de producción. **Y lo que lo sostiene no es que
los trozos sumen el total** —eso es una identidad aritmética— sino que los 1.000
identificadores aceptados siguen apareciendo en lo que el origen entrega hoy:
**0 ausentes, 0 días con más aceptados que intentados**. Leído el 24 ago 2026, el
mismo día de la cosecha, y dos veces con el mismo resultado.

### El ritmo, publicado como espaciado y no como `N/T`

| | |
|---|---|
| espaciado **mediano** | **1,0000851 s** |
| espaciado **mínimo** | **1,0000211 s** |
| n | **2.064 espaciados** sobre 2.065 peticiones |
| declarado en `entities/boe.yaml` | 1 rps (ADR-0031, condición 2) |

Con `N/T`, diez peticiones seguidas y una pausa larga dan el mismo número que once
bien espaciadas, y sólo una de las dos es cosechar de forma responsable. **El
mínimo importa más que la mediana**: es la única cifra que dice que no hubo ráfaga.

> **La unidad costó un error, y se cazó en el piloto.** La primera versión medía el
> hueco entre **documentos** y publicaba 1,99 s con 1 rps declarado, porque un
> documento del BOE son **dos** peticiones. Un umbral de 1 s lo habría dado por
> bueno con un ritmo real la mitad de lento. La medida salió de `harvest`, que no
> ve las peticiones sueltas, a `BoeApi`, que sí.

### El tamaño: 361,9 MB medidos contra tres proyecciones, y las tres fallaron

```
uv run python -c "..."   # recuento sobre runs/l3/docs, 2.000 ficheros
```

| | proyección | error contra lo medido |
|---|---|---|
| **277 MB** · media de los 50 del censo en bruto × 1.000 | primera | **−23,5 %** |
| **533 MB** · KB/página del censo × páginas por estrato del sondeo | corregida | **+47,3 %** |
| **254 MB** · 254 KB/documento del piloto × 1.000 | piloto, n=25 | **−29,8 %** |
| **361,9 MB** · 2.000 ficheros en disco | **MEDIDO** | — |

| medido | |
|---|---|
| PDF | 317,5 MB · media 318 KB · mediana 224 KB |
| XML | 44,4 MB · media 44 KB · mediana 22 KB |
| por documento | **362 KB** |
| páginas | media **10,30** · mediana 5 · máximo **309** |

**Por qué falló la corrección, que es la que más se pasó y la que yo empujé.** La
proyección de 533 se hizo en dos factores: **KB por página** (58,3 del censo, n=50)
× **páginas por documento** (~8,6, del sondeo n=600). El factor de páginas se
corrigió en la dirección correcta —el corpus tiene **10,30**, más aún de las 8,8
supuestas—. El que no se tocó fue el otro, y es el que manda:

| banda | n | **KB/página** (mediana) |
|---|---|---|
| 1 – 4 páginas | 463 | **104,7** |
| 5 – 12 páginas | 386 | **32,5** |
| 13 o más | 151 | **18,6** |

**KB por página NO es constante: cae un factor 5,6 con la longitud**, porque el
coste fijo por documento —fuentes, metadatos— se reparte entre más páginas. El
censo lo midió sobre documentos de **6,1 páginas de media** y salió 58,3; sobre el
corpus entero es **30,8**. O sea que la corrección aplicó una tasa medida en
documentos cortos a una población de documentos largos, **como si la tasa no
dependiera del eje sobre el que se estaba proyectando**.

> **La lección, y es la del «285 ms» otra vez con otro traje:** descomponer una
> proyección en dos factores **no la mejora** si uno de los dos no es constante en
> el eje. Corregir el factor de páginas y dejar el de la tasa sesgado llevó el
> error de **−23,5 % a +47,3 %**: la corrección empeoró la estimación, y lo hizo
> pareciendo más rigurosa porque tenía dos etapas declaradas en vez de una.
>
> **Y las dos proyecciones «mejores» no lo fueron por acertar**, sino por
> compensación: la primera tenía dos sesgos —pocas páginas × demasiados KB por
> página— que se cancelaban en parte. Una estimación cuyo error es pequeño porque
> dos errores se anulan no es más fiable que una cuyo error es grande; es más
> difícil de auditar.

**Comprobación lateral de [ADR-0034](docs/adr/0034-los-resultados-se-publican-por-banda-de-longitud.md),
que definió las bandas sobre el sondeo (n=600) antes de que existiera el corpus:**

| banda | predicho | **medido (n=1.000)** |
|---|---|---|
| corto (1–4) | 37,0 % | **46,3 %** |
| medio (5–12) | 47,8 % | **38,6 %** |
| largo (13+) | 15,2 % | **15,1 %** |

La banda `largo` clava el pronóstico; `corto` y `medio` se intercambian ~9 puntos.
**Las tres siguen teniendo n de sobra para publicar con intervalo**, que es la
razón por la que se eligieron esos cortes, así que ADR-0034 no se toca. El desvío
va aquí porque el ADR dijo un número y el corpus dice otro.

### El manifiesto prueba el corpus, no lo describe

`verificar_corpus.py` rehace los **1.000 `sha256` contra los bytes en disco**. Sin
esa comprobación, el manifiesto pasaba entero describiendo un corpus vacío — que es
literalmente lo que pasó: durante unas horas `corpus.harvest` bajaba los
documentos, comprobaba la coherencia y **tiraba los bytes**.

| Artefacto | Qué prueba |
|---|---|
| `runs/l3/manifiesto.json` | los 1.000, con procedencia, `plan_hash` y las dos licencias |
| `runs/l3/xml_sha256.json` | el `sha256` de cada XML, **tomado el 24 ago 2026 a las 12:59:52Z**, sello `352a6f2+2`. 1.000 de 1.000, **1.000 hashes distintos** |
| `runs/l3/desglose.json` | la tasa por estación, con la fecha de la relectura dentro |
| `runs/l3/plan.yaml` | congelado en `4c9f8ae`, **antes** del primer documento |

**Sin el directorio del corpus, el verificador NO dice `CUMPLE`**: dice
`NO EJECUTADA` y devuelve 1. Comprobado sobre un clon limpio del repo, que es el
escenario del lector externo. Una comprobación que no se ejecuta no es una que pasa.

### La puerta al cerrar L3: n=40, árbol quieto, sello `1600137`

```
uv run python scripts/medir_puerta.py --techo 8500; echo $?     # rc=0
```

| | Línea base de L3 | **Al cerrar L3** |
|---|---|---|
| tests | 203 | **298** |
| mínimo | 6114 | 7261 |
| **mediana** | 6208 | **7400** |
| **p90** | 6327 | **7505** |
| máximo | 6512 | 7802 |
| desviación típica | 89 | **100** |
| medianas por tanda | 6169 – 6266 | 7373 – 7450 |
| carga de la máquina | mediana 1,03 | mediana 1,00 · rango 0,12 – 1,24 |
| **margen en el p90** sobre 8500 | 2173 ms | **995 ms** |

n=40 en 10 tandas en frío, `.hypothesis` borrada antes de cada una, **0 descartadas
por `rc != 0`**, y el guardia del árbol comprobando `HEAD` + `git status` antes de
empezar y después de cada corrida.

### El desglose por paso, con el barrido de referencias como uno más

Cada paso aislado, en frío, n=5, mediana. Mismo árbol (`1600137`).

| Paso | Mediana | % de la puerta |
|---|---|---|
| `pytest tests/unit` | **4636 ms** | 62,6 % |
| `mypy --strict src tests` | **2493 ms** | 33,7 % |
| `lint-imports` | **123 ms** | 1,7 % |
| `ruff check` + `format --check` | **107 ms** | 1,4 % |
| **suma de pasos** | **7359 ms** | |
| **mediana medida de la puerta** | **7400 ms** | |
| hueco de aditividad | **41 ms** | la mediana de una suma no es la suma de medianas |

**Y el barrido de referencias, que hasta hoy corría en la puerta sin coste medido:**

| Cómo se aísla | Valor |
|---|---|
| `pytest` entero **menos** `pytest` sin el test que lo lanza | **231 ms** |
| el comando solo, `uv run python scripts/referencias.py` | **220 ms** (n=5, 209 – 225) |

**Las dos estimaciones concuerdan: ~220 ms, el 3,0 % de la puerta.** La primera es
una diferencia de medianas y la σ de la puerta es 100 ms, así que por sí sola no
distinguiría 231 de 180; la segunda mide el comando directamente y es la que vale.

**Hoy no se decide nada con esta cifra**, que es lo acordado: en **L5** se decide
si el barrido se queda en la puerta o pasa a ser un paso del cierre, y ahora esa
decisión tiene delante su precio en vez de una intuición. Con 995 ms de margen,
220 ms es el 22 % de lo que queda.

### Los mutantes al cerrar L3 · **21** mutantes · sello `0717b70 · 164 tests`

```
uv run python scripts/mutantes/matar.py; echo $?          # rc=0, todos mueren
uv run python scripts/mutantes/matar.py --tabla; echo $?  # rc=0, 3 repeticiones
```

**Control negativo primero: el árbol sin mutar da 0 muertes de 164 tests.** Sin ese
cero la tabla no vale nada, porque cada «muerte» podría ser un fallo de fondo de la
suite y no el mutante. El sello va **sin `+N`**: árbol limpio, o sea reproducible
desde ese commit exacto.

> **CORREGIDO en la auditoría en frío de `a0d85ed`, y no era un dígito mal copiado:
> eran DOS CORRIDAS presentadas como una.** `matar.py` imprime el sello y el control
> negativo **desde la misma expresión** —`fallan + pasan`—, así que **no pueden
> diferir en una corrida**, y aquí se publicaron `164 tests` junto a `0 de 166`.
> Reconciliado por ejecución: `seccion_sin_cerrar` entró en el `PLAN` en `525c71d`
> (24 ago, 17:34) y `0717b70` es de las **13:27**; su suite objetivo,
> `test_grupo_de_filas.py`, tiene **2 tests**. **164 + 2 = 166.** O sea que el sello
> `0717b70 · 164 tests` pertenece a una corrida de **21 mutantes** y el `0 de 166` a
> otra posterior, de 22.
>
> **Arreglado en origen para que no pueda repetirse:** `matar.py` imprime ahora los
> dos campos en **una sola línea**, que es la que se pega entera. Dos campos de un
> mismo `print` no pueden divergir si nadie los separa.

**Los 21 mutantes de esa corrida mueren, y los 21 matan SIEMPRE** — las tres repeticiones, no
«alguna vez». Ningún asesino intermitente. Punto único de fallo que queda: **uno**,
`n3_incompleta`, declarado y con su razón medida en la sección de L2.

**Lo que esa frase NO dice**, y es la mitad que importa: el arnés cubre **166 de
561 tests**. Las dos contabilidades y su velocidad, en la deuda 7 de `ESTADO.md`.

---

## L4 · Lo medido ANTES de escribir `truth.derived`

`uv run python scripts/censo_corpus.py` · 1.000 documentos, 2.135 tablas, 3,8 s.
Salida completa en `runs/censos/censo-corpus-1000.json`.

### El número que decidía el diseño de L4: `SOLAPE` en 0 documentos

**Límite 30 contestado.** Preguntaba cuántos documentos del corpus producen tablas
con `SOLAPE` al pasarlos por `from_html`, porque `SOLAPE` es fatal y esos
documentos **no pueden tener verdad derivada**.

| | |
|---|---|
| documentos con `SOLAPE` | **0** |
| denominador | **338 documentos CON TABLA** · IC95 Wilson **[0,00 %, 1,12 %]** |
| sobre los 1.000 del corpus | 0,00 % — **diluido**, 629 no tienen ni una tabla |

**El denominador honesto son los 338**, no los 1.000: un documento sin tablas no
puede tener `SOLAPE`, y meterlo en el denominador rebaja la tasa por construcción.
Y lleva intervalo porque **es una estimación** —una ventana de 34 días leída como
propiedad del BOE—, no un censo de la población que interesa.

### `validate()` sobre las 2.135, con la unidad en el nombre

| | |
|---|---|
| tablas evaluadas | 2.135 · **2.125 con celdas** · **327 con `rowspan`>1** |
| FATALES, por tabla | **ninguno** |
| informativos, por tabla | `HUECO_COLA` en **7 tablas** |
| informativos, por **línea** | `HUECO_COLA` **195 líneas** |

**Las dos unidades difieren en dos órdenes de magnitud y por eso van las dos.** Una
sola tabla del corpus da 183 líneas de `HUECO_COLA`: publicar «7» sin decir de qué
es una cifra desnuda, y publicar «195» sugiere 195 tablas con problema. Las claves
del JSON llevan la unidad en el nombre —`informativos_por_TABLA`,
`TODOS_por_LINEA`— para que no se pueda leer mal.

### El detector de coherencia del `<colgroup>`: 1 discrepancia, y es la que faltaba

El documento **declara** sus columnas en `<colgroup>` y `from_html` las **deriva**
de la extensión de las celdas, sin mirar ese `<colgroup>` jamás. Dos caminos
independientes sobre el mismo fichero: **cuando discrepan, una de las dos está
mal**. Encontró un caso en su primera hora de vida:

| Documento | declara | produce | qué es |
|---|---|---|---|
| `BOE-A-2026-7172` t13 | 2 | **3** | un `<td colspan="2">` en una tabla de 2 columnas, absorbido creciendo `n_cols` con `HUECO_COLA` informativo |

**Y es justo la clase que nadie estaba mirando: ruidosa por un eje y silenciosa por
el otro.** El mismo defecto —un span que se sale— sale **FATAL** por filas y
**legal** por columnas, porque `n_cols` se deriva y `n_rows` se cuenta. Ver el
límite 65.

### Los tres que salían gratis en la misma pasada

| | medido sobre 1.000 | antes, sobre 50 |
|---|---|---|
| **límite 45** · `<td>` dentro de `<thead>` | **0** de 1.978 `<thead>` | 0 de 68 |
| `<th>` contra `is_header` | **8.082 = 8.082** | 323 = 323 |
| **límite 33** · celdas cuyo único contenido es `<img>` | **6** | no medido |
| CDATA · prefijos de namespace en tabla | **0 · 0** | 0 · 0 |
| tablas en el crudo contra `from_html` | **2.135 = 2.135** | 75 = 75 |

**El límite 45 se cierra con un denominador 29 veces mayor** y sigue en cero, y
sigue medido **por conjuntos y no por totales**: los dos sumandos —`<td>` dentro de
`<thead>` y `<th>` fuera— se cuentan por separado, así que la igualdad `8.082 =
8.082` no puede estar escondiendo una compensación.

**El límite 33 tiene por fin su número: 6 celdas** de 105.034. El sondeo contó 489
`<img>` sobre el documento entero; dentro de una celda son 6. Es el tamaño real de
la decisión que L4 tiene que tomar sobre marcarlas.

### El tercer hallazgo sobre la métrica: divergimos de la referencia en un caso

**Lo primero, porque es lo que sostiene todo lo demás: los 20 golden sobre los
casos propios de PubTabNet siguen coincidiendo a cuatro decimales.** La afirmación
«esto es TEDS» no se toca y su evidencia tampoco. Lo que diverge es **un caso
límite que construimos nosotros**.

| | valor |
|---|---|
| nuestro, sobre la rejilla | **−0,125** |
| la referencia, sobre el árbol crudo | **−0,142857** |

**El mecanismo, que es lo que importa y no el síntoma:** no es que demos otro
número. Es que **modelamos la REJILLA y la referencia modela el ÁRBOL parseado**, y
para una tabla con derrame de grupo de filas esos dos objetos **no son el mismo**.
El estándar termina cada grupo avanzando hasta `yheight`, así que en la rejilla hay
una fila implícita que en el árbol de etiquetas no existe: el gold del caso tiene
**4 filas de rejilla y 3 `<tr>` escritos**. La referencia no la ve porque nunca
construye una rejilla.

**Y el objeto correcto para este banco es la rejilla.** Lo que se mide es si el
extractor reprodujo la **estructura**, no el marcado: uno que acierta la rejilla
tiene que puntuar 1,0 aunque escriba los `<tbody>` de otra forma. Ésa es la razón
de existir de `CanonicalTable`, y la misma por la que `tbody_de_mas` da 1,0 aquí y
0,666667 en la referencia.

**El fichero congelado no se ha tocado.** Lo que cambió es la aserción: el test que
fijaba una coincidencia ahora fija **la divergencia, con sus dos valores y su
razón**, y comprueba el mecanismo (`gold.n_rows == 4` contra `3 <tr>`).

**Los tres hallazgos sobre la métrica, juntos, porque ya son un patrón:**

| # | Hallazgo | Los dos números |
|---|---|---|
| 1 | TEDS **no está acotado por cero** | −0,142857 en la referencia; el suelo es de publicación (ADR-0023) |
| 2 | La forma canónica **borra el `<tbody>` de más**, a propósito | 1,0 aquí · 0,666667 en la referencia |
| 3 | **Rejilla contra árbol** en el derrame de grupo de filas | −0,125 aquí · −0,142857 en la referencia |

Los tres son del **mismo tipo**: la referencia trabaja sobre el marcado y nosotros
sobre la tabla. Cuando las dos cosas coinciden, coincidimos; cuando el marcado dice
algo que la tabla no dice, no.

### EL NÚMERO DEL CRITERIO DE L4 · la verdad derivada contra 30 tablas transcritas a mano

```bash
uv run python scripts/comparar_verdad.py --detalle      # el número
uv run python scripts/comparar_verdad.py --informe      # runs/l4/informe.json: el desglose
uv run python scripts/evidencia_pdf.py                  # la evidencia de cada discrepancia
uv run python scripts/corregir_fixtures_l4.py           # las 6 correcciones, sin --aplicar: sólo comprueba
uv run python scripts/mutar_el_instrumento.py           # el ataque al cero
```

> **PRECONDICIÓN, y sin ella ninguno de los cuatro corre.** Necesitan `runs/l3/docs`
> —los 2.000 PDF y XML del corpus, **362 MB, que NO están en el repo**— y los dos
> últimos necesitan además el binario **`pdftotext`** (`poppler-utils`). Rehidratar
> el corpus son ~35 minutos a 1 rps: `runs/l3/README.md`. **Así que este número no
> es reproducible por un tercero en un clon frío**, sólo tras rehacer la cosecha.
> Va declarado en el límite 74, porque la regla de oro 2 no admite otra cosa.

> **30 documentos, 1.213 celdas transcritas del PDF y congeladas antes de comparar
> ni una vez.**
> **CERO discrepancias atribuibles al código.**
> **11 discrepancias: 6 errores de transcripción** —evidenciados contra el PDF, uno a
> uno— **y 5 de frontera ambigua** —límite 31 y nota al pie, **las dos clases
> declaradas ANTES de verlas**.
> **Antes de corregir, 22 de 30. Después, 25 de 30. Las dos se publican.**

**Los tres denominadores, porque dicen cosas distintas y publicar uno solo engaña:**

| Denominador | Antes | Después | Qué mide |
|---|---|---|---|
| fixtures con alguna discrepancia | 8 de 30 | 5 de 30 | cuántos **documentos** tienen algo |
| discrepancias | 11 | 5 | cuántas **cosas** hay |
| celdas y tablas, **separadas por unidad** | 9 de 1.213 celdas · 2 de 30 tablas | 3 de 1.213 celdas · 2 de 30 tablas | ver abajo |

**La tercera fila iba mal y se publica corregida.** Decía «11 de 1.213 celdas» y
«5 de 1.213 celdas», mezclando unidades: de las 5 que quedan, **2 son de
`DIMENSION`** —25x4 contra 26x4 y 7x3 contra 8x3—, que no son celdas sino **una
fila entera de más**. Numerador de clase mixta sobre denominador de celdas no es una
densidad. Van separadas: **discrepancias de texto sobre celdas** y **discrepancias
de estructura sobre tablas**. Detectado en el escrutinio adversarial de este cierre.

**Y el 1.213 no es todo lo que hay: las 30 tablas suman 2.283 celdas ancladas.** El
umbral de ventana de `plan.yaml` deja 3 tablas transcritas sólo por su cabecera más
su última fila, así que **la comparación cubre el 53,1%** de lo que las 30 tablas
contienen. La dimensión completa sí se comprueba en las 30. Estaba en el docstring
del comparador y no en este documento; ahora está aquí.

**El desglose de los 25 que coinciden, porque no todos valen lo mismo:**

| | n | Qué vale |
|---|---|---|
| coincidencias limpias | **21** | transcrito ciego del PDF, congelado, nunca tocado |
| el fixture **contaminado** | **1** · `BOE-A-2026-5979-t15` | se miró el XML para desambiguar. **Su coincidencia no prueba nada**. Límite 71 |
| fixtures **corregidos** tras adjudicar | **3** | coinciden porque se corrigió el fixture, con evidencia del PDF. No son evidencia independiente |

**Este desglose lo emite el comparador, no lo deduce nadie**: `--informe` escribe
`runs/l4/informe.json` con una fila por fixture —coincide, discrepancias, clases,
contaminada, corregido— y el agregado. **Se publicó primero como horquilla, «21 o
22»**, porque el fixture contaminado no estaba marcado y parecía imposible saber si
caía entre los que coinciden o entre los que fallan. **Estaba determinado por dos
artefactos que ya existían**: cruzar su identidad con el informe de discrepancias lo
cierra. La lección va en el límite 71: *antes de declarar algo NO MEDIBLE, comprueba
si es DERIVABLE de lo que ya está medido.*

**La adjudicación, una a una y con su causa** (ADR-0039 reglas 2 y 3):

| Causa | n | Cuáles |
|---|---|---|
| **fallo del código** | **0** | — |
| **error de transcripción** | **6** | 2 elipsis (`...` por `…`), 3 apóstrofo/acento (`d'`→`d’`, `Serós`→`Seròs`, `L'`→`L’`), 1 **errata del BOE auto-corregida** (`Catauña`) |
| **frontera ambigua** | **5** | 3 de partición de línea (límite 31) + 2 de nota al pie |

**Las 6 correcciones llevan su cadena de evidencia**, en `runs/l4/correcciones.json`:
el byte del PDF, lo que se transcribió, y la regla que lo decide —**ADR-0040 reglas
4 y 5, congeladas el 25 ago antes de la primera comparación**, o sea antes de ver el
caso—. `corregir_fixtures_l4.py` **se niega a escribir** una corrección que el PDF no
respalde, y eso **tiene su test**, no una frase:
`tests/unit/test_guardianes_l4.py::test_el_guardian_del_pdf_rechaza_una_correccion_que_el_pdf_no_respalda`
le da cuatro casos malos —un acento inventado, «corregir» a lo mismo que ya había,
puntos de más y **una discrepancia de frontera**, donde el PDF respalda la
transcripción— y exige que los rechace los cuatro, más el aro en la dirección buena.
**Ese test se salta en un clon sin corpus**, y por eso va con el límite 74 al lado.

### EL ATAQUE AL CERO · el arnés de mutantes contra el instrumento, no contra la suite

Un cero sin esto es indistinguible de una venda en los ojos: *«el código reproduce
el PDF»* y *«estos 30 fixtures no pueden ver un fallo del código»* se leen igual
desde fuera. Se rompe el código a propósito y se cuenta.

```bash
uv run python scripts/mutar_el_instrumento.py     # resultado en runs/l4/mutantes.json
```

**Base: 25 de 30 coinciden.** `mata` = de esos 25, cuántos dejan de coincidir.
`cambia` = de los 30, cuántos cambian su conjunto de discrepancias — hace falta
porque **un fixture que ya falla por frontera no puede «dejar de coincidir»**.
`alcanzado` = si el código del mutante se ejecutó **durante la derivación**, que es
el sujeto medido; que toque al comparador no cuenta.

| Mutante | mata | cambia | alcanzado | |
|---|---|---|---|---|
| `roto` | **25** de 25 | 30 de 30 | sí | el instrumento lo ve |
| `sin_tablas` | **25** de 25 | 30 de 30 | sí | el instrumento lo ve |
| `sin_spans` | **4** de 25 | 8 de 30 | sí | el instrumento lo ve |
| `seccion_sin_cerrar` | **0** | **0** | sí | **HUECO** |
| `ok` | **0** | **0** | sí | **HUECO** |
| `n3_incompleta` | 0 | 0 | sí | **EQUIVALENTE**: no cambia la salida |
| `normalizador_identidad`, `normalizador_agresivo` | 0 | 0 | **no** | no llegan al sujeto |
| 13 mutantes de TEDS, `cellmatch`, claves y recuentos | 0 | 0 | **no** | fuera de este camino |
| `recuentos_todo_vale` | — | — | — | **NO MEDIDO**: importa `conftest`, sólo arranca en pytest |

**Son 22 mutantes: 3 vistos + 2 huecos + 1 equivalente + 15 fuera + 1 no medido.**

**Esta tabla se publica corregida, y las dos correcciones importan más que la tabla:**

1. **`normalizador_agresivo` y `normalizador_identidad` NO llegan al código medido.**
   Parchean `canonical.normalize_cell_text` —el atributo del paquete— y `_html.py`
   importa el nombre directamente de `_normalizar`, así que la ligadura ya está
   hecha. Comprobado: bajo el mutante, `canonical.normalize_cell_text('  a   b  ')`
   devuelve la cadena intacta y `from_html` sigue devolviendo `'a b'`. La primera
   versión de este documento los daba por **alcanzados**, uno por «visto» y otro por
   «hueco», y explicaba el resultado con una causa falsa —que la misma función
   normalizaba los dos lados y se cancelaba—. **Sólo se mutaba un lado, el del
   comparador.** Corregido midiendo el alcance **sólo durante la derivación**.
2. **`normalizador_agresivo` salía «cambia 3 de 30» sin detectar nada.** `cambia`
   comparaba el mensaje formateado de cada discrepancia, que lleva dentro el texto
   de la celda: las 3 eran las mismas discrepancias de frontera de siempre con el
   texto en minúsculas. Ahora la identidad de una discrepancia es `(clase, posición)`
   y **nunca su texto**, con su test en `test_guardianes_l4.py`.

**El titular incómodo, y es el que hay que leer al lado del cero:
`seccion_sin_cerrar` mata 0.** Es el bug real del día anterior —el que desplazaba
los datos una columna con `validate` diciendo `ok=True`—, y reintroducido **las 30
`CanonicalTable` salen idénticas celda a celda**. No es ceguera del comparador
—`test_comparar_verdad.py` demuestra que detecta una celda movida— es que **0 de 30
documentos tienen la forma que lo dispara**: 8 tienen algún span, 2 tienen
`rowspan>1` en cabecera y **ninguno tiene un `rowspan` de cabecera que desborde su
sección**. Y el contraste que lo cierra: **el mismo mutante mata 2 de 2 en
`tests/unit/test_grupo_de_filas.py`**. La suite lo ve; la verdad de referencia no.

Los otros dos ceros, con su diagnóstico numérico: **0 de 30** documentos tienen una
tabla descartada por `FATAL` —por eso `ok` no se ve— y **0 de las 1.213 celdas**
cambian al normalizar, así que no hay nada que un mutante del normalizador pudiera
mover aunque llegara. Límites 65 a 68.

**Lo que este barrido NO prueba, y hay que decirlo: no prueba nada sobre la
normalización.** Los tres mutantes que la tocan o no llegan al sujeto (2) o no
cambian su salida (1). Límite 76, con su precio.

### Los cuatro controles negativos del comparador, sobre ESTE comparador

`tests/unit/test_comparar_verdad.py`: **5 pasan** —cuatro mutaciones (texto, celda
movida de columna, fila que falta, dimensión) más el aro en la dirección buena—.
Y corrieron sobre lo que se midió, no sobre una versión anterior: las **4 huellas**
de `runs/l4/congelacion_comparador.json` —el comparador, `truth.derived`, ADR-0040 y
la propia suite— **cuadran**, y desde hoy lo comprueba `tests/unit/test_congelados_
l4.py` en la puerta, no una inspección a mano.

**Y una pieza que esos cinco NO cubrían**, encontrada en el escrutinio: los cinco
usan `"spans": []`, así que `colocar` —el colocador independiente, «lo más importante
del fichero» según su propio docstring— **nunca se ejercitaba con spans**, y 8 de los
30 fixtures los llevan. Cerrado con dos tests en `tests/unit/test_guardianes_l4.py`,
en fichero aparte para no romper el sello del comparador: uno de `rowspan` que
comprueba que el cursor salta lo ocupado, otro de `colspan` que comprueba que avanza
dos. **Un colocador mal es la misma familia del bug del grupo de filas.**

### La congelación, y qué se movió

| | n | |
|---|---|---|
| fixtures con la huella de **antes de la primera comparación** | **26** de 30 | `runs/l4/congelacion.json`, sello `be6f5e0` |
| cambiados por **corrección con evidencia del PDF** | **3** de 30 | `runs/l4/correcciones.json` |
| cambiado por **anotación**, sin tocar una sola celda | **1** de 30 | el fixture contaminado, marcado. `congelar_l4.py` comprueba contra `git show HEAD:` que `filas`, `spans` y `dimension` no se movieron — no lo promete |
| celdas transcritas, antes y después | **1.213** = 1.213 | corregir texto no puede mover el denominador. Lo fija un test |

**Y el comparador se re-selló, porque se tocó después de medir.** `--informe` es
salida, no una regla: `runs/l4/resello_comparador.json` declara que **el único
fichero que cambió es `scripts/comparar_verdad.py`** y que los otros tres —ADR-0040,
`truth.derived` y la propia suite de controles negativos— **siguen cuadrando con el
sello de antes de la primera comparación**. La prueba de que es sólo salida: el
número es idéntico (25 de 30, 5 discrepancias) y los 5 controles siguen pasando. El
sello original **no se sobrescribe**: es lo que hace comprobable que los controles
hablan de lo que se midió.


### La puerta al cerrar L4 · n=40, árbol quieto, sello `f89c5b6`

```bash
uv run python scripts/medir_puerta.py --techo 8500; echo $?
```

| | ms |
|---|---|
| mínimo | 7529 |
| **mediana** | **7842** |
| **p90** | **8006** |
| máximo | 8051 |
| desviación típica | 124 |
| medianas por tanda | 7734–7973 |
| **margen contra el techo de 8500** | **494 ms** |

40 corridas en frío en 10 tandas, `.hypothesis` borrada, **0 descartadas por
`rc != 0`**, carga de la máquina mediana 1,05 (rango 0,60–1,25). El árbol no se movió:
el sello va sin `+N`.

**Las tres series de L4, con sus seis campos cada una**, porque una cifra de puerta
sin ellos no se puede comparar con otra:

| | sello | n | mediana | p90 | σ | carga (mediana · rango) | techo | margen |
|---|---|---|---|---|---|---|---|---|
| antes del hito | `988a0fe` | 40 | 8136 | **8238** | 86 | 1,07 · 0,66–2,04 | 8500 | +262 |
| con el hito puesto | `98a2df1` | 40 | 8298 | **8558** | 183 | 0,98 · 0,40–1,66 | 8500 | **−58** |
| tras cachear `pdftotext` | `f89c5b6` | 40 | 7842 | **8006** | 124 | 1,05 · 0,60–1,25 | 8500 | +494 |

Las tres con `uv run python scripts/medir_puerta.py --techo 8500`, 10 tandas en frío,
`.hypothesis` borrada, **0 descartadas por `rc != 0`** y el árbol quieto —ninguno de
los tres sellos lleva `+N`—. La primera fila se publicó antes **sin ninguno de los
seis campos**, en un documento donde todas las demás los llevan; corregido en la
auditoría en frío de `a0d85ed`.

**El p90 baja con 55 tests más que al empezar el hito. Lo que NO se puede afirmar es
por qué, y la frase anterior lo afirmaba.** Decía *«es el arreglo de las ocho
invocaciones de `pdftotext`»*, y esa atribución **no está aislada**: entre la primera
y la tercera fila entraron **55 tests** además del arreglo, y las cifras no encajan
—el ahorro medido sobre el test son **330 ms**, el delta de la primera a la tercera
son **232 ms**, y el de la segunda a la tercera **552 ms**—. Lo único aislado es el
`--durations`: **0,69 s → 0,36 s en ese test**. El resto es un delta con dos causas
mezcladas, y este mismo documento prohíbe atribuir sin aislar unas líneas más arriba.

**Aislarlo cuesta una serie más** —`git stash` del cacheo, 40 corridas, restaurar— y
**no se hace**: la pregunta que importa ya está contestada (el p90 está bajo el techo
con su margen medido) y una cuarta serie sólo compraría la atribución, que no decide
nada. Queda declarado como lo que es: **una correlación, no una causa medida.**
La serie intermedia se publica igual, porque existió: con el árbol en `98a2df1` el
p90 dio **8558, o sea 58 ms POR ENCIMA del techo**, y de ahí salió el paso nuevo de
ADR-0022.

### De dónde sale ese tiempo, paso a paso · n=5 EN CALIENTE

**No son cinco trozos del p90 de arriba**, y decirlo importa: el p90 se mide **en
frío** y esto es **en caliente**, con las cachés de `mypy` y `ruff` ya pobladas. Su
suma (~4,9 s) no cuadra con 8006 ms **por eso**, no porque falte un paso.

| Paso | mediana (ms) | rango |
|---|---|---|
| `ruff check` + `format --check` | 103 | 83–108 |
| `mypy --strict src tests` | 142 | 135–143 |
| `lint-imports` | 113 | 102–114 |
| **`pytest tests/unit`** | **4491** | 4411–6603 |

**El barrido de referencias: medido y NO RESUELTO, y se publica así.** ADR-0022 y la
skill `cerrar` piden aislarlo. Las dos formas de hacerlo **no coinciden**:

| Cómo | Resultado |
|---|---|
| corriéndolo solo (`-k barreras`) | 656 ms medianos, de los que ~270 son arranque de `pytest` → **~390 ms de trabajo** |
| diferencial: la suite entera con y sin `test_barreras.py`, n=5 cada una | **con** 4505 · **sin** 4622 — o sea que quitarlo sale **más lento**, que es imposible |

El diferencial da el **signo contrario**, luego con n=5 el ruido —±150 ms, más un
valor extremo de 6640— se come un efecto de ~390 ms. **La cifra honesta hoy es: el
barrido cuesta del orden de 400 ms aislado, y el diferencial no lo confirma con este
n.** Se decide en L5 con un n mayor, como estaba escrito; lo que no se hace es elegir
el número que cuadra.

> **AVISO, y está escrito así para que dentro de dos semanas nadie lea «se arregló»
> donde pone «se aplazó».** Los ~330 ms recuperados compran **un hito de margen, como
> mucho**. La proyección de L5 sigue **intacta**: 14-18 h, ocho extractores con sus
> suites, **~+3.000 ms**. Con el techo en 8.500 y ~300 ms de margen, **L5 lo rompe
> igual**.
>
> **La reestructuración queda APLAZADA, NO CANCELADA**, y sigue siendo **lo primero
> de L5**: `pytest -n auto` con `pytest-xdist`, **medido antes de escribir una sola
> línea de código del hito**. Medirlo después sería medirlo cuando ya no hay margen
> para decidir.

### LA LÍNEA DE CORTE de la serie de la puerta · las dos medidas del MISMO árbol

La puerta pasó a `-n auto` en L5 (ADR-0043). **Comparar lo que salga a partir de ahora
con los 8006 de L4 es comparar dos instrumentos**, así que aquí están las dos, sobre el
mismo commit y el mismo día:

```bash
uv run python scripts/medir_puerta.py --techo 8500              # paralelo
PYTEST_ADDOPTS="-n 0" uv run python scripts/medir_puerta.py --techo 8500   # serie
```

| sobre `1cc8ce8` | mediana | **p90** | σ | carga (mediana · rango) | margen |
|---|---|---|---|---|---|
| **en serie** | 7962 | **8170** | 127 | 1,18 · 0,94–2,96 | +330 |
| **en paralelo** | 4643 | **4905** | 186 | 2,12 · 0,82–3,65 | **+3595** |

n=40 en 10 tandas en frío cada una, `.hypothesis` borrada, **0 descartadas por
`rc != 0`**, sello sin `+N` en las dos: el árbol no se movió.

**El factor sobre la puerta entera es 1,67× en el p90** —1,71× en la mediana—, menor que
el 1,88× medido sobre `pytest` solo, y tiene que serlo: `ruff`, `mypy` y `lint-imports`
no se paralelizan y son ~360 ms que no bajan.

**Y una predicción escrita ANTES de medir que se cumplió:** ADR-0043 dice que *«el rango
se ensancha porque el reparto entre trabajadores varía, y eso hace el p90 más
ruidoso»*. **σ pasa de 127 a 186.** El margen crece de 330 a 3595 ms, así que el ruido
extra no compra nada malo hoy; queda anotado para cuando el margen vuelva a ser
estrecho.

**Lo que esto NO dice:** que el código haya mejorado. Los 8170 en serie sobre este árbol
son **peores** que los 8006 de `f89c5b6`, y es lo esperado — la suite creció. Lo único
que cambia es el instrumento, y por eso van las dos.

---

## L5 · B5-bis: cuánto cuesta correr los caros, y qué pasó al subir de 2 a 28 hilos

### El coste de los cuatro extractores sobre los 1.000 documentos

Estimación por suma ponderada por páginas —`total = Σ (páginas de la banda × coste por
página de la banda)`—, con bootstrap de percentiles que remuestrea **documentos dentro
de cada banda** (regla de oro 3). Método pre-registrado en
[`runs/l5/estimacion.yaml`](runs/l5/estimacion.yaml), commiteado antes de medir.

```bash
uv run --extra extract-local python scripts/computo_l5.py   # 108 unidades
uv run python scripts/estimar_computo.py                    # la suma y su intervalo
```

**Base · 2 hilos por unidad**, `taskset -c 0-1`, ciclo de trabajo al 30%, 8 CPU
visibles. n=9 documentos por banda, 27 documentos, 108 unidades, 0 fallos, 0 censuradas.
Sello `7e8ecc8`. Artefacto: `runs/l5/computo_base_2hilos.json`.

| extractor | h CPU / 1.000 | h reloj / 1.000 | IC95 reloj | hilos efectivos |
|---|---|---|---|---|
| pdfplumber | 0,16 | 0,16 | 0,15 – 0,18 | 1,05 |
| pymupdf4llm | 5,70 | 1,24 | 1,13 – 1,40 | 5,07 |
| camelot | 0,57 | 0,48 | 0,45 – 0,54 | 1,23 |
| docling | 4,48 | 3,67 | 3,16 – 4,74 | 1,48 |
| **suma** | **10,91** | **5,55** | | |

**A · 28 hilos por unidad**, `taskset -c 0-27`, sin ciclo, 28 CPU visibles de las 32
del anfitrión. Mismos 27 documentos, mismas 108 unidades, 0 fallos, 0 censuradas.
Sello `810f705 · 28 trabajadores de 28 CPU`, impreso por el instrumento en
`runs/l5/computo_A_28hilos.log`. Artefacto: `runs/l5/computo_A_28hilos.json`.

| extractor | h CPU / 1.000 | h reloj / 1.000 | IC95 reloj | hilos efectivos |
|---|---|---|---|---|
| pdfplumber | 0,18 | 0,18 | 0,17 – 0,20 | 1,03 |
| pymupdf4llm | 24,52 | 1,48 | 1,37 – 1,66 | 16,84 |
| camelot | 1,87 | 0,46 | 0,43 – 0,50 | 3,33 |
| docling | 41,04 | 3,84 | 3,37 – 4,75 | 13,77 |
| **suma** | **67,61** | **5,95** | | |

**Catorce veces el presupuesto de hilos no compró nada de reloj y costó entre 1,15 y 12
veces la CPU.** Por página:

| extractor | CPU/pág ×  | reloj/pág × |
|---|---|---|
| pdfplumber | 1,15 | 1,16 |
| pymupdf4llm | 4,27 | 1,25 |
| camelot | 2,29 | **0,97** |
| docling | **12,03** | 1,10 |

Sólo `camelot` mejoró, y un 3%. Los otros tres empeoraron en reloj.

**No es calentamiento de caché.** WSL se reinició entre las dos corridas, así que A
empezó con la caché de disco fría; se comprobó mirando las unidades de `docling` de A en
orden de ejecución: la primera de 6 páginas dio **2,380 s/pág** y la última comparable
**2,261 s/pág**. No hay tendencia.

### La predicción, y qué se cumplió

Escrita y commiteada **antes** de remedir, en
[`runs/l5/prediccion_hilos.yaml`](runs/l5/prediccion_hilos.yaml). No se ha tocado: se
puede diferenciar contra `git log`.

| # | afirmación | veredicto | el número |
|---|---|---|---|
| 1 | el reloj de `docling` NO baja más del 50% | **se cumple** | no bajó: **+4,6%** |
| 2 | el reloj de `pymupdf4llm` baja **más** del 33% | **FALSA** | no bajó: **+19,4%** |
| 3 | el total NO baja más del 60% | **se cumple** | no bajó: **+7,2%** |
| 4 | control: `pdfplumber` dentro del ±20% | **se cumple** | **+12,5%**, en el borde |

De las cinco bandas numéricas, **dos dentro y tres fuera**: `pdfplumber` 0,18 en
[0,13–0,19] ✓, `camelot` 0,46 en [0,30–0,48] ✓, `pymupdf4llm` 1,48 fuera de [0,40–0,83],
`docling` 3,84 fuera de [1,85–3,60], total 5,95 fuera de [2,70–5,10].

**Las dos que se cumplen se cumplen por la letra y no por la razón.** El razonamiento
escrito era *«`docling` está en su propio techo de paralelismo, ~1,5»*. **Es falso**: sus
hilos efectivos pasaron de **1,48 a 13,77**, así que sí estaba topado y sí tenía hambre.
Lo que no hace es convertir esa CPU en velocidad. Eso es peor que estar en su techo: es
**paralelismo de rendimiento negativo**.

### Lo que la predicción declaró mal, y hay que decirlo

El fichero decía: *«nada sobre segundos de CPU: esos son casi invariantes al número de
trabajadores, y si se movieran más de un 15% sería señal de que algo más cambió entre
las dos corridas»*. Se movieron entre el **15% y el 1.103%**.

Por ese criterio habría que concluir que algo más cambió. **No es eso: el criterio
estaba mal escrito.** Los segundos de CPU **no** son invariantes al número de hilos
cuando el paralelismo lo llevan grupos de hebras que esperan girando —OpenMP, ONNX
Runtime, *torch*—: una hebra bloqueada en espera activa consume CPU sin hacer trabajo.
El supuesto era mío y era falso; se deja escrito en vez de reinterpretarlo para que
encaje.

**El control 4 es el que autoriza a comparar las dos corridas**, y pasa: `pdfplumber`,
que es monohilo, se movió +12,5% dentro del ±20% declarado. Pero se movió, y en la
dirección de ir más lento — así que **hay una componente de máquina de ~15% metida en
todos los números de A**, y las diferencias por debajo de eso no significan nada.

### La pendiente se dio la vuelta, y con ella un argumento pre-registrado

El pre-registro afirmaba, antes de medir, que excluir el documento de 309 páginas sesga
el total **al alza** —conservador— porque el coste por página baja con la longitud
cuando hay un coste fijo por documento. A 2 hilos la pendiente salió **−9,275e-05**,
negativa, y el argumento se sostenía.

**A 28 hilos sale +1,801e-02, positiva.** El coste por página ahora **sube** con la
longitud dentro de la banda `>50`, porque un documento largo pasa más tiempo dentro de
las secciones paralelas donde está la contención. Así que **a 28 hilos el argumento es
falso y la exclusión sesga el total a la baja**, que es la dirección mala.

No se arregla reinterpretándolo: se publica que la dirección del sesgo **depende de la
configuración de hilos**, y que sólo es conservadora en la configuración de pocos hilos.

### B5-bis, CERRADO · la campaña de L5 cabe con cuatro extractores

```bash
uv run python scripts/poblacion_l5.py
```

| población | docs | páginas | horas de reloj |
|---|---|---|---|
| **con tabla · censo, puntúan** | 338 | 6.076 | 2,54 |
| sin tabla `≤10` · muestra de 584 | 200 | 833 | 0,82 |
| sin tabla `11-50` · censo | 72 | 1.085 | 0,44 |
| sin tabla `>50` · censo | 6 | 739 | 0,21 |
| **total de la campaña** | **616** | **8.733** | **4,01** |
| los 1.000, para comparar | 1.000 | 10.298 | 5,55 |

**Presupuesto congelado en [`runs/l5/computo.yaml`](runs/l5/computo.yaml): ~4 h. Cabe.**
Con los ocho no cabe —serían del orden de 8 h—, y ahí se aplica la regla escrita antes
de medir: **se recortan extractores, no documentos**. Los otros cuatro entran de uno en
uno con `/extractor`, que es el patrón que §16 ya tiene escrito.

Las horas salen del modelo de coste de **pocos hilos**
(`runs/l5/computo_base_2hilos.json`), que es la configuración en la que L5 va a correr:
el experimento A midió que 28 hilos por unidad cuestan entre 4 y 12 veces la CPU para el
mismo reloj o peor.

**QUÉ FAMILIAS CUBRE ESTA TABLA, Y CUÁLES NO.** §16 dice que los ocho extractores cubren
cinco familias. **Los cuatro de esta campaña cubren tres.**

| familia | extractores de §16 | en esta campaña |
|---|---|---|
| parser de texto | `pymupdf4llm`, `pdfplumber` | **los dos** |
| extractor de tablas | `camelot` | **sí** |
| document-AI | `docling`, `marker`, `unstructured` | **`docling`** |
| TEI / científico | `grobid` | **NO** |
| OCR | `tesseract` | **NO** |

**No fue una elección: son todo lo que está medido.** Cambiar `pymupdf4llm` —que repite
familia con `pdfplumber`— por `tesseract` compraría la familia OCR, pero **su coste no
está medido** y es OCR sobre 8.733 páginas: elegirlo hoy sería decidir con un número que
no existe. Va aquí, en la tabla, y no en un límite al final, porque quien lea los
resultados tiene que ver el hueco sin buscarlo.

**La palanca conocida y no accionada.** El paralelismo útil está **entre unidades**, no
en hilos por unidad. Su cuello no será la CPU sino la RAM: `docling` pica **4,4 GB** por
unidad y hay 47 GB, así que salen del orden de **10 unidades a la vez**, no 28. No se
mide ahora: se mide cuando haga falta, que es cuando entren los otros cuatro extractores
y el presupuesto deje de dar. Su predicción se escribe entonces, antes de medirla.

---

## L5 · La puerta: la regresión de 25,5 s, su arreglo, y contra qué se compara

### Antes: n=9, sello `b54ec82`, 14 CPU visibles

`uv run python scripts/medir_puerta.py --tandas 3 --por-tanda 3`, 26 ago 2026.

| ms | valor |
|---|---|
| mínimo | 25 685 |
| mediana | 25 949 |
| **p90** | **27 611** |

σ=751 · carga mediana **1,40** · 0 descartadas por `rc!=0`. **Techo 8500: margen
−19 111 ms**, y el instrumento salió con código 1, que es lo que hace desde L2.

> **n=9 y no n=40, y eso es una desviación del protocolo de esta casa.** Se declara en
> vez de esconderse: **esta serie no se publica como la medida de la puerta**, sólo como
> la constatación de que pasaba del techo por un factor de tres, para lo cual n=9 sobra.
> La medida buena es la de abajo, con sus 40.

### La atribución del salto: tres mediciones, misma máquina, mismo día, en frío

| commit | qué es | mypy en frío | `make fast` en frío |
|---|---|---|---|
| `f89c5b6` | cierre de L4 | **3 576 ms** | **9 399 ms** |
| `99be97d` | el commit ANTERIOR al primer extractor | **25 554 ms** | 30 259 ms |
| `b54ec82` | el primer extractor y el corredor | 23 551 ms | 25 949 (mediana, n=9) |

**La regresión no la trajo el hito que la encontró**: ya estaba en `99be97d`. Entró con
B5-bis, que **no fue un cierre de hito y por tanto no re-midió la puerta**.

### La causa, contada en ficheros y no en sospechas

`mypy --strict src tests -v | grep -c "^LOG:  Parsing"` sobre `b54ec82`: **6 023
ficheros**.

| paquete | ficheros parseados |
|---|---|
| `transformers` | 2 241 |
| `torch` | 1 549 |
| `huggingface_hub` | 146 |
| `docling` | 140 |
| `numpy` | 131 |

La cadena entra por una línea: `tests/unit/test_estimador_computo.py` →
`estimar_computo` → `unidad_computo`, que importa `torch`, `docling` y `camelot`
**dentro de funciones** —y mypy los sigue igual que los de arriba—.

**Y a `transformers` lo trae `camelot`, no `docling`.** Con `torch` y `docling`
saltados quedaban **3 904 ficheros y 18 319 ms**; el recuento por paquete dijo quién
faltaba. De ahí la regla escrita en `pyproject.toml`: **la lista se decide mirando qué
parsea mypy, no adivinando qué es pesado.** Después del arreglo, mypy en frío **4 362 ms**.

### Después: n=40, sello `0f9816c` **sin `+N`**, 14 CPU visibles

`uv run python scripts/medir_puerta.py --tandas 10 --por-tanda 4`, 26 ago 2026.

| ms | valor |
|---|---|
| mínimo | 6 177 |
| mediana | 6 507 |
| **p90** | **6 866** |
| máximo | 6 885 |

σ=178 · medianas por tanda 6 425–6 582 · carga mediana **2,48**, rango 0,17–2,84 ·
0 descartadas. **Techo 8500: margen +1 634 ms.**

### CONTRA QUÉ SE COMPARA ESTE 6 866, QUE NO ES CONTRA EL 8 006

**El 8 006 de L4 se midió EN SERIE**, antes de ADR-0043. La LÍNEA DE CORTE de este
mismo documento dice que a partir de ahí la serie mide otro instrumento, y **su primer
uso real es éste**. El compañero de comparación es el **4 905** del mismo árbol
`1cc8ce8` en paralelo.

**Y ni siquiera ése, en crudo.** El 4 905 se midió el 25 ago con **8 CPU visibles**;
hoy hay 14, y la máquina es una condición declarada desde B5-bis. Así que `1cc8ce8` se
ha vuelto a medir HOY, con el mismo protocolo, para separar máquina de código:

| serie (n=40, paralelo, en frío) | mediana | **p90** | σ | qué aporta |
|---|---|---|---|---|
| `1cc8ce8`, 25 ago, **8 CPU** | 4 643 | **4 905** | 186 | lo publicado en la línea de corte |
| `1cc8ce8`, **26 ago, 14 CPU** | 5 584 | **6 014** | 316 | el MISMO árbol, esta máquina |
| `0f9816c`, 26 ago, 14 CPU | 6 507 | **6 866** | 178 | L5 dentro |

```bash
git checkout --detach 1cc8ce8 && uv run python scripts/medir_puerta.py --tandas 10 --por-tanda 4
git checkout main            && uv run python scripts/medir_puerta.py --tandas 10 --por-tanda 4
```

**El +1 961 del p90 se reparte así: +1 109 de máquina y +852 de código.** Y el de
máquina es el mayor de los dos, lo cual **no era la lectura esperada** —14 CPU deberían
ir más rápido que 8, no más lento—: lo que hay medido es que el mismo árbol tarda hoy
1 109 ms más, y no se sabe por qué. Va a la deuda, no a una explicación inventada.

**La lectura honesta, entonces:** la puerta **ha subido** 852 ms de código sobre la
línea de corte, que es lo que tiene que pasar cuando entran `extract/`, `corpus.store`
y la CLI —**+2 403 líneas en `src/` y +2 776 en `tests/` desde `1cc8ce8`**— y sigue con
**1 634 ms de margen** bajo el techo. No «bajó»: eso sería comparar con el instrumento
de antes de la línea de corte.

### Una serie descartada, y por qué se dice

La primera medida de `1cc8ce8` de hoy salió con **cuatro corridas consecutivas de
13 659 a 16 164 ms** entre las tandas 4 y 5, con el resto entre 5 372 y 6 204 (σ=2 824,
p90 13 659). Es un evento externo a la máquina, no una propiedad del árbol: se repitió
la serie entera y la segunda es la de la tabla. **`medir_puerta.py` no descarta
atípicos** —sólo aborta si el árbol se mueve o si alguna corrida sale en rojo—, así que
la decisión de repetir es de quien mide y por eso se escribe aquí.

### El ruido de una sola corrida en frío, que decidió cómo es el aro del techo

Seis corridas en frío del **mismo árbol**, medidas al montar el aro:

    6 367 · 6 383 · 6 819 · 7 835 · 9 236 · 9 661 ms

**Dos de las seis pasan del techo de 8500**, sobre un árbol cuya serie de n=40 da p90
6 866 y máximo 6 885. O sea que la diferencia no es del árbol: es de la máquina, y una
sola corrida no sirve para decidir contra un techo. Por eso `guard-commit.sh` compara el
**mínimo** de las corridas en frío de ese árbol, y no la última.

**El sesgo va declarado**: un mínimo es optimista. Lo que no puede esconder es una
regresión que multiplica todas las corridas, que es lo que hay que cazar — las 40 de
`b54ec82` estuvieron entre 25 685 y 27 611, sin una sola por debajo del techo.

### Lo que sigue sin haber

Un guardián que avise **entre** cierres ya existe desde este hito: `make fast` registra
su duración y `guard-commit.sh` exige una medida **en frío** bajo el techo para dejar
commitear. Lo que no hay es nada que vigile la **tendencia**: 852 ms más por hito agotan
el margen en dos hitos, y eso no lo dice ningún aro. Va en el límite 102.
