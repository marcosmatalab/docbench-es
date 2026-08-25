"""Las 6 correcciones de transcripción de L4, **cada una con su evidencia y su regla**.

    uv run python scripts/corregir_fixtures_l4.py              # comprueba, sin escribir
    uv run python scripts/corregir_fixtures_l4.py --aplicar

## Qué separa «corregir con evidencia» de «ajustar hasta que pase»

Tres cosas, y las tres son comprobables por un tercero:

1. **La evidencia sale del PDF y nunca del XML** (ADR-0039 regla 5). Este script
   **se niega a escribir** una corrección que el PDF no respalde: comprueba que el
   texto corregido aparece en la capa de texto y que el que se transcribió **no**.
   Si el PDF no da la razón a la corrección, sale con error y no toca nada.
2. **La regla que decide cada caso se escribió ANTES de ver el caso**: ADR-0040
   reglas 4 y 5, congeladas el 25 ago 2026 antes de la primera comparación, con su
   sello en `runs/l4/congelacion_comparador.json`. Sin eso, «los acentos son
   significativos» sería una regla elegida al ver que un acento falla.
3. **Sólo se corrigen las adjudicadas como error de transcripción.** Las cinco de
   frontera —límite 31 y nota al pie— NO se tocan: no son errores de nadie, y
   corregirlas sería exactamente ajustar el fixture para que salga el número.

## Qué NO hace

No re-congela ni re-compara: eso es `sellar_l4.py` y `comparar_verdad.py`, y van
después, en ese orden. Aquí sólo se corrige, y se deja el rastro en
`runs/l4/correcciones.json`.

**El congelado original no se toca.** `runs/l4/congelacion.json` guarda las huellas
de antes de comparar y es el registro histórico: si se sobrescribiera, la cadena
«transcrito ciego → comparado → adjudicado → corregido» dejaría de ser auditable.
La re-congelación va a un fichero nuevo.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "runs" / "l3" / "docs"
FIXTURES = RAIZ / "runs" / "l4" / "fixtures"
DESTINO = RAIZ / "runs" / "l4" / "correcciones.json"

REGLA_4 = 'ADR-0040 regla 4: guion corto ≠ largo y " ≠ «. Glifos visibles distintos'
REGLA_5 = "ADR-0040 regla 5: los acentos son significativos; sólo NFC se unifica"
REGLA_17 = "ADR-0017: ningún glifo visible se altera ni se borra"

CORRECCIONES: list[dict[str, object]] = [
    {
        "fixture": "BOE-A-2026-6204-t3",
        "pos": [4, 0],
        "puse": "...",
        "el_pdf_dice": "…",
        "que_paso": "transcribí el glifo de elipsis como tres puntos. Se ven igual",
        "regla": REGLA_17,
        "por_que_no_es_del_codigo": (
            "el PDF trae U+2026 en su capa de texto, así que un extractor saca «…» y"
            " coincide con la verdad: no se le penaliza por acertar"
        ),
    },
    {
        "fixture": "BOE-A-2026-7623-t3",
        "pos": [4, 0],
        "puse": "...",
        "el_pdf_dice": "…",
        "que_paso": "el mismo caso que 6204: es la misma plantilla de anexo",
        "regla": REGLA_17,
        "por_que_no_es_del_codigo": "ídem: U+2026 en el PDF",
    },
    {
        "fixture": "BOE-A-2026-6957-t0",
        "pos": [7, 0],
        "puse": (
            "Dirección General de Agricultura y Ganadería. Departamento de Acción"
            " Climática, Alimentación y Agenda Rural. Generalitat de Cataluña."
        ),
        "el_pdf_dice": (
            "Dirección General de Agricultura y Ganadería. Departamento de Acción"
            " Climática, Alimentación y Agenda Rural. Generalitat de Catauña."
        ),
        "que_paso": (
            "AUTO-CORREGÍ UNA ERRATA DEL ORIGEN. El BOE escribe «Catauña» en el PDF y en"
            " el XML —los dos formatos coinciden— y al transcribir la arreglé sin darme"
            " cuenta. Es el error más importante de los seis: si se adjudica al revés,"
            " entra «Cataluña» en la verdad y todo extractor fiel pierde un punto"
        ),
        "regla": REGLA_17,
        "por_que_no_es_del_codigo": (
            "los dos formatos oficiales coinciden en la errata: no hay defecto del origen"
            " ni techo sobre la exactitud de L5"
        ),
    },
    {
        "fixture": "BOE-A-2026-6957-t0",
        "pos": [28, 0],
        "puse": "Ayuntamiento de Granja d'Escarp (Lleida).",
        "el_pdf_dice": "Ayuntamiento de Granja d’Escarp (Lleida).",  # noqa: RUF001
        "que_paso": "apóstrofo tipográfico U+2019 transcrito como U+0027",
        "regla": REGLA_4,
        "por_que_no_es_del_codigo": (
            "el cuerpo del mismo documento usa el recto, pero la TABLA usa el tipográfico,"
            " y la tabla es lo que se mide"
        ),
    },
    {
        "fixture": "BOE-A-2026-6957-t0",
        "pos": [31, 0],
        "puse": "Ayuntamiento de Serós (Lleida).",
        "el_pdf_dice": "Ayuntamiento de Seròs (Lleida).",
        "que_paso": (
            "acento grave U+00F2 transcrito como agudo U+00F3. El grave es la grafía catalana"
        ),
        "regla": REGLA_5,
        "por_que_no_es_del_codigo": "el PDF trae el grave; castellanicé el topónimo al copiar",
    },
    {
        "fixture": "BOE-A-2026-6957-t0",
        "pos": [32, 0],
        "puse": "Plataforma en Defensa de L'Ebre.",
        "el_pdf_dice": "Plataforma en Defensa de L’Ebre.",  # noqa: RUF001
        "que_paso": "apóstrofo tipográfico U+2019 transcrito como U+0027",
        "regla": REGLA_4,
        "por_que_no_es_del_codigo": "ídem que (28, 0)",
    },
]


def _pos(c: dict[str, object]) -> tuple[int, int]:
    """La posición de una corrección, comprobada. Un `pos` mal formado aborta aquí y
    no más adentro, cuando ya se ha escrito medio fixture."""
    bruto = c["pos"]
    if not isinstance(bruto, list) or len(bruto) != 2:
        raise TypeError(f"pos mal formado en {c.get('fixture')}: {bruto!r}")
    return int(bruto[0]), int(bruto[1])


@functools.cache
def _pdf(ident: str, modo: str) -> str:
    """**Cacheado**: las 6 correcciones tocan 3 documentos y este script llegaba a
    invocar `pdftotext` ocho veces sobre los mismos bytes. Se notaba en la puerta —
    el test del guardián costaba 0,69 s, el más caro de la suite."""
    salida = subprocess.run(
        ["pdftotext", modo, str(DOCS / f"{ident}.pdf"), "-"], capture_output=True, check=True
    )
    return re.sub(r"\s+", " ", salida.stdout.decode("utf-8", errors="replace"))


@functools.cache
def _palabras(ident: str) -> frozenset[str]:
    salida = subprocess.run(
        ["pdftotext", "-bbox", str(DOCS / f"{ident}.pdf"), "-"], capture_output=True, check=True
    )
    xml = salida.stdout.decode("utf-8", errors="replace")
    return frozenset(
        html.unescape(w) for w in re.findall(r"<word[^>]*>(.*?)</word>", xml, re.DOTALL)
    )


def respalda_el_pdf(ident: str, puse: str, corregido: str) -> tuple[bool, str]:
    """¿El PDF respalda la corrección Y desmiente lo transcrito? Las dos cosas.

    Para una cadena de **un solo token** la prueba de subcadena no vale —`'...'` está
    dentro de cualquier línea de puntos de relleno—, así que se pregunta por palabra
    suelta, que es la pregunta que corresponde a una celda de un solo token.
    """
    if " " not in corregido and " " not in puse:
        palabras = _palabras(ident)
        return (corregido in palabras and puse not in palabras), "palabra suelta (-bbox)"
    texto = _pdf(ident, "-raw")
    return (corregido in texto and puse not in texto), "subcadena en -raw colapsado"


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--aplicar", action="store_true", help="escribe. Sin esto sólo comprueba")
    args = partes.parse_args()

    registro: list[dict[str, object]] = []
    fallos = 0
    for c in CORRECCIONES:
        nombre = str(c["fixture"])
        ident = nombre.rsplit("-t", 1)[0]
        puse, corregido = str(c["puse"]), str(c["el_pdf_dice"])
        ok, como = respalda_el_pdf(ident, puse, corregido)
        fila, col = _pos(c)
        marca = "RESPALDADA" if ok else "SIN RESPALDO"
        print(f"  [{marca:<12}] {nombre} ({fila}, {col}) · {como}")
        if not ok:
            fallos += 1
            continue
        registro.append(
            {
                **c,
                "evidencia": {
                    "fuente": "el PDF, nunca el XML (ADR-0039 regla 5)",
                    "prueba": como,
                    "el_pdf_contiene_el_corregido": True,
                    "el_pdf_contiene_lo_que_puse": False,
                    "bytes_utf8_del_corregido": corregido.encode().hex(),
                },
            }
        )
    if fallos:
        print(f"\n  {fallos} correcciones SIN RESPALDO en el PDF. No se escribe nada.")
        return 1
    print(f"\n  {len(registro)} de {len(CORRECCIONES)} respaldadas por el PDF.")
    if not args.aplicar:
        print("  Sin --aplicar: no se ha escrito nada.")
        return 0

    for c in registro:
        ruta = FIXTURES / f"{c['fixture']}.json"
        fx = json.loads(ruta.read_text(encoding="utf-8"))
        fila, col = _pos(c)
        actual = fx["filas"][fila][col]
        if actual != c["puse"]:
            print(f"  ABORTA: {c['fixture']} ({fila}, {col}) ya no dice lo transcrito.")
            return 1
        fx["filas"][fila][col] = c["el_pdf_dice"]
        ruta.write_text(json.dumps(fx, indent=1, ensure_ascii=False), encoding="utf-8")
        c["sha256_despues"] = hashlib.sha256(ruta.read_bytes()).hexdigest()

    DESTINO.write_text(
        json.dumps(
            {
                "esquema": "docbench-es.correcciones-l4/1",
                "adjudicacion": "docs/adr/0039-la-adjudicacion-de-discrepancias-de-la-verdad.md",
                "reglas_del_comparador": "docs/adr/0040-las-reglas-del-comparador-de-verdad.md",
                "congelado_original": "runs/l4/congelacion.json",
                "LO_QUE_NO_SE_CORRIGE": (
                    "las 5 de FRONTERA AMBIGUA —3 de partición de línea (límite 31) y 2 de"
                    " nota al pie—. No son errores de nadie: corregirlas sería ajustar el"
                    " instrumento para que salga el número"
                ),
                "n": len(registro),
                "correcciones": registro,
            },
            indent=1,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"  Escritas. Rastro en {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
