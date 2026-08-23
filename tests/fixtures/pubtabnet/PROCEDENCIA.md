# PubTabNet · procedencia de los casos congelados

**Este directorio está CONGELADO.** Si un test falla contra estos ficheros, el
fallo está en el código. No se toca la verdad de referencia para que salgan los
números.

## De dónde sale

| | |
|---|---|
| Origen | `https://github.com/ibm-aur-nlp/PubTabNet`, directorio `src/` |
| Ficheros | `sample_gt.json` (20 tablas reales con su HTML) y `sample_pred.json` (20 predicciones) |
| Descargados | 22 de agosto de 2026, rama `master`, vía `https://raw.githubusercontent.com/…` |
| Licencia | **Apache-2.0**, la del directorio `src/` del repo (`src/LICENSE`) |
| Implementación de referencia | `src/metric.py`, misma licencia. **No se copia a este repo**: se descarga en el momento de generar |

Son **los casos propios de PubTabNet**, que es literalmente lo que pide §9.2 del
manual: *«contra la implementación de referencia de PubTabNet sobre sus propios
casos»*.

## Cómo se regenera

```bash
uv run --with apted --with distance --with lxml python scripts/pubtabnet_golden.py
```

Necesita red **una vez**, para bajar `metric.py`. Los tests de la puerta **no**:
leen `casos.json`, que ya está aquí.

`apted`, `distance` y `lxml` son dependencias de la REFERENCIA, no de este
proyecto. Van por `uv run --with` a propósito: el núcleo es puro y `pyproject.toml`
no las declara, así que nadie puede acabar calculando TEDS con la implementación
ajena por accidente.

Versiones con las que se generó: `apted 1.0.3`, `distance 0.1.3`, `lxml 6.1.2`,
Python 3.12.3.

## Qué hay en `casos.json`

Por cada uno de los 20 casos:

- `gold` y `pred` — las tablas ya en forma canónica, tal y como las devuelve
  `from_html`. Es lo que come `core.teds`.
- `html_canonico_gold` / `html_canonico_pred` — el render canónico que se le dio
  a la referencia. Está aquí para que la comparación sea auditable sin volver a
  ejecutar nada.
- **`canonico`** — `{teds, teds_s}` calculados por la REFERENCIA sobre ese render.
  **Éste es el golden del criterio de aceptación de L2.**
- `original` — `{teds, teds_s}` calculados por la referencia sobre el HTML crudo
  de PubTabNet. **No es un golden**: es la medida de cuánto mueve el número pasar
  por la forma canónica y por las normalizaciones de L1. Ver ADR-0020.

## Por qué el golden es `canonico` y no `original`

Porque si no, L2 no mediría lo que dice medir. La referencia trabaja sobre HTML
crudo y **no normaliza nada**; este proyecto trabaja sobre `CanonicalTable`, cuyo
texto ya pasó por las seis normalizaciones de L1, y cuyo árbol no tiene el
marcado inline que la referencia sí cuenta. Comparando contra `canonico`, los dos
lados ven **el mismo contenido y la misma forma**, así que una diferencia sólo
puede venir del algoritmo, que es lo que §9.2 manda validar.

La diferencia contra `original` está medida y publicada en `RESULTS.md`, con su
descomposición: en 10 de los 20 casos la normalización no cambia ni un texto de
celda y aun así el número difiere, o sea que **la causa dominante es la forma del
árbol, no normalizar**.
