#!/usr/bin/env bash
# PreToolUse en Write|Edit|NotebookEdit: BLOQUEA la edición de ficheros congelados.
# Los golden files y los planes congelados no se tocan para que salgan los
# números: se corrige el código, no la verdad de referencia.
#
# Congelado = YA EXISTE. Crearlo la primera vez está permitido: si no, los hitos
# que tienen que traer PubTabNet o escribir el plan de muestreo serían imposibles.
set -uo pipefail

es_congelado() {
  case "$1" in
    *tests/fixtures/pubtabnet/*|*tests/fixtures/tablas/*|*tests/fixtures/quickstart/*|*/plan.yaml|*/runs/*/fixtures/*|*/runs/*/congelacion.json|*/runs/*/congelacion_comparador.json|*/runs/*/recongelacion.json|*/runs/*/correcciones.json) return 0 ;;
  esac
  return 1
}

# --- MODO INFORME: CUÁNTOS FICHEROS PROTEGE AHORA MISMO ---------------------
#
#   UNA PROTECCIÓN QUE NO DICE CUÁNTO PROTEGE ES INDISTINGUIBLE DE NO PROTEGER NADA.
#
# Es el modo de fallo POR DEFECTO de cualquier guardián basado en patrones: el glob no
# casa, el guardián NO SE QUEJA —no tiene de qué— y su verde significa «no hay nada
# que vigilar» en vez de «todo está bien». Pasó en este mismo fichero:
# `runs/*/fixtures` protegía CERO ficheros mientras `LIMITS.md` publicaba «arreglado
# en los dos hooks».
#
# Por eso el guardián publica su conjunto, y `tests/unit/test_guardianes_por_glob.py`
# afirma que es > 0 y que contiene lo que tiene que contener. El recuento solo no
# arregla nada: el test es la mitad que lo hace cumplir.
if [ "${1:-}" = "--cuantos" ]; then
  cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0
  git ls-files -o -c --exclude-standard 2>/dev/null | while IFS= read -r f; do
    es_congelado "/$f" && printf '%s\n' "$f"
  done | sort -u
  exit 0
fi

IN=$(cat 2>/dev/null || true)

# Un guardián que no puede comprobar debe FALLAR CERRADO, no ceder.
if ! command -v jq >/dev/null 2>&1; then
  echo "guard-frozen: falta jq, no puedo comprobar si el fichero está congelado. Instala jq." >&2
  exit 2
fi

F=$(printf '%s' "$IN" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
[ -z "$F" ] && exit 0
[ -e "$F" ] || exit 0   # todavía no existe: crearlo es legítimo

if es_congelado "$F"; then
  MSG="FICHERO CONGELADO: $F. Los casos de referencia, las tablas con verdad conocida, los 20 documentos del quickstart y los planes de muestreo no se editan para que cuadren los números. Si el test falla, el fallo está en el código. Si de verdad hay que cambiar la verdad de referencia, pídeselo al usuario explícitamente y explica por qué."
  jq -n --arg m "$MSG" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$m}}'
  printf '%s\n' "$MSG" >&2
  exit 2
fi

exit 0
