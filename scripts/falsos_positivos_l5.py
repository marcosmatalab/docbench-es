"""La tasa de **tabla no presente en la referencia**, que `poblacion.yaml` pre-registró y
nadie publicó.

    uv run python scripts/falsos_positivos_l5.py

## Qué mide, y por qué NO se llama tasa de alucinación

`runs/l5/poblacion.yaml` decidió, antes de la campaña, correr **278** documentos **sin
ninguna tabla en la verdad** —muestra estratificada de los 662— para publicar *«tasa de
falso positivo de DETECCION, con intervalo de Wilson»*. Los 278 se corrieron, entraron en
el denominador del coste y se cobraron su parte de las 2,30 h. **El número no se publicó**,
y tampoco se declaró el hueco: lo encontró el escrutinio adversarial del paso 4 de L5.

El propio pre-registro escribió la salida: *«si no da tiempo a adjudicar, se publica la
tasa cruda LLAMÁNDOLA "tasa de tabla no presente en la referencia" y NO "tasa de
alucinación", y se declara que la separación está sin hacer»*. Eso es lo que hace esto.

**La distinción no es un matiz.** La referencia es el XML del BOE: «cero tablas» significa
cero tablas **en el XML**, no en el documento. Si el maquetador no marcó como `<table>`
algo que en el PDF sí lo es, un extractor que la encuentre **acierta** y aquí cuenta como
positivo. La tasa cruda mezcla alucinación con omisión de la fuente, y separarlas exige
adjudicar contra el PDF (ADR-0039 regla 5). **Eso no está hecho.**

## Los regímenes, que no son el mismo para las tres bandas

`poblacion.yaml` estratificó: `<=10` es **muestra** —200 de 584—, y `11-50` (72) y `>50`
(6) son **censo** de su estrato. Así que la primera lleva intervalo de Wilson y las otras
dos no (ADR-0015). **No se publica una tasa global**: combinar una muestra con dos censos
exige ponderar por los tamaños de estrato, y eso es una decisión de agregación que este
número no necesita para decir lo que dice.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))

from _censo_agregado import wilson  # noqa: E402
from docbench_es.corpus.store import Almacen  # noqa: E402
from docbench_es.entity import boe_xml  # noqa: E402
from docbench_es.extract.diario import Diario  # noqa: E402
from docbench_es.truth.derived import derivar  # noqa: E402

CAMPANA = RAIZ / "runs" / "l5" / "campana"
ESTRATOS = (
    ("<=10", 1, 10, "muestra", 584),
    ("11-50", 11, 50, "censo", 72),
    (">50", 51, 10**9, "censo", 6),
)
"""Nombre, rango de páginas, régimen y población del estrato. Los cuatro campos salen de
`runs/l5/poblacion.yaml`, que los congeló antes de medir."""


def _banda(paginas: int) -> str:
    for nombre, lo, hi, _, _ in ESTRATOS:
        if lo <= paginas <= hi:
            return nombre
    return "(sin páginas)"


def main() -> int:
    almacen = Almacen(RAIZ / "runs/l3/manifiesto.json", RAIZ / "runs/l3/docs")
    sello = json.loads((CAMPANA / "sello.json").read_text(encoding="utf-8"))
    nombres = [str(e["id"]) for e in sello["extractores"]]
    leidos = {n: Diario(CAMPANA / f"{n}.jsonl").leer() for n in nombres}
    paginas = {e.external_id: e.n_pages or 0 for e in almacen.entradas}
    ids = sorted({e.doc_ref.external_id for x in leidos.values() for e in x.extracciones})

    sin_tabla: list[str] = []
    for ident in ids:
        doc = almacen.cargar(ident)
        xml = doc.companions.get("xml")
        if xml is None:
            continue
        d = derivar(doc.ref, boe_xml.tablas(xml.decode("utf-8", errors="replace")))
        if not d.verdad.tables:
            sin_tabla.append(ident)

    fuera: dict[str, object] = {
        "sello_de_la_corrida": sello,
        "documentos_sin_tabla_en_la_verdad": len(sin_tabla),
        "extractores": {},
    }
    print(f"\n  {len(sin_tabla)} documentos SIN ninguna tabla en la verdad, de {len(ids)}\n")
    print(
        f"  {'extractor':<14}{'banda':<8}{'n':>5}{'con tabla':>11}{'tasa':>9}"
        "   regimen · Wilson 95%"
    )
    for nombre, leido in sorted(leidos.items()):
        por_doc: dict[str, int] = {}
        for ex in leido.extracciones:
            por_doc[ex.doc_ref.external_id] = por_doc.get(ex.doc_ref.external_id, 0) + len(
                ex.tables
            )
        de_este: dict[str, object] = {}
        for banda, _, _, regimen, poblacion in ESTRATOS:
            de_la = [d for d in sin_tabla if _banda(paginas.get(d, 0)) == banda]
            if not de_la:
                continue
            con = sum(1 for d in de_la if por_doc.get(d, 0) > 0)
            tablas = sum(por_doc.get(d, 0) for d in de_la)
            ic = wilson(con, len(de_la)) if regimen == "muestra" else None
            de_este[banda] = {
                "n": len(de_la),
                "poblacion_del_estrato": poblacion,
                "regimen": regimen,
                "documentos_con_tabla": con,
                "tablas_devueltas": tablas,
                "tasa": con / len(de_la),
                "wilson95": list(ic) if ic else None,
            }
            cola = (
                f"MUESTRA de {poblacion} · [{100 * ic[0]:.1f}% - {100 * ic[1]:.1f}%]"
                if ic
                else f"CENSO de {poblacion} · sin intervalo (ADR-0015)"
            )
            print(
                f"  {nombre:<14}{banda:<8}{len(de_la):>5}{con:>11}"
                f"{100 * con / len(de_la):>8.1f}%   {cola}"
            )
        fuera["extractores"][nombre] = de_este  # type: ignore[index]
    (RAIZ / "runs" / "l5" / "falsos_positivos.json").write_text(
        json.dumps(fuera, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(
        "\n  NO es una tasa de alucinación y no se llama así: la referencia es el XML, y una\n"
        "  tabla que el maquetador no marcó cuenta aquí aunque el extractor ACIERTE. La\n"
        "  separación exige adjudicar contra el PDF y NO está hecha (ADR-0039 regla 5).\n"
        "  Sin tasa global: combinar una muestra con dos censos exige ponderar por estrato.\n"
        "  Escrito runs/l5/falsos_positivos.json\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
