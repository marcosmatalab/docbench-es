"""Ningún instrumento lee dos veces el mismo fichero en una sola llamada.

## Por qué esto es un test y no una nota

**Tercera vez seguida con la misma forma de defecto**, y las tres encontradas con
`--durations` **después** de que el techo se pusiera rojo:

| Hito | Dónde | Veces |
|---|---|---:|
| L4 | `corregir_fixtures_l4.py`, `pdftotext` sobre los mismos bytes | **8** |
| L5 | `huerfanos.reparto()`, el AST de `tests/` una vez por documento | **9** |
| L7 | `censo_paginas.paginas()`, 520 KB de JSON por llamada a `reloj()` | **5** |

Una función pura que lee o parsea algo caro, llamada una vez por elemento de un bucle,
sin cachear. **Y estaba anotado dos veces y exigido cero**: `scripts/huerfanos.py` lleva
escrito *«cacheada, y por la misma razón que el `lru_cache` de `pdftotext` en L4»*. Es la
frase de ADR-0022 sobre sí misma — *se hizo una vez, funcionó, y no se convirtió en paso*.

**Un diagnóstico post mortem tres de tres es el daño hecho tres veces.** Si esto hubiera
existido en L4, los tres se habrían cazado **antes** del rojo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

import censo_paginas  # noqa: E402
import lecturas  # noqa: E402


@pytest.mark.parametrize("nombre", sorted(lecturas.INSTRUMENTOS))
def test_un_instrumento_no_lee_dos_veces_lo_mismo(nombre: str) -> None:
    """El aro, instrumento a instrumento. **El alcance es UNA llamada, no la suite**: dos
    tests que leen el mismo fixture no comparten nada; una llamada que parsea el mismo
    fichero cinco veces es siempre el defecto."""
    with lecturas.contando() as cuenta:
        lecturas.INSTRUMENTOS[nombre]()

    repes = lecturas.repetidas(cuenta)

    assert not repes, (
        f"`{nombre}` lee lo mismo más de una vez: "
        + "; ".join(f"{n}x {que} {arg}" for (que, arg), n in repes)
        + ". Es el defecto de L4, L5 y L7. Cachea el lector, no el llamante"
    )


def test_el_aro_caza_una_lectura_repetida(tmp_path: Path) -> None:
    """**Control negativo con un lector inventado.** Un contador que no contara nada
    pasaría el test de arriba con las manos en los bolsillos."""
    fichero = tmp_path / "caro.json"
    fichero.write_text("{}", encoding="utf-8")

    with lecturas.contando() as cuenta:
        for _ in range(3):
            fichero.read_text(encoding="utf-8")

    assert lecturas.repetidas(cuenta) == [(("read_text", str(fichero)), 3)]


def test_el_aro_habria_cazado_el_defecto_real_de_l7() -> None:
    """**Y el control negativo que de verdad importa: el defecto REAL, revivido.**

    Un contador que caza un bucle de juguete no demuestra que hubiera cazado el fallo que
    costó 418 ms de puerta. Aquí se le quita la caché a `censo_paginas.paginas()` —que es
    exactamente como estaba antes— y se comprueba que el aro ve las cinco lecturas del
    manifiesto dentro de una sola llamada a `reloj()`.

    Sin esto, «el aro habría cazado los tres» sería una afirmación sobre el pasado que
    nadie ha comprobado, que es la clase de frase que este repo persigue.
    """
    sin_cache = censo_paginas._del_manifiesto.__wrapped__
    original = censo_paginas._del_manifiesto
    censo_paginas._del_manifiesto = sin_cache  # type: ignore[assignment]
    try:
        with lecturas.contando() as cuenta:
            lecturas.INSTRUMENTOS["error_del_estimador.reloj"]()
    finally:
        censo_paginas._del_manifiesto = original
        censo_paginas._del_manifiesto.cache_clear()

    repes = dict(lecturas.repetidas(cuenta))
    manifiesto = ("read_text", str(RAIZ / "runs" / "l3" / "manifiesto.json"))

    assert manifiesto in repes, "el aro NO ve el defecto de L7: no sirve para lo que existe"
    assert repes[manifiesto] > 1
