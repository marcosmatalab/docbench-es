---
paths:
  - "src/docbench_es/extract/**/*.py"
---

# Reglas de los extractores

Cada extractor vive en **su propio fichero**, por debajo de 150 líneas, y no sabe nada
de los demás.

- `extract()` **nunca lanza** salvo los errores del enum `ExtractionFailure`. Si falla,
  devuelve `Extraction(failed=True, failure_reason=...)`.
- `expresses_spans` lo fija **el conversor canónico según el formato de origen**, no el
  extractor. Un extractor no puede declararse capaz de algo que su formato no permite.
- `cost_of()` es **puro**: no llama a nada, solo calcula.
- `probe()` comprueba que está instalado y alcanzable **sin procesar ningún documento**.
- Toda la salida pasa por `core.canonical`. Ningún extractor construye una
  `CanonicalTable` a mano.

**El criterio de terminado de un extractor nuevo es uno solo:**
`docbench conform --extractor <id>` en verde. Nada más, y nada menos.

Y la regla que lo mantiene honesto: **el extractor de un cliente pasa exactamente por
el mismo aro que los míos.** Si alguna vez hay un camino privilegiado, la promesa de
extensibilidad del proyecto es mentira.
