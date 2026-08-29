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
| L2 `core.teds` + validación contra PubTabNet | 10-14 | **CERRADO 2026-08-23** | Coincide a cuatro decimales con la referencia | **20 de 20 a cuatro decimales** —de hecho a seis— sobre los 20 casos propios de PubTabNet, más **6 de 6** casos límite. Golden calculado por su `metric.py` con APTED, contra un Zhang-Shasha propio. No es una estimación: recuento sobre el censo completo, sin intervalo (ADR-0015). Los golden van de 0,5883 a 1,0000, o sea que discriminan. Puerta al cerrar: **mediana 5593 ms, p90 5933**, n=40 en 10 tandas en frío, σ=286, cero descartadas, `uv run python scripts/medir_puerta.py`. La suite creció de 145 a **185 tests** (+28%) y la mediana pasó de 5593 a **5920 ms** tras la auditoría del guardián: **8,2 ms por test** (327/40), contra ~900 ms de arranque. Sigue dominando el arranque, pero **decir «no se movió» ya era falso**: lo decía cuando la suite estaba en 177 y nadie reescribió la frase al remedir (límite 55). **18 mutantes** al cerrar L2, todos mueren. *(Aquí ponía «22 mutantes, control negativo 0 de 166», que son las cifras de una corrida MUY posterior —los 22 no existían en L2, el cierre los subió de 12 a 18— metidas en la fila de un hito cerrado. Misma clase que el sello de L3: corridas distintas presentadas como una.)* Censo: **8525/8525** en **20 familias, ninguna vacía**. Techo **8500 local / 20 000 CI** (ADR-0022); el techo avisa, el 90 s del manual bloquea. **Cada número con SU comando**: los 20 de 20, `uv run pytest tests/unit/test_teds_referencia.py -q`; los 6 de 6 casos límite, `uv run pytest tests/unit/test_teds_limites.py -q` —viven en otro fichero y el comando anterior no los cubría—; la puerta, `uv run python scripts/medir_puerta.py`. **Y lo que este criterio NO valida**: el mapeo `CanonicalTable → árbol`, que se cancela en los dos lados de la comparación (límite 52). Números en [`RESULTS.md`](RESULTS.md) |
| L3 `entity.base` + conformidad + `entity.boe` + `boe_xml` + `corpus` | ~~16-20~~ **18-23** | **CERRADO 2026-08-24** | 1.000 documentos emparejados PDF/XML, con manifiesto y tasa de descarte | **1.000 de 1.000 emparejados**, de 1.043 intentados, con **tasa de descarte 4,12%** —denominador 1.043, umbral 0,85, ventana 2026-03-09 a 2026-04-11, causa única `incoherente` (43)—, 0 reintentos agotados y 4 días sin boletín fuera del denominador. `uv run python scripts/verificar_corpus.py runs/l3/manifiesto.json --plan runs/l3/plan.yaml` → **CUMPLE, 0 fallos, rc=0**, y ese CUMPLE incluye **rehacer los 1.000 `sha256` contra los bytes**. No es una estimación: censo sobre la población completa de la ventana, sin intervalo (ADR-0015). **Desglose por estación**, que es para lo que la ventana cruza el equinoccio: invierno **3,90%** (462/444), primavera **4,30%** (581/556), reconstruido y declarado (límite 63). **La ventana se eligió sobre el tramo con MÁS descarte de los tres medidos** —agosto 2,0%, otoño 4,5%, primavera 5,5%— para que a la tasa no se le pueda acusar de estar elegida. Ritmo **1,0000851 s de espaciado mediano, mínimo 1,0000211, n=2.064**, contra 1 rps declarado. **361,9 MB** en disco contra tres proyecciones que fallaron las tres (−23,5%, **+47,3%**, −29,8%): la corrección empeoró la estimación por aplicar KB/página medido en documentos cortos a una población larga, y KB/página **cae un factor 5,6** con la longitud. Puerta al cerrar: **mediana 7400 ms, p90 7505**, n=40 en 10 tandas en frío, σ=100, cero descartadas, sello `1600137`, **margen 995 ms** bajo el techo de 8500. Desglose por paso con el **barrido de referencias medido por fin: 220 ms, el 3,0%** de la puerta. **21 mutantes, todos mueren y todos SIEMPRE**, control negativo **0 de 164**, sello `0717b70 · 164 tests`. *(Publicado como «22 mutantes, 0 de 166» junto a un sello de 164: eran DOS corridas presentadas como una. `seccion_sin_cerrar` entró en el `PLAN` cuatro horas después, y su suite objetivo tiene 2 tests — 164 + 2 = 166. Corregido en la auditoría en frío de `a0d85ed`.)* El escrutinio adversarial del cierre sacó **12 hallazgos y 4 eran afirmaciones falsas**, todas corregidas en el acto. Números en [`RESULTS.md`](RESULTS.md) |
| L4 `truth.derived` + fixtures de tabla | 8-10 | **CERRADO 2026-08-25** | La verdad derivada reproduce las tablas a mano | **25 de 30 coinciden** sobre 30 documentos y **1.213 celdas** transcritas del PDF, `uv run python scripts/comparar_verdad.py --detalle`. No es una estimación: recuento exhaustivo sobre las 30, sin intervalo (ADR-0015). **CERO discrepancias atribuibles al código**; de las 11, **6 errores de transcripción** evidenciados contra el PDF y **5 de frontera ambigua**, las dos clases declaradas antes de verlas. **Antes de corregir, 22 de 30**, y las dos cifras se publican. De los 25, **21 limpias + 1 contaminada + 3 corregidas**, y el desglose lo emite el propio comparador en `runs/l4/informe.json` (`--informe`), no se deduce. **Y el cero está atacado**: `seccion_sin_cerrar` —el bug real del grupo de filas— **mata 0 de 25** porque 0 de 30 documentos tienen la forma que lo dispara, mientras mata 2 de 2 en `test_grupo_de_filas.py`. **Dos huecos medidos** del instrumento de 22 mutantes, límites 65-68. Cobertura de la comparación: **53,1%** (1.213 de 2.283 celdas), límite 75. **No reproducible en clon frío**, límite 74, y el **orden del congelado tampoco está atestiguado por git**, límite 78. **Puerta: p90 8006 ms, techo 8500, margen 494 ms**, n=40, sello `f89c5b6`, 0 descartadas. **Baja** desde los 8238 de antes del hito (sello `988a0fe`, σ=86) con 55 tests más — **correlación, no causa aislada**: entre las dos series entraron el arreglo de `pdftotext` *y* los 55 tests, y las tres series con sus seis campos están en [`RESULTS.md`](RESULTS.md). Números en [`RESULTS.md`](RESULTS.md), método en [`docs/metrics.md`](docs/metrics.md) |
| L5 `extract.base` + conformidad + **cuatro** extractores locales + nivel 1 | 14-18 | **CERRADO 2026-08-28** | Primera tabla de estructura con coste y cobertura evaluable | **2.464 unidades sobre 616 documentos**, `uv run docbench report --campaign runs/l5/campana`, con sus cifras en [`runs/l5/informe.json`](runs/l5/informe.json) y la regla R7 de `scripts/derivadas.py` comprobando contra él lo publicado — el titular deja de estar tecleado. **EL TITULAR: 103 de 338 documentos (30,5%) sobre el panel de CUATRO** —`camelot`, `docling`, `pdfplumber`, `pymupdf4llm`— coinciden con la referencia en cuántas tablas hay; el panel va en la etiqueta porque el número **sólo sabe bajar** al añadir extractores (límite 113, pre-registrado antes de que se mueva). *(Se publicó **82 de 338 (24,3%)** y era FALSO: ése es el número de los que PUNTUARON todos, y los 21 de diferencia son `NO_APLICABLE` por la regla de oro 4 presentados como desacuerdo. Lo encontró el escrutinio adversarial; ningún test podía verlo porque ningún fixture tenía una celda combinada. Límite 112.)* **Cobertura evaluable del 23,6% al 38,0%**, así que las cuatro notas NO son comparables entre sí: para eso está la cara a cara sobre los **82**, donde **el orden cambia**. **Fallos 0/0/0/0**, contados recorriendo los diarios, con el cero atacado por el aro `extract_no_lanza`. **Coste: 0,00 € medido**, 2,30 h de reloj contra **4,011 h** pre-registradas (**+74,6%** contra lo medido). **Tasa de tabla no presente en la referencia**, que el pre-registro pedía y no se publicaba: ~3% en los cortos y ~18% en 11-50, con Wilson donde es muestra. **28 mutantes al cerrar L5**, todos mueren, control negativo 0, sello `5550ca2`; **seis nuevos contra el instrumento que emite la tabla**, que hasta ahora no tenía ninguno. Puerta: **p90 7845**, n=40, σ=119, y **el techo BAJA por primera vez, 8500 → 8200** ([ADR-0022](docs/adr/0022-el-techo-de-la-puerta.md)). Cierra con cuatro y no con ocho por [ADR-0046](docs/adr/0046-l5-cierra-con-los-extractores-que-caben.md), que transcribe una regla congelada **antes de medir**. Números en [`RESULTS.md`](RESULTS.md) |
| L6 `sample` con McNemar + bootstrap agrupado | 8-10 | PENDIENTE · **va DESPUÉS de L7** (ADR-0042) | Plan congelado y publicado antes de la primera campaña seria | — |
| L7 quickstart: 20 documentos versionados + `make quickstart` | 6-8 | **PENDIENTE, el siguiente** · **ADELANTADO, va antes de L6** (ADR-0042) | De clone a tabla en < 3 min, sin red y sin gastar | — |
| L8 los tres adaptadores hostiles + cableado de `benchcore.core.policy` + fuga de credenciales | ~~10-12~~ **11-14** | PENDIENTE | Los tres bloquean. Ningún secreto en ningún artefacto | **Alcance ampliado en L3 (ADR-0037):** L8 mueve `src/docbench_es/core/policy.py` a `benchcore.core.policy`, con su suite y subiendo el menor de `API_VERSION`. **~1 h 30 min**, y el rango sube porque un cambio en otro repo tiene ida y vuelta |
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
| `from_tei`, `from_text_heuristic` | **cada uno con SU extractor**: `grobid` → TEI, `tesseract` → texto. Ninguno de los dos está en la campaña de L5 | `tests/unit/test_sin_consumidor.py`, por AST |
| ~~`from_markdown`~~ **VALIDADO el 2026-08-26** por `extract.pymupdf4llm`. Tres de tres: también trajo su hallazgo, el marcado dentro del texto de la celda (límite 103) | — | — |
| ~~`from_dataframe`~~ **VALIDADO el 2026-08-26** por `extract.pdfplumber`, y la predicción se cumplió al escribirlo: apareció que `dataframe` faltaba en `FORMATOS_SIN_SPANS` (límite 98) | — | — |
| Campos `page_span` y `caption` | Sin fecha. `page_span` además no está medido (LIMITS 32) | Idem |

**Ninguna cifra publicada puede pasar por ellos**, y lo impide un test, no una
nota. Ver LIMITS 49.

**LA PREDICCIÓN DE ESTA SECCIÓN LLEVA TRES CONFIRMACIONES, Y LAS TRES SON DE CONVERSORES.**
*«El hito que ESCRIBE un módulo no encuentra los bugs que encuentra el que lo CONSUME»*:

| conversor | quién lo estrenó | qué le encontró |
|---|---|---|
| `from_html` | L2, el árbol de TEDS | marcaba mal el **100%** de las cabeceras de PubTabNet |
| `from_dataframe` | L5, `pdfplumber` | `dataframe` faltaba en `FORMATOS_SIN_SPANS` (LIMITS 98) |
| `from_markdown` | L5, `pymupdf4llm` | el marcado llegaba al texto de la celda, **19,5%** (LIMITS 103) |

**Los tres los encontró el CONSUMIDOR, ninguno un guardián.** Quedan dos sin estrenar
—`from_tei` y `from_text_heuristic`—, y ninguno está en la campaña de L5.

> **Aquí ponía CUATRO, y la cuarta fila era `holes`.** No es una confirmación, y hay que
> decir por qué en vez de borrarla y ya: la predicción habla de **lo que encuentra el
> consumidor**, y `holes()` **no tiene consumidor en `src/`** (deuda 11). Sin consumidor
> la predicción no puede confirmarse ni refutarse — no es un contraejemplo, es un caso
> **fuera de su dominio**, y meterlo en la tabla infló el titular de tres a cuatro.
>
> **Y su atribución también estaba mal.** Decía *«L1→su propia auditoría»*. La
> divergencia entre `holes()` y `_invariantes._cobertura` salió de **la poda de `src/`**
> (límite 81), no de la auditoría de L1; lo que sí salió alrededor de L2 fue otra cosa
> —que la justificación de L1, *«`holes()` es lo que L2 usa»*, era falsa porque
> `core.teds` no la llama—.
>
> **Lo que ese caso sí dice, y por eso no desaparece:** que una auditoría encuentra
> defectos donde no hay consumidor que los encuentre. Eso acota la lectura retórica
> —*«sólo el consumidor los encuentra»*—, que es más fuerte que la predicción escrita y
> **no** está sostenida por estas tres filas.
>
> **La clase de fallo es la de siempre**: un titular que cuenta las filas de su tabla sin
> comprobar que todas las filas pertenecen a la tabla. Ver LIMITS 55.

## EL SEGUNDO PATRÓN: LOS ESTIMADORES FALLAN POR EXTRAPOLAR DE UNA MUESTRA PEQUEÑA

Van **dos confirmaciones, en dos hitos distintos y con el mismo mecanismo**, así que deja
de ser una anécdota y pasa a ser algo que mirar antes de publicar la siguiente estimación.

| hito | qué se estimó | pre-registrado | medido | error contra lo medido | de qué muestra extrapolaba |
|---|---|---:|---:|---:|---|
| L3 | tamaño del corpus en disco | 533 MB | **361,9 MB** | **+47,3%** | KB/página de 50 documentos de **6,1 páginas** de media, aplicado a un corpus de **10,30** |
| L5 | reloj de la campaña | 4,01 h | **2,30 h** | **+74,6%** | s/página de B5-bis, medido **un proceso por unidad**, aplicado a un corredor que carga los modelos una vez |

> **Y la fila de L5 estuvo publicada con DOS valores, `+74,5%` y `+74,6%`, en seis
> sitios.** No eran dos mediciones: era la misma división con el **dividendo** redondeado
> y sin redondear —`scripts/poblacion_l5.py` emite 14.439,4 s y publicarlo como «4,01 h»
> da 14.436—. Las dos caían dentro de la resolución declarada, ±0,2 puntos, así que la
> discrepancia **no le chirriaba a nadie**. Ahora el número vive en
> [`runs/l5/reloj.json`](runs/l5/reloj.json) y lo comprueba la regla R8 de
> `scripts/derivadas.py`. Límite 114.

**Las dos van con la MISMA convención**, `(predicho − real) / real`, y eso hace falta
decirlo: el error de L5 se publicó primero como «−43%» —la fracción de la predicción que
sobraba— y puesto al lado del +47,3% de L3 invitaba a leer «éste falló menos» cuando con
el mismo divisor **falló más**. Las dos filas y su fórmula, en `RESULTS.md`.

**El mecanismo, idéntico las dos veces:** una tasa medida sobre una muestra pequeña **con
otra forma que la población** —documentos más cortos allí, un régimen de proceso distinto
aquí—, multiplicada por el tamaño de la población. Ninguno de los dos fallos fue un
descuido: la corrección de L3 a 533 MB fue deliberada y razonada, y el modelo de coste de
L5 salía de una medición real.

**Y las dos veces ganó el estimador más simple.** En L3 la primera proyección (277 MB,
−23,5%) acertó más que la corregida en dos factores; en L5 la proyección lineal por
página acertó al segundo decimal mientras la de por documento no. Descomponer una
proyección **no la mejora** si uno de los factores no es constante en el eje sobre el que
se proyecta.

**Lo que sale de aquí, y no es «estimar mejor»:** una estimación de este repo se publica
**con la forma de la muestra de la que extrapola** —n, y en qué se diferencia de la
población— y se confronta con la medida real en el mismo hito. Las dos están confrontadas
y publicadas, con su dirección y su porcentaje; ninguna desapareció del documento.

**Ningún guardián lo hace cumplir**, igual que el límite 106: es una regla de método. Lo
que sí es comprobable —que el número publicado no se quede viejo— ya lo vigila
`scripts/derivadas.py`.

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
   - **L8b · LA UNIDAD DE ESTRATIFICACIÓN, decidida antes de empezar y no a mitad.**
     L8b son **120 documentos con doble pasada ciega** y es lo que cierra `v0.1.0`,
     o sea el hito más caro en horas de persona del release. Si sus estratos son de
     **documento**, hereda el muestreo en dos etapas de L4 —el estrato garantiza que
     *alguna* tabla del documento tiene spans, no la que salga—. Si son de **tabla**,
     el censo tiene que calcular el estrato **por tabla**, y hoy lo calcula por
     documento: `boe_xml.estratos` corre sobre el XML **entero**.

     **No se resuelve aquí**, porque la respuesta depende de qué se anota en L8b —
     tablas sueltas o documentos completos— y eso es su decisión. Lo que no puede
     pasar es que se descubra con 120 documentos ya repartidos entre anotadores.
     **Precio de la opción «por tabla»: ~1 h** de censo, medido por analogía con lo
     que costó el censo actual.

   - **AL CERRAR L3 · reconciliar las TRES estimaciones de tamaño del corpus
     contra la medida real.** Están publicadas **277 MB** (media de los 50 en
     bruto del censo), **533 MB** (corrección por páginas y estrato) y **254 MB**
     (proyección desde el piloto, 254 KB × 1.000 sobre n=25). La medida del
     piloto se parece a la primera y no a la corrección, o sea que **la corrección
     a 533 pudo pasarse de frenada** — y fue una corrección deliberada, no un
     descuido. Al cerrar se mide el tamaño real en disco y **se explica la
     diferencia**, con el mismo criterio con el que se retiraron los «285 ms»:
     si el 533 estaba mal, se dice por qué. Una cifra que se corrige se publica
     corregida; una cifra que desaparece del documento es la que este repo
     prohíbe.
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

7. **El arnés cubre 218 de 692 tests y su hueco se ensancha; la protección real
   no.** Límite 51, criterio en el 60. Faltaban dos cosas por escribir: **la
   velocidad** y **la segunda contabilidad**. Con las dos:

   | | tests | arnés | % arnés | protegidos por algo | % | sin ningún control |
   |---|---|---|---|---|---|---|
   | al cerrar **L2** | 185 | 162 | 87,6% | 182 | 98,4% | 3 |
   | **L3**, cerrado | 321 | 166 | 51,7% | 318 | 99,1% | 3 |
   | **L4**, cerrado | 384 | 166 | 43,2% | 381 | 99,2% | 3 |
   | delta L3→L4 | **+63** | **0** | **−8,5 puntos** | **+63** | **+0,1 puntos** | **0** |

   **Y las dos series van en direcciones distintas, que es exactamente lo que había
   que saber antes de L5. La divergencia es ESTRUCTURAL, no deterioro**, y hay que
   publicarla diciéndolo: el arnés cae **porque la regla de barreras funciona** —
   cada módulo nuevo trae su control negativo en su propio fichero, en el mismo
   hito, y el mutante que lo mediría por rotura va a plazos con su precio. Sin esa
   frase al lado, un número que baja de 87,6% a 51,7% se lee como decadencia
   cuando lo que describe es una suite que crece más deprisa que su arnés. L3 ha
   añadido **136 tests y UN mutante**, el del grupo de filas: el arnés casi no ha
   crecido, ha crecido la suite por debajo. Pero **los 136 están protegidos**: 4
   por el arnés y **132 por el control negativo de su propio fichero**. Por eso la
   protección no baja. *(Aquí ponía 122, 3 y 119, tres cifras copiadas a mano de una
   versión anterior de la columna de al lado: la tabla dice 185→321 tests, 162→166 arnés
   y 182→318 protegidos. Es el límite 55 en el párrafo que lo explica.)*
   Publicar sólo la primera columna exageraba el hueco; publicar sólo la segunda lo
   escondería.

   **Lo que sigue siendo verdad y hay que vigilar:** «los 29 mutantes mueren» dice
   cada vez menos sobre el conjunto — hoy habla del **31,9%** de la suite. Los
   mismos **3 tests sin ningún control** en las dos fechas son los de
   `test_errors.py`.

   > **Aquí ponía «sólo el 78,1% está medido contra una rotura real».** Ese 78,1%
   > era 164/210, o sea el porcentaje del arnés **cuando la suite tenía 210
   > tests**: una copia a mano de la columna «% arnés» que se quedó vieja mientras
   > la columna se actualizaba sola. Es la quinta aparición del límite 55 en este
   > cierre, y la más difícil de ver, porque el número no cuadraba con nada y por
   > eso no se podía comprobar de un vistazo. **Cuando una cifra ya está en una
   > columna, la prosa la cita, no la repite.**

   **Ya hay tres puntos, y la proyección de L3 se cumplió por poco.** Se publicó
   *«si L4 añadiera tests fuera del arnés al ritmo de L3 y ni un mutante, la
   cobertura del arnés bajaría del 51,7% al entorno del 50%»*. Bajó a **43,2%**,
   o sea **más de lo proyectado**: L4 añadió 63 tests y **cero mutantes**, y 63 de
   63 quedaron fuera del arnés. La proyección erraba porque suponía «al ritmo de
   L3» y L4 fue más extremo: todo lo que añadió son candados de fichero y de
   proceso, que no admiten mutante.

   **La divergencia sigue siendo estructural y ahora se ve mejor**: el arnés cae
   6,1 puntos mientras la protección real sube. Y L5 es un hito más grande (ocho
   extractores) con código de producción de verdad, así que **es el primero que
   puede subir el arnés en vez de bajarlo**. Si no lo sube, deja de ser estructural
   y pasa a ser deterioro: ése es el criterio, escrito antes de medirlo.

   ### ESE CRITERIO SE DECLARA INVÁLIDO PARA L5, Y LAS DOS LECTURAS SE PUBLICAN

   | | tests | arnés | % arnés | protegidos por algo | % | sin ningún control |
   |---|---|---|---|---|---|---|
   | **L5** al cerrar | 653 | 208 | 31,9% | 650 | 99,5% | 3 |

   **Por qué inválido: no nombra su columna.** La tabla tiene una columna «arnés»
   —un recuento— y otra «% arnés» —una fracción—, y *«subir el arnés»* no dice
   cuál. Las dos van en direcciones opuestas en L5, así que elegir la lectura
   **es** elegir el criterio, y elegirlo ahora, con los dos números delante, es
   exactamente contra lo que existe la pre-registración.

   **Y no vale escudarse en la ambigüedad, porque el texto se inclina.** Dice
   *«subir el arnés EN VEZ DE BAJARLO»*, y «en vez de bajarlo» sólo tiene sentido
   si el referente venía bajando. **El recuento nunca bajó: 162, 166, 166.** Lo que
   baja en toda la tabla, y lo que esta deuda entera se dedica a explicar, es el
   porcentaje: 87,6 → 51,7 → 43,2. Así que la lectura a la que apunta el texto es
   la del porcentaje, y **bajo esa lectura L5 FALLA**.

   | lectura | L4 cerrado | L5 hoy | ¿lo cumple? |
   |---|---|---|---|
   | **columna «arnés»**, el recuento | 166 | **208** | **SÍ**, +42 |
   | **columna «% arnés»**, la fracción | 43,2% | **31,9%** | **NO**, −11,3 puntos |

   > **Aquí ponía dos cosas más y las dos eran falsas**, y las encontró el escrutinio del
   > paso 4 leyendo la tabla de ocho líneas más arriba:
   >
   > · *«+41, y es la primera vez que sube desde L2»*. **El recuento subió en L3**: 162 →
   >   166, o sea +4, y la prosa de esta misma deuda lo dice con palabras —«el arnés casi
   >   no ha crecido»—, que es haber crecido. Lo que no subió fue L3→L4, y para eso la
   >   tabla ya tiene su fila de delta.
   >
   > · *«−11,3 puntos, la caída más grande de la serie»*. La serie es 87,6 → 51,7 → 43,2 →
   >   31,9, o sea −35,9, −8,5 y −11,3. **La más grande es L2→L3 con −35,9**, y está en la
   >   tabla de arriba y citada en el párrafo que habla de «un número que baja de 87,6% a
   >   51,7%». Ésta es la segunda.
   >
   > Las dos son la misma forma: prosa que adorna una columna **sin mirar la columna**.

   **Las dos se publican, y se dice cuál falla.** Lo que NO se hace es quedarse con
   la que sale bien: el recuento sube porque L5 escribió seis mutantes contra el
   instrumento del titular, y la fracción baja porque la suite creció +269 tests en
   el mismo hito. Las dos cosas son ciertas a la vez y describen lo mismo.

   **Lo que esto NO decide:** si la divergencia es estructural o deterioro. El
   criterio que iba a decidirlo no era decidible, así que **esa pregunta sigue
   abierta** y no se contesta con una lectura elegida a posteriori. Límite 110.

   ### EL CRITERIO DE L6, REESCRITO ANTES DE QUE L6 EMPIECE

   > **Criterio, pre-registrado el 28 ago 2026:** la columna **`% arnés`** —definida como
   > `dentro / total`, la fracción de tests de `tests/unit` a cuyo fichero apunta algún
   > mutante del `PLAN` de `scripts/mutantes/matar.py`— **no baja más de 5 puntos en
   > NINGUNO de los dos cierres siguientes**, cada uno medido contra el cierre anterior:
   > **L7 contra L5** y **L6 contra L7**.
   >
   > **Y son dos cierres y no uno porque L7 va ANTES que L6** (ADR-0042), cosa que la
   > primera versión de este criterio no miró: decía «al cerrar L6 … respecto al valor con
   > el que cierre L5» y entre esos dos puntos se ejecuta L7 entero. Un criterio con una
   > ventana de dos hitos deja que uno compense al otro, y L7 —20 documentos congelados y
   > su regresión— es exactamente el tipo de hito que esta deuda describe como el que
   > hunde la fracción sin tocar el arnés. Medirlos por separado es lo que impide que el
   > hito que la hunde se esconda detrás del que la sube.
   >
   > **El comando que la calcula, y es el único:**
   > `uv run python scripts/contabilidades.py`, que imprime las dos contabilidades
   > con sus porcentajes y sale de la misma colección que usa el guardián de
   > recuentos. No hay segunda implementación: el script llama a `recuentos()` de
   > `tests/unit/conftest.py`.
   >
   > **Qué pasa si baja más de 5 puntos en cualquiera de los dos:** deja de llamarse
   > estructural y se abre el trabajo del límite 51 —los mutantes a plazos— con su precio
   > en horas. Qué pasa si no baja: se publica y ya, sin declarar victoria sobre la otra
   > columna.
   >
   > **Por qué 5 puntos y no otra cosa:** L3→L4 fueron −8,5 y L4→L5 son −11,3, o
   > sea que la serie viene bajando y 5 puntos es **más estricto que la tendencia**.
   > Un umbral por encima de la tendencia se cumpliría solo. Y L6 es un hito
   > pequeño —8-10 h, el plan de muestreo y su potencia— con código puro y
   > mutable, o sea el tipo de hito en el que un mutante por módulo es barato.
   >
   > **Y lo que este criterio NO mide, dicho antes:** la protección real, que es la
   > segunda columna y la que lleva tres cierres por encima del 99%. Un criterio
   > sobre `% arnés` puede fallar con la protección intacta; por eso se publican
   > las dos y por eso ésta no sustituye a aquélla.

   **De los 445 de fuera, 442 llevan control negativo en su propio fichero.**
   `test_entity_conformance.py` (9) corre la suite contra `AdaptadorRoto`, que
   incumple cinco aros a propósito, y **afirma el conjunto exacto** de
   comprobaciones en rojo — así que borrar o ablandar una comprobación pone el test
   rojo, que es lo que hace un mutante. `test_entity_registry.py` (9) y
   `test_barreras.py` (14) hacen lo mismo. El criterio está declarado en
   `CONTROLES_NEGATIVOS` y verificado por AST; lo que no puede verificar —si el
   control es *fuerte*— está en el límite 60.

   ### La regla, decidida: barreras en el mismo hito, lo demás a plazos

   `ESTADO.md` decía las dos cosas a la vez —«se cierra a plazos» y «cada hito que
   añada módulo añade su mutante»— y en L3 pasó la primera. La regla, en firme:

   > **Un módulo cuyo único trabajo es PONERSE ROJO —una barrera— trae su control
   > negativo en el MISMO hito. El resto se cierra a plazos, con su precio.**

   **Por qué la línea cae ahí.** Código de producción que está mal se delata en lo
   que produce: sale un número raro, se cae un test, alguien lo ve. Una barrera que
   está mal **se delata con silencio**, que es indistinguible de ir bien. Un
   candado que nadie ha visto rojo no es un candado, y eso ya estaba escrito aquí
   abajo para `ancla` y `sin_consumidor`.

   **La forma del control negativo da igual** —un mutante en `scripts/mutantes/` o
   un doble roto en el propio fichero de test, como `AdaptadorRoto`—. Lo que no es
   negociable es que exista en el hito que estrena la barrera.

   **Aplicada a L3, las cuatro barreras nuevas están pagadas EN EL HITO:**

   | Barrera nueva | Su control negativo |
   |---|---|
   | `src/docbench_es/entity/conformance.py` + `_comprobaciones.py` | `AdaptadorRoto`, con sus cinco aros y el conjunto exacto afirmado |
   | `src/docbench_es/entity/registry.py` | adaptadores sin versión y con mayor incompatible, rechazados en carga |
   | `scripts/referencias.py` | `test_barreras.py`: dice que **no** ante una ruta que no existe, y que **sí** ante una que existe |
   | el guardia del árbol de `medir_puerta.py` | `test_barreras.py`: detecta un fichero nuevo en un repo temporal, y el aborto sale con su causa |

   **Las dos últimas se declararon como deuda y no lo eran.** Nacieron en L3, son
   barreras, y por la regla de arriba vencían el mismo día: dejarlas a plazos era
   incumplir la regla en el mismo documento en que se escribe. Se pagaron — seis
   tests en `tests/unit/test_barreras.py`, con las dos direcciones cada una.

   El desglose de los 46, por si alguien busca dónde escribir el primer mutante:

   | Sin mutante | Tests | Qué habría que romper | Precio |
   |---|---|---|---|
   | `types_invariantes` | 7 | las invariantes de `Documento` y la clave | ~25 min |
   | `entity_conformance` | 9 | una comprobación de la suite que no mira nada, o un `NO_EJECUTADA` que pasa | ~25 min |
   | `barreras` | 8 | el barrido que no extrae rutas, o la huella del árbol que no cambia | ~20 min |
   | `boe` | 12 | `fetch` que se salta la autorización, o `discover` que no filtra | ~30 min |
   | `boe_api` | 10 | el ritmo que no espera, o el 404 tratado como fallo | ~25 min |
   | `pairing` | 8 | el umbral invertido, o un descarte que no se cuenta | ~20 min |
   | `boe_xml` | 6 | los spans de valor 1 contados, o el estrato doble | ~15 min |
   | `policy` | 7 | la puerta de egress que deja pasar, o que bloquea siempre | ~15 min |
   | `harvest` | 12 | la reanudación que cuenta dos veces, o la parada que no para | ~30 min |
   | `manifest` | 8 | la atribución que no se exige, o el JSON que no cuadra | ~20 min |
   | `verificar_corpus` | 9 | el verificador que no mira nada y publica «CUMPLE» | ~25 min |
   | `entity_registry` | 8 | el registro tragándose el rechazo por versión, o construyendo lo que descubre | ~20 min |
   | `ancla` | 5 | `unica()` devolviendo el primer índice sin contar | ~10 min |
   | `types` | 5 | `congelar_mapas` que no congela | ~20 min |
   | `errors` | 3 | el enum de fallo con una causa de más o de menos | ~15 min |
   | `sin_consumidor` | 3 | la barrera por AST que no mira los scripts | ~15 min |

   **~5 h 30 min en total** para los dieciséis. No es «~20 min por módulo nuevo»: son
   módulos ya escritos, no futuros. Y no son «tests sin proteger»: son **tests sin
   mutante**, que con la segunda contabilidad delante es otra cosa. `recuentos` salió de esta lista al escribírsele sus tres
   mutantes en este mismo commit, que es cómo se cierra a plazos. **Se cierra a plazos** —cada hito que añada módulo añade
   su mutante— pero éstos ya están en deuda y tienen precio puesto.

   `ancla` y `sin_consumidor` son los que más urgen: son **barreras**, o sea
   código cuyo único trabajo es ponerse rojo, y un candado que no se ha probado
   contra su propia rotura no es un candado.

9. **El guardián de recuentos tiene puntos ciegos, y el tamaño está MEDIDO: 10 de
   22.** Límite 54. Sobre un corpus de 35 frases que alguien escribiría en este
   repo —13 que no son recuentos y 22 que sí—,
   `uv run python scripts/cobertura_patrones.py --detalle` da **0 falsos positivos
   de 13** y **10 escapes de 22**. O sea que **más de cuatro de cada diez formas
   naturales de publicar un recuento no las vigila nadie**.

   Las nueve: «el PLAN tiene N mutantes», «mueren los N mutantes», «N/N», una
   fila de tabla `| Mutantes | N |`, «cubre N de los M tests», «quedan N tests
   fuera», «la suite tiene N tests en total», «hay N reglas en .claude/rules/» y
   «las N reglas se cargan solas».

   **Y la comparación entre fechas, resuelta midiendo en vez de suponiendo.** El
   corpus creció de 30 a 35 frases —la familia `reglas` y la forma que se escapó
   en `RESULTS.md`—, así que la tasa global no se puede comparar con la de ayer.
   El desglose sí: **8 de 19 en el subcorpus original** y **2 de 3 en la familia
   nueva**. Y el precio de estrechar los patrones en `6ebf592`, que era la
   sospecha razonable, es **cero**:
   `uv run python scripts/cobertura_patrones.py --anchos` da 4 falsos positivos y
   9 escapes de 19 contra 0 y 8 hoy.

   **Dos de esos puntos ciegos ya se cobraron su pieza**, y por eso la cifra no es
   teórica: la forma de `ESTADO.md`:15 —«29 mutantes, todos mueren»— se escapaba
   entera, en el documento que el hook `SessionStart` inyecta en cada sesión; y el
   mensaje de error enumeraba sólo lo que veía, así que **corregir lo enumerado
   dejaba `ESTADO.md` en verde mintiendo**. Los dos están tapados; los siete de
   arriba no.

   **Precio de barrerlo, medido sobre lo que costó esta ronda**: cada fraseo son
   ~10 min entre escribir el patrón, comprobar que no genera falsos positivos
   contra el corpus, y correr el control negativo. Siete fraseos ≈ **1 h 10 min**.
   A eso hay que sumarle que el corpus de 30 frases **no es exhaustivo**: es lo
   que un escrutinio adversarial de un agente por familia produjo en una tarde, y
   el número real de fraseos posibles no lo sabe nadie.

   **NO se promete cerrarla.** Barrer siete fraseos no cierra la clase —el español
   no se enumera— y cada patrón nuevo es una oportunidad más de falso positivo,
   que es la dirección grave. Lo que sí se hace: **el mensaje de error dice que la
   lista no está completa y remite a este número**, para que nadie lea lo
   enumerado como el total. Y si un punto ciego se cobra una pieza concreta, se
   tapa ese, como se taparon estos dos.

8. **La tasa de muerte de cada asesino no está medida.** Límite 50. La columna
   «mata SIEMPRE» se calcula con n = 3, y eso llama determinista a un test con
   p = 0,9 el 73% de las veces. El arnés ya trae `--reps` y `--solo` para afinar
   un caso; lo que no hay es un n suficiente por defecto, porque costaría decenas
   de repeticiones por mutante. **No se cierra**: se declara y se usa el flag
   cuando la diferencia entre columnas no se explique sola.

10. **La poda de `src/`: ~600 líneas sin productor ni consumidor.** Límite 81, con
    su medición: 14 de 23 tipos de `types/` no se construyen en ningún punto de
    `src/`, `_campana.py` son 191 líneas de las que sólo `TedsReport` tiene productor,
    y hay 14 ficheros de tres líneas útiles o menos. **Es poda, no rediseño**, y
    vuelven cuando su hito las construya. Los cinco defectos concretos que salieron
    con ella —dos literales huérfanos, una rama inalcanzable, un docstring que
    prometía publicar lo que nadie lee y otro que atribuía `holes()` a `validate`— ya
    están arreglados: eran afirmaciones falsas, no cobertura pendiente.

11. **`holes()` y `_invariantes._cobertura` son dos implementaciones de lo mismo y
    DIFIEREN para tablas mal formadas.** `holes` recorta con `max`/`min`, el colocador
    descarta la celda. Hoy no muerde porque `holes()` **no tiene consumidor en
    `src/`**; su primero es el informe de L5, y ése es el hito que tiene que decidir
    si convergen o si una llama a la otra. **Tocarlo antes es cambiar el
    comportamiento de `validate` a ciegas**, sin nadie que pida el cambio.

12. **`sin_urls` se recoge y no se publica**, y su docstring afirmaba que sí. La
    afirmación está corregida; publicarlo de verdad es trabajo del informe, o sea L5.
    Se conserva la recolección porque es gratis y el dato hará falta.

13. **Tres implementaciones idénticas de `tasa_descarte`** —`src/docbench_es/corpus/pairing.py`,
    `src/docbench_es/corpus/_cosecha.py`, `src/docbench_es/corpus/manifest.py`— y dos de `n_descartados`, en un repo
    cuyo `src/docbench_es/entity/boe.py` dice que «dos copias del mismo dato no pueden divergir».
    Unificarlas es ~30 min y toca tres módulos con tests propios; va con L5.

14. **LA PUERTA ESTÁ EN ROJO POR EL TECHO. LA DECISIÓN NO SE TOMA HOY: SE TOMA EN EL
    CIERRE, CON LAS 40.** Abierta el 29 ago 2026, al entrar la portada.

    **No es un `make fast` que falle**: los 692 tests, el linter, los tipos y el contrato
    de capas están en verde y las 40 corridas salieron con `rc=0`. Lo que suena es la
    **alarma del techo**: p90 **8231** contra **8200** —**31 ms**—, n=40,
    `uv run python scripts/medir_puerta.py`. El paso 1 de ADR-0022 ha valido **498 ms
    de p90** en dos pasadas, así que lo que queda ya no es un defecto: es trabajo.

    **Por qué la decisión NO es de hoy, con el ADR delante.** ADR-0022 dice que el techo
    se re-justifica *«al cerrar cada hito, con las 40 corridas y la fórmula»*, y sus tres
    condiciones de parada están escritas *«medidas en el cierre»*. Lo que hay hoy es una
    medición **pareada con n=5** y **L7 abierto**: elegir concesión con eso es tomar la
    decisión del cierre con un quinto de la muestra.

    **Y dos de las tres concesiones ya están cerradas por medición, no por opinión:**

    | Concesión | Por qué no está sobre la mesa |
    |---|---|
    | gastar una palanca | La única declarada es `max_examples` 100→50 y **vale 44 ms medidos** (ADR-0022, alternativa descartada (b)). Contra ~859 ms pareados es ruido, y reabrirla exige volver a medirla, que cuesta más que los 44 ms |
    | reestructurar | Su primer peldaño —`pytest -n auto`— **se gastó en L5** (ADR-0043). El segundo es mover suites a `full`, del que el propio ADR dice que es lo que el límite 25 llama enseñar a ignorar el rojo |

    **Así que lo que queda es re-justificar el techo con la fórmula, y eso es el cierre.**
    Hasta entonces **`.techos` no se toca** y la portada publica los dos números diciendo
    que la última serie midió por encima, que es lo que tiene que hacer una alarma.

    **Y los 31 ms ni siquiera están medidos, descubierto el 29 ago 2026 restando dos
    números publicados el 24.** El techo se compara contra el **p90**, y la única
    evidencia de reproducibilidad del repo era sobre la **mediana**: las dos series de
    aquel día **difirieron 10 ms en la mediana y 65 ms en el p90**, los dos números en la
    misma tabla y **la resta sin hacer**. **31 es menos de la mitad de 65**, así que con
    una serie no se puede afirmar que la alarma suene. No cambia la decisión —sigue siendo
    del cierre— pero cambia el protocolo: [ADR-0048](docs/adr/0048-el-techo-se-decide-con-dos-series.md)
    pasa el cierre a **dos series de 40**, da el techo por roto **sólo si los dos p90 lo
    pasan** y añade un tercer código de salida para el caso del medio. Límite **119**, y
    **no** es el 116: aquél dice que el término del medio de la fórmula no está medido;
    éste, que el primero no tiene medida de reproducibilidad en la forma en que decide.

    **Lo que sí se ha hecho, porque en el cierre ya no se podría medir:**

    - **El paso 1 de ADR-0022, dos veces.** La primera encontró `censo_paginas.paginas()`
      reparseando 520 KB **cinco veces**; la segunda, **sobre el árbol ya arreglado**,
      encontró un defecto **mayor**: `censo_tablas.tablas()` recorriendo mil XML donde
      bastaba leer el censo publicado —0,27 s → **4,2 ms**—. Haber encontrado uno no
      contestaba si era el único ni si era el mayor, y no era ninguna de las dos.
    - **`mypy` con SU instrumento**, que `--durations` no alcanza: `--timing-stats` dice
      que los 14 módulos nuevos cuestan **35 ms** y que el mayor son 5,9 ms. **No hay
      patología de tipos**; el resto del delta de reloj no es atribuible a ningún módulo.

    Los números y sus corridas, en [`RESULTS.md`](RESULTS.md); el hueco de la fórmula
    —el término «incremento proyectado», que nunca se ha medido— en el **límite 116**.

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
| El techo de la puerta AVISA, el manual BLOQUEA | [`0022`](docs/adr/0022-el-techo-de-la-puerta.md) | Techo vigente: 8200 ms local · 21000 ms en CI, re-justificado en cada cierre con 40 corridas. **Bajó** en L5, la primera vez. **No toca el manual**: §15 y sus 90 s no cambian |
| El techo se decide con **DOS** series de 40 | [`0048`](docs/adr/0048-el-techo-se-decide-con-dos-series.md) | Modifica a 0022 en un punto: roto sólo si **los dos** p90 pasan, y un código 3 para el caso del medio. Las dos series del 24 ago difirieron 10 ms en la mediana y **65 en el p90**, y el techo decide contra el p90 |
| El TEDS negativo se recorta SOLO al publicar | [`0023`](docs/adr/0023-teds-negativo-suelo-al-publicar.md) | El calculo no se toca —romperia el criterio de L2—; `para_publicar()` recorta, y se dice cuantos se recortaron |
| Un documento con varias tablas: la nota es la media | [`0024`](docs/adr/0024-teds-batch-varias-tablas-por-documento.md) | `teds_batch` sobrescribia por clave y la tabla mal extraida desaparecia con cobertura 1,0. Regla de oro 6 rota |
| La portada se GENERA desde `informe.json`, y son dos salidas | [`0047`](docs/adr/0047-la-portada-se-genera-desde-el-informe.md) | `docs/index.html` y el bloque `PORTADA` del README, con **cero** cifras tecleadas y la regla R9 comprobandolas en la puerta. Una portada escrita a mano seria la copia catorce del titular y la primera en quedarse vieja |
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
| 0047 | **Si**: §8 y §11. Anade `report/portada/` al arbol y `docbench portada` a la CLI, que §11 no declaraba. Transcrito en el mismo commit |
| 0024 | **No lo contradice, lo cumple**: §6 ya decia que `evaluable_coverage` es «sobre cuantas TABLAS se pudo calcular» y el codigo contaba documentos. El ADR arregla el codigo, no el manual |

Los 0017 y 0019 son de L0 y L1 y estan en sus cierres.

> **Esta tabla estaba desfasada y decia «los cuatro».** Existen 0013–0026, 0030–0047.
> Enumerarlos mal es exactamente el fallo que la regla de oro 8 persigue: si nadie
> sabe que ADR hay, nadie puede comprobar cual falta por transcribir.

Los numeros 0001 a 0012 estan **reservados** para los doce ADR de §4 del manual.
Se transcriben conforme llega el hito que implementa cada uno.

## Requisito previo, antes del primer `uv sync`

`benchcore` tiene que estar en `https://github.com/marcosmatalab/benchcore`, rama
`main`. Sin el, `uv sync` muere en el primer comando y no hay puerta que valga.

## Inventario real de L3, y por que la estimacion sube

**El plan de diez ficheros que se aprobo no esta escrito en ningun sitio del
repo**: vivio en la conversacion. Eso es la misma familia que el barrido de
referencias persigue —una afirmacion sin fichero detras—, asi que aqui queda el
inventario, que si se puede comprobar: `wc -l` sobre lo que hay.

**Hecho** (lineas medidas el 24 ago 2026, `wc -l`):

| Fichero | Lineas | Estaba en el plan |
|---|---|---|
| `src/docbench_es/entity/base.py` | 268 | si |
| `src/docbench_es/entity/conformance.py` | 116 | si |
| `src/docbench_es/entity/_comprobaciones.py` | 247 | **no**: parte de `conformance.py`, que juntos daban 330 y el limite son 300 |
| `src/docbench_es/entity/registry.py` | 115 | **no**: sale de ADR-0036, el descubrimiento no era de `benchcore` |
| `src/docbench_es/entity/boe_api.py` | 168 | si |
| `src/docbench_es/entity/_sumario.py` | 151 | **no**: parte de `boe_api.py`, que juntos daban 298 |
| `src/docbench_es/entity/boe.py` | 228 | si |
| `src/docbench_es/entity/boe_xml.py` | 121 | si |
| `src/docbench_es/corpus/pairing.py` | 191 | si |
| `entities/boe.yaml` | 66 | si |
| `tests/unit/test_entity_conformance.py` | 172 | si |
| `tests/unit/test_entity_registry.py` | 173 | **no**: el camino de registro necesita su propio fichero |
| `tests/unit/test_boe.py` · `test_boe_api.py` · `test_boe_xml.py` · `test_pairing.py` | 238 · 171 · 98 · 141 | si |
| `tests/unit/_adaptadores_falsos.py` · `_adaptadores_rotos.py` | 170 · 183 | los cuatro falsos si; **partirlos en dos, no** |
| `tests/unit/_boe_falso.py` | 168 | **no**: el doble del origen con la forma real del sumario |
| `tests/unit/test_barreras.py` | 145 | **no**: el control negativo de las dos barreras de scripts |
| `src/docbench_es/corpus/harvest.py` | 300 | si |
| `src/docbench_es/corpus/manifest.py` | 232 | si |
| `src/docbench_es/core/policy.py` | 86 | **no**: sale de ADR-0037, y su motor se muda a `benchcore` en L8 |
| `tests/unit/test_harvest.py` · `test_manifest.py` · `test_policy.py` | 225 · 205 · 127 | los dos primeros si |
| `scripts/referencias.py` · `scripts/sello.py` | 277 · 44 | **no**: salen del quinto entry point fantasma y del `18 de 54` viejo |

**Falta**: nada de codigo. Los diez ficheros del plan estan escritos y sus tests
pasan. Lo que queda es **la cosecha de los 1.000 documentos**, que es tiempo de
reloj y no de teclado, y que **NO SE LANZA SIN AVISAR** (ver «Siguiente paso»).

**Por que sube el rango a 18-23 h.** Es una **estimacion, no una medicion**, y va
con su intervalo por la regla de oro 2. De donde sale: sobre las 16-20 h del plan
se han anadido tres modulos y un script que no estaban —unos 720 lineas y 17
tests—, y el trabajo que generaron alrededor (dos ADR, la transcripcion al manual,
el guardia del arbol en `medir_puerta.py`, el patron de `reglas` en el guardian de
recuentos) es de la misma clase: **no estaba previsto y no era opcional**. Estimo
ese sobrecoste en **2 a 3 h**, que es lo que separa 16-20 de 18-23.

**Lo que NO se pide con esto es recortar.** Se pide que el numero publicado del
hito no se quede viejo mientras el hito crece, que es exactamente la familia de
fallo que L3 lleva cazando desde que empezo.

## Siguiente paso

**`/hito L5`: `extract.base` + conformidad + los ocho extractores locales + nivel 1.**
Criterio del manual (§16): *primera tabla de estructura con coste y cobertura
evaluable*. Ocho y no trece: los otros cinco entran después con `/extractor`, una
tarde cada uno.

> **Y la regla de oro 1 manda aquí más que en ningún otro hito: `docbench-es` NUNCA
> construye un extractor propio.** L5 es exactamente el hito donde eso parecería una
> buena idea. Si lo fuera, el ranking valdría cero.

> **AVISO, y está escrito así para que dentro de dos semanas nadie lea «se arregló»
> donde pone «se aplazó».** Los ~330 ms recuperados compran **un hito de margen, como
> mucho**. La proyección de L5 sigue **intacta**: 14-18 h, ocho extractores con sus
> suites, **~+3.000 ms**. Con el techo en 8.500 y ~300 ms de margen, **L5 lo rompe
> igual**.
>
> **La reestructuración queda APLAZADA, NO CANCELADA**, y sigue siendo **lo primero
> de L5**: `pytest -n auto` con `pytest-xdist`, **medido antes de escribir una sola
> línea de código del hito**. Medirlo después sería medirlo cuando ya no hay margen
> para decidir.

**Y ANTES de comprometerse con ocho extractores, una PRUEBA DE HUMO con uno.** Las 30
tablas de L4 ya tienen verdad derivada congelada y el TEDS de L2 ya está validado
contra PubTabNet. Pasar **`pdfplumber`, el más simple**, sobre esos 30 y sacar el TEDS
contra la verdad derivada son **~2 h** y dan tres cosas que hoy no existen:

- la **primera prueba de extremo a extremo** de la cadena L1→L2→L3→L4 con un consumidor
  real — que es exactamente el patrón que la sección «Construido y NO VALIDADO» de este
  fichero declara: L1 cerró verde y **L2 descubrió que `from_html` marcaba mal el 100%
  de las cabeceras de PubTabNet**;
- el **orden de magnitud del coste por documento**, que es lo que decide si ocho
  extractores caben en las 14-18 h presupuestadas;
- y los **bugs de integración antes** de que ocho extractores los multipliquen.

> **NO SE PUBLICA COMO NÚMERO.** 30 documentos elegidos por riqueza de spans no son
> muestra de nada, y publicar un TEDS de ahí sería justo lo que este repo prohíbe. Es
> **prueba de humo con su límite escrito**, y se dice que lo es.

**Lo que L5 hereda de L4 y no puede ignorar:**

- **LO PRIMERO, y antes de escribir código del hito: `pytest -n auto` medido.** Ver
  el aviso de arriba. Margen actual: **494 ms** sobre un techo de 8.500, contra un
  incremento proyectado de **~+3.000 ms**.

- **Límite 76 · el barrido de mutantes no prueba nada sobre la normalización.**
  40-60 min, con el riesgo de que la suite objetivo no mate al mutante nuevo. L5
  vuelve a tocar ese camino con los ocho extractores.
- **Límite 74 · el número de L4 no es reproducible en un clon frío.** Los cuatro
  comandos necesitan `runs/l3/docs` (362 MB, fuera del repo) y `pdftotext`. L5
  estrena `make quickstart`, que es donde esto se decide de verdad.
- **Límite 29 · el modelo de §6.8 no sabe expresar «un intervalo por métrica» ni el
  desglose por estrato.** 2-3 h más su ADR, y **L5 es quien lo estrena**: el primero
  que rellena `StructureMetrics` de verdad.
- **Límite 66 · la muestra de L4 no puede ver el bug del grupo de filas.** Si L5
  toca el colocador, el instrumento de L4 **no lo va a delatar**: lo delata
  `test_grupo_de_filas.py`, y sólo si se corre.
- **Límite 75 · la comparación de L4 cubre el 53,1% de las celdas.** Un cambio en la
  derivación puede pasar por el 46,9% que no se compara.

**Esta línea decía `/hito L1` con L1 y L2 ya cerrados.** No es cosmético: el hook
`SessionStart` inyecta `ESTADO.md` entero, así que la sesión siguiente lo lee antes
que nada y se pone a rehacer un hito cerrado. Es el mismo argumento de la regla de
oro 8 —gana la fuente que el bucle lee primero— aplicado a este fichero. **Y volvió
a pasar en el cierre de L4**: el diff de este fichero cambiaba una sola cifra y
dejaba L4 en «PENDIENTE, el siguiente» con «—» donde va el número. Lo encontró el
escrutinio adversarial, no una relectura.

Lo que L3 hereda y no puede ignorar esta en «Deuda abierta», arriba: el techo de
8500 ms se re-justifica con `scripts/medir_puerta.py`, y los limites 42 (coste de
TEDS por tamaño), 51 (el arnes cubre 162 de 192) y 52 (el criterio de L2 no valida
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
