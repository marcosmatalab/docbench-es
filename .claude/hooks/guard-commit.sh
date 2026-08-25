#!/usr/bin/env bash
# PreToolUse en Bash: NO SE COMMITEA CON LA PUERTA EN ROJO.
#
# El daño no fue mirar mal el código de salida: fue COMMITEAR EN ROJO. `05ddcdc` entró
# con `test_limite_lineas` caído porque el comando era
#
#     make fast 2>&1 | tail -3 && git commit ...
#
# y el `&&` mira el código de `tail`, que siempre es 0. La clase es «un código de salida
# tragado por una tubería», y va a volver con otro `| head`, otro `| grep`. Mirar mejor
# es una COSTUMBRE; esto es el mecanismo.
#
# El aro no vuelve a correr la puerta —eso costaría segundos en cada commit—: comprueba
# que la última puerta verde registrada es de ESTE árbol, con la misma huella que
# escribe `stop-gate.sh`. Si el árbol cambió desde ese verde, no hay verde para él.
#
#   .claude/hooks/guard-commit.sh --cuantos   -> QUÉ vigila y contra qué compara
set -uo pipefail

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$DIR" || exit 0

MARCA=".claude/.ultima-puerta"

#   UNA PROTECCIÓN QUE NO DICE CUÁNTO PROTEGE ES INDISTINGUIBLE DE NO PROTEGER NADA.
# Este guardián publica su denominador como los demás: qué órdenes intercepta, qué
# entra en la huella y si ahora mismo hay un verde válido.
if [ "${1:-}" = "--cuantos" ]; then
  # Se dice lo que HACE la expresión de abajo, no lo que estaría bien que hiciera.
  # La primera versión de esta línea anunciaba merge, rebase y cherry-pick, y la
  # expresión sólo casa `git commit`: un guardián que declara de más es peor que uno
  # que no declara, porque el de más se cree.
  echo "intercepta: git commit, en cualquier punto de una cadena. NO --dry-run."
  echo "NO intercepta: git merge, rebase ni cherry-pick, que también crean commits"
  echo "compara contra: $MARCA"
  echo "la huella cubre:"
  "$DIR/.claude/hooks/huella-puerta.sh" --que | sed 's/^/  /'
  if [ -f "$MARCA" ] && [ "$(cat "$MARCA")" = "$("$DIR/.claude/hooks/huella-puerta.sh")" ]; then
    echo "ahora mismo: HAY verde para este árbol"
  else
    echo "ahora mismo: NO hay verde para este árbol"
  fi
  exit 0
fi

IN=$(cat 2>/dev/null || true)
command -v jq >/dev/null 2>&1 || exit 0
ORDEN=$(printf '%s' "$IN" | jq -r '.tool_input.command // empty' 2>/dev/null || true)
[ -n "$ORDEN" ] || exit 0

# Sólo lo que CREA un commit. `git log`, `git show` o `git commit --dry-run` no.
printf '%s' "$ORDEN" | grep -Eq '(^|[;&|]|&&)[[:space:]]*git[[:space:]]+(-[^[:space:]]+[[:space:]]+)*commit\b' || exit 0
printf '%s' "$ORDEN" | grep -Eq '\-\-dry-run' && exit 0

bloquea() {
  jq -n --arg r "$1" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}

[ -f "$MARCA" ] || bloquea "NO HAY NINGUNA PUERTA VERDE REGISTRADA, así que no se commitea.
Corre la puerta y MIRA SU CÓDIGO DE SALIDA, no su última línea:

    make fast > /tmp/puerta.txt 2>&1; echo \$?

Un 0 registra el verde y este aro te deja pasar."

AHORA=$("$DIR/.claude/hooks/huella-puerta.sh")
if [ "$(cat "$MARCA")" != "$AHORA" ]; then
  bloquea "EL ÚLTIMO VERDE NO ES DE ESTE ÁRBOL: algo de lo que la puerta mira ha
cambiado desde entonces. No se commitea con la puerta sin comprobar.

    make fast > /tmp/puerta.txt 2>&1; echo \$?

Y se mira el código de salida, no la última línea: \`make fast | tail -3 && git commit\`
devuelve el código de \`tail\`, que siempre es 0. Así entró 05ddcdc en rojo."
fi
exit 0
