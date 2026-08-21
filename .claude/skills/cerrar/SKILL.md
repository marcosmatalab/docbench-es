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

2. **Escrutinio adversarial.** Ejecuta `/adversarial` y trae sus hallazgos aquí sin
   filtrar. Trátalos uno a uno delante del usuario: arreglado, descartado con razón
   escrita, o anotado en LIMITS.md. Un hallazgo sin tratar deja el hito abierto.

3. **Números medidos.** Añade a `RESULTS.md` los números que este hito produce, con
   fecha, versión y **el comando exacto que los reproduce**. Un hito sin número medido
   no se cierra.

4. **Límites.** Si has descubierto algo que el proyecto NO mide o dónde se rompe,
   añádelo a `LIMITS.md` numerado.

5. **ADR.** Si has tomado una decisión de diseño no prevista, escríbela en
   `docs/adr/` con su alternativa descartada y su trade-off.

6. **ESTADO.md.** Marca $hito como CERRADO con su fecha y su número. Marca el
   siguiente como PENDIENTE. No inventes hitos que no estén en el manual.

7. **Commit.** Prepara el mensaje: qué cierra, **el número medido en el asunto** si lo
   hay, y los ficheros. No hagas push.

Ejemplo de asunto bueno: `L2: TEDS validado contra PubTabNet, coincidencia a 4 decimales`
Ejemplo de asunto malo: `refactor y mejoras`
