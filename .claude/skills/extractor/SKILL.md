---
name: extractor
description: Añade un extractor nuevo al banco. Un fichero, una línea de entry point, y la suite de conformidad en verde.
argument-hint: "[nombre del extractor]"
arguments: [nombre]
allowed-tools: Read, Glob, Grep, Bash, Write, Edit
---

# Extractor nuevo: $nombre

## Extractores ya presentes

!`ls -1 src/docbench_es/extract/ 2>/dev/null | grep -v __ | sed 's/.py$//'`

## Lo que hay que hacer, y nada más

1. **Un fichero**: `src/docbench_es/extract/$nombre.py`, por debajo de **150 líneas**.
2. **Una línea** en `pyproject.toml`, entry point `docbench.extractor`.
3. **Un test** en `tests/contract/` que lo mete en la suite de conformidad.

## Lo que tiene que declarar bien, y aquí está el 90% de los errores

- **`expresses_spans`**: `True` solo si su formato NATIVO puede con `rowspan`/`colspan`.
  Markdown no puede. Texto plano no puede. Un DataFrame no puede. HTML y TEI sí.
  **Si mientes aquí, el extractor recibe un cero donde debería recibir `NO_APLICABLE`,
  y toda la comparación se vuelve injusta.**
- **`extract()` nunca lanza** salvo los errores del enum `ExtractionFailure`. Si falla,
  devuelve `Extraction(failed=True, failure_reason=...)`.
- **La salida pasa por `core.canonical`**. No construyas una `CanonicalTable` a mano.
- **`cost_of()` es puro.** No llama a nada.
- **`probe()`** comprueba instalación y alcance **sin procesar ningún documento**.

## Criterio de terminado, uno solo

```
docbench conform --extractor $nombre
```

En verde. Nada más, y nada menos. No hace falta que saque buena nota: hace falta que
cumpla el contrato. **La nota la decide el banco, no tú.**

Y recuerda la regla que mantiene esto honesto: el extractor de un cliente pasa por
exactamente el mismo aro. Si escribes un atajo para el tuyo, la promesa de
extensibilidad del proyecto es mentira.
