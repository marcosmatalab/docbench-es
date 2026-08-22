# ADR-0013 · `types` es un paquete, no un fichero

**Fecha:** 2026-08-21  ·  **Estado:** aceptada

> Los números 0001 a 0012 están **reservados** para los doce ADR de §4 del
> manual, que ya están decididos y escritos allí. Se transcriben a
> `docs/adr/` conforme llega el hito que implementa cada uno. Este es el primero
> tomado **fuera** del manual, y por eso arranca en el 0013.

## Contexto

§6 del manual dice, literalmente: *"Todo en `src/docbench_es/types.py`, que no
importa nada del proyecto"*, y §8 lo dibuja como un fichero suelto en el árbol.

El modelo de datos de §6 son unas 30 estructuras: referencias y documentos, forma
canónica de tabla, extracción, verdad, preguntas, glosario, plan de muestreo,
campaña, los agregados de los tres niveles y los tres objetos de salida. Escritas
con su docstring —y aquí un docstring no es decoración: es donde vive el *por
qué* de cada campo, que es justo lo que un examinador viene a leer— salen sobre
**340 líneas**.

`CLAUDE.md` dice, también literalmente: *"Ningún fichero por encima de 300 líneas.
Si un módulo crece, se parte."* Las dos reglas no se pueden cumplir a la vez.

Y hay una tercera restricción que estrecha las salidas: el contrato de capas de
`.importlinter` lleva `exhaustive = true`, así que **todo módulo hijo directo de
`docbench_es` tiene que estar listado en `layers`**. Un paquete nuevo sin ubicar
pone el CI en rojo, que es exactamente para lo que está esa opción.

## Decisión

`types` es un **paquete**: `src/docbench_es/types/` con cinco submódulos privados
—`_documento`, `_tabla`, `_verdad`, `_glosario`, `_campana`— y un `__init__.py`
que los reexporta todos con `__all__`.

`docbench_es.types` sigue siendo la **única** superficie de import del modelo de
datos. Nadie de fuera importa `docbench_es.types._loquesea`.

## Alternativa descartada

**Un `types.py` de ~340 líneas, incumpliendo el límite de 300.** Se descarta por
dos razones, y la segunda pesa más que la primera:

1. El límite de 300 líneas no es cosmético en este repo: es lo que ha mantenido a
   `benchcore` legible y lo que obliga a que un módulo tenga un solo tema.
2. Sobre todo: **la regla que gobierna el repo es que lo que el proyecto afirma y
   el código no cumple es el fallo más grave posible.** `CLAUDE.md` afirma 300
   líneas. Dejar un fichero de 340 dentro sería una afirmación incumplida en el
   fichero que define cómo se trabaja aquí, y de ahí en adelante el límite sería
   una sugerencia. Prefiero desviarme de la *forma* del manual —el árbol de §8—
   antes que de una regla de conducta, y dejarlo escrito aquí.

También se descartó **`docbench_es._types/` como paquete privado hermano**:
rompería `exhaustive = true` al ser hijo directo de `docbench_es` sin sitio en
`layers`, y arreglarlo exigiría tocar el contrato de capas. En este repo el
contrato no se toca para que quepa el código; se toca el código.

## Trade-off

**Se pierde la correspondencia literal con el árbol de §8 del manual**, que es un
coste real: alguien que lea el manual y busque `types.py` no lo va a encontrar.
Lo compensa, en parte, que `docbench_es.types` se importe exactamente igual que
antes, así que ningún ejemplo de código del manual queda inválido.

Y se gana una vía nueva de erosión: cinco submódulos son cinco sitios desde los
que alguien puede importar directamente, saltándose el `__init__`. Si eso pasa,
la partición deja de ser un detalle interno y se convierte en API, y mover una
estructura de `_verdad` a `_campana` pasaría a romper a terceros. Por eso la
verificación de abajo no es opcional.

## Cómo se verifica

Dos tests en `tests/unit/test_types.py`, los dos por AST y no por `grep` —el
propio fichero de test contiene la cadena que busca, y un `grep` se delataría a sí
mismo:

- `test_nadie_de_fuera_importa_los_submodulos_privados_de_types` recorre todo
  `src/` y `tests/`, salta lo que esté dentro del paquete `types/` y falla si
  alguien importa `docbench_es.types._*`. **Comprobado que puede ponerse rojo:**
  con un fichero mutante en `core/` que importa `docbench_es.types._tabla`, el
  test falla y nombra al culpable.
- `test_types_no_importa_nada_del_proyecto` mantiene en pie la otra mitad de la
  frase de §6. El contrato de capas **no** cubre esto: `types` está en la capa de
  abajo, así que import-linter le permitiría importar hacia arriba sin quejarse.

Y `make arch` sigue en `4 kept, 0 broken`: el paquete es hijo directo de
`docbench_es`, está listado en `layers`, y sus submódulos son nietos, que es
lo que `exhaustive` no mira.

## Consecuencias

- **Queda prohibido** importar `docbench_es.types._*` desde fuera del paquete
  `types/`. Un test lo hace cumplir.
- Una estructura nueva del modelo de datos entra en el submódulo que le toca por
  tema **y** se añade a `__all__` del `__init__.py`. Si no está en `__all__`, para
  el resto del repo no existe.
- Ningún submódulo de `types/` importa nada de `docbench_es` que no sea el propio
  `types`. `benchcore` sí, que es una dependencia, no el proyecto.
- Si algún día el modelo adelgaza por debajo de las 300 líneas, **esta decisión se
  revierte** y vuelve a ser `types.py`. Este ADR pasaría a *sustituida*.
