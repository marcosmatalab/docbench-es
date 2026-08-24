# ADR-0036 · El descubrimiento de adaptadores de entidad es de `docbench`: grupo propio, mecánica prestada

**Fecha:** 2026-08-23 · **Estado:** aceptada en L3, **implementada en L3**.
Consecuencia directa de [ADR-0035](0035-entityadapter-es-nativo-de-docbench.md).
Transcrito al manual en el mismo commit: §8 (`entity/registry.py`)

## Contexto

ADR-0035 decide que `EntityAdapter` no es un eje de `benchcore`. La consecuencia
que hay que sacar en el mismo hito, porque el `Protocol` **se publica hoy**:
**si un adaptador de entidad no pasa por `benchcore.registry`, ¿quién lo
descubre?**

No es una pregunta teórica ni aplazable:

- **L13, segunda entidad real, es REQUISITO y no opcional**, y §16 dice que es *«la
  única prueba de ADR-0001»* —que la interfaz aguanta sin tocar el motor—. Esa
  prueba consiste precisamente en registrar un adaptador que el motor no conoce.
- **`generico_pdf`** (ADR-0032) es lo que convierte esto en herramienta, y necesita
  la misma vía.
- Y §13.1 vende exactamente eso para extractores: *«entra por entry point, pasa la
  suite de conformidad, y aparece en la tabla»*. Venderlo para extractores y no
  tenerlo para entidades sería una promesa a medias.

Sin vía de registro, en L13 se descubre que el contrato publicado no tiene por
dónde entrar, y para entonces hay adaptadores escritos contra él.

**El hallazgo que decide la forma:** `benchcore.registry.discover(group)` **no
comprueba el eje, ni exige `Plugin`, ni llama a `capabilities()`**. Hace tres
cosas: recorre un grupo de entry points, carga, y exige `benchcore_api` con mayor
compatible. Es decir: **el eje no se comparte, pero el apretón de manos de versión
sí, y es reusable tal cual.**

## Decisión

**El descubrimiento de adaptadores de entidad lo hace `docbench`, en
`entity/registry.py`, sobre un grupo de entry points propio.** Seis puntos:

**1 · Grupo propio: `docbench.entity`.** Ya estaba declarado en `pyproject.toml`.
Un adaptador de fuera se registra igual que un extractor de fuera —una línea en su
`pyproject`— y el camino propio y el ajeno son **el mismo camino**. Es lo que dice
el docstring de `benchcore.registry` y es lo que hace verificable la
extensibilidad: si hubiera un atajo privilegiado, la suite sólo probaría el que
nadie de fuera usa.

```toml
# pyproject.toml de quien trae su entidad
[project.entry-points."docbench.entity"]
mi-organismo = "mi_paquete.bench:MiAdaptador"
```

**2 · Se reusa `benchcore.registry.discover`, no se copia.** `entity/registry.py`
es una capa fina encima. **Una sola convención**, no dos que divergen: el día que
`benchcore` endurezca el chequeo de versión, aquí se endurece solo.

**3 · Falla CERRADO, en carga.** Un entry point que no se puede importar, o que no
declara `benchcore_api`, o que declara un mayor incompatible, **aborta el
descubrimiento con su causa**. Nunca a mitad de campaña. Saltárselo en silencio
produciría una campaña con menos concursantes de los que el informe afirma, que es
la regla de oro 6 rota por omisión.

**4 · Traduce los errores; no amplía la jerarquía.**
`benchcore.errors.ContractViolation` e `IncompatibleApi` se relanzan como
`docbench_es.errors.ContractViolation` —código de salida **5**— con `from exc`. Si
la de `benchcore` escapara, **un `except DocbenchError` no la vería** y la CLI
saldría con traza en vez de con su código. Y no se añade un séptimo código: §11
tiene seis y una incompatibilidad de versión **es** una violación de contrato.

**5 · Descubrir no construye.** El registro devuelve **lo que carga el entry
point** —la clase, no una instancia—. Es la misma regla que *«`discover` no
descarga»*: `docbench entity list` no puede abrir ficheros, leer YAML ni tocar la
red. Además, una instancia necesita su `PerfilEntidad`, y el perfil es de quien
monta la campaña, no del catálogo.

> **La consecuencia dura, y está comprobada ejecutándola:** `benchcore_api` tiene
> que ser **atributo de clase**. Un adaptador que lo asigne en `__init__`
> **no llega a cargarse**: en carga no hay instancia, así que el registro no ve
> versión ninguna y lo rechaza por *«no declara `benchcore_api`»*. Falla cerrado
> —que es lo correcto— pero **el mensaje habla de una versión ausente y no de la
> que el adaptador creía declarar**, y quien lo escribió puede tardar un rato en
> entender por qué. Por eso entra en la suite de conformidad como comprobación
> explícita: el fallo es confuso, no silencioso.
>
> La única forma de que un `__init__` sirva es que el entry point apunte a una
> **instancia ya construida** en el módulo del plugin. Se desaconseja y no se
> prohíbe: construirla al importar mete E/S en el catálogo, que es justo lo que el
> punto 5 evita.

**6 · Dónde va la puerta de política, que no es aquí y hay que decirlo.** §14 y
§19 dicen que *«el registro rechaza»* un adaptador con `special_categories: true`,
y HITOS lo pone en **L8** como test hostil obligatorio. Ese rechazo necesita la
`PrivacyDecl`, que vive en el **perfil**, no en la clase — y por el punto 5 aquí no
hay instancia ni perfil. Así que la comprobación va **donde el adaptador se
construye con su perfil**, y su hito es **L8 · Política**, precio **~1 h** con su
test hostil en `tests/hostile/`. Lo que queda fijado hoy es de quién es esa puerta:
**de `docbench`**. `benchcore.registry` no sabe qué es una `PrivacyDecl`, y no
debe saberlo.

**Y un hallazgo de paso, que el fallo cerrado convierte en bloqueante.**
`pyproject.toml` declaraba entry points apuntando a módulos **que todavía no
existen**: `boe` y `generico-pdf` en `docbench.entity`, y `oracle`,
`pymupdf4llm` y `docling` en `docbench.extractor`. Comprobado ejecutándolo: los
cinco dan `ModuleNotFoundError`. Con fallo cerrado —que es lo correcto— **la
primera llamada a `descubrir()` reventaba antes de encontrar nada**. Se retiran las
cinco líneas y **cada una vuelve con su fichero**, en su hito. Declarar un
concursante que no existe es exactamente la clase de afirmación que este repo no
puede permitirse.

## Alternativas descartadas

**Copiar la mecánica de `benchcore.registry` aquí (unas 70 líneas).** Es lo que
parecía «tener registro propio». Descartada: dos implementaciones del mismo
apretón de manos divergen, y quien traiga un adaptador tendría que aprender dos
convenciones para dos grupos del mismo proyecto.

> **El riesgo que se acepta al reusar, escrito porque es real:** si `benchcore`
> metiera un `isinstance(plugin, Plugin)` dentro de `discover()`, los adaptadores
> de entidad dejarían de cargar. Por eso el test registra un adaptador falso **por
> el camino real**: ese día el rojo sale en la puerta, no en L13.

**Descubrir por convención: escanear `docbench_es/entity/*.py`.** Descartada, y es
la peor de las tres: los adaptadores de fuera **no viven en este paquete**, que es
justo el caso que L13 tiene que probar. Funcionaría para los propios y fallaría
exactamente donde importa.

**Aplazarlo a L5 o a L13, apuntándolo como deuda.** Descartada por la regla de oro
8 aplicada a código: el `Protocol` se publica hoy, y publicar un contrato sin vía
de registro es publicar media promesa. El coste hoy son ~40 líneas y un test; en
L13, cambiar una interfaz con implementaciones vivas.

## Trade-off

Lo que se paga: `docbench_es.entity` **depende ahora de `benchcore.registry`**, o
sea que una regresión en otro repo puede poner roja la puerta de éste. Y el
proyecto expone **dos grupos** de entry points que quien integra tiene que
distinguir (`docbench.extractor` y `docbench.entity`).

Lo que se compra: dos grupos, **una sola convención**; el rechazo por versión
ocurre en carga y no a mitad de campaña; y L13 —la única prueba de ADR-0001— tiene
por dónde entrar el día que empiece, en vez de descubrir que no la tiene.

## Cómo se verifica

`tests/unit/test_entity_registry.py` registra un adaptador falso **escribiendo
una distribución falsa** —`dist-info` con su `entry_points.txt`— en un directorio
temporal e insertándola en `sys.path`. Es el camino real de `importlib.metadata`,
**no** un `monkeypatch` de `entry_points`: parchear la función probaría el parche.
Comprueba cuatro cosas, todas sin red y en la puerta:

1. el adaptador falso —el de carpeta de ADR-0032— **se descubre** por su grupo, y
   lo que se descubre es **la clase**. Que además **pase la suite de conformidad**
   se comprueba en `test_entity_conformance.py`, que cierra el círculo: el
   registro entrega algo que el motor sabe usar, no sólo algo que carga;
2. uno que **no declara** `benchcore_api` se rechaza **en carga**;
3. uno que declara un **mayor incompatible** (`"2.x"`) se rechaza en carga;
4. lo que se lanza es un `DocbenchError` con `exit_code == 5` —y sigue siendo un
   `BenchcoreError`—, no una excepción que se escape del `except` del motor;
5. y **el descubrimiento no construye**: el falso `ConstruirTocaElMundo` lanza en
   su `__init__`, así que si el registro instanciara lo que carga, el test se
   caería con esa excepción.

## Consecuencias

- Nace `src/docbench_es/entity/registry.py`. **`base.py` no crece**: el manual
  decía *«el Protocol y el registro»* en un solo fichero y se transcribe en este
  mismo commit, porque `base.py` está en 268 líneas y el límite del repo son 300.
- Queda **prohibido instanciar un adaptador durante el descubrimiento**.
- Queda **prohibido** declarar un entry point cuyo módulo no existe: con fallo
  cerrado, rompe el descubrimiento entero de su grupo.
- `benchcore_api` como atributo de clase pasa a ser parte del contrato de entidad,
  y lo comprueba la suite.
- L8 hereda la puerta de política del registro, con su precio puesto arriba.
