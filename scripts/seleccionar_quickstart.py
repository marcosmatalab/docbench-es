"""**LOS 20 DEL QUICKSTART**, aplicando `runs/l7/seleccion.yaml` sin tocar nada a mano.

    uv run python scripts/seleccionar_quickstart.py            # imprime y emite el json
    uv run python scripts/seleccionar_quickstart.py --congelar # copia los ficheros

## Por qué esto es un programa y no una lista escrita a mano

Porque la regla que gobierna L7 es que **la tasa de acuerdo es SALIDA, nunca objetivo**,
y una lista escrita a mano no se puede distinguir de una lista ajustada. Aquí el criterio
está en un YAML commiteado **antes** que este fichero, el programa lo aplica en un orden
declarado, y el acuerdo se calcula **después** de que el conjunto esté fijado.

**Este módulo no mira `acuerdo` para elegir.** Lo lee sólo para contarlo al final, y eso
se puede comprobar leyéndolo: la única aparición de esa clave fuera del informe está en
el fenómeno `aciertan_los_cuatro`, que es un fenómeno declarado y no una nota.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from fuera_de_git import exige  # noqa: E402
from presupuesto_quickstart import DOCS, por_documento  # noqa: E402

CRITERIO = RAIZ / "runs" / "l7" / "seleccion.yaml"
ELEGIDOS = RAIZ / "runs" / "l7" / "elegidos.json"
FIXTURE = RAIZ / "tests" / "fixtures" / "quickstart"

Doc = dict[str, int | bool]


@dataclass(frozen=True)
class Elegido:
    """Un documento del fixture **con la razón por la que entró**.

    La razón viaja con el documento y no en un comentario aparte porque es lo que hace
    auditable el conjunto: cualquiera puede comprobar que cada plaza la ocupa lo que el
    criterio decía, sin creerse a quien lo corrió.
    """

    id: str
    banda: str
    razon: str
    paginas: int
    bytes: int
    coste_ms: int
    tablas_verdad: int
    celda_combinada: bool
    aciertan: int
    de_mas: int


BANDAS: dict[str, tuple[int, int]] = {"2-10": (2, 10), "11-50": (11, 50), ">50": (51, 10**9)}

FENOMENOS: dict[str, Callable[[Doc], bool]] = {
    "celda_combinada": lambda v: bool(v["celda_combinada"]),
    "aciertan_los_cuatro": lambda v: bool(v["tablas_verdad"]) and v["aciertan"] == 4,
    "discrepan_los_cuatro": lambda v: bool(v["tablas_verdad"]) and v["aciertan"] == 0,
    "sin_tablas": lambda v: not v["tablas_verdad"],
    "tabla_de_mas": lambda v: int(v["de_mas"]) > 0,
}
"""Los cinco de `seleccion.yaml`, en su orden. **El orden es parte del criterio.**"""


def cuotas(d: dict[str, Doc], plazas: int) -> dict[str, int]:
    """El reparto por banda, **método del resto mayor** sobre la población de cada una.

    No es representatividad —con n=20 no está al alcance— es no sobre-representar
    ninguna longitud, que es lo contrario de lo que hace elegir por precio.
    """
    con = {i: v for i, v in d.items() if v["tablas_verdad"] and v["paginas"] > 1}
    poblacion = {
        b: sum(1 for v in con.values() if lo <= int(v["paginas"]) <= hi)
        for b, (lo, hi) in BANDAS.items()
    }
    total = sum(poblacion.values())
    exactas = {b: plazas * n / total for b, n in poblacion.items()}
    reparto = {b: int(q) for b, q in exactas.items()}
    sobran = plazas - sum(reparto.values())
    for b in sorted(exactas, key=lambda b: -(exactas[b] - reparto[b]))[:sobran]:
        reparto[b] += 1
    return reparto


def _elige(candidatos: list[str], d: dict[str, Doc]) -> str:
    """El desempate declarado: **el más ligero**; a igualdad de peso, el `external_id`
    menor. El peso es lo único que entra en el presupuesto de los 3 minutos."""
    return min(candidatos, key=lambda i: (int(d[i]["bytes"]), i))


def seleccionar(d: dict[str, Doc]) -> list[Elegido]:
    """Aplica el criterio. Devuelve los 20 **con la razón por la que entró cada uno**."""
    criterio = yaml.safe_load(CRITERIO.read_text(encoding="utf-8"))
    plazas = int(criterio["reparto"]["plazas"])
    reservadas = criterio["reparto"]["reservadas"]
    reparto = cuotas(d, plazas - sum(reservadas.values()))

    def _en(banda: str) -> Callable[[str], bool]:
        if banda == "sin tablas":
            return lambda i: not d[i]["tablas_verdad"]
        if banda == "una página":
            return lambda i: bool(d[i]["tablas_verdad"]) and d[i]["paginas"] == 1
        lo, hi = BANDAS[banda]
        return lambda i: bool(d[i]["tablas_verdad"]) and lo <= int(d[i]["paginas"]) <= hi

    plan = [("sin tablas", int(reservadas["sin_tablas"]))]
    plan += [(b, reparto[b]) for b in (">50", "11-50", "2-10")]
    plan += [("una página", int(reservadas["una_pagina"]))]

    elegidos: list[Elegido] = []
    ya: set[str] = set()
    pendientes = list(FENOMENOS)
    for banda, cuota in plan:
        dentro = [i for i in sorted(d) if _en(banda)(i) and i not in ya]
        for _ in range(cuota):
            razon, candidatos = f"reparto · banda {banda}", dentro
            for f in list(pendientes):
                hay = [i for i in dentro if i not in ya and FENOMENOS[f](d[i])]
                if hay:
                    razon, candidatos = f"fenómeno · {f}", hay
                    pendientes.remove(f)
                    break
            libres = [i for i in candidatos if i not in ya]
            if not libres:
                continue
            ident = _elige(libres, d)
            ya.add(ident)
            v = d[ident]
            elegidos.append(
                Elegido(
                    id=ident,
                    banda=banda,
                    razon=razon,
                    paginas=int(v["paginas"]),
                    bytes=int(v["bytes"]),
                    coste_ms=int(v["coste_ms"]),
                    tablas_verdad=int(v["tablas_verdad"]),
                    celda_combinada=bool(v["celda_combinada"]),
                    aciertan=int(v["aciertan"]),
                    de_mas=int(v["de_mas"]),
                )
            )
    if pendientes:
        raise RuntimeError(f"fenómenos sin cubrir: {pendientes}. El criterio no se cumple")
    return elegidos


def congelar(elegidos: list[Elegido]) -> None:
    """Copia los PDF y sus XML al fixture. **Sólo la primera vez** (CLAUDE.md)."""
    exige(DOCS)
    FIXTURE.mkdir(parents=True, exist_ok=True)
    for e in elegidos:
        for ext in ("pdf", "xml"):
            destino = FIXTURE / f"{e.id}.{ext}"
            if destino.exists():
                raise FileExistsError(f"{destino.relative_to(RAIZ)} ya existe: está CONGELADO")
            shutil.copyfile(DOCS / f"{e.id}.{ext}", destino)


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--congelar", action="store_true", help="copia los ficheros al fixture")
    args = partes.parse_args()

    d = por_documento()
    elegidos = seleccionar(d)
    peso = sum(e.bytes for e in elegidos)
    coste = sum(e.coste_ms for e in elegidos)
    ELEGIDOS.write_text(
        json.dumps(
            {
                "que": "los 20 de tests/fixtures/quickstart, por runs/l7/seleccion.yaml",
                "criterio": "runs/l7/seleccion.yaml",
                "n": len(elegidos),
                "bytes": peso,
                "coste_de_los_cuatro_ms": coste,
                "documentos": [asdict(e) for e in elegidos],
            },
            indent=1,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        f"\n  {len(elegidos)} documentos · {peso / 1e6:.2f} MB · "
        f"coste de los cuatro {coste / 1000:.1f} s\n"
    )
    for e in elegidos:
        print(
            f"    {e.id} · {e.paginas:>3} pág · {e.bytes / 1000:6.0f} KB"
            f" · {e.coste_ms / 1000:6.1f} s · {e.razon}"
        )
    if args.congelar:
        congelar(elegidos)
        print(f"\n  congelados en {FIXTURE.relative_to(RAIZ)}")
    print(f"\n  escrito {ELEGIDOS.relative_to(RAIZ)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
