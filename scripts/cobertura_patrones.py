"""Cuántos fraseos naturales caza —y cuántos se le escapan— el guardián de recuentos.

`LIMITS.md` 54 dice que `tests/unit/test_recuentos.py` sólo caza los fraseos que
alguien previó. Eso es una afirmación, y este proyecto no publica afirmaciones sin
número ni números sin comando.

    uv run python scripts/cobertura_patrones.py
    uv run python scripts/cobertura_patrones.py --detalle

Dos censos, y las dos direcciones importan:

**FALSOS POSITIVOS** — prosa correcta que el guardián leería como un recuento y
que le haría ponerse rojo contra un documento que no miente. Es la dirección
grave: un candado que da rojos falsos deja de leerse.

**ESCAPES** — formas naturales de afirmar el recuento que ningún patrón reconoce.
Es la dirección declarada en el límite 54: deja un hueco, no un rojo falso.

El corpus es a mano y **no pretende ser exhaustivo**: son frases que alguien
escribiría en ESTE repo, sacadas de un escrutinio adversarial con un agente por
familia de patrón. Su valor es que el número se mueve cuando los patrones cambian.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tests" / "unit"))

from test_recuentos import PATRONES, _plano, _valor  # noqa: E402

# (frase, clave que DEBERÍA leerse o None si la frase no es un recuento)
CORPUS: tuple[tuple[str, str | None], ...] = (
    # --- no son recuentos: si casan, es un falso positivo ---
    ("Son 0 mutantes supervivientes: matar.py devuelve 0.", None),
    ("Son cero mutantes supervivientes.", None),
    ("Los 12 mutantes existentes antes de este cierre no cubrían teds.", None),
    ("Los dos mutantes: qué mata cada uno.", None),
    ("Los dos mutantes van versionados y mueren en 20 y 7 tests.", None),
    ("cubre 3 de 7 casos del fixture", None),
    ("los cinco conversores restantes siguen sin consumidor", None),
    ("los 806 ms restantes son los tests y sus propiedades", None),
    ("el censo detecta 8525 de 8525 tablas rotas", None),
    ("teds_siempre_uno se cae en 18 tests de esa suite", None),
    ("20 de 20 a cuatro decimales", None),
    ("la tabla de asesinos usa 3 repeticiones", None),
    # --- sí son recuentos: si NO casan, se escapan ---
    ("Los 21 mutantes del repo mueren.", "mutantes"),
    ("Son 21 mutantes, no 12.", "mutantes"),
    ("sobre los 21 mutantes existentes", "mutantes"),
    ("Los 21 mutantes apuntan a canonical y a teds.", "mutantes"),
    ("El PLAN de matar.py tiene 21 mutantes.", "mutantes"),
    ("Mueren los 21 mutantes del repo.", "mutantes"),
    ("21/21 mutantes muertos.", "mutantes"),
    ("| Mutantes | 21 | todos mueren |", "mutantes"),
    ("el arnés cubre 160 de 183 tests", "dentro"),
    ("el árbol SIN mutar da 0 muertes de 160 tests", "dentro"),
    ("con control negativo 0 de 160", "dentro"),
    ("el arnés cubre 160 de los 183 tests", "dentro"),
    ("hay 23 tests restantes sin mutante", "fuera"),
    ("esos 23 tests no tienen mutante", "fuera"),
    ("23 tests quedaban fuera del arnés", "fuera"),
    ("quedan 23 tests fuera del arnés", "fuera"),
    ("la suite ya en 183 tests", "total"),
    ("la suite tiene 183 tests en total", "total"),
)


def _lee(frase: str) -> set[str]:
    plano = _plano(frase)
    return {
        clave
        for clave, patron in PATRONES
        for m in re.finditer(patron, plano)
        if _valor(m.group(1)) is not None
    }


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--detalle", action="store_true")
    args = partes.parse_args()

    falsos, escapes, bien = [], [], 0
    for frase, esperada in CORPUS:
        leidas = _lee(frase)
        if esperada is None:
            if leidas:
                falsos.append((frase, leidas))
            else:
                bien += 1
        elif esperada in leidas:
            bien += 1
        else:
            escapes.append((frase, leidas))

    no_recuentos = sum(1 for _, e in CORPUS if e is None)
    recuentos = len(CORPUS) - no_recuentos
    print(
        f"corpus de {len(CORPUS)} frases · {no_recuentos} que NO son recuentos, {recuentos} que sí"
    )
    print(
        f"  falsos positivos ... {len(falsos)}/{no_recuentos}  (prosa correcta leída como recuento)"
    )
    print(
        f"  escapes ............ {len(escapes)}/{recuentos}  (recuento real que ningún patrón ve)"
    )
    if args.detalle:
        for frase, leidas in falsos:
            print(f"    FALSO POSITIVO  {sorted(leidas)}  {frase}")
        for frase, _ in escapes:
            print(f"    ESCAPA          {frase}")
    print(
        "\nLos falsos positivos son la dirección GRAVE: ponen rojo contra un documento\n"
        "correcto. Los escapes dejan un hueco, y están declarados en LIMITS 54."
    )
    return 1 if falsos else 0


if __name__ == "__main__":
    raise SystemExit(main())
