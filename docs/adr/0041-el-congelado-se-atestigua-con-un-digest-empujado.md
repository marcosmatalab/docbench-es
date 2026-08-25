# ADR-0041 · Al congelar, lo que va a git es el DIGEST, no el puntero

**Fecha:** 2026-08-25 · **Estado:** aceptada, **sin construir**. Se aplica en la
próxima congelación, que es **L8b**. **No toca el manual**: §16 no dice cómo se
congela; ADR-0039 sí afirma que se congela antes, y esa afirmación es la que aquí se
vuelve comprobable

## Contexto

L4 congeló dos cosas y **sólo una quedó atestiguada**, en el mismo hito y con una
hora de diferencia.

| | Qué se congeló | Cómo quedó |
|---|---|---|
| el **comparador** | ADR-0040, `comparar_verdad.py`, `truth/derived.py` y su suite de controles | **atestiguado**: `b0853f4` mete sus **bytes** en git a las 06:38, una hora antes de que `988a0fe` publique el número a las 07:38 |
| el **instrumento** —las 30 transcripciones— | 30 `sha256` en `runs/l4/congelacion.json` | **NO atestiguado**: `c4ac769` escribió un **puntero** a un fichero que aún no estaba en git; los 30 hashes entraron en `988a0fe`, **el mismo commit que publica el 25 de 30** |

Lo único que sostiene *«transcrito a ciegas antes de comparar»* es un campo
`congelado_en` dentro de un JSON escrito por la misma persona en el mismo commit.
Ver `LIMITS.md` 78, con sus tres comandos.

**La asimetría es lo que lo convierte en decisión y no en anécdota**: el mecanismo
correcto ya se conocía y se aplicó **a nueve metros de distancia**, en el mismo hito.
Lo que faltó no fue la idea; fue que no era un paso — igual que con `--durations` en
ADR-0022, y ésta es la segunda vez que este repo aprende lo mismo.

Y pesa más que cualquier otro número: el 1.000/1.000 de L3 lo puede recomprobar un
tercero contra el BOE. El *«antes de comparar»* **no lo puede comprobar nadie** si el
compromiso no está en git.

## Decisión

> **AL CONGELAR, LO QUE VA A GIT ES EL DIGEST, NO EL PUNTERO.**

Cinco pasos, en este orden:

1. Se calcula el `sha256` **del manifiesto de huellas**.
2. Esa línea se escribe en un fichero **que YA ESTÁ EN GIT** — el plan del hito.
3. **Ese commit se hace SOLO y SE EMPUJA SOLO**, antes de la primera comparación.
4. El manifiesto y los ficheros congelados **se revelan después**, en su commit.
5. Un **test de clon frío** recalcula el `sha256` del manifiesto y lo compara con el
   digest. Cualquiera lo comprueba, para siempre.

Es el esquema estándar de compromiso-y-revelación, y su valor entero está en el paso
3: **el sello de tiempo del push lo guarda GitHub, o sea un tercero, no el autor.**

## La contrapartida, escrita y no escondida

**Empujar antes de medir la puerta va contra la disciplina de este repo**, que no
empuja sin número. Se admite **sólo** porque ese commit **no lleva código**: una
línea de digest en un YAML no mueve la puerta, así que no hay número que medir. Si
alguna vez ese commit llevara algo más que la línea de digest, esta excepción **no
aplica** y hay que medir antes.

## Lo que NO se hace ahora, y por qué

**No se construye el script ni el test.** Este repo tiene una sección entera de
*«Construido y NO VALIDADO»* precisamente por adelantarse. El paso se escribe hoy
—es texto, es gratis— y el mecanismo se construye **en la primera congelación que lo
use**.

**Y no se retrofita L4.** Meter hoy un digest de `runs/l4/congelacion.json` en un
commit posterior **parece** un compromiso y no lo es: sería publicar como observado
lo que no se observó, que es la familia que este repo lleva declarada cinco veces.
**L4 se declara —límite 78— y no se retoca.**

**El tamaño, comprobado antes de prometerlo:** el compromiso es
`sha256sum <manifiesto>` —una línea, sin script— y el test son ~10 líneas: leer el
digest del plan, rehacer el `sha256` del manifiesto, comparar. Si al construirlo
resultara necesitar más, **eso es un hallazgo y se dice**, en vez de crecer en
silencio.

## Alternativas descartadas

**Firmar los commits con GPG.** Atestigua **quién**, no **cuándo**, y el problema
aquí es el orden. Además no lo comprueba un clon sin las claves.

**Un servicio de sellado de tiempo externo.** Resuelve lo mismo que el push y añade
una dependencia de red y una cuenta. El push ya deja el sello en un tercero.

**Dejarlo como está y confiar en el mensaje del commit.** Es lo que hizo L4. El
mensaje de `c4ac769` afirma la congelación con todas las letras y su contenido son
cinco líneas sin un solo hash: **un mensaje de commit es una afirmación del autor,
no una prueba.**

## Trade-off

Lo que se paga: **un commit y un push de más por congelación**, y una excepción
declarada a la regla de no empujar sin número.

Lo que se compra: que *«se congeló antes de comparar»* deje de ser una afirmación de
quien lo hizo y pase a ser **algo que cualquiera comprueba con un `sha256sum` y un
`git log`**, para siempre y sin pedirle nada al autor.
