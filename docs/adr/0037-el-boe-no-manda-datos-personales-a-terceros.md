# ADR-0037 · El BOE declara `may_send_to_third_party: false`, y la decisión se revisa en L12

**Fecha:** 2026-08-24 · **Estado:** aceptada en L3, **se revisa en L12**.
No contradice el manual: §8.3 ya dice qué pasa con `false`. Decide **el valor** del
perfil del BOE y **por qué el restrictivo es el que va por defecto**

## Contexto

`entities/boe.yaml` nació con el campo en `true`, apoyado en un argumento que
resuelve **media** pregunta: el BOE es información publicada oficialmente y su
licencia autoriza expresamente la reutilización comercial, la copia y la obra
derivada (ADR-0031, con las tres fuentes citadas literalmente).

**El problema es que el campo mezcla dos preguntas distintas, y esa licencia sólo
contesta una:**

| | La pregunta | ¿Quién la contesta? |
|---|---|---|
| **(a)** ¿permite **la fuente** que se retransmita el documento? | la licencia del BOE: **sí** | el organismo, por escrito y con fecha |
| **(b)** ¿tiene **el operador** base legal para *ese* tratamiento concreto —mandar datos personales a un tercero, quizá fuera de la UE—? | **nadie, en este repo** | el responsable del tratamiento, y depende de quién trate y desde dónde |

**«Publicado oficialmente» no es consentimiento para cualquier tratamiento
posterior.** Que un dato sea público no convierte en lícito cualquier uso que se le
dé después: la licencia habla del documento, no de los datos personales que lleva
dentro, y la base legal de (b) es del responsable —quien monta la campaña— y cambia
con la jurisdicción, el proveedor y el destino de los datos. El BOE declara nombres
y documentos de identidad parciales en resoluciones, nombramientos y edictos: eso
está en el perfil y no es discutible.

## Decisión

**`may_send_to_third_party: false` en `entities/boe.yaml`. Y se revisa en L12.**

Sin respuesta a (b), **el valor por defecto es el restrictivo**. No porque la
respuesta sea que no, sino porque **nadie la ha contestado**, y un `true` puesto
por defecto convierte una pregunta abierta en un permiso silencioso.

**Y lo decisivo, que es lo que hace la decisión barata:** §16 pone en **L5 ocho
extractores LOCALES** y los **VLM por API en L12**. Así que **de L3 a L11 este
`false` no quita absolutamente nada** — ni un número, ni un extractor, ni una fila
de la tabla. El coste de elegir el lado seguro es, hoy, cero.

**Y se gana algo que no es cero:**

- **La ruta de rechazo se EJERCITA durante ocho hitos** en vez de ser código muerto
  que nadie sabe si funciona. Es la regla que este repo ya aplica a sus barreras: *una
  barrera que nunca se dispara no se sabe si funciona*, y aquí lo dispara el perfil
  real de la entidad de referencia, en la puerta, en cada corrida.
- **L12 llega con la decisión viva y con el caso delante** —qué proveedor, qué
  destino, qué encargado de tratamiento— en vez de heredar un `true` que alguien
  puso en agosto y que ya nadie recuerda por qué.

## Alternativas descartadas

**Dejarlo en `true` con una nota.** Es lo que había. Descartada por lo de arriba y
por una razón de forma: una nota en un YAML no la lee quien monta una campaña dos
hitos después. Un `false` que bloquea, sí.

**Partir el campo en dos** —uno para (a) y otro para (b)—. Es lo correcto de
verdad, y **no se puede hacer aquí**: `PrivacyDecl` es de `benchcore`, o sea otro
repo y otro contrato, y cambiarlo con un solo consumidor es exactamente lo que
ADR-0035 decide no hacer. Queda como **límite 61**, que es lo que corresponde a una
cobertura que falta: declarada, con su tamaño, y sin promesa.

**Esperar a L12 para decidir.** Descartada porque el campo tiene que valer algo
*hoy*: el perfil se escribe en L3 y lo hereda todo lo que venga detrás. Aplazar la
decisión es tomarla, y en la dirección permisiva.

## Trade-off

Lo que se paga: **en L12 hay que hacer el trabajo de verdad** —evaluar la base
legal, el encargado de tratamiento y las transferencias internacionales— o publicar
la frontera de Pareto sólo con extractores locales, que sería una frontera con la
mitad de los puntos. Y cualquiera que hoy monte una campaña sobre el BOE pidiendo
un extractor por API **no arranca**, aunque su caso concreto fuera lícito.

Lo que se compra: que la respuesta a (b) se dé cuando haya que darla y por quien
tiene que darla, y que hasta entonces el proyecto no afirme con su configuración
algo que no ha comprobado.

## Cómo se verifica

`tests/unit/test_policy.py`, en la puerta y en las dos direcciones:

- `test_el_perfil_real_del_boe_rechaza_hoy_un_extractor_por_api` carga
  **`entities/boe.yaml` tal cual** y exige que el campo siga en `false` y que la
  puerta lance. Si alguien lo pone en `true` sin pasar por aquí, se cae y le manda
  a leer este ADR.
- Los otros cinco cubren la dirección contraria: con la fuente cerrada y ocho
  extractores locales la campaña **arranca**, y con la fuente abierta el extractor
  por API **pasa**. Una puerta que bloqueara siempre dejaría a L5 sin poder medir.

`PolicyViolation` sale con **código 2**, no con el 1 genérico: *«la campaña no
arrancó por política»* y *«la medición salió peor de lo tolerado»* exigen dos
reacciones distintas.

## Consecuencias

- Nace `src/docbench_es/core/policy.py`, la puerta de egress, **pura**.

  **Y con hito, no con un «cuando exista».** §16 pone ese motor en
  `benchcore.core.policy` y lo cablea L8; ese módulo no existe (deuda 1). La
  primera versión de este ADR decía *«cuando exista, L8 pasa a llamarlo»*, y eso
  **no es un plazo**: nada haría que existiera, y el final probable es que L8 vea
  que el de `docbench` funciona, no lo mueva, y el manual quede divergiendo en
  silencio. Así que se elige:

  > **L8 incluye EN SU ALCANCE mover este módulo a `benchcore.core.policy`**, con
  > su suite, subiendo el **menor** de `API_VERSION`, y dejando aquí la llamada.
  > **Precio: ~1 h 30 min**, y el rango de L8 pasa de 10-12 h a **11-14**: un
  > cambio en otro repositorio tiene ida y vuelta, y eso también se paga.

  **Por qué (a) y no «se queda aquí para siempre y se corrige §16».** Los tipos
  sobre los que decide —`PrivacyDecl`, `LicenseDecl`— **ya viven en `benchcore`**.
  Una puerta que opera enteramente sobre tipos compartidos no es de un consumidor:
  la regla espejo de ADR-0035 apunta al otro lado esta vez, y el manual ya lo tenía
  puesto donde toca.
- El perfil del BOE queda **cerrado a terceros** hasta que L12 diga otra cosa.
- **`cargar_perfil` invierte el defecto del contrato**: `PrivacyDecl` trae
  `True` y el cargador de perfiles pone `False` cuando el campo falta. Un
  perfil que se olvida del campo no ha dicho que sí: no ha dicho nada, y con
  el defecto permisivo la forma más fácil de abrir el egress de una entidad
  sería **olvidarse de declararlo**. Tiene su test.
- Queda escrito que el campo **mezcla dos preguntas**: límite 61.
- **En L12, este ADR se revisa con nombre y apellidos.** Si la respuesta es que sí,
  se sustituye con su fecha y su razón; si es que no, la frontera de Pareto se
  publica sólo con local y **se dice por qué**.
