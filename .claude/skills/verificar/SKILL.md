---
name: verificar
description: Pasa todas las puertas del repo y dice exactamente qué falla y dónde. Sin arreglar nada.
allowed-tools: Bash, Read
disable-model-invocation: true
---

# Verificación completa

Las herramientas van SIEMPRE con `uv run`: en un proyecto uv no están en el PATH,
y llamarlas peladas devuelve `command not found` disfrazado de puerta rota.

!`echo "── la puerta entera ──"; make fast 2>&1 | tail -40`
!`echo "── cobertura del núcleo puro ──"; uv run --no-sync pytest tests/unit --cov=src/docbench_es --cov-report=term-missing -q 2>&1 | tail -20`

Resume en una tabla: **qué puerta**, **pasa o no**, **el error concreto**, y **el
fichero y la línea**. No arregles nada todavía. Si todo pasa, dilo en una línea.

Y si `lint-imports` falla, avisa en grande: **un import prohibido no es un detalle de
estilo, es una afirmación del README que se acaba de romper.**
