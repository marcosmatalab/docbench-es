"""Las reglas de `derivadas.py` que comprueban un RECUENTO contra su censo real.

Van aparte porque `derivadas.py` se pasó de 300 líneas al meterlas, y porque son de otra
clase que las demás: las otras comprueban la aritmética **dentro** de un documento —una
suma, un porcentaje, dos cifras que aparecen juntas—, y éstas van a **contar ficheros en
el disco** y comparar. Necesitan importar los censos; las otras no necesitan nada.

Las dos nacieron de números que llevaban días viejos sin que nadie los mirara:
«hay 82 límites numerados» cuando eran 88, y «22 de 36 huérfanos» cuando eran 25 de 42.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from huerfanos import reparto  # noqa: E402
from rota import Rota  # noqa: E402

# Los que ACUMULAN: un ADR o un diario registran el estado de un momento, y
# actualizarles una cifra sería reescribir la historia.
ACUMULAN = ("RESULTS.md", "ESTADO.md", "LIMITS.md", "CHANGELOG.md", "MANUAL.md")


def limites_declarados(texto: str, documento: str) -> list[Rota]:
    """**R4 · «hay N límites numerados» contra los que LIMITS.md tiene de verdad.**

    `docs/como-se-mide-aqui.md` publicaba **82** cuando ya eran **88**. Es el modo de
    fallo de la regla 3 en su forma más pura: un número derivado tecleado en un
    documento que **sostiene**, mientras su fuente crece sola por debajo. Y estaba
    justo en la regla que dice *«lo que NO se mide se publica igual de fuerte»* — o
    sea, la frase que vende el rigor llevaba dentro el número equivocado.

    **No se comprueban los ADR**, y es deliberado: un ADR registra el estado en el
    momento de decidir. Actualizarle una cifra sería reescribir la historia, que es lo
    contrario de para lo que existe. Los documentos que ACUMULAN tampoco. Sólo los que
    SOSTIENEN, que son los que alguien lee esperando el estado de hoy.
    """
    if documento.startswith("docs/adr/") or documento in ACUMULAN:
        return []
    reales = len(
        set(
            re.findall(
                r"^(\d+)\. ", (RAIZ / "LIMITS.md").read_text(encoding="utf-8"), flags=re.MULTILINE
            )
        )
    )
    fuera: list[Rota] = []
    for m in re.finditer(r"[Hh]ay (\d+) l[íi]mites numerados", texto):
        linea = texto[: m.start()].count("\n") + 1
        if int(m.group(1)) != reales:
            fuera.append(Rota(documento, linea, "entradas en LIMITS.md", m.group(1), str(reales)))
    return fuera


def huerfanos_declarados(texto: str, documento: str) -> list[Rota]:
    """**R5 · «huérfanos: N de M» contra lo que el censo de scripts dice hoy.**

    La primera versión de LIMITS 84 publicó «22 de 36» y estaba vieja **seis días
    después de escribirla**: el propio trabajo de B5-bis añadió scripts, y ninguno de
    ellos lo alcanza un test. Es la regla 3 aplicada a un número que vive **dentro de un
    límite que habla de otra cosa** — el sitio donde nadie va a mirarlo.
    """
    alcanzables, huerfanos, _mutantes = reparto()
    # El denominador son los NO mutantes: tipar un mutante no querría decir nada, así
    # que meterlos en el total inflaría el denominador y haría parecer menor el hueco.
    real = f"{len(huerfanos)} de {len(huerfanos) + len(alcanzables)}"
    fuera: list[Rota] = []
    for m in re.finditer(r"hu[ée]rfanos: \*?\*?(\d+) de (\d+)", texto):
        publicado = f"{m.group(1)} de {m.group(2)}"
        if publicado != real:
            linea = texto[: m.start()].count("\n") + 1
            fuera.append(Rota(documento, linea, "scripts/huerfanos.py", publicado, real))
    return fuera
