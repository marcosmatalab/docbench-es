# ADR-0035 · `EntityAdapter` es un `Protocol` nativo de `docbench`, no un eje de `benchcore`

**Fecha:** 2026-08-23 · **Estado:** aceptada en L3.
Fija dónde vive el contrato de §7.1 y por qué

## Contexto

L3 escribe el contrato de entidad. La pregunta obligada, porque `sources/` y
`extract/` sí lo hacen así: **¿por qué `EntityAdapter` no es un `Plugin` de
`benchcore`, registrado por su eje como los demás?**

El hecho, comprobado sobre la versión instalada y no supuesto:
`benchcore.contracts.Plugin` exige `capabilities()` y `probe()`, y
`Capabilities.axis` es un `Literal["datos", "computo", "ejecucion", "salida"]`
—**un literal cerrado, sin `entidad`**—. Así que hoy un adaptador de entidad no
puede registrarse por el eje.

**Ese hecho es la razón práctica, y la razón práctica es la débil**: se arregla
añadiendo una cadena a un `Literal` en otro repo. Un argumento que se cae con un
`git commit` de una línea no sostiene una decisión de arquitectura. La razón de
diseño es otra y es la que manda.

## Decisión

**`EntityAdapter` vive en `docbench_es.entity.base` por diseño, no por
conveniencia.** El argumento:

**El eje de entidad tendría exactamente un consumidor, y siempre.** `benchcore`
sirve a `docbench-es` y a `gonogo`. `gonogo` tiene jueces y tareas, no entidades:
no hay ni habrá un segundo repo que implemente «qué documentos hay, cómo se bajan
y qué sé de ellos». El **D-003 de `benchcore`** dice que un contrato diseñado sin
un consumidor que lo pruebe es **un contrato a ciegas**; la regla espejo, que es
la que se aplica aquí, es que **un contrato compartido con un solo consumidor no
está compartido: está mal colocado.** Sería una interfaz cuyo único implementador
y único llamador viven en este repo, y cada cambio costaría dos PR en dos
repositorios y una subida de `API_VERSION` que nadie más notaría.

**El contraste lo confirma, y por eso se escribe al lado:** `sources/` —los
conectores de plataforma de L15— **sí** son `DataSource`, que es un eje que **sí**
existe y que **sí** tiene dos consumidores posibles: bajar bytes de SharePoint, S3
o SFTP le sirve igual a `gonogo`. La separación entre los dos es real y no de
etiqueta: un `DataSource` dice **de dónde salen los bytes**; un `EntityAdapter`
dice además **qué son** —verdad, glosario, estratos, licencia, privacidad—, y eso
último sólo significa algo dentro de un banco documental.

**Lo que sí se comparte es el apretón de manos de versión.** `benchcore_api` se
declara igual que en cualquier plugin, como manda §7.1, para que el día que el eje
crezca los adaptadores ya digan contra qué contrato se escribieron. Que el eje no
se comparta no quiere decir que la convención tampoco: ver [ADR-0036](0036-el-descubrimiento-de-adaptadores-de-entidad-es-de-docbench.md).

## Alternativas descartadas

**Añadir `"entidad"` al `Literal` de `Capabilities.axis`.** Es una línea en otro
repo y es la salida fácil. Descartada por dos motivos, y el segundo es peor que el
primero: crea un eje con un único consumidor —lo que este ADR decide no hacer—, y
**obliga a todo adaptador de entidad a implementar `capabilities()` y `probe()`**,
dos métodos que §7.1 no pide. Sobre una carpeta de PDFs, `probe()` es
`os.path.isdir` y `capabilities()` es un objeto ceremonial que se rellena para
pasar el aro. Los siete métodos pasarían a nueve por una razón de catálogo, y el
adaptador más importante del proyecto —el que convierte esto en herramienta— sería
el que peor encaja.

**Envolver `EntityAdapter` en un `Plugin` que lo adapte.** Un *shim* que expone
`capabilities()` y `probe()` sobre el adaptador real. Descartada: dos nombres para
una cosa, y la suite de conformidad tendría que decidir a cuál de los dos aprieta.

**Aplazar la decisión y escribir el `Protocol` «provisional».** Descartada: en L13
habría dos adaptadores reales escritos contra él. Un contrato provisional con
implementaciones vivas es un contrato definitivo con mala documentación.

## Trade-off

Lo que se paga: un adaptador de entidad **no aparece en `benchcore.conform.check`**,
así que la conformidad de forma hay que escribirla aquí —`entity.conformance`, que
es trabajo de este mismo hito— y no se hereda gratis lo que `benchcore` mejore en
su suite. Y si algún día `gonogo` necesitara entidades, la migración costaría un
ADR y mover un fichero.

Lo que se compra: los siete métodos son **exactamente** los que §7.1 pide, sin dos
métodos de ceremonia; el contrato se mueve al ritmo de su único consumidor, que es
quien lo prueba; y no se sube el mayor de `API_VERSION` de un repo compartido por
algo que sólo usa uno.

Se acepta el cambio de dirección: **mover un `Protocol` con dos implementaciones
es barato; desmontar un eje compartido mal puesto, no.**

## Cómo se verifica

Un test de la puerta fija la premisa, no la conclusión:
`test_el_eje_de_entidad_sigue_sin_existir_en_benchcore` comprueba que el `Literal`
de `Capabilities.axis` **no** contiene `"entidad"`. El día que `benchcore` lo
añada, el test se pone rojo y este ADR se revisa **con el hecho delante**, en vez
de quedarse escrito con un argumento que ya no describe la realidad.

Y el contrato de capas hace lo suyo: `entity` está por encima de `core`, así que el
núcleo no puede importar el `Protocol` ni nada que dependa de él.

## Consecuencias

- `entity/base.py` declara un `Protocol` nativo y **no** importa
  `benchcore.contracts`. Sí importa `benchcore.types` para `LicenseDecl` y
  `PrivacyDecl`, que son tipos de datos compartidos y no ejes.
- Todo adaptador de entidad declara `benchcore_api` igual que un plugin.
- La conformidad de entidad es de este repo (§14), y correrla es obligatorio por
  adaptador.
- **El descubrimiento de adaptadores de entidad pasa a ser problema de
  `docbench`**, que es la consecuencia directa y tiene su propio ADR: el 0036.
