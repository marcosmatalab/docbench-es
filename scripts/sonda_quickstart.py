"""**EL RELOJ DE VERDAD DEL QUICKSTART**, y si los cuatro corren SIN RED.

    uv run python scripts/sonda_quickstart.py                 # el reloj, 20 documentos
    uv run python scripts/sonda_quickstart.py --sin-red       # un documento, cache vacía

## Por qué no basta con sumar las latencias de la campaña

Los `latency_ms` de `runs/l5/campana` se midieron en un Ryzen 9950X3D **con 32
trabajadores en paralelo** y con los modelos ya en la caché. El quickstart corre
**secuencial**, en la máquina de cualquiera y desde un clon. Sumar aquellas latencias da
una predicción; esto la comprueba, y la primera vez que se comprobó salió **un 25% por
encima** de la suma.

## Y la segunda pregunta es la que decide el hito

El criterio de L7 dice **SIN RED**. `docling` carga pesos de HuggingFace: con la caché
vacía y sin red **falla** —limpiamente, con su causa del enum cerrado, que es lo que la
regla de oro 6 exige—, y esos pesos son **medio giga** que este repo no versiona ni puede
versionar contra unos 4 MB de fixtures. Los otros tres corren.

**Eso no se arregla eligiendo mejor los 20**, así que va medido antes de elegirlos.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from fuera_de_git import exige  # noqa: E402
from presupuesto_quickstart import CUANTOS, por_documento  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"
MANIFIESTO = RAIZ / "runs" / "l3" / "manifiesto.json"
RELOJ = RAIZ / "runs" / "l7" / "reloj_sonda.json"


def _extractores() -> dict[str, object]:
    """Los cuatro, en orden de coste creciente **medido**, no supuesto."""
    from docbench_es.extract.camelot import CamelotExtractor
    from docbench_es.extract.docling import DoclingExtractor
    from docbench_es.extract.pdfplumber import PdfplumberExtractor
    from docbench_es.extract.pymupdf4llm import Pymupdf4llmExtractor

    return {
        "pdfplumber": PdfplumberExtractor(),
        "camelot": CamelotExtractor(),
        "pymupdf4llm": Pymupdf4llmExtractor(),
        "docling": DoclingExtractor(),
    }


ELEGIDOS = RAIZ / "runs" / "l7" / "elegidos.json"


def _conjunto() -> tuple[list[str], str]:
    """Los 20 que el criterio eligió, o un conjunto **provisional** si aún no existen.

    El provisional sirve sólo para cronometrar; se dice cuál de los dos es, porque un
    reloj medido sobre otro conjunto no es el reloj del quickstart.
    """
    if ELEGIDOS.is_file():
        datos = json.loads(ELEGIDOS.read_text(encoding="utf-8"))
        return [str(e["id"]) for e in datos["documentos"]], "runs/l7/elegidos.json"
    d = por_documento()
    con = {i: v for i, v in d.items() if v["tablas_verdad"]}
    objetivo = sum(bool(v["acuerdo"]) for v in con.values()) / len(con)
    si = sorted((i for i in con if con[i]["acuerdo"]), key=lambda i: int(con[i]["bytes"]))
    no = sorted((i for i in con if not con[i]["acuerdo"]), key=lambda i: int(con[i]["bytes"]))
    k = min(range(CUANTOS + 1), key=lambda k: abs(k / CUANTOS - objetivo))
    return si[:k] + no[: CUANTOS - k], "PROVISIONAL, no el fixture"


def reloj() -> dict[str, object]:
    """De arrancar el proceso a la tabla, **secuencial y cronometrado por partes**."""
    from docbench_es.corpus.store import Almacen
    from docbench_es.entity import boe_xml
    from docbench_es.report.cara_a_cara import cara_a_cara
    from docbench_es.report.nivel1 import medir
    from docbench_es.truth.derived import derivar

    exige(DOCS)
    arranque = time.perf_counter()
    ids, procedencia = _conjunto()
    almacen = Almacen(MANIFIESTO, DOCS)
    docs = [almacen.cargar(i) for i in ids]
    carga = time.perf_counter() - arranque

    extracciones: dict[str, list[object]] = {}
    por_extractor: dict[str, float] = {}
    for nombre, e in _extractores().items():
        t = time.perf_counter()
        extracciones[nombre] = [e.extract(doc) for doc in docs]  # type: ignore[attr-defined]
        por_extractor[nombre] = round(time.perf_counter() - t, 2)

    t = time.perf_counter()
    verdades = {}
    for doc in docs:
        xml = doc.companions["xml"]
        v = derivar(doc.ref, boe_xml.tablas(xml.decode("utf-8", errors="replace")))
        if v.verdad.tables:
            verdades[doc.ref.external_id] = v.verdad.tables
    paginas = {e.external_id: e.n_pages or 0 for e in almacen.entradas if e.external_id in set(ids)}
    filas = {n: medir(x, verdades, paginas) for n, x in extracciones.items()}  # type: ignore[arg-type]
    cc = cara_a_cara(filas, paginas)
    medida = round(time.perf_counter() - t, 2)

    return {
        "que": "sonda de reloj del quickstart, secuencial y en frío",
        "conjunto": procedencia,
        "documentos": len(ids),
        "cargar_del_almacen_s": round(carga, 2),
        "por_extractor_s": por_extractor,
        "verdad_teds_cara_a_cara_s": medida,
        "total_s": round(sum(por_extractor.values()) + carga + medida, 2),
        "sin_docling_s": round(
            sum(v for n, v in por_extractor.items() if n != "docling") + carga + medida, 2
        ),
        "presupuesto_s": 180,
        "acuerdo_del_conjunto_provisional": f"{cc.n_acuerdo} de {len(verdades)}",
        "puntuan_todos": cc.n,
    }


def sin_red() -> dict[str, object]:
    """¿Corre cada extractor con la caché de modelos vacía? **Un documento, los cuatro.**

    Se ejecuta con `HF_HOME` en un directorio vacío y `HF_HUB_OFFLINE=1`, que es lo que
    ve un clon frío sin red. Lo que se mira no es el tiempo: es **quién falla**.
    """
    from docbench_es.corpus.store import Almacen

    exige(DOCS)
    doc = Almacen(MANIFIESTO, DOCS).cargar(sorted(por_documento())[0])
    fuera: dict[str, object] = {"documento": doc.ref.external_id}
    for nombre, e in _extractores().items():
        ex = e.extract(doc)  # type: ignore[attr-defined]
        fuera[nombre] = (
            f"FALLA: {ex.failure_reason}" if ex.failed else f"OK · {len(ex.tables)} tablas"
        )
    return fuera


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--sin-red", action="store_true", help="caché vacía: quién falla")
    args = partes.parse_args()

    salida = sin_red() if args.sin_red else reloj()
    RELOJ.parent.mkdir(parents=True, exist_ok=True)
    anterior = json.loads(RELOJ.read_text(encoding="utf-8")) if RELOJ.is_file() else {}
    anterior["sin_red" if args.sin_red else "reloj"] = salida
    RELOJ.write_text(json.dumps(anterior, indent=1, ensure_ascii=False), encoding="utf-8")
    print()
    for clave, valor in salida.items():
        print(f"  {clave}: {valor}")
    print(f"\n  escrito {RELOJ.relative_to(RAIZ)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
