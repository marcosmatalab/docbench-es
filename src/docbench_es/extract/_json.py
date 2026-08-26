"""Cómo viaja una `Extraction` a JSON **y cómo vuelve**.

Va aparte de `diario.py` por el límite de 300 líneas de `CLAUDE.md`, y la costura cae
donde tenía que caer: allí está **el fichero** —qué está hecho, qué se añade, qué no se
pudo leer— y aquí **el formato**.

## Ida y vuelta, y no sólo ida

`.importlinter` protege una promesa concreta: *«el núcleo es puro: se prueba sin red y **se
puede reejecutar sobre extracciones viejas**»*. Eso exige poder RECONSTRUIR una
`Extraction`, no sólo escribir un resumen de ella. De ahí `de_json`, y de ahí que su test
compare **el objeto entero** en vez de los campos que a uno se le ocurran: un formato que
perdiera la `caption` o el `page_span` pasaría una comparación escrita a mano.

## Lo que se guarda y lo que no

Todo lo que la `Extraction` traía, **incluido el texto**. Ocupa —87 MB por extractor sobre
los 616— y aun así sale a cuenta: recuperarlo de otra forma cuesta volver a correr la
campaña. Lo que no se guarda es nada derivado, ni TEDS ni recuentos, porque eso es
justamente lo que el núcleo puro tiene que poder recalcular.

**`Decimal` viaja como cadena.** Un `float` en el JSON convertiría el dinero en coma
flotante al leerlo, que es exactamente lo que `CLAUDE.md` prohíbe.

**Y lo que se lee no se da por bueno.** `json.loads` devuelve `object`, así que cada campo
pasa por un estrechador que dice **qué campo** falló. El efecto que importa no es el
tipado: es que un diario a medias levanta en vez de colarse como una extracción a medias
que luego puntúa a alguien.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import cast, get_args

from benchcore.types import Cost, TokenUsage

from docbench_es.errors import ContractViolation
from docbench_es.types import CanonicalCell, CanonicalTable, DocRef, Extraction, ExtractionFailure

__all__ = ["CAUSAS", "a_json", "de_json", "identificador"]

CAUSAS = frozenset(get_args(ExtractionFailure))
"""El enum cerrado de §6.9, sacado del tipo. Una lista a mano se quedaría corta."""


def _decimal(valor: object) -> Decimal | None:
    return None if valor is None else Decimal(str(valor))


def _celda(c: CanonicalCell) -> dict[str, object]:
    return {
        "row": c.row,
        "col": c.col,
        "rowspan": c.rowspan,
        "colspan": c.colspan,
        "text": c.text,
        "is_header": c.is_header,
    }


def _tabla(t: CanonicalTable) -> dict[str, object]:
    return {
        "cells": [_celda(c) for c in t.cells],
        "n_rows": t.n_rows,
        "n_cols": t.n_cols,
        "page_span": list(t.page_span),
        "caption": t.caption,
        "expresses_spans": t.expresses_spans,
        "source_format": t.source_format,
    }


def _coste(c: Cost) -> dict[str, object]:
    return {
        "eur": str(c.eur),
        "usd": None if c.usd is None else str(c.usd),
        "tokens": {
            "input_uncached": c.tokens.input_uncached,
            "input_cached": c.tokens.input_cached,
            "cache_write": c.tokens.cache_write,
            "output": c.tokens.output,
            "reasoning": c.tokens.reasoning,
        },
        "price_table": c.price_table,
        "fx_table": c.fx_table,
        "fx_rate": None if c.fx_rate is None else str(c.fx_rate),
        "estimated": c.estimated,
        "measured": c.measured,
        "wall_ms": c.wall_ms,
    }


def a_json(ex: Extraction) -> dict[str, object]:
    """La `Extraction` entera, sin nada derivado. `Decimal` como cadena."""
    return {
        "extractor_id": ex.extractor_id,
        "extractor_version": ex.extractor_version,
        "doc_ref": {
            "entity": ex.doc_ref.entity,
            "external_id": ex.doc_ref.external_id,
            "published_on": None
            if ex.doc_ref.published_on is None
            else ex.doc_ref.published_on.isoformat(),
            "url": ex.doc_ref.url,
            "kind": ex.doc_ref.kind,
        },
        "text": ex.text,
        "tables": [_tabla(t) for t in ex.tables],
        "native_format": ex.native_format,
        "pages_processed": ex.pages_processed,
        "cost": _coste(ex.cost),
        "latency_ms": ex.latency_ms,
        "warnings": list(ex.warnings),
        "failed": ex.failed,
        "failure_reason": ex.failure_reason,
    }


def _dic(valor: object, donde: str) -> dict[str, object]:
    """Un objeto del JSON, o **un error con su sitio**. Nada se da por supuesto.

    Los cuatro estrechadores de aquí abajo existen porque `json.loads` devuelve
    `object` y este repo prohíbe `Any` explícito. El efecto secundario es el que
    importa: un diario corrupto **levanta diciendo qué campo**, en vez de colarse como
    una extracción a medias que luego puntúa a alguien.
    """
    if not isinstance(valor, dict):
        raise ContractViolation(f"{donde}: se esperaba un objeto y vino {type(valor).__name__}")
    return {str(k): v for k, v in valor.items()}


def _lista(valor: object, donde: str) -> list[object]:
    if not isinstance(valor, list):
        raise ContractViolation(f"{donde}: se esperaba una lista y vino {type(valor).__name__}")
    return list(valor)


def _txt(valor: object, donde: str) -> str:
    if not isinstance(valor, str):
        raise ContractViolation(f"{donde}: se esperaba texto y vino {type(valor).__name__}")
    return valor


def _num(valor: object, donde: str) -> int:
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise ContractViolation(f"{donde}: se esperaba un entero y vino {valor!r}")
    return valor


def identificador(crudo: object) -> str:
    """El `external_id` de una línea, **sin reconstruir la extracción entera**.

    Es lo que `Diario.hechos()` necesita para reanudar, y son 616 líneas de hasta 100 KB:
    parsearlas enteras para leer un campo costaría lo que no hace falta gastar.
    """
    return _txt(_dic(_dic(crudo, "línea")["doc_ref"], "doc_ref")["external_id"], "external_id")


def de_json(crudo: object) -> Extraction:
    """La vuelta. **Sin esto, «reejecutar sobre extracciones viejas» es una frase.**"""
    d = _dic(crudo, "extracción")
    ref = _dic(d["doc_ref"], "doc_ref")
    coste = _dic(d["cost"], "cost")
    fichas = _dic(coste["tokens"], "cost.tokens")
    publicado = ref["published_on"]
    razon = d["failure_reason"]
    return Extraction(
        extractor_id=_txt(d["extractor_id"], "extractor_id"),
        extractor_version=_txt(d["extractor_version"], "extractor_version"),
        doc_ref=DocRef(
            entity=_txt(ref["entity"], "doc_ref.entity"),
            external_id=_txt(ref["external_id"], "doc_ref.external_id"),
            published_on=None if publicado is None else date.fromisoformat(str(publicado)),
            url=None if ref["url"] is None else _txt(ref["url"], "doc_ref.url"),
            kind=_txt(ref["kind"], "doc_ref.kind"),
        ),
        text=_txt(d["text"], "text"),
        tables=tuple(_tabla_de(t) for t in _lista(d["tables"], "tables")),
        native_format=_txt(d["native_format"], "native_format"),
        pages_processed=_num(d["pages_processed"], "pages_processed"),
        cost=Cost(
            eur=Decimal(_txt(coste["eur"], "cost.eur")),
            usd=_decimal(coste["usd"]),
            tokens=TokenUsage(**{k: _num(v, f"tokens.{k}") for k, v in fichas.items()}),
            price_table=_opcional(coste["price_table"], "cost.price_table"),
            fx_table=_opcional(coste["fx_table"], "cost.fx_table"),
            fx_rate=_decimal(coste["fx_rate"]),
            estimated=bool(coste["estimated"]),
            measured=bool(coste["measured"]),
            wall_ms=_num(coste["wall_ms"], "cost.wall_ms"),
        ),
        latency_ms=_num(d["latency_ms"], "latency_ms"),
        warnings=tuple(_txt(w, "warnings") for w in _lista(d["warnings"], "warnings")),
        failed=bool(d["failed"]),
        failure_reason=None if razon is None else _causa(_txt(razon, "failure_reason")),
    )


def _opcional(valor: object, donde: str) -> str | None:
    return None if valor is None else _txt(valor, donde)


def _causa(nombre: str) -> ExtractionFailure:
    """La causa, **comprobada contra el enum CERRADO de §6.9**.

    Sin esto, un diario con `failure_reason: "vete a saber"` reconstruiría una
    `Extraction` con una causa que no existe, y el informe la contaría en una fila que
    nadie declaró. El enum es cerrado precisamente para que eso no pueda pasar.
    """
    if nombre not in CAUSAS:
        raise ContractViolation(
            f"failure_reason={nombre!r} no es del enum cerrado de §6.9: {sorted(CAUSAS)}"
        )
    return cast("ExtractionFailure", nombre)


def _celda_de(crudo: object) -> CanonicalCell:
    c = _dic(crudo, "celda")
    return CanonicalCell(
        row=_num(c["row"], "celda.row"),
        col=_num(c["col"], "celda.col"),
        rowspan=_num(c["rowspan"], "celda.rowspan"),
        colspan=_num(c["colspan"], "celda.colspan"),
        text=_txt(c["text"], "celda.text"),
        is_header=bool(c["is_header"]),
    )


def _tabla_de(crudo: object) -> CanonicalTable:
    t = _dic(crudo, "tabla")
    tramo = _lista(t["page_span"], "tabla.page_span")
    return CanonicalTable(
        cells=tuple(_celda_de(c) for c in _lista(t["cells"], "tabla.cells")),
        n_rows=_num(t["n_rows"], "tabla.n_rows"),
        n_cols=_num(t["n_cols"], "tabla.n_cols"),
        page_span=(_num(tramo[0], "page_span[0]"), _num(tramo[1], "page_span[1]")),
        caption=_opcional(t["caption"], "tabla.caption"),
        expresses_spans=bool(t["expresses_spans"]),
        source_format=_txt(t["source_format"], "tabla.source_format"),
    )
