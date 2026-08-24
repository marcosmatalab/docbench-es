"""§9.1 · El XML oficial del BOE a forma canónica. **Es lo que hace la verdad `DERIVED`.**

El XML del BOE trae las tablas **como HTML dentro del XML**: `<table>`, `<tr>`,
`<td>`, con sus `rowspan` y `colspan`. Así que aquí no hay un parseador nuevo: se
le pasa el documento entero a `core.canonical.from_html`, que es el conversor ya
validado contra PubTabNet en L2.

## Por qué se le pasa el XML ENTERO y no un recorte

Sería fácil sacar primero las `<table>` con un regex y pasar sólo eso. No se hace:
**toda normalización se documenta porque una normalización agresiva es hacer
trampas en silencio** (regla de oro 7), y recortar es normalizar. `from_html` ya
ignora lo que no es tabla, así que recortar no compra nada y sí introduce un paso
propio que puede perder una tabla con un atributo raro sin que nadie se entere.

## Precondiciones declaradas

- **No valida el XML.** Un XML mal formado no revienta aquí: `from_html` es un
  parseador tolerante y devolverá las tablas que reconozca. Quien necesite
  distinguir «no hay tablas» de «el XML está roto» tiene que mirar antes.
- **`page_span` lo pone quien llama.** El XML del BOE **no tiene páginas**, así que
  este módulo no puede saberlo (LIMITS 32). Por lo mismo **no se emite el estrato
  `multipagina`**: exigiría saber si una tabla cruza una página, y aquí eso no
  existe. No se aproxima; se declara.
- **`escaneado` tampoco sale de aquí**: es una propiedad de la capa de texto del
  PDF, no del XML.
- **Los `SOLAPE` del *table model error* del estándar HTML pasan de largo**
  (LIMITS 30): `from_html` los convierte en tablas con solape, que es un invariante
  fatal. Cuántos documentos del BOE lo disparan **no está medido**, y es la deuda
  que L4 tiene que mirar antes de derivar verdad de ellos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from docbench_es.core.canonical import from_html
from docbench_es.types import CanonicalTable

__all__ = ["Rasgos", "estratos", "rasgos", "tablas", "texto_plano"]

_ETIQUETA = re.compile(r"<[^>]+>")
_SPAN = re.compile(r'(rowspan|colspan)\s*=\s*"?(\d+)', re.IGNORECASE)


@dataclass(frozen=True)
class Rasgos:
    """Lo que se puede contar del XML **sin extractor**, que es lo que da el estrato.

    Los spans se cuentan **sólo si valen más de 1**: un `colspan="1"` no combina
    nada, y contarlo inflaría la cifra sobre la que se apoya medio proyecto.
    """

    n_tablas: int
    n_img: int
    n_rowspan: int
    n_colspan: int
    max_span: int


def texto_plano(xml: str) -> str:
    """El texto sin etiquetas. Es lo que `corpus.pairing` compara contra el PDF.

    Sustituye cada etiqueta por un espacio en vez de borrarla: sin el espacio,
    `<p>uno</p><p>dos</p>` daría `unodos`, una palabra que no existe, y la
    similitud contra el PDF bajaría por un motivo inventado aquí.
    """
    return _ETIQUETA.sub(" ", xml)


def tablas(xml: str, *, page_span: tuple[int, int] = (1, 1)) -> list[CanonicalTable]:
    """Las tablas del documento, en orden, en forma canónica."""
    return from_html(xml, page_span=page_span)


def rasgos(xml: str) -> Rasgos:
    """Cuenta tablas, imágenes y spans reales sobre el XML crudo.

    **Sobre el crudo y no sobre las tablas canónicas** a propósito: lo que decide
    el estrato es lo que el documento oficial declara, no lo que un conversor haya
    conseguido reconstruir. Si algún día `from_html` perdiera una tabla, el estrato
    seguiría diciendo que la había — y esa discrepancia es una señal, no un fallo
    que haya que esconder alineando las dos cuentas.
    """
    n_rowspan = n_colspan = maximo = 0
    for clase, valor in _SPAN.findall(xml):
        n = int(valor)
        if n <= 1:
            continue
        if clase.lower() == "rowspan":
            n_rowspan += 1
        else:
            n_colspan += 1
        maximo = max(maximo, n)
    return Rasgos(
        n_tablas=xml.count("<table"),
        n_img=xml.count("<img"),
        n_rowspan=n_rowspan,
        n_colspan=n_colspan,
        max_span=maximo,
    )


def estratos(r: Rasgos) -> frozenset[str]:
    """§9.4 · Los estratos que se pueden decidir **desde el XML y nada más**.

    Cuatro de los seis. Los otros dos no salen de aquí y no se inventan:
    `multipagina` porque el XML no tiene páginas, y `escaneado` porque es una
    propiedad de la capa de texto del PDF.

    Devuelve **un solo estrato de tabla**, que es como lo clasificó el sondeo sobre
    n=600: son categorías excluyentes por diseño —un documento con celdas
    combinadas ya no es `tabla-simple`— y publicar dos a la vez rompería la
    ponderación por estrato de §12, que reparte cada documento en una sola casilla.
    """
    if r.n_tablas == 0:
        return frozenset({"anexo-png" if r.n_img > 0 else "sin-tabla"})
    if r.n_rowspan + r.n_colspan > 0:
        return frozenset({"celdas-combinadas"})
    return frozenset({"tabla-simple"})
