# ADR-0015 · La regla del intervalo se acota a las estimaciones

**Fecha:** 2026-08-22  ·  **Estado:** aceptada

## Contexto

La regla de oro 2 de `CLAUDE.md` decía, sin alcance ni excepción:

> **Todo número publicado lleva su intervalo y su comando de reproducción.** Un
> número sin intervalo no se publica. Un número que no se puede reproducir no
> existe.

Es media identidad del proyecto: `docbench-es` vende rigor, y esa frase es la que
lo hace verificable.

Al cerrar L0, `RESULTS.md` publicó su primer número: **4,43 s**, el tiempo de la
puerta en el runner de GitHub. Y la regla se rompió al primer intento, porque a un
tiempo no se le puede dar un intervalo de confianza:

- Un IC estima un parámetro de una **población** a partir de una **muestra**. En
  este proyecto esa población son documentos, y por eso la regla de oro 3 dice que
  el bootstrap remuestrea documentos. Es lo que hace que una exactitud del 84% con
  IC [81, 87] signifique algo.
- Un tiempo de puerta no tiene población. Hay una máquina que tarda lo que tarda.
  Calcular un «IC del 95%» sobre tres corridas de CI no sería rigor: sería
  inventarse una estadística, que es el mismo pecado por la otra cara.

Durante unas horas el repo estuvo en el peor estado posible: `CLAUDE.md` afirmando
que todo número lleva intervalo, y `RESULTS.md` publicando uno que no lo lleva. Un
fichero afirmando algo que el resto del repo no cumple es, según el propio
`CLAUDE.md`, el fallo más grave que puede haber aquí.

Y había un segundo defecto, más silencioso: la regla, tal como estaba, **no pedía
nada** a los números que no son estimaciones. El límite 26 de `LIMITS.md` publicaba
«10 tests unitarios» —eran 15— sin método, sin fecha y sin nada que lo desmintiera.
Un recuento desnudo pasaba el filtro porque la regla sólo hablaba de intervalos.

## Decisión

La regla de oro 2 se **acota**, y al acotarla se **endurece**:

> 2. **Todo número publicado lleva su comando de reproducción, y toda ESTIMACIÓN
>    lleva su intervalo.** Un número que no se puede reproducir no existe. Una
>    estimación sin intervalo no se publica: exactitud, TEDS, kappa, coste por
>    éxito, aporte del glosario. Un número que NO es una estimación —un tiempo, un
>    recuento, una tasa de descarte sobre el censo completo— no lleva intervalo,
>    pero lleva su método y su incertidumbre declarada: n, rango y resolución del
>    instrumento. Una cifra desnuda no se admite en ninguno de los dos casos.

La línea divisoria **no** es entre números importantes y accesorios: es entre
**estimaciones** y **medidas directas**. Una estimación infiere un parámetro que no
se ha observado entero; una medida directa observa lo que hay.

Consecuencia inmediata en `RESULTS.md`: el tiempo de la puerta se publica con
**rango observado** (mínimo, mediana, máximo, n y fecha de corte), **resolución
del instrumento** (~0,1 s para el paso, 1 s para el job y el run) e
**incertidumbre derivada**, y con su método en `docs/metrics.md`. No con un IC.

## Alternativa descartada

**A · Ablandarla a «en general».** Escribir «todo número publicado lleva su
intervalo, en general» o «salvo excepciones justificadas». Descartada: una regla
que dice «en general» deja de gobernar. Es exactamente la redacción que permite que
el próximo número incómodo se publique desnudo alegando que es una excepción, y
nadie tiene que argumentar cuál. La regla dejaría de ser código y pasaría a ser una
aspiración.

**B · Dejarla intacta y que `RESULTS.md` la incumpla.** Mantener la redacción
absoluta, publicar el tiempo sin intervalo y confiar en que se entiende. Descartada
por lo mismo que hace grave el problema: el repo estaría afirmando en su fichero de
gobierno algo que su fichero de resultados no cumple. Y es la peor de las dos, no
la más conservadora: una regla que se incumple visiblemente enseña que las reglas de
este repo son decorativas, y con eso se va el valor de todas las demás.

**C · Un fichero aparte para los tiempos**, fuera del alcance de la regla.
Descartada: mueve el problema sin resolverlo, y multiplica los sitios donde un
número puede vivir sin método. El reparto que sí se hace es otro —`RESULTS.md` los
números, `docs/metrics.md` el método— y ninguno de los dos queda fuera de la regla.

## Trade-off

Lo que se gana: la regla vuelve a ser cumplible **y** pide más que antes. Un
recuento de tests, una tasa de descarte o un tamaño de corpus ya no pueden
publicarse desnudos; tienen que traer n, rango y resolución aunque no lleven
intervalo.

Lo que cuesta: **hay que clasificar cada número** al publicarlo, y la frontera no
siempre es obvia. Una tasa de descarte sobre el censo completo es una medida
directa; la misma tasa estimada sobre una muestra del censo es una estimación y
lleva IC. La regla obliga a decir cuál de las dos es, que es precisamente el trabajo
que evita publicar de más.

## Cómo se verifica

Hoy, leyendo: `RESULTS.md` publica tres tiempos y los tres llevan rango, n y
resolución; ninguno lleva IC. `docs/metrics.md` deriva la incertidumbre de cada uno.

**No hay test que lo haga cumplir, y eso es deuda declarada.** Los números viajan a
`README.md`, `ESTADO.md`, `LIMITS.md` y `docs/reading-order.md`, y al cerrar L0 tres
de ellos publicaban cifras retiradas —el README, la puerta de entrada del repo,
seguía dando «12 s sobre `e32c846`»— y se cazaron leyendo, no con una prueba. En L5,
con exactitud por extractor y por estrato, serán decenas y leer no bastará. El test
que lo cierra está en la deuda abierta de `ESTADO.md`, con su hito y su precio.

## Consecuencias

- **Publicar un número obliga a clasificarlo.** Si es estimación, IC. Si no,
  método e incertidumbre. No hay tercera casilla.
- **`RESULTS.md` no lleva método.** Se parte en dos: los números aquí, el método en
  `docs/metrics.md`. Al cerrar L0, `RESULTS.md` había llegado a 228 líneas de las
  cuales la mayoría eran metodología de un solo tiempo; en L5 eso habría enterrado
  los números de verdad.
- **La regla de oro 3 no cambia.** El bootstrap sigue remuestreando documentos.
  Este ADR no toca cómo se calcula un intervalo, sólo a qué números se les exige.
- **El límite 29 de `LIMITS.md` sigue abierto.** Que `StructureMetrics` tenga un
  solo campo `ci` para cuatro estimadores es un defecto del modelo de datos, no de
  esta regla, y se cierra en L5.
