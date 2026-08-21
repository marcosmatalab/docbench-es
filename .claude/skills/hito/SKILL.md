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

**PARA AQUÍ.** No escribas código. Espera el OK del usuario.

Regla de tamaño: ningún fichero nuevo por encima de 300 líneas. Si un módulo se pasa,
pártelo y dilo en el plan.
