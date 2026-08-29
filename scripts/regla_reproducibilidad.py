"""**R10** · la diferencia entre las dos series, contra la resta de su propia tabla.

## El hallazgo que la justifica, y estaba en una columna publicada

`RESULTS.md` publica desde el 24 ago 2026 dos series de 40 medidas el mismo día. La
sección se titulaba *«el protocolo reproduce a 10 ms»* y lo argumentaba bien… **sobre la
mediana**. En esa misma tabla, dos filas más abajo, están los dos p90 —**6262 y 6327**—
y **nadie los restó nunca**: son **65 ms**, más del doble del margen de 31 ms con el que
se estaba discutiendo si el techo suena.

> **Es la clase de la que este repo ya lleva cinco: una cifra que está en una columna y
> que la prosa de al lado no usa.** El guardián de derivadas existe justo para eso, y
> esta forma se le escapaba porque la resta no estaba escrita en ninguna parte —no había
> nada que contradijera nada—.

## Qué comprueba

Lee la tabla de `RESULTS.md` —la que tiene `serie A` y `serie B` en su cabecera—, hace
las dos restas, y las compara con **todas** las copias de la frase canónica

    difirieron **10 ms** en la mediana y **65 ms** en el p90

allí donde esté escrita, incluidos los **docstrings de los dos scripts** que implementan
la regla de decisión: una copia en el código diverge igual de bien que una en la prosa, y
la sexta copia del error del estimador ya enseñó que el sitio no importa.

**Y avisa si no ve ninguna copia**, que es el modo de fallo por defecto de toda regla
basada en patrones: si nadie escribe ya la forma canónica, el silencio pasa por
conformidad. Mismo aro que R6.
"""

from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from rota import Rota  # noqa: E402

FUENTE = "RESULTS.md"
"""Dónde vive la tabla. **Es la fuente porque es donde el instrumento la dejó publicada**
—las dos series son del 24 ago 2026, anteriores al modo `--series`—, y la aritmética
interna de lo publicado es exactamente lo que `derivadas.py` declara comprobar."""

CON_EL_PAR: tuple[str, ...] = (
    "RESULTS.md",
    "LIMITS.md",
    "ESTADO.md",
    "docs/metrics.md",
    "docs/adr/0048-el-techo-se-decide-con-dos-series.md",
    "scripts/medir_puerta.py",
    "scripts/serie_puerta.py",
)
"""Dónde se busca la frase. **Los dos scripts están dentro a propósito.**"""

FRASE = re.compile(
    r"difirieron\s+\*{0,2}(\d+)\s*ms\*{0,2}\s+en\s+(?:la\s+)?mediana"
    r"\s+y\s+\*{0,2}(\d+)\s*(?:ms)?\*{0,2}\s+en\s+el\s+p90"
)
FILAS = ("mediana", "p90")
COLUMNAS = ("serie A", "serie B", "diferencia")


def _celda(texto: str) -> str:
    return texto.strip().strip("*`").strip()


def _tabla(texto: str) -> dict[str, tuple[int, int, int | None]]:
    """Las dos series, **leídas de la tabla**. Ni una cifra tecleada en este fichero.

    La tabla se reconoce por su cabecera —`serie A` y `serie B`— y no por su número de
    línea: un documento que crece por arriba movería el número y no la cabecera. Y las
    columnas se leen **por su posición en esa cabecera**, no por «los dos primeros
    números de la fila»: la tabla lleva ahora una columna `diferencia` y una regla que
    contara números la sumaría a la cuenta sin enterarse.

    Devuelve, por fila, `(serie A, serie B, la diferencia PUBLICADA o None)`.
    """
    par: dict[str, tuple[int, int, int | None]] = {}
    columnas: dict[str, int] = {}
    for linea in texto.splitlines():
        if not linea.lstrip().startswith("|"):
            columnas = {}
            continue
        celdas = [_celda(c) for c in linea.strip().strip("|").split("|")]
        if "serie A" in celdas and "serie B" in celdas:
            columnas = {c: i for i, c in enumerate(celdas) if c}
            continue
        if not columnas or not celdas or celdas[0] not in FILAS:
            continue
        crudas = [
            celdas[columnas[c]] if columnas.get(c, 99) < len(celdas) else "" for c in COLUMNAS
        ]
        if not all(re.fullmatch(r"\d+", c) for c in crudas[:2]):
            continue
        publicada = int(crudas[2]) if re.fullmatch(r"\d+", crudas[2]) else None
        par[celdas[0]] = (int(crudas[0]), int(crudas[1]), publicada)
    return par


@lru_cache(maxsize=1)
def _el_par() -> dict[str, tuple[int, int, int | None]]:
    """La tabla de la FUENTE, leída una vez por corrida. `lru_cache` por la misma razón
    que en `reglas_de_censo`: la regla se llama una vez por documento."""
    return _tabla((RAIZ / FUENTE).read_text(encoding="utf-8"))


def diferencias_entre_series(_texto: str, documento: str) -> list[Rota]:
    """**R10.** Corre **una vez por corrida**, no una por documento: mira ficheros fijos.

    Si corriera por documento, un mismo desajuste saldría nueve veces y el recuento de
    «derivadas rotas» diría nueve donde hay una — el mismo cuidado que R6.
    """
    if documento != FUENTE:
        return []
    par = _el_par()
    if set(par) != set(FILAS):
        return [
            Rota(
                FUENTE,
                0,
                "la tabla de las dos series (cabecera `serie A` / `serie B`)",
                f"filas vistas: {sorted(par) or 'ninguna'}",
                f"hacen falta {list(FILAS)}",
            )
        ]
    esperadas = {clave: abs(v[1] - v[0]) for clave, v in par.items()}
    fuera: list[Rota] = []
    copias = 0
    for nombre in CON_EL_PAR:
        ruta = RAIZ / nombre
        if not ruta.is_file():
            fuera.append(Rota(nombre, 0, "un documento de CON_EL_PAR que ya no existe", nombre, ""))
            continue
        contenido = ruta.read_text(encoding="utf-8")
        for clave, valores in _tabla(contenido).items():
            if nombre != FUENTE and valores[:2] != par[clave][:2]:
                fuera.append(
                    Rota(
                        nombre,
                        0,
                        f"copia de la fila `{clave}` de las dos series",
                        str(valores[:2]),
                        str(par[clave][:2]),
                    )
                )
            if valores[2] is not None and valores[2] != esperadas[clave]:
                fuera.append(
                    Rota(
                        nombre,
                        0,
                        f"la columna `diferencia` de {clave}",
                        str(valores[2]),
                        str(esperadas[clave]),
                    )
                )
        for m in FRASE.finditer(contenido):
            copias += 1
            publicado = {"mediana": int(m.group(1)), "p90": int(m.group(2))}
            for clave, valor in publicado.items():
                if valor != esperadas[clave]:
                    fuera.append(
                        Rota(
                            nombre,
                            contenido[: m.start()].count("\n") + 1,
                            f"la resta de las dos series en {clave} ({par[clave][:2]})",
                            str(valor),
                            str(esperadas[clave]),
                        )
                    )
    if not copias:
        fuera.append(
            Rota(
                FUENTE,
                0,
                "copias de la resta entre series (la frase canónica)",
                "0 copias vistas",
                "al menos 1, o esta regla protege cero",
            )
        )
    return fuera
