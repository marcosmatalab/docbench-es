#!/usr/bin/env bash
# Stop: no deja cerrar el turno con la puerta rápida en rojo.
# El contrato de salida del evento Stop es decision/reason. `additionalContext`
# NO bloquea nada en Stop: con él, este hook era decorativo.
# `stop_hook_active` es obligatorio leerlo: sin ese guardia, un `decision:block`
# con la puerta todavía roja provoca un bucle infinito.
set -uo pipefail
IN=$(cat 2>/dev/null || true)
command -v jq >/dev/null 2>&1 || exit 0
[ "$(printf '%s' "$IN" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$DIR" || exit 0
command -v make >/dev/null 2>&1 || exit 0
[ -f Makefile ] || exit 0
# Barato y determinista: si no ha cambiado ningún .py desde el último verde,
# no se vuelve a pagar la puerta entera al final de CADA turno.
MARCA=".claude/.ultima-puerta"
AHORA=$( { git -C "$DIR" status --porcelain -- '*.py' 2>/dev/null || true; } | sort | md5sum | cut -d' ' -f1)
[ -f "$MARCA" ] && [ "$(cat "$MARCA")" = "$AHORA" ] && exit 0

LOG=$(mktemp)
if make fast >"$LOG" 2>&1; then
  mkdir -p .claude && printf '%s' "$AHORA" > "$MARCA"
  rm -f "$LOG"; exit 0
fi
COLA=$(tail -25 "$LOG"); rm -f "$LOG"
jq -n --arg r "\`make fast\` NO pasa. Últimas líneas:

$COLA

Arréglalo antes de cerrar, o dilo explícitamente al usuario con el error concreto.
No se cierra un hito con la puerta en rojo." \
  '{hookSpecificOutput:{hookEventName:"Stop",decision:"block",reason:$r}}'
exit 0
