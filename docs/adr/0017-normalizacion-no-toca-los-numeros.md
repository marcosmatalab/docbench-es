# ADR-0017 · `normalize_cell_text` no toca los números, ni los acentos, ni los glifos

**Fecha:** 2026-08-22 · **Estado:** aceptada, implementada y **transcrita al manual**
(§9.1) en el mismo commit, como manda la regla de oro 8

## Contexto

§9.1 del manual describe `normalize_cell_text` así, literalmente:

> ```python
> def normalize_cell_text(s: str) -> str:
>     """Espacios, guiones suaves, comas decimales, separadores de millares.
>     CADA normalización va documentada: una normalización agresiva es una
>     forma silenciosa de hacer trampas a favor de un extractor."""
> ```

El docstring se contradice a sí mismo. Pide normalizar **comas decimales y
separadores de millares** y, en la frase siguiente, avisa de que una normalización
agresiva es una trampa silenciosa. Normalizar el separador decimal es exactamente
esa trampa, y de la peor especie que puede darse en este proyecto concreto.

**Por qué justo aquí y no en otra normalización.** El separador decimal es el
fallo más específicamente español que existe en una tabla de números. Un extractor
que devuelve `1,234.56` donde la página dice `1.234,56` no ha cometido un error de
codificación: ha aplicado la convención anglosajona a un documento español. Es un
fallo real, medible, publicable, y **es lo que distingue a este banco de una
traducción de OmniDocBench**. Si `normalize_cell_text` lo repara, el banco pierde
la capacidad de detectar el único fallo que justifica que sea un banco *en
español*. Eso no es normalizar: es borrar la medición.

Y no es un caso hipotético. El corpus son tablas del BOE: el 28% de los documentos
de las secciones I+III traen tabla, y lo que llevan dentro son importes.

## Decisión

**La regla, de la que sale todo lo demás:**

> Sólo se toca lo invisible o la forma de composición Unicode. **Ningún glifo
> visible se altera ni se borra.** Una excepción, enumerada y con test propio: la
> expansión de las siete ligaduras latinas.

De ahí salen **seis normalizaciones aplicadas** —NFC, expansión de ligaduras,
borrado de `Cf`, mapeo de `Cc`/`Zs` a espacio, colapso de espacios y recorte— y
**seis rechazadas**: acentos, mayúsculas, comillas y guiones, separadores
numéricos, deshacer la partición de línea y NFKC. Las doce, con qué hacen y **a
quién benefician si me paso**, están en `docs/metrics.md`, y un test de la puerta
—`test_las_doce_decisiones_estan_documentadas`— se pone rojo si una decisión del
código no está documentada allí.

**La equivalencia numérica no desaparece: cambia de sitio.** Vive en el
verificador `numeric` de §9.3 y en `truth.derived` de L4, con su tolerancia
declarada, que es una comparación explícita y auditable en vez de una reescritura
silenciosa de la celda.

### La consecuencia que hay que leer entera

Un extractor que devuelve `1,234.56` donde la página dice `1.234,56` **queda
penalizado en dos niveles**:

- en **TEDS con contenido** (L2), porque la cadena de la celda es distinta;
- en el verificador **`numeric`** (L9), donde con su tolerancia declarada el
  número **puede darse por bueno**.

No es doble contabilidad. Son dos preguntas distintas —*«¿transcribiste la
celda?»* y *«¿el número es correcto?»*— y responderlas por separado es
informativo, porque un extractor puede acertar la segunda fallando la primera.
Lo que sería una sola pregunta mal hecha es repararlo en la normalización y
publicar las dos como si estuvieran bien.

## Alternativa descartada

**Hacer lo que dice el docstring de §9.1 y normalizar los separadores numéricos**,
convirtiendo `1.234,56` y `1,234.56` a una forma común antes de comparar.

Se descarta porque el resultado sería un banco que **no puede medir su propia
razón de ser**. Todas las notas de nivel 1 subirían, ninguna mediría peor, y la
mejora sería invisible en el informe: no hay ninguna columna donde apareciera
«aquí he perdonado el separador decimal». Es el patrón exacto que la regla de oro
7 del repo llama trampa silenciosa.

También se descartó una **variante intermedia**: normalizar sólo el separador de
millares y no el decimal. Se descarta porque no se pueden separar sin analizar el
número entero —`1.234` es mil doscientos treinta y cuatro en español y uno coma
doscientos treinta y cuatro en inglés— y ese análisis es precisamente el que tiene
que hacer el verificador `numeric`, con su tolerancia declarada.

## Trade-off

Lo que se paga: **dos extractores que transcriben igual de bien salvo por la
convención numérica salen con notas distintas en L2**, y hay que explicar por qué
en el informe. Lo que se compra: que esa diferencia **se vea**, que es la única
manera de que el banco publique algo que otro no publica.

Segundo coste, más sutil: `normalize_cell_text` deja de ser el sitio donde
comparar dos números, así que L2 y L4 tendrán que llamar a la comparación
numérica explícitamente. Eso es más código, y es el código correcto: una
comparación con tolerancia declarada en vez de una igualdad de cadenas que fingía
serlo.
