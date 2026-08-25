"""§9.4 · Emparejado PDF/XML: si los dos no dicen lo mismo, **se descarta y se cuenta**.

> *«Un emparejado silenciosamente incorrecto envenena todo el benchmark.»*

Es la frase que justifica este fichero. Si el PDF de un documento y su XML no son
el mismo documento, la verdad `DERIVED` que salga del XML se comparará contra lo
que un extractor leyó del PDF, y **la nota del extractor medirá el desajuste del
par, no su calidad**. Por eso el par se descarta. Y por eso el descarte **se
cuenta**: la tasa de descarte es un resultado publicado (§12,
`n_discarded_pairing`), no un detalle de limpieza.

## El umbral y de dónde sale

**Similitud de secuencia ≥ 0,85**, y el número **vive en el perfil de la entidad,
no aquí** (`umbral_coherencia`). Está medido sobre n=600 en tres ventanas: a 0,85
descarta el **4,00%**, IC [2,7 a 5,9]; a 0,95 descartaría uno de cada cinco documentos
buenos. Ver `docs/sondeo-boe-2026-08-22.md`.

**Se mide la similitud de SECUENCIA y no la contención.** La secuencia castiga el
reordenamiento, que en una tabla importa. La contención —*«¿está todo el XML
dentro del PDF?»*— se midió en el sondeo y **se retiró**: no decidía nada, y
publicar una segunda columna que nadie vuelve a comprobar es lo que acaba en la
siguiente corrección.

## La normalización, declarada entera (regla de oro 7)

Una normalización agresiva es hacer trampas en silencio **a favor de la
coherencia**: cuanto más se normaliza, más se parecen dos textos que no son
iguales, y menos documentos se descartan.

- Del PDF se quitan **las líneas de maquetación que el XML no tiene**: la cabecera
  `BOLETÍN OFICIAL DEL ESTADO`, `Núm.`, `Sec.`, `Pág.`, el `cve:`, la URL, el
  depósito legal, el ISSN y el «Verificable en». Sin quitarlas la similitud bajaría
  por un motivo que no tiene nada que ver con el contenido.
- De los dos: `NFKC`, minúsculas y partido en palabras `\\w+`.
- **Los acentos se conservan a propósito.** Quitarlos es agresivo y aquí sólo
  serviría para inflar la similitud.

## Precondiciones declaradas

- **Este módulo no abre un PDF.** Recibe los dos textos ya extraídos. De dónde sale
  el del PDF es problema de quien cosecha — y no es un extractor del banco: es
  preparación de corpus, y la regla de oro 1 sigue en pie porque este texto **no
  puntúa a nadie**.
- **`TOPE_TOKENS` acota el coste, y por tanto el número.** `SequenceMatcher` crece
  mucho más que lineal, así que se comparan los primeros 12.000 tokens de cada
  lado. En un documento más largo, lo que se mide es su principio.
- **La tasa se publica con su ventana.** Está medido que depende de cuándo
  coseches: entre ventanas hay un factor 2,75 (ADR-0030). Este módulo cuenta; quien
  publique tiene que decir sobre qué ventana.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

__all__ = [
    "TOPE_TOKENS",
    "CausaDescarte",
    "Coherencia",
    "Recuento",
    "Veredicto",
    "contar",
    "juzgar",
    "normalizar",
]

CausaDescarte = Literal[
    "sin_xml", "sin_pdf", "pdf_ilegible", "xml_sin_texto", "pdf_sin_texto", "incoherente"
]
"""**`pdf_ilegible` no es `sin_pdf`, y confundirlos manda a mirar al sitio
equivocado.** `sin_pdf` es que el fichero no llegó; `pdf_ilegible` es que llegó y
la librería no pudo abrirlo — el primero se arregla mirando el origen y el
segundo mirando el extractor de texto. Entró en el cierre de L3: quien inyecta los
textos capturaba el error de `pypdf` y devolvía `None`, o sea que un PDF de 34
páginas que `pypdf` no supiera abrir se publicaba como «no había PDF».

Es un enum CERRADO. Sin cajón de sastre a propósito: un `otro` dejaría que un
documento que se cae desaparezca del informe con la mitad mala de su historia."""

TOPE_TOKENS = 12_000
"""Tokens por lado que entran en la comparación. Ver la precondición del módulo."""

RUIDO_PDF = re.compile(
    r"^(BOLETÍN OFICIAL DEL ESTADO|Núm\.\s|Sec\.\s|Pág\.\s|cve:\s*BOE|"
    r"https?://www\.boe\.es|D\.\s*L\.:|ISSN:|Verificable en)",
    re.IGNORECASE,
)
_PALABRA = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class Coherencia:
    """Lo medido sobre un par, con los dos tamaños al lado.

    Los tokens van dentro porque una similitud de 0,9 entre dos textos de 30
    palabras y entre dos de 8.000 no son el mismo hecho, y sin el tamaño nadie
    puede distinguirlas al leer el informe.
    """

    similitud: float
    tokens_pdf: int
    tokens_xml: int


@dataclass(frozen=True)
class Veredicto:
    """Si el par entra, y si no entra, por qué. `causa` es `None` sii `acepta`."""

    acepta: bool
    causa: CausaDescarte | None
    coherencia: Coherencia


@dataclass(frozen=True)
class Recuento:
    """El censo de un lote. **`n_pares` cuadra siempre**, y por eso nada se traga.

    `aceptados + los descartes de todas las causas == n_pares` es un invariante
    estructural, no una comprobación de cortesía: si no cuadrara, habría documentos
    que salieron del emparejado sin aparecer en ningún lado, que es exactamente la
    forma que tiene un descarte de desaparecer del denominador.
    """

    n_pares: int
    n_aceptados: int
    por_causa: Mapping[str, int]

    @property
    def n_descartados(self) -> int:
        return sum(self.por_causa.values())

    @property
    def tasa_descarte(self) -> float:
        """Sobre el censo completo del lote, así que **no lleva intervalo** (ADR-0015).

        Lo que sí lleva, y no lo pone este objeto, es **su ventana**: la tasa
        depende de cuándo se coseche por un factor medido de 2,75.
        """
        return self.n_descartados / self.n_pares if self.n_pares else 0.0


def normalizar(texto: str, *, quitar_ruido: bool) -> list[str]:
    """Texto a lista de palabras. `quitar_ruido` sólo para el lado del PDF.

    Ver la sección de normalización del módulo: cada línea que se quita está
    declarada, porque quitar de más sube la similitud y baja los descartes.
    """
    lineas = texto.splitlines()
    if quitar_ruido:
        lineas = [ln for ln in lineas if not RUIDO_PDF.match(ln.strip())]
    plano = unicodedata.normalize("NFKC", " ".join(lineas)).lower()
    return _PALABRA.findall(plano)


def coherencia(texto_pdf: str, texto_xml: str) -> Coherencia:
    """Similitud de secuencia entre los dos textos ya normalizados."""
    pdf = normalizar(texto_pdf, quitar_ruido=True)
    xml = normalizar(texto_xml, quitar_ruido=False)
    if not pdf or not xml:
        return Coherencia(0.0, len(pdf), len(xml))
    ratio = SequenceMatcher(None, xml[:TOPE_TOKENS], pdf[:TOPE_TOKENS], autojunk=False).ratio()
    return Coherencia(ratio, len(pdf), len(xml))


def juzgar(texto_pdf: str | None, texto_xml: str | None, *, umbral: float) -> Veredicto:
    """El veredicto de un par, con su causa del enum cerrado si se descarta.

    El orden de las causas importa: **falta antes que vacío, y vacío antes que
    incoherente**. Un par sin XML no es un par incoherente — decir que lo es
    mandaría a alguien a mirar el umbral cuando el problema es que no se descargó.
    """
    if texto_xml is None:
        return Veredicto(False, "sin_xml", Coherencia(0.0, 0, 0))
    if texto_pdf is None:
        return Veredicto(False, "sin_pdf", Coherencia(0.0, 0, 0))
    medida = coherencia(texto_pdf, texto_xml)
    if medida.tokens_xml == 0:
        return Veredicto(False, "xml_sin_texto", medida)
    if medida.tokens_pdf == 0:
        return Veredicto(False, "pdf_sin_texto", medida)
    if medida.similitud < umbral:
        return Veredicto(False, "incoherente", medida)
    return Veredicto(True, None, medida)


def contar(veredictos: Sequence[Veredicto]) -> Recuento:
    """El censo del lote. Cada veredicto cae en un sitio y **en uno solo**."""
    causas = Counter(v.causa for v in veredictos if v.causa is not None)
    return Recuento(
        n_pares=len(veredictos),
        n_aceptados=sum(1 for v in veredictos if v.acepta),
        por_causa={str(c): n for c, n in sorted(causas.items())},
    )
