#!/usr/bin/env bash
# PostToolUse en Write|Edit|NotebookEdit: comprueba SOLO el fichero tocado.
# Se invoca con `uv run --no-sync` porque en un proyecto uv las herramientas NO
# están en el PATH: invocarlas peladas devolvía "command not found" disfrazado
# de error de lint en CADA edición.
set -uo pipefail
IN=$(cat 2>/dev/null || true)
command -v jq >/dev/null 2>&1 || exit 0
F=$(printf '%s' "$IN" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
[ -z "$F" ] && exit 0
case "$F" in *.py) ;; *) exit 0 ;; esac
# Un fichero borrado o movido no se comprueba: ruff y mypy dirian "cannot read file"
# y eso llegaria a Claude disfrazado de error de codigo.
[ -f "$F" ] || exit 0

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$DIR" || exit 0
command -v uv >/dev/null 2>&1 || exit 0
[ -d .venv ] || exit 0
UVR=(uv run --no-sync)

OUT=""
if ! R=$("${UVR[@]}" ruff check --output-format concise "$F" 2>&1); then
  case "$R" in *"No such file or directory"*|*"not found"*) : ;; *) OUT+="ruff:
$R
";; esac
fi
if ! "${UVR[@]}" ruff format --check --quiet "$F" >/dev/null 2>&1; then
  OUT+="formato: ejecuta 'uv run ruff format $F'
"
fi
if ! R=$("${UVR[@]}" mypy --strict "$F" 2>&1); then
  case "$R" in *"not found"*) : ;; *) OUT+="mypy:
$(printf '%s' "$R" | head -15)
";; esac
fi

[ -z "$OUT" ] && exit 0
OUT=$(printf '%s' "$OUT" | head -40)
jq -n --arg c "Fichero recién editado con problemas. Arréglalos antes de seguir:
$OUT" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$c}}'
exit 0
