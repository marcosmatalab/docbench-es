---
name: adversarial
description: Lanza al revisor adversarial contra el trabajo sin commitear y trae sus hallazgos.
allowed-tools: Bash, Read, Glob, Grep
---

# Escrutinio adversarial

!`git diff HEAD --stat`

Invoca al subagente `revisor` con el diff completo frente a HEAD y el contexto del
hito en curso (mira ESTADO.md). Pídele que busque, por este orden:

1. Afirmaciones del README o del manual que este código **ya no cumple**.
2. Estadística mal planteada, fórmulas mal derivadas, supuestos no declarados.
3. Casos degenerados sin tratar: división por cero, varianza cero, muestra vacía,
   `NaN` disfrazados.
4. Errores tragados: `except` que no relanza, fallos que no se cuentan.
5. Ficheros por encima de 300 líneas o con más de una responsabilidad.
6. Tests que pasarían igual con el código roto.

Trae sus hallazgos aquí **sin filtrar**, y trata cada uno delante del usuario:
arreglado, descartado con razón escrita, o anotado en LIMITS.md.
