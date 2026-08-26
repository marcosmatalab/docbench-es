"""Un corpus de juguete con la forma exacta del de L3, para los tests de la puerta.

El corpus real son 361 MB fuera de git (LIMITS 74), así que un test que dependiera de él
no correría donde hace falta que corra. Éste tiene lo que `corpus.store` necesita —el
manifiesto con `sha256`, `n_pages` y `fetched_at`, y los bytes al lado— y **los hashes son
de verdad**: si lo fueran de mentira, el test de «un PDF que cambió por debajo» no
demostraría nada.

Vive aparte porque lo usan tres ficheros de test. Una cuarta copia del mismo montaje era
la alternativa, y este repo tiene una sección de límites dedicada a lo que pasa cuando
una decisión se escribe dos veces.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from docbench_es.corpus.store import Almacen

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Sequence
    from pathlib import Path

BYTES = b"%PDF-1.4\nde juguete\n%%EOF"


def contenido_de(ident: str) -> bytes:
    """Bytes distintos por documento: con bytes iguales, un `sha256` cruzado pasaría."""
    return BYTES + ident.encode()


def montar(
    tmp_path: Path,
    ids: Sequence[str],
    *,
    con_xml: bool = True,
    contenido: dict[str, bytes] | None = None,
) -> Almacen:
    """Escribe el corpus y devuelve su `Almacen`. `almacen.docs` y `.ruta` dan el resto."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    documentos = []
    for i, ident in enumerate(ids):
        crudos = (contenido or {}).get(ident, contenido_de(ident))
        (docs / f"{ident}.pdf").write_bytes(crudos)
        if con_xml:
            (docs / f"{ident}.xml").write_bytes(b"<doc/>")
        documentos.append(
            {
                "external_id": ident,
                "sha256": hashlib.sha256(crudos).hexdigest(),
                "n_pages": i + 1,
                "fetched_at": datetime(2026, 8, 24, 12, 0, tzinfo=UTC).isoformat(),
                "url_pdf": f"https://ejemplo/{ident}.pdf",
                "seccion": "3",
                "strata": ["sin-tabla"],
            }
        )
    manifiesto = tmp_path / "manifiesto.json"
    manifiesto.write_text(
        json.dumps({"entidad": "boe", "documentos": documentos}), encoding="utf-8"
    )
    return Almacen(manifiesto, docs)


def unos_cuantos(tmp_path: Path, cuantos: int = 3, *, con_xml: bool = True) -> Almacen:
    """`BOE-A-2026-1000`, `…1001`, … con la numeración del BOE de verdad."""
    ids = [f"BOE-A-2026-{1000 + i}" for i in range(cuantos)]
    return montar(tmp_path, ids, con_xml=con_xml)
