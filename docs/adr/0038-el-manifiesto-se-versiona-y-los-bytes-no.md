# ADR-0038 · El manifiesto se versiona, los bytes no, y el criterio se comprueba rehidratando

**Fecha:** 2026-08-24 · **Estado:** aceptada. **No toca el manual**: §10.4 define
qué lleva el manifiesto; esto decide **dónde vive** y cómo se comprueba desde fuera

## Contexto

L3 produce dos cosas: **362 MB de PDF y XML** y un manifiesto de **520 KB**. Hasta
el cierre, `runs/` estaba entero en `.gitignore` salvo `plan.yaml`, así que el
manifiesto no salía del disco de quien cosechó.

El problema no es de elegancia. §16 pide *«1.000 documentos emparejados PDF/XML,
**con manifiesto** y tasa de descarte»*, y `scripts/verificar_corpus.py` es el
comando que dice si eso se cumple. **Con el manifiesto fuera del repo, su
`CUMPLE · rc=0` es una afirmación que sólo puede comprobar quien la produjo** — que
es exactamente lo que la regla de oro 2 existe para impedir.

Y hay una segunda razón, que es de ADR-0033: ese ADR decide que el manifiesto
**nace publicable**. Un manifiesto publicable que no se publica es una
contradicción declarada.

## Decisión

**Dentro del repo: la decisión y la evidencia. Fuera: los bytes.**

| Fichero | Qué es | Tamaño |
|---|---|---|
| `runs/*/plan.yaml` | la **decisión**, congelada antes de medir | 3 KB |
| `runs/*/manifiesto.json` | la **evidencia**: 1.000 documentos con su hash y su procedencia | 520 KB |
| `runs/*/xml_sha256.json` | el hash de cada XML, con la fecha en que se tomó | 127 KB |
| `runs/*/desglose.json` | la tasa por trozo de ventana, con la fecha de la relectura | 2 KB |
| `runs/*/README.md` | cómo se rehidrata | 4 KB |
| `runs/*/docs/` | **los bytes** | **362 MB** — fuera |

**Y el criterio se comprueba rehidratando, no confiando.** Quien clona ejecuta
`cosechar_boe.py --reanudar` —que baja del origen sólo lo que no tenga en disco— y
después `verificar_corpus.py`, que **rehace los 1.000 `sha256` contra los bytes**.
Si el origen hubiera cambiado un documento, sale ahí con su identificador.

**Sin los bytes, el verificador NO dice que cumple**: dice `NO EJECUTADA` y
devuelve 1. Comprobado sobre un clon limpio, que es el escenario del lector
externo. Una comprobación que no se ejecuta no es una comprobación que pasa.

**Y rehidratar no reescribe el manifiesto publicado.** `cosechar_boe.py` se niega
si `--reanudar` y la salida son el mismo fichero: sobrescribirlo cambiaría el
`ritmo` y los `dias_sin_boletin` por los de otra corrida, o sea que la evidencia
contra la que se compara sería la que produjo la comparación.

## Alternativas descartadas

**Versionar también los bytes**, con LFS o similar. 362 MB por campaña, y L5 hará
varias. Rompe `git clone` para todo el que no quiera el corpus, y **no compra
nada** que no compre el hash: el manifiesto ya permite comprobar que lo bajado es
lo mismo. Lo que se publica del corpus se decidirá con ADR-0033 delante, y no es
una decisión de L3.

**Dejarlo todo fuera y publicar sólo los números en `RESULTS.md`.** Es lo que había,
y es lo que convierte el criterio de aceptación en una afirmación de palabra. Con
los números pero sin el manifiesto, un lector no puede ni empezar a comprobar.

**Un tercer repo de datos.** Más infraestructura para el mismo problema, y añade
un sitio donde el manifiesto y el código pueden desincronizarse. Con 520 KB no hace
falta.

## Trade-off

Lo que se paga: **el repo crece ~650 KB por campaña**, y cada cosecha deja un
fichero que hay que commitear. Con varias campañas en L5 hay que vigilarlo — si
llegara a molestar, la salida es publicar el manifiesto como release y no en el
árbol, y eso es una decisión que se toma con el número delante.

Lo que se compra: que **cualquiera pueda comprobar el criterio de aceptación de L3
sin pedirme nada**, y que el corpus se pueda publicar el día que se decida sin
volver al origen.
