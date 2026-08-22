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
