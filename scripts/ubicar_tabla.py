"""En qué PÁGINA del PDF está una tabla de la selección de L4.

**Para qué, y por qué no es hacer trampa.** Las tablas se transcriben del PDF y no
del XML —del XML sería comparar el XML consigo mismo—, pero encontrar «la tabla
número 12» de un PDF de 175 páginas a ojo cuesta más que transcribirla. Esto usa el
XML **como índice**, no como fuente: saca un texto de anclaje de la tabla y busca en
qué página del PDF aparece.

**La distinción importa y va declarada:** el XML dice DÓNDE mirar; los valores se
leen del PDF. La circularidad estaría en tomar los valores del XML, no en usarlo
para pasar página.

**Y la desambiguación va POR ESTRUCTURA, nunca por contenido.** Cuando la página
trae varias tablas hay que saber cuál es la buscada, y mirar el TEXTO del XML para
decidirlo **contamina la transcripción**: quien ya ha visto los valores no los
transcribe ciego, y su coincidencia no prueba nada. Por eso se publica la
**dimensión** y **cuál es de las de su dimensión** —estructura, no valores—, que
basta para elegirla en la página. Salió transcribiendo `BOE-A-2026-5979` t15, donde
sí se miró el contenido: ese fixture queda marcado como contaminado.

    uv run python scripts/ubicar_tabla.py BOE-A-2026-5511 0
    uv run python scripts/ubicar_tabla.py --todas
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from docbench_es.entity import boe_xml  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"


def _anclas(xml: str, indice: int) -> list[str]:
    """Textos de celda largos y raros de esa tabla. Los mejores para buscar."""
    tablas = boe_xml.tablas(xml)
    t = tablas[indice]
    textos = [c.text.strip() for c in t.cells if len(c.text.strip()) >= 12]
    # De más raro a menos: los que aparecen una sola vez en el documento entero.
    plano = boe_xml.texto_plano(xml)
    unicos = [x for x in textos if plano.count(x) == 1]
    return (unicos or textos)[:6]


def _paginas(pdf: Path) -> list[str]:
    from pypdf import PdfReader

    return [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]


def ubicar(ident: str, indice: int) -> dict[str, object]:
    xml = (DOCS / f"{ident}.xml").read_text(encoding="utf-8", errors="replace")
    tablas = boe_xml.tablas(xml)
    t = tablas[indice]
    anclas = _anclas(xml, indice)
    paginas = _paginas(DOCS / f"{ident}.pdf")
    encontradas: list[int] = []
    for i, texto in enumerate(paginas, 1):
        limpio = re.sub(r"\s+", " ", texto)
        if any(re.sub(r"\s+", " ", a) in limpio for a in anclas):
            encontradas.append(i)
    # DESAMBIGUACION POR ESTRUCTURA, NUNCA POR CONTENIDO. Cuando hay varias tablas
    # en la pagina, hay que saber cual es. Mirar el TEXTO del XML para decidirlo
    # contamina la transcripcion: quien ya ha visto los valores no los transcribe
    # ciego. La dimension y el ORDEN son estructura, no valores, y bastan.
    misma_dimension = [
        i for i, o in enumerate(tablas) if (o.n_rows, o.n_cols) == (t.n_rows, t.n_cols)
    ]
    return {
        "external_id": ident,
        "tabla": indice,
        "dimension_xml": f"{t.n_rows}x{t.n_cols}",
        "tablas_del_documento": len(tablas),
        "es_la_n_esima_de_su_dimension": misma_dimension.index(indice) + 1,
        "cuantas_hay_de_su_dimension": len(misma_dimension),
        "celdas": len(t.cells),
        "paginas_pdf": len(paginas),
        "paginas_con_la_tabla": encontradas,
        "anclas": anclas[:3],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ident", nargs="?")
    p.add_argument("indice", nargs="?", type=int)
    p.add_argument("--todas", action="store_true")
    args = p.parse_args()

    if args.todas:
        sel = json.loads((RAIZ / "runs" / "l4" / "seleccion.json").read_text(encoding="utf-8"))[
            "seleccion"
        ]
        for d in sel:
            r = ubicar(str(d["external_id"]), int(d["tabla"]))
            pgs = r["paginas_con_la_tabla"]
            print(
                f"{r['external_id']} t{r['tabla']:<3} {r['dimension_xml']:>8} "
                f"{r['celdas']:>5} celdas · pdf {r['paginas_pdf']:>3} pág · "
                f"tabla en {pgs if pgs else 'NO LOCALIZADA'}"
            )
        return 0

    if not args.ident or args.indice is None:
        p.error("ident e indice, o --todas")
    print(json.dumps(ubicar(args.ident, args.indice), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
