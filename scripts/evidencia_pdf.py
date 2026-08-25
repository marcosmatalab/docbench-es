"""La EVIDENCIA de cada discrepancia, sacada del PDF y **nunca del XML**. El comando.

    uv run python scripts/evidencia_pdf.py

## Por qué existe este fichero

**ADR-0039 regla 5**, escrita antes de adjudicar ni una discrepancia:

> Para adjudicar una discrepancia como «error de transcripción», la evidencia viene
> de la FUENTE DE TRANSCRIPCIÓN —el PDF—, nunca de la FUENTE MEDIDA —el XML.

Comprobar contra el XML **da por supuesto que el XML acierta**, y el XML es lo que
este hito mide. Sería la circularidad que «se transcribe del PDF» evita al
principio, reintroducida al final: toda discrepancia saldría «error de
transcripción» por construcción y la columna «fallo del código» quedaría vacía
siempre.

## La prueba, y por qué NO usa anclas

Para cada discrepancia de texto se buscan **las dos versiones enteras** —la
transcrita a mano y la derivada del XML— en la capa de texto del PDF. La respuesta
es una tabla de dos por dos y no depende de dónde se busque.

**La primera versión de esto sí usaba un ancla derivada del prefijo común, y falló
en dos de las once**: `'Ayuntamiento de'` cayó en el primer ayuntamiento de la
tabla, que era otro, y `'...'` cayó en una línea de puntos de relleno. Un ancla que
puede caer en el sitio equivocado no es evidencia. Buscar la cadena entera no tiene
ese modo de fallo.

| a mano aparece | la verdad aparece | Qué dice |
|---|---|---|
| no | **sí** | el PDF respalda a la verdad → **error de transcripción** |
| **sí** | no | el PDF respalda a la transcripción → sólo entonces se mira el XML
  crudo, y sólo para separar *defecto del origen* de *fallo del código* |
| **sí** | **sí** | las dos formas están en el documento: no decide, hay que ir a la celda |
| no | no | ninguna aparece literal: casi siempre **partición de línea** (límite 31) |

**Y una tercera prueba para las cadenas de un solo token**, porque la de dos por dos
no las decide: `'...'` está contenido en cualquier línea de puntos de relleno, así
que sale «SÍ» en los dos lados y no dice nada. Para esas se pregunta si el PDF trae
una **palabra suelta** exactamente igual —`pdftotext -bbox` emite un `<word>` por
token—, que es la pregunta que corresponde a una celda cuyo contenido entero es ese
token.

## Lo que hace, y lo que NO hace

**Imprime la evidencia. No adjudica.** La causa la decide una persona: es la regla 2
de ADR-0039, y automatizarla devolvería al código la decisión que se le está
quitando.

## De dónde sale el texto del PDF

`pdftotext`, que lee la capa de texto —el `ToUnicode` de las fuentes—, que es **lo
mismo que lee un extractor de PDF**. Por eso vale como evidencia: si el PDF trae `…`
y la transcripción puso tres puntos, un extractor saca `…` y coincide con la verdad,
así que el error es de la persona y no se le penaliza a él.

Se usan los **dos** modos y hacen falta los dos: `-raw` sigue el orden del flujo de
contenido, así que el texto de una celda partida en dos líneas sale contiguo;
`-layout` reconstruye columnas, así que sale separado por el texto de las columnas
de al lado. Una celda puede aparecer en uno y no en el otro sin que eso signifique
nada, y por eso se declaran por separado en vez de mezclarse.
"""

from __future__ import annotations

import ast
import html
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))

from scripts.comparar_verdad import _tabla_de, comparar  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"
FIXTURES = RAIZ / "runs" / "l4" / "fixtures"


def _pdftotext(ident: str, modo: str) -> str:
    """La capa de texto del PDF, con los espacios colapsados a uno."""
    salida = subprocess.run(
        ["pdftotext", modo, str(DOCS / f"{ident}.pdf"), "-"], capture_output=True, check=True
    )
    return re.sub(r"\s+", " ", salida.stdout.decode("utf-8", errors="replace"))


def palabras_del_pdf(ident: str) -> set[str]:
    """Cada token suelto de la capa de texto. `pdftotext -bbox` emite uno por `<word>`."""
    salida = subprocess.run(
        ["pdftotext", "-bbox", str(DOCS / f"{ident}.pdf"), "-"], capture_output=True, check=True
    )
    xml = salida.stdout.decode("utf-8", errors="replace")
    crudas = re.findall(r"<word[^>]*>(.*?)</word>", xml, re.DOTALL)
    return {html.unescape(w) for w in crudas}


def puntos_de_codigo(s: str) -> str:
    """Cada carácter no trivial con su punto de código y su nombre. Decide C y E."""
    piezas = []
    for ch in s:
        if ch.isascii() and ch.isalnum():
            piezas.append(ch)
        else:
            piezas.append(f"[{ch!r} U+{ord(ch):04X} {unicodedata.name(ch, '?')}]")
    return "".join(piezas)


def diferencia(a_mano: str, la_verdad: str) -> tuple[str, str]:
    """Los dos trozos que difieren, con tres caracteres de margen a cada lado."""
    i = 0
    while i < min(len(a_mano), len(la_verdad)) and a_mano[i] == la_verdad[i]:
        i += 1
    ja, jv = len(a_mano), len(la_verdad)
    while ja > i and jv > i and a_mano[ja - 1] == la_verdad[jv - 1]:
        ja, jv = ja - 1, jv - 1
    return a_mano[max(0, i - 3) : ja + 3], la_verdad[max(0, i - 3) : jv + 3]


def las_dos_versiones(detalle: str) -> tuple[str, str] | None:
    """Las dos versiones, de vuelta desde el detalle que imprime el comparador."""
    m = re.match(r"^\(\d+, \d+\): a mano (.+), la verdad (.+)$", detalle)
    if not m:
        return None
    try:
        return str(ast.literal_eval(m.group(1))), str(ast.literal_eval(m.group(2)))
    except (SyntaxError, ValueError):
        return None


def contexto(pdf: str, aguja: str, margen: int = 45) -> str:
    """El trozo del PDF alrededor de la cadena buscada. Sólo si aparece entera."""
    i = pdf.find(aguja)
    if i < 0:
        return ""
    return pdf[max(0, i - margen) : i + len(aguja) + margen]


def evidencia(ident: str, a_mano: str, la_verdad: str) -> list[str]:
    """La tabla de dos por dos, y el contexto de la versión que aparezca."""
    lineas = []
    presencia: dict[str, tuple[bool, bool]] = {}
    for modo in ("-raw", "-layout"):
        pdf = _pdftotext(ident, modo)
        presencia[modo] = (a_mano in pdf, la_verdad in pdf)
        lineas.append(
            f"     el PDF {modo:<8} contiene · a mano: "
            f"{'SÍ' if presencia[modo][0] else 'no':<3}· la verdad: "
            f"{'SÍ' if presencia[modo][1] else 'no'}"
        )
    if " " not in a_mano and " " not in la_verdad:
        palabras = palabras_del_pdf(ident)
        lineas.append(
            f"     el PDF como PALABRA SUELTA  · a mano: "
            f"{'SÍ' if a_mano in palabras else 'no':<3}· la verdad: "
            f"{'SÍ' if la_verdad in palabras else 'no'}"
            "   ← la que decide un token"
        )
    for modo in ("-raw", "-layout"):
        pdf = _pdftotext(ident, modo)
        for cual, aguja in (("a mano", a_mano), ("la verdad", la_verdad)):
            ctx = contexto(pdf, aguja)
            if ctx:
                lineas.append(f"     EL PDF ({modo}) DICE, alrededor de «{cual}»:")
                lineas.append(f"       …{ctx}…")
                return lineas
    lineas.append("     NINGUNA de las dos aparece literal en el PDF.")
    return lineas


def main() -> int:
    fixtures = sorted(FIXTURES.glob("*.json"))
    print(f"\n  EVIDENCIA CONTRA EL PDF · ADR-0039 regla 5 · {len(fixtures)} fixtures\n")
    total = 0
    for f in fixtures:
        fx = json.loads(f.read_text(encoding="utf-8"))
        tabla, _ = _tabla_de(fx)
        for d in comparar(fx, tabla):
            total += 1
            print(f"  ── {d.fixture} · {d.clase}")
            print(f"     {d.detalle}")
            par = las_dos_versiones(d.detalle) if d.clase == "TEXTO" else None
            if par is None:
                print("     EVIDENCIA: no hay texto que buscar. Se mira la página del PDF.\n")
                continue
            a_mano, la_verdad = par
            for linea in evidencia(str(fx["external_id"]), a_mano, la_verdad):
                print(linea)
            da, dv = diferencia(a_mano, la_verdad)
            print(f"     difieren en · a mano: {puntos_de_codigo(da)}")
            print(f"                   verdad: {puntos_de_codigo(dv)}\n")
    print(f"  {total} discrepancias con su evidencia. SIN ADJUDICAR (ADR-0039 regla 2).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
