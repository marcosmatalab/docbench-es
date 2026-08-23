# ADR-0024 · Un documento con varias tablas: la nota es la media, y ninguna se pierde

**Fecha:** 2026-08-23 · **Estado:** aceptada, implementada y con dos tests que la
fijan. **No contradice el manual**: lo cumple. §6 ya decía que
`evaluable_coverage` es *«sobre cuántas tablas se pudo calcular»* y el código
contaba documentos

## Contexto

`teds_batch` recibe `(clave, predicha, real)` y su propio docstring dice que **la
clave es la del documento, no la de la tabla**: es la unidad de agrupación del
bootstrap de L6 (regla de oro 3, se remuestrean DOCUMENTOS). O sea que un
documento con tres tablas manda **tres pares con la misma clave**. Eso no es un
caso raro: es el caso normal en el BOE.

La implementación era `por_documento[clave] = nota`. Medido:

```
teds_batch([("boe/doc1", mala, gold), ("boe/doc1", gold, gold)])
→ per_document={'boe/doc1': 1.0}   aggregate=1.0   evaluable_coverage=1.0
```

**La tabla mal extraída desaparece del informe y la cobertura afirma que se
evaluó todo.** Es la regla de oro 6 rota en sus dos mitades a la vez: ni se
cuenta el fallo ni se avisa de él. Y no es un error neutro: sesga **hacia
arriba** justo en los documentos con más tablas, que son los más difíciles. Como
la clave de documento es además la unidad de remuestreo del bootstrap, el sesgo
sobreviviría intacto al intervalo de confianza de L6, que lo publicaría con
aspecto de rigor.

Lo encontró el escrutinio adversarial del cierre de L2. **No lo encontró ningún
test** porque `test_teds_batch.py` mandaba un par por clave: con una tabla por
documento, todas las cuentas coinciden y el fallo es invisible.

## Decisión

**La nota de un documento es la media de sus tablas evaluables.**

1. Los pares se **acumulan** por clave, nunca se sobrescriben.
2. `per_document[clave]` = media de las evaluables, o `None` si no hay ninguna.
3. `not_applicable` lista los documentos **sin una sola tabla evaluable**.
4. **`evaluable_coverage` se cuenta sobre TABLAS**, no sobre documentos, que es
   lo que §6 dice literalmente. Un documento con 1 de 20 tablas evaluables no es
   cobertura total.

La media **sin ponderar por tamaño de tabla** es deliberada: ponderar por número
de celdas haría que un documento con una tabla enorme y otra pequeña puntuara
casi sólo por la grande, y la unidad que el informe compara es el documento.

## Alternativa descartada

**Lanzar ante clave repetida.** Es la opción más ruidosa y por eso tentadora:
convierte el fallo silencioso en una excepción. Descartada porque **el caso no es
un error**: un documento con varias tablas es lo normal, y `teds_batch` tendría
que rechazar el corpus real. Habría empujado a quien llama a inventarse claves
`doc#tabla`, y entonces el bootstrap de L6 remuestrearía **tablas** creyendo que
remuestrea documentos — que es exactamente lo que la regla de oro 3 prohíbe, y
además callado.

**Devolver una entrada por tabla y agrupar al agregar.** Descartada por lo mismo:
`TedsReport.per_document` se llama así porque lo que hay dentro son documentos.
Dos escalas en el mismo objeto es el error que ADR-0023 ya descartó para el TEDS
negativo.

**Quedarse con la peor tabla del documento** en vez de la media. Es defendible
—«un documento vale lo que su peor tabla»— y se descarta porque no es lo que §12
mide: §12 promedia notas por tabla, y coger el mínimo cambiaría la métrica sin
decirlo. Si alguna vez interesa, es una columna añadida, no una redefinición.

## Trade-off

Lo que se paga: **la media de medias no es la media de tablas.** Un documento con
una tabla pesa lo mismo que uno con veinte. Es intencionado —el documento es la
unidad de comparación y de remuestreo— pero hay que decirlo, porque el agregado
NO es «el TEDS medio de las tablas del corpus». Está en `LIMITS.md` como parte
del límite 43.

Lo que se compra: que ninguna tabla desaparezca del informe, y que la cobertura
diga la verdad sobre cuántas se pudieron evaluar. `batch_sobrescribe` es el
mutante versionado que restaura el fallo, y lo matan 2 tests.
