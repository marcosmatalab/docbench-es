# ADR-0025 · «Tras alinear» se lee como «sin alinear», y se declara el precio

**Fecha:** 2026-08-23 · **Estado:** aceptada, implementada y con su límite (53).
**Toca el manual:** §12 dice *«Emparejado por posición tras alinear»* y aquí se
precisa qué significa ese *«tras alinear»*, igual que ADR-0020 precisó *«sus
números»*. Transcrito a §12 en este mismo commit (regla de oro 8)

## Contexto

§12 fija el supuesto de la exactitud de celda en cinco palabras: *«Emparejado por
posición **tras alinear**»*. `core.cellmatch` empareja por `(fila, columna,
rowspan, colspan, texto)` y **no alinea nada**. El docstring del módulo cita la
frase del manual y decide en el acto que no hay alineamiento.

**El problema no es la decisión, es dónde estaba.** Una decisión que cambia el
número publicado —una tabla desplazada **una fila entera** saca `cell_accuracy`
**0,0** teniendo todas sus celdas bien transcritas— vivía en un docstring, sin
ADR y sin límite. `grep -rn "alinea" LIMITS.md RESULTS.md docs/` no devolvía
nada. Lo encontró el escrutinio adversarial del cierre de L2.

Es exactamente el patrón que la regla de oro 7 persigue para las
normalizaciones, aplicado a un supuesto de métrica: **lo que no se declara se
convierte en una ventaja o un castigo silencioso para algún extractor**. Aquí
castiga, y castiga fuerte, a un extractor que se coma una fila de encabezado.

## Decisión

**No se alinea, y «tras alinear» se lee como «tras la colocación canónica».**

El alineamiento que §12 pide **ya ocurrió**: es L1. Los cinco conversores colocan
cada celda en su `(fila, columna)` de la rejilla resolviendo `rowspan`/`colspan`
con el algoritmo del estándar HTML. Cuando `core.cellmatch` recibe dos
`CanonicalTable`, las dos están **ya alineadas a la misma rejilla**; buscar
además el mejor desplazamiento entre ellas sería un segundo alineamiento, y uno
que **el manual no pide en ningún sitio**.

Y hay una razón de fondo, no sólo de lectura: **en una tabla de importes, la
posición ES el dato.** Una columna desplazada cambia a qué concepto pertenece
cada número. Un emparejado que buscara el mejor desplazamiento le daría 1,0 a un
extractor que ha destruido la correspondencia concepto→importe, que es
precisamente el fallo que este banco existe para medir.

**El precio se declara**: `LIMITS.md` 53. `cell_accuracy` es **exactitud
posicional**, y no es comparable con cifras de la literatura que sí alinean.

## Alternativa descartada

**Alinear buscando el desplazamiento que maximiza los aciertos.** Es lo que haría
un lector caritativo de *«tras alinear»*, y captura un fallo real —comerse una
fila de encabezado no es lo mismo que transcribir mal cada celda—. Se descarta
por tres cosas, en orden:

1. **Premia destruir la correspondencia posicional**, que en tablas de importes
   es el contenido mismo.
2. **El fallo que pretende perdonar ya se mide en otro sitio**: una fila de menos
   cambia la forma del árbol y TEDS la penaliza. Perdonarla aquí y castigarla
   allí es informativo; perdonarla en los dos sitios sería no medirla.
3. Introduce un parámetro —cuánto desplazamiento se permite— que habría que
   justificar con un número que **nadie ha medido**, y un parámetro sin medir es
   una perilla para mover la nota.

**Emparejado por contenido, ignorando la posición** (multiconjunto de textos).
Descartada: mide transcripción de texto, no lectura de tabla, y para eso ya
existe el verificador `numeric` de L9.

## Trade-off

Lo que se paga: **un extractor que se come una fila de encabezado saca 0,0 en
exactitud de celda con todo el texto bien**, y ese 0,0 es duro de leer sin la
nota al pie. Se mitiga publicando siempre TEDS al lado, que sí distingue «se comió
una fila» de «transcribió mal todas las celdas», y con el límite 53.

Lo que se compra: que la exactitud de celda signifique **una** cosa y se pueda
comprobar leyendo dos tablas, sin un parámetro de tolerancia que nadie ha medido.
