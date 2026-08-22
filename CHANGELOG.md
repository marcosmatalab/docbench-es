# CHANGELOG

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado: [SemVer](https://semver.org/lang/es/).

Cada entrada corresponde a un hito de `HITOS.md` y se escribe al cerrarlo con
`/cerrar`. **Los números van en [`RESULTS.md`](RESULTS.md) y el método en
[`docs/metrics.md`](docs/metrics.md), no aquí.** Aquí va qué cambió en cada hito, y
un resumen de las cifras que se retiraron; el historial detallado de correcciones
de cada número vive con su método, en `docs/metrics.md`.

## [No publicado]

### L0 · Esqueleto, canon y contrato de capas · 2026-08-21, cerrado el 2026-08-22

#### Añadido

- **El modelo de datos completo de §6**, en `src/docbench_es/types/`: 32 nombres
  exportados, todos `frozen`. Incluye la forma canónica de tabla, extracción,
  verdad, preguntas, glosario, plan de muestreo, campaña y los agregados de los
  tres niveles.
- **La jerarquía de errores de §6.9**, en `src/docbench_es/errors.py`, con **el
  código de salida de §11 como atributo de clase**: política 2, presupuesto 3,
  infraestructura 4, contrato 5, `TruthUnavailable` 6. Las tres cuyo significado
  coincide con el contrato heredan **también** de la excepción de `benchcore`,
  para que un `except BenchcoreError` del motor cace lo que lance el plugin de un
  cliente.
- **15 tests unitarios** en `tests/unit/`, dos de ellos **property-based** con
  `hypothesis`, que convierten en contrato afirmaciones que hasta ahora solo
  estaban escritas en el manual: que el modelo es inmutable —atributos **y**
  mapas—, que `types` no importa nada del proyecto, que nadie de fuera importa sus
  submódulos privados, que la tabla de códigos de salida es código y no prosa, que
  el enum de fallo de extracción está cerrado y se exige en el agregado, que un
  fallo sin causa no se puede construir, y que **`DocRef.key()` es inyectiva**.
- `docs/adr/0014-mapas-inmutables-en-el-modelo-de-datos.md`.
- `README.md`, `RESULTS.md`, `LIMITS.md`, `CHANGELOG.md` y `LICENSE` (Apache-2.0).
- `docs/reading-order.md` con las rutas de 5 min, 30 min y 2 h.
- `docs/adr/0013-types-como-paquete.md`.
- Los trabajos de CI `full.yml` y `nightly.yml`.

#### Cambiado

- `src/docbench_es/types.py` pasa de fichero a **paquete** `types/` con cinco
  submódulos privados. `docbench_es.types` sigue siendo la única superficie de
  import. Motivo y alternativa descartada en el ADR-0013.
- `full.yml` y `nightly.yml` **nacen dormidos**, con `on: workflow_dispatch:`
  únicamente. Se encienden en L7. Ver el límite 25 de `LIMITS.md`.

#### Eliminado

- `tests/unit/test_humo_unit.py`, el marcador que traía el pack de arranque. Ese
  directorio ya tiene tests de verdad. Los de los otros ocho directorios siguen
  en pie hasta que su hito los sustituya.

#### Corregido en el escrutinio de cierre

El escrutinio adversarial de `/cerrar` sacó 12 hallazgos. Diez se arreglaron, uno
se declaró como límite y uno resultó no reproducirse. Los que cambiaban una
afirmación del repo:

- **`DocRef.key()` colisionaba.** `("an", "boe/A/B")` y `("an/boe", "A/B")` daban
  la misma clave siendo documentos distintos. `key()` es **la unidad de
  remuestreo del bootstrap agrupado**: dos documentos colapsados en una clave
  estrechan el intervalo y publican más precisión de la que hay. Ahora va
  percent-encoded, con test de propiedad.
- **`frozen=True` no congelaba los mapas**, y un test afirmaba que sí. Ver
  ADR-0014.
- **Un fallo sin causa era construible** (`failed=True, failure_reason=None`), y
  `failures` estaba tipado `dict[str, int]`, eludiendo el enum cerrado justo en el
  agregado que se publica. Las dos cosas rompían la regla de oro 6.
- **`cell_at` no declaraba el caso `span < 1`**, en el que la celda desaparece.
- **El README afirmaba en presente cinco mecanismos que no existen** (política,
  motor, CLI, adaptador de entidad). Reescritos en futuro y con su hito.
- **Quince `__init__.py` decían «lo rellena /hito L0»** y L0 los deja vacíos.
  Ahora cada uno nombra el hito real que lo rellena.
- **`LIMITS.md` 19 presentaba L8b como medido**, y está pendiente.
- **`stop-gate.sh` dejaba colar la puerta en rojo**: la marca de caché hasheaba el
  listado de `git status`, no el contenido, así que romper más un fichero que ya
  figuraba como `M` daba la misma huella. Y su detección de congelados no veía un
  fixture aún sin commitear, que es su estado durante todo el hito que lo crea.

#### Verificado, ejecutándolo

**1 · La puerta, en verde y dentro de presupuesto.** `make fast` en **4,43 s** en
el runner de GitHub contra los 90 s de §15, corrida `32572683716` sobre `28186b9`,
el commit que cierra L0. `RESULTS.md` separa ese número del job (11 s) y del run
(15 s), que no son lo mismo, y le pone **rango observado** —que no es un intervalo
de confianza, y así se declara—: **toda corrida cuyo árbol de código sea idéntico**
al del cierre entra en la muestra. Hoy son cuatro —`78ee8f0`, `4e4ea0b`, `28186b9`
y `3a6b9d7`, que sólo se diferencian en markdown— y dan **mínimo 3,41 s, mediana
3,95 s, máximo 4,43 s**, con corte a 22 ago 2026.

**2 · Que `python-version` no hacía nada.** Los tres workflows se lo pasaban a
`astral-sh/setup-uv@v3`, que **no acepta ese input**. Comprobado empujando una
rama con un paso de diagnóstico (corrida `32531009942`):

```console
##[warning]Unexpected input(s) 'python-version', valid inputs are ['version',
  'checksum','github-token','enable-cache',...]
##[warning]Failed to restore: Cache service responded with 400
Using CPython 3.12.3 interpreter at: /usr/bin/python3.12
```

El pin no estaba donde el fichero decía: el runner caía en el Python del sistema
por casualidad. Arreglado migrando a `setup-uv@v6`, dejando `.python-version` como
fuente única y **añadiendo un paso que lo comprueba** en vez de suponerlo. Tras el
arreglo (corrida `32537436252`): `esperado=3.12 real=3.12`, `Cache hit`, y cero
avisos de configuración.

**3 · El control negativo.** Con `import httpx` metido a mano en `core/`,
`make arch` sale en rojo. Salida literal:

```console
$ make arch
El nucleo es puro: no toca red, disco ni proveedores BROKEN
La deriva funciona SIN verdad de referencia nueva, ... KEPT
La recomendacion se deriva de mediciones publicadas, ... KEPT

Contracts: 3 kept, 1 broken.

----------------
Broken contracts
----------------

El nucleo es puro: no toca red, disco ni proveedores
----------------------------------------------------

docbench_es.core is not allowed to import httpx:

-   docbench_es.core._control_negativo -> httpx (l.3)

make: *** [Makefile:32: arch] Error 1
```

Detalle que merece la pena: **`httpx` ni siquiera está instalado en el entorno**.
El contrato es análisis estático sobre el AST, no una comprobación en tiempo de
ejecución, así que detecta el import prohibido aunque el paquete no exista. Al
borrar el fichero, `Contracts: 4 kept, 0 broken`.

**4 · El contrato se encuentra.** `uv run lint-imports` lee `.importlinter` y
analiza el grafo entero: 28 ficheros y 34 dependencias cuando se comprobó, 32 y
42 al cerrar el hito. Con el nombre `importlinter.ini`
respondería *"Could not read any configuration"* y el CI se pondría rojo por el
motivo equivocado.

**5 · Los tests nuevos pueden ponerse rojos.** Comprobado con un mutante: un
fichero en `core/` que importa `docbench_es.types._tabla` hace fallar a
`test_nadie_de_fuera_importa_los_submodulos_privados_de_types`, y el fallo nombra
al culpable. Un test que solo se ha visto en verde no demuestra nada.

#### El reparto de `RESULTS.md`, y las correcciones de su número

`RESULTS.md` llegó a 228 líneas, de las cuales la mayoría eran metodología de un
solo tiempo. Se parte, según §8 del manual:

- **`RESULTS.md`** son los **números**: tabla, presupuesto, margen, corrida,
  commit y comando de reproducción. Crece por hitos, no por matices. Queda en 95.
- **`docs/metrics.md`** —creado aquí— es el **método**: qué mide cada ventana, la
  resolución del instrumento, la incertidumbre y su derivación, qué entra y qué no
  en «en frío», por qué el local no sustituye al runner, y **el historial completo
  de correcciones del número**. Ahí está el detalle de todo lo de abajo.

El número de la puerta se publicó mal **seis veces** antes de quedar en 4,43 s, y
el registro entero, con sus cifras y su verificación, está en
[`docs/metrics.md`](docs/metrics.md). En una línea cada una: se citó la corrida del
pack de arranque en vez de la de L0; se publicaron los **12 s** del *run* como si
fueran `make fast`, y luego el **job** como cota superior porque el log había
expirado; se sostuvo **3,41 s**, el mínimo de la muestra, cuando ya existían las
tres corridas; se llamó **«intervalo»** a un rango de n=3; se escribió **«±30%»**
para una dispersión asimétrica; y se publicó **`4,4304 s`**, cuatro decimales sobre
una frontera de decenas de milisegundos.

**La corrección tuvo a su vez tres errores, cazados por escrutinio adversarial
antes de publicarse:** «setecientas veces» donde son quinientas, llamar «suelo» a
una ventana que también sobra por el arranque, y estadísticos derivados con tres
cifras significativas. Van corregidos y documentados.

**Y un error de la propia arqueología:** decía «los **16 s** del run» donde fueron
**12 s**. El 16 es el run de la corrida nueva; se actualizó la tabla y se arrastró
el número a la frase histórica sin comprobarla. Verificable con
`git show 78ee8f0:RESULTS.md`.

#### Corregido después del cierre

- **`make clean` no borraba `.hypothesis`**, así que el «en frío» local nunca lo
  era: la base de ejemplos de los dos tests property-based sobrevivía a todas las
  corridas mientras el runner nacía sin ella. Arreglado en el `Makefile` y añadido
  a `.gitignore`. Remedido: la mediana en frío pasa de **1095 ms a 1697,5 ms**, o
  sea que **la caché valía ~600 ms** y el número anterior estaba inflado a favor
  del local en más de un tercio. Era una salvedad que se podía eliminar, y
  documentarla en vez de arreglarla habría sido deuda disfrazada de rigor.
- **Tres ficheros publicaban números retirados.** `README.md` daba «12 s sobre
  `e32c846`» y remitía a `RESULTS.md` por una procedencia que allí ya no existía;
  `docs/reading-order.md` daba «menos de un segundo en local y 12 s en CI»; y
  `LIMITS.md` 26 decía «10 tests» cuando son 15. Arreglados. Lo que revelan —que
  los números se copian a cuatro ficheros y derivan— es la **deuda abierta 5** de
  `ESTADO.md`, con su test, su hito (L5) y su precio.
- **La regla de oro 2 se acota a las estimaciones**, y al acotarla se endurece:
  ver [ADR-0015](docs/adr/0015-alcance-de-la-regla-del-intervalo.md).
