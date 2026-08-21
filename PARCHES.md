# Parches aplicados al pack de arranque · 21 ago 2026

Este pack no arrancaba tal cual salia del zip. Los siete fallos de abajo estan
**reproducidos ejecutandolos** en contenedor limpio, no deducidos leyendo, y
cada arreglo lleva el motivo. Si algo de aqui contradice al `MANUAL.md`, manda
el manual y este fichero esta mal.

## Los siete

| # | Sintoma exacto | Causa | Arreglo |
|---|---|---|---|
| 1 | `uv sync` muere: *"failed to fetch tag \`v0.1.0\`"` de `TU-USUARIO/benchcore`* | El repo `benchcore` no existia | `[tool.uv.sources]` apunta a `marcosmatalab/benchcore`, rama `main` |
| 2 | `uv run` ni llega al linter: *"Unable to determine which files to ship inside the wheel"* | El pack no traia `src/`, asi que hatchling no podia construir el paquete | `[tool.hatch.build.targets.wheel] packages = ["src/..."]` |
| 3 | `ruff format --check .` pide reformatear **`MANUAL.md`** | Ruff 0.16 formatea los bloques de Python **dentro de los Markdown**, y el manual lleva snippets elididos a proposito (`...`, argumentos recortados). Ademas `make fix` habria **reescrito el manual**, que `CLAUDE.md` declara fuente de verdad | `extend-exclude = ["*.md"]` |
| 4 | `ruff check`: *"N818 Exception name should be named with an Error suffix"* | El `MANUAL.md` declara literalmente `PolicyViolation`, `ContractViolation` y `BudgetExceeded`, y el pack traia `"N"` en `select` | `ignore = ["N818"]`. Es la unica regla desactivada, y se desactiva porque manda el manual, no porque estorbe |
| 5 | `lint-imports`: *"Missing layer in container: module X does not exist"* | El contrato de capas exige que **exista** cada capa que nombra, y con `exhaustive = true` una de mas tambien lo rompe. O sea que el arbol no es opcional: es parte de la puerta | Sembradas todas las capas del `.importlinter`, vacias |
| 6 | `pytest` devuelve 4 o 5 y mata la puerta | Los directorios que nombra `make fast` no existian, y un directorio vacio da codigo 5 por coleccion vacia | Un `test_humo_<dir>.py` por directorio, con nombre unico (repetir `test_humo.py` sin `__init__.py` hace que pytest aborte por modulos duplicados) |
| 7 | `mypy --strict`: *"benchcore.types: module is installed, but missing library stubs or py.typed marker"* | `benchcore` no llevaba el marcador PEP 561, asi que el consumidor lo veia sin tipar | Arreglado en `benchcore`, no aqui. Solo aparece con la cadena montada |

Del 1 al 6 afectaban **a los dos packs** (el 6 solo mataba la puerta de gonogo,
porque su `make fast` nombra `tests/reference` y `tests/decision`; en
docbench-es estaba latente).

## Estado medido tras los parches

```
uv sync --only-group dev
make fast
```

Verde en **4 segundos** (presupuesto: 90). Los cuatro contratos de capas en KEPT.
Control negativo ejecutado: al meter un import prohibido en `core/`, el contrato
correspondiente pasa a BROKEN.

## Lo que esto cambia en L0

El `/hito L0` de `HITOS.md` pedia montar el arbol de paquetes y los directorios
de test. **Ya estan, vacios.** L0 sigue teniendo que hacer todo lo demas: los
`__init__.py` con contenido de verdad, `types.py` y `errors.py`, los ficheros de
raiz (`README.md`, `RESULTS.md`, `LIMITS.md`, `CHANGELOG.md`, `LICENSE`),
`docs/reading-order.md` y los tres trabajos de CI. Y sus tres criterios de
aceptacion se comprueban igual.

Los `test_humo_*.py` son marcadores: se borran en cuanto ese directorio tenga un
test de verdad.

## Requisito previo que sigue en pie

`benchcore` tiene que estar subido a `https://github.com/marcosmatalab/benchcore`
en la rama `main` **antes** del primer `uv sync`. Va en `benchcore-semilla.zip`.

Se apunta por **rama y no por tag** a proposito: `uv.lock` fija el commit exacto,
asi que sigue siendo reproducible y el CI lo reconstruye igual, pero no hay que
re-taggear cada vez que benchcore crece. Se sube version con
`uv lock --upgrade-package benchcore`. Al cortar el `v0.1.0`, ahi si se pasa a tag.
