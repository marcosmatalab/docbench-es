#!/usr/bin/env bash
# LO QUE LA PUERTA REGISTRA DE SÍ MISMA: su huella, su duración y si fue EN FRÍO.
#
# La huella sola no bastaba, y costó diez commits descubrirlo: la puerta estuvo a
# 25,5 s —tres veces el techo de 8500— desde B5-bis hasta el primer extractor, con
# `medir_puerta.py` funcionando perfectamente. El instrumento sólo se corre al cerrar
# hito, y entre cierre y cierre pasa el trabajo. LIMITS 102.
#
# EN FRÍO NO ES UN DETALLE, ES LA MITAD DEL MECANISMO. Medido sobre `99be97d`, con la
# regresión dentro:
#
#     en frío     30 259 ms     <- lo que mide el techo
#     en caliente  2 781 ms     <- lo que ve quien trabaja
#
# O sea que registrar la duración de un `make fast` cualquiera habría dejado pasar los
# diez commits igual: el 2.781 no pasa del techo ni de lejos. Lo que el aro del commit
# exige, por eso, es una medida **en frío**, que cuesta unos 7 s y se hace una vez por
# commit con `make frio`.
#
#   registrar-puerta.sh --empieza   marca el instante y si las cachés estaban vacías
#   registrar-puerta.sh --acaba     escribe huella, ms y frío/caliente
#   registrar-puerta.sh --que       QUÉ registra y contra qué techo
#   registrar-puerta.sh --techo     el techo, para quien lo necesite
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

INICIO=".claude/.puerta-inicio"
MARCA=".claude/.ultima-puerta"
REGISTRO=".claude/.ultima-puerta.txt"

# El techo local de ADR-0022. Está aquí Y en `scripts/medir_puerta.py --techo`, y son
# dos copias: lo hace cumplir `tests/unit/test_guardianes_por_glob.py`, que se pone rojo
# si dejan de coincidir. Una copia comprobada es una copia; una sin comprobar es un bug
# esperando a que alguien mueva la otra.
TECHO=8500

# Frío es que NO EXISTA NINGUNA de las cuatro cachés, no sólo la de mypy. Con el criterio
# flojo, borrar sólo `.mypy_cache` contaría como frío y la cifra saldría optimista: la
# medida que el techo vigila incluye `.hypothesis`, que no es una caché de velocidad sino
# de lo ya explorado.
CACHES=(.mypy_cache .pytest_cache .ruff_cache .hypothesis)

esta_frio() {
  for c in "${CACHES[@]}"; do [ -e "$c" ] && return 1; done
  return 0
}

case "${1:-}" in
  --techo) echo "$TECHO"; exit 0 ;;
  --que)
    echo "registra: huella del árbol, duración en ms, y frío/caliente"
    echo "frío = no existía ninguna de: ${CACHES[*]}"
    echo "techo (ADR-0022, local): $TECHO ms"
    echo "lo escribe: la receta de \`make fast\`, sólo si TODOS los pasos pasaron"
    if [ -f "$REGISTRO" ]; then
      read -r h ms estado < "$REGISTRO"
      echo "última registrada: $ms ms, $estado, huella ${h:0:8}"
    else
      echo "última registrada: (ninguna)"
    fi
    exit 0 ;;
  --empieza)
    mkdir -p .claude
    estado=caliente
    esta_frio && estado=frio
    printf '%s %s\n' "$(date +%s%3N)" "$estado" > "$INICIO"
    exit 0 ;;
  --acaba)
    mkdir -p .claude
    huella=$("$(pwd)/.claude/hooks/huella-puerta.sh")
    printf '%s' "$huella" > "$MARCA"
    if [ ! -f "$INICIO" ]; then
      # Sin marca de arranque no se INVENTA una duración: se registra sin ella, y el
      # aro del commit la tratará como «no medida», que es lo que es.
      printf '%s - sin-medir\n' "$huella" > "$REGISTRO"
      echo "  puerta verde registrada (sin duración: faltaba la marca de arranque)"
      exit 0
    fi
    read -r t0 estado < "$INICIO"
    ms=$(( $(date +%s%3N) - t0 ))
    printf '%s %s %s\n' "$huella" "$ms" "$estado" > "$REGISTRO"
    rm -f "$INICIO"
    aviso=""
    [ "$estado" = "frio" ] && [ "$ms" -gt "$TECHO" ] && aviso="  ·  PASA DEL TECHO de $TECHO"
    echo "  puerta verde registrada · ${ms} ms en $estado$aviso"
    exit 0 ;;
  *)
    echo "uso: registrar-puerta.sh --empieza|--acaba|--que|--techo" >&2
    exit 2 ;;
esac
