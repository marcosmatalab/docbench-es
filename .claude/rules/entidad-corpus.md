---
paths:
  - "src/docbench_es/entity/**/*.py"
  - "src/docbench_es/corpus/**/*.py"
  - "src/docbench_es/sources/**/*.py"
  - "entities/*.yaml"
---

# Reglas de entidad, corpus y fuentes

Aquí es donde el proyecto **toca el mundo**: la red, un origen ajeno, y bytes que
no controlamos. Todo lo demás es determinista; esto no.

> **Esta regla no repite ni una cifra ni una afirmación que viva en otro sitio.**
> Sólo conductas. Los números están en `RESULTS.md`, los límites en `LIMITS.md`, y
> la especificación en `MANUAL.md`. Una regla que copia una cifra es una copia más
> que se queda vieja — que es el bug para el que existe `tests/unit/test_recuentos.py`.

## Antes de escribir nada

- **Antes de diseñar encima de un contrato del repo** —capas, tests, formatos de
  fichero— **se lee la sección del manual que lo define.** No se deduce del fichero
  de configuración. El plan de L3 dedujo del `.importlinter` que los hermanos de
  capa no podían importarse, y `MANUAL.md` explica en su sección de capas que el
  separador elegido significa justo lo contrario, y por qué.

## La red

- **Ningún test de estos módulos toca la red fuera de `tests/e2e`.** Lo dice
  `.claude/rules/tests.md` y no se negocia: si hace falta separar «el origen de hoy
  cumple el contrato» de «el pipeline entero funciona», se usa **un marcador de
  pytest dentro de `tests/e2e`**, no un directorio nuevo.
- **Todo fallo de red se cuenta, con su causa del enum cerrado.** Un fallo tragado
  no es un fallo menos: es **un documento que desaparece del denominador sin que
  nadie lo sepa**, y entonces la tasa que se publique estará calculada sobre una
  población que nadie declaró.
- **Un día del origen que no se pudo consultar no es un descarte**: es un día sin
  publicar, y se cuenta aparte. Confundirlos mueve el denominador.

## Lo que va en el perfil y no en el código

`entities/*.yaml` (§10.1). **Nunca literales en el código** para:

- el **ritmo de petición** y si hay paralelismo;
- los **umbrales** —capa de texto, coherencia PDF/XML— que deciden estrato y descarte;
- el **filtro de secciones**, que es parte de la definición del corpus y no una
  optimización;
- la **licencia** y la **privacidad**, que ya son código por la regla de oro 5.

El motivo es el mismo para todos: son decisiones de la entidad, no del motor, y el
motor tiene que ser agnóstico o «se adapta a cualquier entidad» es una frase.

## Cómo se pide

- **Identificarse.** El `User-Agent` dice qué proyecto es y cómo contactar. Es lo
  que separa a quien cosecha de forma responsable de un scraper anónimo, y es gratis.
- **Tener derecho a los datos y saber pedirlos son cosas distintas.** La licencia va
  en el perfil; el ritmo y lo que diga el `robots.txt` del origen son la otra mitad,
  y se miran **antes** de la primera petición de cada campaña, no después.
- **El ritmo real se mide y se publica**, porque no va a ser el declarado.

## `page_span` y `multipagina`

- **`page_span` no es derivable de un XML**: lo pone quien llama (§9.1). Un
  `page_span` inventado envenena el estrato `multipagina`.
- Por lo mismo, **`multipagina` no se etiqueta desde XML**. Si la fuente no tiene
  páginas, el estrato no se emite — no se aproxima.

## La flota

- **Ningún agente toca nada fuera de esta máquina salvo que el prompt lo autorice
  explícitamente**, y cuando lo autoriza, **el ritmo va en la autorización**.
  Denegar por defecto, no permitir por defecto.
- Pasó lo contrario al preparar L3: un escrutinio en paralelo descargó documentos
  del origen real porque sólo uno de sus frentes tenía prohibida la red. Lo que
  midieron sirve **para decidir**; no entra en ningún número publicado, porque no
  es reproducible: sin commitear, sin manifiesto, y nadie puede re-derivarlo.
