"""Toda referencia a un fichero, módulo, comando u objetivo de `make`, comprobada.

**El patrón que lo motiva, y ya van cinco.** Cinco veces ha aparecido lo mismo:
un documento o un fichero de configuración **afirmaba algo sobre código que no se
estaba construyendo**, y la afirmación sobrevivió hasta el hito que se la creyó.

| # | Qué afirmaba | Cómo se descubrió |
|---|---|---|
| 1 | el docstring de `sources/` | de refilón |
| 2 | «en `.claude/rules/` hay 3 ficheros», con cuatro | leyendo una regla nueva |
| 3 | recuentos de tests viejos en cuatro documentos | un cierre |
| 4 | `is_header` | escribiendo el conversor |
| 5 | cinco entry points a módulos inexistentes | la primera llamada a `descubrir()` |

Las cinco se encontraron **tropezándose**. Esto lo hace a propósito y de una vez:

    uv run python scripts/referencias.py
    uv run python scripts/referencias.py --detalle

**Comprueba por ejecución, no por lectura.** Un fichero existe si el sistema de
ficheros lo dice; un módulo existe si `importlib` lo importa; un objetivo de `make`
existe si `make -n` no dice «No rule to make target»; una herramienta existe si
está en el `bin` del entorno. Leer el repo y creerse lo que dice es exactamente el
fallo que esto persigue.

## Qué NO se recorre, y por qué

`MANUAL.md` y `HITOS.md` describen el proyecto **terminado**: su árbol de ficheros
está lleno de módulos que llegan en L5, L13 o L17, y todos «rotos» hoy. Meterlos
aquí produciría cien falsos positivos, y un informe con cien falsos positivos no
se lee. Los seis que sí se recorren son los **operativos**: los que describen lo
que hay, no lo que habrá.

## El apartado de futuras, que es lo que evita aflojar el criterio

Una referencia puede apuntar legítimamente a algo que todavía no existe —`ESTADO.md`
habla de lo que hará el hito siguiente—. Ésas van en `FUTURAS`, **una a una y con
su razón escrita**, nunca por patrón. El día que el fichero exista, su línea sobra
y hay que quitarla: eso es un recordatorio, no una excepción permanente.
"""

from __future__ import annotations

import argparse
import importlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

FUENTES: tuple[str, ...] = (
    "pyproject.toml",
    "Makefile",
    "CLAUDE.md",
    "ESTADO.md",
)
"""Los ficheros operativos sueltos. Los workflows y las skills se añaden por glob."""

DECLARADAS: dict[str, str] = {
    "tests/fixtures/tablas": "lo crea L6; CLAUDE.md ya dice que crearlo la primera vez sí se puede",
    "tests/fixtures/quickstart": "lo crea L7, mismo párrafo de CLAUDE.md",
    "tests/fixtures/quickstart/plan.yaml": "el plan congelado de `make quickstart`, L7",
    "docbench_es.cli.main:app": "la CLI llega en L5. Deuda 4 de ESTADO.md, con su fecha",
    "docs/entity-guide.md": "la skill `entidad` lo lee «si ya existe»: guardado en el propio texto",
    "runs/2026-Q4/plan.yaml": "ruta de EJEMPLO en la ayuda de `make bench`; la escribe quien mide",
    "runs/2026-Q4": "misma ruta de ejemplo, sin el fichero",
    "runs/nightly": "directorio de SALIDA que crea el workflow nocturno al correr",
}
"""Referencia -> por qué NO apunta a algo que exista hoy. Vacío sería lo ideal.

Se llena **a mano y una a una, con su razón**. Un patrón aquí («todo lo de
`entity/` puede faltar») convertiría el barrido en un adorno: lo que hace que
valga es que cada excepción tenga dueño y un día en el que sobra. Las tres
familias que hay dentro son distintas y conviene no mezclarlas al leerlas:
**lo que llega con su hito**, **lo que es un ejemplo** y **lo que el propio texto
declara opcional**.

Las ocho marcadas `PENDIENTE de L3` son un caso aparte y conviene verlo: son el
**inventario de lo que falta** que `ESTADO.md` publica. Que estén aquí no las
excusa — las convierte en una lista de tareas que **el propio barrido tacha**: el
día que el fichero exista, su línea sobra y `referencias.py` se pone rojo pidiendo
que la quites."""

EXTENSIONES = "py|md|toml|yaml|yml|sh|json|cfg|ini|txt|lock|sha256"

RUTA = re.compile(rf"(?<![\w/.])((?:[\w.\-]+/)+[\w.\-]+(?:\.(?:{EXTENSIONES}))?)")
"""Algo con al menos una barra. Sin barra hay demasiada prosa que parece fichero."""

FICHERO = re.compile(rf"[\w\-]+\.(?:{EXTENSIONES})$")
"""Con extensión conocida **y con nombre delante**: `s/.py` sale de un `sed`, no
de un fichero. Salió del primer barrido, con cuatro casos como ése."""

CITA_ADR = re.compile(r"\bADR-(\d{4})\b")
"""Una cita a una decisión por su número. **Se comprueba que el fichero exista.**

Salió de un caso real y feo: `ADR-0030` estaba citado en tres documentos —uno de
ellos otro ADR, otro un módulo de `src/`— y **no existía en ningún commit de
ninguna rama**. Una cita a una decisión que nadie puede ir a leer es peor que una
ruta rota: la ruta se nota al abrirla, y la cita se cree."""

MAYUSCULAS = re.compile(r"[A-Z]{3,}")
"""`NNNN-slug.md` es una plantilla y `PDF/XML` es una pareja de formatos. Ninguno
de los dos es una ruta, y los dos casaban."""


def _es_ruta(valor: str) -> bool:
    """Tres filtros, y cada uno salió de un falso positivo del primer barrido.

    El de los directorios es el que más aprieta: **una referencia sin extensión
    sólo se comprueba si su primer segmento existe en la raíz del repo**, o
    `actions/checkout` y `Deuda/p` entran como ficheros rotos. Lo que se paga está
    escrito en el límite: una ruta inventada bajo un directorio que tampoco existe
    —`srcs/algo/` sin extensión— se salta. Con extensión sí se caza, y es el caso
    común.
    """
    if MAYUSCULAS.search(valor):
        return False
    if FICHERO.search(valor):
        return True
    primero = valor.split("/", 1)[0]
    return primero in {p.name for p in RAIZ.iterdir()}


RAIZ_SUELTA = re.compile(
    r"(?<![\w/.])((?:MANUAL|HITOS|ESTADO|LIMITS|RESULTS|README|CHANGELOG|CLAUDE"
    r"|PARCHES|LEEME-PRIMERO|ARQUITECTURA-AGENTICA)\.md|Makefile|pyproject\.toml|\.importlinter)"
)
MODULO = re.compile(r"([\w.]+):([\w]+)")
OBJETIVO = re.compile(r"\bmake\s+([a-z][\w-]*)")
HERRAMIENTA = re.compile(r"\buv run\s+(?!python\b)([a-z][\w-]*)")


@dataclass(frozen=True)
class Referencia:
    tipo: str
    valor: str
    fuente: str
    linea: int


TODO = frozenset({"ruta", "modulo", "objetivo", "herramienta", "adr"})
SOLO_CITAS = frozenset({"adr"})
"""Qué se extrae de cada clase de fuente. **Los dos conjuntos importan.**

De los ficheros **operativos** se mira todo: describen lo que hay hoy. De
`docs/adr/` y de `src/**.py` **sólo las citas `ADR-NNNN`**, y no es pereza: un ADR
viejo escribe rutas en prosa —`core/teds/_arbol.py`, `types/_invariantes.py`— y a
veces rutas que **nunca fueron de este repo**, como el `src/metric.py` de
PubTabNet. Mirarlas daría dieciséis rojos sobre documentos que no mienten, y
reescribir la prosa de un ADR cerrado para callar a un linter es peor que el
linter."""


def _fuentes() -> list[Path]:
    """Los ficheros operativos: los que describen lo que hay, no lo que habrá."""
    sueltos = [RAIZ / n for n in FUENTES]
    globs = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
    skills = sorted((RAIZ / ".claude").rglob("*.md"))
    return [p for p in sueltos + globs + skills if p.exists()]


def _fuentes_de_citas() -> list[Path]:
    """Todo lo que puede citar una decisión por su número: los ADR y el código.

    Se añadieron cuando apareció un `ADR-0030` citado desde tres sitios y sin
    fichero detrás — y **uno de los tres era un módulo de `src/`**, que no se
    estaba mirando.
    """
    adrs = sorted((RAIZ / "docs" / "adr").glob("*.md"))
    codigo = sorted((RAIZ / "src").rglob("*.py"))
    return adrs + codigo


def _sin_ruido(texto: str) -> str:
    """Fuera URLs y globs: ni una ni otro son una ruta que se pueda comprobar."""
    return re.sub(r"https?://\S+", " ", texto).replace("*", " ")


def _referencias(
    fuentes: list[Path] | None = None, tipos: frozenset[str] = TODO
) -> list[Referencia]:
    """Las fuentes entran por parámetro para que el test pueda darle las suyas.

    Sin esto, la única forma de probar que este barrido **se pone rojo** sería
    romper el repo de verdad. Una barrera que sólo se puede probar rompiendo lo
    que protege es una barrera que no se prueba.
    """
    vistas: set[tuple[str, str]] = set()
    salida: list[Referencia] = []
    for fichero in fuentes if fuentes is not None else _fuentes():
        # Una fuente de fuera del repo es lo que usa el test de la barrera: sin
        # esto, probarla desde `tmp_path` reventaba con un `ValueError`.
        nombre = str(fichero.relative_to(RAIZ)) if fichero.is_relative_to(RAIZ) else str(fichero)
        for n, cruda in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            linea = _sin_ruido(cruda)
            candidatos = (
                [("ruta", m.group(1)) for m in RUTA.finditer(linea) if _es_ruta(m.group(1))]
                + [("ruta", m.group(1)) for m in RAIZ_SUELTA.finditer(linea)]
                + [("modulo", m.group(0)) for m in MODULO.finditer(linea)]
                + [("objetivo", m.group(1)) for m in OBJETIVO.finditer(linea)]
                + [("herramienta", m.group(1)) for m in HERRAMIENTA.finditer(linea)]
                + [("adr", m.group(1)) for m in CITA_ADR.finditer(linea)]
            )
            for tipo, valor in candidatos:
                if tipo not in tipos or (tipo, valor) in vistas:
                    continue
                vistas.add((tipo, valor))
                salida.append(Referencia(tipo, valor, nombre, n))
    return salida


def _existe_ruta(valor: str) -> bool:
    return (RAIZ / valor.rstrip("/")).exists()


def _existe_modulo(valor: str) -> bool:
    """Importa de verdad y busca el atributo. Un `ImportError` es un «no existe»."""
    modulo, _, atributo = valor.partition(":")
    if not modulo.startswith(("docbench_es", "benchcore")):
        return True
    try:
        return hasattr(importlib.import_module(modulo), atributo)
    except Exception:
        return False


def _objetivos_de_make() -> set[str]:
    texto = (RAIZ / "Makefile").read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r"^([a-z][\w-]*):", texto, re.MULTILINE)}


def _existe_herramienta(valor: str) -> bool:
    return (RAIZ / ".venv" / "bin" / valor).exists()


def _existe_adr(numero: str) -> bool:
    """¿Hay un `docs/adr/NNNN-*.md`? Los 0001 a 0012 están **reservados** a §4.

    Reservados quiere decir que se transcriben cuando llega el hito que los
    implementa, así que citarlos antes es legítimo y no cuenta como roto. Del 0013
    en adelante, una cita sin fichero es una decisión que nadie puede leer.
    """
    if int(numero) <= 12:
        return True
    return any((RAIZ / "docs" / "adr").glob(f"{numero}-*.md"))


def _comprueba(ref: Referencia, objetivos: set[str]) -> bool:
    if ref.tipo == "adr":
        return _existe_adr(ref.valor)
    if ref.tipo == "ruta":
        return _existe_ruta(ref.valor)
    if ref.tipo == "modulo":
        return _existe_modulo(ref.valor)
    if ref.tipo == "objetivo":
        return ref.valor in objetivos
    return _existe_herramienta(ref.valor)


def _make_responde(objetivo: str) -> bool:
    """`make -n`: la comprobación por EJECUCIÓN del objetivo, no por parseo."""
    salida = subprocess.run(
        ["make", "-n", objetivo], cwd=RAIZ, capture_output=True, text=True, check=False
    )
    return "No rule to make target" not in (salida.stderr + salida.stdout)


def analizar(
    fuentes: list[Path] | None = None, declaradas: dict[str, str] | None = None
) -> tuple[list[Referencia], list[Referencia], list[Referencia], list[str]]:
    """(todas, rotas, sin excusa, declaraciones que sobran). **La decisión, sin imprimir.**

    Separado de `main` a propósito: lo que hay que poder probar es el veredicto,
    no el formato. Y hay que poder probarlo **en las dos direcciones** —que dice
    «no» ante una referencia rota y «sí» cuando no hay ninguna—, que es lo que
    separa un candado de un adorno.
    """
    dec = DECLARADAS if declaradas is None else declaradas
    objetivos = _objetivos_de_make()
    referencias = _referencias(fuentes)
    if fuentes is None:
        referencias += _referencias(_fuentes_de_citas(), SOLO_CITAS)
    rotas = [r for r in referencias if not _comprueba(r, objetivos)]
    sin_excusa = [r for r in rotas if r.valor not in dec]
    sobran = [v for v in sorted(dec) if v not in {r.valor for r in rotas}]
    return referencias, rotas, sin_excusa, sobran


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--detalle", action="store_true")
    args = partes.parse_args()

    objetivos = _objetivos_de_make()
    referencias, rotas, sin_excusa, sobran = analizar()
    # Los objetivos se confirman además por ejecución: el parseo del Makefile es
    # la lista, `make -n` es la prueba.
    discrepan = [o for o in sorted(objetivos) if not _make_responde(o)]

    por_tipo = {
        t: sum(1 for r in referencias if r.tipo == t) for t in sorted({r.tipo for r in referencias})
    }

    print(f"{len(referencias)} referencias comprobadas por ejecución · {por_tipo}")
    print(f"  rotas .............. {len(rotas)}")
    print(f"  declaradas con razón {len(rotas) - len(sin_excusa)}")
    print(f"  SIN EXCUSA ......... {len(sin_excusa)}")
    if discrepan:
        print(f"  objetivos de make que el parseo ve y `make -n` no: {discrepan}")
    if sobran:
        print(
            "  DECLARACIONES QUE SOBRAN (o ya existe lo que decían, o nadie las "
            f"referencia): {sobran}"
        )
    if args.detalle:
        for r in sorted(sin_excusa, key=lambda r: (r.fuente, r.linea)):
            print(f"    ROTA  {r.fuente}:{r.linea}  [{r.tipo}] {r.valor}")
        for r in sorted(rotas, key=lambda r: r.valor):
            if r.valor in DECLARADAS:
                print(f"    declarada  {r.valor}  — {DECLARADAS[r.valor]}")
    return 1 if sin_excusa or discrepan or sobran else 0


if __name__ == "__main__":
    sys.exit(main())
