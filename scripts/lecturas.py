"""CUENTA LECTURAS REPETIDAS. El aro contra el defecto que va por la tercera.

    uv run python scripts/lecturas.py     # los instrumentos declarados, con su cuenta

## El patrón, con sus tres apariciones y sus fechas

| Hito | Dónde | Veces |
|---|---|---:|
| L4 | `corregir_fixtures_l4.py`, `pdftotext` sobre los mismos bytes | **8** |
| L5 | `huerfanos.reparto()`, el AST de `tests/` por documento del barrido | **9** |
| L7 | `censo_paginas.paginas()`, 520 KB de JSON por llamada a `reloj()` | **5** |

Siempre la misma forma: **una función pura que lee o parsea algo caro, llamada una vez
por elemento de un bucle, sin cachear.** Y las tres se encontraron con `--durations`
**después** de que el techo se pusiera rojo: un diagnóstico post mortem tres de tres es
el daño hecho tres veces.

**Y estaba anotado dos veces y exigido cero.** `scripts/huerfanos.py` lleva escrito
*«cacheada, y por la misma razón que el `lru_cache` de `pdftotext` en L4»*. Es la frase
de ADR-0022 sobre sí misma: *se hizo una vez, funcionó, y no se convirtió en paso*.

## Qué es esto

Un contador. Envuelve `Path.read_text`, `Path.read_bytes` y `subprocess.run` durante **una
llamada a un instrumento** y anota `(qué, argumento)`. Si el mismo argumento se lee dos
veces en la misma llamada, es este defecto y sale por su nombre.

**El alcance es UNA LLAMADA, no la suite**, y es la única definición que significa algo:
dos tests que leen el mismo fixture no comparten nada y no son un defecto; una sola
llamada que parsea el mismo fichero cinco veces sí lo es, siempre.

## Lo que NO cubre, y va dicho

* **Lo que no se declare en `INSTRUMENTOS`.** El aro no descubre instrumentos: los mira.
* **Los que necesitan datos fuera de git** —el caso de L4 es uno— no se pueden correr en
  la puerta, así que su forma queda cubierta por el contador y su **caso** no.
* **Una lectura repetida barata** también sale. Es a propósito: el umbral es «dos veces»,
  no «dos veces y caro», porque «caro» depende de la máquina y «dos veces» no.
"""

from __future__ import annotations

import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    pass

RAIZ = Path(__file__).resolve().parents[1]

Cuenta = Counter[tuple[str, str]]


class Llamable(Protocol):
    """Lo que el contador necesita de los tres originales: **poder llamarlos y devolver**.

    Con `Callable[..., object]` mypy lo cuenta como un `Any` explícito, que este repo
    prohíbe; y con la firma real de `subprocess.run` —una docena de sobrecargas— llamarlo
    con `*a, **k` no resuelve ninguna. Un `Protocol` de una línea dice exactamente lo que
    se usa y nada más.
    """

    def __call__(self, *a: object, **k: object) -> object: ...


@contextmanager
def contando() -> Iterator[Cuenta]:
    """Cuenta las lecturas de fichero y las llamadas a `subprocess` de este bloque.

    Se restauran los tres originales en un `finally`: dejar parcheado `Path.read_text`
    tras un fallo envenenaría el resto de la corrida, y un aro que rompe lo que vigila
    es peor que no tenerlo.

    Los tres originales se guardan como `Callable[..., object]` **a propósito**:
    `subprocess.run` tiene una docena de sobrecargas y llamarlo con `*a, **k` no resuelve
    ninguna. Aquí no hace falta el tipo de vuelta —el contador no mira el resultado, sólo
    lo deja pasar— y `Any` está prohibido en este repo.
    """
    cuenta: Cuenta = Counter()
    leer_texto: Llamable = Path.read_text  # type: ignore[assignment]
    leer_bytes: Llamable = Path.read_bytes  # type: ignore[assignment]
    correr: Llamable = subprocess.run  # type: ignore[assignment]

    def _texto(self: Path, *a: object, **k: object) -> object:
        cuenta[("read_text", str(self))] += 1
        return leer_texto(self, *a, **k)

    def _bytes(self: Path, *a: object, **k: object) -> object:
        cuenta[("read_bytes", str(self))] += 1
        return leer_bytes(self, *a, **k)

    def _correr(*a: object, **k: object) -> object:
        orden = a[0] if a else k.get("args", ())
        pasos = orden if isinstance(orden, (list, tuple)) else [orden]
        cuenta[("subprocess", " ".join(str(x) for x in pasos))] += 1
        return correr(*a, **k)

    Path.read_text = _texto  # type: ignore[method-assign,assignment]
    Path.read_bytes = _bytes  # type: ignore[method-assign,assignment]
    subprocess.run = _correr  # type: ignore[assignment]
    try:
        yield cuenta
    finally:
        Path.read_text = leer_texto  # type: ignore[method-assign,assignment]
        Path.read_bytes = leer_bytes  # type: ignore[method-assign,assignment]
        subprocess.run = correr  # type: ignore[assignment]


def repetidas(cuenta: Cuenta) -> list[tuple[tuple[str, str], int]]:
    """Las que salieron más de una vez, de la peor a la menos mala."""
    return sorted(((k, n) for k, n in cuenta.items() if n > 1), key=lambda kv: -kv[1])


def _reloj() -> object:
    sys.path.insert(0, str(RAIZ / "scripts"))
    import error_del_estimador

    return error_del_estimador.reloj()


def _huerfanos() -> object:
    sys.path.insert(0, str(RAIZ / "scripts"))
    import huerfanos

    huerfanos.reparto.cache_clear()
    return huerfanos.reparto()


def _portada() -> object:
    sys.path.insert(0, str(RAIZ / "src"))
    from docbench_es.report.portada import del_repo

    return del_repo(RAIZ)


INSTRUMENTOS: dict[str, Callable[[], object]] = {
    "error_del_estimador.reloj": _reloj,
    "huerfanos.reparto": _huerfanos,
    "report.portada.del_repo": _portada,
}
"""Los instrumentos que el aro vigila. **Los tres leen ficheros caros y publican números.**

`reloj` es el de L7 —el que trajo el defecto—, `reparto` el de L5 y `del_repo` el que
entra con la portada. El de L4 no está: necesita el corpus, y eso no corre en la puerta.
"""


def main() -> int:
    fuera = 0
    print(f"\n  {len(INSTRUMENTOS)} instrumentos vigilados\n")
    for nombre, llamar in INSTRUMENTOS.items():
        with contando() as cuenta:
            llamar()
        repes = repetidas(cuenta)
        print(f"  {nombre:<32} {sum(cuenta.values()):3d} lecturas · {len(repes)} repetidas")
        for (que, arg), n in repes:
            fuera += 1
            print(f"      {n}x  {que}  {arg.replace(str(RAIZ) + '/', '')}")
    print(
        "\n  Una lectura repetida dentro de UNA llamada es el defecto de L4, L5 y L7.\n"
        if fuera
        else "\n  Ninguna lectura repetida.\n"
    )
    return 1 if fuera else 0


if __name__ == "__main__":
    sys.exit(main())
