# Orden de lectura

Tres rutas según el tiempo que tengas. La marca 🕓 significa **llega en el hito que
se indica**; ✅, que existe hoy.

<!-- ESTADO:inicio -->
| | |
|---|---|
| Release en curso | `v0.1.0` · **5 hitos cerrados** (L0, L1, L2, L3, L4), el último el 2026-08-25. Siguiente: **L5** |
| La puerta | `make fast` en verde. **p90 8006 ms** local sobre `f89c5b6`, techo 8500 (ADR-0022), margen 494 ms, n=40 en frío. El presupuesto del manual son 90 s y es del runner. Procedencia en [`RESULTS.md`](../RESULTS.md) |
| Dónde va el checkpoint | [`ESTADO.md`](../ESTADO.md), que se actualiza al cerrar cada hito. **Esta tabla se genera desde ahí** con `uv run python scripts/estado_readme.py --escribir` |
<!-- ESTADO:fin -->

## 5 minutos · ¿esto me sirve?

1. [`README.md`](../README.md) — qué es, para quién y qué funciona hoy.
2. [Cómo se mide aquí](como-se-mide-aqui.md) — las cinco reglas y tres casos en que
   decidieron algo. **Es lo que separa este repo de un script con tests.**
3. [Las cinco cosas que lo hacen distinto](las-cinco-cosas.md) — cada una con el hito
   en que deja de ser una promesa.

## 30 minutos · ¿es serio el método?

1. [`RESULTS.md`](../RESULTS.md) — los números medidos, **cada uno con el comando que
   lo reproduce**. Empieza por el criterio del último hito cerrado.
2. [`LIMITS.md`](../LIMITS.md) — lo que este proyecto **no** mide, numerado y con la
   fecha en que se descubrió. Si sólo vas a leer un documento, que sea éste.
3. [`docs/metrics.md`](metrics.md) — qué mide cada métrica, con qué resolución, de
   dónde sale su incertidumbre y **su historial de correcciones**.
4. [`docs/adr/`](adr/) — una decisión por fichero, con su alternativa descartada.
   Los que más se citan: [0015](adr/0015-alcance-de-la-regla-del-intervalo.md) (qué
   número lleva intervalo), [0022](adr/0022-el-techo-de-la-puerta.md) (el techo de la
   puerta y qué hacer al romperlo), [0039](adr/0039-la-adjudicacion-de-discrepancias-de-la-verdad.md)
   y [0040](adr/0040-las-reglas-del-comparador-de-verdad.md) (cómo se adjudica una
   discrepancia contra la verdad de referencia).

## 2 horas · quiero poder cambiarlo

1. [`MANUAL.md`](../MANUAL.md) — la especificación completa: modelo de datos,
   interfaces, métricas e hitos. **Manda sobre cualquier otro documento.**
2. [`CLAUDE.md`](../CLAUDE.md) — las reglas de oro del repo y el contrato de capas,
   que lo verifica el CI y no es cuestión de estilo.
3. [`ESTADO.md`](../ESTADO.md) — dónde está el proyecto, qué se hereda de cada hito y
   la deuda abierta con su tamaño medido.
4. [`HITOS.md`](../HITOS.md) — el prompt literal de cada hito.

### Si vas a contribuir

`make fast` es la puerta y no se cierra un hito con la puerta en rojo. Todo lo demás
—cómo se cierra un hito, qué se congela y cuándo, y por qué una barrera nueva trae su
control negativo el mismo día— está en las cinco reglas de
[Cómo se mide aquí](como-se-mide-aqui.md).
