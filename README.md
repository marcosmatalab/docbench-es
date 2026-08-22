# docbench-es

> **Hito L0 de 10 de la `v0.1.0`. Todavía no hay número.** Lo que existe hoy es
> el esqueleto, el modelo de datos y la puerta de CI: **ni corpus, ni verdad de
> referencia, ni extractores, ni CLI**. Aquí no va a aparecer una cifra de
> exactitud hasta que existan. Cuando la haya, esta primera línea será el número
> y no el badge. Lo que hay medido hoy está en [`RESULTS.md`](RESULTS.md); lo que
> este proyecto **no** mide, en [`LIMITS.md`](LIMITS.md).
>
> El número que irá aquí, en L10: *"con extracción perfecta X; con el mejor
> extractor real Y; el hueco atribuible a la extracción es Z puntos, IC [a, b]"*.

**Banco de extracción documental en español, adaptable a cualquier entidad.**

Tienes miles de PDFs en español con tablas —convenios, pliegos, expedientes,
cuentas anuales— y quieres que una IA conteste preguntas sobre ellos. El primer
paso es sacar el texto y las tablas del PDF, y hay unas quince herramientas que
lo hacen, de gratis a caras, con un rango de calidad enorme.

Nadie sabe cuál usar con documentos en español, **porque no existe ningún
benchmark en español**. Verificado el 19 de agosto de 2026 contra los cuatro
únicos candidatos: OmniDocBench (981 páginas, 0 en español), DocVQA (equipo
español, documentos en inglés), MDPBench (~200 muestras como techo optimista) y
MORE (unidades de páginas). Lo que sí hay en español es texto **ya extraído**
—LexBOE, BOE-XSUM—, que no mide la extracción.

`docbench-es` lo mide, y mide lo que importa: no qué extractor saca mejor nota
técnica, sino **cuántas respuestas finales pierdes por elegir mal**.

## Las cinco cosas que lo hacen distinto de un estudio de laboratorio

Son el diseño del proyecto, no una descripción de lo que ya corre. **Cada una
lleva el hito en que deja de ser una promesa**: ✅ ya está, 🕓 todavía no. En un
repo que vende rigor, escribir en presente lo que no existe es el peor fallo
posible, más grave que un bug.

1. ✅ **El juez no es concursante.** Este repo no construye ni construirá un
   extractor propio. Si lo hiciera, el ranking valdría cero. Es una regla, no
   código, y se cumple desde el primer día.
2. 🕓 **L3-L4 · Verdad de referencia gratis y auditable.** El BOE publica el mismo
   documento como PDF firmado y como XML con marcado de tabla real, así que va a
   haber miles de documentos con verdad derivada sin anotar una celda a mano. El
   emparejado llega en L3 y la verdad derivada en L4. **Su error frente a
   auditoría humana se mide en L8b**, y hasta entonces nadie sabe cuánto vale.
3. 🕓 **L3 · El motor no sabrá qué es el BOE.** Cualquier entidad entrará por un
   adaptador de siete métodos, con su fuente, su modo de verdad, su licencia, su
   privacidad y su vocabulario. Hoy el `Protocol` ni siquiera está escrito: se
   escribe en L3, antes que su primera implementación.
4. 🕓 **L8 · La licencia y la privacidad serán código.** Cuando un adaptador
   declare `may_send_to_third_party: false`, el motor **rechazará** los
   extractores por API y la campaña no arrancará, con código de salida 2. No será
   una advertencia. Hoy no hay motor, ni CLI, ni `benchcore.core.policy`: la
   cadena entera se cablea en L8.
5. ✅🕓 **Ningún error se traga.** El enum cerrado de causas y el invariante que
   impide registrar un fallo sin causa **ya son código** (`docbench_es.types`,
   L0). Que además **se cuente en el informe** —la tasa de fallo por extractor
   como resultado publicado— llega con el informe, en **L5**.

## Quickstart

```bash
git clone https://github.com/marcosmatalab/docbench-es && cd docbench-es
uv sync --only-group dev
make fast          # la puerta: lint + tipos + arquitectura + núcleo. < 90 s, sin red
```

`make quickstart` —de clone a una tabla en menos de 3 minutos, sin red y sin
gastar— **llega en L7**, que es cuando existen los 20 documentos congelados y los
extractores que los procesan. Hoy falla con `ModuleNotFoundError`, y por eso los
trabajos `full` y `nightly` de CI nacen dormidos en vez de rojos.

## Orden de lectura

Tres rutas, según el tiempo que tengas, en
[`docs/reading-order.md`](docs/reading-order.md): **5 minutos** para saber si
esto te sirve, **30 minutos** para juzgar si el método es serio, **2 horas** para
poder cambiarlo.

## Estado

| | |
|---|---|
| Release en curso | `v0.1.0` · L0 cerrado el 22 ago 2026, L1 a L8b pendientes |
| La puerta | `make fast` en verde, **4,43 s** en el runner de GitHub sobre `28186b9`, presupuesto 90 s. Rango observado sobre código idéntico: 3,41 – 4,43 s (n=4, corte 22 ago 2026). Procedencia y matices en [`RESULTS.md`](RESULTS.md) |
| Dónde va el checkpoint | [`ESTADO.md`](ESTADO.md), que se actualiza al cerrar cada hito |

## Documentos

| Fichero | Qué es |
|---|---|
| [`MANUAL.md`](MANUAL.md) | La especificación completa: modelo de datos, interfaces, métricas, hitos |
| [`RESULTS.md`](RESULTS.md) | Los números medidos, con su máquina y su comando; y las métricas de calidad, con su intervalo |
| [`LIMITS.md`](LIMITS.md) | Lo que este proyecto **no** mide y dónde se rompe |
| [`ESTADO.md`](ESTADO.md) | Dónde estamos y cuál es el siguiente paso |
| [`CHANGELOG.md`](CHANGELOG.md) | Qué cambió en cada hito |
| [`docs/adr/`](docs/adr/) | Una decisión por fichero, con su alternativa descartada |

## Licencia

[Apache-2.0](LICENSE). El contenido de los corpus **no** hereda esta licencia:
cada adaptador de entidad declara la suya en código, y `publish` aborta si no
permite redistribuir.
