#!/usr/bin/env bash
# SessionStart: inyecta el estado del proyecto como contexto adicional.
# Claude Code NO tiene checkpoint persistente entre sesiones. Esto lo suple.
# NOTA: sin `set -e` a propósito. Con `set -e` + `pipefail`, un `git` que
# devuelve 128 (directorio sin repo) mataba el hook en silencio y la sesión
# arrancaba sin ningún contexto y sin ningún mensaje de error.
set -uo pipefail

IN=$(cat 2>/dev/null || true)
DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
ESTADO="$DIR/ESTADO.md"

if command -v jq >/dev/null 2>&1; then
  SRC=$(printf '%s' "$IN" | jq -r '.source // "startup"' 2>/dev/null || echo startup)
else
  SRC=startup
fi
# Tras un /compact el estado ya está en el resumen: no lo dupliques.
[ "$SRC" = "compact" ] && exit 0

emitir() {  # $1 = texto
  if command -v jq >/dev/null 2>&1; then
    jq -n --arg c "$1" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
  else
    python3 -c 'import json,sys;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.stdin.read()}}))' <<<"$1"
  fi
}

if [ ! -f "$ESTADO" ]; then
  emitir "=== AVISO del hook SessionStart ===
No existe ESTADO.md en $DIR. Ese fichero ES el checkpoint del proyecto: sin él,
cada sesión empieza a ciegas. Créalo con la tabla de hitos del manual antes de
tocar código."
  exit 0
fi

RAMA="$( { git -C "$DIR" branch --show-current 2>/dev/null || true; } )"; RAMA="${RAMA:--}"
SUCIO="$( { git -C "$DIR" status --porcelain 2>/dev/null || true; } | wc -l | tr -d ' ')"
ULTIMO="$( { git -C "$DIR" log -1 --format='%h %s' 2>/dev/null || true; } )"; ULTIMO="${ULTIMO:--}"

emitir "=== ESTADO DEL PROYECTO (inyectado por el hook SessionStart) ===
rama: $RAMA · ficheros sin commitear: $SUCIO · último commit: $ULTIMO

$(cat "$ESTADO")

REGLA: antes de tocar nada, lee el hito EN CURSO de arriba y continúa por ahí.
Si no hay ninguno en curso, propón el siguiente y espera OK."
