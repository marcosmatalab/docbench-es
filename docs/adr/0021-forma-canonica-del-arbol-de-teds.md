# ADR-0021 · La forma del árbol de TEDS: `<thead>`/`<tbody>`, todo `<td>`, y el hueco ausente

**Fecha:** 2026-08-22 · **Estado:** aceptada, implementada y **transcrita al manual**
(§9.2) en el mismo commit

## Contexto

TEDS no está definido sobre `CanonicalTable`: está definido sobre **el árbol HTML
de una tabla**. Convertir una en el otro parece mecánico y no lo es, porque
`CanonicalTable` **no guarda tres cosas que mueven el número**:

- si una fila iba en `<thead>` o en `<tbody>`;
- si una celda era `<th>` o `<td>` —guarda `is_header`, que no es lo mismo—;
- el marcado inline dentro de la celda.

Medido contra la implementación de referencia, sobre una tabla de una sola celda:

| Diferencia | TEDS |
|---|---|
| `<tr>` suelto contra el mismo dentro de `<tbody>` | **0,667** |
| `<tbody>` contra `<thead>` | **0,667** |
| `<th>` contra `<td>` | **0,667** |

Un tercio de la nota en una tabla pequeña, por una decisión de render. No es un
detalle de implementación: es una decisión con número.

Y hay una cuarta, que viene de L1 y sí estaba decidida: **un hueco es la ausencia
de un `<td>`**, no un `<td>` vacío (ADR-0018).

## Decisión

La forma canónica del árbol, fijada en `core/teds/_arbol.py` y usada **también**
para generar el golden, de modo que los dos lados comparen lo mismo:

1. Raíz `<table>`. **No cuenta** en el denominador: la referencia normaliza por
   los DESCENDIENTES.
2. **`<thead>` sólo si hay filas de cabecera**, y sólo con el **prefijo máximo**
   de filas cuyas celdas son todas `is_header`. Una fila de cabecera que aparezca
   en mitad de la tabla se queda en `<tbody>`: HTML exige `<thead>` antes de
   `<tbody>`, y moverla cambiaría el orden de las filas, que es justo lo que el
   árbol codifica.
3. **`<tbody>` con el resto**, si queda alguna.
4. **Todas las celdas son `<td>`, nunca `<th>`.** La referencia trata `<th>` como
   un nodo cualquiera: se baja a sus hijos y **no le lee los spans**, así que un
   `<th>` cuesta un renombrado entero. La condición de cabecera viaja en
   `<thead>`, que es como la escribe PubTabNet.
5. **Un `<td>` es una hoja.** Lleva `colspan`, `rowspan` y su contenido
   tokenizado en caracteres; no se baja a sus hijos.
6. **Un hueco no emite nodo.** El árbol se construye recorriendo las celdas que
   **originan** en cada fila, así que el hueco no es un nodo que haya que omitir:
   es un nodo que nunca existió.

## Lo que esto corrige de L1

ADR-0018 justificó `holes()` diciendo que era *«lo que L2 usa para emitir celda
ausente»*. **`core.teds` no llama a `holes()`**, y hay un test que lo comprueba
por AST. La distinción hueco/celda vacía **sí se respeta**, pero por construcción
del árbol, no consumiendo esa función.

`holes()` sigue teniendo consumidores —`validate` declara los huecos, y L4 y L5
los necesitan para el informe—, pero la frase de L1 era optimista y queda
corregida aquí, en ADR-0018 y en `RESULTS.md`.

La distinción, medida contra la referencia sobre el mismo par de tablas:

| | TEDS-S |
|---|---|
| Predicción con **celda vacía** contra verdad completa | **1,000000** |
| Predicción con **hueco** contra verdad completa | **0,857143** |

En TEDS completo los dos dan 0,857143 contra la tabla completa, y no por
casualidad: borrar un nodo cuesta 1 y renombrar una celda vacía a una con texto
también cuesta 1, porque la distancia va normalizada. La distinción aparece
**cuando la verdad es la que tiene el hueco**, que es el caso real del BOE con sus
filas cortas: ahí el que reproduce el hueco saca 1,0 y el que rellena con una
celda vacía paga por la celda de más.

## Alternativa descartada

**Emitir `<th>` para las celdas con `is_header`**, que es la traducción literal
del modelo. Se descarta porque la referencia no le lee los spans a un `<th>`: una
cabecera con `colspan=3` pasaría a compararse **sin su colspan**, y el estrato de
celdas combinadas —el titular del proyecto— quedaría medido con menos información
justo en las cabeceras, que es donde el BOE combina.

**No emitir sección ninguna** (`<table><tr>…`) y ahorrarse la decisión. Se
descarta porque entonces `is_header` no viajaría al árbol de ninguna forma y TEDS
no distinguiría una tabla con cabecera de la misma sin ella. Se estaría tirando
información que el modelo sí tiene.

## Trade-off

Lo que se paga: **`is_header` sobrevive de forma parcial**. Una fila de cabecera
en mitad de la tabla acaba en `<tbody>` y su condición se pierde para TEDS. Va a
`LIMITS.md` 41. En el BOE las cabeceras van arriba, así que el caso es raro, pero
raro no es imposible y no está medido cuántas veces pasa.

Lo que se compra: un árbol determinista, con las tres decisiones escritas, y un
golden que compara algoritmo contra algoritmo.
