---
name: cerrar
description: Cierra un hito. Verifica el criterio de aceptación, escruta de forma adversarial, actualiza ESTADO.md y RESULTS.md y prepara el commit.
argument-hint: "[L0|L1|L2|...]"
arguments: [hito]
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
disable-model-invocation: true
---

# Cerrar el hito $hito

## La puerta

!`make fast 2>&1 | tail -30`

## Diferencia acumulada

!`git diff --stat HEAD`

## Pasos, en este orden y sin saltarte ninguno

1. **Criterio de aceptación.** Copia el del manual y ejecuta el comando que lo
   comprueba. Pega la salida real. Si no pasa, **el hito no está cerrado**: dilo y para.

2. **Los dos mutantes.** *(Sustituye a «todo test se ve fallar contra el código
   roto», que no bastaba: hay DOS formas de estar roto y un test que sólo afirma
   `not ok` pasa en verde contra la que rechaza todo.)*

   Cada test de este hito se corre contra dos versiones rotas de la función que
   prueba, y **la suite tiene que caerse contra las dos**:

   - `siempre_ok` — la función devuelve el resultado bueno pase lo que pase
     (`(True, [])`, la identidad, lista vacía). Caza al test que no comprueba nada.
   - `siempre_roto` — la función rechaza o falla siempre (`(False, ["x"])`). Caza
     al test que sólo afirma la mitad negativa, que es el que **miente en la
     dirección tranquilizadora**: da un 100% de detección que en realidad es un
     100% de pesimismo.

   Están versionados en `scripts/mutantes/`. Dos órdenes, y las dos se pegan:

   ```bash
   uv run python scripts/mutantes/matar.py; echo $?          # todos mueren
   uv run python scripts/mutantes/matar.py --tabla           # QUÉ test mata a cuál
   ```

   **`matar.py` empieza por el CONTROL NEGATIVO**: la suite sin mutar tiene que
   dar **0 muertes**. Sin ese cero la tabla no vale nada, porque cada «muerte»
   podría ser un fallo de fondo de la suite y no el mutante.

   **`--tabla` publica dos agregaciones sobre 3 repeticiones**: los que matan
   SIEMPRE y los que matan ALGUNA VEZ. *Un asesino intermitente no es un
   asesino.* Y delata los **puntos únicos de fallo**: un mutante al que mata un
   solo test es una garantía sostenida por una sola aserción, y hay que añadirle
   un segundo asesino o declarar por qué no se puede.

   **SIEMPRE no es una categoría, es una estimación con n = 3** (límite 50): a
   p = 0,9 un test intermitente sale «SIEMPRE» el 73% de las veces. Cuando las dos
   columnas difieran y no se explique sola, se afina el caso antes de publicarlo:

   ```bash
   uv run python scripts/mutantes/matar.py --tabla --reps 10 --solo EL_MUTANTE
   ```

   **Publica el n al lado de la tabla, y publica también cuántos tests quedan
   FUERA del arnés.** «Los 21 mutantes mueren» habla de esos 21 huecos, no de la
   suite: hoy el arnés cubre 164 de 301 tests, o sea que los 137 tests que quedan
   fuera no están medidos por mutación.

   **Y publica las DOS contabilidades, no sólo ésa.** La cobertura del arnés mide
   el arnés; lo que importa es cuántos tests tienen **algo** que demuestre que se
   pondrían rojos —un mutante o un control negativo en su propio fichero—: hoy,
   **298 de 301 tests protegidos por algo** y **3 tests sin ningún control**.
   Publicar sólo la primera exagera el hueco; publicar sólo la segunda lo esconde.
   Las dos, con el criterio del límite 60 al lado.

   **Y si la cobertura del arnés ha bajado, di POR QUÉ en la misma frase.** Suele
   ser estructural y no deterioro: los módulos nuevos traen su control negativo en
   su propio fichero —la regla de barreras— y su mutante va a plazos. Un número que
   cae sin esa explicación al lado se lee como decadencia, y quien lo lea dentro de
   seis meses no estará en esta conversación.

   **Estos recuentos NO se copian a mano a ningún documento.** Los calcula
   `tests/unit/conftest.py` en cada colección y `tests/unit/test_recuentos.py`
   comprueba que todo documento publicado que los cite coincida — `.claude/`
   incluido, que es donde se quedó un «12» en el cierre de L2.

   **Y una vez por cierre, su control negativo A MANO**, porque el test sólo caza
   los fraseos previstos (límite 54):

   ```bash
   # cambia UNA cifra en cada documento y comprueba que las caza TODAS
   uv run pytest tests/unit -q -k recuentos    # tiene que fallar, con 4 líneas
   git checkout -- RESULTS.md LIMITS.md ESTADO.md .claude/
   ```

   En L2 la primera versión cazaba **2 de 4**. Si tu ronda caza menos que
   documentos has tocado, falta un patrón: añádelo antes de cerrar.

   **Y el censo de fraseos**, que mide el hueco en vez de suponerlo:

   ```bash
   uv run python scripts/cobertura_patrones.py --detalle   # 0 falsos positivos, 10 escapes
   ```

   Los **falsos positivos tienen que quedarse en cero**: uno solo pone rojo un
   documento que no miente, y un candado que da rojos falsos deja de leerse. Los
   escapes son el hueco declarado en el límite 54; si suben mucho, añade patrones
   —pero **estrechos**: ante la duda, se cambia la redacción del documento, no el
   patrón.

   **Y lo que ningún regex puede hacer por ti (límite 55): cuando el guardián te
   obligue a cambiar una cifra, RELEE LA FRASE ENTERA, no sólo el dígito.** El
   guardián sincroniza números, no afirmaciones. Cambió un 18 por un 21 y dejó al
   lado «añadieron seis»: 12 + 6 = 18, y el resultado —número correcto en una
   frase que se contradice sola— es **más difícil de ver leyendo** que el número
   viejo, porque la cifra da bien al comprobarla.

   Al releer, busca **sumas, restas, enumeraciones y «de N a M»** alrededor de la
   cifra que cambió. Y al escribir, **prefiere enumerar a sumar**: una lista de 21
   se ve incompleta de un vistazo; un «12 + 6» no.

   **Y LA REGLA DE QUÉ DEBE MUTANTE Y CUÁNDO**, que hasta L3 decía dos cosas a la
   vez:

   > **Un módulo cuyo único trabajo es PONERSE ROJO —una barrera— trae su control
   > negativo en el MISMO hito. El resto se cierra a plazos, con su precio.**

   Código de producción que está mal se delata en lo que produce. Una barrera que
   está mal **se delata con silencio**, que se lee igual que ir bien.

   La forma da igual —un mutante en `scripts/mutantes/` o un doble roto en el
   propio fichero de test—; lo que no es negociable es que exista en el hito que
   estrena la barrera. **Y publica la velocidad, no sólo el total**: qué fracción
   de la suite queda fuera del arnés este hito contra el anterior. Un hueco que se
   ensancha y un total grande se leen igual si sólo publicas el total — pasó en
   L3: de 12,4% a 19,7% sin que ninguna cifra publicada lo dijera.

3. **¿Sigue alcanzando la estrategia el sitio donde vive el bug NUEVO?** Un test
   de propiedad que sigue **en verde** después de cambiar la implementación **no
   es evidencia** hasta comprobarlo. Una estrategia codifica dónde creías que
   estaban los bugs **cuando la escribiste**, no dónde están ahora: si el código
   cambió de forma, puede haber dejado de tocar la zona que importa sin que nada
   se ponga rojo.

   Por cada test de propiedad que cubra código que este hito ha tocado: escribe
   qué familia de fallo puede aparecer AHORA, y comprueba con un mutante que la
   estrategia la alcanza. Si no la alcanza, la estrategia se amplía o se añade un
   censo exhaustivo al lado; lo que no vale es dar por bueno el verde.

   *Caso que lo motiva (L1).* La estrategia de `DocRef.key()` generaba los dos
   pares partiendo **la misma cadena** por dos sitios, así que un campo era
   siempre prefijo del otro. Cuando L1 cambió `urllib.parse.quote` por un
   escapado a mano, apareció una familia de fallo nueva —que el ESCAPADO no fuera
   inyectivo— y esa estrategia **no puede alcanzarla por construcción**. Medido:
   contra un escapado que sustituye `/` por `%2F` sin escapar antes el `%`, el
   fichero de L0 pasaba **7 de 7** mientras el censo nuevo fallaba 2.

4. **¿Están tus mutantes DE VERDAD rotos?** Un censo de mutación tiene que
   verificar que cada mutante produce de verdad una entrada inválida. Si no, el
   censo **exige falsos positivos**: pide detectar algo que es legal, y entonces
   el 100% de detección se consigue rechazando lo válido, que es el peor sitio al
   que puede llegar un validador.

   Comprueba cada familia de mutación contra una entrada donde de verdad rompa, y
   manda a un censo aparte —de control negativo— las mutaciones que resultan ser
   legales.

   *Caso que lo motiva (L1).* Crecer un `colspan` sobre una tabla con hueco de
   cola **rellena el hueco**: la tabla resultante es legal, es lo que se vería si
   la celda tuviera de verdad ese span. El censo la contaba como «tendría que
   detectarse», o sea le pedía a `validate` que rechazara HTML válido. Sólo
   apareció al meter las formas reales del BOE en el censo; con rejillas
   sintéticas completas no había huecos que rellenar.

5. **Escrutinio adversarial.** Ejecuta `/adversarial` y trae sus hallazgos aquí sin
   filtrar. Trátalos uno a uno delante del usuario: arreglado, descartado con razón
   escrita, o anotado en LIMITS.md. Un hallazgo sin tratar deja el hito abierto.

6. **La puerta, con el protocolo de ADR-0022.** Ejecuta y **pega la salida**:

   ```bash
   uv run python scripts/medir_puerta.py --techo <el del hito>; echo $?
   ```

   40 corridas en frío en 10 tandas, `.hypothesis` borrada, corridas con `rc != 0`
   descartadas. Devuelve 1 si el p90 pasa del techo. **Publica mediana, p90,
   máximo y desviación**, y fija el techo del hito siguiente con la proyección
   escrita.

   **Y el desglose por PASO, con el barrido de referencias como uno más.** La
   puerta son cinco pasos y cada uno lleva su número medido, igual que `pytest`,
   `mypy`, `ruff` y `lint-imports`:

   | Paso | Cómo se aísla |
   |---|---|
   | `ruff check` + `format --check` | corriéndolo solo, en frío |
   | `mypy --strict src tests` | idem |
   | `lint-imports` | idem |
   | `pytest tests/unit` | idem |
   | **el barrido de referencias** | `pytest tests/unit -k barreras` contra la misma corrida sin ese test |

   El barrido corre **dentro de la puerta** —lo ata `test_barreras.py`, y ha cazado
   dos referencias rotas reales— pero **su coste no está medido**, y una décima
   parte de la puerta sin medir es exactamente lo que este repo no publica.
   **En L5 se decide con esa cifra delante** si se queda en la puerta o pasa a ser
   un paso de este cierre. Hoy no se decide: hoy se mide. Si se cumple alguna de las tres condiciones de parada de ADR-0022, la
   respuesta ya no es subir el techo: es reestructurar, y eso va con su ADR.

7. **Números medidos.** Añade a `RESULTS.md` los números que este hito produce, con
   fecha, versión y **el comando exacto que los reproduce**. Un hito sin número medido
   no se cierra.

   **TODA CIFRA CUYO DENOMINADOR DEPENDA DEL TAMAÑO DE LA SUITE SE PUBLICA CON EL
   SELLO DEL ÁRBOL EN QUE SE MIDIÓ**, no sólo con la fecha.

   *El caso.* `RESULTS.md` publicó durante **todo L3** que un mutante se caía en
   «18 de 54 tests». Era cierto al medirlo y dejó de serlo en cuanto alguien añadió
   un test. **La fecha no lo delata**: un lector ve «23 ago» y no sabe si la suite
   ha crecido desde entonces. El commit sí — se compara con `git log` en un
   segundo. La regeneración en cada cierre las mantiene frescas; **el sello las
   hace honestas entre medias**, que es donde vive un hito entero.

   - **Lo imprime el instrumento, no tú.** `scripts/sello.py`, y ya lo sacan
     `matar.py` y `medir_puerta.py` en su primera línea. Un sello escrito a mano en
     el documento sería una copia más capaz de quedarse vieja: el mismo bug una
     capa por encima.
   - **El `+N` es parte del sello**, y son los ficheros sin commitear. Una medición
     sobre un árbol sucio **no se puede reproducir desde ningún commit**, y quien
     la lea tiene derecho a saberlo antes de compararla con la suya.
   - **Lo que NO lleva sello, y decirlo importa:** los recuentos que
     `tests/unit/conftest.py` recalcula en cada colección —tests totales, dentro,
     fuera, mutantes, reglas—. Ésos **no pueden quedarse viejos**, así que ponerles
     sello sugeriría que sí. En su lugar va el nombre del guardián. La pregunta
     para decidir es una: **¿hay algo que lo recalcule solo?** Si lo hay, guardián;
     si no lo hay, sello.

   **Si editas un documento publicado con un script, el ancla pasa por
   `scripts/ancla.py`.** Un encabezado como «### El coste en la puerta» se repite
   por hito: un `s.index` sobre él corta por el del hito viejo y **duplica** todo
   lo que hay en medio —pasó en L2, ~230 líneas—, y con cero apariciones **borra**
   sin que nadie lo note. `unica(texto, ancla)` aborta si no aparece exactamente
   una vez.

8. **El barrido de referencias.** Ejecuta y pega la salida:

   ```bash
   uv run python scripts/referencias.py --detalle; echo $?
   ```

   Comprueba **por ejecución** toda referencia a un fichero, módulo, comando u
   objetivo de `make` en los ficheros operativos. Devuelve 1 si queda alguna rota
   sin declarar — **o si sobra una declaración**, que es una afirmación vieja una
   capa más adentro.

   **Por qué es un paso del cierre y no una cosa que se mira cuando toca:** el
   mismo fallo —afirmar algo sobre código que no se está construyendo— ha
   aparecido **cinco veces**, y las cinco se encontraron tropezándose con ellas.
   Un hito que estrena módulos es exactamente cuando se crean referencias nuevas.

9. **Límites.** Si has descubierto algo que el proyecto NO mide o dónde se rompe,
   añádelo a `LIMITS.md` numerado.

   **LA FAMILIA QUE MÁS VECES SE HA COLADO AQUÍ, y ya van cuatro:**

   > **PUBLICAR COMO OBSERVADO ALGO QUE NO SE OBSERVÓ.**

   No son tres despistes distintos: es un mismo hueco, y el patrón es siempre el
   mismo — hay un número o un estado que *parece* venir de una medición, y la
   medición no se hizo.

   | Caso | Qué se publicó | Qué se había observado de verdad |
   |---|---|---|
   | **L1** | «bajar `max_examples` ahorra **285 ms**» | nada: era una regla de tres sobre el coste de un test. Medido, **44 ms** |
   | **L2** | la tabla de asesinos, con su columna «mata SIEMPRE» | un recuento que sumaba **una línea `FAILED` por parámetro**, no por test |
   | **L3** | «`make fast` rc=0» | **nada**: el `echo $?` iba dentro de un comando lanzado en segundo plano, así que ese código de salida no lo vio nadie. Estuvo rojo |
   | **L3** | «p90 6266 ms, 2234 de margen», de una serie de 40 corridas | **dos árboles**: un docstring cambió a mitad de la serie. Parte de las 40 midió un código y el resto otro, y **cuántas de cada no se sabe**. Serie descartada entera |

   **Que sea la cuarta es la señal: no es despiste, es que falta el guardia.** Y
   fíjate en que la tercera y la cuarta se parecen sólo por fuera: una era el
   segundo plano y la otra el primero. Lo que comparten es el árbol moviéndose
   debajo de una medición.

   **El guardia, concreto y barato:**

   - **NINGUNA MEDICIÓN CORRE MIENTRAS EL ÁRBOL SE MUEVE**, esté en primer plano
     o en segundo. Una serie que abarca dos estados del código **no mide ninguno
     de los dos**, y da igual que el cambio parezca inocuo: quien lo juzga
     inocuo es el mismo que quiere que el número salga bien. Se descarta entera.
     Editar mientras mides es la forma general; el segundo plano sólo es donde
     más fácil pasa, porque no hay nada delante recordándotelo.
   - **Y como caso particular de lo mismo: nunca se reporta el código de salida de
     un comando lanzado en segundo plano.** Si vas a afirmar `rc=0`, el comando
     corre en **primer plano** y lees su salida; o escribe su código a un fichero
     y el informe **lee el fichero**.
   - **Esto ya no depende de que alguien se acuerde:** `scripts/medir_puerta.py`
     compara `HEAD` + `git status --porcelain` antes de empezar y **después de
     cada corrida**, y si algo se movió aborta con **rc=2**, dice qué fichero fue
     y **no imprime ni un tiempo**. Comprobado moviendo el árbol a propósito a
     mitad de una serie corta. Que no imprima nada es parte del guardia: **mirar
     el p90 de una serie contaminada sesga la decisión siguiente** aunque después
     la descartes, porque el número ya está en la cabeza de quien decide.
   - Antes de escribir una cifra, la pregunta es **«¿qué comando la imprimió?»**.
     Si la respuesta es una multiplicación, no es una medición: márcala como
     proyección, con sus dos etapas declaradas.
   - Y si un recuento sale de parsear una salida, **comprueba la unidad**: tests
     contra líneas, documentos contra tablas, celdas contra etiquetas. Los tres
     errores grandes de este repo han sido de unidad o de origen, ninguno de
     aritmética.

   **SU HERMANA, Y ES LA MÁS FINA DE TODAS:**

   > **COMPROBAR EN UN ENTORNO QUE NO ES EL QUE VA A LEER EL RESULTADO.**

   La familia de arriba publica como observado lo que no se observó. Ésta observa
   de verdad — **pero en el sitio equivocado**, y por eso es más difícil de ver: hay
   una medición, hay un verde, y el verde es real. Lo que no es real es que
   signifique lo que se cree.

   *El caso, del cierre de L3 y en el peor momento posible.* `scripts/referencias.py`
   comprobaba cada ruta con `Path.exists()`, o sea **contra el árbol de trabajo de
   quien lo corre**. Tres referencias —`.claude/.ultima-puerta`,
   `.claude/.congelados.sha256` y `runs/l3/docs`— existían en mi máquina porque las
   crean los hooks al correr y porque el corpus está ignorado. En un clon no
   existen. **La puerta estaba verde en local y roja en CI y en cualquier clon**, y
   se empujó así.

   **Lo que hace este caso instructivo es que la barrera TENÍA su control negativo,
   y era bueno.** Probaba las dos direcciones: que dice «no» ante una referencia
   rota y «sí» ante una que existe. Los dos pasaban. Lo que ninguno de los dos
   probaba es **de qué depende esa respuesta**:

   | | Qué prueba | Qué NO prueba |
   |---|---|---|
   | control negativo de veredicto | que la lógica distingue bien | que mide lo que dice medir |
   | control negativo de **entorno** | que el resultado no cambia según quién lo corra | — |

   **Un candado puede tener la lógica perfecta y aun así estar midiendo la máquina
   de quien lo escribió.** Y entonces su verde es una propiedad de esa máquina.

   **Las preguntas, antes de cerrar:**

   - **¿Contra qué compara esta comprobación?** Si la respuesta es «el disco», «el
     entorno», «lo que hay instalado» o «el directorio actual», entonces mide la
     máquina. Lo que hay que comparar es **lo que recibe quien va a leer el
     resultado**: para un repo, `git ls-files`; para un paquete, lo que instala;
     para un despliegue, lo que se copia.
   - **¿Existe algo que esté en local y no en el artefacto?** Cachés, huellas,
     ficheros que crean los hooks, datos ignorados, `.venv`, salidas de corridas
     anteriores. Cada uno es una forma de que el verde sea tuyo y de nadie más.
   - **Y el control negativo que lo prueba** no es «¿dice no ante algo malo?» sino
     **«¿dice no ante algo que existe aquí y no allí?»**. En `referencias.py` eso se
     hizo inyectando el conjunto de lo versionado, para que el test no dependa de
     qué haya en el disco de nadie.

   **La comprobación barata que lo cierra todo: CLÓNATE EN `/tmp` Y CORRE LA PUERTA
   AHÍ**, antes de decir que está verde. No `git status` limpio: un clon de verdad.
   Un `git clone . /tmp/x && cd /tmp/x && uv sync --only-group dev && make fast`
   cuesta un minuto y es el único sitio donde la respuesta significa lo que parece.

   **Y mira CI antes de cantar victoria.** El badge de `82a55f9` estaba en rojo
   mientras se escribía el informe de cierre. Si el badge hubiera estado **verde**
   con el clon rojo, el problema habría sido mucho mayor que este bug — y ésa es la
   primera pregunta que hay que hacerse, antes de arreglar nada.

   **Y la forma más fuerte de un guardia: METERLO EN UN TIPO.**

   Una regla escrita en esta skill la cumple quien la lee y se acuerda. Un tipo no
   se puede olvidar, porque no hace falta acordarse de él.

   *Caso de L3.* `InformeConformidad` tiene **tres** severidades y no dos —`FALLA`,
   `AVISO` y **`NO_EJECUTADA`**— y su `pasa` exige **cero `FALLA` y cero
   `NO_EJECUTADA`**. Si `discover` no trae ningún documento, la suite no dice
   «cumple»: dice que **no lo ha mirado**, y el informe no pasa. La regla de
   proceso —*«no publiques como observado lo que no observaste»*— dejó de
   depender de que alguien la recordara en el momento en que se convirtió en un
   valor del enum que el `if` tiene que tratar.

   **Cuando un guardia quepa en el tipo de retorno, en un `Protocol`, en un código
   de salida o en un `assert` de la puerta, ahí es donde va.** La skill se queda
   con lo que no cabe en ningún sitio ejecutable.

   **La regla que decide qué es deuda y qué no, y no admite matices:**

   > **Una AFIRMACIÓN FALSA nunca es deuda: se arregla en el momento en que se
   > detecta.** La **COBERTURA que falta** sí es deuda: se declara con su **tamaño
   > medido** y se cierra a plazos.

   **Por qué la línea cae ahí:** el documento que declararía la deuda es el mismo
   que estaría mintiendo. «Ya lo apunto y lo arreglo en L3» convierte `LIMITS.md`
   —el fichero cuyo trabajo es decir la verdad sobre lo que el repo no hace— en
   otro sitio donde vive una falsedad. Una cobertura que falta, en cambio, es
   verdad desde el momento en que se escribe: *«esto no lo vigila nadie, son 7 de
   18, costaría ~1 h 10 min, y no prometo hacerlo»* es una frase cierta y
   comprobable.

   Ejemplos de este mismo hito, uno de cada:

   | | Qué se hizo |
   |---|---|
   | Un docstring afirmaba que la adyacencia cerraba el riesgo del nombre propio, y era falso | **Borrado en el acto**, y sustituido por lo que la adyacencia sí hace y lo que no |
   | El guardián no vigila 7 de 18 fraseos naturales | **Deuda 9 de `ESTADO.md`**, con su cifra, su precio y sin promesa |

   **Y una deuda con tamaño medido vale más que una promesa**: se puede priorizar
   contra otras, y no caduca en silencio.

10. **ADR.** Si has tomado una decisión de diseño no prevista, escríbela en
   `docs/adr/` con su alternativa descartada y su trade-off.

11. **ESTADO.md.** Marca $hito como CERRADO con su fecha y su número. Marca el
   siguiente como PENDIENTE. No inventes hitos que no estén en el manual.

12. **Commit.** Prepara el mensaje: qué cierra, **el número medido en el asunto** si lo
   hay, y los ficheros. No hagas push.

Ejemplo de asunto bueno: `L2: TEDS validado contra PubTabNet, coincidencia a 4 decimales`
Ejemplo de asunto malo: `refactor y mejoras`
