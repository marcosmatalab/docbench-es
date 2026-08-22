# Orden de lectura

Tres rutas según el tiempo que tengas. Cada una termina en un sitio distinto: la
primera te dice **si esto te sirve**, la segunda **si el método es serio**, la
tercera **te deja poder cambiarlo**.

> **Marcas.** ✅ existe hoy · 🕓 llega en el hito que se indica. A 21 de agosto de
> 2026 el repo está en L0, así que buena parte de la ruta de 2 h está por escribir
> y sería deshonesto no decirlo aquí.

---

## 5 minutos · ¿esto me sirve?

| # | Qué leer | Qué te llevas |
|---|---|---|
| 1 | ✅ [`README.md`](../README.md), las tres primeras líneas | El número. Hoy: que todavía no hay número, y cuál será |
| 2 | ✅ [`RESULTS.md`](../RESULTS.md), la sección *"lo que todavía NO hay aquí"* | Qué está medido y qué no, sin adornos |
| 3 | ✅ [`LIMITS.md`](../LIMITS.md), los límites 4, 10 y 11 | El sesgo de corpus, la falta de potencia y por qué `NO_APLICABLE` no es cero |

**Si después de esto te sirve**, el siguiente paso es `make fast`: la puerta entera
en ~1,7 s en local y 4,43 s en el runner de GitHub, sin red. Las dos cifras y su
rango, en [`RESULTS.md`](../RESULTS.md); el método, en
[`docs/metrics.md`](metrics.md).

---

## 30 minutos · ¿es serio el método?

Esta es la ruta de quien va a juzgar el proyecto, no a usarlo.

| # | Qué leer | Qué demuestra |
|---|---|---|
| 1 | ✅ `MANUAL.md` §1, *"Qué es, y el hueco verificado"* | Que el hueco está comprobado página a página contra los cuatro candidatos, no supuesto |
| 2 | ✅ `MANUAL.md` §4, los doce ADR | Que cada decisión tiene su alternativa descartada escrita |
| 3 | ✅ [`.importlinter`](../.importlinter) | **El corazón del asunto.** Tres prohibiciones, y cada una hace cumplir una afirmación del README. Si `lint-imports` se pone rojo, se ha roto una promesa, no un estilo |
| 4 | ✅ [`src/docbench_es/errors.py`](../src/docbench_es/errors.py) | Que "ningún error se traga" es código: enum cerrado y un código de salida por causa |
| 5 | ✅ [`tests/unit/test_types.py`](../tests/unit/test_types.py) | Cómo se escribe un test aquí: la pregunta no es *qué prueba* sino *qué demuestra* |
| 6 | ✅ `MANUAL.md` §12, *"Métricas: fórmula, supuestos y caso degenerado"* | Que cada métrica declara qué hace cuando la entrada es degenerada |
| 7 | ✅ `MANUAL.md` §14, la tabla de tests | Los tres que casi nadie tiene: degradación, deriva sintética y los tres adaptadores hostiles |
| 8 | ✅ [`docs/metrics.md`](metrics.md) | El método de cada número publicado: qué mide, resolución del instrumento, de dónde sale su incertidumbre, y el historial de correcciones. Hoy sólo el tiempo de la puerta; crece con TEDS en L2 y con exactitud y kappa en L5 y L8b |

**El atajo de un minuto para un examinador con prisa:** §14 del manual y el
`.importlinter`. Uno dice qué se prueba y por qué; el otro impide que deje de
probarse.

---

## 2 horas · quiero poder cambiarlo

| # | Qué leer | Para qué |
|---|---|---|
| 1 | ✅ `MANUAL.md` §6 y [`src/docbench_es/types/`](../src/docbench_es/types/) en paralelo | El modelo de datos entero. Lee el manual y el código a la vez: el código lleva en cada docstring **por qué** el campo es así |
| 2 | ✅ [`docs/adr/`](adr/) | Las decisiones tomadas fuera del manual, una por fichero |
| 3 | ✅ `MANUAL.md` §7, las tres interfaces | `EntityAdapter` (siete métodos), `Extractor`, `AnswerEngine` |
| 4 | ✅ `MANUAL.md` §8, el árbol fichero a fichero | Dónde va cada cosa y por qué el contrato de capas lo obliga |
| 5 | ✅ `MANUAL.md` §9, *"los módulos con lógica no obvia"* | La forma canónica, TEDS, los seis verificadores, las tres señales de deriva |
| 6 | ✅ [`CLAUDE.md`](../CLAUDE.md) y [`.claude/rules/`](../.claude/rules/) | Las reglas de trabajo del repo. Las tres de `rules/` se cargan solas según el fichero que toques |
| 7 | ✅ [`PARCHES.md`](../PARCHES.md) | Los siete fallos del pack de arranque, con su síntoma exacto. Léelo **antes** de tocar `pyproject.toml` |
| 8 | 🕓 `docs/entity-guide.md` — **L3** | Cómo escribir un adaptador de entidad, con un ejemplo entero |
| 9 | 🕓 `docs/extractor-guide.md` — **L5** | Cómo conectar tu propio extractor. Pasa por el mismo aro que los de casa |
| 10 | 🕓 `docs/glossary-guide.md` — **L11** | Cómo construir la capa semántica de una entidad |
| 11 | 🕓 `docs/deployment.md` — **L15** | Los seis perfiles de entorno y qué se pierde en cada uno |

### Si lo que quieres es contribuir

1. ✅ `MANUAL.md` §16, la tabla de hitos con su criterio de aceptación.
2. ✅ [`ESTADO.md`](../ESTADO.md), que dice dónde está el proyecto ahora mismo.
3. ✅ `make fast`. **Es la puerta.** No se cierra un hito con la puerta en rojo.
4. ✅ [`LIMITS.md`](../LIMITS.md). Si descubres un límite construyendo, se apunta
   el mismo día. Es el fichero que más dice de este proyecto.
