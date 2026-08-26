"""§8 · `corpus.store` — el almacén local de la campaña: del manifiesto a `RawDoc`.

L3 dejó 1.000 documentos en disco y un manifiesto que dice de cada uno su `sha256`, sus
páginas y de dónde salió. Lo que faltaba era la vuelta: **cargarlos como `RawDoc`**, que
es lo que come un extractor. Sin esto, cada consumidor —la suite de conformidad, el
corredor de la campaña, el día de mañana la verdad— se escribiría su propio lector, y con
él su propia decisión sobre si comprobar los bytes.

## El `sha256` se REHACE en cada carga, y por eso está aquí y no en cada llamador

Un corpus que cambia por debajo no da un error: da **otro número**, con la misma pinta que
el bueno. El criterio de aceptación de L3 ya lo dice —su CUMPLE incluye rehacer los 1.000
hashes contra los bytes— y una campaña de cuatro horas no puede tener una garantía más
floja que su verificador.

Cuesta lo que cuesta leer el fichero, que hay que leerlo igual. Y **no es un fallo del
documento**: no sale por `ExtractionFailure` sino por `ContractViolation`, porque un corpus
que no es el que el manifiesto declara no produce una extracción mala, produce un número
**no atribuible**. Eso para la campaña; no la puntúa.

## Perezoso a propósito

`recorrer` va documento a documento. Los 616 de la campaña de estructura son ~360 MB, y
tenerlos todos en memoria a la vez no sirve para nada: el corredor procesa uno, escribe su
punto de control y lo suelta.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from docbench_es.errors import ContractViolation
from docbench_es.types import DocRef, RawDoc

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Iterator, Sequence
    from pathlib import Path

__all__ = ["Almacen", "Entrada"]


@dataclass(frozen=True)
class Entrada:
    """Lo que el manifiesto dice de un documento, **sin sus bytes**.

    Existe para poder decidir qué se procesa —por sección, por estrato, por páginas— sin
    leer 360 MB de disco antes de saberlo.
    """

    external_id: str
    sha256: str
    n_pages: int | None
    fetched_at: datetime
    url: str
    seccion: str
    estratos: frozenset[str]


class Almacen:
    """El manifiesto de una campaña y la carpeta con sus bytes, atados."""

    def __init__(self, manifiesto: Path, docs: Path, entidad: str = "boe") -> None:
        crudo = json.loads(manifiesto.read_text(encoding="utf-8"))
        self.ruta = manifiesto
        self.docs = docs
        self.entidad = str(crudo.get("entidad", entidad))
        self.entradas: tuple[Entrada, ...] = tuple(
            Entrada(
                external_id=str(d["external_id"]),
                sha256=str(d["sha256"]),
                n_pages=None if d.get("n_pages") is None else int(d["n_pages"]),
                fetched_at=datetime.fromisoformat(str(d["fetched_at"])),
                url=str(d.get("url_pdf", "")),
                seccion=str(d.get("seccion", "")),
                estratos=frozenset(str(e) for e in d.get("strata", ())),
            )
            for d in crudo["documentos"]
        )
        self._por_id = {e.external_id: e for e in self.entradas}

    def __len__(self) -> int:
        return len(self.entradas)

    def ids(self) -> list[str]:
        """Los identificadores del manifiesto, en su orden. **El denominador.**"""
        return [e.external_id for e in self.entradas]

    def cargar(self, external_id: str) -> RawDoc:
        """El documento con sus bytes, **con el `sha256` rehecho contra el manifiesto**."""
        entrada = self._por_id.get(external_id)
        if entrada is None:
            raise ContractViolation(
                f"{external_id} no está en {self.ruta}: {len(self.entradas)} documentos"
            )
        pdf = self.docs / f"{external_id}.pdf"
        if not pdf.exists():
            raise ContractViolation(
                f"el manifiesto declara {external_id} y no está en {self.docs}. "
                f"Un corpus incompleto no da una nota mala: da un denominador falso"
            )
        crudos = pdf.read_bytes()
        visto = hashlib.sha256(crudos).hexdigest()
        if visto != entrada.sha256:
            raise ContractViolation(
                f"{external_id}: el manifiesto dice sha256={entrada.sha256[:12]}… y los "
                f"bytes en disco dan {visto[:12]}…. El corpus cambió por debajo, así que "
                f"ningún número medido sobre él es atribuible a este manifiesto"
            )
        xml = self.docs / f"{external_id}.xml"
        return RawDoc(
            ref=DocRef(
                entity=self.entidad,
                external_id=external_id,
                published_on=None,
                url=entrada.url or None,
                kind="pdf",
            ),
            primary=crudos,
            primary_mime="application/pdf",
            companions={"xml": xml.read_bytes()} if xml.exists() else {},
            sha256=entrada.sha256,
            fetched_at=entrada.fetched_at,
            n_pages=entrada.n_pages,
        )

    def recorrer(self, ids: Sequence[str] | None = None) -> Iterator[RawDoc]:
        """Uno a uno, en el orden pedido —o el del manifiesto—. **Nunca todos a la vez.**"""
        for ident in self.ids() if ids is None else ids:
            yield self.cargar(ident)
