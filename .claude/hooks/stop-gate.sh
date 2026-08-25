#!/usr/bin/env bash
# Stop: no deja cerrar el turno con un fichero congelado modificado ni con la
# puerta rápida en rojo.
# El contrato de salida del evento Stop es decision/reason DENTRO de
# `hookSpecificOutput`. `additionalContext` NO bloquea nada en Stop: con él,
# este hook era decorativo.
# `stop_hook_active` es obligatorio leerlo: sin ese guardia, un `decision:block`
# con la puerta todavía roja provoca un bucle infinito.
set -uo pipefail

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$DIR" || exit 0

bloquea() {
  jq -n --arg r "$1" \
    '{hookSpecificOutput:{hookEventName:"Stop",decision:"block",reason:$r}}'
  exit 0
}

# --- 1. Ficheros congelados tocados por cualquier vía -----------------------
# `guard-frozen.sh` es PreToolUse con matcher Write|Edit|NotebookEdit, así que
# sólo ve esas tres herramientas: un `cat >`, un `sed -i` o un
# `uv run python -c 'open(...).write(...)'` lo esquivan por completo. No se
# pueden enumerar todas las formas de escribir un fichero; sí se puede mirar el
# resultado. La prevención es best-effort; esta detección es la red.
#
# Hacen falta DOS comprobaciones porque `git diff HEAD` sólo ve lo que ya está
# en HEAD, y un fixture recién creado no lo está durante todo el hito que lo
# crea (L2, L6, L7). Eso dejaba desprotegido justo el hito que más importa.
# `runs/*/fixtures` entró con L4: las 30 tablas transcritas del PDF viven ahí y
# NINGUNO de los dos hooks las veía, mientras el repo afirmaba «congeladas con
# hash». Eso es la regla que gobierna el repo incumplida, no un descuido de globs.
# El candado de verdad es tests/unit/test_congelados_l4.py, que está en la puerta;
# esto es la red de siempre, para las vías que no pasan por Write/Edit.
# `runs/*/fixtures/*` con la BARRA Y EL ASTERISCO FINALES: como pathspec de git,
# `runs/*/fixtures` casa con el DIRECTORIO y no con lo que hay dentro — devuelve 0
# ficheros. La primera versión de este glob lo tenía mal y `LIMITS.md` 70 llegó a
# publicar «arreglado en los dos hooks» con uno de los dos ciego. Comprobado:
#   git ls-files -o -c --exclude-standard -- 'runs/*/fixtures'    -> 0
#   git ls-files -o -c --exclude-standard -- 'runs/*/fixtures/*'  -> 30
#
# Y LOS MANIFIESTOS TAMBIÉN, que es el agujero de verdad: los fixtures se comparan
# CONTRA ellos, así que la forma barata de hacer pasar un fixture manipulado no es
# tocar el fixture, es tocar el manifiesto.
GLOBS=(tests/fixtures/pubtabnet tests/fixtures/tablas tests/fixtures/quickstart
       plan.yaml '*/plan.yaml' 'runs/*/fixtures/*'
       'runs/*/congelacion.json' 'runs/*/congelacion_comparador.json'
       'runs/*/recongelacion.json' 'runs/*/correcciones.json')

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
congelados() { git ls-files -o -c --exclude-standard -- "${GLOBS[@]}" 2>/dev/null | sort -u; }

if [ "${1:-}" = "--cuantos" ]; then
  congelados
  exit 0
fi

IN=$(cat 2>/dev/null || true)
command -v jq >/dev/null 2>&1 || exit 0
[ "$(printf '%s' "$IN" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

if git rev-parse --git-dir >/dev/null 2>&1; then
  # 1a. Congelados YA EN HEAD. `--diff-filter=MDRT`: modificado, borrado,
  # renombrado o cambiado de tipo. La A de añadido se deja fuera a propósito:
  # crear un congelado la primera vez sigue permitido.
  TOCADOS=$(git diff --name-only --diff-filter=MDRT HEAD -- "${GLOBS[@]}" 2>/dev/null || true)

  # 1b. Congelados que AÚN NO ESTÁN EN HEAD: recién creados, con o sin `git
  # add`. Contra un manifiesto de huellas. La primera vez que se ve un fichero
  # se anota su huella y se deja pasar —eso es crearlo—; a partir de ahí,
  # cualquier cambio se caza. Cubre la ventana entera entre crear el fixture y
  # commitearlo, que es donde vivía el agujero.
  MANIF=".claude/.congelados.sha256"
  NUEVOS=$(git ls-files -o -c --exclude-standard -- "${GLOBS[@]}" 2>/dev/null | sort -u || true)
  if [ -n "$NUEVOS" ]; then
    mkdir -p .claude; [ -f "$MANIF" ] || : > "$MANIF"
    while IFS= read -r f; do
      [ -f "$f" ] || continue
      H=$(sha256sum -- "$f" | cut -d' ' -f1)
      PREV=$(grep -F -- "  $f" "$MANIF" 2>/dev/null | cut -d' ' -f1 | head -1)
      if [ -z "$PREV" ]; then
        printf '%s  %s\n' "$H" "$f" >> "$MANIF"   # primera vez: es una creación
      elif [ "$PREV" != "$H" ]; then
        TOCADOS=$(printf '%s\n%s' "$TOCADOS" "$f")
      fi
    done <<< "$NUEVOS"
  fi

  TOCADOS=$(printf '%s' "$TOCADOS" | grep -v '^$' || true)
  if [ -n "$TOCADOS" ]; then
    bloquea "FICHEROS CONGELADOS MODIFICADOS:

$TOCADOS

Son verdad de referencia. Si un test falla contra ellos, el fallo está en el
código, no en el fichero. Revierte:

  git checkout HEAD -- <fichero>     # si ya estaba commiteado
                                     # si no, deshaz el cambio a mano

y arregla el código, o declara el límite en LIMITS.md. Si de verdad hay que
cambiar la verdad de referencia, pídeselo al usuario explícitamente y explica
por qué antes de tocar nada; una vez aprobado, se borra su línea de
$MANIF para volver a fijar la huella."
  fi
fi

# --- 2. La puerta rápida ----------------------------------------------------
command -v make >/dev/null 2>&1 || exit 0
[ -f Makefile ] || exit 0
# Barato y determinista: si no ha cambiado nada de lo que la puerta mira desde
# el último verde, no se vuelve a pagar la puerta entera al final de CADA turno.
#
# La huella es del CONTENIDO, no del listado de `git status`. Con el listado, un
# fichero que ya figuraba como ` M` seguía figurando como ` M` por mucho que se
# rompiera después: misma huella, y la puerta en rojo se colaba entera. Y el
# filtro `'*.py'` a secas dejaba fuera la configuración, así que romper
# `.importlinter` o `pyproject.toml` tampoco invalidaba la marca.
MARCA=".claude/.ultima-puerta"
# La huella vive en su propio fichero desde que la necesitó un SEGUNDO guardián
# (`guard-commit.sh`). Copiarla habría creado dos definiciones de «el árbol no ha
# cambiado» que se irían por su lado al primer retoque.
AHORA=$("$DIR/.claude/hooks/huella-puerta.sh")
[ -f "$MARCA" ] && [ "$(cat "$MARCA")" = "$AHORA" ] && exit 0

LOG=$(mktemp)
if make fast >"$LOG" 2>&1; then
  mkdir -p .claude && printf '%s' "$AHORA" > "$MARCA"
  rm -f "$LOG"; exit 0
fi
COLA=$(tail -25 "$LOG"); rm -f "$LOG"
bloquea "\`make fast\` NO pasa. Últimas líneas:

$COLA

Arréglalo antes de cerrar, o dilo explícitamente al usuario con el error concreto.
No se cierra un hito con la puerta en rojo."
