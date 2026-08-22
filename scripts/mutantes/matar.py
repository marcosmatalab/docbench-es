"""Corre la suite contra cada mutante y comprueba que **todos mueren**.

Un mutante que sobrevive es un hueco en los tests: hay una forma de romper el
código que ninguna aserción nota. El comando devuelve 1 si alguno sobrevive, para
que no se pueda leer un fallo como un éxito.

Los recuentos son un SUELO: las suites llevan `hypothesis`, que sortea, así que un
mutante al que sólo caza una propiedad muere unas veces y otras no. Por eso se
borra `.hypothesis` antes de cada corrida —para que la búsqueda empiece de cero— y
por eso lo que se exige es «muere», no «muere en N tests».

Uso:  uv run python scripts/mutantes/matar.py   ·   echo $?
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# mutante -> suite que tiene que caerse contra él
PLAN = [
    ("ok", "tests/unit/test_canonical_invariantes.py tests/unit/test_canonical_huecos.py"),
    ("roto", "tests/unit/test_canonical_invariantes.py tests/unit/test_canonical_huecos.py"),
    ("normalizador_identidad", "tests/unit/test_canonical_normalizar.py"),
    ("normalizador_agresivo", "tests/unit/test_canonical_normalizar.py"),
    ("n3_incompleta", "tests/unit/test_canonical_normalizar.py"),
    (
        "sin_tablas",
        "tests/unit/test_canonical_html.py tests/unit/test_canonical_conversores.py"
        " tests/unit/test_canonical_tei_texto.py",
    ),
    (
        "sin_spans",
        "tests/unit/test_canonical_html.py tests/unit/test_canonical_conversores.py"
        " tests/unit/test_canonical_tei_texto.py",
    ),
    ("clave_sin_escapar", "tests/unit/test_types_clave.py"),
    ("clave_orden_malo", "tests/unit/test_types_clave.py"),
]


def _corre(mutante: str, suite: str) -> tuple[int, int]:
    shutil.rmtree(RAIZ / ".hypothesis", ignore_errors=True)
    salida = subprocess.run(
        # SIN `-q`: `addopts` de pyproject ya lo pone, y `-qq` hace que pytest
        # SUPRIMA la linea de resumen. La primera version de este script leia
        # entonces «0 de 0» y declaraba SOBREVIVE sobre mutantes que si mueren.
        ["uv", "run", "pytest", *suite.split(), "-p", mutante, "--tb=no"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(RAIZ / "scripts" / "mutantes")},
        check=False,
    )
    texto = salida.stdout + salida.stderr
    fallan = int(m.group(1)) if (m := re.search(r"(\d+) failed", texto)) else 0
    pasan = int(m.group(1)) if (m := re.search(r"(\d+) passed", texto)) else 0
    if fallan + pasan == 0:
        # Ni un test recogido no es «el mutante sobrevive»: es que la medicion no
        # se hizo. Distinguirlo importa, porque las dos cosas se leen igual en la
        # tabla y una es un hueco en la suite y la otra un script roto.
        raise RuntimeError(f"{mutante}: pytest no recogio ni un test.\n{texto[-800:]}")
    return fallan, pasan


def main() -> int:
    supervivientes: list[str] = []
    print(f"{'mutante':<26} {'suite se cae':>13}   qué caza")
    for mutante, suite in PLAN:
        fallan, pasan = _corre(mutante, suite)
        if fallan == 0:
            supervivientes.append(mutante)
        marca = f"{fallan} de {fallan + pasan}"
        print(f"  {mutante:<24} {marca:>13}   {'SOBREVIVE' if fallan == 0 else ''}")
    if supervivientes:
        print(f"\nSOBREVIVEN, y eso es un hueco en la suite: {supervivientes}")
        return 1
    print("\nTodos mueren.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
