#!/usr/bin/env bash
# LA HUELLA DEL ÁRBOL QUE MIRA LA PUERTA. Una sola vez, para dos guardianes.
#
# La escriben `stop-gate.sh` —cuando `make fast` pasa— y la leen tanto él como
# `guard-commit.sh`. Vivía dentro de `stop-gate.sh`; se saca aquí porque en cuanto la
# necesitó un segundo guardián, copiarla habría creado dos definiciones de «el árbol no
# ha cambiado» que se irían por su lado en el primer retoque. Un guardián que compara
# contra una huella distinta de la que se escribió no compara nada.
#
#   .claude/hooks/huella-puerta.sh          -> imprime la huella
#   .claude/hooks/huella-puerta.sh --que    -> imprime QUÉ entra en ella
#
# La huella es del CONTENIDO, no del listado de `git status`: con el listado, un fichero
# que ya figuraba como ` M` seguía figurando igual por mucho que se rompiera después.
# Y el filtro `'*.py'` a secas dejaba fuera la configuración, así que romper
# `.importlinter` o `pyproject.toml` tampoco invalidaba la marca.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

CONFIG="pyproject.toml .importlinter Makefile uv.lock"

if [ "${1:-}" = "--que" ]; then
  echo "diff de *.py contra HEAD"
  echo "contenido de los *.py sin seguimiento"
  for f in $CONFIG; do echo "contenido de $f"; done
  exit 0
fi

{
  git diff HEAD -- '*.py' 2>/dev/null || true
  git ls-files -o --exclude-standard -- '*.py' 2>/dev/null | sort | while IFS= read -r f; do
    [ -f "$f" ] && { printf '### %s\n' "$f"; cat -- "$f"; }
  done
  # shellcheck disable=SC2086
  cat -- $CONFIG 2>/dev/null || true
} | md5sum | cut -d' ' -f1
