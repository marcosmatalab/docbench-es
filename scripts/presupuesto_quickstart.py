"""**LO QUE HAY QUE DECIDIR ANTES DE CONGELAR LOS 20 DE L7**, con los datos de L5.

    uv run python scripts/presupuesto_quickstart.py --regenerar   # necesita el corpus
    uv run python scripts/presupuesto_quickstart.py               # lee el artefacto

## Las dos preguntas, y ninguna es opcional

L7 pide **20 documentos, ~4 MB, cuatro extractores, menos de 3 minutos, sin red**. Esas
cuatro cifras juntas **eligen los documentos**, y elegirlos por precio es elegir cortos.

1. **¿Caben 20?** No con la mediana global: el reloj es una **suma**, y la suma de una
   distribución con cola a la derecha la gobierna la **media**, no la mediana. La mediana
   del coste de los cuatro por documento con tabla son 8,8 s; la media, **17,1**.
2. **¿Cuánto halaga el conjunto que sí cabe?** El acuerdo del corpus es **103 de 338**.
   El de los 20 más ligeros, **14 de 20**. Publicar el segundo sin el primero al lado, en
   la primera herramienta que ejecuta cualquiera, es el sesgo del que avisó ADR-0042.

## Lo que este script NO hace

**No elige los 20 ni los congela.** Emite los números con los que se decide, y el
criterio de selección se escribe **antes** de mirar cuál sale mejor. Elegir el conjunto
para que su acuerdo cuadre con el del corpus sería exactamente la trampa que la regla de
oro del repo prohíbe: el conjunto se elige por **cobertura de fenómenos**, se mide
después, y sale publicado el número que salga.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from fuera_de_git import exige  # noqa: E402

CAMPANA = RAIZ / "runs" / "l5" / "campana"
DOCS = RAIZ / "runs" / "l3" / "docs"
MANIFIESTO = RAIZ / "runs" / "l3" / "manifiesto.json"
POR_DOCUMENTO = RAIZ / "runs" / "l7" / "por_documento.json"
PRESUPUESTO = RAIZ / "runs" / "l7" / "presupuesto.json"
EXTRACTORES = ("camelot", "docling", "pdfplumber", "pymupdf4llm")

PRESUPUESTO_MS = 180_000
"""Los 3 minutos de `HITOS.md`. **Es el criterio, no una elección de este script.**"""
PRESUPUESTO_BYTES = 4_000_000
"""Los «unos 4 MB» de `HITOS.md`, que resultan ser la restricción que aprieta."""
CUANTOS = 20


@dataclass(frozen=True)
class Analisis:
    """Lo que se publica. Un `dict[str, object]` se lee igual y no lo comprueba nadie."""

    poblacion: dict[str, float]
    coste_de_los_cuatro_ms: dict[str, int]
    peso_pdf_mas_xml_bytes: dict[str, int]
    presupuestos: dict[str, int]
    candidatos_por_precio: dict[str, dict[str, float]]
    frontera_de_viabilidad: list[dict[str, float]]


def regenerar() -> dict[str, dict[str, int | bool]]:
    """Deriva la verdad de los 616 y emite el **por documento**. Necesita el corpus.

    Se emite un artefacto en vez de recalcular en cada análisis por la misma razón que
    `censo_tablas.publicado()`: el consumidor no puede depender de 350 MB que no están en
    git, o degrada en silencio en un clon frío (LIMITS 118).
    """
    from docbench_es.corpus.store import Almacen
    from docbench_es.entity import boe_xml
    from docbench_es.extract.diario import Diario
    from docbench_es.report.cara_a_cara import cara_a_cara
    from docbench_es.report.nivel1 import medir
    from docbench_es.truth.derived import derivar

    exige(DOCS)
    exige(CAMPANA)
    almacen = Almacen(MANIFIESTO, DOCS)
    leidos = {n: Diario(CAMPANA / f"{n}.jsonl").leer() for n in EXTRACTORES}
    ids = sorted({e.doc_ref.external_id for x in leidos.values() for e in x.extracciones})
    verdades = {}
    for ident in ids:
        doc = almacen.cargar(ident)
        xml = doc.companions.get("xml")
        if xml is None:
            continue
        d = derivar(doc.ref, boe_xml.tablas(xml.decode("utf-8", errors="replace")))
        if d.verdad.tables:
            verdades[ident] = d.verdad.tables
    paginas = {e.external_id: e.n_pages or 0 for e in almacen.entradas}
    filas = {n: medir(x.extracciones, verdades, paginas) for n, x in leidos.items()}
    cc = cara_a_cara(filas, paginas)
    acuerdo, puntuan = set(cc.acuerdo_de_recuento), set(cc.documentos)

    coste: dict[str, int] = {}
    cuantas: dict[str, dict[str, int]] = {}
    for nombre in EXTRACTORES:
        for linea in (CAMPANA / f"{nombre}.jsonl").read_text(encoding="utf-8").splitlines():
            e = json.loads(linea)
            i = e["doc_ref"]["external_id"]
            coste[i] = coste.get(i, 0) + int(e["latency_ms"])
            cuantas.setdefault(i, {})[nombre] = len(e["tables"])

    def _combinada(ident: str) -> bool:
        """¿Trae la verdad alguna celda que ocupe más de una fila o columna?

        Es el fenómeno que dispara la regla de oro 4 —y con ella el `NO_APLICABLE`—,
        o sea el mecanismo que separa los 103 que aciertan el recuento de los 82 que
        puntúan. Un quickstart sin ninguno no enseña ese mecanismo.
        """
        return any(
            c.rowspan > 1 or c.colspan > 1 for tab in verdades.get(ident, ()) for c in tab.cells
        )

    fuera = {
        i: {
            "paginas": paginas.get(i, 0),
            "tablas_verdad": len(verdades.get(i, ())),
            "coste_ms": coste[i],
            "bytes": (DOCS / f"{i}.pdf").stat().st_size + (DOCS / f"{i}.xml").stat().st_size,
            "acuerdo": i in acuerdo,
            "puntua": i in puntuan,
            "celda_combinada": _combinada(i),
            # Cuántos de los cuatro clavan el recuento, y cuántos sacan MÁS tablas de
            # las que hay. El segundo es un fenómeno por sí mismo —una tabla que no
            # está en la referencia— y no se ve en el acuerdo, que sólo dice sí o no.
            "aciertan": sum(n == len(verdades.get(i, ())) for n in cuantas[i].values()),
            "de_mas": sum(n > len(verdades.get(i, ())) for n in cuantas[i].values()),
        }
        for i in sorted(coste)
    }
    POR_DOCUMENTO.parent.mkdir(parents=True, exist_ok=True)
    POR_DOCUMENTO.write_text(json.dumps(fuera, indent=1), encoding="utf-8")
    return fuera


def por_documento() -> dict[str, dict[str, int | bool]]:
    """El artefacto versionado. **Lanza si no está**, en vez de devolver `{}`."""
    if not POR_DOCUMENTO.is_file():
        raise FileNotFoundError(
            f"falta {POR_DOCUMENTO.relative_to(RAIZ)}. Regenéralo con el corpus delante:"
            " uv run python scripts/presupuesto_quickstart.py --regenerar"
        )
    datos: dict[str, dict[str, int | bool]] = json.loads(POR_DOCUMENTO.read_text(encoding="utf-8"))
    return datos


def _n(d: dict[str, dict[str, int | bool]], ids: list[str], campo: str) -> list[int]:
    return [int(d[i][campo]) for i in ids]


def conjunto(d: dict[str, dict[str, int | bool]], ids: list[str]) -> dict[str, float]:
    """Coste, peso y acuerdo de un conjunto candidato. **La cuenta de (b), sin elegir.**"""
    acuerdan = sum(bool(d[i]["acuerdo"]) for i in ids)
    return {
        "n": len(ids),
        "coste_s": round(sum(_n(d, ids, "coste_ms")) / 1000, 1),
        "mb": round(sum(_n(d, ids, "bytes")) / 1e6, 2),
        "acuerdan": acuerdan,
        "acuerdo": round(acuerdan / len(ids), 4) if ids else 0.0,
        "paginas_min": min(_n(d, ids, "paginas"), default=0),
        "paginas_max": max(_n(d, ids, "paginas"), default=0),
    }


def frontera(d: dict[str, dict[str, int | bool]], cuantos: int = CUANTOS) -> list[dict[str, float]]:
    """**El precio de NO halagar**: los más ligeros de cada lado, con k de acuerdo.

    Es una cuenta de **viabilidad**, no una propuesta de conjunto: contesta *«¿existe un
    conjunto de 20 que quepa y cuyo acuerdo no esté inflado?»*, que es la pregunta que hay
    que responder antes de escribir el criterio, no después.
    """
    con = [i for i in d if d[i]["tablas_verdad"]]
    si = sorted((i for i in con if d[i]["acuerdo"]), key=lambda i: int(d[i]["bytes"]))
    no = sorted((i for i in con if not d[i]["acuerdo"]), key=lambda i: int(d[i]["bytes"]))
    salida = []
    for k in range(cuantos + 1):
        if k > len(si) or cuantos - k > len(no):
            continue
        salida.append(conjunto(d, si[:k] + no[: cuantos - k]))
    return salida


def analisis(d: dict[str, dict[str, int | bool]]) -> Analisis:
    """Todo lo que se publica, en una estructura tipada.

    **Ni una cifra tecleada en la prosa**, y `main` imprime de aquí en vez de indexar
    un `dict[str, object]`: un diccionario suelto se lee igual pero `mypy --strict` no
    puede comprobar ni una de las claves, que es medio guardián menos.
    """
    ids = sorted(i for i in d if d[i]["tablas_verdad"])
    costes = sorted(_n(d, ids, "coste_ms"))
    pesos = sorted(_n(d, ids, "bytes"))
    baratos = sorted(ids, key=lambda i: int(d[i]["coste_ms"]))[:CUANTOS]
    ligeros = sorted(ids, key=lambda i: int(d[i]["bytes"]))[:CUANTOS]
    cortos = sorted(ids, key=lambda i: int(d[i]["paginas"]))[:CUANTOS]
    una = [i for i in ids if d[i]["paginas"] == 1]
    return Analisis(
        poblacion=conjunto(d, ids),
        coste_de_los_cuatro_ms={
            "mediana": int(statistics.median(costes)),
            "media": int(statistics.mean(costes)),
            "p90": costes[int(0.9 * len(costes))],
            "maximo": costes[-1],
            "por_20_con_la_mediana": int(statistics.median(costes)) * CUANTOS,
            "por_20_con_la_media": int(statistics.mean(costes)) * CUANTOS,
        },
        peso_pdf_mas_xml_bytes={
            "mediana": pesos[len(pesos) // 2],
            "media": int(statistics.mean(pesos)),
            "los_20_mas_ligeros": sum(pesos[:CUANTOS]),
            "por_20_con_la_media": int(statistics.mean(pesos)) * CUANTOS,
        },
        presupuestos={"ms": PRESUPUESTO_MS, "bytes": PRESUPUESTO_BYTES, "cuantos": CUANTOS},
        candidatos_por_precio={
            "los_20_mas_baratos": conjunto(d, baratos),
            "los_20_mas_ligeros": conjunto(d, ligeros),
            "los_20_mas_cortos": conjunto(d, cortos),
            "los_de_una_pagina": conjunto(d, una),
        },
        frontera_de_viabilidad=frontera(d),
    )


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument(
        "--regenerar", action="store_true", help="re-deriva la verdad; necesita corpus"
    )
    args = partes.parse_args()

    datos = regenerar() if args.regenerar else por_documento()
    salida = analisis(datos)
    PRESUPUESTO.parent.mkdir(parents=True, exist_ok=True)
    PRESUPUESTO.write_text(
        json.dumps(asdict(salida), indent=1, ensure_ascii=False), encoding="utf-8"
    )

    p, c, w = salida.poblacion, salida.coste_de_los_cuatro_ms, salida.peso_pdf_mas_xml_bytes
    print(
        f"\n  población: {p['n']} documentos con tabla · acuerdo {p['acuerdan']}"
        f" = {100 * p['acuerdo']:.1f}%"
    )
    print(
        f"  coste de los CUATRO por documento: mediana {c['mediana']} ms · media {c['media']} ms"
        f" · p90 {c['p90']} · máximo {c['maximo']}"
    )
    print(
        f"    x20 con la mediana {c['por_20_con_la_mediana'] / 1000:.0f} s · "
        f"con la MEDIA {c['por_20_con_la_media'] / 1000:.0f} s · "
        f"presupuesto {PRESUPUESTO_MS / 1000:.0f} s"
    )
    print(
        f"  peso pdf+xml: mediana {w['mediana'] / 1000:.0f} KB · los 20 más ligeros"
        f" {w['los_20_mas_ligeros'] / 1e6:.2f} MB · presupuesto {PRESUPUESTO_BYTES / 1e6:.0f} MB"
    )
    print("\n  ELEGIDOS POR PRECIO — y el acuerdo del corpus es %.1f%%:" % (100 * p["acuerdo"]))
    for nombre, v in salida.candidatos_por_precio.items():
        print(
            f"    {nombre:<22} n={v['n']:>2} · {v['coste_s']:6.1f} s · {v['mb']:5.2f} MB ·"
            f" acuerdo {v['acuerdan']}/{v['n']} = {100 * v['acuerdo']:5.1f}%"
            f" · páginas {v['paginas_min']}-{v['paginas_max']}"
        )
    print("\n  VIABILIDAD — 20 documentos con k de acuerdo, los más ligeros de cada lado:")
    for v in salida.frontera_de_viabilidad:
        if v["acuerdan"] in (0, 4, 5, 6, 7, 8, 14, 20):
            print(
                f"    {v['acuerdan']:>2}/20 = {100 * v['acuerdo']:5.1f}% ·"
                f" {v['coste_s']:6.1f} s · {v['mb']:5.2f} MB ·"
                f" páginas {v['paginas_min']}-{v['paginas_max']}"
            )
    print(f"\n  escrito {PRESUPUESTO.relative_to(RAIZ)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
