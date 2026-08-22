# ADR-0014 · Los mapas del modelo de datos son `Mapping` de solo lectura

**Fecha:** 2026-08-22  ·  **Estado:** aceptada, implementada y **transcrita al
manual** (§6, §6.8) el 22 ago 2026, al escribirse la regla de oro 8

## Contexto

§6.8 del manual declara los campos de agregado como `dict[...]`: `level1`,
`level2`, `level3`, `costs`, `failures`, `by_verifier`, `confusion_rate`,
`per_document`, `by_stratum`, `summary`, `when`, `measured`. Todas las estructuras
de §6 son `@dataclass(frozen=True)`, y `tests/unit/test_types.py` tiene un test
—`test_todo_el_modelo_de_datos_es_inmutable`— cuyo docstring afirma que eso
*"demuestra que un resultado no se puede mutar DESPUÉS de medirlo"*, y que es
*"la base de que `substance_hash` y `plan_hash` signifiquen algo"*.

**La afirmación era falsa.** `frozen=True` solo impide reasignar un atributo; no
dice nada del contenido. Comprobado en el escrutinio adversarial de cierre de L0:

```python
m = StructureMetrics(..., failures={"timeout": 1}, ...)
m.failures["timeout"] = 999
m.failures["inventado"] = 42       # -> {'timeout': 999, 'inventado': 42}
```

Y casi todo lo publicable de §6.8 vive en un mapa, o sea justo los números. Un
`CampaignResult` "congelado" se podía reescribir entero sin tocar un solo
atributo, con lo que `substance_hash` dejaba de atar el número publicado a lo que
de verdad se midió. En un repo cuya regla de gobierno es *lo que el proyecto
afirma y el código no cumple es el fallo más grave posible*, un test que afirma
algo falso es peor que no tenerlo: da cobertura aparente a la propiedad que más
sostiene la credibilidad de los resultados.

Un segundo defecto del mismo sitio: `failures: dict[str, int]`. El enum
`ExtractionFailure` es **cerrado** por la regla de oro 6 —ningún fallo puede
registrarse como "otro" y desaparecer del informe—, pero tipado con `str`,
`{"lo_que_sea": 3}` pasaba `mypy --strict` sin una queja, precisamente en la
estructura cuyo contenido se publica como tasa de fallo por causa.

## Decisión

Los campos de mapa del modelo de datos se anotan **`Mapping[K, V]`**, no
`dict[K, V]`, y cada dataclass que tenga alguno recibe un `__post_init__` que los
sustituye por una vista de solo lectura:

```python
def congelar_mapas(obj: object) -> None:
    for campo in dataclasses.fields(obj):
        valor = getattr(obj, campo.name)
        if isinstance(valor, dict):
            object.__setattr__(obj, campo.name, MappingProxyType(dict(valor)))
```

Vive en `docbench_es.types._inmutable` y se llama desde los nueve `__post_init__`
del paquete. El `dict(valor)` de dentro no es redundante: `MappingProxyType` es
una **vista**, no una copia, así que sin él quien conservara la referencia al
diccionario de construcción seguiría pudiendo mutar el resultado por la espalda.

Y `failures` pasa a `Mapping[ExtractionFailure, int]`, con el `Literal` cerrado
como clave.

## Alternativa descartada

**Dejar `dict` y corregir solo el docstring del test**, rebajando lo que afirma a
"no se puede reasignar un atributo". Se descarta porque la afirmación fuerte —un
resultado no se muta después de medirlo— **no es cosmética**: es la premisa de
`substance_hash` y `plan_hash`, y por tanto de que dos corridas con la misma
semilla se puedan comparar. Rebajar la afirmación habría dejado el repo honesto y
el invariante roto; era preferible cumplir la afirmación.

También se descartó **`frozendict` como dependencia**: `MappingProxyType` es de la
biblioteca estándar y hace lo mismo para este uso, y este proyecto añade
dependencias solo cuando aportan algo que la estándar no da.

## Trade-off

**Se pierde la correspondencia literal con los tipos de §6.8**, que dice `dict`.
El coste es real pero acotado: `Mapping` es el supertipo, así que todo consumidor
que solo lea sigue valiendo sin cambios, y quien construya sigue pasando un `dict`
normal. Lo que deja de compilar es el `resultado.failures[k] = v`, que es
exactamente lo que se quería impedir.

El coste que sí hay que declarar: **mypy ahora rechaza en análisis** código que
antes solo fallaba en runtime, y eso incluye código legítimo que quiera construir
un agregado por acumulación. La forma correcta pasa a ser acumular en un `dict`
local y pasarlo al constructor al final, no mutar el campo del resultado.

## Cómo se verifica

Tres tests en `tests/unit/test_types.py`:

- `test_los_mapas_de_un_resultado_tampoco_se_pueden_mutar` intenta las dos
  mutaciones y espera `TypeError`, y además comprueba que mutar el `dict`
  original de construcción **no** cambia el resultado.
- `test_el_agregado_de_fallos_solo_admite_causas_del_enum_cerrado` fija que
  `failures` va tipado con `ExtractionFailure` y no con `str`.
- `test_todo_el_modelo_de_datos_es_inmutable` sigue cubriendo la mitad que da
  `frozen`, ahora con un recuento exacto (`== 28`) en vez de un suelo holgado.

## Consecuencias

- Un campo de mapa nuevo en el modelo de datos se anota `Mapping[...]` **y** su
  dataclass llama a `congelar_mapas` en su `__post_init__`. Si no, el mapa queda
  mutable y la afirmación del test vuelve a ser falsa para ese campo.
- Las estructuras de §6 siguen sin ser hashables: un `Mapping` no lo es, igual que
  no lo era un `dict`. Esto no cambia respecto a antes.
- **Este ADR no cierra el problema de los intervalos.** Que `StructureMetrics`
  tenga un solo `ci` para cuatro estimadores y que le falte el desglose por
  estrato es un defecto distinto del mismo §6.8, y está declarado como límite 29
  de `LIMITS.md` con su hito (L5) y su precio. Se separa a propósito: cambiar la
  *forma* de los tipos no exige consumidor, y cambiar *qué números se publican*
  sí.
