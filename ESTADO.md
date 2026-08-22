# ESTADO · docbench-es

> Este fichero lo inyecta el hook `SessionStart` al arrancar cada sesión de Claude
> Code. Es el checkpoint que Claude Code no trae de serie. **Se actualiza al cerrar
> cada hito, con `/cerrar`.**
>
> La tabla sale de §16 del manual. Si aquí y allí no coinciden, **manda el manual**.

## Release en curso: `v0.1.0` · 112 a 144 horas

| Hito | Horas | Estado | Criterio de aceptación | Número medido |
|---|---|---|---|---|
| L0 esqueleto, canon, CI de tres trabajos, `types`, `errors`, contrato de capas | 8-10 | **CERRADO 2026-08-22** | `make fast` verde en < 90 s con el repo vacío de lógica | **4,43 s** en el runner de GitHub, corrida [`32572683716`](https://github.com/marcosmatalab/docbench-es/actions/runs/32572683716), commit `28186b9`. **20× de margen**. Con intervalo, n=3 sobre código idéntico: mediana **3,62 s**, rango 3,41 – 4,43 s. Local: 1095 ms en frío, rango 1058–1148, n=10 |
| L1 `core.canonical` + invariantes + conversores de los cinco formatos | 12-16 | PENDIENTE | Solapes, huecos y spans fuera de rango detectados al 100% | — |
| L2 `core.teds` + validación contra PubTabNet | 10-14 | PENDIENTE | Coincide a cuatro decimales con la referencia | — |
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

## Deuda abierta

1. **`benchcore` v0.1.0 es una SEMILLA, no el benchcore del plan.** Estan `types`,
   los cuatro `Protocol`, `registry` y `conform`. **NO estan** `core.policy`,
   `runner`, `core.bootstrap` ni `core.power`. Se anaden cuando su primer
   consumidor los pida, subiendo el MENOR de `API_VERSION`. Ver `DECISIONES.md`
   de ese repo, D-003.
2. **El pack de arranque venia con siete fallos que impedian que `make fast`
   arrancara.** Estan arreglados y documentados uno a uno en `PARCHES.md`, con su
   sintoma exacto y su causa. Leelo antes de tocar `pyproject.toml`.
3. **`Cost` no esta definido en este manual.** Se referencia como
   `benchcore.types.Cost` y no aparece en ninguna seccion. Definido en la semilla
   de `benchcore` derivandolo del `AttemptRecord` de gonogo §6.4, con un campo
   anadido, `measured`, para que cero medido y "no se ha podido medir" no sean el
   mismo valor. Ver `DECISIONES.md`, D-001.
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

## Decisiones tomadas fuera del manual

| Decision | ADR | En una linea |
|---|---|---|
| `types` es un paquete, no un fichero | [`0013`](docs/adr/0013-types-como-paquete.md) | Las ~30 estructuras de §6 salen 340 lineas y `CLAUDE.md` prohibe pasar de 300. `docbench_es.types` sigue siendo la unica superficie de import, y un test lo hace cumplir |

Los numeros 0001 a 0012 estan **reservados** para los doce ADR de §4 del manual.
Se transcriben conforme llega el hito que implementa cada uno.

## Requisito previo, antes del primer `uv sync`

`benchcore` tiene que estar en `https://github.com/marcosmatalab/benchcore`, rama
`main`. Sin el, `uv sync` muere en el primer comando y no hay puerta que valga.

## Siguiente paso

`/hito L1` — `core.canonical`, sus invariantes y los conversores de los cinco
formatos. Criterio: solapes, huecos y spans fuera de rango detectados al 100%.

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
