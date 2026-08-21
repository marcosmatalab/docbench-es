---
name: estado
description: Dice dónde está el proyecto, qué queda y cuál es el siguiente paso. Sin tocar nada.
allowed-tools: Bash, Read
---

# Dónde estamos

El hook `SessionStart` ya ha inyectado `ESTADO.md` entero al arrancar: aquí solo se
trae lo que puede haber cambiado desde entonces, y NO se paga la puerta completa.

!`echo "── hitos ──"; sed -n '/## Release en curso/,/## Deuda/p' ESTADO.md`
!`echo "── git ──"; git log --oneline -8 2>/dev/null; echo; git status --short 2>/dev/null`
!`echo "── última puerta verde ──"; test -f .claude/.ultima-puerta && echo "hubo un verde con el árbol actual de .py" || echo "sin verde registrado: ejecuta /verificar"`

Responde exactamente esto, en cuatro líneas y nada más:

1. **Hito en curso** y qué falta para su criterio de aceptación.
2. **Siguiente hito** y sus horas estimadas, que están en la propia tabla de ESTADO.md.
3. **Deuda abierta**: cualquier cosa marcada como pendiente en ESTADO.md o LIMITS.md.
4. **El comando** con el que se sigue ahora mismo.
