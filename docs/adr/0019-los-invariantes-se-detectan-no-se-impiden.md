# ADR-0019 · Los invariantes se detectan a posteriori, no se impiden en construcción

**Fecha:** 2026-08-22 · **Estado:** aceptada, implementada y **transcrita al manual**
(§6.2 y §9.1) en el mismo commit

## Contexto

L0 dejó declarado el caso degenerado de `span < 1`: una celda con `rowspan=0` no
cubre ninguna posición, `cell_at` devuelve `None` para ella igual que para un
hueco, y su docstring dice que **quien lo reporta es `is_wellformed()`, en L1**.

L1 tenía que decidir si eso lo **detecta** `is_wellformed()` o lo **impide**
`validate()` en construcción. No es lo mismo, y hay precedente en el repo para las
dos: `Extraction.__post_init__` **sí** rechaza en construcción un `failed=True`
sin `failure_reason`.

Había una segunda pregunta pegada a la primera: **dónde vive el algoritmo**. §9.1
pone `validate()` en `core.canonical` y §6.2 pone `is_wellformed()` como método de
la dataclass, que vive en `types`. El contrato de capas de `.importlinter` pone
`core` por encima de `types : errors`, así que `types` no puede importar `core` —y
no vale ni un import diferido dentro de la función, porque `lint-imports` lee el
AST—.

## Decisión

**Se detecta. Ni `validate()` ni ningún `__post_init__` impiden construir una
tabla mal formada.** `span < 1` sale como `SPAN_MENOR_QUE_UNO`, que es fatal, y la
celda sigue siendo invisible para `cell_at` como declaró L0.

Tres razones, en orden de peso:

1. **Si no se puede construir una tabla rota, no se puede demostrar que se
   detecta.** El criterio de aceptación de L1 es *«se detectan al 100%»*. Con
   rechazo en construcción, el censo de 7.593 tablas mutadas no existe y el
   criterio se cumple por vacío, que es contra lo que L0 escribió su candado.
2. **Regla de oro 6: ningún error se traga, se cuenta.** Levantar en construcción
   tira el documento entero y pierde el dato en vez de medirlo. La tasa de tablas
   mal formadas por extractor es un resultado de L5.
3. **L0 ya se comprometió** en el docstring de `cell_at` y en su test.

**La diferencia con el precedente de `Extraction`**, que es lo que hace que las
dos decisiones sean coherentes y no contradictorias: allí se impide un estado que
haría **incontable** un fallo —un documento caído sin causa desaparece del informe—
mientras que aquí hay que poder construir la tabla mala **precisamente para
contarla**.

**Y la otra mitad, que es la que de verdad protege:** ningún conversor puede
emitir `span < 1`. `from_html` sigue el propio estándar HTML —`rowspan="0"` baja
hasta el final de su sección; un valor negativo o no numérico vale 1— y un test de
propiedad afirma que `∀ entrada: validate(conversor(entrada))` sale limpio.

**Dónde vive el algoritmo, que es consecuencia forzada y no gusto:** en
`types/_invariantes.py`, junto a los datos que inspecciona.
`core.canonical.validate()` es la puerta pública que manda §9.1 y **delega en el
método público `is_wellformed()`** —no en el submódulo privado, porque
`docbench_es.types` es la única superficie de import del modelo de datos
(ADR-0013) y hay un test de L0 que lo hace cumplir—. Un test de propiedad afirma
que `validate(t) == t.is_wellformed()` para que nadie reimplemente ninguno de los
dos por su cuenta.

## Alternativa descartada

**Rechazar en `__post_init__`**, como hace `Extraction`. Se descarta por las tres
razones de arriba, y sobre todo por la primera: haría el criterio de aceptación de
L1 incomprobable, que es peor que un modelo de datos permisivo.

**Duplicar la comprobación** en `types` y en `core` para que cada sección del
manual tenga su función «en su sitio». Se descarta porque deja dos fuentes de
verdad sobre la misma tabla, y el día que se separen ganaría la que se lea
primero, que es exactamente el fallo que la regla de oro 8 describe para los ADR.

**Tocar el contrato de capas** para permitir `types → core`. Se descarta sin
discusión: en este repo el contrato no se toca para que quepa el código.

## Trade-off

Lo que se paga: **el modelo de datos admite tablas basura**, y cualquiera puede
construir una y pasarla a TEDS sin validarla. Se mitiga con el test de propiedad
que ata a los cinco conversores —lo que sale de un conversor valida limpio—, con
la suite de conformidad de L5 y con el contrato de §7.2, que ya exige que las
tablas devueltas por un extractor cumplan los invariantes.

Lo que se compra: que «se detectan al 100%» sea una frase con un número detrás.
