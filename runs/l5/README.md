# runs/l5 · la campaña de estructura

## Cómo reanudar cuando el guardián del árbol la rechaza

**Escrito el 27 ago 2026 con la corrida al 59% y ANTES de necesitarlo**, que es cuando se
piensa bien. La corrida arrancó sobre `819c06f` con el árbol limpio; cuarenta minutos más
tarde se commiteó `eacb1c2` y el árbol se llenó de trabajo sin commitear. Desde ese
momento **la corrida ya no era reanudable**, y eso no se descubre hasta que se cae.

`sellar()` compara `commit`, `sucios` y `huella` contra el sello y levanta
`ContractViolation` si cualquiera se movió. No se estrecha para que mire sólo la ruta de
extracción: un guardián que se fía de su propio criterio sobre qué importa acaba
protegiendo cero ficheros. Lo que sí hace desde hoy es **decir qué se movió**.

```bash
git stash push -u          # el trabajo sin commitear, a salvo
git checkout 819c06f       # el árbol exacto del sello, en HEAD separado
uv run docbench run --extractors all --salida runs/l5/campana --offline
git checkout - && git stash pop
```

### Por qué esto funciona, comprobado y no supuesto

**El diario sobrevive.** `runs/l5/campana/` lo ignora git —`.gitignore:23`, `runs/*/*`—,
así que `stash push -u` no lo guarda (`-u` son los sin seguir, **no** los ignorados) y
`checkout` no lo toca. Comprobado con `git check-ignore -v`.

**El punto de control es el resultado.** El corredor reanuda saltándose los identificadores
que ya tienen línea en el diario de su extractor. No hay un `estado.json` que pueda
desincronizarse, porque no hay un `estado.json`.

**Y los tres campos del guardián vuelven a cuadrar**, que es lo único que decide:

| campo | en el sello | tras el `checkout` | por qué |
|---|---|---|---|
| `commit` | `819c06f` | `819c06f` | `git rev-parse --short` sobre HEAD separado da lo mismo |
| `sucios` | `0` | `0` | el `stash` deja el árbol limpio; los ignorados no cuentan |
| `huella` | `01ba4719c80b6fe9` | `01ba4719c80b6fe9` | es `sha256("\n")[:16]`: `status` y `diff HEAD` vacíos |

La última fila se comprobó calculando el `sha256` a mano, no ejecutando el guardián — que
es lo que se quiere, porque ejecutarlo exigía tener el problema.

## Lo que hay aquí

`emparejado.yaml`, `ponderacion.yaml`, `computo.yaml` y `estimacion.yaml` son
**pre-registros**: están commiteados antes de medir, y por eso el número que sale de ellos
significa algo. `campana/` son los diarios y no se versionan.
