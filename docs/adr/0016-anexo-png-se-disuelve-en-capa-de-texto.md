# ADR-0016 · `anexo-png` se disuelve: la frontera es la capa de texto, no las imágenes

**Fecha:** 2026-08-22  ·  **Estado:** aceptada, **pendiente de implementar en L3**

## Contexto

El sondeo del BOE del 22 de agosto de 2026
([notas](../sondeo-boe-2026-08-22.md)) clasificó 600 documentos en tres ventanas
usando las reglas de `strata_rules` de §10.1. Al mirar **qué** documentos habían
caído en `anexo-png`, el estrato resultó no ser uno:

| Ventana | n | Imágenes por documento | Páginas por documento |
|---|---|---|---|
| otoño 2025 | 10 | 1 – 14 | 7 – 15 |
| primavera 2026 | 11 | **1 – 134** | **7 – 136** |
| agosto 2026 | 1 | 1 | 12 |

En la misma etiqueta conviven **un documento de 8 páginas con una figura** y **un
anexo de 136 páginas con 134 imágenes**. La regla que los junta es
`anexo-png ⇐ sin <table> y con <img>`, o sea *"tiene alguna imagen"*.

**Por qué eso rompe una medición y no sólo una taxonomía.** El estrato es la unidad
sobre la que §12 calcula la exactitud ponderada. Si un estrato mezcla dos
poblaciones en las que compiten **familias de extractor distintas**, su exactitud
media no describe a ninguna de las dos: es un promedio entre «los parsers de texto
lo bordan» y «los parsers de texto sacan cero», y su valor depende de la proporción
de la mezcla, que nadie declaró. Y no se queda ahí: §12 **propaga** esa media a la
cifra ponderada global.

Lo que de verdad separa a los dos documentos **no es cuántas imágenes tienen**: es
si el PDF trae **capa de texto**. Esa sí decide qué puede competir:

- Sin capa de texto, un parser de texto —`pdfplumber`, `pymupdf`— devuelve nada.
  No es que puntúe bajo: es que **no compite**, y su cero no mide su calidad.
- Con capa de texto, un OCR **se desperdicia**: paga latencia y coste por
  reconstruir algo que ya estaba escrito, y el banco publicaría un coste por
  documento que no tiene sentido comparar con el del parser.

Un documento con una figura decorativa y capa de texto completa es, para un
extractor, **el mismo problema** que un documento sin ninguna imagen.

## Decisión

**`anexo-png` deja de ser un estrato de dificultad.** Se sustituye por una medida
directa sobre el PDF, y las etiquetas que salen de ella son las que §3 bis ya
define.

1. **Se mide `caracteres_extraibles_por_pagina`** sobre `RawDoc.primary`, que es
   exactamente lo que `strata(self, ref: DocRef, doc: RawDoc)` de §7.1 ya recibe:
   `RawDoc` de §6.1 lleva `primary: bytes` —el PDF tal cual— y `n_pages`.
   **No hace falta descargar nada nuevo ni cambiar el contrato de entidad.**
2. **La frontera va en el perfil de la entidad**, no en el código, como el umbral de
   coherencia. Valor inicial propuesto: **< 100 caracteres por página** ⇒ sin capa
   de texto útil.
3. **Las etiquetas resultantes son `nacido-digital` y `escaneado`**, los estratos de
   §3 bis, y la segunda **ya existe** como regla en §10.1:
   `{ name: escaneado, when: "no_text_layer" }`. Este ADR le pone una definición
   operativa a ese `no_text_layer`, que hasta hoy no la tenía.
4. **`anexo-png` desaparece de `strata_rules` y del plan.** «Tiene una imagen» sigue
   siendo un dato observable y se puede registrar, pero **no es un estrato**: no
   determina qué extractor puede competir.

### El eje que este ADR cruza, dicho en voz alta

El glosario de §2 separa **estrato de corpus** —de dónde viene el documento y qué
verdad admite— de **estrato de dificultad** —qué tiene de difícil—, y coloca
`nacido digital` y `escaneado` en el primero y `anexo en imagen` en el segundo.
Esta decisión mueve una etiqueta de un eje al otro, y hay que justificarlo.

La justificación es que **`no_text_layer` determina las dos cosas a la vez**, y el
manual ya lo reconoce sin decirlo: `escaneado` aparece en §3 bis como estrato de
corpus **y** en las `strata_rules` de §10.1 como regla de dificultad. No es una
ambigüedad que este ADR introduce; es una que resuelve. La capa de texto decide el
**modo de verdad** (un escaneado no admite `DERIVED` de un XML que no existe) y
decide la **familia de extractor** que compite. Un mismo hecho medido, dos
consecuencias, y por eso vive en los dos ejes.

**Lo que este ADR NO hace:** no toca el resto de estratos de dificultad
—`tabla-simple`, `celdas-combinadas`, `multipagina`, `con-notas-al-pie`,
`sin-tabla`—, que siguen siendo propiedades de la tabla y no del documento.

## Alternativa descartada

**A · Un umbral de número de imágenes.** Partir `anexo-png` en dos por, digamos,
«más de 20 imágenes» o «más de una imagen por página». Es la alternativa obvia
porque el dato ya está contado y no cuesta nada.

**Se descarta porque parte por una propiedad que no determina nada.** El número de
imágenes no dice si un extractor de texto puede competir: un informe nativo con 40
gráficos tiene capa de texto perfecta y un escaneado de 3 páginas no tiene ninguna.
El umbral separaría documentos que se comportan igual y juntaría documentos que se
comportan distinto, que es exactamente el defecto que se quiere arreglar. Sería
mover la arbitrariedad de sitio en vez de quitarla, y encima con la apariencia de
haberla resuelto — el peor resultado posible para este repo.

**B · Dejar `anexo-png` como está y declarar la heterogeneidad en `LIMITS.md`.**
Descartada por la regla que el propio proyecto acaba de aplicarse con
`.hypothesis` en `make clean`: **una salvedad que se puede eliminar y se decide
documentar es deuda, no rigor.** Aquí además la salvedad no sería inocua: contamina
la exactitud ponderada de §12, o sea el titular del proyecto.

**C · Medir la capa de texto pero conservar `anexo-png` en paralelo.** Tener las dos
etiquetas. Descartada porque multiplica los estratos sin añadir información: si
`escaneado` ya se decide por la capa de texto, `anexo-png` sólo aporta ruido al
muestreo y una casilla más que ponderar.

## Trade-off

**Lo que se gana:** cada estrato vuelve a contener documentos en los que compite la
misma familia de extractor, así que su exactitud media significa algo y la ponderada
de §12 hereda una cifra interpretable. Y se le da definición operativa a
`no_text_layer`, que estaba en `strata_rules` sin decir qué era.

**Lo que cuesta:**

1. **Hay que extraer texto del PDF en `strata()`**, que hasta ahora era barato. Son
   los mismos bytes que ya están en memoria, pero es tiempo de CPU por documento en
   la fase de etiquetado. Se mide y se publica cuando L3 lo implemente.
2. **El umbral es una decisión de diseño más que declarar**, con su tasa de reparto
   como resultado publicable —igual que el 0,85 de coherencia—. No se elimina la
   arbitrariedad: se mueve a una propiedad que sí determina el resultado, y se
   declara.
3. **El BOE apenas tiene escaneados**, así que este ADR casi no cambia los números
   del estrato nacido-digital. **Su valor está en L12b**, con boletines provinciales
   antiguos, donde la mezcla sí será real. Se escribe ahora porque el sondeo lo
   descubrió ahora y porque L6 congela el plan antes.

## Cómo se verifica

- **En L3**, cuando `entity.boe` implemente `strata()`: un test de conformidad que
  compruebe que ningún documento sale con la etiqueta `anexo-png`, y que
  `nacido-digital` y `escaneado` son mutuamente excluyentes y exhaustivos.
- **El reparto se publica** —qué proporción cae en cada lado y con qué umbral—, como
  cualquier otra decisión de diseño con consecuencias numéricas.
- **No hay test hoy.** Este ADR se escribe **antes** que su implementación, así que
  hasta L3 es una decisión declarada y nada más. Decirlo importa: un ADR aceptado no
  es código, y en este repo la diferencia entre lo declarado y lo verificado es la
  que se paga cara.

## Consecuencias

- **`strata_rules` de §10.1 cambia** en el próximo plan: se va `anexo-png` y
  `no_text_layer` pasa a ser `caracteres_extraibles_por_pagina < umbral_perfil`.
- **`SamplingPlan` pierde una casilla y gana otra.** Los `weight` se siguen
  midiendo sobre el corpus real (`found/total`), nunca heredados de un sondeo.
- **`LIMITS.md` no crece.** Esto se arregla, no se declara.
- **§9.4, §2 y §10.1 del manual quedan desalineados con el repo** hasta que se transcriba
  el cambio. Es deuda de documentación, y va a la deuda abierta de `ESTADO.md`.
