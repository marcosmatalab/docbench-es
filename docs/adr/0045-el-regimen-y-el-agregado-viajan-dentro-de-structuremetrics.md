# ADR-0045 · El régimen y el agregado viajan DENTRO de `StructureMetrics`

**Fecha:** 2026-08-27 · **Estado:** aceptada e implementada. **Toca el manual**: cambia
§6, transcrito en este mismo commit

## Contexto

`StructureMetrics` se declaró en L0 y **nadie lo ha producido nunca**. Su primer
consumidor es el nivel 1 de L5, y por tanto es el cuarto candidato al patrón que
`ESTADO.md` lleva prediciendo desde L1: *«el hito que ESCRIBE un módulo no encuentra los
bugs que encuentra el que lo CONSUME»*. Con `from_html`, `from_dataframe` y
`from_markdown` van tres de tres. Éste hace cuatro.

Al mirarlo antes de escribir el productor aparecieron **dos defectos**, y los dos son de
la familia que este repo persigue: **un número cuyo denominador o cuyo régimen no viaja
en el artefacto**.

## Defecto 1 · `ci` era obligatorio sobre una población que es un censo

```python
ci: tuple[float, float]      # sin `| None`
```

ADR-0015 dice que **toda estimación lleva su intervalo**, y su corolario —aplicado ya
cinco veces en `RESULTS.md`— es que **un censo no es una estimación y va sin intervalo**.

`runs/l5/poblacion.yaml` congela que la población de L5 es **mixta**:

| población | n | régimen |
|---|---|---|
| con tabla | 338 | **censo** |
| sin tabla, `<=10` | 200 de 584 | **muestra**, Wilson |
| sin tabla, `11-50` | 72 | **censo** |
| sin tabla, `>50` | 6 | **censo** |

Las métricas de estructura —TEDS, TEDS-S, `cell_f1`— se calculan **sólo sobre los 338**,
que es un censo. Así que el tipo **obligaba a poner un intervalo sobre un número que la
propia regla del repo prohíbe que lo lleve**, y dejaba dos salidas y las dos malas:
inventar un `(x, x)` —publicar un IC degenerado— o quitar el intervalo de donde sí hace
falta.

**Y hay un tercer defecto dentro del primero, que ninguno de los dos había nombrado: un
solo `ci` para cuatro números.** El campo no decía a cuál de `teds`, `teds_s`, `cell_f1` o
`evaluable_coverage` pertenecía. Un intervalo sin dueño no es mejor que ninguno.

## Defecto 2 · `teds` no decía cuál de los tres agregados era

`runs/l5/ponderacion.yaml` decidió —**antes de medir**— que hay **tres** agregados
posibles y que dan **tres números distintos**:

* por documento: los 38 largos pesan el 3,8%;
* ponderado por página: pesan el 36,6%;
* por tabla: cada tabla pesa igual, venga de donde venga.

Los tres son legítimos. Un `teds=0,87` publicado sin decir cuál **es el 2.283 otra vez**:
un número cuyo denominador no vive en el artefacto que lo transporta.

Y `n_documents` tenía el mismo problema en pequeño: 338, no 616 ni 1.000, y tiene que
salir del censo y no de teclearlo.

## Decisión

`StructureMetrics` gana **dos campos declarativos**, `ci` pasa a opcional, y un
`__post_init__` ata el régimen al intervalo **en las dos direcciones**:

```python
regimen: Regimen        # "CENSO" | "MUESTRA"
agregado: Agregado      # "POR_DOCUMENTO" | "PONDERADO_POR_PAGINA" | "POR_TABLA"
ci: tuple[float, float] | None
```

* **`MUESTRA` sin `ci` no se construye.** Es la regla de oro 2 hecha código.
* **`CENSO` con `ci` tampoco.** Sin esta dirección, el `None` sería ambiguo: *«no llevaba
  intervalo»* y *«se me olvidó»* se leen igual, que es lo que el usuario señaló.
* **El `ci` es el de `teds`**, y se dice: es el agregado primario, y los demás campos no
  llevan intervalo hasta que alguien los necesite y lo declare.

Es exactamente el mismo mecanismo que `Extraction.__post_init__` usa para atar `failed` a
`failure_reason`: **no se puede construir el objeto incoherente**, así que no hay que
acordarse de comprobarlo después.

## Alternativas descartadas

**Dejar `ci` obligatorio y publicar `(x, x)` sobre el censo.** Es la salida barata y es la
peor: un lector que ve un intervalo asume que hay incertidumbre muestral, y aquí no la
hay. Publicar un IC degenerado es peor que no publicar ninguno, porque el degenerado
**miente sobre la naturaleza del número**.

**`ci: tuple[float, float] | None` a secas, sin `regimen`.** Era la opción mínima y no
basta, por la razón de arriba: un intervalo ausente y uno olvidado son indistinguibles. El
campo que declara el régimen es lo que convierte el `None` en una afirmación.

**Un `StructureMetrics` por régimen —dos tipos—.** Duplicaría los cuatro campos de métrica
para cambiar uno, y `CampaignResult.level1` es un `dict[str, StructureMetrics]`: habría
que partirlo también. La declaración dentro del objeto cuesta dos campos y no parte nada.

**Desdoblar `teds` en tres campos —uno por agregado—.** Obligaría a calcular los tres
siempre, y `ponderacion.yaml` ya decidió cuál es el primario y que los demás se publican
al lado **si son baratos**. Un tipo que obliga a calcular lo que no se ha decidido calcular
es un tipo que empuja a rellenar con ceros.

## Lo que esto NO resuelve, y va dicho

**La tasa de falso positivo de detección** —los 662 sin tabla, con su muestra de 200 y su
intervalo de Wilson— **no es un `StructureMetrics`**. Tiene otro denominador, otra
población y otras columnas. Este ADR no le da sitio: se lo dará el informe de nivel 1, y
mientras tanto queda escrito aquí para que no se cuele dentro de este objeto por parecerse.
