"""Corre la suite contra cada mutante y comprueba que **todos mueren**.

Un mutante que sobrevive es un hueco en los tests: hay una forma de romper el
código que ninguna aserción nota. El comando devuelve 1 si alguno sobrevive, para
que no se pueda leer un fallo como un éxito.

Los recuentos son un SUELO: las suites llevan `hypothesis`, que sortea, así que un
mutante al que sólo caza una propiedad muere unas veces y otras no. Por eso se
borra `.hypothesis` antes de cada corrida —para que la búsqueda empiece de cero— y
por eso lo que se exige es «muere», no «muere en N tests».

Uso:  uv run python scripts/mutantes/matar.py   ·   echo $?
      uv run python scripts/mutantes/matar.py --tabla [--reps N] [--solo MUTANTE]
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RAIZ / "scripts"))
from sello import sello  # noqa: E402

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
    (
        "teds_siempre_uno",
        "tests/unit/test_teds_referencia.py tests/unit/test_teds_propiedades.py"
        " tests/unit/test_teds_huecos.py",
    ),
    ("teds_cuenta_la_raiz", "tests/unit/test_teds_referencia.py"),
    ("cellmatch_por_pertenencia", "tests/unit/test_cellmatch.py"),
    ("arbol_orden_invertido", "tests/unit/test_teds_referencia.py"),
    ("arbol_thead_solo_la_primera", "tests/unit/test_teds_referencia.py"),
    ("batch_sobrescribe", "tests/unit/test_teds_batch.py"),
    # Las cuatro casillas de `siempre_ok` x `siempre_roto` sobre las dos funciones
    # que L2 construye. `teds_siempre_uno` ya estaba; las otras tres faltaban, y
    # sin `siempre_roto` no hay quien cace al test que sólo afirma la mitad
    # negativa —«esto BAJA la nota»—, que un 0,0 constante satisface entero.
    (
        "teds_siempre_cero",
        "tests/unit/test_teds_referencia.py tests/unit/test_teds_propiedades.py"
        " tests/unit/test_teds_huecos.py tests/unit/test_teds_limites.py",
    ),
    ("cellmatch_siempre_ok", "tests/unit/test_cellmatch.py"),
    ("cellmatch_siempre_roto", "tests/unit/test_cellmatch.py"),
    # El candado más nuevo del repo, contra su propia rotura. Sale de la deuda 7
    # de `ESTADO.md`: «un candado que no se ha probado contra su propia rotura no
    # es un candado», y éste es una barrera, o sea código cuyo único trabajo es
    # ponerse rojo.
    # El paso del estandar que faltaba en `cerrar_seccion`. Su suite es la del
    # conversor de HTML: es donde vive la geometria que el fallo desplazaba.
    ("seccion_sin_cerrar", "tests/unit/test_grupo_de_filas.py"),
    ("recuentos_todo_vale", "tests/unit/test_recuentos.py"),
    ("recuentos_sin_claude", "tests/unit/test_recuentos.py"),
    ("recuentos_plano_flojo", "tests/unit/test_recuentos.py"),
    # L5 · EL INSTRUMENTO QUE EMITE EL TITULAR, no el que lo calcula. Hasta aquí el
    # arnés cubría `canonical`, `teds`, `cellmatch` y los recuentos, o sea la
    # aritmética; ninguno de los 22 tocaba el código que decide QUÉ se compara con
    # QUÉ, con qué denominador y cómo se imprime. Los seis de abajo rompen, uno por
    # uno, las decisiones pre-registradas de las que cuelga la primera tabla:
    # el emparejado, el recuento de fallos, la cobertura, la intersección, el delta
    # y el `n/a`. Cada uno haría mentir a una columna publicada sin que la tabla
    # pareciera rara, que es la clase de fallo que este repo llama la más grave.
    ("emparejado_sin_recuento", "tests/unit/test_nivel1.py"),
    ("fallos_no_se_cuentan", "tests/unit/test_nivel1.py"),
    ("cobertura_siempre_llena", "tests/unit/test_nivel1.py"),
    ("cara_a_cara_la_union", "tests/unit/test_nivel1.py tests/unit/test_tabla_nivel1.py"),
    ("delta_siempre_cero", "tests/unit/test_nivel1.py tests/unit/test_tabla_nivel1.py"),
    ("no_aplicable_impreso_cero", "tests/unit/test_tabla_nivel1.py"),
]


def _corre_sin_mutar(suite: str) -> tuple[int, int]:
    """El CONTROL NEGATIVO: la misma suite sin mutante ninguno.

    «Los 12 mutantes mueren» no prueba nada si el arnés no ha demostrado que sabe
    **no** matar. Si esto no da 0 fallos, la tabla entera no vale: significaría
    que la suite se cae sola y que cada «muerte» podría ser ese mismo fallo de
    fondo, no el mutante.
    """
    return _corre(None, suite)


def _corre(mutante: str | None, suite: str) -> tuple[int, int]:
    shutil.rmtree(RAIZ / ".hypothesis", ignore_errors=True)
    plugin = ["-p", mutante] if mutante else []
    salida = subprocess.run(
        # SIN `-q`: `addopts` de pyproject ya lo pone, y `-qq` hace que pytest
        # SUPRIMA la linea de resumen. La primera version de este script leia
        # entonces «0 de 0» y declaraba SOBREVIVE sobre mutantes que si mueren.
        ["uv", "run", "pytest", *suite.split(), *plugin, "--tb=no"],
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
        raise RuntimeError(
            f"{mutante or 'sin mutar'}: pytest no recogio ni un test.\n{texto[-800:]}"
        )
    return fallan, pasan


def _tabla_de_asesinos(reps: int = 3, solo: str = "") -> int:
    """Qué test mata a cada mutante, sobre `reps` repeticiones en frío.

    Recorre la suite ENTERA por mutante, no sólo su suite objetivo: un mutante
    puede morir en un fichero que no es el suyo, y saberlo es lo que revela los
    puntos únicos de fallo — un mutante al que sólo mata un test es una sola
    aserción sosteniendo una garantía.

    Publica **dos agregaciones**, que no son lo mismo: los que matan SIEMPRE (las
    `reps` repeticiones) y los que matan ALGUNA VEZ (unión). Un asesino
    intermitente no es un asesino: depende de que un sorteo salga bien.

    **SIEMPRE no es una categoría, es una estimación con este n.** Un test que
    mata con probabilidad p sale «SIEMPRE» con probabilidad p^reps: a p = 0,9 y
    reps = 3, eso es el 73% de las veces. Por eso `--reps` existe y por eso el n
    va publicado al lado de la tabla.

        --reps 10 --solo normalizador_agresivo    # afinar la tasa de uno
    """
    print(f"{'mutante':<28}{'siempre':>9}{'alguna vez':>12}   único asesino, si lo hay")
    unicos: list[str] = []
    for mutante, _ in PLAN:
        if solo and mutante != solo:
            continue
        cuenta: dict[str, int] = {}
        for _ in range(reps):
            shutil.rmtree(RAIZ / ".hypothesis", ignore_errors=True)
            salida = subprocess.run(
                ["uv", "run", "pytest", "tests/unit", "-p", mutante, "--tb=no"],
                cwd=RAIZ,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": str(RAIZ / "scripts" / "mutantes")},
                check=False,
            )
            # Un test parametrizado imprime UNA linea FAILED POR PARAMETRO, asi
            # que hay que colapsarlas por corrida antes de contar. Sin este
            # `set`, `test_teds_coincide_con_la_referencia` sumaba 39 —13 casos x
            # 3 corridas— en vez de 3, no cumplia `n == 3` y salia de la columna
            # SIEMPRE aunque mate en las tres. Se publico asi: `teds_cuenta_la_raiz`
            # aparecio como 6 de 8 deterministas cuando sus 8 asesinos lo son.
            for nombre in {
                linea.split()[1].split("[")[0]
                for linea in (salida.stdout + salida.stderr).splitlines()
                if linea.startswith("FAILED")
            }:
                cuenta[nombre] = cuenta.get(nombre, 0) + 1
        siempre = sorted(t for t, n in cuenta.items() if n == reps)
        unico = siempre[0].split("::")[-1] if len(cuenta) == 1 else ""
        if len(cuenta) == 1:
            unicos.append(f"{mutante} -> {unico}")
        print(f"  {mutante:<26}{len(siempre):>9}{len(cuenta):>12}   {unico[:44]}")
        # La diferencia entre las dos columnas SIEMPRE lleva nombre y tasa. Sin
        # esto, dos corridas del mismo arnes dan columnas distintas y no hay
        # forma de saber por que: paso en L2 con `normalizador_agresivo`, 9/9 en
        # una corrida y 8/9 en la siguiente, y reconciliarlo costo medir aparte.
        for t, n in sorted(cuenta.items()):
            # Con `--solo` se listan TODOS con su tasa, no sólo los flojos: para
            # poder afirmar «esta propiedad lo mata 10 de 10» hace falta ver el
            # 10, no deducirlo de que no aparezca en la lista de intermitentes.
            if n < reps or solo:
                print(f"{'':<28}{n:>2}/{reps}   {t.split('/')[-1]}")
    if unicos:
        print("\nPUNTO ÚNICO DE FALLO (un solo test sostiene la garantía):")
        for u in unicos:
            print(f"  {u}")
    return 0


def main() -> int:
    if "--tabla" in sys.argv:
        reps = int(sys.argv[sys.argv.index("--reps") + 1]) if "--reps" in sys.argv else 3
        solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else ""
        return _tabla_de_asesinos(reps, solo)

    # CONTROL NEGATIVO primero: el arnés tiene que saber NO matar.
    suites = " ".join(sorted({s for _, s in PLAN}))
    fallan, pasan = _corre_sin_mutar(suites)
    # El sello va PRIMERO y sale del propio instrumento: toda cifra de aquí abajo
    # lleva denominador de suite, o sea que caduca sola cuando la suite crece.
    # UNA SOLA LÍNEA, y es a propósito. El sello y el control negativo salen de la
    # MISMA expresión —`fallan + pasan`— así que no pueden diferir en una corrida; y
    # sin embargo se publicaron divergentes tres veces («164 tests» junto a «0 de
    # 166»), porque al pegarlos en el documento iban en dos líneas y una se
    # actualizaba sin la otra. **Dos campos de un mismo `print` no pueden divergir si
    # nadie los separa**: ésta es la línea que se pega, entera.
    print(f"sello: {sello(fallan + pasan)} · control negativo: {fallan} muertes")
    if fallan:
        print("EL ÁRBOL SIN MUTAR YA FALLA. La tabla de mutantes no vale nada hasta arreglarlo.")
        return 1

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
