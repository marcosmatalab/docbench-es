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

## PASO 0, ANTES DE ESCRIBIR NADA: PREGÚNTALE A SU CONVERSOR

**¿Qué formato devuelve esta biblioteca DE VERDAD, qué conversor de `core.canonical` lo
recibe, y lo que ese conversor declara coincide con lo que dice `types`?**

No es una formalidad: **es la pregunta que encontró el agujero de cuatro hitos**.
`"dataframe"` faltaba en `types.FORMATOS_SIN_SPANS`, así que una tabla de marco podía
declararse capaz de `rowspan` y `is_wellformed()` la daba por buena — apuntando a
`camelot`, que compite en la campaña. No lo delató ningún guardián: lo delató ir a
escribir el consumidor (LIMITS 98).

Se contesta **ejecutando**, no leyendo la documentación de la biblioteca, y se escribe en
`runs/l5/formatos.yaml` **antes** de escribir el extractor. Si la biblioteca devuelve
algo que no encaja en ninguno de los cinco formatos canónicos, **eso es un hallazgo y no
un detalle de integración**: párate y dilo.

Y `expresses_spans` **no se teclea**: se deriva con `expresa_spans(FORMATO_NATIVO)`, como
en `src/docbench_es/extract/pdfplumber.py`. Así, copiar ese fichero y cambiar el formato no puede mentir
por descuido.

## Lo que hay que hacer, y nada más

1. **Un fichero**: `src/docbench_es/extract/$nombre.py`, por debajo de **150 líneas**.
2. **Una línea** en `pyproject.toml`, entry point `docbench.extractor`.
3. **Un test** en `tests/contract/` que lo mete en la suite de conformidad.
4. **Su fila** en `runs/l5/formatos.yaml`, con lo medido en el paso 0.

**Y el import de la biblioteca va DENTRO de las funciones.** El registro falla cerrado:
un módulo que reviente al importarse tumba el descubrimiento del grupo entero, y
`extract-local` no se instala en la puerta. Lo comprueba
`tests/unit/test_extract_registry.py`, por AST y sobre los extractores registrados.

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
