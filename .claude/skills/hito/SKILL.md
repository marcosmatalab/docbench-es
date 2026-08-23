---
name: hito
description: Arranca un hito del manual. Lee su criterio de aceptación, propone un plan de 10 líneas y ESPERA OK antes de picar.
argument-hint: "[L0|L1|L2|...]"
arguments: [hito]
allowed-tools: Read, Glob, Grep, Bash
disable-model-invocation: true
---

# Arrancar el hito $hito

## Estado actual del repo

!`cat ESTADO.md 2>/dev/null | head -40`

## El hito

Lee en `MANUAL.md` la fila de **$hito** en la sección de Hitos, y las secciones que
ese hito toca. Después:

1. Escribe **qué hay que construir**, en 5 líneas.
2. Escribe **el criterio de aceptación literal** copiado del manual, y **el comando
   concreto que lo comprueba**. Si el manual no da un comando, invéntalo y dilo.
3. Escribe el **plan, máximo 10 líneas**, una por fichero que vas a crear o tocar.
4. Di qué **tests** vas a escribir y **qué demuestra cada uno** (no qué prueba: qué
   demuestra).
5. Di qué **ADR** hay que escribir o actualizar, si aplica.

6. **Las suposiciones que este hito hace sobre los módulos que CONSUME.** Una por
   línea, con la comprobación que las verifica. Va en el plan, no en la revisión
   final.

   **Por qué es un paso y no una buena intención.** El hito que ESCRIBE un módulo
   no encuentra los bugs que encuentra el hito que lo CONSUME: escribe los tests
   que se le ocurren, que son los del código que acaba de escribir. Caso real:
   L1 cerró en verde y L2 descubrió que `from_html` no marcaba como cabecera un
   `<td>` dentro de `<thead>` —el **100%** de las cabeceras de PubTabNet mal
   marcadas—, y sólo apareció al construir el árbol de TEDS, que es el primer
   código que de verdad **necesitaba** `is_header`.

   La consecuencia operativa: cada hito que consume un módulo anterior escribe
   **qué da por supuesto** sobre él y **cómo lo comprueba**. Si la comprobación
   es «lo mismo que ya prueba su suite», no cuenta: su suite es justo la que no
   encontró el fallo.

**PARA AQUÍ.** No escribas código. Espera el OK del usuario.

Regla de tamaño: ningún fichero nuevo por encima de 300 líneas. Si un módulo se pasa,
pártelo y dilo en el plan.
