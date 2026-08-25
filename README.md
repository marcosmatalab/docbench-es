# docbench-es

**Banco de extracción documental en español, adaptable a cualquier entidad.**

Mide cuánto se pierde entre *«el PDF lo dice»* y *«la IA lo contesta»*, y **de quién
es la culpa**: de la extracción de la tabla o del modelo que responde. Los dos fallan,
y hoy nadie mide cuál de los dos. Es para quien tiene miles de PDF en español con
tablas —convenios, pliegos, expedientes, cuentas anuales— y necesita decidir con
números en qué gastar el presupuesto.

<!-- TITULAR:inicio -->
> **5 de 10 hitos de la `v0.1.0` cerrados** — L0, L1, L2, L3, L4 — y el siguiente es **L5**. El último número medido: **25 de 30 coinciden sobre 30 documentos y 1.213 celdas transcritas del PDF** (L4).
>
> Lo que hay medido está en [`RESULTS.md`](RESULTS.md); lo que este proyecto **no** mide, en [`LIMITS.md`](LIMITS.md). **Esta línea se genera desde [`ESTADO.md`](ESTADO.md)**: no se teclea.
<!-- TITULAR:fin -->

## Estado

<!-- ESTADO:inicio -->
| | |
|---|---|
| Release en curso | `v0.1.0` · **5 hitos cerrados** (L0, L1, L2, L3, L4), el último el 2026-08-25. Siguiente: **L5** |
| La puerta | `make fast` en verde. **p90 8006 ms** local sobre `f89c5b6`, techo 8500 (ADR-0022), margen 494 ms, n=40 en frío. El presupuesto del manual son 90 s y es del runner. Procedencia en [`RESULTS.md`](RESULTS.md) |
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
y los extractores que los procesan; hoy no hay CLI y el ejecutable no está declarado,
así que los trabajos `full` y `nightly` de CI nacen dormidos en vez de rojos.

## Por dónde seguir

| Si eres… | Empieza por | Tiempo |
|---|---|---|
| alguien que evalúa si esto es serio | **[Cómo se mide aquí](docs/como-se-mide-aqui.md)** — las cinco reglas y tres casos en que decidieron algo | 3 min |
| alguien que quiere saber si le sirve | [Las cinco cosas que lo hacen distinto](docs/las-cinco-cosas.md), cada una con el hito en que deja de ser promesa | 5 min |
| alguien que va a usar los números | [`RESULTS.md`](RESULTS.md), cada cifra con su comando · y [`LIMITS.md`](LIMITS.md), lo que **no** se mide | 30 min |
| alguien que va a tocar el código | [`docs/reading-order.md`](docs/reading-order.md) · [`MANUAL.md`](MANUAL.md) · [`docs/adr/`](docs/adr/) | 2 h |

Y para saber dónde está el proyecto y cuál es el paso siguiente:
[`ESTADO.md`](ESTADO.md). Qué cambió en cada hito: [`CHANGELOG.md`](CHANGELOG.md).

## Licencia

[Apache-2.0](LICENSE). El contenido de los corpus **no** hereda esta licencia: cada
adaptador de entidad declara la suya en código, y `publish` aborta si no permite
redistribuir.
