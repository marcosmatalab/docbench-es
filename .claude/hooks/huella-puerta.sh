#!/usr/bin/env bash
# LA HUELLA DEL ÁRBOL QUE MIRA LA PUERTA. Una sola vez, para dos guardianes.
#
# La escriben `stop-gate.sh` —cuando `make fast` pasa— y la leen tanto él como
# `guard-commit.sh`. Vivía dentro de `stop-gate.sh`; se saca aquí porque en cuanto la
# necesitó un segundo guardián, copiarla habría creado dos definiciones de «el árbol no
# ha cambiado» que se irían por su lado en el primer retoque. Un guardián que compara
# contra una huella distinta de la que se escribió no compara nada.
#
#   .claude/hooks/huella-puerta.sh          -> imprime la huella
#   .claude/hooks/huella-puerta.sh --que    -> imprime QUÉ entra en ella
#
# La huella es del CONTENIDO, no del listado de `git status`: con el listado, un fichero
# que ya figuraba como ` M` seguía figurando igual por mucho que se rompiera después.
# Y el filtro `'*.py'` a secas dejaba fuera la configuración, así que romper
# `.importlinter` o `pyproject.toml` tampoco invalidaba la marca.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

CONFIG="pyproject.toml .importlinter Makefile uv.lock"

# EL ENTORNO FORMA PARTE DE LA HUELLA, y hizo falta descubrirlo con la puerta tres
# commits en rojo. Al instalar `extract-local` para medir B5-bis, `mypy` dejo de dar
# `import-not-found` sobre pdfplumber, torch y compania... SOLO AQUI. CI instala
# `--only-group dev` a proposito, asi que tenia otro entorno y otra respuesta.
#
# Un verde de un entorno NO es un verde de otro, y la huella tiene que decirlo o el aro
# de `guard-commit.sh` deja pasar un commit avalado por un verde que nadie mas puede
# reproducir. Es la misma familia que el numero de trabajadores de `-n auto`: una cifra
# que depende de una condicion no declarada no es reproducible, es irrepetible.
#
# Se listan los NOMBRES de lo instalado, no su contenido: basta para distinguir entornos
# y cuesta un `ls`, no un `uv pip freeze`.
entorno() {
  ls -1 .venv/lib/python*/site-packages 2>/dev/null | sort
  cat .venv/pyvenv.cfg 2>/dev/null || true
}

if [ "${1:-}" = "--que" ]; then
  echo "diff de *.py contra HEAD"
  echo "contenido de los *.py sin seguimiento"
  for f in $CONFIG; do echo "contenido de $f"; done
  echo "nombres de los paquetes instalados en .venv ($(entorno | wc -l) entradas)"
  exit 0
fi

{
  git diff HEAD -- '*.py' 2>/dev/null || true
  git ls-files -o --exclude-standard -- '*.py' 2>/dev/null | sort | while IFS= read -r f; do
    [ -f "$f" ] && { printf '### %s\n' "$f"; cat -- "$f"; }
  done
  # shellcheck disable=SC2086
  cat -- $CONFIG 2>/dev/null || true
  entorno
} | md5sum | cut -d' ' -f1
