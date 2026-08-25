"""Toda regla congelada en un `.yaml` la puede leer una máquina.

## La clase de fallo que este fichero existe para cerrar

> **UNA REGLA CONGELADA QUE NINGUNA MÁQUINA PUEDE LEER NO ES UNA REGLA.**

Un `plan.yaml` o un `computo.yaml` no son prosa: son **pre-registros**. Su valor entero
está en que se escribieron antes de medir y en que **algo los puede comprobar después**.
Si el fichero no parsea, ese algo no existe, y lo que queda es un comentario largo con
extensión `.yaml` — que se lee igual de bien y no obliga a nada.

**Pasó en este repo.** `runs/l5/computo.yaml` se commiteó solo, antes de medir, como la
regla de decisión de B5-bis… y **no parseaba**: llevaba `de longitud: el coste de OCR`
dentro de un elemento de lista, y un `: ` en un escalar plano de YAML es un error de
sintaxis. Nadie se enteró porque **nadie lo había abierto con un parser todavía**. Lo
descubrió el primer script que intentó leer un hermano suyo.

## Por qué cubre TODOS los YAML del repo y no sólo `runs/`

Por la otra regla de la casa: **una protección que no dice cuánto protege es
indistinguible de no proteger nada.** Un glob restringido a `runs/*/plan.yaml` seguiría
verde el día en que la regla siguiente se escriba en `runs/l6/muestreo.yaml`. Así que
el conjunto es «todo YAML versionado», y el test **afirma su tamaño**: si el inventario
se queda en cero porque el `git ls-files` deja de casar, se cae aquí y no en silencio.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]

# El suelo del inventario. No es el número exacto a propósito —añadir un YAML no debe
# poner el CI rojo—, pero sí impide que el conjunto se vacíe sin que nadie lo note.
MINIMO = 9


def yamls() -> list[Path]:
    """Los YAML **versionados**. `git ls-files` y no `rglob`: lo que no está en el
    índice no es una regla del proyecto, y `.venv` tiene miles."""
    salida = subprocess.run(
        ["git", "ls-files", "-z", "*.yaml", "*.yml"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [RAIZ / n for n in salida.split("\0") if n]


def test_el_inventario_no_esta_vacio() -> None:
    """La mitad que hace que el resto signifique algo."""
    encontrados = yamls()
    assert len(encontrados) >= MINIMO, (
        f"el inventario de YAML versionados ha caído a {len(encontrados)}, por debajo "
        f"de {MINIMO}. O se han borrado ficheros, o el patrón de git ls-files ya no casa "
        f"—y entonces este test estaba protegiendo cero—. Encontrados: {encontrados}"
    )


def revisar(rutas: list[Path]) -> tuple[list[str], list[str]]:
    """Los rotos y los vacíos de un conjunto de rutas. **Aquí vive la comprobación.**

    Está extraído a una función para que el control negativo de más abajo ejerza
    exactamente este código y no una copia suya: un control negativo que valida una
    reimplementación no controla nada.
    """
    rotos: list[str] = []
    vacios: list[str] = []
    for ruta in rutas:
        # Relativo al repo cuando lo es; absoluto cuando viene de un tmp_path.
        nombre = str(ruta.relative_to(RAIZ)) if ruta.is_relative_to(RAIZ) else str(ruta)
        try:
            contenido = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:  # el error se nombra, no se traga
            rotos.append(f"{nombre}: {str(e).splitlines()[0]}")
            continue
        if contenido is None:
            vacios.append(nombre)
    return rotos, vacios


def test_todas_las_reglas_parsean() -> None:
    """Un solo test que recorre todos, y NO uno parametrizado por fichero.

    Parametrizar sería más bonito en el informe, y acopla el **número de tests** al
    contenido del repo: añadir un `.yaml` añadiría un test, y el recuento de tests está
    publicado en `LIMITS.md` 51 con un test que lo hace cumplir. Un fichero de datos
    nuevo pondría el CI rojo en un sitio que no tiene nada que ver. El nombre del
    fichero roto no se pierde: sale en el mensaje.
    """
    rotos, vacios = revisar(yamls())
    assert not rotos, "YAML versionados que no parsean:\n  " + "\n  ".join(rotos)
    assert not vacios, "YAML versionados que parsean pero están vacíos: " + ", ".join(vacios)


def test_una_regla_rota_se_detecta_nombrandola(tmp_path: Path) -> None:
    """**El control negativo.** Sin esto, el verde de arriba sólo dice «no encontré
    nada», que es indistinguible de «no miré».

    El YAML de abajo es EL FALLO REAL que se encontró en `runs/l5/computo.yaml`: un
    `: ` dentro de un escalar plano de una lista. Se reproduce, no se inventa.
    """
    buena = tmp_path / "buena.yaml"
    buena.write_text("hito: L9\nregla: una cosa\n", encoding="utf-8")
    rota = tmp_path / "rota.yaml"
    # La forma EXACTA que falló: escalar plano de DOS líneas cuya primera lleva «: ».
    # En una sola línea, `- clave: valor` es un mapeo válido y no rompe nada — se
    # intentó así primero y el control negativo pasó en verde contra un YAML sano.
    rota.write_text(
        "se_mide:\n"
        "  - cubriendo LAS TRES BANDAS de longitud: el coste de OCR escala con\n"
        "    PAGINAS, no con documentos\n",
        encoding="utf-8",
    )
    vacia = tmp_path / "vacia.yaml"
    vacia.write_text("# sólo comentarios\n", encoding="utf-8")

    rotos, vacios = revisar([buena, rota, vacia])

    assert len(rotos) == 1 and "rota.yaml" in rotos[0], (
        f"la regla rota no se detectó, o no se nombró: {rotos}"
    )
    assert vacios == [str(vacia)], f"el YAML vacío no se detectó: {vacios}"
