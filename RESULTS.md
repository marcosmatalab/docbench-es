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
