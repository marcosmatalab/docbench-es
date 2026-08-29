# docbench-es

**Banco de extracción documental en español, adaptable a cualquier entidad.**

<!-- PORTADA:inicio -->
> ## 103 de 338 · el titular de L5
>
> Documentos con tabla en los que los **cuatro** extractores —`camelot · docling · pdfplumber · pymupdf4llm`— coinciden con la referencia en **cuántas tablas hay**: el **30,5%**. **El panel va dentro de la etiqueta**, porque el número es una intersección y **sólo sabe bajar** al añadir un extractor: dos valores con paneles distintos no son comparables.
>
> **Las notas de los cuatro no son comparables entre sí**: cada TEDS se calcula sobre lo que ese extractor pudo evaluar, y esa cobertura va de **23,6%** a **38,0%**. Ordenarlas sería un ranking falso; la comparación que vale es la cara a cara sobre los **82** que puntuaron todos, y ahí **el orden cambia**.
>
> **Y este titular se publicó mal:** decía ~~82 de 338~~ y son **103 de 338**. Era otra cuenta —los que *puntuaron* todos—, y ningún test podía verlo porque **ningún fixture tenía una celda combinada**. El commit falso sigue en la historia, con la corrección detrás.
>
> **29** mutantes · **118** límites · **32** ADR · coste **0,00 €** medido, con la predicción del reloj fallando **+74,6%** · puerta p90 **8.231 ms** contra un techo de **8.200**: **la alarma está sonando** y el techo no se ha subido para callarla.
>
> [**La portada entera, en diez minutos**](https://marcosmatalab.github.io/docbench-es/) · [`RESULTS.md`](RESULTS.md) · [`LIMITS.md`](LIMITS.md) · [`runs/l5/informe.json`](runs/l5/informe.json). **Este bloque lo genera `uv run docbench portada`**: no se teclea.
<!-- PORTADA:fin -->

Mide cuánto se pierde entre *«el PDF lo dice»* y *«la IA lo contesta»*, y **de quién
es la culpa**: de la extracción de la tabla o del modelo que responde. Los dos fallan,
y hoy nadie mide cuál de los dos. Es para quien tiene miles de PDF en español con
tablas —convenios, pliegos, expedientes, cuentas anuales— y necesita decidir con
números en qué gastar el presupuesto.

<!-- TITULAR:inicio -->
> **6 de 10 hitos de la `v0.1.0` cerrados** — L0, L1, L2, L3, L4, L5 — y el siguiente es **L7**. El último número medido: **2.464 unidades sobre 616 documentos** (L5).
>
> Lo que hay medido está en [`RESULTS.md`](RESULTS.md); lo que este proyecto **no** mide, en [`LIMITS.md`](LIMITS.md). **Esta línea se genera desde [`ESTADO.md`](ESTADO.md)**: no se teclea.
<!-- TITULAR:fin -->

## Estado

<!-- ESTADO:inicio -->
| | |
|---|---|
| Release en curso | `v0.1.0` · **6 hitos cerrados** (L0, L1, L2, L3, L4, L5), el último el 2026-08-28. Siguiente: **L7** |
| Dónde va el checkpoint | [`ESTADO.md`](ESTADO.md), que se actualiza al cerrar cada hito. **Esta tabla se genera desde ahí** con `uv run python scripts/estado_readme.py --escribir` |
<!-- ESTADO:fin -->

## Empezar

```bash
git clone https://github.com/marcosmatalab/docbench-es && cd docbench-es
uv sync --only-group dev
make fast     # lint + tipos + arquitectura + núcleo puro. Sin red, en unos 8 s
```

Eso es lo que funciona hoy en un clon limpio, y se comprueba en cada cierre clonando
el repo en `/tmp` y corriéndolo allí. **`make quickstart` —de clone a una tabla en
menos de 3 minutos— llega en L7**, que es cuando existen los 20 documentos congelados
que hacen falta para correrlo sin red. La CLI y su ejecutable **ya existen** desde L5
—`uv run docbench --help`—, y lo que sigue faltando para `quickstart` son los documentos,
así que los trabajos `full` y `nightly` de CI siguen naciendo dormidos en vez de rojos
hasta L7.

*(Aquí ponía «hoy no hay CLI y el ejecutable no está declarado», y L5 trajo las dos cosas:
`pyproject.toml` declara `docbench = "docbench_es.cli.main:app"` y `tests/unit/test_cli.py`
ejecuta el `--help` de cada subcomando. Era una afirmación falsa en la puerta de entrada
del repo, y la encontró el escrutinio adversarial de L5, no un guardián.)*

## Por dónde seguir

| Si eres… | Empieza por | Tiempo |
|---|---|---|
| alguien que evalúa si esto es serio | **[Cómo se mide aquí](docs/como-se-mide-aqui.md)** — las cinco reglas y cuatro casos en que decidieron algo | 3 min |
| alguien que quiere saber si le sirve | [Las cinco cosas que lo hacen distinto](docs/las-cinco-cosas.md), cada una con el hito en que deja de ser promesa | 5 min |
| alguien que va a usar los números | [`RESULTS.md`](RESULTS.md), cada cifra con su comando · y [`LIMITS.md`](LIMITS.md), lo que **no** se mide | 30 min |
| alguien que va a tocar el código | [`docs/reading-order.md`](docs/reading-order.md) · [`MANUAL.md`](MANUAL.md) · [`docs/adr/`](docs/adr/) | 2 h |

Y para saber dónde está el proyecto y cuál es el paso siguiente:
[`ESTADO.md`](ESTADO.md). Qué cambió en cada hito: [`CHANGELOG.md`](CHANGELOG.md).

## Licencia

[Apache-2.0](LICENSE). El contenido de los corpus **no** hereda esta licencia: cada
adaptador de entidad declara la suya en código, y `publish` aborta si no permite
redistribuir.
