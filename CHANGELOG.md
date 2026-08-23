# CHANGELOG

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado: [SemVer](https://semver.org/lang/es/).

Cada entrada corresponde a un hito de `HITOS.md` y se escribe al cerrarlo con
`/cerrar`. **Los números van en [`RESULTS.md`](RESULTS.md) y el método en
[`docs/metrics.md`](docs/metrics.md), no aquí.** Aquí va qué cambió en cada hito, y
un resumen de las cifras que se retiraron; el historial detallado de correcciones
de cada número vive con su método, en `docs/metrics.md`.

## [No publicado]

### L2 · TEDS validado contra PubTabNet · medido el 2026-08-22, cerrado el 2026-08-23

#### Añadido

- **`core.teds`**, paquete: `teds`, `teds_struct` y `teds_batch`. La distancia es
  **Zhang-Shasha escrito a mano** —la referencia usa APTED—, con el coste de su
  `CustomConfig` copiado línea a línea, y el árbol de TEDS con su forma canónica
  declarada (ADR-0021).
- **`core.cellmatch`**: exactitud celda a celda de §12 y su F1. Emparejado por
  posición y de multiconjuntos.
- **`tests/fixtures/pubtabnet/`, el primer directorio CONGELADO de verdad**: los
  20 casos propios de PubTabNet con su procedencia y su licencia Apache-2.0, más
  6 casos límite, todos con los valores que da **su** implementación.
- **`scripts/pubtabnet_golden.py`**, el generador, que baja `metric.py` y lo
  ejecuta sin tocarle una línea a la lógica. `apted`, `distance` y `lxml` van por
  `uv run --with` y **no** entran en `pyproject.toml`: así nadie puede acabar
  calculando TEDS con la implementación ajena por accidente.
- **101 tests nuevos** (82 → 183), y doce mutantes más (9 → 21).
- **`scripts/ancla.py`**: un ancla de documento publicado tiene que aparecer
  **exactamente una vez** o no se edita nada. Nace de haber duplicado ~230
  líneas de `RESULTS.md` con un `s.index` sobre un encabezado que se repite
  por hito. Mata las dos mitades de la clase, y la que importa es la
  invisible: con cero apariciones se **borra** y nadie echa de menos lo que
  falta.
- **Caché de `mypy` en `fast.yml`**: 1614 ms en frío contra 124 en caliente.

#### Cambiado

- **`from_html` marca como cabecera un `<td>` dentro de `<thead>`.** Era un fallo
  de L1: PubTabNet escribe **todas** sus cabeceras así, o sea que `is_header`
  salía `False` en el 100% de ellas.
- **Presupuesto de `max_examples` declarado en las ocho suites de propiedad**,
  que hasta ahora heredaban el 100 por defecto sin decirlo.

#### Corregido

- **La justificación de `holes()` en L1 era falsa.** ADR-0018 decía que era «lo
  que L2 usa para emitir celda ausente»; **`core.teds` no la llama**, y hay un
  test que lo comprueba por AST. La distinción hueco/celda vacía sí se respeta,
  pero por construcción del árbol. Corregido en ADR-0018, en el código y en
  `RESULTS.md`.
- **Un test afirmaba `0 <= teds <= 1`, y es falso.** TEDS puede salir **negativo**
  —la distancia se calcula con la raíz y el denominador sin ella— y la referencia
  devuelve el mismo −0,142857. La cota real es [−1, 1]. Lo encontró `hypothesis`
  en una corrida de la puerta, no la revisión.

#### Corregido en el bloque de cierre

- **Se publicó una palanca que no existe.** `RESULTS.md` y `docs/metrics.md`
  decían que bajar la suite de normalización de 100 a 50 ejemplos ahorraba
  **~285 ms**, presentado como medido. Era una estimación por regla de tres.
  Medido: **990 / 946 / 935 ms** a 100 / 50 / 25 ejemplos, o sea **44 ms**. El
  coste lo domina el arranque del proceso. Corregido en los dos ficheros con el
  error de razonamiento escrito.
- **La distribución de la puerta estaba caracterizada con dos tandas.** Remedida
  con **40 corridas en frío en 10 tandas**: mediana 5517, p90 5801, máximo 5858,
  σ=134. El p90 consumía el **97%** del techo de 6000.
- **Auditoría del fallo de `is_header`**: ninguna cifra publicada por L1 dependía
  de él. Verificado por dos vías —`is_header` no aparece en la ruta de validación,
  y voltearlo en 500 tablas no cambia ni un hallazgo— y **fijado con un test de
  propiedad** para que deje de ser una comprobación de una sola vez.
- **La tabla de asesinos se publicó con un recuento mal hecho.** Al reescribir
  `matar.py --tabla` para dar las dos agregaciones se perdió el colapso por
  corrida, y un test **parametrizado** sumaba una vez por caso: 7 parámetros × 3
  corridas = 21, distinto de 3, y el test salía de la columna «mata SIEMPRE»
  **aunque mate en las tres**. Afectaba a cinco filas. La versión anterior de la
  tabla, que sí colapsaba, era la correcta. Corregido con un `set` por corrida y
  las tres versiones reconciliadas a la vista en `RESULTS.md`.
- **«Mata SIEMPRE» se publicó como categoría siendo una estimación con n = 3.**
  Medido con `--reps 10`, `test_idempotente` mata a `normalizador_agresivo`
  **26 de 30** veces: p̂ = 0,867, Wilson 95% [0,703 – 0,947], o sea que una tanda
  de tres lo llama determinista el **66% [35% – 85%]** de las veces. Ahora el n y
  el intervalo van al lado de la tabla y `--reps` permite afinarlo.

#### Corregido en el escrutinio adversarial de L2

El revisor trajo **12 hallazgos y ninguno se descartó**. Los dos primeros son de
los que la regla que gobierna el repo llama el fallo más grave posible: el repo
afirmaba algo que el código no cumplía.

- **El criterio de aceptación de L2 no podía ver un error en el árbol.** El golden
  se genera dando a la referencia el render canónico de las mismas tablas, así que
  el mapeo `CanonicalTable → árbol` **aparece en los dos lados y se cancela**.
  Medido: con las columnas de cada fila invertidas, la suite entera daba
  **145 passed**; con `<thead>` reducido a la primera fila, también. Y regenerando
  el golden bajo esos mutantes seguía verde, o sea que un error presente el día de
  la generación sería **invisible para siempre**. Arreglado con
  `test_el_render_canonico_es_el_que_genero_el_golden` sobre los campos
  `html_canonico_*` que el fixture **ya guardaba y nadie miraba**, más un caso a
  mano de dos filas de cabecera. Los dos mutantes van versionados y mueren en
  **20** y **7** tests. Lo que sigue sin cubrirse, en `LIMITS.md` 52.
- **`teds_batch` perdía tablas en silencio.** La clave es la del documento, así que
  un documento con varias tablas manda varios pares; `dict[clave] = nota`
  **sobrescribía**. Medido: la tabla mal extraída desaparecía y
  `evaluable_coverage` seguía diciendo 1,0 — la regla de oro 6 rota en sus dos
  mitades, y con sesgo hacia arriba justo en los documentos con más tablas.
  [ADR-0024](docs/adr/0024-teds-batch-varias-tablas-por-documento.md).
- **Cinco números que se contradecían entre ficheros del repo**: 5440/6000 contra
  5604/8500, «17×» contra «16×», «133 tests» contra 145, «12 valores distintos»
  contra 15, «cinco unos» contra seis. Y **«Cifras retiradas: Ninguna» era falso**:
  este hito retira cuatro.
- **Tasas Bernoulli publicadas sin intervalo**, contra la regla de oro 2. Wilson
  95%: 26/30 → **[0,703 – 0,947]**, y el 66% derivado pasa a **66% [35% – 85%]**.
  Los 0/15 y 2/15 de `max_examples` llevan los suyos, **que se solapan** — y eso
  es lo que sostiene la palabra «ruido», que sin intervalo no la sostenía nada.
- **El techo de 8000 ms no salía de la fórmula del propio ADR-0022**, que da 7623,
  7635 u 8467. Era un número redondo vestido de fórmula, y encima quedaba por
  debajo de la mediana proyectada de L3. Recalculado: **8500**, el escenario
  adverso redondeado **hacia arriba**. Y el «p90» del script queda declarado: es
  el 37.º valor de 40, o sea el percentil 92,5 — conservador, y se deja porque
  cambiarlo haría incomparables L0, L1 y L2.
- **«Para una tabla de documento es inmediato» era falso y no estaba medido.**
  `scripts/coste_teds.py`: 101 ms a 20x8, **1617 ms a 60x10**, **4712 ms a
  100x10**. `LIMITS.md` 42 reescrito con la tabla y con las tres salidas que L5
  tendrá que elegir.
- **El golden se generaba ejecutando código bajado de una rama móvil.** Ahora el
  script comprueba el **SHA-256** de `metric.py` y aborta si cambió. De paso, su
  recorte pasaba por un `.index` —la misma clase de fallo que duplicó 230 líneas
  de `RESULTS.md`— y ahora pasa por `unica`.
- **`StructureMetrics.cell_f1: float` no podía recibir lo que produce
  `cell_f1()`**, que devuelve `float | None`. O el tipo estaba mal o L5 acabaría
  metiendo un 0,0, que es justo lo que ADR-0006 prohíbe. Corregido en `types` **y
  transcrito al manual** (regla de oro 8). De rebote, mypy destapó que el tipo del
  JSON del fixture era falso: se escribió por lo que se usaba, no por lo que el
  fichero tiene.
- **§12 dice «emparejado por posición tras alinear» y `cellmatch` no alinea.** La
  decisión era buena y vivía en un docstring, sin ADR y sin límite:
  `grep -rn "alinea" LIMITS.md RESULTS.md docs/` no devolvía nada.
  [ADR-0025](docs/adr/0025-la-exactitud-de-celda-no-alinea.md), límite 53, y
  transcrito a §12.
- **`_firma` ignoraba `is_header` sin decirlo**, justo en el hito que descubrió que
  `is_header` salía mal en el 100% de las cabeceras de PubTabNet. Se declara con su
  medida —`cell_accuracy` = 1,0 y `teds` = **0,5** sobre dos tablas que sólo
  difieren en el flag— y un test fija **las dos mitades**.
- **La barrera de los conversores sin validar cubría 3 scripts de 7**, escritos a
  mano, mientras `LIMITS.md` 49 afirmaba «los scripts que producen números
  publicados». Ahora recorre todos con `rglob`.
- **`ESTADO.md` decía «Siguiente paso: `/hito L1`»** con L1 y L2 cerrados, y su
  tabla de ADR enumeraba «los cuatro» existiendo 0013–0025. No es cosmético: el
  hook `SessionStart` inyecta ese fichero entero, así que la sesión siguiente lo
  lee antes que nada.

#### Corregido en la auditoría en frío de `b7cc6c3`

**El guardián de recuentos se rompía al correrlo solo.** `uv run pytest
tests/unit/test_recuentos.py` fallaba en árbol limpio, con un mensaje que hablaba
de una desincronización que no existía. Dos causas encadenadas:

- **La precondición no estaba declarada.** Los recuentos salen de lo COLECTADO, así
  que un fichero suelto —o un `-k`— daba `dentro=0` y alimentaba la comparación con
  cifras falsas.
- **Un patrón laxo.** `0 (?:muertes )?de {_N} tests` se escribió para el control
  negativo del arnés de mutantes, pero el «muertes» opcional lo hacía casar con
  cualquier «0 de N tests» — incluido el texto que el propio test se construye. Y
  la laxitud no dependía de la primera causa: un documento que escribiera «0 de 23
  tests» hablando de los de fuera se habría leído como `dentro`.

**Lo que se hizo con cada cosa:**

- **La precondición desaparece en vez de declararse**
  ([ADR-0026](docs/adr/0026-los-recuentos-se-recuperan-no-se-saltan.md)): en una
  corrida parcial los recuentos se **recuperan** con un `--collect-only` en
  subproceso, **233 ms medidos**, y sólo se pagan cuando la selección incluye estos
  tests. Descartadas por escrito las dos alternativas: **saltar** —un guardián que
  se salta es un guardián muerto fuera de CI— y **fallar** —un rojo que no es un
  bug enseña a ignorar el color, límite 25—.
- **Contrapartida de recuperar en vez de saltar**: un test lee el `Makefile` y
  `fast.yml` y se cae si la puerta deja de correr `tests/unit` entero o si CI deja
  de llamar a `make fast`. El guardián funciona en cualquier corrida, pero lo que
  impide que un número viejo llegue a `main` es que la puerta lo ejecute.
- **Todos los patrones repasados con el mismo criterio**, no sólo el de la línea 96.
  Cinco eran laxos y se estrecharon: `[Ss]on {_N} mutantes` casaba con «Son 0
  mutantes supervivientes», `cubr[eí]a?n? {_N} de \d+` con «cubre 3 de 7 casos»,
  `[Ll]os {_N} restantes` con «los cinco conversores restantes», `{_N} mutantes
  existentes` con prosa histórica, y el de la línea 96 con cualquier «0 de N
  tests». **El criterio queda escrito**: ante la duda el patrón se ESTRECHA, y si
  una redacción no casa se cambia la redacción, no el patrón.
- **Segundo control negativo, el que faltaba: cifras DEGENERADAS.** El que había
  cubría «los números no cuadran entre documentos»; éste cubre «los números contra
  los que comparo no son una medición». `exigir_sano()` impone cuatro invariantes
  estructurales —`total == dentro + fuera`, y los tres recuentos ≥ 1— y
  `desacuerdos()` los exige antes de mirar un solo documento.

#### Añadido

- **`scripts/cobertura_patrones.py`**: censo de 30 frases que alguien escribiría en
  este repo, en las dos direcciones. **0 falsos positivos de 12** y **7 escapes de
  18**. `LIMITS.md` 54 deja de ser una afirmación y pasa a tener número y comando.
- **Tres mutantes para el guardián**, que era el candado más nuevo del repo y el
  único sin uno: `recuentos_todo_vale` (la guarda de degenerados acepta todo),
  `recuentos_sin_claude` (deja de mirar `.claude/`) y `recuentos_plano_flojo` (no
  colapsa saltos de línea, lo que además rompe las excepciones históricas). Los
  tres murieron con un solo asesino, y se les añadió el segundo partiendo los tests
  que mezclaban dos preguntas. Sale de la deuda 7 de `ESTADO.md`: *«un candado que
  no se ha probado contra su propia rotura no es un candado»*.

#### Corregido en la auditoría en frío de `c71b31f`

- **La corrección de los recuentos llegó a `RESULTS.md` y no a los otros tres
  sitios**, dentro del mismo commit. `LIMITS.md` 51, la deuda 7 de `ESTADO.md` y
  `.claude/skills/cerrar/SKILL.md` seguían diciendo «12» donde hoy hay 18 y «38»
  donde hoy hay 28, y los dos primeros **nombraban a `teds_limites` y
  `teds_batch` como módulos sin mutante** cuando `teds_siempre_cero` y
  `batch_sobrescribe` ya apuntaban a ellos. La deuda mandaba a L3 escribir
  trabajo que ya existía.
- **La deuda 7 se reescribe contra la lista real** —`types_invariantes`, `ancla`,
  `recuentos`, `types`, `errors`, `sin_consumidor`— con su precio recalculado:
  **~1 h 40 min**, no «~20 min por módulo nuevo». Y con el orden de urgencia
  dicho: `ancla`, `recuentos` y `sin_consumidor` son **barreras**, código cuyo
  único trabajo es ponerse rojo, y un candado que no se ha probado contra su
  propia rotura no es un candado.

#### Añadido para que esa clase no se repita

- **`tests/unit/conftest.py` + `tests/unit/test_recuentos.py`.** Los recuentos
  volátiles —mutantes, tests dentro y fuera del arnés, total— se calculan en
  `pytest_collection_modifyitems`, o sea **en cada `make fast`**, leyendo el
  `PLAN` de `matar.py`. No hay fichero almacenado, así que no hay nada que
  sincronizar; y el recuento es exacto, con la parametrización ya resuelta.
  Un test compara contra **todo lo publicado, `.claude/` incluido**, que es donde
  se quedó el tercer «12».

  **Descartado: comparar los documentos entre sí por regex.** Habría cazado este
  caso y no el peor — si los cuatro dicen 12 y la realidad es 18, concuerdan y
  pasa en verde. **Descartado: que `matar.py` escriba un JSON.** Sería una quinta
  copia capaz de quedarse vieja, el mismo fallo una capa más abajo.

  **Control negativo, medido**: desincronizando a propósito una cifra en cada uno
  de los cuatro documentos, la primera versión cazó **2 de 4** —`arnés cubr` no
  casaba con «El arnés DE MUTANTES cubre», y exigir «tests» detrás dejaba pasar
  «149 de 177.» con punto—. La publicada caza **4 de 4**. Lo que sigue sin
  cubrirse, en `LIMITS.md` 54.

#### Corregido en el paso 3 de `/cerrar`, que es donde se ve si la estrategia llega

- **Ninguna propiedad podía generar `n_cabecera >= 2`**: `_estrategias.py` fijaba
  `is_header = fila == 0`. Ampliado a un sorteo de 0 a 2, que llega a 2 en **11 de
  300** ejemplos… y **seguía sin bastar**: a 30 ejemplos por suite eso es ~1 caso.
  Añadida `tabla_con_dos_filas_de_cabecera`, que la genera **a propósito**, más la
  propiedad `test_mover_la_frontera_de_la_cabecera_cambia_la_estructura`.
- **Y el hallazgo de fondo: ninguna propiedad de TEDS puede ver un reetiquetado
  consistente del árbol.** Todas son invariantes —rango, simetría, una tabla
  contra sí misma vale 1— y un invariante no cambia si `T` cambia igual en los dos
  lados. Medido: **24 propiedades pasan** bajo el mutante del `<thead>` y **las 6**
  bajo el del orden invertido. La propiedad nueva sí lo ve porque **perturba un
  solo lado**; lo demás lo cubre el censo de los 20 casos.
- **`teds_batch` no tenía ninguna propiedad**, y su familia de fallo nueva —varias
  tablas por clave— no la generaba nada. Añadida, con las claves sorteadas de un
  alfabeto de **dos** para que la colisión ocurra.
- **El censo de invariantes no miraba por familia.** Un 8525/8525 sale verde igual
  si una familia deja de generar mutantes. Ahora cuenta las **20 familias**, avisa
  si alguna queda vacía, y `--familias` publica el desglose.

#### Decisiones

- [ADR-0022](docs/adr/0022-el-techo-de-la-puerta.md) · el techo de la puerta:
  **8500 ms local / 20 000 en CI**, re-justificado en cada cierre, que **avisa**
  mientras que el 90 s del manual **bloquea**. Con la proyección de L3 escrita:
  **6000 no aguantaba L3 en ningún escenario**.
- [ADR-0023](docs/adr/0023-teds-negativo-suelo-al-publicar.md) · el TEDS negativo
  se calcula tal cual y se recorta **sólo al publicar**, con `para_publicar()`.
- [ADR-0020](docs/adr/0020-teds-compara-contenido-canonico.md) · TEDS compara el
  contenido **canónico** y el golden se genera sobre él. **Transcrita al manual**
  (§9.2) en el mismo commit.
- [ADR-0021](docs/adr/0021-forma-canonica-del-arbol-de-teds.md) · la forma del
  árbol: `<thead>` con el prefijo de cabecera, todo `<td>`, el hueco sin nodo.
  **Transcrita al manual** (§9.2) en el mismo commit.
- [ADR-0024](docs/adr/0024-teds-batch-varias-tablas-por-documento.md) · un
  documento con **varias tablas**: la nota es la media de sus tablas evaluables y
  ninguna se pierde. La cobertura se cuenta sobre **tablas**, que es lo que §6 ya
  decía. **No contradice el manual: lo cumple.**
- [ADR-0025](docs/adr/0025-la-exactitud-de-celda-no-alinea.md) · *«tras alinear»*
  de §12 se lee como **la colocación canónica de L1**: `cell_accuracy` no hace un
  segundo alineamiento y es exactitud **posicional**. **Transcrita al manual**
  (§12) en el mismo commit, con `is_header` fuera de la firma y su medida.
- [ADR-0023](docs/adr/0023-teds-negativo-suelo-al-publicar.md) **transcrita a
  §9.2** en este commit: `para_publicar()` era una función pública que la interfaz
  del manual no declaraba, y una interfaz incompleta es una contradicción como
  cualquier otra.

#### Cifras retiradas

- **Sí las hay, y decir «ninguna» era el error.** Este hito retira los **285 ms**
  de la palanca de `max_examples` (valen **44**), la caracterización de la puerta
  por dos tandas (remedida con 40 corridas), el techo de **6000 ms** (ADR-0022 lo
  sube a 8500 local / 20 000 CI) y una tabla de mutantes con el recuento mal
  hecho. Detalle arriba, en «Corregido en el bloque de cierre».
- La serie de la puerta suma su tercer punto: 1742 ms en L0, 3829 en L1,
  **5604 ms en L2** (n=40, p90 5728), con techo declarado de **8500**. La versión
  anterior de esta línea publicaba 5440 y 6000: los dos números que el propio
  hito acababa de derogar.

### L1 · La forma canónica: invariantes y los cinco conversores · cerrado el 2026-08-22

#### Añadido

- **`core.canonical`**, paquete y no fichero (§8, precedente de ADR-0013): los
  cinco conversores de §9.1 —`from_html`, `from_markdown`, `from_dataframe`,
  `from_tei`, `from_text_heuristic`—, `validate()`, `holes()` y
  `normalize_cell_text()`. Uno por fichero, ninguno por encima de las 300 líneas
  de `CLAUDE.md`; el mayor es `_normalizar.py` con 226.
- **El enum cerrado `HallazgoTabla`** en `types/_invariantes.py`: 9 hallazgos
  fatales y 3 informativos. `CanonicalTable.is_wellformed()` deja de levantar
  `NotImplementedError` y devuelve `(ok, problemas)`; `core.canonical.validate()`
  delega en el método público.
- **Tests nuevos** (15 → 82), 17 de ellos property-based, y
  `scripts/censo_invariantes.py`, el censo determinista que produce el número
  publicado.
- **`src/docbench_es/py.typed`**: el paquete declara que va tipado, que es lo que
  necesita el extractor de un cliente (§13.1) para analizarlo con `mypy --strict`.

#### Cambiado

- **`mypy --strict` tipa ahora también `tests/`**, no sólo `src`. Cuesta
  **+1284 ms** de puerta, medidos, y se paga solo: ver más abajo.
- **`DocRef.key()` escapa a mano** en vez de con `urllib.parse.quote`. No es una
  preferencia: `.importlinter` prohíbe `urllib` en `core`, `core` importa `types`
  y el contrato se rompía por esa cadena indirecta en cuanto **cualquier** módulo
  de `core` tocara el modelo de datos. Era una mina latente de L0 que L1 hizo
  saltar; el contrato no se toca para que quepa el código.
- **`normalize_cell_text` mapea también `Zl` y `Zp`** —U+2028 y U+2029—, que no
  son `Zs` y se estaban borrando en vez de mapearse.
- **`/cerrar` estrena tres pasos**: los dos mutantes, el alcance de las
  estrategias tras cambiar la implementación, y la verificación de que los
  mutantes de un censo están de verdad rotos.
- **Los nueve mutantes se versionan** en `scripts/mutantes/`, con
  `matar.py` para correrlos todos: `RESULTS.md` publica sus recuentos y la regla
  de oro 2 no distingue entre tipos de número.

#### Corregido

- **Un `assert` estáticamente muerto que decía proteger «dinero en `Decimal`,
  nunca `float`» y no protegía nada.** En `test_types_invariantes.py`:

  ```python
  assert isinstance(extraccion.cost.eur, Decimal)
  assert not isinstance(extraccion.cost.eur, float)   # ← siempre verdadero
  ```

  Con `eur: Decimal`, la segunda línea es **siempre** cierta: `Decimal` no hereda
  de `float`, son bases disjuntas. La comprobación no podía fallar nunca, así que
  el test afirmaba proteger una de las reglas de «Qué NO hacer nunca» de
  `CLAUDE.md` sin protegerla. La delata `mypy --strict` con `warn_unreachable`, y
  **sólo la caza tipando los tests**: ninguna corrida de `pytest`, ningún linter y
  ninguna revisión a ojo la habrían visto, porque el test pasaba en verde.

  Arreglado borrando el tipo estático a propósito —`importe: object = ...`— para
  que la comprobación sea del tipo en **ejecución**, que es donde el riesgo existe
  de verdad: Python no hace cumplir las anotaciones, así que `Cost(eur=0.1)` con
  un `float` corre sin protestar.

  **Es lo que justifica los 1284 ms.** Un test que miente en verde cuesta más que
  un segundo de puerta.

- **La estrategia de `DocRef.key()` no alcanzaba la familia de fallo nueva.**
  Genera los dos pares partiendo la misma cadena, así que un campo es siempre
  prefijo del otro y una colisión del **escapado** le queda fuera por
  construcción. Medido: contra un escapado en mal orden, ese fichero pasa 7 de 7.
  Lo cubre ahora el censo exhaustivo de `tests/unit/test_types_clave.py`.

- **El censo de mutación exigía falsos positivos.** Crecer un span sobre una tabla
  con hueco de cola **rellena el hueco** y produce una tabla legal; el censo la
  contaba como «tendría que detectarse». Apareció al meter las formas reales del
  BOE, y ahora esas mutaciones son un control negativo aparte.

#### Corregido en el escrutinio adversarial del cierre

Once hallazgos, todos tratados. Los que cambiaron el código:

- **`from_html` SÍ producía solapes, y el límite 30 afirmaba lo contrario.** El
  colocador sigue el estándar —la celda va al primer hueco libre de su primera
  columna y, si las siguientes están ocupadas, se pisan—, así que un *table model
  error* del HTML da una tabla con `SOLAPE`. El código era correcto; **la
  afirmación publicada era falsa**. Reescrito el límite, y el caso entra ahora en
  el censo y en el golden. Consecuencia nueva y anotada: en L4, `truth.derived`
  puede emitir una tabla fatal desde el XML del BOE.
- **`int(texto) if texto.isdigit()` reventaba con `²`.** `"²".isdigit()` es `True`
  y `int("²")` lanza. Un conversor del núcleo que lanza sobre entrada de terceros
  contamina la tasa de fallo por extractor, y el BOE usa `<sup>2</sup>` a montones.
- **60 bytes de HTML costaban 28 s y 7,5 GB.** `holes()` materializaba el
  rectángulo de cada celda **sin recortarlo a la tabla**: un `rowspan="65534"
  colspan="1000"` daba 65 millones de tuplas. Recortado: 0,001 s y 42 MB.
- **`from_dataframe` desplazaba una columna con pandas de verdad.**
  `DataFrame.itertuples()` lleva `index=True` por defecto y mete el índice como
  primer elemento. **No lo cazaba ningún test porque el doble simplificaba la
  interfaz real**: se ha hecho fiel. Y un `RangeIndex` de camelot ya no se
  convierte en una fila de cabecera inventada.
- **Un defecto emitía hasta cuatro códigos fatales.** Ahora `comprobar` **deja de
  analizar la cobertura si alguna celda no se pudo colocar**: con una celda
  descartada no se sabe qué área ocupaba, así que todo hueco que saliera sería
  consecuencia de ese defecto. La tasa por código de L5 habría salido inflada.
- **El censo exigía falsos positivos y no ejercitaba dos códigos.** `DIMENSION_
  INCOHERENTE` y `SOURCE_FORMAT_DESCONOCIDO` no aparecían en ninguna mutación, y
  para cinco familias se exige ahora el conjunto **exacto** de códigos fatales.
- **Seis casos degenerados declarados en docstring no tenían test**, y uno de los
  que sí lo tenía **pasaba por otro motivo del que decía**: la entrada de
  «columnas inconsistentes» del heurístico de texto no llegaba a esa rama.

Los que cambiaron los números publicados, y son los que más duelen:

- **El 63% y el 42% del sondeo son de DOCUMENTOS CON TABLA, no de tablas.** El
  sondeo midió `n=57` documentos, con IC `[50–74]` y `[30–55]`. Estaba mal en seis
  sitios, y de ahí salía un **«cobertura evaluable del 37%»** que era una resta
  sobre otra población y encima publicada sin intervalo: **retirado** (límite 36).
- **Los conteos de etiquetas no se midieron «dentro de las tablas»**, sino sobre
  el documento completo. De los **489 `<img>`, 468 están en documentos sin ni una
  tabla**: el número que aplicaba era 21. Reetiquetados los doce recuentos.
- **«Siete propiedades de `hypothesis`» eran 17**, y dos líneas más abajo decía
  «seis». Y el margen de la puerta decía 33× donde `RESULTS.md` decía 22×.

#### Decisiones

- [ADR-0017](docs/adr/0017-normalizacion-no-toca-los-numeros.md) · la
  normalización no toca los números, ni los acentos, ni ningún glifo visible.
  **Contradecía el docstring de §9.1**, transcrito al manual en el mismo commit.
- [ADR-0018](docs/adr/0018-hueco-de-cola-y-hueco-interior.md) · hueco de cola
  legítimo, hueco interior fatal, y los huecos se derivan.
- [ADR-0019](docs/adr/0019-los-invariantes-se-detectan-no-se-impiden.md) · los
  invariantes se detectan a posteriori, no se impiden en construcción.

#### Cifras retiradas

- Ninguna. Las de L0 siguen vigentes; la del tiempo de puerta continúa como
  **serie** en `docs/metrics.md`: 1742 ms en L0, 4060 ms en L1.

### L0 · Esqueleto, canon y contrato de capas · 2026-08-21, cerrado el 2026-08-22

#### Añadido

- **El modelo de datos completo de §6**, en `src/docbench_es/types/`: 32 nombres
  exportados, todos `frozen`. Incluye la forma canónica de tabla, extracción,
  verdad, preguntas, glosario, plan de muestreo, campaña y los agregados de los
  tres niveles.
- **La jerarquía de errores de §6.9**, en `src/docbench_es/errors.py`, con **el
  código de salida de §11 como atributo de clase**: política 2, presupuesto 3,
  infraestructura 4, contrato 5, `TruthUnavailable` 6. Las tres cuyo significado
  coincide con el contrato heredan **también** de la excepción de `benchcore`,
  para que un `except BenchcoreError` del motor cace lo que lance el plugin de un
  cliente.
- **15 tests unitarios** en `tests/unit/`, dos de ellos **property-based** con
  `hypothesis`, que convierten en contrato afirmaciones que hasta ahora solo
  estaban escritas en el manual: que el modelo es inmutable —atributos **y**
  mapas—, que `types` no importa nada del proyecto, que nadie de fuera importa sus
  submódulos privados, que la tabla de códigos de salida es código y no prosa, que
  el enum de fallo de extracción está cerrado y se exige en el agregado, que un
  fallo sin causa no se puede construir, y que **`DocRef.key()` es inyectiva**.
- `docs/adr/0014-mapas-inmutables-en-el-modelo-de-datos.md`.
- `README.md`, `RESULTS.md`, `LIMITS.md`, `CHANGELOG.md` y `LICENSE` (Apache-2.0).
- `docs/reading-order.md` con las rutas de 5 min, 30 min y 2 h.
- `docs/adr/0013-types-como-paquete.md`.
- Los trabajos de CI `full.yml` y `nightly.yml`.

#### Cambiado

- `src/docbench_es/types.py` pasa de fichero a **paquete** `types/` con cinco
  submódulos privados. `docbench_es.types` sigue siendo la única superficie de
  import. Motivo y alternativa descartada en el ADR-0013.
- `full.yml` y `nightly.yml` **nacen dormidos**, con `on: workflow_dispatch:`
  únicamente. Se encienden en L7. Ver el límite 25 de `LIMITS.md`.

#### Eliminado

- `tests/unit/test_humo_unit.py`, el marcador que traía el pack de arranque. Ese
  directorio ya tiene tests de verdad. Los de los otros ocho directorios siguen
  en pie hasta que su hito los sustituya.

#### Corregido en el escrutinio de cierre

El escrutinio adversarial de `/cerrar` sacó 12 hallazgos. Diez se arreglaron, uno
se declaró como límite y uno resultó no reproducirse. Los que cambiaban una
afirmación del repo:

- **`DocRef.key()` colisionaba.** `("an", "boe/A/B")` y `("an/boe", "A/B")` daban
  la misma clave siendo documentos distintos. `key()` es **la unidad de
  remuestreo del bootstrap agrupado**: dos documentos colapsados en una clave
  estrechan el intervalo y publican más precisión de la que hay. Ahora va
  percent-encoded, con test de propiedad.
- **`frozen=True` no congelaba los mapas**, y un test afirmaba que sí. Ver
  ADR-0014.
- **Un fallo sin causa era construible** (`failed=True, failure_reason=None`), y
  `failures` estaba tipado `dict[str, int]`, eludiendo el enum cerrado justo en el
  agregado que se publica. Las dos cosas rompían la regla de oro 6.
- **`cell_at` no declaraba el caso `span < 1`**, en el que la celda desaparece.
- **El README afirmaba en presente cinco mecanismos que no existen** (política,
  motor, CLI, adaptador de entidad). Reescritos en futuro y con su hito.
- **Quince `__init__.py` decían «lo rellena /hito L0»** y L0 los deja vacíos.
  Ahora cada uno nombra el hito real que lo rellena.
- **`LIMITS.md` 19 presentaba L8b como medido**, y está pendiente.
- **`stop-gate.sh` dejaba colar la puerta en rojo**: la marca de caché hasheaba el
  listado de `git status`, no el contenido, así que romper más un fichero que ya
  figuraba como `M` daba la misma huella. Y su detección de congelados no veía un
  fixture aún sin commitear, que es su estado durante todo el hito que lo crea.

#### Verificado, ejecutándolo

**1 · La puerta, en verde y dentro de presupuesto.** `make fast` en **4,43 s** en
el runner de GitHub contra los 90 s de §15, corrida `32572683716` sobre `28186b9`,
el commit que cierra L0. `RESULTS.md` separa ese número del job (11 s) y del run
(15 s), que no son lo mismo, y le pone **rango observado** —que no es un intervalo
de confianza, y así se declara—: **toda corrida cuyo árbol de código sea idéntico**
al del cierre entra en la muestra. Hoy son cuatro —`78ee8f0`, `4e4ea0b`, `28186b9`
y `3a6b9d7`, que sólo se diferencian en markdown— y dan **mínimo 3,41 s, mediana
3,95 s, máximo 4,43 s**, con corte a 22 ago 2026.

**2 · Que `python-version` no hacía nada.** Los tres workflows se lo pasaban a
`astral-sh/setup-uv@v3`, que **no acepta ese input**. Comprobado empujando una
rama con un paso de diagnóstico (corrida `32531009942`):

```console
##[warning]Unexpected input(s) 'python-version', valid inputs are ['version',
  'checksum','github-token','enable-cache',...]
##[warning]Failed to restore: Cache service responded with 400
Using CPython 3.12.3 interpreter at: /usr/bin/python3.12
```

El pin no estaba donde el fichero decía: el runner caía en el Python del sistema
por casualidad. Arreglado migrando a `setup-uv@v6`, dejando `.python-version` como
fuente única y **añadiendo un paso que lo comprueba** en vez de suponerlo. Tras el
arreglo (corrida `32537436252`): `esperado=3.12 real=3.12`, `Cache hit`, y cero
avisos de configuración.

**3 · El control negativo.** Con `import httpx` metido a mano en `core/`,
`make arch` sale en rojo. Salida literal:

```console
$ make arch
El nucleo es puro: no toca red, disco ni proveedores BROKEN
La deriva funciona SIN verdad de referencia nueva, ... KEPT
La recomendacion se deriva de mediciones publicadas, ... KEPT

Contracts: 3 kept, 1 broken.

----------------
Broken contracts
----------------

El nucleo es puro: no toca red, disco ni proveedores
----------------------------------------------------

docbench_es.core is not allowed to import httpx:

-   docbench_es.core._control_negativo -> httpx (l.3)

make: *** [Makefile:32: arch] Error 1
```

Detalle que merece la pena: **`httpx` ni siquiera está instalado en el entorno**.
El contrato es análisis estático sobre el AST, no una comprobación en tiempo de
ejecución, así que detecta el import prohibido aunque el paquete no exista. Al
borrar el fichero, `Contracts: 4 kept, 0 broken`.

**4 · El contrato se encuentra.** `uv run lint-imports` lee `.importlinter` y
analiza el grafo entero: 28 ficheros y 34 dependencias cuando se comprobó, 32 y
42 al cerrar el hito. Con el nombre `importlinter.ini`
respondería *"Could not read any configuration"* y el CI se pondría rojo por el
motivo equivocado.

**5 · Los tests nuevos pueden ponerse rojos.** Comprobado con un mutante: un
fichero en `core/` que importa `docbench_es.types._tabla` hace fallar a
`test_nadie_de_fuera_importa_los_submodulos_privados_de_types`, y el fallo nombra
al culpable. Un test que solo se ha visto en verde no demuestra nada.

#### El reparto de `RESULTS.md`, y las correcciones de su número

`RESULTS.md` llegó a 228 líneas, de las cuales la mayoría eran metodología de un
solo tiempo. Se parte, según §8 del manual:

- **`RESULTS.md`** son los **números**: tabla, presupuesto, margen, corrida,
  commit y comando de reproducción. Crece por hitos, no por matices. Queda en 95.
- **`docs/metrics.md`** —creado aquí— es el **método**: qué mide cada ventana, la
  resolución del instrumento, la incertidumbre y su derivación, qué entra y qué no
  en «en frío», por qué el local no sustituye al runner, y **el historial completo
  de correcciones del número**. Ahí está el detalle de todo lo de abajo.

El número de la puerta se publicó mal **seis veces** antes de quedar en 4,43 s, y
el registro entero, con sus cifras y su verificación, está en
[`docs/metrics.md`](docs/metrics.md). En una línea cada una: se citó la corrida del
pack de arranque en vez de la de L0; se publicaron los **12 s** del *run* como si
fueran `make fast`, y luego el **job** como cota superior porque el log había
expirado; se sostuvo **3,41 s**, el mínimo de la muestra, cuando ya existían las
tres corridas; se llamó **«intervalo»** a un rango de n=3; se escribió **«±30%»**
para una dispersión asimétrica; y se publicó **`4,4304 s`**, cuatro decimales sobre
una frontera de decenas de milisegundos.

**La corrección tuvo a su vez tres errores, cazados por escrutinio adversarial
antes de publicarse:** «setecientas veces» donde son quinientas, llamar «suelo» a
una ventana que también sobra por el arranque, y estadísticos derivados con tres
cifras significativas. Van corregidos y documentados.

**Y un error de la propia arqueología:** decía «los **16 s** del run» donde fueron
**12 s**. El 16 es el run de la corrida nueva; se actualizó la tabla y se arrastró
el número a la frase histórica sin comprobarla. Verificable con
`git show 78ee8f0:RESULTS.md`.

#### Corregido después del cierre

- **`make clean` no borraba `.hypothesis`**, así que el «en frío» local nunca lo
  era: la base de ejemplos de los dos tests property-based sobrevivía a todas las
  corridas mientras el runner nacía sin ella. Arreglado en el `Makefile` y añadido
  a `.gitignore`. Remedido en reposo: la mediana en frío pasa de **1095 a
  1742 ms**. Cronometrado directamente, `pytest` tarda 368–384 ms con la caché
  presente y 953–1026 ms sin ella: **la caché valía ~615 ms**, y el número
  anterior estaba inflado a favor del local en más de un tercio. Era una salvedad
  que se podía eliminar, y documentarla en vez de arreglarla habría sido deuda
  disfrazada de rigor.
- **Tres ficheros publicaban números retirados.** `README.md` daba «12 s sobre
  `e32c846`» y remitía a `RESULTS.md` por una procedencia que allí ya no existía;
  `docs/reading-order.md` daba «menos de un segundo en local y 12 s en CI»; y
  `LIMITS.md` 26 decía «10 tests» cuando son 15. Arreglados. Lo que revelan —que
  los números se copian a cuatro ficheros y derivan— es la **deuda abierta 5** de
  `ESTADO.md`, con su test, su hito (L5) y su precio.
- **La regla de oro 2 se acota a las estimaciones**, y al acotarla se endurece:
  ver [ADR-0015](docs/adr/0015-alcance-de-la-regla-del-intervalo.md).
