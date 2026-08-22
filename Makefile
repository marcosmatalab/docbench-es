.PHONY: help quickstart fast full test bench report arch types lint fix cov clean
.DEFAULT_GOAL := help

help:  ## esta ayuda
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "};{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

quickstart:  ## de clone a una tabla: 20 documentos versionados, 4 extractores locales, < 3 min, sin red
	uv run docbench run --plan tests/fixtures/quickstart/plan.yaml \
	  --level 1 --extractors pymupdf4llm,pdfplumber,camelot,docling --offline

fast:  ## LA PUERTA: lint + tipos + arquitectura + nucleo puro. < 90 s, sin red, sin Docker
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy --strict src tests
	uv run lint-imports
	uv run pytest tests/unit -q --no-header

full: fast quickstart  ## + contratos, hostiles, secretos, degradacion, deriva y e2e. Con Docker
	uv run pytest tests/contract tests/hostile tests/security tests/degradation tests/drift -q
	uv run pytest tests/e2e -q

test:  ## solo los unitarios
	uv run pytest tests/unit -q

bench:  ## una campana de nivel 1 sobre un plan ya congelado:  make bench PLAN=runs/2026-Q4/plan.yaml
	uv run docbench run --plan $(PLAN) --level 1 --extractors all

report:  ## el informe de una campana en md, html y json:  make report CAMPANA=runs/2026-Q4
	uv run docbench report --campaign $(CAMPANA) --format md,html,json

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
