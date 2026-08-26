# ADR-0044 · El hallazgo de conformidad vive en `types`, con tres severidades

**Fecha:** 2026-08-26 · **Estado:** aceptada e implementada. **Toca el manual**: añade
§6.10, transcrito en este mismo commit

## Contexto

`extract.conformance` —la suite del `Protocol` de §7.2— necesita un tipo para decir
*«esta comprobación salió así, y por esto»*. Ese tipo ya existe **dos veces**:

| dónde | forma | severidades |
|---|---|---|
| `benchcore.conform.Finding` | `check`, `severity`, `detail` | `FALLA`, `AVISO` |
| `docbench_es.entity._comprobaciones.Hallazgo` | `comprobacion`, `severidad`, `detalle` | + `NO_EJECUTADA` |

Y las tres salidas de partida eran malas:

* **Copiarlo** en `extract` sería la **tercera** declaración del mismo concepto. Es
  exactamente lo que el límite 81 ya denuncia con `tasa_descarte`, que tiene tres
  implementaciones idénticas en un repo cuyo propio `entity/boe.py` dice que *«dos
  copias del mismo dato no pueden divergir»*.
* **Importarlo de `entity._comprobaciones`** metería a `extract` a leer el **módulo
  privado** de un paquete hermano. Y de la superficie pública `entity.conformance`
  tampoco: acoplaría el vocabulario de la conformidad de extractores a la de entidades,
  y el día que aquélla se mueva ésta se rompe por nada.
* **Usar `benchcore.conform.Finding` tal cual** perdería la tercera severidad.

## La tercera severidad no es un capricho, y por eso no basta `benchcore`

`benchcore.conform.check` mira **la forma** del contrato, y la forma siempre se puede
mirar: o el miembro está o no está. Con `FALLA` y `AVISO` le sobra.

Las suites de `docbench-es` **ejecutan** el sujeto contra documentos, y ahí aparece un
tercer resultado que allí no existe: **`NO_EJECUTADA`**. Si `discover` no trae ni un
documento, la idempotencia de `fetch` no falla — **es que no se ha comprobado**. Si el
conjunto de conformidad no trae ni una celda combinada, `veredicto_de_spans` sale
`SIN_EVIDENCIA` y eso **no es un aprobado**.

Contar cualquiera de las dos como aprobada sería *publicar como observado algo que no se
observó*, que es la familia de fallos que este repo persigue. De ahí que `pasa` exija
**cero `FALLA` y cero `NO_EJECUTADA`**: un aro por el que no se ha pasado no está
superado.

## Decisión

**`Severidad` y `Hallazgo` suben a `docbench_es.types`**, en `types/_conformidad.py`, y
las dos suites los importan de ahí. `entity._comprobaciones` deja de declararlos y
`entity.conformance` los sigue reexportando, así que ningún consumidor se entera.

**Por qué `types` y no un paquete nuevo.** El contrato de capas tiene `exhaustive =
true`: un paquete nuevo sin ubicar pone el CI rojo, y ubicarlo exigiría tocar
`.importlinter` — que es lo que la regla del repo prohíbe hacer para que quepa el código.
`types` está por debajo de todos, no importa nada del proyecto, y un hallazgo de
conformidad **es un dato publicado**: el informe de conformidad se enseña.

## Lo que se descarta, y con qué precio

**Añadir `NO_EJECUTADA` a `benchcore.conform.Severity`.** Sería el sitio teóricamente
correcto si la tercera severidad fuera general, y **no lo es**: nace de que estas suites
ejecutan, y `benchcore.conform` por diseño no ejecuta. Además costaría una publicación de
`benchcore` con subida de `API_VERSION` para desbloquear un hito de otro repo.

Si algún día `gonogo` necesita la misma tercera severidad —porque sus jueces también se
ejecuten contra casos—, entonces sí: el eje es común y el sitio es `benchcore`. **La
señal para moverlo es un segundo consumidor fuera de este repo, no la elegancia.** Es la
misma regla que ADR-0035 aplicó a `EntityAdapter` en la dirección contraria.

## Lo que este ADR NO decide

**Qué comprueba cada suite.** Aquí sólo vive el vocabulario. Las comprobaciones de
extractor van en `extract/conformance.py` y las de entidad ya están en
`entity/_comprobaciones.py`.

Y **no unifica los informes**: `InformeConformidad` sigue en `entity.conformance` con sus
campos, porque un informe de entidad y uno de extractor cuentan cosas distintas —ventana
de descubrimiento uno, documentos ejecutados y veredicto de spans el otro—. Unificarlos
antes de tener los dos escritos sería diseñar el contrato a ciegas que el D-003 de
`benchcore` prohíbe.
