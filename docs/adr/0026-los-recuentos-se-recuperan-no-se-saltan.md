# ADR-0026 · Una corrida parcial no salta la comprobación de recuentos: la recupera

**Fecha:** 2026-08-23 · **Estado:** aceptada, implementada y con su mutante.
**No toca el manual**: es una decisión sobre la suite de tests, no sobre el modelo
de datos ni sobre ninguna métrica publicada

## Contexto

`tests/unit/conftest.py` calcula los recuentos volátiles del repo —mutantes, tests
dentro y fuera del arnés, total— en `pytest_collection_modifyitems`, y
`test_recuentos.py` comprueba que todo documento publicado que los cite coincida.

**Esos números salen de lo COLECTADO.** Con `pytest tests/unit/test_recuentos.py`
la colección son 11 tests: `dentro=0`, `total=11`. Cifras ciertas sobre esa
corrida y **falsas sobre el repo**. La primera versión las usaba igual, y el
resultado fue el peor de los posibles:

```
uv run pytest tests/unit/test_recuentos.py
FAILED test_la_comprobacion_se_cae_con_una_cifra_desincronizada
  'inventado.md: «0 de 5 tests» pero dentro es 0'
```

**Un rojo que habla de una desincronización que no existe.** Y encima se rompía
solo: el propio texto que el test se construye —el que dice cuántos tests cubre el
arnés, con esas cifras degeneradas dentro— caía en un patrón laxo,
`0 (?:muertes )?de {_N} tests`, escrito para el control negativo del arnés de
mutantes pero que casaba con cualquier «0 de N tests». Capturaba el segundo número
como si fuera `dentro`. La precondición «esto exige la suite entera» no estaba
declarada en ningún sitio.

> **Nota sobre cómo está escrito este ADR.** La frase de arriba iba primero con la
> cita literal, y **la propia comprobación la rechazó**: leyó el ejemplo como una
> afirmación sobre el repo de hoy. Es fricción real y es deseable — obliga a que
> una cita ilustrativa se distinga de una afirmación vigente, en vez de meterla en
> la lista de excepciones, que está reservada a cifras **superadas** y no a
> ejemplos.

Lo encontró la auditoría en frío de `b7cc6c3`.

## Decisión

**Cuando la colección es parcial, los recuentos se RECUPERAN**, con un
`--collect-only` de `tests/unit` en un subproceso. **233 ms medidos**, mediana de
5. Así el guardián vive en **todas** las corridas y la precondición desaparece en
vez de declararse.

Y el coste se paga donde no molesta: **sólo cuando la selección incluye estos
tests**. Si `-k` los deselecciona, no llegan a ejecutarse y el subproceso no se
lanza — comprobado, `pytest tests/unit/test_errors.py` sigue costando 0,08 s.

**Los recuentos recuperados pasan por `exigir_sano()`** antes de que nadie compare
nada. Son invariantes estructurales, no umbrales inventados: `total == dentro +
fuera`, `mutantes >= 1`, `dentro >= 1`, `fuera >= 1`. Un recuento degenerado **no
es un desacuerdo**: es que no hay medición, y decir «no hay medición» tiene que
sonar distinto de decir «el documento está mal». Es la misma distinción que
`matar.py` ya hacía cuando pytest no recoge ni un test.

## Alternativas descartadas

**(a) Saltar la comprobación si la corrida es parcial**, con un `pytest.skip` que
explique por qué. Es lo que hacía la versión intermedia, y funciona. Se descarta
porque **un guardián que se salta es un guardián muerto en todo contexto que no
sea CI**: el desarrollador que corre `pytest -k recuentos` mientras toca justo
este fichero es quien más lo necesita, y es a quien se le saltaría. Y la
mitigación —comprobar que CI siempre corre la suite entera— sigue haciendo falta
igual, así que saltar no ahorra trabajo, sólo cobertura. *Esa mitigación se ha
implementado de todos modos*: `test_el_guardian_corre_donde_importa_y_no_solo_
donde_se_le_llama` lee el `Makefile` y `fast.yml` y se cae si la puerta deja de
correr `tests/unit` entero o si CI deja de llamar a `make fast`.

**(b) Fallar con «esta comprobación exige la suite entera».** Es honesto y por eso
era tentador. Se descarta porque **pone rojo el desarrollo normal**, y un rojo que
no es un bug enseña a ignorar el color — que es exactamente el argumento del
límite 25 de este repo para que `full` y `nightly` nacieran dormidos en vez de
rojos. Un candado que da rojos falsos deja de leerse, y entonces no guarda.

**Recolectar SIEMPRE en subproceso, también en las corridas completas.** Costaría
233 ms en cada `make fast` a cambio de nada: cuando la colección es completa los
números ya son exactos y gratis.

## Trade-off

Lo que se paga: **el test lanza un subproceso**, que es más maquinaria que un
`skip` de una línea, y depende del formato `fichero.py: N` de `pytest -q
--collect-only`. Si ese formato cambia, el parseo devuelve cero ficheros — y
entonces **no se cuenta cero en silencio**: se lanza `RecuentoDegenerado` con el
`rc` y la salida del subproceso, porque una medición que no se hizo no puede
parecerse a una que salió vacía.

Lo que se compra: que la comprobación no tenga precondición. No hay una forma de
invocar la suite que la deje sin efecto, y por tanto no hay que acordarse de nada.
