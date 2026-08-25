# ADR-0043 · La puerta pasa a paralelo, y la serie lleva su línea de corte

**Fecha:** 2026-08-25 · **Estado:** aceptada e implementada. **No toca el manual**: §15
fija el presupuesto en 90 s y eso no cambia

## Contexto

L4 cerró con **494 ms de margen** bajo el techo de 8500, y L5 trae **ocho
extractores** con sus suites. La proyección dice que L5 lo rompe igual, así que la
reestructuración de ADR-0022 —opción 1, paralelizar— dejó de ser aplazable.

**Y se midió antes de adoptarla, con el umbral escrito antes de medir:** menos de 1,5×
no se adopta, y el número se publica igual para que nadie lo vuelva a proponer dentro
de dos hitos.

| | mediana | rango | n |
|---|---|---|---|
| `pytest tests/unit` en serie | **5591 ms** | 5406–6083 | 5 |
| `pytest tests/unit -n auto` | **2973 ms** | 2734–4650 | 5 |

**1,88×**, con 8 núcleos y `.hypothesis` borrada entre corridas. Pasa el umbral.

## Decisión

**`-n auto` entra en `addopts`, y `pytest-xdist` en el grupo `dev`.**

Y con ella, lo que no se ve y hay que decidir a la vez:

> **ADOPTAR `-n auto` CAMBIA LAS CONDICIONES DE MEDIDA DE TODA LA SERIE.**

Los **1742, 3829, 5593, 7400 y 8006 ms** de `docs/metrics.md` se midieron en serie.
Con la puerta en paralelo, comparar el siguiente número con 8006 es **comparar dos
instrumentos**, no dos versiones del código. Es la familia del límite 55 aplicada a una
serie longitudinal, y la única que tiene este repo.

**Por eso la serie lleva una LÍNEA DE CORTE declarada, con las DOS medidas del mismo
árbol** —serie y paralelo, mismo commit, mismo día— para que el salto sea atribuible al
**instrumento** y no al código. Es una tanda de 40 corridas más, y es el precio de no
romper la serie.

**Cómo se mide en serie después de esto, sin mover el árbol:**

```bash
PYTEST_ADDOPTS="-n 0" make fast
```

## Lo que se paga, y no es sólo tiempo de máquina

- **Se pierde el orden determinista de la salida.** Un fallo ya no aparece en el mismo
  sitio dos veces seguidas, y eso hace más difícil leer una corrida roja.
- **Los tests que tocan ficheros compartidos pueden competir.** Hoy no hay ninguno
  —los que escriben usan `tmp_path`—, pero **es una restricción nueva** sobre lo que se
  puede escribir a partir de ahora, y por eso está aquí y no sólo en el `pyproject`.
- **El arranque de `xdist` cuesta**, así que en una suite pequeña el paralelo puede ser
  más lento. Con 384 tests no lo es; con 40 lo sería.
- **El rango se ensancha**: σ sube porque el reparto entre trabajadores varía. Eso hace
  el p90 más ruidoso, y es exactamente lo que la línea de corte tiene que dejar visible.

## Alternativas descartadas

**Subir el techo.** Es la concesión que ADR-0022 permite y que su paso nuevo obliga a
mirar de último. Aquí no hace falta: hay una medida que dice 1,88×.

**Mover suites lentas a `full`.** Es la opción 2 de ADR-0022 y sigue disponible, pero
saca cobertura de cada PR — el límite 25 la llama enseñar a ignorar el rojo.

**Esperar a que L5 rompa el techo y decidir entonces.** Es lo que se hizo tres veces, y
la razón de que este ADR exista es que decidir con el árbol ya movido es decidir sin
margen.

## Trade-off

Lo que se paga: una tanda de medición extra, el orden determinista de la salida, una
restricción nueva sobre cómo se escriben los tests, y una discontinuidad en la única
serie longitudinal del repo.

Lo que se compra: **1,88× de margen antes de que entren ocho extractores**, y que la
discontinuidad sea **declarada y medida** en vez de descubierta dentro de dos hitos por
alguien que compare 8006 con un número de otro instrumento.
