# ESTADO · docbench-es

> Este fichero lo inyecta el hook `SessionStart` al arrancar cada sesión de Claude
> Code. Es el checkpoint que Claude Code no trae de serie. **Se actualiza al cerrar
> cada hito, con `/cerrar`.**
>
> La tabla sale de §16 del manual. Si aquí y allí no coinciden, **manda el manual**.

## Release en curso: `v0.1.0` · 112 a 144 horas

| Hito | Horas | Estado | Criterio de aceptación | Número medido |
|---|---|---|---|---|
| L0 esqueleto, canon, CI de tres trabajos, `types`, `errors`, contrato de capas | 8-10 | PENDIENTE | `make fast` verde en < 90 s con el repo vacío de lógica | — |
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

## Decisiones tomadas fuera del manual

_(vacío. Cuando haya una, va aquí y como ADR en `docs/adr/`)_

## Requisito previo, antes del primer `uv sync`

`benchcore` tiene que estar en `https://github.com/marcosmatalab/benchcore`, rama
`main`. Sin el, `uv sync` muere en el primer comando y no hay puerta que valga.

## Siguiente paso

`/hito L0`
