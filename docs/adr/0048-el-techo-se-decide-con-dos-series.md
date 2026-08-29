# ADR-0048 · El techo se decide con DOS series de 40, y sólo está roto si los dos p90 lo pasan

**Fecha:** 2026-08-29 · **Estado:** aceptada. **No toca el manual**: §15 fija los 90 s de
`make fast` y eso no cambia; el techo es una alarma **por debajo** de esa promesa y su
protocolo vive en ADR-0022, que es lo que este ADR modifica.

**Modifica a [ADR-0022](0022-el-techo-de-la-puerta.md)** en un punto y sólo en uno: *cómo
se decide que el techo está roto*. **El estadístico no cambia** —sigue siendo el p90— y la
fórmula de re-justificación tampoco.

## Contexto

`RESULTS.md` publica desde el **24 ago 2026** dos series de 40 corridas medidas el mismo
día, bajo el título *«el protocolo reproduce a 10 ms»*. La sección demuestra lo que dice
y lo argumenta bien: **la MEDIANA de 40 reproduce a 10 ms**, seis a nueve veces menos que
la σ *dentro* de cada serie. En esa misma tabla, dos filas más abajo:

| | serie A | serie B | diferencia |
|---|---|---|---|
| mediana | 6198 | 6208 | **10** |
| p90 | 6262 | 6327 | **65** |

**Las dos series difirieron 10 ms en la mediana y 65 ms en el p90.** Los dos p90 llevaban
cuatro días publicados y **la resta no se hizo nunca**.

**Y el techo se compara contra el p90.** O sea que la única evidencia de reproducibilidad
que este proyecto tenía era sobre **el estadístico que no decide**.

Eso convierte en aire una frase publicada el 29 ago 2026: *«el p90 es 8231 contra un techo
de 8200, sigue sonando por 31 ms»*. **31 es menos de la mitad de 65.** No es que la alarma
no suene: es que **con este instrumento no se puede afirmar que suene**.

**Tiene causa mecánica, no sólo aritmética.** El p90 de n=40 se estima con unas **cuatro**
observaciones de la cola; la mediana usa las **cuarenta**. Un estimador de cola con cuatro
puntos se mueve más que uno central con cuarenta. **El proyecto eligió el estadístico
conceptualmente correcto y validó el estable.** Son dos, y sólo uno tenía aval.

**Qué NO es esto.** No es el [límite 116](../../LIMITS.md), que dice que el **término del
medio** de la fórmula —el incremento proyectado— no está medido. Esto va debajo: **el
primer término tampoco tiene medida de reproducibilidad en la forma en que se usa para
decidir.**

## Decisión

**1. El protocolo del cierre pasa a ser DOS series de 40**, no una:

```bash
uv run python scripts/medir_puerta.py; echo $?      # --series 2 por defecto
```

**2. El techo se considera ROTO sólo si TODOS los p90 lo pasan.** Tres direcciones y tres
códigos de salida, porque son tres cosas distintas:

| Cuántas series pasan del techo | Código | Qué significa |
|---|---|---|
| todas | **1** | roto. Se aplica ADR-0022: primero `--durations`, después las tres concesiones |
| algunas | **3** | **no concluyente**: el margen es más pequeño que el ruido del propio estimador. No se sube el techo **y no se declara roto** |
| ninguna | **0** | dentro |

El **3** es la aportación de este ADR. Un instrumento que devolviera el código del verde
cuando una serie pasa y la otra no estaría contestando con una moneda al aire una pregunta
que él mismo sabe que no ha resuelto.

**3. Se publica EL PAR, nunca una tasa.** La misma disciplina que ya está escrita en la
sección que destapó esto: *«con n=2 no se publica una tasa: se publica el par»*. No se
escribe «la reproducibilidad del p90 es 65 ms»; se escribe que **las dos únicas series
observadas difirieron 10 ms en la mediana y 65 ms en el p90**, y que el techo se compara
contra el primero de los dos.

**4. Lo hace cumplir código, no la buena memoria:** `scripts/serie_puerta.py` tiene la
regla de decisión separada del bucle de medir —`veredicto()`, probada en las tres
direcciones— y `scripts/regla_reproducibilidad.py` es **R10** de `derivadas.py`: las
restas publicadas se comprueban contra la tabla, y si nadie escribe ya la frase canónica
la regla dice **«0 copias vistas»** en vez de callarse.

**Y construye sola lo que hoy no existe.** Cada cierre deja **dos** p90 del mismo árbol el
mismo día. Con tres o cuatro hitos hay una serie de reproducibilidad del p90 medida, que
es el mismo dato que el límite 116 pide por otro camino: el día que exista, el término del
medio de la fórmula deja de ser un juicio.

## Alternativa descartada

**(a) Gatear sobre la mediana, que es el estadístico estable.** Es la salida cómoda y la
respuesta equivocada: **la mediana esconde la cola, que es justo lo que un techo existe
para vigilar.** Un p90 alto con mediana buena significa que hay corridas lentas, y ésa es
exactamente la señal que hay que ver. La respuesta a un estimador ruidoso es **más
evidencia sobre él**, no cambiar a otro que da menos ruido porque mira otra cosa.

**(b) Subir n a 80 en una sola serie.** Cuesta lo mismo —40 minutos— y **no mide lo que
falta**: da un p90 más apretado *dentro* de una serie, y lo que se ignora es la variación
**entre** series, que es la que incluye lo que cambia entre dos ejecuciones —cachés del
sistema, temperatura, lo que la máquina estuviera haciendo—. Dos series de 40 miden justo
eso; una de 80 lo promedia y lo esconde.

**(c) Dejarlo como está y decidir con una serie.** Es lo que se estaba haciendo, y produjo
una discusión de 31 ms sobre un instrumento con 65 ms de diferencia observada. Un techo
que se rompe o no según la serie que te toque **enseña a ignorar el color**, que es el
[límite 25](../../LIMITS.md) y el mismo argumento por el que el techo de CI no bajó.

## Trade-off

**Lo que se paga:** el cierre pasa de ~20 a ~40 minutos de reloj, y `medir_puerta.py`
deja de dar una respuesta en la mitad de tiempo cuando alguien sólo quiere diagnosticar
—para eso está `--series 1`, que lo dice en la salida: *«diagnostica, NO decide»*—.

**Lo que se compra:** que la decisión del techo deje de depender de qué serie te tocó, y
una serie de reproducibilidad del p90 que se construye sola, hito a hito, sin pagar nada
aparte por ella.
