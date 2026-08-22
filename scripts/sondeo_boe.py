"""Sondeo del BOE: valida la premisa de §1.4 del manual antes de invertir en L3.

USAR Y TIRAR. **No es L3 y no construye nada de L3**: no hay `DocRef`, no hay
adaptador de entidad y nada de `src/` importa esto. Mide cinco cosas sobre una
muestra de documentos reales y estampa sus propias condiciones.

    uv run --with httpx --with pypdf python scripts/sondeo_boe.py \
        --desde 20260803 --hasta 20260821 --n 50 --semilla 20260822 \
        --json /tmp/sondeo/sondeo.json

Cada numero sale con su n y su causa. Lo que falla no entra en la muestra: se cuenta
aparte con su causa del enum cerrado `Causa`. Los numeros van a un fichero de notas
del sondeo, **nunca a `RESULTS.md`**: un sondeo no es una medicion del corpus.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sondeo_lib import (
    Causa,
    Doc,
    clasificar,
    comparar,
    descargar,
    items_con_seccion,
    medir_tablas,
    normalizar,
    recorrer_items,
    texto_de_xml,
)

API_SUMARIO = "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"
URL_LICENCIA = "https://www.boe.es/informacion/aviso_legal/index.php"
AGENTE = "docbench-es-sondeo/0.1 (+https://github.com/marcosmatalab/docbench-es)"


def descubrir(
    cliente: Any,  # noqa: ANN401
    desde: str,
    hasta: str,
    espera: float,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Recorre el rango dia a dia. Devuelve los items y el codigo HTTP de cada sumario.

    Los codigos se devuelven enteros, incluidos los 404 de fines de semana: un dia
    que no se pudo consultar tiene que verse en las notas, no desaparecer.
    """
    d0 = datetime.strptime(desde, "%Y%m%d").replace(tzinfo=UTC).date()
    d1 = datetime.strptime(hasta, "%Y%m%d").replace(tzinfo=UTC).date()
    items: list[dict[str, Any]] = []
    codigos: dict[str, int] = {}
    dia: date = d0
    while dia <= d1:
        clave = dia.strftime("%Y%m%d")
        f = descargar(cliente, API_SUMARIO.format(fecha=clave), True, espera)
        codigos[clave] = f.codigo
        if f.ok:
            try:
                datos = json.loads(f.cuerpo)
            except json.JSONDecodeError:
                codigos[clave] = -1
            else:
                sumario = datos.get("data", {}).get("sumario", {})
                con_sec = items_con_seccion(sumario)
                # Guardian: el recorrido por seccion no puede perder ningun documento
                # respecto al recorrido ciego. Se comparan CONJUNTOS de identificadores,
                # no recuentos, y se excluyen los `BOE-S-*`, que son el sumario del dia
                # y no un documento. Si perdiera alguno, la tasa por seccion iria sesgada.
                ciego = {
                    x["identificador"]
                    for x in recorrer_items(datos.get("data", {}), [])
                    if not x["identificador"].startswith("BOE-S-")
                }
                perdidos = ciego - {x["identificador"] for x in con_sec}
                if perdidos:
                    codigos[clave] = -2
                    print(f"AVISO {clave}: el recorrido por seccion pierde {len(perdidos)}")
                for it in con_sec:
                    it["_fecha"] = clave
                    items.append(it)
        dia += timedelta(days=1)
    return items, codigos


def procesar(cliente: Any, it: dict[str, Any], espera: float, cache: Path) -> Doc:  # noqa: ANN401
    """Un documento: descarga, mide y clasifica. Cualquier fallo lo saca de la muestra."""
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    doc = Doc(ident=it["identificador"], fecha=it["_fecha"], seccion=str(it.get("_seccion", "?")))
    doc.url_xml = it.get("url_xml", "")
    pdf = it.get("url_pdf") or {}
    doc.url_pdf = pdf.get("texto", "") if isinstance(pdf, dict) else ""
    if not doc.url_xml:
        doc.fallo = Causa.SIN_URL_XML
        return doc
    if not doc.url_pdf:
        doc.fallo = Causa.SIN_URL_PDF
        return doc

    fx = descargar(cliente, doc.url_xml, True, espera)
    doc.http_xml = fx.codigo
    if not fx.ok:
        doc.fallo = fx.causa
        return doc
    crudo = fx.cuerpo.decode("utf-8", errors="replace")
    if "<documento" not in crudo:
        doc.fallo = Causa.XML_MAL_FORMADO
        return doc
    medir_tablas(crudo, doc)
    t_xml = normalizar(texto_de_xml(crudo), quitar_ruido=False)
    doc.tokens_xml = len(t_xml)
    if doc.tokens_xml < 20:
        doc.fallo = Causa.XML_SIN_TEXTO
        return doc

    fp = descargar(cliente, doc.url_pdf, False, espera)
    doc.http_pdf = fp.codigo
    if not fp.ok:
        doc.fallo = fp.causa
        return doc
    ruta = cache / f"{doc.ident}.pdf"
    ruta.write_bytes(fp.cuerpo)
    try:
        lector = PdfReader(str(ruta))
        doc.paginas = len(lector.pages)
        bruto = "\n".join(p.extract_text() or "" for p in lector.pages)
    except (PyPdfError, ValueError, KeyError, OSError, RecursionError):
        doc.fallo = Causa.PDF_ILEGIBLE
        return doc
    t_pdf = normalizar(bruto, quitar_ruido=True)
    doc.tokens_pdf = len(t_pdf)
    if doc.tokens_pdf < 20:
        doc.fallo = Causa.PDF_SIN_CAPA_TEXTO
        return doc

    doc.similitud, doc.contencion = comparar(t_xml, t_pdf)
    doc.estrato = clasificar(doc)
    return doc


def _cmd(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {"cmd": " ".join(cmd), "rc": p.returncode, "out": p.stdout.strip()[:200]}


def condiciones(args: argparse.Namespace) -> dict[str, Any]:
    """Lo que el sondeo estampa de si mismo.

    Una condicion no declarada es un numero equivocado esperando a que alguien lo
    mida. Va el rango, la semilla, las versiones y el codigo de salida de todo lo
    que se ejecuta, incluido si el arbol estaba limpio.
    """
    import httpx
    import pypdf

    return {
        "ejecutado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "rango": {"desde": args.desde, "hasta": args.hasta},
        "n_pedido": args.n,
        "semilla": args.semilla,
        "espera_s": args.espera,
        "python": sys.version.split()[0],
        "httpx": httpx.__version__,
        "pypdf": pypdf.__version__,
        "plataforma": platform.platform(),
        "git_head": _cmd(["git", "rev-parse", "--short", "HEAD"]),
        "git_porcelain": _cmd(["git", "status", "--porcelain"]),
    }


def licencia(cliente: Any, espera: float) -> dict[str, Any]:  # noqa: ANN401
    """Lee de primera mano las condiciones de reutilizacion. No se fia del manual."""
    f = descargar(cliente, URL_LICENCIA, False, espera)
    if not f.ok:
        return {"url": URL_LICENCIA, "http": f.codigo, "leido": False}
    txt = texto_de_xml(f.cuerpo.decode("utf-8", errors="replace")).lower()
    # Los terminos son los del texto legal, no los del manual. El manual dice
    # "copiar, reproducir, distribuir y difundir"; la licencia lo escribe en
    # sustantivos —"la copia, reproduccion, distribucion y difusion publica"— y la
    # atribucion la llama "citarse la fuente". Buscar los infinitivos daba cuatro
    # falsos negativos: un chequeo mal formulado es peor que no tenerlo.
    terminos = [
        "condiciones de reutilizaci",
        "la copia",
        "reproducci",
        "distribuci",
        "difusi",
        "fines comerciales",
        "citarse la fuente",
        "cesi",
        "gratuita",
    ]
    return {
        "url": URL_LICENCIA,
        "http": f.codigo,
        "leido": True,
        "leido_el": datetime.now(UTC).date().isoformat(),
        "terminos_presentes": {t: (t in txt) for t in terminos},
        "bytes": len(f.cuerpo),
    }


def main() -> int:
    import httpx

    p = argparse.ArgumentParser(description="Sondeo del BOE. Usar y tirar.")
    p.add_argument("--desde", required=True)
    p.add_argument("--hasta", required=True)
    p.add_argument("--n", type=int, default=50)
    p.add_argument("--semilla", type=int, default=20260822)
    p.add_argument("--espera", type=float, default=0.25)
    p.add_argument("--secciones", default="", help="codigos separados por coma; vacio = todas")
    p.add_argument("--cache", type=Path, default=Path("/tmp/sondeo_boe"))
    p.add_argument("--json", type=Path, required=True)
    p.add_argument("--solo-licencia", action="store_true", help="solo el punto 5, sin muestra")
    args = p.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.json.parent.mkdir(parents=True, exist_ok=True)

    cond = condiciones(args)
    if args.solo_licencia:
        with httpx.Client(headers={"User-Agent": AGENTE}) as cli:
            lic = licencia(cli, args.espera)
        args.json.write_text(
            json.dumps({"condiciones": cond, "licencia": lic}, indent=1, ensure_ascii=False),
            encoding="utf-8",
        )
        faltan = [t for t, v in lic.get("terminos_presentes", {}).items() if not v]
        print(f"licencia http={lic['http']} leido={lic['leido']} terminos_ausentes={faltan}")
        return 0 if lic["leido"] and not faltan else 1

    with httpx.Client(headers={"User-Agent": AGENTE, "Accept": "application/json"}) as cli:
        items, codigos = descubrir(cli, args.desde, args.hasta, args.espera)
        vistos: dict[str, dict[str, Any]] = {}
        for it in items:
            vistos.setdefault(it["identificador"], it)
        universo = sorted(vistos.values(), key=lambda x: x["identificador"])
        if args.secciones:
            filtro = {s.strip() for s in args.secciones.split(",")}
            universo = [x for x in universo if x.get("_seccion") in filtro]
        muestra = random.Random(args.semilla).sample(universo, min(args.n, len(universo)))
        muestra.sort(key=lambda x: x["identificador"])
        docs = [procesar(cli, it, args.espera, args.cache) for it in muestra]
        lic = licencia(cli, args.espera)

    salida = {
        "condiciones": cond,
        "descubrimiento": {
            "codigos_sumario": codigos,
            "universo": len(universo),
            "secciones_filtro": args.secciones or "todas",
            "universo_por_seccion": dict(Counter(str(x.get("_seccion")) for x in universo)),
        },
        "licencia": lic,
        "documentos": [asdict(d) for d in docs],
    }
    args.json.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    ok = [d for d in docs if d.fallo is None]
    print(f"universo={len(universo)} muestra={len(docs)} emparejados={len(ok)}")
    print(f"causas={dict(Counter(d.fallo for d in docs if d.fallo))}")
    print(f"json={args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
