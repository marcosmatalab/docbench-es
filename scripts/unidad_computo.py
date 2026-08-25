"""UNA unidad de B5-bis: un extractor sobre un documento, en su propio proceso.

    python scripts/unidad_computo.py docling BOE-A-2024-12345 /ruta/salida.json

Escribe su resultado como JSON **en el fichero que le pasan**, y no en `stdout`.

## Por qué no en `stdout`, que era lo natural

Porque `stdout` no es suyo: lo comparte con todo lo que importe. `pymupdf4llm` arrastra
`rapidocr`, que imprime `rapidocr_api using backend: rapidocr` y un bloque
`=== Document parser messages ===` **antes** de que este programa llegue a escribir
nada. El JSON quedaba precedido de basura, el padre no podía parsearlo y registraba
`SALIDA_ILEGIBLE` en las **tres** unidades de `pymupdf4llm` — un fallo del arnés
disfrazado de fallo del extractor. Con un fichero propio no hay nada que compartir.

**Quien mide el tiempo es el padre**,
con `os.wait4`, porque el `rusage` del hijo da segundos de CPU exactos y no lo altera
ni que el gobernador térmico lo pare a mitad con `SIGSTOP`.

## `salida` NO es una medida

Cada extractor devuelve un entero que sólo sirve de **prueba de que el trabajo ocurrió**,
y significa una cosa distinta en cada uno: tablas en `pdfplumber`, `camelot` y `docling`;
**caracteres de markdown** en `pymupdf4llm`. No se publica, no se compara entre filas y
no entra en ninguna media. Está para que una unidad que devuelve 0 se pueda mirar.

Aquí había un `from_markdown(...)` para contar tablas en `pymupdf4llm`, y **eran dos
fallos**: metía un conversor sin consumidor validado en la ruta de un número publicado
—lo cazó `tests/unit/test_sin_consumidor.py`— y hacía que **sólo esa fila** pagara el
parseo dentro de la región cronometrada, sesgando su coste hacia arriba frente a las
demás. B5-bis mide COSTE, no calidad: el conversor sobra.

## Por qué un proceso por unidad

`docling` y `marker` cargan modelos de *torch* en memoria y levantan un pool de hilos.
Dentro de un solo proceso largo eso queda vivo entre documentos: memoria retenida y
carga sostenida sin una sola pausa — que es como esta máquina llegó a 85 °C. Un proceso
por unidad hace que **al terminar cada documento la carga baje a cero**, y de paso
convierte el cómputo en algo que se puede matar en cualquier segundo y continuar.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "runs" / "l3" / "docs"

# Se fijan ANTES de importar nada: torch, OpenMP y BLAS leen el entorno al cargarse, y
# ponerlas después no tiene ningún efecto. El padre las pasa ya en el entorno; esto es
# el cinturón por si alguien invoca este script a mano.
for _var in (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "TORCH_NUM_THREADS",
    "TOKENIZERS_PARALLELISM",
):
    os.environ.setdefault(_var, "1" if _var != "TOKENIZERS_PARALLELISM" else "false")

sys.path.insert(0, str(RAIZ / "src"))


def _pdfplumber(ruta: Path) -> int:
    import pdfplumber

    with pdfplumber.open(ruta) as pdf:
        return sum(len(p.extract_tables()) for p in pdf.pages)


def _pymupdf4llm(ruta: Path) -> int:
    import pymupdf4llm

    return len(pymupdf4llm.to_markdown(str(ruta), show_progress=False))


def _camelot(ruta: Path) -> int:
    import camelot

    return len(camelot.read_pdf(str(ruta), pages="all"))


def _docling(ruta: Path) -> int:
    import torch

    torch.set_num_threads(int(os.environ.get("TORCH_NUM_THREADS", "1")))
    from docling.document_converter import DocumentConverter

    return len(DocumentConverter().convert(str(ruta)).document.tables)


EXTRACTORES = {
    "pdfplumber": _pdfplumber,
    "pymupdf4llm": _pymupdf4llm,
    "camelot": _camelot,
    "docling": _docling,
}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] not in EXTRACTORES:
        print(
            f"uso: unidad_computo.py {{{'|'.join(EXTRACTORES)}}} <external_id> <salida.json>",
            file=sys.stderr,
        )
        return 2
    nombre, ident, destino = argv
    ruta = DOCS / f"{ident}.pdf"

    def escribir(registro: dict[str, object]) -> None:
        Path(destino).write_text(json.dumps(registro), encoding="utf-8")

    if not ruta.exists():
        escribir({"ok": False, "causa": "PDF_AUSENTE", "detalle": str(ruta)})
        return 1
    try:
        salida = EXTRACTORES[nombre](ruta)
    except Exception as e:  # un extractor que revienta también cuesta, y se cuenta
        escribir({"ok": False, "causa": type(e).__name__, "detalle": str(e)[:200]})
        return 1
    escribir({"ok": True, "salida": salida})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
