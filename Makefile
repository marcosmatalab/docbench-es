# Un `|` dentro de una receta se traga el codigo de salida del comando de la
# izquierda: `make fast | tail` devuelve el de `tail`, que siempre es 0. Asi entro
# 05ddcdc con la puerta en rojo. `pipefail` cierra la clase entera, no el caso.
SHELL := /usr/bin/env bash
.SHELLFLAGS := -o pipefail -c

.PHONY: help quickstart fast frio full test bench report portada arch types lint fix cov clean
.DEFAULT_GOAL := help

help:  ## esta ayuda
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "};{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

quickstart:  ## de clone a una tabla: 20 documentos versionados, 4 extractores locales, < 3 min, sin red
	uv run docbench run --plan tests/fixtures/quickstart/plan.yaml \
	  --level 1 --extractors pymupdf4llm,pdfplumber,camelot,docling --offline

fast:  ## LA PUERTA: lint + tipos + arquitectura + nucleo puro. < 90 s, sin red, sin Docker
	@.claude/hooks/registrar-puerta.sh --empieza
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy --strict src tests
	uv run lint-imports
	uv run pytest tests/unit -q --no-header
# El instrumento registra SU PROPIO verde. Antes lo escribia solo el hook `Stop`,
# asi que un `make fast` a mano dejaba la marca vieja y el aro de `guard-commit.sh`
# bloqueaba un commit con la puerta perfectamente verde. Como esta linea va DESPUES
# de pytest en la misma receta, este paso solo se alcanza si todo lo anterior paso:
# la receta se detiene en el primer comando que devuelve distinto de cero. (Y este
# comentario no puede decir «make <palabra>»: scripts/referencias.py lo leeria como
# un objetivo del Makefile y lo daria por roto. Cazado por el propio barrido.)
	@.claude/hooks/registrar-puerta.sh --acaba

frio:  ## LA PUERTA EN FRIO, que es la que cuenta contra el techo. La exige el aro del commit
# EN FRIO NO ES UN DETALLE. Medido sobre 99be97d, con la regresion de mypy dentro:
# en frio 30.259 ms, en caliente 2.781 ms. Registrar la duracion de un `make fast`
# cualquiera habria dejado pasar los diez commits igual, porque 2.781 no pasa de 8500.
# Cuesta unos 7 s y se hace UNA vez por commit. Ver LIMITS 102.
	@$(MAKE) --no-print-directory clean
	@$(MAKE) --no-print-directory fast

full: fast quickstart  ## + contratos, hostiles, secretos, degradacion, deriva y e2e. Con Docker
	uv run pytest tests/contract tests/hostile tests/security tests/degradation tests/drift -q
	uv run pytest tests/e2e -q

test:  ## solo los unitarios
	uv run pytest tests/unit -q

bench:  ## una campana de nivel 1 sobre un plan ya congelado:  make bench PLAN=runs/2026-Q4/plan.yaml
	uv run docbench run --plan $(PLAN) --level 1 --extractors all

report:  ## el informe de una campana en md, html y json:  make report CAMPANA=runs/2026-Q4
	uv run docbench report --campaign $(CAMPANA) --format md,html,json

portada:  ## regenera la puerta de entrada: docs/index.html y el bloque PORTADA del README
# SIN --escribir COMPRUEBA Y NO ESCRIBE, y eso es lo que corre en la puerta por
# `tests/unit/test_barreras_documentos.py`. Este objetivo es el que SI escribe, y se
# invoca a mano al cerrar un hito. Un comando que sobrescribe artefactos versionados
# no puede ser el modo por defecto: convertiria un rojo en un `git diff` silencioso.
	uv run docbench portada --escribir

arch:  ## solo el contrato de capas
	uv run lint-imports

types:  ## solo el tipado, del codigo Y de los tests
	uv run mypy --strict src tests

lint:  ## solo el linter
	uv run ruff check .

fix:  ## arregla formato e imports
	uv run ruff format .
	uv run ruff check --fix .

cov:  ## cobertura del nucleo puro
	uv run pytest tests/unit --cov=src/docbench_es --cov-report=term-missing -q

clean:  ## borra caches de pytest, mypy, ruff, hypothesis y cobertura
	rm -rf .pytest_cache .mypy_cache .ruff_cache .hypothesis htmlcov .coverage
