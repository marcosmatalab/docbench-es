"""El límite de 300 líneas de `CLAUDE.md`, **comprobado por ejecución**.

Fichero aparte de `test_barreras.py` por el propio límite que hace cumplir, que es
la forma más literal posible de demostrar que funciona.

`CLAUDE.md` lo dice sin matices —«Ningún fichero por encima de 300 líneas»— y hay
siete ficheros del repo cuyo docstring justifica su existencia citándolo
(`_cosecha.py`, `_sumario.py`, `_contra_el_plan.py`, `sondeo_lib.py`,
`censo_mutaciones.py`…). **No lo comprobaba nada**, y así acabaron seis por encima
sin que nadie lo viera. Lo encontró el escrutinio adversarial del cierre de L3.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


TOPE_LINEAS = 300

PASAN_DE_300: dict[str, str] = {
    "tests/unit/test_recuentos.py": (
        "664 · el guardián de recuentos: la tabla de patrones y el corpus de frases "
        "que la justifica. Partirlo los separaría"
    ),
    "tests/unit/test_harvest.py": (
        "395 · la cosecha es el módulo irreversible de L3, y cada punto de su "
        "contrato lleva su test"
    ),
    "tests/unit/conftest.py": (
        "329 · dos responsabilidades, declaradas en su propio docstring: los "
        "recuentos y la fixture `registrar`"
    ),
    "scripts/referencias.py": (
        "328 · el barrido, con su tabla `DECLARADAS` y una razón por entrada"
    ),
    "tests/unit/test_verificar_corpus.py": (
        "318 · el criterio de aceptación de L3, con sus dos direcciones por comprobación"
    ),
    "tests/unit/test_canonical_invariantes.py": "310 · viene de L1",
}
"""Los que ya estaban por encima cuando se escribió esta barrera, **con su tamaño
y su razón**. No es una amnistía: es la deuda, enumerada, y el candado impide que
crezca la lista. Los seis son ficheros de test o scripts; **ni uno de `src/`**."""


def test_ningun_fichero_de_codigo_pasa_de_300_lineas() -> None:
    """La regla de `CLAUDE.md`, por fin comprobada por ejecución.

    Se comprueba sobre lo que git rastrea, que es lo que existe para quien clona.
    Un fichero nuevo por encima del tope pone rojo; los seis heredados están
    enumerados arriba con su razón, y **desaparecer de esa lista al partirlos es
    parte del arreglo**.
    """
    rastreados = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=RAIZ, capture_output=True, text=True, check=True
    ).stdout.split()
    pasados = {
        f: len((RAIZ / f).read_text(encoding="utf-8").splitlines())
        for f in rastreados
        if (RAIZ / f).exists()
        and len((RAIZ / f).read_text(encoding="utf-8").splitlines()) > TOPE_LINEAS
    }

    nuevos = {f: n for f, n in pasados.items() if f not in PASAN_DE_300}

    assert nuevos == {}, (
        f"ficheros nuevos por encima de {TOPE_LINEAS} líneas: {nuevos}. "
        "CLAUDE.md: «Si un módulo crece, se parte». Si de verdad no se puede, "
        "añádelo a PASAN_DE_300 con su razón — y esa razón se lee en el cierre"
    )


def test_la_lista_de_excepciones_no_guarda_ficheros_que_ya_caben() -> None:
    """El control negativo de la barrera anterior, y no es simetría decorativa.

    Una excepción que sobra es **una afirmación vieja una capa más adentro**: dice
    «este fichero no se pudo partir» de uno que ya cabe, y con ella la lista deja
    de medir la deuda. Mismo criterio que el barrido de referencias, que también
    se pone rojo si sobra una declaración.
    """
    sobran = [
        f
        for f in PASAN_DE_300
        if (RAIZ / f).exists()
        and len((RAIZ / f).read_text(encoding="utf-8").splitlines()) <= TOPE_LINEAS
    ]

    assert sobran == [], f"ya caben en {TOPE_LINEAS} líneas y siguen declarados: {sobran}"
