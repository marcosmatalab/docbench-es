"""Primitivas del sondeo del BOE: recorrido del sumario y medidas.

USAR Y TIRAR: nada de `src/` importa esto.

Se separa de `sondeo_boe.py` porque juntos pasaban de 300 lineas y `CLAUDE.md` lo
prohibe. Aqui viven el enum cerrado de causas, la descarga con codigo comprobado y
las cuatro medidas; alli, el descubrimiento y el informe.
"""

from __future__ import annotations

import re
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import StrEnum
from typing import Any


class Causa(StrEnum):
    """Enum CERRADO de por que un documento no entra en la muestra.

    Regla de oro 6: ningun error se traga. Un documento que falla se cuenta con su
    causa, y la tasa de fallo es un resultado, no una nota al pie.
    """

    SIN_URL_XML = "sin_url_xml"
    SIN_URL_PDF = "sin_url_pdf"
    HTTP_XML = "http_xml"
    HTTP_PDF = "http_pdf"
    RED_XML = "red_xml"
    RED_PDF = "red_pdf"
    XML_MAL_FORMADO = "xml_mal_formado"
    PDF_ILEGIBLE = "pdf_ilegible"
    PDF_SIN_CAPA_TEXTO = "pdf_sin_capa_texto"
    XML_SIN_TEXTO = "xml_sin_texto"


# Normalizacion para la coherencia PDF/XML. CLAUDE.md regla 7: toda normalizacion se
# documenta, porque una agresiva es hacer trampas en silencio. Estas lineas son
# maquetacion que el PDF lleva y el XML no; dejarlas hundiria la similitud por un
# motivo que no tiene nada que ver con el contenido.
RUIDO_PDF = re.compile(
    r"^(BOLETÍN OFICIAL DEL ESTADO|Núm\.\s|Sec\.\s|Pág\.\s|cve:\s*BOE|"
    r"https?://www\.boe\.es|D\.\s*L\.:|ISSN:|Verificable en)",
    re.IGNORECASE,
)
PALABRA = re.compile(r"\w+", re.UNICODE)
ETIQUETA = re.compile(r"<[^>]+>")
SPAN = re.compile(r'(rowspan|colspan)\s*=\s*"?(\d+)', re.IGNORECASE)


@dataclass
class Doc:
    """Un documento de la muestra: lo medido y, si fallo, por que."""

    ident: str
    fecha: str
    seccion: str = "?"
    url_xml: str = ""
    url_pdf: str = ""
    fallo: str | None = None
    http_xml: int = 0
    http_pdf: int = 0
    n_tablas: int = 0
    n_rowspan: int = 0
    n_colspan: int = 0
    max_span: int = 0
    n_img: int = 0
    paginas: int = 0
    tokens_xml: int = 0
    tokens_pdf: int = 0
    similitud: float = 0.0
    contencion: float = 0.0
    estrato: str = ""
    etiquetas: dict[str, int] = field(default_factory=dict)


@dataclass
class Fetch:
    """Resultado de una descarga. `codigo` es el HTTP; 0 si ni siquiera llego a haberlo."""

    ok: bool
    codigo: int
    cuerpo: bytes
    causa: Causa | None = None


def descargar(cliente: Any, url: str, es_xml: bool, espera: float) -> Fetch:  # noqa: ANN401
    """Descarga comprobando el codigo. Nada aqui se apoya en 'no ha fallado'."""
    import httpx

    try:
        r = cliente.get(url, timeout=45.0, follow_redirects=True)
    except httpx.HTTPError:
        return Fetch(False, 0, b"", Causa.RED_XML if es_xml else Causa.RED_PDF)
    time.sleep(espera)
    if r.status_code != 200:
        return Fetch(False, r.status_code, b"", Causa.HTTP_XML if es_xml else Causa.HTTP_PDF)
    return Fetch(True, r.status_code, r.content)


def normalizar(texto: str, quitar_ruido: bool) -> list[str]:
    """Minusculas, NFKC y palabras.

    **Se conservan los acentos a proposito**: quitarlos es normalizacion agresiva y
    aqui solo serviria para inflar la similitud entre PDF y XML.
    """
    lineas = texto.splitlines()
    if quitar_ruido:
        lineas = [ln for ln in lineas if not RUIDO_PDF.match(ln.strip())]
    plano = unicodedata.normalize("NFKC", " ".join(lineas)).lower()
    return PALABRA.findall(plano)


def texto_de_xml(crudo: str) -> str:
    return ETIQUETA.sub(" ", crudo)


def medir_tablas(crudo: str, doc: Doc) -> None:
    """Cuenta tablas y spans REALES: solo `rowspan`/`colspan` con valor > 1.

    Un `colspan="1"` no combina nada, y contarlo inflaria la cifra que sostiene el
    proyecto entero.
    """
    doc.n_tablas = crudo.count("<table")
    doc.n_img = crudo.count("<img")
    for clase, valor in SPAN.findall(crudo):
        n = int(valor)
        if n > 1:
            if clase.lower() == "rowspan":
                doc.n_rowspan += 1
            else:
                doc.n_colspan += 1
            doc.max_span = max(doc.max_span, n)
    doc.etiquetas = dict(Counter(re.findall(r"<(\w+)", crudo)).most_common(12))


def clasificar(doc: Doc) -> str:
    """Estratos de dificultad de §9.4, los medibles desde el XML.

    `multipagina` NO lo es: exige saber si UNA tabla cruza una pagina, y el XML del
    BOE no tiene paginas. Se declara en las notas en vez de estimarlo.
    """
    if doc.n_tablas == 0:
        return "anexo-png" if doc.n_img > 0 else "sin-tabla"
    if doc.n_rowspan + doc.n_colspan > 0:
        return "celdas-combinadas"
    return "tabla-simple"


def comparar(t_xml: list[str], t_pdf: list[str]) -> tuple[float, float]:
    """Similitud de secuencia y contencion del XML en el PDF (multiconjunto).

    Las dos, porque miden cosas distintas: la secuencia castiga el reordenamiento
    —que en una tabla importa— y la contencion responde a "¿esta todo el XML dentro
    del PDF?", que es la pregunta de L3.
    """
    if not t_xml or not t_pdf:
        return 0.0, 0.0
    tope = 12000
    sim = SequenceMatcher(None, t_xml[:tope], t_pdf[:tope], autojunk=False).ratio()
    cx, cp = Counter(t_xml), Counter(t_pdf)
    cubierto = sum(min(n, cp.get(w, 0)) for w, n in cx.items())
    return sim, cubierto / sum(cx.values())


def _lista(x: Any) -> list[Any]:  # noqa: ANN401
    """El sumario colapsa las listas de un solo elemento a dict. Normalizar o perder datos."""
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def recorrer_items(nodo: Any, salida: list[dict[str, Any]]) -> list[dict[str, Any]]:  # noqa: ANN401
    """Items sueltos de cualquier profundidad, sin seccion. Solo para diagnostico."""
    if isinstance(nodo, dict):
        if "identificador" in nodo and "url_pdf" in nodo:
            salida.append(nodo)
        else:
            for v in nodo.values():
                recorrer_items(v, salida)
    elif isinstance(nodo, list):
        for v in nodo:
            recorrer_items(v, salida)
    return salida


def _cajas(nodo: dict[str, Any]) -> list[dict[str, Any]]:
    """El nodo y, si lo tiene, su envoltorio `texto`.

    El sumario del BOE mete a veces una clave `texto` entre un nivel y el siguiente,
    y a veces no, **en cualquier nivel**: visto en `seccion` (sumario del 20260809) y
    en `departamento` (20260817). Sin mirar dentro se pierden documentos reales.
    """
    return [c for c in (nodo, nodo.get("texto")) if isinstance(c, dict)]


def _hijos(nodo: dict[str, Any], clave: str) -> list[dict[str, Any]]:
    """`nodo[clave]` buscando en el nodo y en su envoltorio `texto`, como lista."""
    fuera: list[dict[str, Any]] = []
    for caja in _cajas(nodo):
        fuera += [x for x in _lista(caja.get(clave)) if isinstance(x, dict)]
    return fuera


def items_con_seccion(sumario: dict[str, Any]) -> list[dict[str, Any]]:
    """Recorre diario -> seccion -> departamento -> [epigrafe] -> item etiquetando la seccion.

    Importa: el manual dice que `discover` **filtra por seccion**, asi que la tasa de
    tabla global mezcla anuncios y edictos con las disposiciones. Sin esta etiqueta el
    sondeo no puede responder a la pregunta que decide L3.
    """
    salida: list[dict[str, Any]] = []
    for diario in _lista(sumario.get("diario")):
        for sec in _lista(diario.get("seccion")):
            cod = str(sec.get("codigo", "?"))
            nom = str(sec.get("nombre", ""))
            for dep in _hijos(sec, "departamento"):
                for g in _hijos(dep, "epigrafe") or [dep]:
                    for it in _hijos(g, "item"):
                        it["_seccion"] = cod
                        it["_seccion_nombre"] = nom
                        salida.append(it)
    return salida
