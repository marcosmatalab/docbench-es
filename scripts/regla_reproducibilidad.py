"""**R10** · cada resta entre series publicada, contra la tabla de la que sale.

## El hallazgo que la justifica, y estaba en una columna publicada

`RESULTS.md` publica desde el 24 ago 2026 dos series de 40 medidas el mismo día. La
sección se titulaba *«el protocolo reproduce a 10 ms»* y lo argumentaba bien… **sobre la
mediana**. En esa misma tabla, dos filas más abajo, están los dos p90 —**6262 y 6327**—
y **nadie los restó nunca**: son **65 ms**, más del doble del margen de 31 ms con el que
se estaba discutiendo si el techo suena.

> **Es la clase de la que este repo ya lleva cinco: una cifra que está en una columna y
> que la prosa de al lado no usa.** Al guardián de derivadas se le escapaba porque la
> resta no estaba escrita en ninguna parte — no había nada que contradijera nada.

## Qué comprueba, y por qué las tablas van ETIQUETADAS

Desde ADR-0048 **cada cierre deja un par**, así que las tablas de series se multiplican y
«la tabla de las dos series» deja de identificar a ninguna. La primera celda de la
cabecera es su **etiqueta** —`24 ago 2026`, `29 ago 2026`— y la frase canónica la nombra:

    las series del 24 ago 2026 difirieron **10 ms** en la mediana y **65 ms** en el p90

Con eso se comprueban cuatro cosas: que cada frase sale de la tabla que nombra, que las
**copias** de una tabla en otro documento coinciden con la original, que la columna
`diferencia` de cada copia es la resta, y que la etiqueta que cita una frase **existe**.

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
"""Dónde viven las tablas. **Es la fuente porque es donde el instrumento las deja
publicadas**, y la aritmética interna de lo publicado es lo que `derivadas.py` declara
comprobar."""

CON_EL_PAR: tuple[str, ...] = (
    "RESULTS.md",
    "LIMITS.md",
    "ESTADO.md",
    "docs/metrics.md",
    "docs/adr/0022-el-techo-de-la-puerta.md",
    "docs/adr/0048-el-techo-se-decide-con-dos-series.md",
    ".claude/skills/cerrar/SKILL.md",
    "scripts/medir_puerta.py",
    "scripts/serie_puerta.py",
)
"""Dónde se busca. **Los dos scripts y la skill están dentro a propósito:** una copia en
un docstring o en un guion diverge igual de bien que una en la prosa, y la sexta copia del
error del estimador ya enseñó que el sitio da igual."""

FRASE = re.compile(
    r"las series del (?P<etiqueta>[\w\s]{5,20}?) difirieron\s+\*{0,2}(?P<mediana>\d+)\s*ms\*{0,2}"
    r"\s+en\s+la\s+mediana\s+y\s+\*{0,2}(?P<p90>\d+)\s*(?:ms)?\*{0,2}\s+en\s+el\s+p90"
)
FILAS = ("mediana", "p90")
COLUMNAS = ("serie A", "serie B", "diferencia")

Tabla = dict[str, tuple[int, int, int | None]]


def _celda(texto: str) -> str:
    return texto.strip().strip("*`").strip()


def _tablas(texto: str) -> dict[str, Tabla]:
    """Las tablas de series de un texto, **por su etiqueta**.

    Se reconocen por la cabecera —`serie A` y `serie B`— y las columnas se leen **por su
    posición en esa cabecera**, no por «los dos primeros números de la fila»: las tablas
    llevan una columna `diferencia` y una regla que contara números la sumaría a la cuenta
    sin enterarse. Cada fila devuelve `(serie A, serie B, la diferencia PUBLICADA o None)`.
    """
    tablas: dict[str, Tabla] = {}
    columnas: dict[str, int] = {}
    etiqueta = ""
    for linea in texto.splitlines():
        if not linea.lstrip().startswith("|"):
            columnas = {}
            continue
        celdas = [_celda(c) for c in linea.strip().strip("|").split("|")]
        if "serie A" in celdas and "serie B" in celdas:
            columnas = {c: i for i, c in enumerate(celdas) if c}
            etiqueta = celdas[0]
            tablas.setdefault(etiqueta, {})
            continue
        if not columnas or not celdas or celdas[0] not in FILAS:
            continue
        crudas = [
            celdas[columnas[c]] if columnas.get(c, 99) < len(celdas) else "" for c in COLUMNAS
        ]
        if not all(re.fullmatch(r"\d+", c) for c in crudas[:2]):
            continue
        publicada = int(crudas[2]) if re.fullmatch(r"\d+", crudas[2]) else None
        tablas[etiqueta][celdas[0]] = (int(crudas[0]), int(crudas[1]), publicada)
    return tablas


@lru_cache(maxsize=1)
def _las_fuentes() -> dict[str, Tabla]:
    """Las tablas de la FUENTE, leídas una vez por corrida. `lru_cache` por la misma
    razón que en `reglas_de_censo`: la regla se llama una vez por documento."""
    return _tablas((RAIZ / FUENTE).read_text(encoding="utf-8"))


def _restas(tabla: Tabla) -> dict[str, int]:
    return {clave: abs(v[1] - v[0]) for clave, v in tabla.items()}


def diferencias_entre_series(_texto: str, documento: str) -> list[Rota]:
    """**R10.** Corre **una vez por corrida**, no una por documento: mira ficheros fijos.

    Si corriera por documento, un mismo desajuste saldría nueve veces y el recuento de
    «derivadas rotas» diría nueve donde hay una — el mismo cuidado que R6.
    """
    if documento != FUENTE:
        return []
    fuentes = _las_fuentes()
    fuera = [
        Rota(FUENTE, 0, "una tabla de series sin etiqueta en su primera celda", "«»", "24 ago 2026")
        for etiqueta in fuentes
        if not etiqueta
    ]
    incompletas = [e for e, t in fuentes.items() if set(t) != set(FILAS)]
    fuera += [
        Rota(
            FUENTE, 0, f"la tabla de series «{e}»", f"filas: {sorted(fuentes[e])}", str(list(FILAS))
        )
        for e in incompletas
    ]
    if not fuentes or incompletas:
        return fuera or [Rota(FUENTE, 0, "tablas de series (cabecera `serie A`)", "ninguna", ">=1")]

    copias = 0
    for nombre in CON_EL_PAR:
        ruta = RAIZ / nombre
        if not ruta.is_file():
            fuera.append(Rota(nombre, 0, "un documento de CON_EL_PAR que ya no existe", nombre, ""))
            continue
        contenido = ruta.read_text(encoding="utf-8")
        for etiqueta, tabla in _tablas(contenido).items():
            if etiqueta not in fuentes:
                fuera.append(
                    Rota(
                        nombre,
                        0,
                        "una tabla de series cuya etiqueta no está en la fuente",
                        etiqueta,
                        str(sorted(fuentes)),
                    )
                )
                continue
            for clave, valores in tabla.items():
                if nombre != FUENTE and valores[:2] != fuentes[etiqueta][clave][:2]:
                    fuera.append(
                        Rota(
                            nombre,
                            0,
                            f"copia de la fila `{clave}` de «{etiqueta}»",
                            str(valores[:2]),
                            str(fuentes[etiqueta][clave][:2]),
                        )
                    )
                esperada = _restas(fuentes[etiqueta])[clave]
                if valores[2] is not None and valores[2] != esperada:
                    fuera.append(
                        Rota(
                            nombre,
                            0,
                            f"la columna `diferencia` de {clave} en «{etiqueta}»",
                            str(valores[2]),
                            str(esperada),
                        )
                    )
        for m in FRASE.finditer(contenido):
            copias += 1
            linea = contenido[: m.start()].count("\n") + 1
            etiqueta = m.group("etiqueta").strip()
            if etiqueta not in fuentes:
                fuera.append(
                    Rota(
                        nombre,
                        linea,
                        "una frase que cita una tabla de series que no existe",
                        etiqueta,
                        str(sorted(fuentes)),
                    )
                )
                continue
            esperadas = _restas(fuentes[etiqueta])
            for clave in FILAS:
                publicado = int(m.group(clave))
                if publicado != esperadas[clave]:
                    fuera.append(
                        Rota(
                            nombre,
                            linea,
                            f"la resta de «{etiqueta}» en {clave} ({fuentes[etiqueta][clave][:2]})",
                            str(publicado),
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
