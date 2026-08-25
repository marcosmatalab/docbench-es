"""Qué scripts NO tipa la puerta, y cuántos son.

    uv run python scripts/huerfanos.py

`make fast` corre `mypy --strict src tests`. `scripts/` entra sólo por `mypy_path`,
así que se tipa **lo que un test alcance**, directa o transitivamente, y nada más. Este
programa calcula ese conjunto de la misma forma que mypy: cierre transitivo de las
importaciones desde `tests/`.

**Comprobado, no deducido**: se plantó `def _plantado() -> int: return "no soy un int"`
al final de `scripts/informe_l4.py` —alcanzable— y de `scripts/termometro.py` —huérfano—.
`mypy --strict src tests` cazó el primero y **no vio el segundo**.

Los mutantes de `scripts/mutantes/` no cuentan: son carga útil que se rompe a propósito
y que `matar.py` inyecta por `monkeypatch`. Tiparlos no querría decir nada.

Este fichero es, él mismo, uno de los huérfanos que cuenta. Se cuenta.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def importados(ruta: Path) -> set[str]:
    """Los nombres de módulo de primer nivel que importa un fichero."""
    fuera: set[str] = set()
    for n in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            fuera |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            fuera.add(n.module.split(".")[0])
    return fuera


def reparto() -> tuple[list[str], list[str], list[str]]:
    """(alcanzables, huérfanos, mutantes), por sus nombres de módulo."""
    scripts = {p.stem: p for p in (RAIZ / "scripts").rglob("*.py") if p.name != "__init__.py"}
    alcanzables: set[str] = set()
    frontera: set[str] = set()
    for t in (RAIZ / "tests").rglob("*.py"):
        frontera |= importados(t) & set(scripts)
    while frontera:  # cierre transitivo: es lo que hace mypy al seguir un import
        m = frontera.pop()
        if m in alcanzables:
            continue
        alcanzables.add(m)
        frontera |= (importados(scripts[m]) & set(scripts)) - alcanzables
    mutantes = {n for n, p in scripts.items() if "mutantes" in p.parts}
    return (
        sorted(alcanzables),
        sorted(set(scripts) - alcanzables - mutantes),
        sorted(mutantes),
    )


def main() -> int:
    alcanzables, huerfanos, mutantes = reparto()
    total = len(alcanzables) + len(huerfanos) + len(mutantes)
    print(f"\n  {total} scripts · {len(mutantes)} mutantes (carga útil, no cuentan)")
    print(f"  {len(alcanzables)} los tipa la puerta · {len(huerfanos)} NO\n")
    print("  huérfanos, que la puerta no ve:")
    for n in huerfanos:
        print(f"    {n}")
    print("\n  los que sí, por alcance transitivo desde tests/:")
    print("    " + ", ".join(alcanzables))
    return 0


if __name__ == "__main__":
    sys.exit(main())
