# ADR-0030 · La tasa de descarte se publica con su VENTANA y su dispersión, nunca como cifra única

**Fecha:** 2026-08-24, **escrito con retraso**: la decisión llevaba desde el 22 de
agosto citada por su número en tres documentos y **el fichero no existía**.
Estado: aceptada. No toca el manual: §12 no dice cómo se publica esta tasa

## Por qué este ADR se escribe hoy y no el día que se decidió

**Se detectó al preparar `corpus.harvest`.** Tres documentos citaban `ADR-0030`
para justificar cómo se publica un número, y `docs/adr/0030-*.md` no existía en
ningún commit de ninguna rama — comprobado con `git log --all`. Los números 0027,
0028 y 0029 tampoco, y de ésos sólo 0029 tenía una cita.

**Esto no es deuda, es una afirmación falsa**: tres documentos afirmaban que había
una decisión numerada que se podía ir a leer. Así que se arregla en el momento en
que se detecta, y así se escribe.

**Lo que este fichero NO hace es inventar la decisión.** Su contenido es
exactamente el que las tres citas ya fijaban, y los números son los del sondeo, que
sí está medido y publicado:

| Dónde | Qué decía, literal |
|---|---|
| `docs/sondeo-boe-2026-08-22.md`:173 | «se publica con su ventana y su dispersión, **nunca como cifra única** (ADR-0030)» |
| `docs/adr/0033`:44 | «la tasa de descarte se publica con su ventana y su dispersión, nunca como cifra única (ADR-0030): está medido que entre ventanas va de 2,0% a 5,5%, un factor 2,75» |
| `src/docbench_es/corpus/pairing.py`:49 | «depende de cuándo coseches: entre ventanas hay un factor 2,75 (ADR-0030)» |

## Contexto

La tasa de descarte del emparejado PDF/XML es un **resultado publicado** (§12,
`n_discarded_pairing`), no un detalle de limpieza: dice qué fracción del corpus se
tiró por incoherencia entre las dos representaciones del mismo documento.

**Y está medido que depende de cuándo se coseche.** Sobre las tres ventanas del
sondeo, con el umbral 0,85 que fija el perfil:

| Ventana | Tasa de descarte |
|---|---|
| agosto 2026 | 2,0% |
| otoño 2025 | 4,5% |
| primavera 2026 | 5,5% |
| **agregado, n=600** | **4,00%**, IC [2,7 a 5,9] |

Entre el mínimo y el máximo hay un **factor 2,75**. Y ya se cobró una pieza: esa
tabla se publicó una vez con **una sola columna sin decir de qué ventana salía**, y
era la más favorable — el 2,0% de agosto presentado como la tasa general.

## Decisión

**Toda tasa de descarte que este proyecto publique va con su ventana y su
dispersión. Nunca como cifra única.** En concreto:

1. **La ventana**, con sus fechas exactas. Una tasa sin ventana es una propiedad
   del calendario disfrazada de propiedad del corpus.
2. **La dispersión entre ventanas** cuando haya más de una, o el intervalo cuando
   sea una estimación sobre muestra (regla de oro 2).
3. **El umbral que la produjo**, porque moverlo la cambia por un factor grande y el
   umbral vive en el perfil de la entidad.
4. **Y el denominador**: sobre cuántos pares intentados. Una tasa sin denominador
   no se puede comparar con la de otra corrida.
5. **La tasa es del CORPUS, no del proceso.** Añadido el 24 ago 2026 al escribir
   `corpus.harvest`, que es donde la pregunta se vuelve concreta: en una
   **reanudación** cuenta el **estado final** de cada documento. Uno que agotó sus
   reintentos ayer y baja bien hoy es un **aceptado**, no un descarte.

   Sin esta regla, la tasa publicada dependería de **cuántas veces alguien le dio a
   reintentar**, que es una propiedad del operador y no del corpus. Y los fallos
   transitorios no se pierden —regla de oro 6—: van aparte, en
   `Cosecha.reintentos_agotados`, que es otro número y responde a otra pregunta.

## Alternativa descartada

**Publicar el agregado y ya**, que es lo que hace todo el mundo. Descartada porque
el agregado de tres ventanas concretas **no es la tasa del BOE**: es la tasa de
esos tres trozos de calendario, y con un factor 2,75 entre ellos la diferencia no
es un matiz. Quien coseche en otra ventana obtendrá otra cosa y creerá que algo se
ha roto.

**Publicar sólo el rango, sin agregado.** Descartada por lo contrario: el rango sin
un valor central no se puede usar para proyectar cuántos documentos hacen falta
para llegar a mil.

## Trade-off

Lo que se paga: cada tasa ocupa una tabla en vez de una cifra, y hay que arrastrar
la ventana por todo el pipeline hasta el informe — `corpus.manifest` lleva las
fechas dentro por eso, no por completismo.

Lo que se compra: que la cifra siga significando lo mismo cuando alguien la lea en
otra estación del año.

## Cómo se verifica

`corpus.pairing` **no publica**: cuenta. `Recuento` trae `n_pares`, `n_aceptados` y
el desglose por causa, y su docstring dice que **la ventana la pone quien publica**
porque este módulo no la conoce. Lo que sí está en la puerta es el invariante que
hace que la tasa signifique algo: `aceptados + descartes == n_pares`, con su test —
sin él, un descarte puede desaparecer del denominador.

`corpus.harvest` arrastra la ventana —`desde` y `hasta`— hasta el manifiesto, y el
manifiesto la guarda. Ahí es donde este ADR deja de ser una intención.

## Consecuencias

- Ninguna tasa de descarte se publica sin ventana, dispersión, umbral y denominador.
- El manifiesto guarda las fechas de la ventana **por requisito**, no por adorno.
- Y el barrido de referencias pasa a comprobar que **toda cita `ADR-NNNN` tiene su
  fichero**: este ADR existe porque tres documentos citaron un número que no
  estaba, y eso no puede volver a pasar por no mirarlo.
