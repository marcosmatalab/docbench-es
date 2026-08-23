# ADR-0032 · El contrato de entidad se diseña para admitir un adaptador sin API y sin verdad

**Fecha:** 2026-08-23 · **Estado:** aceptada. **No construye `generico_pdf`**:
decide que el contrato de L3 **no le cierre la puerta**

## Contexto

El árbol de §8 incluye `entity/generico_pdf.py`, *«una carpeta de PDFs sin más»*.
Ese fichero es el que convierte esto de banco de pruebas en **herramienta usable**:
es lo que permite que alguien apunte a **su** carpeta y el proyecto le diga qué
extractor usar, clasificando sus documentos en los estratos ya medidos.

No se construye en L3. Pero el contrato de entidad **sí** se escribe en L3, y un
contrato que exija cosas que ese adaptador no puede cumplir estaría mal **hoy**,
no en L5 — y arreglarlo entonces costaría un hito, porque para entonces habría
adaptadores escritos contra él.

## Decisión

**`entity.base` y la suite de conformidad se diseñan sabiendo que existirá un
adaptador cuyo `discover` lee un directorio, cuyo `truth` devuelve `None` y que no
habla con ninguna API.** Método a método:

| Método | Cómo lo cumple una carpeta de PDFs | Qué NO puede exigir el contrato |
|---|---|---|
| `discover(since, until, **filters)` | Recorre el directorio y filtra por fecha de modificación. Perezoso con `os.scandir` | Que haya paginación, ni que exista un «sumario». El contrato pide **perezoso**, no *paginado por el origen* |
| `fetch(ref)` | Lee el fichero del disco. Idempotente por construcción | Que haya caché por HTTP, ni `ETag`, ni reintentos. La idempotencia se comprueba por `sha256`, no por conducta de red |
| `truth(ref)` | **`None`**, porque su `truth_mode` es `NONE` | Nada: §7.1 ya dice «`None` si y sólo si `truth_mode != DERIVED`», y eso lo cumple |
| `license()` | La declara quien monta el adaptador; típicamente interna y sin redistribución | Que sea pública, ni que tenga `source_url` alcanzable |
| `privacy()` | Declarada; típicamente `may_send_to_third_party: false` | Nada |
| `glossary()` | Glosario vacío | Que tenga términos |
| `strata(ref, doc)` | `escaneado` / `nacido-digital` por capa de texto, que **sí** se calcula sobre el PDF | **Que emita las seis etiquetas.** `celdas-combinadas`, `multipagina` y `sin-tabla` exigen ver tablas, y ver tablas exige un extractor — que el núcleo no puede importar |

**La consecuencia más dura, y es la que justifica escribir esto ahora:** la suite
de conformidad **no puede exigir un conjunto fijo de etiquetas de estrato**. Sólo
puede exigir que `strata` sea **determinista** y que devuelva un subconjunto de las
declaradas en el perfil. Un contrato que pidiera «devuelve `sin-tabla` o
`tabla-simple`» sería incumplible sin extractor, y habría convertido el estrato en
una obligación del adaptador en vez de una propiedad del documento.

**Dos más, del mismo tipo:**

- **`discover` «no descarga: se mide el tráfico y debe ser el mínimo»** (§7.1). Con
  un directorio el tráfico es **cero**, así que la comprobación tiene que aceptar
  el cero como válido y no como «no se pudo medir».
- **La suite corre sin red.** Es lo que permite que viva en `tests/unit` y no en
  `tests/e2e`, y por tanto que esté en la puerta. Si la conformidad necesitara red,
  el contrato de entidad **no tendría cobertura de CI hasta L7** (límite 25).

**Y entra ya un cuarto adaptador falso** en `test_entity_conformance.py`: uno de
tipo carpeta, con `truth_mode = NONE`, sin red y sin verdad. Cuesta poco y **fija
el diseño**: si mañana alguien endurece el contrato de una forma que ese adaptador
no pueda cumplir, se cae un test en la puerta, no un hito dentro de dos meses.

## Alternativa descartada

**Escribir el contrato sólo contra el BOE y ensancharlo en L5.** Es lo que sale
gratis hoy y caro después: en L5 habría ocho extractores y varios adaptadores
escritos contra el contrato estrecho, y ensancharlo sería cambiar una interfaz con
implementaciones vivas. El coste de admitirlo hoy es **un adaptador falso de
treinta líneas**; el de admitirlo en L5 es un hito.

**Construir `generico_pdf` ya, en L3.** Descartada: no está en la fila de L3 de
§16 y no hace falta para el criterio. Lo que hace falta es **no cerrarle la
puerta**, y eso lo da el falso.

## Trade-off

Lo que se paga: la suite de conformidad es **más floja** de lo que podría ser
contra un solo adaptador rico. No puede exigir estratos concretos ni conducta de
red, y eso deja fuera comprobaciones que con el BOE serían posibles.

Lo que se compra: que *«el motor es agnóstico a la entidad»* —lo que §14 llama
demostrar con la suite— sea cierto para una carpeta de PDFs y no sólo para dos
organismos que se parecen. Y las comprobaciones que el contrato general no puede
exigir no se pierden: van a la suite **específica** de `entity.boe`, que sí sabe
que hay una API.
