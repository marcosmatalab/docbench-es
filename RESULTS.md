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
| **`make fast` en `ubuntu-latest`, en frío** | **3,41 s** | **90 s** | **26×** |
| Job `fast` completo (incluye `checkout`, `setup-uv`, `uv sync`) | 11 s | — | — |
| *Run* completo (incluye encolado y pasos `Post`) | 16 s | — | — |

> **Qué mide cada fila, porque las tres se han confundido antes.** Sólo la
> primera es el criterio de aceptación de L0: es el paso `la puerta`, medido desde
> su `##[group]Run make fast` hasta la última línea de `pytest`, o sea `make fast`
> y nada más. Las otras dos se publican para que nadie las confunda con ella: el
> job añade el `checkout`, el `setup-uv` y el `uv sync`, y el run añade encima el
> encolado y los pasos `Post`. Una versión anterior de esta tabla publicaba los
> 16 s del run como si fueran `make fast`, y luego el job como «cota superior»
> porque el log ya no estaba disponible. Ahora está el número exacto.

- **Corrida:** [`32572385551`](https://github.com/marcosmatalab/docbench-es/actions/runs/32572385551) · commit `78ee8f0` · 2026-08-22T12:13:00Z · `success`
- **Máquina:** runner estándar de GitHub, `ubuntu-latest`, 4 vCPU
- **En frío** de verdad: no hay caché de mypy, ruff ni import-linter que valga,
  porque el runner nace limpio. La caché de `setup-uv` sólo cubre la descarga de
  paquetes, que queda **fuera** de los 3,41 s por estar en el paso anterior.
- **Reproducción:**
  ```bash
  gh run view 32572385551
  # y el desglose por pasos, que `--json` no da:
  JID=$(gh run view 32572385551 --json jobs -q '.jobs[0].databaseId')
  gh api "repos/marcosmatalab/docbench-es/actions/jobs/$JID/logs" \
    | grep -E '##\[group\]Run make fast|\[100%\]'
  ```
- **Este número mide L0**, el commit `78ee8f0`, no el pack de arranque. La tabla
  anterior citaba la corrida `32482756941` de `e32c846`, y lo decía; se ha
  sustituido al cerrar el hito, como estaba previsto.
- **Sin intervalo porque es n=1**: una sola corrida en el runner. El rango con
  n=10 está abajo, en local. Publicar un intervalo de una sola medición sería
  inventárselo.

**Qué comprueba además esa corrida**, y es parte del resultado: el paso
`CI corre el Python de .python-version` imprime `esperado=3.12 real=3.12`. Hasta
este hito el pin era decorativo —`setup-uv@v3` ignoraba el input `python-version`
con un aviso en cada corrida— y CI y local coincidían por casualidad.

### El número local: mi máquina, declarada, y en frío y en caliente

No sustituye al de arriba. Está para saber qué se siente al desarrollar aquí, y
para que la diferencia entre frío y caliente no se cuele en la cifra publicada.

| Medida | Mediana | Rango (n=10) |
|---|---|---|
| `make fast` en frío | **1095 ms** | 1058 – 1148 ms |
| `make fast` en caliente | **720 ms** | 713 – 749 ms |

En milisegundos y en crudo, no redondeado a dos cifras: con el redondeo anterior
la mediana en frío salía «1,00 s» y el máximo también «1,00 s», que es una tabla
que se lee como imposible. Medidas en frío: `1112 1148 1058 1118 1098 1091 1080
1101 1078 1093`. En caliente: `716 720 740 717 713 721 749 748 714 730`.

Medidas sobre `78ee8f0`, el árbol tal como queda al cerrar L0. Suben respecto a
la primera medición del hito (958 / 564 ms) porque L0 creció al cerrarse: cinco
tests más —dos de ellos property-based, que ejecutan 100 casos cada uno—, dos
módulos más y los `__post_init__` que congelan los mapas. Se deja escrito para que
la subida no se lea como una regresión sin causa.

**El local es ~3× más rápido que el runner** (1,1 s contra 3,41 s) y esa
diferencia no se atribuye aquí a ninguna causa concreta: son máquinas distintas y
no se ha medido el reparto. El número que vale es el del runner.

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

`ruff check` (34 ficheros) + `ruff format --check` (33 ficheros) +
`mypy --strict src` (24 ficheros) + `lint-imports` (4 contratos, 32 ficheros y 42
dependencias analizadas) + `pytest tests/unit` (15 tests, dos de ellos
property-based con `hypothesis`). Sin red y sin Docker.

Los cuatro recuentos son distintos y eso es correcto, no un descuadre: `ruff
check` incluye `pyproject.toml` además de los 33 `.py`, `ruff format` sólo los
`.py`, `mypy --strict` sólo `src/`, y `lint-imports` recorre el grafo de paquetes.
Se anota porque una versión anterior de esta línea le atribuía a mypy los 28 de
`lint-imports`. Comprobados con `uv run ruff check . -v`, y el de `mypy` y el de
`lint-imports` coinciden con los que imprime la corrida `32572385551`.

### Control negativo, ejecutado

Un tiempo en verde no demuestra que la puerta detecte nada. Lo que lo demuestra
es romperla a propósito: con `import httpx` metido a mano en `core/`, el contrato
`nucleo-sin-mundo` pasa a **BROKEN** y `make arch` sale en rojo. La salida
literal está en el registro de L0 del `CHANGELOG.md`.
