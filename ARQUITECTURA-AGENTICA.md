# Por qué esta arquitectura, cuando quien construye es Claude Code

Una arquitectura óptima para que la construya una persona **no es la misma** que una
óptima para que la construya un agente. Este documento explica las decisiones que solo
tienen sentido por eso, para `docbench-es`.

## Los siete principios, y qué problema del agente resuelve cada uno

| Principio | El problema del agente que resuelve |
|---|---|
| **Núcleo puro grande, bordes finos** | Un agente itera a la velocidad de su bucle de retroalimentación. Con `core/` sin red, sin disco y sin claves, ese bucle son **20 segundos**. Con red, son minutos y credenciales que fallan |
| **Contrato antes que implementación** | Un `Protocol` más su suite de conformidad convierte "implementa un extractor" en una tarea con **criterio objetivo**. El agente sabe cuándo ha terminado sin preguntarte |
| **Un fichero por concepto, por debajo de 150 o 300 líneas** | Los agentes editan peor conforme crece el fichero: más contexto, más riesgo de edición equivocada. Ocho extractores en ocho ficheros son ocho tareas limpias; en uno solo son un campo de minas |
| **Golden files antes que métrica** | El agente necesita un objetivo **numérico** contra el que iterar. "Coincide a 4 decimales con PubTabNet" es un objetivo. "Que TEDS esté bien" no lo es |
| **Property-based testing en los invariantes** | Un agente escribe casos límite pobres. `hypothesis` encuentra el solape de celdas que a nadie se le ocurre escribir a mano |
| **Contratos de import verificados en CI** | Un agente **erosiona la arquitectura sin darse cuenta**: mete un import para resolver un caso raro y nadie se entera en tres semanas. `lint-imports` lo caza el mismo día |
| **Entry points para todo lo enchufable** | Añadir un extractor pasa a ser "un fichero nuevo más una línea". Es la unidad de trabajo perfecta para un agente: pequeña, aislada y con criterio de terminado |

## Lo que es específico de ESTE repo

### El orden de los hitos está elegido para desbloquear paralelismo

L1 canonical → L2 TEDS con golden → **L5 los ocho extractores**.

Después de L2, cada extractor es una tarea **independiente y sin ambigüedad**: un
fichero, un entry point, y `docbench conform --extractor X` en verde. Puedes lanzarlos
en sesiones distintas, en cualquier orden, y ninguno depende de otro.

**Si hicieras los extractores antes que la forma canónica y que TEDS, cada uno sería
una negociación**: cómo devuelve las tablas, qué se considera correcto, cómo se
compara. Ocho negociaciones en vez de ocho tareas.

### `expresses_spans` lo fija el conversor, no el extractor

Es la decisión que más errores de agente evita en todo el repo. Si el extractor lo
declarara, un agente escribiendo el adaptador de Markdown pondría `True` sin pensarlo,
y la comparación entera se volvería injusta en el estrato que más pesa.

Al fijarlo el conversor según el **formato de origen**, es imposible mentir por
descuido.

### Los ficheros congelados están protegidos por un hook, no por una norma

Cuando un test falla contra un fichero de referencia, la salida más rápida es cambiar
el fichero. Un agente lo hace sin mala intención: "ajusto el valor esperado". El hook
`guard-frozen.sh` **lo bloquea con exit 2** y escribe el motivo **en stderr y en
`permissionDecisionReason`**, para que llegue por los dos caminos.

Dos matices que hacen que funcione en la práctica:

- **Congelado significa "que ya existe".** Crear el fichero la primera vez está
  permitido; si no, los hitos que traen los casos de referencia o escriben el plan de
  muestreo serían imposibles. Por eso esas rutas están en `ask` en `settings.json` y
  no en `deny`: las reglas `deny` ganan incluso a un hook y bloquearían la creación.
- **No es infalible.** El hook escucha en `Write`, `Edit` y `NotebookEdit`. Una
  redirección de shell (`>`) sí se comprueba contra las reglas de `Edit`, pero
  `uv run python -c "..."` puede escribir donde quiera. Está anotado abajo.

Sin ese hook, en algún momento de las 286 a 366 horas de construcción alguien mueve un golden
y el proyecto deja de medir lo que dice medir. Es la protección más barata del repo.

### La regla de "el juez no puede ser concursante" está en `CLAUDE.md` en negrita

Porque es la única regla del proyecto que un agente rompería **con buena intención**:
en algún momento verá que puede mejorar los resultados con un pequeño preprocesado
propio, y eso convertiría el banco en juez y parte. Está escrita arriba del todo y
repetida en la lista de "qué no hacer nunca".

## El bucle de trabajo

```
/estado           dónde estamos, en 4 líneas
/hito L<n>        plan de 10 líneas, PARA y espera OK
   (das OK)
   (pica, y el hook verify-edit revisa cada fichero al guardarlo)
/verificar        qué falla y dónde, sin arreglar
/adversarial      el subagente revisor busca fallos, sin elogiar
/cerrar L<n>      criterio + RESULTS + LIMITS + ADR + ESTADO + commit
```

Los cuatro hooks trabajan de fondo:

| Hook | Cuándo | Qué hace |
|---|---|---|
| `session-start` | Al abrir sesión | **Inyecta `ESTADO.md`.** Es el checkpoint que Claude Code no trae de serie |
| `verify-edit` | Tras cada Write, Edit o NotebookEdit | Pasa ruff y mypy con `uv run` **solo al fichero tocado**. Rápido y quirúrgico. Si no hay `uv` o no hay `.venv`, se calla en vez de inventar errores |
| `guard-frozen` | Antes de cada Write, Edit o NotebookEdit | Bloquea los ficheros de referencia y los planes congelados **que ya existen** |
| `stop-gate` | Al final de cada turno | Si `make fast` está en rojo, **bloquea el cierre** con `decision: block`. Lee `stop_hook_active` para no entrar en bucle, y cachea el último verde en `.claude/.ultima-puerta` para no pagar la puerta entera en cada respuesta |

## Lo que este montaje NO resuelve

- **No hay checkpoint nativo entre sesiones en Claude Code.** `ESTADO.md` más el hook
  lo suplen, pero **hay que actualizarlo**, y de eso se encarga `/cerrar`. Si cierras
  un hito a mano sin `/cerrar`, el checkpoint se queda viejo y la siguiente sesión
  empieza desorientada.
- **El hook `verify-edit` no ve el proyecto entero**, solo el fichero tocado. Un cambio
  que rompe otro módulo lo caza `make fast`, no el hook.
- **`Bash(uv run *)` está en `allow`, y eso es ejecución arbitraria.** `uv run python -c
  "..."` puede escribir donde quiera y esquivar `guard-frozen`. Es el precio de no
  confirmar cada comando; si prefieres el aislamiento, quita esa regla.
- **Los hooks necesitan `jq`.** `guard-frozen` falla **cerrado** si no lo encuentra
  —bloquea en vez de ceder—, y los otros tres se saltan sin hacer nada.
- **Nada de esto sustituye tu criterio.** El agente propone el plan; el OK lo das tú.
  Esa es la parte del bucle que no se automatiza, y es a propósito.
