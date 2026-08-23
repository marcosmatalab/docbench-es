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
proceso —`uv run pytest` cuesta ~900 ms antes de ejecutar nada—, no por los
ejemplos. Con 44 ms no se salva un techo al 97%.

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

**El supuesto que puede tumbar la proyección**, y va escrito para que se compruebe
en vez de creerse: que el reparto entre `fast` y `full` de L3 sea el que se supone
aquí. Si `entity.conformance` acaba siendo pura y grande, el incremento se parece
al escenario de arriba y el techo de 8500 se queda corto en el propio L3.

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
2. **El tiempo EN PROCESO de `pytest tests/unit` pasa de 10 s.** Hoy son 2,8 s de
   los ~3,8 s del paso: el resto es arranque. Mientras el arranque domine, el
   problema no son los tests y recortarlos no compra nada —es justo el error que
   se cometió al estimar la palanca de `max_examples` en 285 ms cuando valía 44—.
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
