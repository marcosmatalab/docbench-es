# Corpus L3 · BOE, 1.000 documentos emparejados PDF/XML

**Aquí está el manifiesto, no los bytes.** 520 KB de JSON entran en el repo; los
362 MB de PDF y XML no. Esta carpeta contiene la evidencia de la cosecha y las
instrucciones para rehidratarla; el corpus se vuelve a bajar del origen.

| Fichero | Qué es | Por qué está versionado |
|---|---|---|
| `plan.yaml` | la ventana, el objetivo, el filtro y el ritmo | **congelado ANTES de bajar el primer documento** (§16). Un plan escrito después de ver los resultados no es un plan |
| `manifiesto.json` | los 1.000 documentos con su procedencia y su `sha256` | §16 pide el corpus **con manifiesto**. Sin él en el repo, el `CUMPLE` del verificador sólo lo puede comprobar quien cosechó |
| `xml_sha256.json` | el `sha256` de cada XML, tomado al terminar la cosecha | el manifiesto pone hash al PDF y no al XML (límite 62). Su valor está en **cuándo** se tomó, y en git la fecha se comprueba |
| `desglose.json` | la tasa de descarte por trozo de la ventana | reconstruido releyendo los sumarios (límite 63), con la fecha de la lectura dentro |
| `docs/` | los 2.000 ficheros | **no está**: son datos, y pesan 362 MB |

## Rehidratar el corpus

```bash
# 1. Baja los 1.000 documentos. ~2.065 peticiones a 1 rps: unos 35 minutos.
uv run python scripts/cosechar_boe.py \
    --reanudar runs/l3/manifiesto.json \
    --salida   runs/l3/rehidratado.json

# 2. Comprueba que lo que has bajado es lo que ESTE manifiesto publica.
uv run python scripts/verificar_corpus.py runs/l3/manifiesto.json --plan runs/l3/plan.yaml
```

El paso 1 usa el manifiesto como caché (ADR-0031, condición 4) **y mira el disco**:
sólo pide lo que no tengas, así que una descarga interrumpida se retoma sin gastar
peticiones de más. **`--salida` es obligatorio aquí y no es un detalle**: sin él
escribiría encima del manifiesto publicado, o sea que la evidencia contra la que se
compara sería la que produjo la comparación. El script se niega, pero conviene
saber por qué.

El paso 2 rehace los 1.000 `sha256` **contra los bytes** y comprueba que el
`plan.yaml` que le pasas es el congelado, por su `plan_hash`. Si el BOE hubiera
cambiado un documento, sale ahí con su identificador.

## Qué pasa si clonas y NO rehidratas

`verificar_corpus.py` **no dice `CUMPLE`**. Sin `docs/` no puede rehacer los
hashes, así que dice `NO EJECUTADA` y devuelve **1**:

```
  NO EJECUTADA  la comprobación de disco: runs/l3/docs no existe
```

Es deliberado. Una comprobación que no se ejecuta no es una comprobación que pasa,
y devolver 0 ahí afirmaría sobre un corpus que nadie ha mirado. Para verificar
sólo la forma del manifiesto —sin los bytes— está la función `verificar()`, que es
lo que ejercen los tests.

## Los números, y dónde vive cada uno

La tasa de descarte es **4,12 %** sobre **1.043 intentados**, con umbral de
coherencia 0,85 y ventana 2026-03-09 → 2026-04-11 (ADR-0030: la tasa nunca viaja
sola). El desglose por estación y el resto de cifras, con su comando de
reproducción, en [`RESULTS.md`](../../RESULTS.md).

**La ventana no es la que da el mejor número, a propósito.** El sondeo midió la
tasa en tres épocas —agosto 2,0 %, otoño 4,5 %, primavera 5,5 %— y esta ventana
cae sobre el tramo con **más** descarte de los tres, para que a la tasa publicada
no se le pueda acusar de estar elegida. El razonamiento entero, en `plan.yaml`.

## La licencia del corpus NO es la del código

El código es Apache-2.0. El corpus está sujeto a las condiciones de reutilización
del BOE, que exigen atribución: **«Basado en datos de la Agencia Estatal Boletín
Oficial del Estado»**, literal, y la fecha de última actualización. Las dos
licencias van declaradas y separadas dentro del manifiesto (ADR-0033, requisito 3).
