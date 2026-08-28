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
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from huerfanos import reparto  # noqa: E402
from rota import Rota  # noqa: E402

# Los que ACUMULAN: un ADR o un diario registran el estado de un momento, y
# actualizarles una cifra sería reescribir la historia.
ACUMULAN = ("RESULTS.md", "ESTADO.md", "LIMITS.md", "CHANGELOG.md", "MANUAL.md")


@lru_cache(maxsize=1)
def _cuantos_limites() -> int:
    """Cuántas entradas numeradas tiene `LIMITS.md` **hoy**, leído UNA vez por corrida.

    Estaba dentro de la regla, que se aplica **una vez por documento**: nueve lecturas y
    nueve barridos del fichero más grande del repo para obtener el mismo número. Mismo
    caso que `huerfanos.reparto`, y la misma cura.
    """
    return len(
        set(
            re.findall(
                r"^(\d+)\. ", (RAIZ / "LIMITS.md").read_text(encoding="utf-8"), flags=re.MULTILINE
            )
        )
    )


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
    reales = _cuantos_limites()
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


ADR_TECHO = RAIZ / "docs" / "adr" / "0022-el-techo-de-la-puerta.md"

CON_TECHO_VIVO: tuple[str, ...] = (
    "docs/adr/0022-el-techo-de-la-puerta.md",
    "docs/metrics.md",
    "ESTADO.md",
    "RESULTS.md",
    "LIMITS.md",
    "README.md",
)
"""Los documentos donde una copia VIVA del techo puede aparecer.

No es «todos»: es donde ya apareció alguna. El escrutinio del paso 4 encontró dos
—`docs/metrics.md` y `ESTADO.md`— que publicaban **20 000 en CI** cuando la fuente dice
21 000, y ninguna de las dos estaba en el censo de LIMITS 111. Se añaden aquí y se
escriben en la FORMA CANÓNICA para que esta regla las vea.
"""

FORMA_CANONICA = re.compile(r"Techo vigente: (\d+) ms local · (\d+) ms en CI")
"""La forma que esta regla comprueba. **Lo que no se escriba así, no lo ve nadie**, y eso
está declarado en LIMITS 111: una copia en prosa con otra redacción es indistinguible de
una nota histórica para cualquier expresión regular."""


@lru_cache(maxsize=1)
def _techos_de_la_fuente() -> dict[str, int]:
    """Los techos de `.techos`, que es su fuente única."""
    fuera: dict[str, int] = {}
    for linea in (RAIZ / ".techos").read_text(encoding="utf-8").splitlines():
        if re.fullmatch(r"TECHO_(LOCAL|CI)_MS=\d+", linea.strip()):
            clave, valor = linea.strip().split("=")
            fuera[clave] = int(valor)
    return fuera


def techo_vigente_del_adr(_texto: str, documento: str) -> list[Rota]:
    """**R6 · la línea «techo vigente» de ADR-0022 contra `.techos`.**

    Es la copia número cinco de las seis que tenía el techo, y la única que no puede
    LEER la fuente porque es prosa. Así que se comprueba contra ella, que es la otra
    mitad de la regla: *o la lee o se comprueba contra ella*.

    **Corre una sola vez**, colgada del primer documento del barrido, porque no es una
    comprobación sobre el texto de nadie: es sobre un fichero fijo. Los ADR están fuera
    del barrido a propósito —registran el estado del día en que se decidió— y **éste es
    la excepción declarada**: ADR-0022 dice de sí mismo que se re-justifica en cada
    cierre, así que su techo vigente es una afirmación sobre hoy y no un registro.

    `_texto` va sin usar y con guion bajo delante **a propósito**: la firma es la de
    todas las reglas del barrido, y romperla para esta una obligaría a `derivadas.py` a
    saber cuál es cuál. Una excepción en el bucle es más cara que un argumento ignorado.
    """
    if documento != "RESULTS.md":
        return []
    fuente = _techos_de_la_fuente()
    fuera: list[Rota] = []
    vistas = 0
    for nombre in CON_TECHO_VIVO:
        texto = (RAIZ / nombre).read_text(encoding="utf-8")
        for casa in FORMA_CANONICA.finditer(texto):
            vistas += 1
            linea = texto[: casa.start()].count("\n") + 1
            for i, clave in enumerate(("TECHO_LOCAL_MS", "TECHO_CI_MS")):
                if int(casa.group(i + 1)) != fuente.get(clave, -1):
                    fuera.append(
                        Rota(
                            nombre,
                            linea,
                            f".techos {clave}",
                            casa.group(i + 1),
                            str(fuente.get(clave)),
                        )
                    )
    if not vistas:
        # UN GUARDIÁN CON ALCANCE CERO SE LEE IGUAL QUE UNO EN VERDE. Si nadie escribe ya
        # la forma canónica, esta regla no protege nada y tiene que decirlo.
        fuera.append(
            Rota("docs/adr/0022-el-techo-de-la-puerta.md", 0, ".techos", "0 copias vistas", "≥1")
        )
    return fuera
