"""LA PUERTA ÚNICA DE LOS DATOS QUE NO ESTÁN EN GIT. **Lanza; nunca devuelve vacío.**

    uv run python scripts/fuera_de_git.py            # el censo: quién los lee y cómo

## El fallo que cierra, y va por la cuarta

`censo_tablas.tablas()` recorría `runs/l3/docs` —362 MB de XML que el repo no versiona— y
**devolvía `{}` cuando no estaban**. Sin corpus no fallaba: `poblacion_l5` seguía
corriendo, repartía los 1.000 documentos como si ninguno tuviera tabla y emitía **otra
predicción**. El test que la comprobaba habría pasado en verde en un clon frío afirmando
un número falso.

> **Un test que degrada en silencio es peor que un test roto.** El roto se ve; éste
> afirma algo distinto de lo que dice afirmar, y lo afirma **en verde**.

Y es un patrón, no un caso: el barrido de referencias que medía la máquina de quien lo
escribió, el `mypy` que no veía los huérfanos, el límite 109 con la primera tabla de L5
irreproducible en un clon, y esto.

## La regla

> **Todo dato que no está en git se lee por aquí, y aquí se LANZA si no está.**

No es una comodidad para dar mejores mensajes: es lo que convierte «no hay datos» en un
rojo en vez de en un número distinto. Quien puede seguir sin el dato lo dice **arriba**
—`pytest.mark.skipif` con su razón— y no abajo devolviendo un vacío.

## Qué NO hace

**No comprueba que la ruta esté de verdad fuera de git.** Eso lo sabe `git ls-files` y
cuesta un subproceso por llamada. Lo que hace es tener **una sola lista declarada** de las
raíces, con su razón, y lanzar con esa razón dentro. La lista y su censo se comprueban en
`tests/unit/test_datos_fuera_de_git.py`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

RAICES: dict[str, str] = {
    "runs/l3/docs": "los 362 MB del corpus. Versionado va el manifiesto, no los bytes (ADR-0038)",
    "runs/l5/campana": (
        "los 143 MB de diarios de la campaña de L5. Versionado va su informe.json, "
        "no las 2.464 extracciones (LIMITS 109)"
    ),
    ".claude/.ultima-puerta": "lo escribe `medir_puerta.py` al correr; en un clon no está",
    ".claude/.congelados.sha256": "manifiesto de huellas que crea el hook `stop-gate.sh`",
    "data": "el corpus descargado. `.gitignore` lo deja fuera desde L0",
}
"""Raíz -> por qué NO está en git. **Una sola lista, y `referencias.py` la lee de aquí.**

Tenía una copia en `referencias.ARTEFACTOS` con su propia redacción. Dos listas de lo
mismo divergen —es el límite 111 en pequeño— y encima cada una servía para lo contrario:
aquélla para poner rojo si aparecen en git, ésta para poner rojo si se leen sin declararlo.
Son las dos direcciones del mismo hecho y salen del mismo sitio.
"""


class FaltaElDato(FileNotFoundError):
    """El dato no está y **no se puede seguir**. Lleva la razón de por qué no está en git.

    Hereda de `FileNotFoundError` a propósito: quien ya capturaba eso sigue funcionando, y
    quien no lo capture verá un rastro con la ruta y la razón en vez de un `KeyError` tres
    funciones más arriba sobre un diccionario vacío.
    """


def raiz_de(ruta: Path) -> str | None:
    """La raíz declarada bajo la que cae `ruta`, o `None` si no cae bajo ninguna."""
    relativa = ruta.resolve().relative_to(RAIZ).as_posix() if ruta.is_absolute() else str(ruta)
    for raiz in RAICES:
        if relativa == raiz or relativa.startswith(f"{raiz}/"):
            return raiz
    return None


def exige(ruta: Path) -> Path:
    """`ruta` si existe. **Si no, lanza** — nunca devuelve un vacío ni un defecto.

    Es la línea entera de este módulo. Todo lo demás es la lista y su censo.
    """
    if ruta.exists():
        return ruta
    raiz = raiz_de(ruta)
    if raiz is None:
        raise FaltaElDato(f"{ruta} no existe, y no cae bajo ninguna raíz declarada")
    raise FaltaElDato(
        f"falta {ruta}. Está bajo `{raiz}`, que NO se versiona: {RAICES[raiz]}.\n"
        "  Quien pueda seguir sin este dato tiene que decirlo ARRIBA —saltando el test con"
        " su razón— y no aquí devolviendo un vacío que se lee como una medida."
    )


LECTORES = re.compile(r'RAIZ\s*/\s*"runs"\s*/\s*"l3"\s*/\s*"docs"|"runs/l3/docs"|"runs/l5/campana"')
"""Cómo se reconoce a un fichero que nombra una raíz declarada. **Un censo, no un candado.**"""


def censo() -> dict[str, list[str]]:
    """Quién nombra una raíz declarada, y si pasa por la puerta. **Con denominador.**"""
    con: list[str] = []
    sin: list[str] = []
    for p in sorted((RAIZ / "scripts").glob("*.py")) + sorted((RAIZ / "src").rglob("*.py")):
        texto = p.read_text(encoding="utf-8")
        if p.name == "fuera_de_git.py" or not LECTORES.search(texto):
            continue
        (con if "fuera_de_git" in texto else sin).append(str(p.relative_to(RAIZ)))
    return {"por la puerta": con, "sin pasar por la puerta": sin}


def main() -> int:
    c = censo()
    total = sum(len(v) for v in c.values())
    print(f"\n  {total} ficheros nombran una raíz declarada · {len(RAICES)} raíces\n")
    for etiqueta, ficheros in c.items():
        print(f"  {etiqueta} ({len(ficheros)}):")
        for f in ficheros:
            print(f"    {f}")
    print("\n  Lo que la puerta garantiza es que quien pasa por ella LANZA en vez de")
    print("  degradar. Los de la segunda lista van declarados uno a uno con su razón")
    print("  en tests/unit/test_datos_fuera_de_git.py, y el hueco es ese número.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
