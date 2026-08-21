---
name: adr
description: Escribe un ADR nuevo con el formato del repo, numerado y con su alternativa descartada.
argument-hint: "[título de la decisión]"
allowed-tools: Read, Glob, Write, Bash
---

# ADR nuevo: $ARGUMENTS

!`ls -1 docs/adr/ 2>/dev/null | tail -5`

Escribe `docs/adr/NNNN-slug.md` con el siguiente número libre y esta estructura exacta:

```markdown
# ADR-NNNN · <título>

**Fecha:** <hoy>  ·  **Estado:** aceptada

## Contexto
Qué problema aparece y por qué hay que decidir algo.

## Decisión
Qué se hace. En imperativo y sin ambigüedad.

## Alternativa descartada
Qué otra cosa se podía hacer y por qué NO se hizo. Obligatorio: un ADR sin
alternativa descartada no es una decisión, es una descripción.

## Trade-off
Qué se pierde con esta decisión. Obligatorio: si no pierdes nada, no era una decisión.

## Cómo se verifica
El test, el comando o el contrato de capas que hace cumplir esta decisión.
Si no se puede verificar, dilo: es una decisión que se va a erosionar.

## Consecuencias
Qué cambia en el código y qué queda prohibido a partir de ahora.
```
