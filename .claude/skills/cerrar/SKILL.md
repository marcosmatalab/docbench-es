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

   Se montan como plugins de pytest que parchean el símbolo en el módulo que lo
   consume, y se corren con `PYTHONPATH=<scratchpad> uv run pytest ... -p <mutante>`.
   **Pega los dos recuentos** (`N failed, M passed`) en el cierre. Un mutante que
   no mata a nadie es un hueco en la suite, no un mutante mal escrito.

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

6. **Números medidos.** Añade a `RESULTS.md` los números que este hito produce, con
   fecha, versión y **el comando exacto que los reproduce**. Un hito sin número medido
   no se cierra.

7. **Límites.** Si has descubierto algo que el proyecto NO mide o dónde se rompe,
   añádelo a `LIMITS.md` numerado.

8. **ADR.** Si has tomado una decisión de diseño no prevista, escríbela en
   `docs/adr/` con su alternativa descartada y su trade-off.

9. **ESTADO.md.** Marca $hito como CERRADO con su fecha y su número. Marca el
   siguiente como PENDIENTE. No inventes hitos que no estén en el manual.

10. **Commit.** Prepara el mensaje: qué cierra, **el número medido en el asunto** si lo
   hay, y los ficheros. No hagas push.

Ejemplo de asunto bueno: `L2: TEDS validado contra PubTabNet, coincidencia a 4 decimales`
Ejemplo de asunto malo: `refactor y mejoras`
