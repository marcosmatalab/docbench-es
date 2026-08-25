#!/usr/bin/env bash
# PostToolUse en Write|Edit|NotebookEdit: comprueba SOLO el fichero tocado.
# Se invoca con `uv run --no-sync` porque en un proyecto uv las herramientas NO
# están en el PATH: invocarlas peladas devolvía "command not found" disfrazado
# de error de lint en CADA edición.
set -uo pipefail

#   UNA PROTECCIÓN QUE NO DICE CUÁNTO PROTEGE ES INDISTINGUIBLE DE NO PROTEGER NADA.
# Este guardián no va por globs de contenido sino por extensión, así que su forma de
# tener alcance cero es otra: que `uv` o `.venv` no estén y se salga en silencio. Eso
# es exactamente lo que `--cuantos` tiene que delatar.
if [ "${1:-}" = "--cuantos" ]; then
  cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0
  N=$(git ls-files -o -c --exclude-standard -- '*.py' 2>/dev/null | wc -l)
  echo "vigila: los *.py que se editen con Write|Edit|NotebookEdit ($N en el árbol)"
  echo "corre sobre el fichero tocado: ruff check + ruff format --check + mypy"
  command -v uv >/dev/null 2>&1 || { echo "AHORA MISMO NO VIGILA NADA: falta uv"; exit 0; }
  [ -d .venv ] || { echo "AHORA MISMO NO VIGILA NADA: falta .venv"; exit 0; }
  command -v jq >/dev/null 2>&1 || { echo "AHORA MISMO NO VIGILA NADA: falta jq"; exit 0; }
  echo "ahora mismo: activo"
  exit 0
fi

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
