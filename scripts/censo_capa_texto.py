"""Cuántas páginas del corpus NO tienen capa de texto. **Con su instrumento declarado.**

    uv run python scripts/censo_capa_texto.py
    uv run python scripts/censo_capa_texto.py --escribir   # runs/censos/capa_texto.json

## La pregunta que contesta, y por qué no es curiosidad

`pymupdf4llm` hizo **264 pasadas de OCR sobre 668 páginas** de los 12 documentos del humo
y `pdfplumber` ninguna (LIMITS 104). Eso admite **dos explicaciones opuestas**:

* si esas páginas **no tienen** capa de texto, `pymupdf4llm` está leyendo lo que
  `pdfplumber` no puede, y la diferencia es de **alcance**;
* si **sí la tienen**, `pymupdf4llm` está haciendo trabajo innecesario **y peor** —el OCR
  de una página digital es peor que leer su capa—, y la diferencia es de **coste**.

Sólo un censo las separa, y hay que separarlas **antes** de congelar el diseño de la
tabla: de ello depende si la cobertura se cuenta por página o por documento.

## El instrumento, y por qué NO es ninguno de los concursantes

Se mide con **`pypdf`**, que `pyproject.toml` declara desde L3 como preparación de corpus
y **no** como extractor del banco: *«este texto NO puntúa a nadie»*. Usar `pymupdf` o
`pdfplumber` sería preguntarle a un concursante si el examen estaba en blanco.

**Lo que este censo NO dice.** No dice que la página esté vacía «de verdad»: dice que
**`pypdf` no saca de ella ni un carácter**. `pypdf` extrae peor que `pymupdf`, así que el
recuento de páginas sin capa es un **techo**, no un valor exacto — y en la dirección que
conviene: si `pypdf` SÍ saca texto, no hay duda de que la capa existe.

`UMBRAL_POBRE` es una segunda cifra, no un criterio: una página con cuatro caracteres es
tan escaneada como una con cero a efectos de un extractor, y se publica aparte para que
nadie tenga que creerse un solo número.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_paginas import DEL_COSTE  # noqa: E402
from fuera_de_git import exige  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"
MANIFIESTO = RAIZ / "runs" / "l3" / "manifiesto.json"
DESTINO = RAIZ / "runs" / "censos" / "capa_texto.json"
HUMO = RAIZ / "runs" / "l5" / "humo_campana.json"

INSTRUMENTO = "pypdf.PdfReader.extract_text por pagina"
"""El instrumento, en el sello del censo: NO es ninguno de los concursantes."""

ILEGIBLE = "(ilegible)"
"""La banda de un documento que `pypdf` no pudo abrir. **Se cuenta, no se salta.**"""

UMBRAL_POBRE = 10
"""Caracteres por debajo de los cuales una página es tan ilegible como una vacía.

No es un criterio: es una **segunda cifra**. El número que manda es el de CERO caracteres,
que no depende de ningún umbral elegido por nadie.
"""


@dataclass(frozen=True)
class Documento:
    """Lo que el censo sabe de un documento, sin guardar su texto."""

    external_id: str
    paginas: int
    sin_texto: int
    pobres: int

    @property
    def banda(self) -> str:
        """La banda de páginas, o `ILEGIBLE` si no se pudo abrir.

        **Un documento de cero páginas no cae en ninguna banda**, y la primera versión de
        esto levantaba `ValueError`: un solo PDF que `pypdf` no abriera tumbaba el censo
        entero de 1.000. Lo encontró su propio test, no el corpus — sobre los 1.000 de L3
        se abren todos—. Un ilegible **se cuenta en su propia fila**: ni desaparece del
        denominador ni se cuela entre los cortos.
        """
        if self.paginas == 0:
            return ILEGIBLE
        for nombre, (lo, hi) in DEL_COSTE.items():
            if lo <= self.paginas <= hi:
                return nombre
        raise ValueError(f"{self.paginas} páginas no cae en ninguna banda")


def censar(ids: list[str], docs: Path = DOCS) -> list[Documento]:
    """Página a página, con `pypdf`. Un documento que no se puede abrir **se cuenta**."""
    exige(docs)
    from pypdf import PdfReader

    fuera: list[Documento] = []
    for i, ident in enumerate(ids, start=1):
        ruta = docs / f"{ident}.pdf"
        if not ruta.exists():
            continue
        try:
            paginas = [len((p.extract_text() or "").strip()) for p in PdfReader(ruta).pages]
        except Exception:  # un PDF que pypdf no abre no desaparece del denominador
            paginas = []
        fuera.append(
            Documento(
                external_id=ident,
                paginas=len(paginas),
                sin_texto=sum(1 for n in paginas if n == 0),
                pobres=sum(1 for n in paginas if 0 < n < UMBRAL_POBRE),
            )
        )
        if i % 200 == 0:
            print(f"    {i}/{len(ids)}…", file=sys.stderr)
    return fuera


def _ids() -> list[str]:
    man = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    return [str(d["external_id"]) for d in man["documentos"]]


@dataclass(frozen=True)
class Resumen:
    """Los totales del censo, **con los denominadores separados a propósito**.

    `con_alguna_pagina_sin_texto` y `enteros_sin_texto` son cosas distintas, y confundirlas
    es la forma barata de publicar un número más bonito. `ilegibles` es una tercera: un PDF
    que no se abre no tiene cero páginas sin texto, tiene cero páginas.
    """

    documentos: int
    paginas: int
    paginas_sin_texto: int
    paginas_pobres: int
    con_alguna_pagina_sin_texto: int
    enteros_sin_texto: int
    ilegibles: int
    por_banda: dict[str, dict[str, int]]

    def como_json(self) -> dict[str, object]:
        return {
            "instrumento": INSTRUMENTO,
            "umbral_pobre": UMBRAL_POBRE,
            "documentos": self.documentos,
            "paginas": self.paginas,
            "paginas_sin_texto": self.paginas_sin_texto,
            "paginas_pobres": self.paginas_pobres,
            "documentos_con_alguna_pagina_sin_texto": self.con_alguna_pagina_sin_texto,
            "documentos_enteros_sin_texto": self.enteros_sin_texto,
            "documentos_ilegibles": self.ilegibles,
            "por_banda": self.por_banda,
        }


def resumen(docs: list[Documento]) -> Resumen:
    """Los totales y el desglose por banda. **Denominadores explícitos.**"""
    por_banda: dict[str, Counter[str]] = {b: Counter() for b in (*DEL_COSTE, ILEGIBLE)}
    for d in docs:
        c = por_banda[d.banda]
        c["documentos"] += 1
        c["paginas"] += d.paginas
        c["sin_texto"] += d.sin_texto
        c["pobres"] += d.pobres
        c["documentos_con_alguna_sin_texto"] += 1 if d.sin_texto else 0
    return Resumen(
        documentos=len(docs),
        paginas=sum(d.paginas for d in docs),
        paginas_sin_texto=sum(d.sin_texto for d in docs),
        paginas_pobres=sum(d.pobres for d in docs),
        con_alguna_pagina_sin_texto=sum(1 for d in docs if d.sin_texto),
        enteros_sin_texto=sum(1 for d in docs if d.paginas and d.sin_texto == d.paginas),
        ilegibles=sum(1 for d in docs if d.paginas == 0),
        por_banda={b: dict(c) for b, c in por_banda.items()},
    )


def main(argv: list[str]) -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--escribir", action="store_true")
    partes.add_argument("--solo-humo", action="store_true", help="los 12 del humo")
    args = partes.parse_args(argv)

    ids = json.loads(HUMO.read_text(encoding="utf-8")) if args.solo_humo else _ids()
    docs = censar([str(x) for x in ids])
    r = resumen(docs)
    print(f"\n  {r.documentos} documentos · {r.paginas} páginas · {INSTRUMENTO}\n")
    print(f"  páginas SIN capa de texto ....... {r.paginas_sin_texto}")
    print(f"  páginas con menos de {UMBRAL_POBRE} caracteres  {r.paginas_pobres}")
    print(f"  documentos con alguna sin texto . {r.con_alguna_pagina_sin_texto}")
    print(f"  documentos enteros sin texto .... {r.enteros_sin_texto}")
    print(f"  ilegibles para pypdf ............ {r.ilegibles}\n")
    print(f"  {'banda':>9} {'docs':>6} {'pags':>7} {'sin texto':>10} {'pobres':>7}")
    for b, d in r.por_banda.items():
        print(
            f"  {b:>9} {d.get('documentos', 0):>6} {d.get('paginas', 0):>7} "
            f"{d.get('sin_texto', 0):>10} {d.get('pobres', 0):>7}"
        )
    if args.escribir:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        crudo = {
            **r.como_json(),
            "por_documento": [d.__dict__ for d in docs if d.sin_texto or d.pobres],
        }
        DESTINO.write_text(json.dumps(crudo, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n  escrito {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
