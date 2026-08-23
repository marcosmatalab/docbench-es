# ADR-0023 · Un TEDS negativo se calcula tal cual y se recorta SÓLO al publicar

**Fecha:** 2026-08-23 · **Estado:** aceptada, implementada y con test que la fija

## Contexto

TEDS **no está acotado por cero**. La fórmula publicada es

    TEDS = 1 - distancia(pred, gold) / max(nodos(pred), nodos(gold))

y la asimetría que lo permite es que **la distancia se calcula sobre los árboles
con su raíz** mientras que **el denominador cuenta sólo los descendientes**. Entre
dos tablas suficientemente distintas, la distancia se pasa del denominador.

Lo encontró `hypothesis`, no la revisión: un test de L2 afirmaba `0 <= teds <= 1`
y falló en una corrida de la puerta. El caso, congelado en
`tests/fixtures/pubtabnet/casos_limite.json` bajo la clave `teds_negativo`:

| | |
|---|---|
| **pred** | `<table><thead><tr><td></td><td></td><td></td><td></td></tr></thead></table>` — una fila de cabecera con cuatro celdas |
| **gold** | `<table><thead><tr><td rowspan="2"></td></tr></thead><tbody><tr></tr><tr><td></td></tr></tbody></table>` — una columna con un `rowspan` y dos filas más |
| nodos | 6 contra 7 |
| distancia | **8** |
| **TEDS** | 1 − 8/7 = **−0,142857** |
| La referencia de PubTabNet | **−0,142857**. Idéntico: no es un bug de este proyecto |

La cota real es **[−1, 1]**: en el peor caso la distancia es `n_a + n_b`, o sea
`1 − (n_a+n_b)/max(n_a,n_b) ≥ −1`.

**Por qué hay que decidirlo ahora y no en L5.** §12 publica TEDS como nota y la
pondera por estrato. En L5 esto puede acabar en una tabla delante de un
examinador, y una columna que mezcle valores negativos con positivos en una
métrica que el lector cree en [0,1] es una tabla que hay que explicar de pie.

## Qué significa un TEDS negativo, en una frase

> Convertir la tabla predicha en la real cuesta **más ediciones que nodos tiene la
> mayor de las dos**, o sea que **la predicción es peor que no haber predicho
> nada**: una predicción vacía puntúa exactamente 0.

Esa última cláusula es lo que hace la frase comprobable, y hay un test que la
comprueba: `teds(vacía, gold) == 0.0` y el caso negativo queda por debajo.

## Decisión

**El valor calculado no se toca en ningún caso.** `core.teds.teds()` devuelve el
número de la referencia, negativo incluido. Recortar ahí rompería el criterio de
aceptación de L2 —dejaría de reproducir la referencia— y convertiría una decisión
de presentación en una diferencia de algoritmo.

**El recorte es de PRESENTACIÓN, vive en `core.teds.para_publicar()` y se declara
junto al número.** Un solo sitio, un nombre y un test, en vez de aparecer disperso
por el informe de L5.

**Requisito para L5**, en `LIMITS.md` 46, con la misma forma que el límite 35:

1. El mismo criterio se aplica a los valores **por documento** y al **agregado**.
   Publicar una media sobre valores crudos junto a una columna recortada sería
   mezclar dos escalas en la misma tabla.
2. **Se dice cuántos se recortaron.** Un «3 de 200 documentos tenían TEDS crudo
   por debajo de 0, recortados a 0 en esta tabla» es información; esconderlo es
   presentar 200 valores como si todos estuvieran en escala.
3. Los valores crudos siguen en el artefacto de la campaña.

## Alternativa descartada

**Publicar el negativo con una nota al pie.** Es más fiel y se descarta por lo que
hace aguas abajo: §12 pondera por estrato, y un valor negativo en una media
ponderada **compensa** valores positivos de otro estrato, con lo que la cifra
global deja de significar «cuánto se parece» y pasa a significar algo sin nombre.
Recortar a 0 es conservador y no pierde casi nada: **0 ya significa
«completamente distinta»**, y el negativo sólo añade «además, peor que vacía»,
que es una distinción sin consecuencia práctica para el lector de una tabla de
resultados y que sigue disponible en el artefacto.

**Recortar dentro de `teds()`.** Descartada: apartarse de la referencia en
silencio es lo contrario de lo que L2 acaba de demostrar, y el propio test del
criterio de aceptación dejaría de medir el algoritmo.

**Recortar en `teds_batch`, dentro del agregado.** Descartada porque dejaría
`per_document` en crudo y `aggregate` recortado: **dos escalas en el mismo
objeto**, que es peor que cualquiera de las dos por separado.

## Trade-off

Lo que se paga: **L5 tiene que acordarse.** `core.teds` no puede obligar, porque
la decisión es del informe. Se mitiga con el test que fija las dos mitades —el
cálculo no recorta, `para_publicar` sí— y con el límite 46, que lo deja como
requisito y no como recordatorio.

Lo que se compra: que el número publicado esté en la escala que el lector supone,
sin que el cálculo mienta ni una vez.
