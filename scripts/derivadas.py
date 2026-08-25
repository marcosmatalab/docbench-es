"""Recalcula los NÚMEROS DERIVADOS de los documentos publicados. El comando.

    uv run python scripts/derivadas.py --detalle ; echo $?

## Por qué existe, y por qué el guardián de recuentos no bastaba

`tests/unit/test_recuentos.py` sincroniza **recuentos**: cifras que
`tests/unit/conftest.py` recalcula en cada colección, así que no pueden quedarse
viejas. Cubre **una** de las cinco clases de número que producen estos documentos:

| Clase | Quién la vigilaba antes de esto |
|---|---|
| recuentos (`166 de 374`) | el guardián de recuentos |
| **porcentajes** (`51,7%`) | **nadie** |
| **deltas y restas** (`+136`, `-7,3 puntos`) | **nadie** |
| **sumas de una enumeración** (`9+3+3+3+3` contra «son 22») | **nadie** |
| **sellos** (`0717b70 · 164 tests`) | **nadie**, y encima salen de una variable ya impresa |

**Y ésa es la forma exacta del límite 77 aplicada al propio guardián**: una
protección que cubre una clase de cinco y **no dice cuál cubre** se lee igual que una
que las cubre todas. La auditoría en frío de `a0d85ed` encontró **doce** números
rotos, once de ellos de las cuatro clases sin vigilar, y **tres imposibles por
construcción** —un porcentaje que no sale de su propia fracción, una enumeración de
21 rotulada «son 22», y dos campos de un mismo `print` publicados divergentes—.

Y el censo dijo el tamaño antes de decidir el arreglo: **287 expresiones con forma
derivada** en los cuatro documentos. A mano no se cierra.

## La regla que hace cumplir

> **UN NÚMERO DERIVADO NO SE TECLEA. O lo emite el script que lo mide, o no se
> publica.**

El `1.213` de L4 está bien porque vive en `runs/l4/congelacion.json`. El `2.283` del
mismo párrafo estaba mal porque **no vivía en ninguna parte** y nadie podía
recomputarlo. Ésa es toda la diferencia, y es la regla entera.

## Qué comprueba, y qué NO

**Comprueba la ARITMÉTICA INTERNA de lo publicado**, que es lo que se puede hacer sin
inventar una fuente para cada frase: si un documento publica `N de M` y a su lado un
porcentaje, el porcentaje tiene que salir de esa fracción; si una tabla publica dos
filas y una de delta, el delta tiene que ser la resta.

**NO comprueba** que `N` y `M` sean ciertos —eso es medir, y lo hacen los
instrumentos—. Un `304 de 321` con los dos números mal y el 94,7% bien pasa por aquí.
Lo que caza es la clase que la auditoría encontró doce veces: **el dígito que se
sincroniza y la derivada que se queda detrás.**

**Y el hueco va declarado, como el del límite 54:** los patrones son ESTRECHOS a
propósito. Un patrón laxo se pone rojo contra prosa correcta, y un candado que da
rojos falsos enseña a ignorar el color. `--censo` mide cuántas expresiones existen
frente a cuántas se comprueban, para que el hueco sea un número y no una impresión.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from reglas_de_censo import huerfanos_declarados, limites_declarados  # noqa: E402
from rota import Rota  # noqa: E402

# Los que ACUMULAN: un diario que discute con su propio pasado.
ACUMULAN = ("RESULTS.md", "ESTADO.md", "LIMITS.md", "CHANGELOG.md", "MANUAL.md")
# Los que SOSTIENEN: la primera pantalla de alguien que no va a volver. Estos NO
# estaban en la lista, así que las reglas de este fichero protegían **cero** líneas de
# ellos — y ahí es donde apareció «hay 82 límites numerados» cuando ya eran 88.
SOSTIENEN = (
    "README.md",
    "docs/reading-order.md",
    "docs/como-se-mide-aqui.md",
    "docs/las-cinco-cosas.md",
    "docs/quien-publica-los-bancos.md",
)
DOCS = ("RESULTS.md", "ESTADO.md", "LIMITS.md", "docs/metrics.md", *SOSTIENEN)

# Las formas que un lector con calculadora reconoce como derivadas. Sirven para el
# CENSO —cuántas hay— no para comprobarlas: comprobar exige saber de dónde sale cada
# una, y eso es lo que hacen las reglas de abajo sobre las que sí se puede.
FORMAS = {
    "N de M": r"\b\d[\d.]* de \d[\d.]*\b",
    "porcentaje": r"\b\d+[,.]\d+\s?%|\b\d+\s?%",
    "puntos": r"[+\u2212-]\s?\d+[,.]?\d*\s+puntos",
    "factor": r"\b\d+[,.]?\d*\u00d7",
    "sello · tests": r"sello[^\n·]*·\s*\d+\s+tests",
}


def _numero(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def fila_de_tabla(linea: str) -> list[str]:
    """Las celdas de una fila markdown, sin los bordes."""
    if not linea.lstrip().startswith("|"):
        return []
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def porcentajes_de_una_fila(texto: str, documento: str) -> list[Rota]:
    """**R1 · una fila con `total`, `parte` y su porcentaje.**

    La forma que falló: `| 321 | 166 | 51,7% | 304 | 99,0% | 3 |`, donde 304/321 es
    94,70% y no 99,0%, y donde 321-304 son 17 y no 3. Se comprueba **cada porcentaje
    contra la primera columna numérica de su fila**, que es el total.
    """
    fuera: list[Rota] = []
    for n, linea in enumerate(texto.splitlines(), 1):
        celdas = fila_de_tabla(linea)
        if len(celdas) < 3:
            continue
        crudos = [c for c in celdas if re.fullmatch(r"\*{0,2}[\d.]+\*{0,2}", c)]
        if not crudos:
            continue
        total = _numero(crudos[0].strip("*"))
        if total <= 0:
            continue
        for i, celda in enumerate(celdas):
            m = re.fullmatch(r"\*{0,2}(\d+[,.]\d+)\s?%\*{0,2}", celda)
            if not m or i == 0:
                continue
            antes = [c for c in celdas[:i] if re.fullmatch(r"\*{0,2}[\d.]+\*{0,2}", c)]
            if len(antes) < 2:
                continue
            parte = _numero(antes[-1].strip("*"))
            esperado = 100 * parte / total
            # **La tolerancia sale de la PRECISIÓN PUBLICADA**, no es una constante.
            # Con un umbral fijo, un `99,0%` publicado sobre un 99,07% real se caza
            # o no según el umbral que se eligiera, y elegir el umbral que hace pasar
            # el caso que tengo delante es lo que este repo no admite. Con un decimal
            # publicado, lo admisible es media unidad de ese decimal.
            decimales = len(m.group(1).split(",")[-1].split(".")[-1])
            tolerancia = 0.5 * 10 ** (-decimales) + 1e-9
            if abs(esperado - _numero(m.group(1))) > tolerancia:
                fuera.append(
                    Rota(
                        documento,
                        n,
                        f"{parte:g}/{total:g}",
                        f"{m.group(1)}%",
                        f"{esperado:.2f}%".replace(".", ","),
                    )
                )
    return fuera


def enumeracion_de_mutantes(texto: str, documento: str) -> list[Rota]:
    """**R2 · «son N mutantes» contra la suma de su propia enumeración Y contra el disco.**

    La forma que falló dos veces en la MISMA tabla: `**Son 22 mutantes**, y esta es su
    composición completa, sin sumas que cuadrar`, seguido de una enumeración que suma
    **21**. La primera vez fue «son 21» sobre una enumeración de 18.
    """
    fuera: list[Rota] = []
    reales = len([f for f in (RAIZ / "scripts" / "mutantes").glob("*.py") if f.stem != "matar"])
    for m in re.finditer(r"\*\*Son (\d+) mutantes\*\*", texto):
        linea = texto[: m.start()].count("\n") + 1
        bloque = texto[m.end() : m.end() + 1400]
        suma = sum(int(x) for x in re.findall(r"\*\*[^*]+\*\* \((\d+)\)", bloque))
        if suma and suma != int(m.group(1)):
            fuera.append(Rota(documento, linea, "suma de la enumeración", m.group(1), str(suma)))
        if int(m.group(1)) != reales:
            fuera.append(
                Rota(documento, linea, "ficheros en scripts/mutantes/", m.group(1), str(reales))
            )
    return fuera


def sellos_contra_los_recuentos(texto: str, documento: str) -> list[Rota]:
    """**R3 · el denominador de un sello contra el tamaño real de su suite.**

    `sello: 0717b70 · 164 tests` publicado al lado de `control negativo 0 de 166`: los
    dos salen de `fallan + pasan` en `matar.py`, así que **no pueden diferir**. Aquí
    se comprueba lo que se puede sin re-correr: que los dos números que aparecen
    juntos coincidan entre sí.
    """
    fuera: list[Rota] = []
    for n, linea in enumerate(texto.splitlines(), 1):
        sello = re.search(r"sello[^\n·]*·\s*(\d+)\s+tests", linea)
        control = re.search(r"control negativo[^\n]{0,30}?(\d+) (?:de|muertes de) (\d+)", linea)
        if sello and control and sello.group(1) != control.group(2):
            fuera.append(
                Rota(
                    documento, n, "sello contra control negativo", sello.group(1), control.group(2)
                )
            )
    return fuera


REGLAS = (
    porcentajes_de_una_fila,
    enumeracion_de_mutantes,
    sellos_contra_los_recuentos,
    limites_declarados,
    huerfanos_declarados,
)


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--detalle", action="store_true")
    partes.add_argument("--censo", action="store_true", help="cuántas hay frente a cuántas se ven")
    args = partes.parse_args()

    rotas: list[Rota] = []
    censo = dict.fromkeys(FORMAS, 0)
    for nombre in DOCS:
        texto = (RAIZ / nombre).read_text(encoding="utf-8")
        for forma, patron in FORMAS.items():
            censo[forma] += len(re.findall(patron, texto))
        for regla in REGLAS:
            rotas += regla(texto, nombre)

    if args.censo:
        print(f"\n  CENSO de expresiones con forma derivada en {len(DOCS)} documentos\n")
        for forma, n in censo.items():
            print(f"    {forma:<16}{n:>5}")
        print(f"    {'TOTAL':<16}{sum(censo.values()):>5}")
        print("\n  Lo que estas reglas comprueban es la ARITMÉTICA INTERNA, no todas.")
        print("  El hueco es real y está declarado: ver el docstring y LIMITS.\n")

    # TODO GUARDIÁN IMPRIME SU DENOMINADOR. No «verde», sino «verde sobre N de M».
    # Este fichero miraba CUATRO documentos y ninguno de los que SOSTIENEN, así que su
    # verde significaba «no hay nada que vigilar» en `como-se-mide-aqui.md» y no «está
    # bien». Con el denominador delante, un alcance de cero no puede pasar por verde.
    print(
        f"\n  {len(DOCS)} documentos · {sum(censo.values())} expresiones con forma "
        f"derivada · {len(REGLAS)} reglas"
    )
    print(f"  {len(rotas)} derivadas que no salen de su fuente\n")
    if args.detalle or rotas:
        for r in rotas:
            print(
                f"    {r.documento}:{r.linea}  {r.que}: publicado {r.publicado}, sale {r.calculado}"
            )
    if rotas:
        print("\n  UN NÚMERO DERIVADO NO SE TECLEA. Corrige el documento, no la regla.\n")
        return 1
    print("  Aritmética interna cuadrada.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
