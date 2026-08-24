# ADR-0022 · El techo de la puerta: qué es, cómo se re-justifica y qué pasa al romperse

**Fecha:** 2026-08-23 · **Estado:** aceptada e implementada. **No toca el manual**:
§15 fija el presupuesto en 90 s y eso no cambia. Esto añade una alarma **por
debajo** de esa promesa

## Contexto

La puerta ha crecido así, con el mismo método y la misma máquina:

| Hito | Mediana | Tests |
|---|---|---|
| L0 | 1742 ms | 15 |
| L1 | 3829 ms | 82 |
| L2 | **5517 ms** | 133 |

De L1 a L2, **+1688 ms en un hito**. Al cerrar L2 el techo local era 6000 y la
mediana lo consumía al 92%, así que había que decidir el techo con datos y no con
la sensación de que aún cabía.

**Dos tandas no caracterizan una distribución**, y eso se vio: la segunda tanda de
L2 tuvo un máximo (5616) fuera del rango de la primera (≤5497). Así que se
midieron **40 corridas en frío, en 10 tandas de 4**, con `make clean` —que borra
`.hypothesis`— antes de cada una:

| | ms |
|---|---|
| mínimo | 5382 |
| mediana | **5517** |
| p90 | **5801** |
| p95 | 5816 |
| máximo | 5858 |
| desviación típica | 134 (coef. variación 2,4%) |
| medianas por tanda | 5459 – 5691 (232 ms de dispersión entre tandas) |

**El p90 consume el 97% del techo de 6000.** El margen en el p90 son 199 ms, o sea
1,5 desviaciones típicas. Eso no es margen: es estar dentro por suerte.

### La palanca que se creía tener no existe

`RESULTS.md` y `docs/metrics.md` publicaban que bajar la suite de normalización de
100 a 50 ejemplos ahorraba **~285 ms**. **Es falso, y estaba publicado como
medido.** Salió de suponer que el coste de un test escala con `max_examples`
partiendo de que `test_r1` cuesta 570 ms. Medido de verdad, media de 5 corridas en
frío por presupuesto:

| `max_examples` | Coste de la suite |
|---|---|
| 100 | 990 ms |
| 50 | **946 ms** |
| 25 | 935 ms |

**La palanca vale 44 ms, no 285.** La suite está dominada por el arranque del
proceso, no por los ejemplos.

> **CORRECCIÓN, 23 ago 2026, al preparar L3.** Aquí ponía que `uv run pytest`
> cuesta **~900 ms** antes de ejecutar nada y que el arranque **domina**. Medido
> —mediana de 3 en frío, `pytest tests/unit -q -k <nombre inexistente>` contra la
> suite entera—: **arranque + colección 273 ms (8%)**, **tests 3229 ms (92%)**.
> `uv run python -c pass` son 44 ms. **La afirmación estaba invertida.**
>
> **Qué NO cambia:** la decisión de este ADR. La palanca de `max_examples` sigue
> valiendo **44 ms medidos**, y con eso no se salva un techo — el argumento de
> descartar la opción (b) se sostiene solo, sin necesidad de que el arranque
> domine. El techo sigue en 8500/20 000.
>
> **Qué SÍ cambia:** que «recortar tests no compra nada» es falso. Con los tests al
> 92%, recortarlos **es** la palanca — sólo que sigue sin hacer falta usarla, y
> cuando haga falta, la condición de parada 2 de más abajo es la que manda. Con 44 ms no se salva un techo al 97%.

### Y bajar ejemplos tampoco sale gratis en cobertura

Se midió, en vez de suponerlo, cuánto explora cada presupuesto: 15 corridas en
frío por presupuesto contra el mutante `n3_incompleta`, que devuelve N3 a
`Cc ∪ Zs` y reintroduce la regresión de U+2028.

| `max_examples` | La PROPIEDAD caza la regresión | Wilson 95% |
|---|---|---|
| 100 | 0 de 15 | [0,000 – 0,204] |
| 50 | 2 de 15 | [0,037 – 0,379] |

**Los intervalos van porque son estimaciones** (regla de oro 2): son 15 sorteos,
no un censo. Y hacen falta para la conclusión: **se solapan casi enteros**, así
que 0 contra 2 no es «el presupuesto bajo caza más», es la misma tasa vista dos
veces. Sin el intervalo, la misma tabla sostiene la conclusión contraria.

Los dos son ruido alrededor de una tasa muy baja: **la propiedad no es un candado
a ningún presupuesto**, y quien caza esa regresión siempre es el test determinista
que recorre los 1,1 millones de codepoints. La lección no es «da igual el
presupuesto»: es que **el presupuesto de ejemplos no es la palanca de tiempo que
parecía, y recortarlo tampoco compra seguridad**.

## Decisión

**(a) Se sube el techo, y se le da una regla de re-justificación.** La opción (b)
—gastar la palanca y mantener 6000— **queda descartada por medición**: 44 ms no
mueven un p90 de 5801.

### Qué es cada número

| | Valor | Quién lo fija | Qué hace al romperse |
|---|---|---|---|
| **Presupuesto del manual** | 90 s en el runner (§15) | El manual | **BLOQUEA.** Es una promesa publicada |
| **Techo de crecimiento, CI** | **20 000 ms** | Este ADR, re-justificado en cada `/cerrar` | **AVISA** (`::warning::`), no bloquea |
| **Techo de crecimiento, local** | **8 500 ms** para L3 | Idem | Es de lectura humana: se comprueba al medir en `/cerrar` |

**Por qué el techo AVISA y no BLOQUEA.** Un runner lento pondría la puerta roja
por el motivo equivocado, y una puerta que se pone roja por motivos equivocados
enseña a ignorar el color —que es exactamente el argumento del límite 25 para que
`full` y `nightly` nacieran dormidos en vez de rojos—. Bloquear se reserva para la
promesa publicada. El aviso, en cambio, aparece en cada PR y obliga a tratarlo en
el siguiente cierre.

### Cómo se re-justifica

Al cerrar cada hito: se miden **40 corridas en frío en 10 tandas**, se publica
mediana, p90, máximo y desviación, y se fija el techo del hito siguiente como

    techo = p90 medido + incremento proyectado + una desviación típica

El techo **nunca se sube después de romperlo para que deje de avisar**. Se sube
antes, con la proyección escrita, o no se sube.

### La proyección de L3, y su supuesto declarado

L1 → L2 fueron **+1688 ms** de mediana. L3 es `entity.base` + conformidad +
`entity.boe` + `boe_xml` + `corpus`, y §16 le da 16-20 h contra las 10-14 de L2.

| Escenario | Supuesto | Mediana L3 proyectada |
|---|---|---|
| Analogía directa | L3 añade lo mismo que L2 | 5517 + 1688 = **7205** |
| Escalado por horas | ×1,5 (18 h contra 12) | 5517 + 2532 = **8049** |
| Corregido a la baja | **La mitad de L3 no entra en `fast`**: `entity.boe` y `boe_xml` necesitan red y sus tests van a `contract`/`e2e` | **~6400 – 7200** |

**Respuesta directa a la pregunta: 6000 NO aguanta L3 en ningún escenario.** El
más optimista ya se lo come.

### El techo, aplicando la fórmula de arriba en vez de redondeando a ojo

    techo = p90 medido (5801) + incremento proyectado + una desviación (134)

| Escenario | Incremento | Techo que da la fórmula |
|---|---|---|
| Analogía directa | 1688 | 7623 |
| Corregido a la baja | ~1700 | 7635 |
| **Escalado por horas** | **2532** | **8467** |

**El techo local es 8500**, que es el escenario más adverso redondeado **hacia
arriba**.

> **Corrección.** La primera versión de este ADR fijaba **8000** y lo llamaba «el
> escenario malo más una desviación». **La fórmula no da 8000 en ningún
> escenario** —da 7623, 7635 u 8467— y el escenario malo proyecta una *mediana*
> de 8049 para L3, o sea que 8000 habría quedado por debajo de la **mediana**
> proyectada, no ya del p90. Era un número redondo vestido de fórmula. Un techo
> se redondea **hacia arriba** o deja de ser un techo, que es el mismo argumento
> por el que este ADR prohíbe subirlo después de romperlo.

El de CI pasa a **20 000**, que son esos 8500 escalados por el ×2,3 medido en L0
entre local y runner (19 550), redondeado.

### Qué es exactamente el «p90» de estas mediciones

`scripts/medir_puerta.py` usa `ordenadas[int(0,90·n)]`, que con n = 40 es el
**37.º valor de 40**: el percentil empírico **92,5**, un rango por encima del p90
por rango más próximo (el 36.º). **Se declara y se deja como está**, por dos
razones: es **conservador** —nunca subestima el techo— y cambiarlo ahora haría
incomparables L0, L1 y L2, que es justo lo que este protocolo existe para evitar.
Lo que no vale es llamarlo p90 sin decir cuál de las convenciones es.

### EL TECHO ES SOBRE EL p90, NO SOBRE EL MÁXIMO

**Y eso significa que por construcción habrá corridas individuales por encima del
techo.** No es un fallo del protocolo: es lo que hace un percentil. `medir_puerta.py`
devuelve 1 si **el p90** pasa del techo, y no mira el máximo.

**El caso medido, para que no haya que imaginárselo.** Al preparar L4, con el techo
en 8500:

| | |
|---|---|
| n | 40 en 10 tandas, cero descartadas |
| mediana | 7628 |
| **p90** | **7787** — dentro |
| **máximo** | **8621** — **por encima del techo** |
| σ | 195 · carga mediana 1,27 |

`rc = 0`. Correcto: una corrida suelta a 8621 con σ=195 es la cola de una
distribución ruidosa, no un cambio en el código. **Fijar el techo sobre el máximo
haría que el rojo dependiera de si alguien abrió el navegador durante la tanda**,
que es exactamente el ruido que este protocolo existe para separar de la señal.

**Pero «el techo son 8500» se lee como «ninguna corrida pasa de 8500», y es falso.**
De ahí la regla de publicación: **el máximo se publica SIEMPRE al lado del p90**, que
es lo único que hace visible la diferencia entre las dos lecturas. Un p90 con su
máximo al lado no se puede malinterpretar; un p90 solo, sí.

**El supuesto que puede tumbar la proyección**, y va escrito para que se compruebe
en vez de creerse: que el reparto entre `fast` y `full` de L3 sea el que se supone
aquí. Si `entity.conformance` acaba siendo pura y grande, el incremento se parece
al escenario de arriba y el techo de 8500 se queda corto en el propio L3.

### El techo de L4: 9000 local, 21 000 en CI

Aplicada la misma fórmula al cerrar L3 y con el protocolo de las 40 corridas:

    techo = p90 medido (7787) + incremento proyectado + una desviación (195)

L2 → L3 fueron **+1807 ms** de mediana (5593 → 7400), con **+123 tests** y **+13
módulos** en 18-23 h. L4 son 8-10 h. Tres analogías sobre ese único delta:

| Escenario | Cuenta | Incremento | Techo que da la fórmula |
|---|---|---|---|
| Por pasos | `mypy` x5/13 + `pytest` x45/123 | 644 | 8626 |
| Por tests | 14,7 ms/test x ~45 | 660 | 8642 |
| **Por horas, el adverso** | 1807/20,5 h x 9 h | **790** | **8772** |

**El techo local es 9000**, el adverso redondeado hacia arriba. El de CI, **21 000**
(9000 x 2,3 = 20 700, redondeado). **Es una proyección sobre UN delta**, no sobre una
tendencia, y se publica con esa palabra.

**Lo que este número ya anticipa:** el margen que quedaba bajo 8500 eran 713 ms y el
escalón proyectado de L4 son 640-790, o sea que **se lo come entero**. Y la condición
que disparará primero no es el techo sino la **número 2**: `pytest` en proceso ha
pasado de 3,2 s a **4,52 s** (n=3, medido al cerrar L3), y a ese ritmo llega a los
10 s hacia L8.

### Cuándo se deja de subir el techo, que es la parte que faltaba

Subir el techo cada hito es honesto y **no tiene final**. 6000 no aguantaba L3;
8500 aguanta L3 y, por esta misma proyección, **no aguanta L5** —que trae ocho
extractores y el nivel 1 entero—. Así que la regla necesita un punto donde la
respuesta deja de ser «sube el techo».

**Se deja de subir y se REESTRUCTURA cuando se cumpla cualquiera de estas tres,
medidas en el cierre:**

1. **La mediana en el runner pasa de 30 000 ms**, o sea un tercio del presupuesto
   de §15. Con el ×2,3 medido en L0 entre local y runner, eso son ~13 000 ms
   locales. Es el número de parada.
2. **El tiempo EN PROCESO de `pytest tests/unit` pasa de 10 s.** Hoy son 3,2 s de
   los 3,5 s del paso: el arranque son **273 ms, el 8%**. Ésta es la condición que
   manda, y por eso está escrita sobre el tiempo en proceso y no sobre el total:
   es la que separa «la suite hace más trabajo» de «la máquina va lenta».
3. **Dos hitos seguidos con incremento mayor de 2 000 ms.** L1→L2 fue +1688. Dos
   seguidos por encima de 2 000 significa que la pendiente cambió y que la
   proyección lineal ya no sirve.

**Qué significa reestructurar**, en este orden y con su coste declarado:

| | Medida | Qué cuesta |
|---|---|---|
| 1º | **Paralelizar `pytest`** con `-n auto` (`pytest-xdist`) | Una dependencia de desarrollo y perder el orden determinista de la salida |
| 2º | **Mover suites lentas a `full`** con su límite declarado en `LIMITS.md` | Que dejan de correr en cada PR: es exactamente lo que el límite 25 llama enseñar a ignorar el rojo, así que va con su fecha de vuelta |
| 3º | **Partir la suite por capas** y correr en la puerta sólo el núcleo puro | Que la puerta deja de cubrir lo que hoy cubre, y hay que decir qué deja de cubrir |

### Qué es mecánico y qué no, dicho sin adornos

**El protocolo de 40 corridas NO es mecánico.** Es un paso de `/cerrar`, que es
una lista en markdown: una persona puede saltárselo, y si se lo salta no pasa
nada. Se ha hecho lo que se podía hacer sin inventar una obligación falsa:

- **`scripts/medir_puerta.py`** convierte el protocolo en **una orden con código
  de salida**: 10 tandas de 4, borra `.hypothesis`, descarta las corridas con
  `rc != 0` y **devuelve 1 si el p90 pasa del techo**. Ya no depende de que cada
  uno recuerde el mismo procedimiento.
- **`/cerrar` exige pegar su salida**, no describirla.
- **Lo único con fuerza real es el aviso de CI**, que sale en cada PR sin que
  nadie decida ejecutarlo. Por eso el techo vive ahí y no sólo en este documento.

Que el ritual sea manual y el aviso automático es una asimetría consciente: el
aviso dice *«esto ha crecido»* en cada PR, y el ritual sirve para decidir qué
hacer al respecto, que es una decisión humana con un ADR detrás.

## Alternativa descartada

**(b) Gastar la palanca de `max_examples` y mantener 6000.** Descartada **con el
número delante**: la palanca vale 44 ms medidos y el p90 está a 199 ms del techo.
Mantener 6000 con eso sería declarar un techo que se rompe solo, y además gastaría
la única palanca que queda por 0,8% de tiempo.

**Bloquear en el techo, no avisar.** Descartada porque el tiempo depende de la
máquina y el techo es una alarma de *crecimiento*, no una promesa. Lo que sí
bloquea es el 90 s del manual, que sí es promesa.

**Cronometrar dentro de `make fast`.** Descartada: la puerta se ejecuta en
portátiles de distinta velocidad y el Makefile es la definición única de qué
comprueba la puerta, no de cuánto puede tardar en la máquina de cada uno.

## Trade-off

Lo que se paga: **el techo deja de ser una barrera y pasa a ser un aviso**, y un
aviso se puede ignorar. Se mitiga atándolo al ciclo: `/cerrar` mide y
re-justifica, así que ignorarlo cuesta explicarlo por escrito en el cierre.

Lo que se compra: que la alarma sea proporcional. Hoy hay **16×** de margen contra
la promesa real de 90 s; gastar el presupuesto de atención en defender un 6000
inventado, cuando la palanca para respetarlo vale 44 ms, era optimizar el número
equivocado.
