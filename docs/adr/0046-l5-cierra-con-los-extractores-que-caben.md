# ADR-0046 · L5 cierra con los extractores que caben, y los demás entran con `/extractor`

> **ESTO NO ES UNA DECISIÓN DE HOY. Es la transcripción al manual de una regla escrita el
> 25 ago 2026 ANTES de medir el cómputo** —`runs/l5/computo.yaml`, commit
> [`008e68d`](https://github.com/marcosmatalab/docbench-es/commit/008e68d), *«La regla de
> si no cabe el cómputo, escrita ANTES de medirlo»*— **y aplicada y publicada el mismo día
> en [`b90c291`](https://github.com/marcosmatalab/docbench-es/commit/b90c291), «B5-bis
> CERRADO: cabe con cuatro»**. Lo que llega tarde es la transcripción, no la decisión.
>
> **Y la distinción no es cosmética.** Un ADR fechado el día del cierre que reduce el
> criterio de ese cierre se lee como mover la portería, por muy cierto que sea lo que
> diga. Éste registra una regla **anterior, pre-registrada y ya publicada**, y lo que
> corrige es la **regla de oro 8** aplicándose con tres días de retraso: el manual seguía
> diciendo «ocho» mientras el repo llevaba tres días operando con «los que quepan».

**Fecha de la decisión:** 2026-08-25 · **Fecha de la transcripción:** 2026-08-28 ·
**Estado:** aceptada. **Toca el manual**: §16, en este mismo commit.

## Contexto

`MANUAL.md` §16 fija L5 como *«`extract.base` + conformidad + **ocho** extractores locales
+ nivel 1»*, con el criterio *«primera tabla de estructura con coste y cobertura
evaluable»* y la coletilla *«ocho, no trece: los otros cinco entran después con
`/extractor`»*.

**La regla de decisión de L5 se congeló antes de medir nada**, en `runs/l5/computo.yaml`:

```yaml
las_dos_salidas:
  censo:
    que_es: 1.000 documentos x los extractores que quepan
    si_sobran_extractores: entran de uno en uno con /extractor, una tarde cada uno
    veredicto: hito cerrado
  muestra:
    que_es: ~300 documentos x los ocho
    veredicto: contradiccion con ADR-0042
```

**El veredicto «hito cerrado» estaba escrito antes de saber cuántos cabían.** Y la razón
por la que la otra salida no valía tampoco es de conveniencia: muestrear en L5 exige un
plan de muestreo, y el plan de muestreo **es L6**, que ADR-0042 acababa de mover **después**
de L5. Una muestra en L5 incumpliría *«el plan congelado y publicado antes de la primera
campaña seria»* **por el hito anterior al que lo establece**.

Medido en B5-bis: con los cuatro que caben, **4,01 h proyectadas** (2,30 h reales); con los
ocho, **del orden de 8 h**. Se aplicó la regla: **se recortan extractores, no documentos.**

## Decisión

**L5 cierra con los extractores que caben en su presupuesto, que son cuatro.** El criterio
de aceptación —*primera tabla de estructura con coste y cobertura evaluable*— no cambia y
está cumplido. Lo que cambia es el **número de extractores de la fila de §16**, que pasa de
un tramo de aplazamiento a **dos**.

### Lo que se pierde, que es la parte que hay que escribir

Un ADR que sólo cuenta lo que pasó es un parte; lo que lo hace utilizable es lo que declara
que **cuesta**. Con cuatro:

| Qué se pierde | Detalle |
|---|---|
| **Dos de las cinco familias**, enteras | Los cuatro cubren **tres**: parser de texto (2 de 2), extractor de tablas (1 de 1) y document-AI (1 de 3). **Fuera: TEI/científico y OCR** |
| **Los dos conversores sin estrenar siguen sin estrenar** | `from_tei` y `from_text_heuristic` esperan a `grobid` y `tesseract`. Son los dos únicos que quedan de los cinco de L1 (LIMITS 49) |
| **La predicción viva más fuerte del repo se queda otro hito sin ponerse a prueba** | *«El hito que ESCRIBE un módulo no encuentra los bugs que encuentra el que lo CONSUME»* lleva **tres de tres**, y las tres son de conversores. `from_tei` y `from_text_heuristic` son los dos casos que quedan para confirmarla o romperla, y **ninguno está en esta campaña** |

**Ese tercero es el que de verdad cuesta**, y por eso va con nombre y no diluido en «faltan
extractores»: una predicción con tres confirmaciones y ningún intento de refutación
pendiente **deja de aprenderse algo cada hito que pasa sin ejercitarla**.

### El orden de los cuatro que quedan, por lo que COMPRA cada uno

No por lo que cuesta, y no de golpe: *«correr los otros cuatro»* empaqueta lo que más vale
con lo que menos, que es justo lo que este repo desempaqueta en todas partes.

| Extractor | ¿familia nueva? | ¿conversor nuevo? | Cuándo |
|---|---|---|---|
| `grobid` | **SÍ** — TEI/científico | **SÍ** — `from_tei` | **primero** |
| `tesseract` | **SÍ** — OCR | **SÍ** — `from_text_heuristic` | **segundo**, y con su coste medido antes |
| `marker` | no, document-AI ya cubierta | ninguno | al final, o nunca |
| `unstructured` | no, document-AI ya cubierta | ninguno | al final, o nunca |

**Los dos baratos no compran ni familia ni conversor: sólo mueven el titular** (LIMITS
113), y un panel de seis sería lo peor de las dos opciones — mueve el número sin comprar
nada.

**Y `tesseract` se mide antes de comprometerlo.** El censo de
[`5dbe647`](https://github.com/marcosmatalab/docbench-es/commit/5dbe647) dio **0 de 10.298
páginas sin capa de texto**, y LIMITS 104 ya dejó escrito que el OCR de `pymupdf4llm` es
**coste y no alcance**. Correr `tesseract` sobre 8.733 páginas es comprar un número que el
censo ya predice, al mayor coste no medido de la mesa. **No es que no valga la pena**:
*«el OCR cuesta X y no aporta nada en este corpus»* es un resultado publicable y bueno. Es
que se mide sobre **50 páginas** antes de comprometer 8.733.

## Alternativa descartada

**Correr los ocho en L5.** Descartada **por la regla congelada y con el número delante**:
del orden de 8 h contra un presupuesto de ~4 h, y la salida alternativa —muestrear— se
contradice con ADR-0042. Descartarla hoy no sería una decisión: la regla ya la descartó el
25 de agosto, antes de medir.

**Cerrar L5 sin transcribir al manual.** Descartada por la regla de oro 8: un ADR sin
transcribir deja dos fuentes de verdad en desacuerdo y **gana la que el bucle lee primero**,
que es el manual. Ya han sido tres días.

## Trade-off

**Lo que se paga:** el criterio de L5 se cumple con la mitad de los extractores que su fila
prometía, y las dos familias que faltan son justo las que traen los dos conversores sin
estrenar. Se mitiga escribiéndolo arriba con nombre, y poniendo el orden por lo que compra
cada uno en vez de por lo que cuesta.

**Lo que se compra:** que el hito cierre con una tabla real, medida y reproducible en vez
de con una campaña de 8 h que la regla congelada ya había descartado — y que el manual
vuelva a decir lo que el repo hace.
