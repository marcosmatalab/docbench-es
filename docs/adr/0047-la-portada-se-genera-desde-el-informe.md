# ADR-0047 · La portada del proyecto se GENERA desde `informe.json`, y son dos salidas

**Fecha:** 2026-08-28 · **Estado:** aceptada. **Toca el manual**: §8 y §11, en este mismo
commit.

## Contexto

Este repo tiene un problema que **no es de rigor**: `LIMITS.md` son 2.433 líneas,
`RESULTS.md` 2.100 y `MANUAL.md` 2.000. Quien ya sabe qué está mirando se convence rápido;
quien no, rebota. **Los 114 límites no existen para quien no llega a ellos**, y eso es
distribución, no método.

Hace falta una puerta de entrada de diez minutos. La pregunta que decide este ADR **no es
si hacerla, sino si escribirla o generarla.**

**Escrita a mano sería la copia número catorce del titular y la primera en quedarse
vieja.** No es una hipótesis: el `README.md` de este mismo repo estuvo **33 commits**
publicando *«Hito L0 de 10 de la v0.1.0. Todavía no hay número»* con cuatro hitos más
cerrados, y el propio README contiene la frase *«en un repo que vende rigor, escribir en
presente lo que no existe es el peor fallo posible, más grave que un bug»*. La cura ya
existe y ya está aplicada dos veces: `scripts/estado_readme.py`, **un generador con dos
salidas** —el titular del README y el bloque de estado de `docs/reading-order.md`—, con su
barrera en la puerta.

Y hay una segunda razón, más fuerte: `scripts/derivadas.py` existe para hacer cumplir que
**un número derivado no se teclea**. Una portada con los números tecleados sería
exactamente lo que ese guardián persigue, **en el sitio más visible del proyecto**.

## Decisión

**La portada se genera, con un comando, desde `runs/l5/informe.json`, y emite dos
salidas.**

```bash
uv run docbench portada --informe runs/l5/informe.json --salida docs/index.html
```

* **`docs/index.html`** — la página entera, servida por GitHub Pages;
* **el bloque `PORTADA` del `README.md`** — la versión corta, con tope de líneas
  comprobado por `tests/unit/test_documentos_que_sostienen.py` como los otros tres.

**El modo por defecto COMPRUEBA y no escribe.** Lo que corre en la puerta es la
comprobación; escribir exige `--escribir`. Un comando cuyo modo por defecto sobrescribe
artefactos versionados invita a meterlo en un hook y convertir un rojo en un `git diff`
silencioso.

### Las cuatro reglas que la hacen defendible

| Regla | Cómo se hace cumplir |
|---|---|
| **Ni una cifra tecleada en la plantilla** | Todas salen de `_cifras.cifras()`, que las construye desde el JSON y el censo, y cada una lleva **de dónde sale** pegada |
| **El panel sale de `acuerdo.panel`, y va DENTRO de la etiqueta del titular** | LIMITS 113. Lo comprueban `tests/unit/test_portada.py` y la regla R9, **sobre el sitio y no sobre el valor** |
| **La página se marca a sí misma** | Cada número va en un elemento con `data-cifra="<clave>"`, así que el guardián compara **el titular con el titular** y no «¿aparece 103 en el HTML?» |
| **La puerta compara** | R9 de `scripts/derivadas.py`, con su control negativo, y el mutante `portada_sin_panel` |

### Las TRES direcciones de R9, y la tercera es nueva en este repo

1. **la que no cuadra** — una clave publicada con otro valor;
2. **la que falta** — una clave que el instrumento emite y la página no lleva;
3. **la que sobra** — una clave **en la página** que el instrumento no emite.

La tercera no la tenía ninguna otra regla de `derivadas.py`, y es la que cierra el agujero
real: **un número escrito a mano en la plantilla pasa cualquier comprobación de «lo
publicado coincide con lo medido»**, porque no hay nada con qué compararlo.

## Alternativa descartada

**Meter el censo del repo —límites, ADR, mutantes, el techo— dentro de `informe.json`, para
que la portada tuviera una sola fuente.** Es lo que pide la simetría, y **está descartada
por un modo de fallo concreto**: `informe.json` lo escribe `docbench report`, que necesita
los **143 MB de diarios de la campaña** que el repo no versiona (LIMITS 109). Un `114`
congelado ahí dentro se quedaría viejo el día que entre el límite 115, y arreglarlo
exigiría **rehacer una campaña de 2,30 h con el corpus delante**: la puerta se pondría roja
**sin arreglo disponible**, que es la peor clase de guardián que se puede construir.

Así que las fuentes son dos y **las separa la cadencia, no la comodidad**: `informe.json`
para lo que cambia con la campaña, el censo del repo —contado en cada generación— para lo
que cambia en cualquier commit. Es la misma decisión, y por la misma razón, que
`tests/unit/conftest.py` tomó con los recuentos: *«un JSON que escribe `matar.py` sólo está
al día si alguien se acuerda de correr `matar.py`»*.

**`docbench report --format html`, que el manual ya preveía.** Descartada porque no es lo
mismo: ese formato es la **tabla de la campaña** en HTML, para quien viene a leer
resultados. La portada es la **primera pantalla** —lleva la errata, el método y los
límites, que no son de la campaña— y tiene una segunda salida en el README. Empaquetarlas
en la misma bandera obligaría a que `report` leyera `LIMITS.md`.

**Escribir la portada a mano y comprobarla con una regla.** Descartada: una regla que
compara prosa escrita contra el JSON tendría que enumerar patrones —es lo que hace R8 con
las seis copias del error del estimador, y su hueco declarado es que **una copia escrita de
otra forma es invisible**—. Generando, el hueco no existe.

## Trade-off

**Lo que se paga.** Un artefacto versionado más que puede quedarse rancio —`docs/index.html`
son 270 líneas de HTML generado en el árbol—, y una barrera más en la puerta que cuesta un
subproceso. Y la portada **hereda el sesgo de las cifras que elige**: enseña cuatro límites
de 114 y cuatro puertas, y **esa selección no la comprueba nadie**. Va declarado en la
propia página —«los que más cambian cómo se leen los números de arriba»— y es lo que queda
sin cubrir.

**Lo que se compra.** Que la cifra más citable del proyecto no pueda divergir en su copia
más visible; que la errata del hito vaya **antes** que la lista de método, que es lo que
distingue esta página de un folleto; y que quien no va a leer 2.400 líneas se lleve el
titular **con su panel**, que es la única forma en que ese número no engaña.
