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

## La regla que más veces se olvida al escribir un ADR

> **Si la decisión se apoya en una afirmación sobre una DEPENDENCIA EXTERNA, esa
> afirmación lleva test.**

Un ADR se escribe una vez y se lee durante meses. Las afirmaciones sobre el propio
repo las vigila la suite sin que nadie haga nada: si el código cambia, algo se pone
rojo. Las afirmaciones sobre **otro repo, otra librería o una API ajena** no las
vigila nadie — **se quedan viejas en silencio**, y el ADR sigue ahí con un
argumento que ya no describe la realidad.

El test **no fija la conclusión: fija la PREMISA.** No comprueba que la decisión
siga siendo buena —eso lo decide una persona— sino que el hecho en que se apoyaba
sigue siendo cierto. Cuando se ponga rojo, la respuesta correcta casi nunca es
cambiar el test: es **volver a mirar el ADR con el hecho nuevo delante**.

*Caso que lo motiva (ADR-0035).* La decisión de que `EntityAdapter` viva en
`docbench` se apoya en una razón de diseño —el eje tendría un solo consumidor— y
menciona además un hecho sobre `benchcore`: que `Capabilities.axis` es un `Literal`
cerrado sin `entidad`. Ese hecho vive en otro repositorio y puede cambiar cualquier
día. `test_el_eje_de_entidad_sigue_sin_existir_en_benchcore` lo fija:

```python
ejes = get_args(get_type_hints(Capabilities)["axis"])
assert ejes == ("datos", "computo", "ejecucion", "salida")
assert "entidad" not in AXES
```

Ponlo en la sección **Cómo se verifica**, con el nombre del test, y di **qué
significa que se ponga rojo** — porque no siempre significa lo mismo, y quien lo
vea dentro de seis meses no estará en esta conversación.
