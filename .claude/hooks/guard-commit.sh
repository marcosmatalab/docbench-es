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
# Y DESDE L5 VIGILA TAMBIÉN EL TECHO, porque verde y rápida son dos cosas. La puerta
# estuvo a 25,5 s —tres veces el techo de 8500— durante diez commits con
# `medir_puerta.py` funcionando: aquél sólo se corre al cerrar hito, y entre cierre y
# cierre pasa el trabajo. LIMITS 102.
#
# LA MEDIDA TIENE QUE SER EN FRÍO, y no es un matiz: sobre `99be97d`, con la regresión
# dentro, `make fast` daba 30.259 ms en frío y 2.781 en caliente. Vigilar la duración de
# un `make fast` cualquiera habría dejado pasar los diez commits igual. Por eso lo que
# se exige es `make frio`, que cuesta unos 7 s una vez por commit.
#
#   .claude/hooks/guard-commit.sh --cuantos   -> QUÉ vigila y contra qué compara
set -uo pipefail

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$DIR" || exit 0

MARCA=".claude/.ultima-puerta"
REGISTRO=".claude/.ultima-puerta.txt"
TECHO=$(.claude/hooks/registrar-puerta.sh --techo 2>/dev/null || echo 8500)

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
  echo "compara contra: $MARCA y $REGISTRO"
  echo "exige ademas: el MINIMO de las corridas EN FRIO (\`make frio\`) de ESTE arbol,"
  echo "              por debajo de $TECHO ms"
  "$DIR/.claude/hooks/registrar-puerta.sh" --que | sed 's/^/  /'
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

# --- El techo, en cada commit y no sólo al cerrar hito -----------------------
[ -f "$REGISTRO" ] || bloquea "HAY VERDE PERO NO HAY MEDIDA DE LA PUERTA, y verde y rápida
son dos cosas distintas. Corre la puerta EN FRÍO, que es la que cuenta contra el techo:

    make frio > /tmp/puerta.txt 2>&1; echo \$?

Cuesta unos 7 s. En caliente NO vale: con la regresión de LIMITS 102 dentro, \`make fast\`
daba 2.781 ms en caliente y 30.259 en frío."

read -r H_REG MS ESTADO N_FRIAS CARGA < "$REGISTRO"
if [ "$H_REG" != "$AHORA" ] || [ "$ESTADO" != "frio" ]; then
  bloquea "LA ÚLTIMA MEDIDA DE LA PUERTA ES ${ESTADO:-desconocida} y hace falta una EN FRÍO
de ESTE árbol. En caliente la puerta no ve su propia regresión: medido sobre 99be97d,
2.781 ms en caliente contra 30.259 en frío, con tres veces el techo dentro.

    make frio > /tmp/puerta.txt 2>&1; echo \$?"
fi
if [ "$MS" != "-" ] && [ "$MS" -gt "$TECHO" ] 2>/dev/null; then
  bloquea "LA PUERTA PASA DEL TECHO: ${MS} ms contra ${TECHO} de ADR-0022, y eso es el
MÍNIMO de ${N_FRIAS:-?} corridas en frío de este árbol, no una corrida con mala suerte.
Carga de la máquina en la última: ${CARGA:-?}.

Verde no es suficiente: la puerta estuvo a 25,5 s durante diez commits con todos los
tests en verde, y eso es lo que LIMITS 102 cuenta. O se arregla la causa —mírala con
\`uv run mypy --strict src tests -v | grep -c \"^LOG:  Parsing\"\`, que es lo que la
encontró la última vez— o se re-justifica el techo en ADR-0022, EN EL MISMO COMMIT.

Si la carga de arriba es alta, la máquina estaba ocupada y la medida no dice nada del
árbol: espera a que termine lo que esté corriendo y repite \`make frio\`. El registro se
queda con el MÍNIMO, así que una corrida buena lo baja y una mala no lo sube. Y ojo — la
carga NO es una excusa: el aro bloquea igual, sólo te dice dónde mirar."
fi
exit 0
