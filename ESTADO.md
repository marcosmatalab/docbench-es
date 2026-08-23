# ESTADO · docbench-es

> Este fichero lo inyecta el hook `SessionStart` al arrancar cada sesión de Claude
> Code. Es el checkpoint que Claude Code no trae de serie. **Se actualiza al cerrar
> cada hito, con `/cerrar`.**
>
> La tabla sale de §16 del manual. Si aquí y allí no coinciden, **manda el manual**.

## Release en curso: `v0.1.0` · 112 a 144 horas

| Hito | Horas | Estado | Criterio de aceptación | Número medido |
|---|---|---|---|---|
| L0 esqueleto, canon, CI de tres trabajos, `types`, `errors`, contrato de capas | 8-10 | **CERRADO 2026-08-22** | `make fast` verde en < 90 s con el repo vacío de lógica | **4,43 s** en el runner de GitHub, corrida [`32572683716`](https://github.com/marcosmatalab/docbench-es/actions/runs/32572683716), commit `28186b9`. **20× de margen**. Rango observado, n=4 sobre código idéntico (no es un IC): mínimo 3,41 s, mediana **3,95 s**, máximo 4,43 s, corte 22 ago 2026. Local: 1742 ms en frío, rango 1715–1872, n=10, máquina en reposo (remedido el 22 ago tras arreglar `make clean`, que no borraba `.hypothesis`). Números en [`RESULTS.md`](RESULTS.md), método en [`docs/metrics.md`](docs/metrics.md) |
| L1 `core.canonical` + invariantes + conversores de los cinco formatos | 12-16 | **CERRADO 2026-08-22** | Solapes, huecos y spans fuera de rango detectados al 100% | **8.525/8.525 detectadas y 0/45 falsos positivos**, censo determinista y exhaustivo, `uv run python scripts/censo_invariantes.py`. No es una estimación: es una tasa sobre el censo completo, así que no lleva intervalo (ADR-0015). Puerta: **3829 ms** en frío, rango 3713–3875, n=10, todas con `rc=0`, `load average` 0,93 — **24× de margen**. Números en [`RESULTS.md`](RESULTS.md), método en [`docs/metrics.md`](docs/metrics.md) |
| L2 `core.teds` + validación contra PubTabNet | 10-14 | **CERRADO 2026-08-23** | Coincide a cuatro decimales con la referencia | **20 de 20 a cuatro decimales** —de hecho a seis— sobre los 20 casos propios de PubTabNet, más **6 de 6** casos límite. Golden calculado por su `metric.py` con APTED, contra un Zhang-Shasha propio. No es una estimación: recuento sobre el censo completo, sin intervalo (ADR-0015). Los golden van de 0,5883 a 1,0000, o sea que discriminan. Puerta al cerrar: **mediana 5593 ms, p90 5933**, n=40 en 10 tandas en frío, σ=286, cero descartadas, `uv run python scripts/medir_puerta.py`. La suite creció de 145 a **177 tests** (+22%) y la mediana no se movió: domina el arranque. **18 mutantes**, todos mueren, control negativo **0 de 149**. Censo: **8525/8525** en **20 familias, ninguna vacía**. Techo **8500 local / 20 000 CI** (ADR-0022); el techo avisa, el 90 s del manual bloquea. **Cada número con SU comando**: los 20 de 20, `uv run pytest tests/unit/test_teds_referencia.py -q`; los 6 de 6 casos límite, `uv run pytest tests/unit/test_teds_limites.py -q` —viven en otro fichero y el comando anterior no los cubría—; la puerta, `uv run python scripts/medir_puerta.py`. **Y lo que este criterio NO valida**: el mapeo `CanonicalTable → árbol`, que se cancela en los dos lados de la comparación (límite 52). Números en [`RESULTS.md`](RESULTS.md) |
| L3 `entity.base` + conformidad + `entity.boe` + `boe_xml` + `corpus` | 16-20 | PENDIENTE | 1.000 documentos emparejados PDF/XML, con manifiesto y tasa de descarte | — |
| L4 `truth.derived` + fixtures de tabla | 8-10 | PENDIENTE | La verdad derivada reproduce las tablas a mano | — |
| L5 `extract.base` + conformidad + **ocho** extractores locales + nivel 1 | 14-18 | PENDIENTE | Primera tabla de estructura con coste y cobertura evaluable | — |
| L6 `sample` con McNemar + bootstrap agrupado | 8-10 | PENDIENTE | Plan congelado y publicado antes de la primera campaña seria | — |
| L7 quickstart: 20 documentos versionados + `make quickstart` | 6-8 | PENDIENTE | De clone a tabla en < 3 min, sin red y sin gastar | — |
| L8 los tres adaptadores hostiles + cableado de `benchcore.core.policy` + fuga de credenciales | 10-12 | PENDIENTE | Los tres bloquean. Ningún secreto en ningún artefacto | — |
| **L8b verdad auditada**: 120 documentos, doble pasada ciega | 20-26 | PENDIENTE | *"La verdad derivada coincide con la auditoría humana en X%, IC [a,b]"*. **Cierra `v0.1.0`** | — |

## Releases siguientes

| Release | Hitos | Horas |
|---|---|---|
| `v0.2.0` | L9, L10, L11, L12, **L12b** (los tres estratos que faltan), L13, L14 | 90-114 |
| `v0.3.0` | L15, L16, L17, L18, L19, L20, **L20b** (`toolwatch`), **L20c** (leaderboard + badge) | 84-108 |

**Total: 286 a 366 horas.** Cada release es publicable por sí solo.

## Construido y NO VALIDADO

Tienen código y tests propios, pero **ningún consumidor real los ha ejercitado**.
El patrón que obliga a listarlos: el hito que ESCRIBE un módulo no encuentra los
bugs que encuentra el que lo CONSUME — L1 cerró en verde y L2 descubrió que
`from_html` marcaba mal el **100%** de las cabeceras de PubTabNet.

| Qué | Primer consumidor real | Barrera |
|---|---|---|
| `from_markdown`, `from_dataframe`, `from_tei`, `from_text_heuristic` | **L5**: `pymupdf4llm`/`marker` → Markdown, `camelot` → DataFrame, `grobid` → TEI, `tesseract` → texto | `tests/unit/test_sin_consumidor.py`, por AST |
| Campos `page_span` y `caption` | Sin fecha. `page_span` además no está medido (LIMITS 32) | Idem |

**Ninguna cifra publicada puede pasar por ellos**, y lo impide un test, no una
nota. Ver LIMITS 49.

## Deuda abierta

0. **Lo que L1 deja atado a hitos posteriores, y no es opcional.** Sale del
   escrutinio adversarial del cierre, y cada uno tiene su número en `LIMITS.md`:
   - **L3 o L4 · cuántos documentos del BOE traen el *table model error* del
     estándar** (límite 30). `from_html` los convierte en tablas con `SOLAPE`,
     que es fatal, así que en L4 `truth.derived` dejaría esos documentos **sin
     verdad de referencia**. No está medido.
   - **L5 · si el TEDS negativo se recorta a cero AL PUBLICAR** (límite 44). TEDS
     puede salir negativo —medido, −0,142857, y la referencia hace lo mismo— y
     §12 lo publica como nota. Recortarlo dentro de `core.teds` sería apartarse
     de la referencia en silencio, así que la decisión es del informe.
   - **L3 · cuántas cabeceras del BOE viajaban sin marcar** (límite 45), antes de
     que L2 arreglara el `<thead><td>` de `from_html`.
   - **L3 · el techo de la puerta se queda corto si `entity.conformance` es puro
     y grande** (ADR-0022). La proyección da 6400–8000 ms suponiendo que la mitad
     de L3 va a `full` por necesitar red. **Ese supuesto se comprueba, no se
     cree**: si falla, el techo de 8500 se rompe dentro del propio L3.
   - **L5 · validar antes de puntuar** (límite 47). `core.teds` da 0,75 a una
     tabla con `SOLAPE` sin protestar.
   - **L5 · el suelo del TEDS negativo** (límite 46 y ADR-0023): mismo criterio
     por documento y en el agregado, y se dice cuántos se recortaron.
   - **L4 · la celda que sólo contiene `<img>`** (límite 33): hoy sale vacía, y
     un extractor que la OCR-ee bien queda penalizado **por acertar**.
   - **L5 · la nota de un extractor sin spans no se puede publicar sin su
     cobertura evaluable** (límite 35). Es una condición sobre el objeto que
     emite el informe, con su test.
   - **L5 · qué fracción de las TABLAS trae celdas combinadas** (límite 36). El
     sondeo midió documentos; el 63% y el 42% son de documentos con tabla, n=57.

1. **`benchcore` v0.1.0 es una SEMILLA, no el benchcore del plan.** Estan `types`,
   los cuatro `Protocol`, `registry` y `conform`. **NO estan** `core.policy`,
   `runner`, `core.bootstrap` ni `core.power`. Se anaden cuando su primer
   consumidor los pida, subiendo el MENOR de `API_VERSION`. Ver **D-003 en
   [`DECISIONES.md` de `benchcore`](https://github.com/marcosmatalab/benchcore/blob/main/DECISIONES.md)**
   — ese fichero vive en el repo de `benchcore`, **no en éste**.
2. **El pack de arranque venia con siete fallos que impedian que `make fast`
   arrancara.** Estan arreglados y documentados uno a uno en `PARCHES.md`, con su
   sintoma exacto y su causa. Leelo antes de tocar `pyproject.toml`.
3. **`Cost` no esta definido en este manual.** Se referencia como
   `benchcore.types.Cost` y no aparece en ninguna seccion. Definido en la semilla
   de `benchcore` derivandolo del `AttemptRecord` de gonogo §6.4, con un campo
   anadido, `measured`, para que cero medido y "no se ha podido medir" no sean el
   mismo valor. Ver **D-001 en
   [`DECISIONES.md` de `benchcore`](https://github.com/marcosmatalab/benchcore/blob/main/DECISIONES.md)**,
   el mismo fichero de otro repo que la deuda 1.
4. **`full.yml` y `nightly.yml` nacen DORMIDOS, con `on: workflow_dispatch:`
   unicamente.** Reproducido ejecutandolo el 21 ago 2026: `make full` muere en
   `quickstart` con `ModuleNotFoundError: No module named 'docbench_es.cli.main'`,
   porque `full = fast + quickstart` y `quickstart` necesita CLI (L5+),
   extractores (L5) y los 20 documentos congelados (L7). **Se encienden en L7**,
   sustituyendo su bloque `on:` por `on: [push, pull_request]`. Un badge rojo
   permanente durante ~90 horas es peor que no tener el workflow: ensena al
   equipo a ignorar el color. Consecuencia real mientras tanto: hasta L7 **no hay
   cobertura de CI** del contrato de entidad, del de extractor, de los tres
   adaptadores hostiles, de la fuga de credenciales ni de la degradacion. Ver el
   limite 25 de `LIMITS.md`.

5. **Los números publicados se copian a cuatro ficheros y derivan. Hoy se cazan
   leyendo; en L5 ya no.** Al cerrar L0, tres sitios fuera de `RESULTS.md`
   publicaban cifras retiradas: `README.md` —la puerta de entrada del repo— daba
   «`make fast` en verde, 12 s sobre `e32c846`» **y remitía a `RESULTS.md` por una
   procedencia que allí ya no existía**; `docs/reading-order.md`, la ruta de 5
   minutos, daba «menos de un segundo en local y 12 s en CI»; y `LIMITS.md` 26
   decía «10 tests» cuando son 15. Los tres se encontraron **leyendo**, con un
   escrutinio adversarial, no con una prueba.
   **Por qué no basta con disciplina:** hoy es un número que viaja a tres sitios.
   En L5 son exactitud, TEDS, `cell_f1` y cobertura evaluable **por extractor y
   por estrato** —decenas de cifras—, más el coste. Un humano no las relee todas
   en cada commit, y el fallo es del tipo más grave que hay aquí: el repo
   afirmando algo que otro fichero del repo desmiente.
   **Lo que cierra el agujero, y su precio:** un test en la puerta rápida que
   compruebe que ningún número publicado fuera de `RESULTS.md` lo contradice. Los
   números que viajan se marcan en origen y en destino con un ancla —por ejemplo
   `<!-- RESULTS:l0.ci.gate -->`—, el test extrae ambos y falla si no coinciden.
   Precio estimado: 2-3 h, un fichero de test más el marcado de las anclas
   existentes. **Se hace en L5**, que es el primero que lo necesita de verdad;
   hacerlo antes sería infraestructura para tres cifras que caben en una lectura.
   Mientras tanto el riesgo está declarado aquí y no en ningún sitio más.

6. **`ADR-0016` esta transcrito al manual pero NO tiene test.** La deuda anterior
   —el manual diciendo lo contrario que el ADR— **se cerro el 22 ago 2026**
   transcribiendo a §2, §6.9, §9.4, §10.1 y §10.2 en el mismo commit. Se cerro
   entonces y no en L3 por una razon operativa, no de higiene: el bucle `/hito`
   empieza leyendo `MANUAL.md`, asi que una sesion de L3 habria leido §9.4, visto
   `anexo-png` entre los estratos y lo habria implementado. Dos fuentes de verdad en
   desacuerdo durante ~40 horas, y la que gana por defecto es la que el bucle lee
   primero. De ahi sale la regla 8 de `CLAUDE.md`.
   **Lo que queda abierto es lo otro:** no hay ningun test que impida volver a
   emitir la etiqueta `anexo-png` ni que compruebe que `nacido-digital` y
   `escaneado` son excluyentes y exhaustivos. Hoy lo sostiene el manual y nada mas.
   **Se cierra en L3**, con la suite de conformidad de `entity.boe`. Precio: un test
   de conformidad, ~1 h. Mientras tanto, `umbral_capa_texto` es un numero declarado
   que nadie ha medido contra un corpus real.

7. **El arnés de mutantes cubre 149 de 177 tests, y no hay mutante para el resto.**
   Límite 51. Los **23 tests** que quedan fuera son de cinco módulos, y ésta es la
   lista de verdad —la anterior mandaba a L3 escribir un mutante para `teds_batch`
   que **ya existe**, `batch_sobrescribe`—:

   | Sin mutante | Tests | Qué habría que romper | Precio |
   |---|---|---|---|
   | `types_invariantes` | 7 | las invariantes de `Documento` y la clave | ~25 min |
   | `ancla` | 5 | `unica()` devolviendo el primer índice sin contar | ~10 min |
   | `recuentos` | 5 | un patrón que deja de casar y pasa en verde sobre cero citas | ~15 min |
   | `types` | 5 | `congelar_mapas` que no congela | ~20 min |
   | `errors` | 3 | el enum de fallo con una causa de más o de menos | ~15 min |
   | `sin_consumidor` | 3 | la barrera por AST que no mira los scripts | ~15 min |

   **~1 h 25 min en total**, no «~20 min por módulo nuevo»: son cinco módulos ya
   escritos, no futuros. **Se cierra a plazos** —cada hito que añada módulo añade
   su mutante— pero éstos ya están en deuda y tienen precio puesto.

   `ancla` y `sin_consumidor` son los que más urgen: son **barreras**, o sea
   código cuyo único trabajo es ponerse rojo, y un candado que no se ha probado
   contra su propia rotura no es un candado.

8. **La tasa de muerte de cada asesino no está medida.** Límite 50. La columna
   «mata SIEMPRE» se calcula con n = 3, y eso llama determinista a un test con
   p = 0,9 el 73% de las veces. El arnés ya trae `--reps` y `--solo` para afinar
   un caso; lo que no hay es un n suficiente por defecto, porque costaría decenas
   de repeticiones por mutante. **No se cierra**: se declara y se usa el flag
   cuando la diferencia entre columnas no se explique sola.

## Decisiones tomadas fuera del manual

| Decision | ADR | En una linea |
|---|---|---|
| `types` es un paquete, no un fichero | [`0013`](docs/adr/0013-types-como-paquete.md) | Las ~30 estructuras de §6 salen 340 lineas y `CLAUDE.md` prohibe pasar de 300. `docbench_es.types` sigue siendo la unica superficie de import, y un test lo hace cumplir |
| Los mapas del modelo de datos se congelan | [`0014`](docs/adr/0014-mapas-inmutables-en-el-modelo-de-datos.md) | `frozen=True` no congelaba los mapas y un test afirmaba que si. `congelar_mapas` en `__post_init__` |
| `anexo-png` se disuelve en capa de texto | [`0016`](docs/adr/0016-anexo-png-se-disuelve-en-capa-de-texto.md) | Mezclaba un documento con una figura y un anexo escaneado de 136 paginas. La frontera que decide que extractor compite no son las imagenes, es si hay capa de texto |
| La regla del intervalo se acota a las **estimaciones** | [`0015`](docs/adr/0015-alcance-de-la-regla-del-intervalo.md) | Un tiempo no tiene poblacion de la que muestrear: lleva rango, n y resolucion, no IC. Se acota **y se endurece**: los numeros que no son estimaciones dejan de poder publicarse desnudos |

| El hueco de cola es legitimo, el interior es fatal | [`0018`](docs/adr/0018-hueco-de-cola-y-hueco-interior.md) | El «o declara los huecos» de §6.2 no era traducible tal cual. La lectura es la del ORIGEN de la celda, no la de la rejilla rellena |
| TEDS compara contenido CANONICO | [`0020`](docs/adr/0020-teds-compara-contenido-canonico.md) | La referencia no normaliza y cuenta el marcado inline. El golden se genera dandole el mismo render canonico |
| La forma canonica del arbol de TEDS | [`0021`](docs/adr/0021-forma-canonica-del-arbol-de-teds.md) | `<thead>` con el prefijo maximo de cabecera, todo `<td>`, el hueco sin nodo. Un `<tbody>` de mas cuesta 0,667 |
| El techo de la puerta AVISA, el manual BLOQUEA | [`0022`](docs/adr/0022-el-techo-de-la-puerta.md) | 8500 local / 20 000 CI, re-justificado en cada cierre con 40 corridas. **No toca el manual**: §15 y sus 90 s no cambian |
| El TEDS negativo se recorta SOLO al publicar | [`0023`](docs/adr/0023-teds-negativo-suelo-al-publicar.md) | El calculo no se toca —romperia el criterio de L2—; `para_publicar()` recorta, y se dice cuantos se recortaron |
| Un documento con varias tablas: la nota es la media | [`0024`](docs/adr/0024-teds-batch-varias-tablas-por-documento.md) | `teds_batch` sobrescribia por clave y la tabla mal extraida desaparecia con cobertura 1,0. Regla de oro 6 rota |
| «Tras alinear» = la colocacion canonica de L1 | [`0025`](docs/adr/0025-la-exactitud-de-celda-no-alinea.md) | `cell_accuracy` no hace un segundo alineamiento: es exactitud POSICIONAL, y el precio esta en el limite 53 |

**Cuales estan transcritos al manual**, por la regla de oro 8, y cuales no tocan
el manual — que no es lo mismo y hay que distinguirlo:

| ADR | Al manual |
|---|---|
| 0013, 0014, 0016 | **Si**: §6 y §8 · §6 y §6.8 · §2, §6.9, §9.4, §10.1 y §10.2 |
| 0018, 0020, 0021, 0025 | **Si**: §6.2 · §9.2 · §9.2 · §12 |
| 0015 | **No lo toca**: la regla del intervalo vive en `CLAUDE.md` y el manual no la enuncia —`grep -n 'sin intervalo' MANUAL.md` no devuelve nada— |
| 0022 | **No lo toca**: §15 fija 90 s y no cambia; el techo es una alarma POR DEBAJO de esa promesa |
| 0023 | **Si**: §9.2. `para_publicar()` es una funcion publica que §9.2 no declaraba, y una interfaz incompleta es una contradiccion como cualquier otra. Transcrita en el mismo commit |
| 0024 | **No lo contradice, lo cumple**: §6 ya decia que `evaluable_coverage` es «sobre cuantas TABLAS se pudo calcular» y el codigo contaba documentos. El ADR arregla el codigo, no el manual |

Los 0017 y 0019 son de L0 y L1 y estan en sus cierres.

> **Esta tabla estaba desfasada y decia «los cuatro».** Existen 0013–0025.
> Enumerarlos mal es exactamente el fallo que la regla de oro 8 persigue: si nadie
> sabe que ADR hay, nadie puede comprobar cual falta por transcribir.

Los numeros 0001 a 0012 estan **reservados** para los doce ADR de §4 del manual.
Se transcriben conforme llega el hito que implementa cada uno.

## Requisito previo, antes del primer `uv sync`

`benchcore` tiene que estar en `https://github.com/marcosmatalab/benchcore`, rama
`main`. Sin el, `uv sync` muere en el primer comando y no hay puerta que valga.

## Siguiente paso

`/hito L3` — `entity.base` + su suite de conformidad + `entity.boe` + `boe_xml` +
`corpus`. Criterio del manual (§16): **un corpus del BOE descargado, versionado y
reproducible**.

**Esta linea decia `/hito L1` con L1 y L2 ya cerrados.** No es cosmetico: el hook
`SessionStart` inyecta `ESTADO.md` entero, asi que la sesion siguiente lo lee
antes que nada y se pone a rehacer un hito cerrado. Es el mismo argumento de la
regla de oro 8 —gana la fuente que el bucle lee primero— aplicado a este fichero.

Lo que L3 hereda y no puede ignorar esta en «Deuda abierta», arriba: el techo de
8500 ms se re-justifica con `scripts/medir_puerta.py`, y los limites 42 (coste de
TEDS por tamaño), 51 (el arnes cubre 149 de 177) y 52 (el criterio de L2 no valida
el mapeo) llegan con su precio puesto.

Lo que L1 hereda de L0 y no puede ignorar:

- **`CanonicalTable.is_wellformed()` levanta `NotImplementedError` a propósito**,
  y hay un test que lo exige. L1 lo implementa y ese test cambia de forma. Si
  devolviera `(True, [])`, el criterio de L1 se cumpliría trivialmente.
- **`cell_at` declara tres casos degenerados** —fuera de rango, hueco y `span < 1`—
  y el tercero deja la celda invisible a propósito. Quien tiene que reportarlo es
  `is_wellformed()`, no `cell_at`.
- **Los tests de invariantes van con `hypothesis`**, no con casos a mano: lo pide
  `.claude/rules/tests.md`, y L0 comprobó por qué. El primer test de propiedad
  escrito en L0 pasaba en verde contra el código roto porque la estrategia era
  demasiado ancha; hubo que dirigirla para que encontrara la colisión. Un test de
  propiedad mal dirigido da cobertura aparente y no avisa.
