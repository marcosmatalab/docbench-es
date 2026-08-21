#!/usr/bin/env bash
# PreToolUse en Write|Edit|NotebookEdit: BLOQUEA la edición de ficheros congelados.
# Los golden files y los planes congelados no se tocan para que salgan los
# números: se corrige el código, no la verdad de referencia.
#
# Congelado = YA EXISTE. Crearlo la primera vez está permitido: si no, los hitos
# que tienen que traer PubTabNet o escribir el plan de muestreo serían imposibles.
set -uo pipefail
IN=$(cat 2>/dev/null || true)

# Un guardián que no puede comprobar debe FALLAR CERRADO, no ceder.
if ! command -v jq >/dev/null 2>&1; then
  echo "guard-frozen: falta jq, no puedo comprobar si el fichero está congelado. Instala jq." >&2
  exit 2
fi

F=$(printf '%s' "$IN" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
[ -z "$F" ] && exit 0
[ -e "$F" ] || exit 0   # todavía no existe: crearlo es legítimo

case "$F" in
  *tests/fixtures/pubtabnet/*|*tests/fixtures/tablas/*|*tests/fixtures/quickstart/*|*/plan.yaml)
    MSG="FICHERO CONGELADO: $F. Los casos de referencia, las tablas con verdad conocida, los 20 documentos del quickstart y los planes de muestreo no se editan para que cuadren los números. Si el test falla, el fallo está en el código. Si de verdad hay que cambiar la verdad de referencia, pídeselo al usuario explícitamente y explica por qué."
    jq -n --arg m "$MSG" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$m}}'
    printf '%s\n' "$MSG" >&2
    exit 2 ;;
esac
exit 0
