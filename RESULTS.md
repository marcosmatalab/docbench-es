# RESULTS · docbench-es

> **La regla de este fichero.** Un número sin intervalo no se publica. Un número
> que no se puede reproducir no existe. Cada fila lleva su fecha, su versión, la
> máquina y el comando exacto que la regenera.
>
> Si buscas lo que este proyecto NO mide, está en [`LIMITS.md`](LIMITS.md).

## Lo que todavía NO hay aquí, dicho antes que lo que sí

**No hay ni un solo número de exactitud, de TEDS ni de coste.** A 21 de agosto de
2026 el repo está en L0: esqueleto, modelo de datos y puerta de CI. No hay corpus,
no hay verdad de referencia y no hay extractores, así que cualquier número de
calidad que apareciera aquí estaría inventado.

Cuándo llega cada uno:

| Número | Hito | Qué dirá |
|---|---|---|
| Primera tabla de estructura, con coste y cobertura evaluable | L5 | Qué extractor reconstruye mejor las tablas |
| **El titular**: hueco atribuible a la extracción | L10 | *"Con extracción perfecta X; con el mejor real Y; el hueco es Z puntos"* |
| Cuánto aporta la capa semántica | L11 | *"Cargar el glosario sube X puntos, IC [a,b]"* |

---

## L0 · Tiempo de la puerta rápida

El criterio de aceptación de L0 es un tiempo, así que el tiempo es el número.
Presupuesto declarado en §15 del manual: **< 90 s**.

### El número reproducible: el runner de GitHub

Es el que vale, porque es el que cualquiera puede volver a ejecutar sin tener mi
portátil delante.

| Medida | Valor | Presupuesto | Margen |
|---|---|---|---|
| *Run* completo del workflow `fast`, en frío | **12 s** | — | — |
| Job `fast` dentro de ese run | **10 s** | 90 s | 9× |

> **Qué mide exactamente cada fila, porque no es lo que parece.** Los 12 s son el
> reloj de pared del *run* entero: encolado, `actions/checkout`, `setup-uv`,
> `uv sync`, la puerta y los pasos `Post`. El job son 10 s. **`make fast` a secas
> es un subconjunto de esos 10 s, y no se puede desglosar**: el log de la corrida
> ya no está disponible y `gh run view --json` no da tiempos por paso. Así que
> contra el presupuesto de §15 se compara el job, que es una **cota superior** del
> tiempo de la puerta: si 10 s cabe en 90 s, `make fast` también. Una versión
> anterior de esta tabla publicaba los 12 s como si fueran `make fast`.

- **Corrida:** [`32482756941`](https://github.com/marcosmatalab/docbench-es/actions/runs/32482756941) · commit `e32c846` · 2026-08-21T12:37:19Z
- **Máquina:** runner estándar de GitHub, `ubuntu-latest`, 4 vCPU
- **En frío** de verdad: incluye `uv sync --only-group dev` y no hay caché de
  mypy, ruff ni import-linter que valga, porque el runner nace limpio.
- **Reproducción:** `gh run list --workflow fast` · `gh run view 32482756941`

> **Honestidad sobre a qué commit corresponde.** Esa corrida mide `e32c846`, el
> pack de arranque parcheado, no el contenido de L0. L0 añade el modelo de datos
> (28 ficheros analizados en vez de 18) y 10 tests en vez de 1. **Este número se
> vuelve a tomar en el push de L0**, con `/cerrar`, y esta tabla se sustituye por
> el de su corrida. Publicarlo ahora como si fuera el de L0 sería exactamente el
> tipo de cosa que este repo dice no hacer.
> Sin intervalo porque es **n=1**: una sola corrida. Con dos o más se publica el
> rango, como abajo.

### El número local: mi máquina, declarada, y en frío y en caliente

No sustituye al de arriba. Está para saber qué se siente al desarrollar aquí, y
para que la diferencia entre frío y caliente no se cuele en la cifra publicada.

| Medida | Mediana | Rango (n=10) |
|---|---|---|
| `make fast` en frío | **1089 ms** | 1052 – 1107 ms |
| `make fast` en caliente | **730 ms** | 687 – 760 ms |

En milisegundos y en crudo, no redondeado a dos cifras: con el redondeo anterior
la mediana en frío salía «1,00 s» y el máximo también «1,00 s», que es una tabla
que se lee como imposible. Medidas en frío: `1104 1084 1096 1079 1086 1074 1107
1095 1052 1092`. En caliente: `690 698 729 760 732 757 749 687 740 714`.

Suben respecto a la primera medición de L0 (958 / 564 ms) porque el hito creció
al cerrarse: cinco tests más —dos de ellos property-based, que ejecutan 100 casos
cada uno—, un módulo más en `src/` y los `__post_init__` que congelan los mapas.
Se deja escrito para que la subida no se lea como una regresión sin causa.

- **Máquina:** AMD Ryzen 9 9950X3D, 8 vCPU asignadas a WSL2, 31 GB RAM ·
  Ubuntu 24.04.3 LTS sobre WSL2 (kernel 6.6.87.2) · Python 3.12.3 · uv 0.12.0
- **Medido dentro de WSL**, en una shell nativa. **No** a través de `wsl.exe`:
  ver más abajo por qué eso importa y cuánto costaba.
- **"En frío"** aquí significa **sin cachés de herramienta**: `make clean` más
  borrar `.import_linter_cache` antes de cada corrida. **No** incluye `uv sync`,
  que el runner sí paga. La diferencia con el runner **no se atribuye aquí a
  ninguna causa concreta**: los 12 s del runner incluyen encolado, `checkout`,
  `setup-uv` y pasos `Post`, y sin el log por pasos no se puede repartir. Se
  publica el del runner porque es el que cualquiera puede reejecutar.
- **Reproducción** (desde una shell dentro de WSL, no desde Windows):
  ```bash
  for i in $(seq 10); do
    make clean >/dev/null 2>&1; rm -rf .import_linter_cache
    s=$(date +%s%N); make fast >/dev/null 2>&1; e=$(date +%s%N)
    echo "$(( (e - s) / 1000000 )) ms"
  done
  ```

#### Sobre el arranque de `wsl.exe`, comprobado y descartado

Había la sospecha de que estas cifras estuvieran infladas por invocar la puerta
como `wsl.exe -- make fast` desde Windows, pagando el arranque del contenedor en
cada llamada. **Se midió y no era el caso:** los números de la tabla coinciden
con la medición nativa, no con la de `wsl.exe`.

| Vía | En caliente (mediana, n=3) |
|---|---|
| Shell nativa dentro de WSL | 0,56 s |
| `wsl.exe -d Ubuntu -- bash -lc 'make fast'` | 0,68 s |
| `wsl.exe -d Ubuntu -- true` (sólo el arranque) | 0,16 s |

O sea que `wsl.exe` cuesta **~0,15 s por llamada**. Si la cifra vieja lo hubiera
incluido, habría salido ~0,70 s en caliente, no 0,56 s. Queda escrito para no
volver a medirlo: **la puerta se mide dentro de WSL**, y el sobrecoste conocido de
no hacerlo son esos 0,15 s.

### Qué cubre exactamente ese tiempo

`ruff check` (33 ficheros) + `ruff format --check` (32 ficheros) +
`mypy --strict src` (24 ficheros) + `lint-imports` (4 contratos, 32 ficheros y 42
dependencias analizadas) + `pytest tests/unit` (15 tests, dos de ellos
property-based con `hypothesis`). Sin red y sin Docker.

Los cuatro recuentos son distintos y eso es correcto, no un descuadre: `ruff
check` incluye `pyproject.toml` además de los 32 `.py`, `ruff format` sólo los
`.py`, `mypy --strict` sólo `src/`, y `lint-imports` recorre el grafo de paquetes.
Se anota porque una versión anterior de esta línea le atribuía a mypy los 28 de
`lint-imports`. Comprobados con `uv run ruff check . -v`.

### Control negativo, ejecutado

Un tiempo en verde no demuestra que la puerta detecte nada. Lo que lo demuestra
es romperla a propósito: con `import httpx` metido a mano en `core/`, el contrato
`nucleo-sin-mundo` pasa a **BROKEN** y `make arch` sale en rojo. La salida
literal está en el registro de L0 del `CHANGELOG.md`.
