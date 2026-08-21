---
name: entidad
description: Añade una entidad nueva (BOE, diputación, empresa privada) con sus siete métodos, su licencia, su privacidad y su glosario.
argument-hint: "[id de la entidad]"
arguments: [entidad]
allowed-tools: Read, Glob, Grep, Bash, Write, Edit
---

# Entidad nueva: $entidad

Lee primero `docs/entity-guide.md` (si ya existe) y la sección de interfaces de `MANUAL.md`.

## Los siete métodos

`discover` · `fetch` · `truth` · `license` · `privacy` · `glossary` · `strata`

## El orden correcto, que evita el 80% del trabajo tirado

1. **`license()` y `privacy()` PRIMERO.** Antes de escribir una línea de descarga,
   decide qué permite la fuente. Si `special_categories` es `True`, **el adaptador no
   se registra y el trabajo termina aquí**. Si `may_send_to_third_party` es `False`,
   toda la campaña será local, y eso cambia el plan.
2. **`truth_mode` después.** ¿Hay una versión estructurada oficial del mismo documento?
   Si sí, `DERIVED` y `truth()` la parsea. Si no, `CONSENSUS` y `truth()` devuelve
   `None`. **No hay término medio y el contrato lo comprueba.**
3. **`discover()` sin descargar.** Perezoso y paginable. El test de contrato mide el
   tráfico.
4. **`fetch()` idempotente.** Dos llamadas, el mismo `sha256`.
5. **`strata()` determinista** sobre el documento ya bajado.
6. **`glossary()` al final**, y es trabajo de dominio, no de código: hay que hablar con
   alguien que conozca esos documentos. Empieza por los pares confundibles, que son lo
   que de verdad mide la capa 3.

## Criterio de terminado

```
docbench conform --entity $entidad
docbench entity doctor $entidad
```

Los dos en verde. Y si es la **segunda** entidad del repo, escríbelo en `RESULTS.md`:
es la única prueba real de que ADR-0001 es cierto y no una declaración.
