# Mutantes · el control negativo de la suite

Cada fichero es un **plugin de pytest** que rompe una función a propósito. La
suite tiene que **caerse** contra cada uno: un mutante que no mata a nadie es un
hueco en los tests, no un mutante mal escrito.

Existen porque `RESULTS.md` publica sus recuentos, y la regla de oro 2 no
distingue entre tipos de número: **si no se puede reproducir, no existe**.

```bash
uv run python scripts/mutantes/matar.py          # todos, con su recuento
echo $?                                          # 0 si TODOS mueren
```

Las dos formas de estar roto, que son las que exige `/cerrar`:

- **`siempre_ok`** — la función devuelve el resultado bueno pase lo que pase.
  Caza al test que no comprueba nada.
- **`siempre_roto`** — la función rechaza o falla siempre. Caza al test que sólo
  afirma la mitad negativa, que es el que miente en la dirección tranquilizadora:
  da un 100% de detección que en realidad es un 100% de pesimismo.

**Los recuentos son un SUELO, no un valor fijo.** Las suites llevan tests de
`hypothesis`, que sortea: un mutante que sólo caza una propiedad muere unas veces
y otras no. El mínimo garantizado lo dan los tests deterministas, y es lo que
`matar.py` comprueba.
