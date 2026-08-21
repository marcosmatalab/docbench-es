# Cómo arrancar este repo con Claude Code

## 1. Crea el repo y descomprime esto dentro

```bash
mkdir docbench-es && cd docbench-es && git init
# descomprime aquí el contenido de docbench-es/
chmod +x .claude/hooks/*.sh
```

**`MANUAL.md` ya viene dentro.** Es la especificación completa y `CLAUDE.md` la importa
con `@MANUAL.md`: sin ese fichero, Claude Code arranca sin especificación.

## 2. Requisitos

```bash
uv --version     # gestor de entorno y de dependencias
jq --version     # lo usan los cuatro hooks. Sin jq, el guardián de ficheros
                 # congelados BLOQUEA por precaución en vez de dejar pasar
git rev-parse --is-inside-work-tree
```

Antes de nada, abre `pyproject.toml` y apunta `[tool.uv.sources] benchcore` a **tu**
repositorio. Existe un paquete ajeno llamado `benchcore` en PyPI: sin esa sección,
`uv sync` instalaría el de otra persona en silencio.

Después:

```bash
uv sync --only-group dev     # las herramientas van en un grupo, no en un extra:
                             # `uv run` NO instala extras por defecto
make fast
```

## 3. Comprueba que la configuración carga

```bash
claude
> /estado
```

Si el hook `SessionStart` funciona, verás el contenido de `ESTADO.md` inyectado sin que
lo pidas.

## 4. Arranca

```
> /hito L0
```

Y a partir de ahí, el bucle de siempre, que está en `HITOS.md`.

## Qué hay aquí

| Fichero | Para qué |
|---|---|
| `MANUAL.md` | La especificación completa. **Es la fuente de verdad**: si el pack y el manual discrepan, manda el manual |
| `CLAUDE.md` | Las reglas del repo. Claude Code lo lee solo en cada sesión |
| `.claude/rules/*.md` | Reglas con `paths:` en el frontmatter: se cargan **solo** cuando Claude toca ficheros que casan con esos globs |
| `.claude/skills/<nombre>/SKILL.md` | Los comandos: `/hito`, `/cerrar`, `/verificar`, `/adr`, `/estado`, `/adversarial` y los propios de este repo |
| `.claude/agents/<nombre>.md` | Los subagentes: `revisor` y `estadistico`. **Ficheros planos**, no directorios |
| `.claude/settings.json` | Permisos y los cuatro hooks |
| `.claude/hooks/*.sh` | El checkpoint al arrancar, la verificación por edición, el guardián de ficheros congelados y la puerta al cerrar el turno |
| `ESTADO.md` | Dónde estamos. **El checkpoint que Claude Code no trae de serie** |
| `HITOS.md` | El prompt exacto de cada hito, para copiar y pegar |
| `Makefile`, `pyproject.toml`, `.importlinter` | La puerta, las herramientas y el contrato de capas |

## Lo que este montaje NO resuelve

- `Bash(uv run *)` está permitido, y `uv run python -c "..."` es ejecución arbitraria:
  puede escribir donde quiera y esquivar el guardián de ficheros congelados, que solo
  escucha en `Write`, `Edit` y `NotebookEdit`. Es el precio de no confirmar cada
  comando. Si te importa más el aislamiento que la fluidez, quita esa regla de `allow`.
- El hook `Stop` corre al final de **cada turno**, no al cerrar un hito. Por eso guarda
  una marca en `.claude/.ultima-puerta` y solo vuelve a pagar `make fast` si ha cambiado
  algún `.py`.
- Los hooks necesitan `jq`. `guard-frozen.sh` falla **cerrado** si no lo encuentra; los
  otros tres se saltan sin hacer nada.
