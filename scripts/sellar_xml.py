"""El `sha256` de cada XML del corpus, capturado HOY. **Sin tocar el esquema.**

El manifiesto pone hash al PDF y no al XML (límite 62), y el XML es *la verdad de
referencia*: la mitad menos protegida del par es la que decide quién gana. Meter
el campo dentro de `Procedencia` toca el esquema, `corpus.harvest` y la
reanudación, y eso es L4.

**Pero capturar el hash y cambiar el esquema son dos cosas distintas, y sólo una
corre prisa.** Lo que separa una captura buena de una mala es **el hueco entre la
descarga y el hash**: hecha al terminar la cosecha son minutos, sobre ficheros que
acaba de escribir este mismo código en esta misma máquina. Hecha en L4 son días, y
**un hash calculado sobre un fichero ya sustituido lo bendice para siempre** —
sería peor que no tenerlo, porque a partir de ahí la comprobación diría que todo
cuadra.

Así que esto no espera a L4. Escribe un fichero aparte, con **cuándo se tomó y
sobre qué commit**, y en L4 ese fichero **se pliega dentro del esquema en vez de
recalcularse**. Si en L4 se recalcula, el hueco vuelve a ser de días y esta
captura no habrá servido de nada.

    uv run python scripts/sellar_xml.py runs/l3/manifiesto.json

**Por eso se niega a sobrescribir.** Volver a correrlo sobre un corpus viejo es
exactamente el error que existe para evitar, y un fichero de sellos que se puede
regenerar en cualquier momento no es evidencia de nada. Para refijar a propósito,
`--refijar` con su razón, que queda escrita dentro.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from sello import sello  # noqa: E402

ESQUEMA = "docbench-es.sellos-xml/1"


def capturar(manifiesto: dict[str, object], docs: Path) -> dict[str, object]:
    """Recorre los documentos del manifiesto y hashea su XML. **En este orden.**

    Se recorre el manifiesto y no el directorio a propósito: lo que hay que sellar
    es *el corpus publicado*, no *lo que haya en la carpeta*. Un XML suelto que no
    esté en el manifiesto no es parte del corpus, y sellarlo daría una cuenta que
    no cuadra con ninguna otra del hito.

    Un XML que falta **no se salta en silencio**: sale en `faltan` y el comando
    devuelve 1. Una captura incompleta que se presenta como completa es la misma
    familia de fallo que un manifiesto sin sus bytes.
    """
    documentos = manifiesto.get("documentos")
    filas = [d for d in documentos if isinstance(d, dict)] if isinstance(documentos, list) else []
    sellos: dict[str, object] = {}
    faltan: list[str] = []
    for fila in filas:
        ident = fila.get("external_id")
        if not isinstance(ident, str):
            continue
        xml = docs / f"{ident}.xml"
        if not xml.is_file():
            faltan.append(ident)
            continue
        crudo = xml.read_bytes()
        sellos[ident] = {"sha256": hashlib.sha256(crudo).hexdigest(), "bytes": len(crudo)}
    return {
        "esquema": ESQUEMA,
        # CUÁNDO empieza la evidencia. Sin esto el fichero no dice nada: un hash
        # sin fecha no distingue «tomado al bajarlo» de «tomado seis meses después».
        "tomado_en": datetime.now(UTC).isoformat(timespec="seconds"),
        "sello": sello(),
        "documentos_en_manifiesto": len(filas),
        "sellados": len(sellos),
        "faltan": faltan,
        "sellos": sellos,
    }


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("manifiesto", type=Path)
    partes.add_argument("--docs", type=Path, default=None)
    partes.add_argument("--salida", type=Path, default=None)
    partes.add_argument(
        "--refijar",
        default="",
        metavar="RAZON",
        help="sobrescribe una captura anterior; la razón queda escrita dentro",
    )
    args = partes.parse_args()

    docs = args.docs or args.manifiesto.parent / "docs"
    salida = args.salida or args.manifiesto.parent / "xml_sha256.json"
    if salida.exists() and not args.refijar:
        viejo = json.loads(salida.read_text(encoding="utf-8"))
        print(f"YA EXISTE {salida}, tomado en {viejo.get('tomado_en')} sobre {viejo.get('sello')}")
        print("  Recalcularlo ahora tomaría el hash de los bytes de HOY, no de los")
        print("  que se bajaron: bendeciría un fichero sustituido. Usa --refijar RAZON.")
        return 1

    manifiesto = json.loads(args.manifiesto.read_text(encoding="utf-8"))
    captura = capturar(manifiesto, docs)
    if args.refijar:
        captura["refijado"] = args.refijar
    salida.write_text(json.dumps(captura, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"{captura['sellados']} XML sellados de {captura['documentos_en_manifiesto']} del")
    print(f"  manifiesto · tomado_en {captura['tomado_en']} · sello {captura['sello']}")
    print(f"  escrito {salida}")
    faltan = captura["faltan"]
    if isinstance(faltan, list) and faltan:
        print(f"  FALTAN {len(faltan)} XML en disco: {faltan[:5]}…")
        print("  La captura está INCOMPLETA y el fichero lo dice.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
