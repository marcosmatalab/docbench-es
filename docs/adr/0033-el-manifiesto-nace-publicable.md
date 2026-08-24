# ADR-0033 · El manifiesto nace publicable, y eso es un requisito de diseño

**Fecha:** 2026-08-23 · **Estado:** aceptada. **Amplía §10.4 del manual**, que
define el manifiesto con menos campos de los que hacen falta para publicarlo

## Contexto

**No existe un corpus español de extracción documental con verdad derivada.** El
corpus que construye L3 puede acabar siendo **más útil y más citado que la propia
tabla de resultados** — le pasó a ExtractBench de LlamaIndex, cuyo dataset tuvo
más recorrido que el benchmark.

Y aquí está la asimetría que decide: **publicarlo después es gratis si el
manifiesto nace con lo necesario dentro, y es otro hito si no.** Si falta la
procedencia por documento, reconstruirla obliga a re-cosechar; si los resultados
sólo existen en markdown, publicar un dataset es reescribirlo todo.

§10.4 define el manifiesto con `external_id`, `sha256`, `n_pages`, `strata`, las
dos URLs y `fetched_at`, más un `n_discarded_pairing` total. **Es suficiente para
reproducir la campaña y no para publicar el corpus.**

## Decisión

**La publicabilidad es un requisito de diseño del manifiesto, no una intención.**
Cuatro cosas dentro desde el primer documento:

1. **Procedencia por documento**, no agregada: identificador, **fecha del sumario**,
   **sección**, las dos URLs, `sha256`, y la **fecha de última actualización** que
   exigen las condiciones de reutilización. Sin la fecha de actualización el
   manifiesto no cumple la licencia; sin la sección no se puede re-derivar la
   población del denominador.
2. **La atribución de obra derivada, literal y dentro del manifiesto**: «Basado en
   datos de la Agencia Estatal Boletín Oficial del Estado». No una referencia a
   dónde leerla: el texto.
3. **Licencia del corpus declarada y SEPARADA de la del código.** Son cosas
   distintas y confundirlas es lo que hace impublicable un dataset: el código puede
   ser MIT y el corpus estar sujeto a las condiciones del BOE, que exigen
   atribución.
4. **Los resultados en formato de máquina desde el primer día.** JSON con esquema
   declarado, y el markdown **renderizado a partir de él**. Así publicar una página
   o un dataset es **un paso de renderizado**, no un reescribido.

**Y la tasa de descarte se publica con su ventana y su dispersión, nunca como cifra
única** (ADR-0030): está medido que entre ventanas va de 2,0% a 5,5%, un factor
2,75, así que una cifra sola sería una propiedad del calendario disfrazada de
propiedad del corpus.

## Alternativa descartada

**Publicar el manifiesto mínimo de §10.4 y ampliarlo cuando se decida publicar el
corpus.** Es lo que parece más barato y es lo que cuesta un hito: la fecha de
última actualización y la sección **no se pueden reconstruir sin volver al
origen**, y volver al origen seis meses después no devuelve lo mismo — y evitar
exactamente eso es para lo que el manifiesto existe: §19 del manual lo dice en su
tabla de riesgos, *«el manifiesto con hashes permite reproducir campañas viejas
aunque la fuente desaparezca»*.

> **Corrección, 24 ago 2026.** Esta frase citaba **la decisión número 0029, que
> no existe** —
> comprobado con `git log --all`: nunca estuvo en ningún commit—. La cita se
> sustituye por la fuente que sí dice eso, el manual. Se anota en vez de borrarse
> porque el hueco tenía dos citas colgando y la otra, a `ADR-0030`, obligó a
> escribir el ADR que faltaba.

**Publicar el corpus en L3.** Descartada: no está en el criterio de §16 y mete
decisiones de distribución en un hito que no las necesita. Lo que sí entra es que
**no haga falta re-cosechar** para hacerlo.

## Trade-off

Lo que se paga: el manifiesto es **más grande** y `corpus.manifest` tiene más
campos que validar. Con 1.000 documentos son unos cientos de KB de JSON, que no es
un problema, y unos cuantos campos más de dataclass.

Lo que se compra: que la decisión de publicar el corpus sea **una decisión y no un
proyecto**. Y que el manifiesto cumpla la licencia del BOE por construcción, en
vez de por acordarse.
