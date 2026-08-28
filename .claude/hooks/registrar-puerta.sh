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
# Y SE GUARDA EL MÍNIMO, NO LA ÚLTIMA. Medido nada más montar esto: seis corridas en
# frío sobre el MISMO árbol dieron 6.367, 6.383, 6.819, 7.835, 9.236 y 9.661 ms, con una
# serie de n=40 del mismo árbol en p90 6.866. O sea que **una sola corrida se pasa del
# techo una de cada tres** por contención de la máquina, y un aro que bloquea una de
# cada tres veces sin motivo se acaba sorteando, que es peor que no tenerlo.
#
# El mínimo es el estimador honesto del suelo —la contención sólo SUMA tiempo— y su
# sesgo está declarado: es optimista. Lo que un mínimo NO puede esconder es lo único que
# este aro tiene que cazar: una regresión que multiplica TODAS las corridas, como los
# 25,5 s de LIMITS 102. Repetir `make frio` mejora el mínimo; no lo empeora.
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

# El techo local de ADR-0022. YA NO ESTÁ AQUÍ: se lee de `.techos`, que es su fuente
# única, y lo mismo hacen `scripts/medir_puerta.py` y el workflow de CI. Antes había un
# `TECHO=8500` tecleado aquí y otro en el instrumento, y `test_aro_del_techo.py`
# —NO `test_guardianes_por_glob.py`, que es lo que decía este comentario y era falso—
# comparaba los dos entre sí. Se separaron los dos JUNTOS del ADR y el test siguió verde.
#
# FALLA CERRADO: sin fichero no hay techo, y sin techo no se deja pasar un commit por
# defecto. Un guardián que no puede comprobar no cede.
TECHO=$(grep -E '^TECHO_LOCAL_MS=' .techos 2>/dev/null | cut -d= -f2)
if ! [ "${TECHO:-}" -gt 0 ] 2>/dev/null; then
  echo "no se pudo leer TECHO_LOCAL_MS de .techos: el aro del techo no puede comprobar" >&2
  exit 1
fi

# Frío es que NO EXISTA NINGUNA de las cuatro cachés, no sólo la de mypy. Con el criterio
# flojo, borrar sólo `.mypy_cache` contaría como frío y la cifra saldría optimista: la
# medida que el techo vigila incluye `.hypothesis`, que no es una caché de velocidad sino
# de lo ya explorado.
CACHES=(.mypy_cache .pytest_cache .ruff_cache .hypothesis)

carga() {
  # El `load average` de un minuto. Se registra porque SIN EL un rojo del techo no se
  # puede leer: «esta maquina se ha vuelto lenta» y «esta maquina esta ocupada» son
  # diagnosticos opuestos con el MISMO sintoma. Paso al medir con la campaña de los 616
  # corriendo: el minimo en frio no bajaba de 8.941 ms y la causa no estaba en el arbol.
  #
  # Y NO ES UNA EXCUSA: el aro bloquea igual. Lo que hace la carga es decirle a quien lee
  # si tiene que re-medir en maquina quieta o si tiene que ir a mirar el codigo.
  cut -d' ' -f1 /proc/loadavg 2>/dev/null || echo "?"
}

ms_monotonicos() {
  # MILISEGUNDOS DE CLOCK_MONOTONIC, y por UNA sola definicion: scripts/reloj.py, que
  # llaman tambien medir_puerta.py y fast.yml. Aqui hubo primero un `date +%s%3N` —reloj
  # de PARED midiendo una DURACION— y despues un /proc/uptime, que es BOOTTIME y cuenta
  # el tiempo suspendido. El porque de las dos correcciones esta en scripts/reloj.py.
  #
  # MEDIDO EN ESTA MAQUINA el 27 ago 2026, con la campaña de los 616 corriendo. Dos
  # observaciones del MISMO proceso, separadas por un rato:
  #     el reloj de pared avanzo   1647 s   (12:01:03 -> 12:28:30)
  #     el proceso envejecio       1483 s   (etimes 4380 -> 5863)
  # O sea 164 s que el reloj de pared se invento, por resincronizacion de WSL2 con el
  # anfitrion. `etimes` y `/proc/uptime`, que cuentan ticks, no se enteraron. Si esos
  # 164 s hubieran caido DENTRO de un `make fast`, el aro habria registrado 164 000 ms.
  #
  # LO QUE ESTO ARREGLA NO ES UN NUMERO MALO CONOCIDO. Los bloqueos de 13.957 ms y las
  # cuatro corridas de 13.659 a 16.164 que se descartaron son excursiones de 7 a 10 s, y
  # el salto medido es de 163: los ordenes de magnitud NO cuadran, asi que decir «era el
  # reloj» seria inventarse una causa. Lo que arregla es el DIAGNOSTICO futuro: con un
  # reloj de pared, un numero raro del aro tiene DOS explicaciones posibles —contencion
  # y reloj— y no se pueden separar. Con monotonico solo queda una.
  #
  # `scripts/medir_puerta.py` ya usaba `time.monotonic_ns()`, asi que la serie de n=40
  # que se publica estaba a salvo. El ARO —el que decide si se puede commitear— no lo
  # estaba, y son DOS INSTRUMENTOS QUE MIDEN LO MISMO. Ahora leen el mismo tipo de reloj.
  # Si no esta el reloj no se INVENTA una duracion: se devuelve vacio y quien llama
  # registra `sin-medir`. Es la misma regla que la marca de arranque ausente.
  [ -f scripts/reloj.py ] && python3 scripts/reloj.py
}

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
    echo "lo que compara con el techo: el MINIMO de las corridas en frio de ESE arbol"
    echo "por que el minimo: n=1 se pasa del techo una de cada tres por contencion"
    echo "  (medido: 6367 6383 6819 7835 9236 9661 sobre un arbol con p90 6866 a n=40)"
    if [ -f "$REGISTRO" ]; then
      read -r h ms estado n c < "$REGISTRO"
      echo "registrado ahora: minimo $ms ms, $estado, n=${n:-0} frias, carga ${c:-?}, huella ${h:0:8}"
    else
      echo "registrado ahora: (nada)"
    fi
    exit 0 ;;
  --empieza)
    mkdir -p .claude
    estado=caliente
    esta_frio && estado=frio
    # Sin reloj la marca nace INVALIDA a proposito: un `-` no es un entero, asi que el
    # guardian de `--acaba` la rechaza y se registra `sin-medir`. Escribir el campo vacio
    # dejaria una marca de UN solo campo, y quien la lea por posicion lee el estado como
    # si fuera el instante.
    t0=$(ms_monotonicos); [ -z "$t0" ] && t0="-"
    printf '%s %s\n' "$t0" "$estado" > "$INICIO"
    exit 0 ;;
  --acaba)
    mkdir -p .claude
    huella=$("$(pwd)/.claude/hooks/huella-puerta.sh")
    printf '%s' "$huella" > "$MARCA"
    if [ ! -f "$INICIO" ]; then
      # Sin marca de arranque no se INVENTA una duración: se registra sin ella, y el
      # aro del commit la tratará como «no medida», que es lo que es.
      printf '%s - sin-medir 0 %s\n' "$huella" "$(carga)" > "$REGISTRO"
      echo "  puerta verde registrada (sin duración: faltaba la marca de arranque)"
      exit 0
    fi
    read -r t0 estado < "$INICIO"
    ahora=$(ms_monotonicos)
    [ -z "$ahora" ] && ahora=-1
    # UNA MARCA QUE NO PUEDE SER DE ESTE ARRANQUE NO SE RESTA: se descarta. El uptime
    # sólo crece dentro de un arranque, así que `t0 > ahora` significa una de dos, y las
    # dos invalidan la medida igual:
    #   · la marca la dejó la versión vieja de este hook, que guardaba `date +%s%3N`
    #     —epoch de PARED, del orden de 1,79e12 frente a 3,2e7 de uptime—;
    #   · o la máquina se reinició entre `--empieza` y `--acaba`, y el uptime volvió a 0.
    # Sin esto, la primera daría un `ms` NEGATIVO de doce cifras y el aro lo registraría
    # como si fuera una duración. Es la misma regla que la marca ausente: no se INVENTA.
    if ! [ "$t0" -ge 0 ] 2>/dev/null || [ "$t0" -gt "$ahora" ]; then
      printf '%s - sin-medir 0 %s\n' "$huella" "$(carga)" > "$REGISTRO"
      rm -f "$INICIO"
      echo "  puerta verde registrada (sin duración: la marca de arranque no es de este arranque)"
      exit 0
    fi
    ms=$(( ahora - t0 ))
    rm -f "$INICIO"
    # El mínimo, y SÓLO de este árbol: una medida rápida de otro no dice nada de éste.
    minimo="$ms"; n=0; anterior_estado=caliente
    if [ -f "$REGISTRO" ]; then
      read -r h_prev ms_prev est_prev n_prev _c_prev < "$REGISTRO" || true
      if [ "$h_prev" = "$huella" ]; then
        anterior_estado="${est_prev:-caliente}"
        n="${n_prev:-0}"
        [ "$anterior_estado" = "frio" ] && [ "$ms_prev" -lt "$minimo" ] 2>/dev/null && minimo="$ms_prev"
      fi
    fi
    if [ "$estado" = "frio" ]; then
      n=$((n + 1))
    else
      # Una corrida caliente NO toca el mínimo ni el estado: no mide lo mismo.
      estado="$anterior_estado"
      [ "$anterior_estado" = "frio" ] && minimo="${ms_prev:-$ms}"
    fi
    ahora_carga=$(carga)
    printf '%s %s %s %s %s\n' "$huella" "$minimo" "$estado" "$n" "$ahora_carga" > "$REGISTRO"
    if [ "$n" -gt 0 ]; then
      aviso=""
      [ "$minimo" -gt "$TECHO" ] && aviso="  ·  PASA DEL TECHO de $TECHO"
      echo "  puerta verde registrada · ${ms} ms · carga ${ahora_carga} · mínimo en frío de $n: ${minimo}$aviso"
    else
      echo "  puerta verde registrada · ${ms} ms en caliente · sin medida en frío de este árbol"
    fi
    exit 0 ;;
  *)
    echo "uso: registrar-puerta.sh --empieza|--acaba|--que|--techo" >&2
    exit 2 ;;
esac
