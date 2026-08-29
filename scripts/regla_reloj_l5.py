"""**R8 · el error del estimador de L5, contra `runs/l5/reloj.json`.**

    uv run python scripts/derivadas.py --detalle

## Por qué existe: un número, seis copias, dos valores

`+74,5%` en `RESULTS.md` tres veces, en la tabla de estimadores de `ESTADO.md` y en
`docs/metrics.md`; `+74,6%` en la fila de L5 de `ESTADO.md`. **Y ninguna de las seis salía
de un fichero**, así que no había cómo saber cuál era la buena sin rehacer la división a
mano — que es lo que se hizo, y salió que el 74,5% era el dividendo redondeado a dos
decimales de hora antes de dividir.

Es la forma del **límite 111** aplicada a un porcentaje en vez de a una constante: una
cifra que vive en N sitios y no se comprueba en ninguno no se separa de golpe, se separa
**por partes**, y la parte que se queda vieja es la que nadie mira. Con la diferencia de
que aquí las dos lecturas eran defendibles —la resolución declarada en `docs/metrics.md`
era ±0,2 puntos, o sea que las dos caían dentro—, y **eso es peor**: una discrepancia que
cabe dentro de la incertidumbre declarada no llama la atención de nadie.

## Cómo se comprueba, y por qué con copias enumeradas y no con una forma canónica

R6 pudo imponer una **forma canónica** —*«Techo vigente: N ms local · M ms en CI»*— porque
el techo se cita siempre igual. Este número no: aparece como celda de una tabla con la
fórmula en la cabecera, como paréntesis dentro del titular de un hito, y como frase
corrida en la prosa del método. Reescribir las seis a una forma única las haría ilegibles.

Así que se enumeran, como hace R7, **y cada patrón que deja de casar sale como `no
aparece`**: una regla que se queda sin copias que mirar dice que se ha quedado sin
copias, en vez de callarse en verde.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RELOJ = RAIZ / "runs" / "l5" / "reloj.json"

from rota import Rota  # noqa: E402


@lru_cache(maxsize=1)
def _reloj() -> dict[str, object] | None:
    """El fichero del reloj, o `None` si no está — que no es lo mismo que estar mal.

    Igual que R7 con `informe.json`: un fichero que falta es una medición que no se ha
    hecho, y decir «roto» ahí sería acusar al documento de mentir cuando lo que pasa es
    que no hay con qué comparar.
    """
    if not RELOJ.exists():
        return None
    datos: dict[str, object] = json.loads(RELOJ.read_text(encoding="utf-8"))
    return datos


def _pct(valor: float) -> str:
    """`+74,6`. **Un decimal**, que es la precisión con la que se publica."""
    return f"{valor * 100:+.1f}".replace(".", ",")


def _signo(publicado: str) -> str:
    """El menos tipográfico y el guion son el MISMO signo, y los documentos usan los dos.

    `RESULTS.md` escribe `-42,7%` con U+2212 y `ESTADO.md` escribe `+74,6%` con el `+`
    de siempre. Comparar cadenas sin normalizar esto pondría rojo un documento por su
    tipografía, que es un rojo falso — y un candado que da rojos falsos enseña a
    ignorar el color.
    """
    return publicado.replace("\u2212", "-")


def _miles(valor: float) -> str:
    """`14.439`. Segundos enteros con punto de millar, como los escriben los documentos."""
    return f"{round(valor):,}".replace(",", ".")


def _horas(valor: float, decimales: int) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def _esperados(datos: dict[str, object]) -> dict[str, str]:
    """Clave -> la cadena que el instrumento emite para ella."""
    pred: dict[str, float] = datos["prediccion"]  # type: ignore[assignment]
    real: dict[str, float] = datos["real"]  # type: ignore[assignment]
    err: dict[str, float] = datos["error_contra_lo_medido"]  # type: ignore[assignment]
    sobra: dict[str, float] = datos["sobra_de_la_prediccion"]  # type: ignore[assignment]
    return {
        "error": _pct(err["valor"]),
        "sobra": _pct(sobra["valor"]),
        "predicho_s": _miles(pred["segundos"]),
        "predicho_h2": _horas(pred["horas"], 2),
        "predicho_h3": _horas(pred["horas"], 3),
        "real_s": _miles(real["segundos"]),
        "real_h2": _horas(real["horas"], 2),
    }


S = r"[+\u2212-]"
"""El signo, en los patrones. Alias porque sale en once y alargaba cada línea.

Va como escape y no como carácter literal: el fuente queda ASCII —`ruff` marca el menos
tipográfico como carácter ambiguo— y el patrón compilado es exactamente el mismo.
"""

COPIAS: tuple[tuple[str, str, str], ...] = (
    # ---- ESTADO.md ----
    ("ESTADO.md", "predicho_h3", r"contra \*\*([\d,]+) h\*\* pre-registradas"),
    ("ESTADO.md", "error", rf"pre-registradas \(\*\*({S}[\d,]+)%\*\* contra lo medido\)"),
    (
        "ESTADO.md",
        "error",
        rf"\| L5 \| reloj de la campaña \| [\d,]+ h \| \*\*[\d,]+ h\*\* \| \*\*({S}[\d,]+)%",
    ),
    ("ESTADO.md", "predicho_h2", r"\| L5 \| reloj de la campaña \| ([\d,]+) h \|"),
    # ---- RESULTS.md ----
    ("RESULTS.md", "real_s", r"\| reloj \| \*\*([\d.]+) s = [\d,]+ h\*\* \|"),
    ("RESULTS.md", "real_h2", r"\| reloj \| \*\*[\d.]+ s = ([\d,]+) h\*\* \|"),
    (
        "RESULTS.md",
        "predicho_s",
        r"\| pre-registrado en `runs/l5/poblacion\.yaml` \| \*\*[\d,]+\*\* \| ([\d.]+) \|",
    ),
    (
        "RESULTS.md",
        "predicho_h2",
        r"\| pre-registrado en `runs/l5/poblacion\.yaml` \| \*\*([\d,]+)\*\* \|",
    ),
    ("RESULTS.md", "real_s", r"\| real \| \*\*[\d,]+\*\* \| \*\*([\d.]+)\*\* \|"),
    ("RESULTS.md", "real_h2", r"\| real \| \*\*([\d,]+)\*\* \|"),
    (
        "RESULTS.md",
        "error",
        rf"\| \*\*error contra lo medido\*\*[^|\n]*\| \| \*\*({S}[\d,]+)%\*\* \|",
    ),
    ("RESULTS.md", "sobra", rf"\| sobra de la predicción[^|\n]*\| \| ({S}[\d,]+)% \|"),
    (
        "RESULTS.md",
        "error",
        rf"sobreestimó\s+el reloj de la campaña: \*\*({S}[\d,]+)%\*\*",
    ),
    ("RESULTS.md", "error", rf"contra lo medido son \*\*({S}[\d,]+)%\*\*"),
    # ---- docs/metrics.md ----
    ("docs/metrics.md", "predicho_h2", r"\*\*Pre-registrado:\*\* ([\d,]+) h"),
    ("docs/metrics.md", "predicho_s", r"\*\*Pre-registrado:\*\* [\d,]+ h = ([\d.]+) s"),
    ("docs/metrics.md", "real_s", r"\*\*Real:\*\* ([\d.]+) s"),
    ("docs/metrics.md", "real_h2", r"\*\*Real:\*\* [\d.]+ s = \*\*([\d,]+) h\*\*"),
    (
        "docs/metrics.md",
        "error",
        rf"estimador es\s+\*\*({S}[\d,]+)%\*\* contra lo medido",
    ),
    (
        "docs/metrics.md",
        "sobra",
        rf"\(real \u2212 predicho\) / predicho`— es \*\*({S}[\d,]+)%\*\*",
    ),
)
"""`(documento, clave, patrón)`. **Las seis copias del error y las ocho de sus dos
operandos**, cada una con el grupo 1 sobre la cifra publicada.

No es «todas las cifras del bloque»: es cada sitio donde una de ellas está VIVA, o sea
donde se afirma en presente lo que el instrumento mide hoy. Las órdenes y las notas
históricas quedan fuera por la misma razón por la que R6 deja fuera las `--techo N` de
`RESULTS.md`: reescribirlas falsificaría la reproducción de una medición ya hecha.
"""


def cifras_del_reloj_l5(texto: str, documento: str) -> list[Rota]:
    """Las cifras del reloj de L5, contra el fichero que las emite."""
    datos = _reloj()
    if datos is None:
        return []
    esperados = _esperados(datos)
    fuera: list[Rota] = []
    for doc, clave, patron in COPIAS:
        if doc != documento:
            continue
        esperado = esperados[clave]
        casa = re.search(patron, texto)
        if casa is None:
            # UNA COPIA QUE DEJA DE CASAR NO ES UNA COPIA ARREGLADA. Si alguien
            # reescribe la frase, esta regla deja de vigilarla y su silencio se leería
            # como conformidad: LIMITS 111 otra vez. Así que se dice.
            fuera.append(
                Rota(documento, 0, f"reloj.json {clave} · patrón sin casar", "no aparece", esperado)
            )
        elif _signo(casa.group(1)) != esperado:
            linea = texto[: casa.start()].count("\n") + 1
            fuera.append(Rota(documento, linea, f"reloj.json {clave}", casa.group(1), esperado))
    return fuera
