"""Censo del corpus de L3: **lo que L4 tiene que saber ANTES de escribir `derived.py`.**

El censo de 50 documentos salvó L3 midiendo antes de bajar 2.000 ficheros. Éste es
su equivalente para L4, y la pregunta que decide el hito es la primera:

1. **¿Cuántos de los 1.000 documentos producen tablas con `SOLAPE`?** (límite 30).
   `SOLAPE` es **fatal**, así que esos documentos **no pueden tener verdad
   derivada**: `truth.derived` emitiría una tabla que `validate` rechaza. Si son el
   3%, L4 sigue igual; si son el 30%, L4 cambia entero y hay que decidir qué se
   hace con ellos **antes** de escribir una línea.
2. **`validate()` sobre TODAS las tablas del corpus**, con el reparto de hallazgos
   publicado, **fatales e informativos por separado** — mezclarlos convertiría
   `FILA_VACIA`, que es HTML legal y cotidiano en el BOE, en algo que suena a bug.

Y cuatro medidas que salen gratis en la misma pasada, porque el coste es abrir los
mil ficheros y eso ya se paga:

3. **Límite 45 re-medido sobre 1.000** en vez de sobre 50: las cabeceras que
   viajaban sin marcar. **Por CONJUNTOS y no por totales**, que es lo que hace la
   afirmación válida — «323 = 323» no demuestra que sean las mismas celdas.
4. **Límite 33**: cuántas celdas contienen `<img>`, que es lo que el sondeo contó
   sobre el documento entero y no dentro de `<table>`.
5. El **reparto por estrato** recalculado, contra el que publica el manifiesto.
6. El **reparto por banda de longitud** (ADR-0034), contra el 37/48/15 predicho.

    uv run python scripts/censo_corpus.py

**Sin red y sin PDF.** Sólo lee los XML que ya están en disco, así que se puede
repetir tantas veces como haga falta sin pedirle nada al origen.

## Precondiciones declaradas

- **El corpus tiene que estar en disco.** Si falta un XML, esto **no lo salta**:
  lo cuenta en `sin_fichero` y lo dice. Un censo incompleto que se presenta como
  completo es la misma familia que un manifiesto sin sus bytes.
- **Las cabeceras y las imágenes se cuentan con un parser, no con regex.** Un
  `<td>` dentro de `<thead>` exige saber dónde estás, y `re` no lo sabe. El parser
  es el mismo `html.parser` que usa `from_html`, así que **ve exactamente lo que
  ve el conversor** — incluido tragarse el CDATA, que es lo que hay que medir.
- **`n_tablas` del crudo contra `len(from_html(...))`** es el detector gratis del
  fallo silencioso: un prefijo de namespace hace desaparecer la tabla entera y el
  documento se contaría como «sin tabla» sin que nada se ponga rojo.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from _censo_agregado import agregar, imprimir  # noqa: E402
from docbench_es.core.canonical import validate  # noqa: E402
from docbench_es.entity import boe_xml  # noqa: E402
from fuera_de_git import exige  # noqa: E402

SALIDA = RAIZ / "runs" / "censos" / "censo-corpus-1000.json"


def columnas_declaradas(tabla: str) -> int | None:
    """Las columnas que **el propio documento declara**, o `None` si no lo dice.

    **Es una comprobación de coherencia INTERNA y sale gratis.** El origen escribe
    `<colgroup><col/>…</colgroup>`, y `from_html` deriva `n_cols` de la extensión
    de las celdas **sin mirar ese `<colgroup>` jamás** —a propósito: creérselo
    permitiría declarar columnas que nadie usa—. Así que las dos cifras salen de
    caminos independientes sobre el mismo documento, y **cuando discrepan, una de
    las dos está mal**.

    No es una anécdota: es la forma general del fallo que cazó el cierre de L3. La
    tabla de tarifas de `BOE-A-2026-7193` declaraba 4 columnas y el conversor
    producía 5 porque no terminaba el grupo de filas — y `validate` la daba por
    buena. Este detector la habría cazado sin que nadie mirase una rejilla a mano.

    `<col span="3">` cuenta 3. Sin `<colgroup>` y sin `<col>`, `None`: **no es
    cero**, y confundirlos haría que toda tabla sin `<colgroup>` saliera como
    discrepancia.
    """
    dentro = re.search(
        r"<colgroup\b.*?(?:</colgroup>|(?=<t(?:head|body|foot|r)\b))", tabla, re.S | re.I
    )
    if dentro is None:
        return None
    total = 0
    for col in re.findall(r"<col\b[^>]*>", dentro.group(0), re.I):
        span = re.search(r'span\s*=\s*"?(\d+)', col, re.I)
        total += int(span.group(1)) if span else 1
    return total or None


class _Escaner(HTMLParser):
    """Cabeceras e imágenes **con el mismo parser que `from_html`**.

    Que sea el mismo importa: si `html.parser` se traga un CDATA o pierde una
    etiqueta con prefijo, este censo lo pierde igual, y entonces mide lo que el
    conversor ve en vez de lo que el fichero pone. Medir el fichero daría una
    discrepancia que no le pasa a nadie en producción.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.th = 0
        self.thead = 0
        self.td_en_thead = 0
        self.th_fuera_de_thead = 0
        self.img_en_celda = 0
        self.celdas_solo_img = 0
        self._en_thead = 0
        self._celda: list[str] | None = None
        self._img_en_esta = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag == "thead":
            self.thead += 1
            self._en_thead += 1
        elif tag in {"td", "th"}:
            if tag == "th":
                self.th += 1
                if not self._en_thead:
                    self.th_fuera_de_thead += 1
            elif self._en_thead:
                self.td_en_thead += 1
            self._celda, self._img_en_esta = [], 0
        elif tag == "img" and self._celda is not None:
            self.img_en_celda += 1
            self._img_en_esta += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "thead":
            self._en_thead = max(0, self._en_thead - 1)
        elif tag in {"td", "th"} and self._celda is not None:
            if self._img_en_esta and not "".join(self._celda).strip():
                # LÍMITE 33: la celda cuyo ÚNICO contenido es una imagen. La verdad
                # dirá `""` y un extractor que la OCR-ee bien saca texto: se le
                # penaliza por acertar. Es la cifra que el límite pide y el sondeo
                # no midió, porque contó `<img>` sobre el documento entero.
                self.celdas_solo_img += 1
            self._celda = None

    def handle_data(self, data: str) -> None:
        if self._celda is not None:
            self._celda.append(data)


def _mide(xml: str) -> dict[str, object]:
    """Un documento. **Nunca lanza**: un XML raro es un dato, no una excepción."""
    tablas = boe_xml.tablas(xml)
    # DOS recuentos, y la diferencia importa: `codigos` cuenta TABLAS con ese
    # hallazgo —un `set` por tabla— y `lineas` cuenta HALLAZGOS. Publicar «5» sin
    # decir de qué es una cifra desnuda: una sola tabla del corpus da 183 líneas de
    # `HUECO_COLA`, así que las dos unidades difieren en dos órdenes de magnitud.
    codigos: Counter[str] = Counter()
    lineas: Counter[str] = Counter()
    tablas_fatales = 0
    con_tablas_con_celdas = con_rowspan = 0
    for t in tablas:
        ok, problemas = validate(t)
        vistos = {p.split(":", 1)[0] for p in problemas}
        codigos.update(vistos)
        lineas.update(p.split(":", 1)[0] for p in problemas)
        if t.cells:
            con_tablas_con_celdas += 1
        if any(c.rowspan > 1 for c in t.cells):
            con_rowspan += 1
        if not ok:
            tablas_fatales += 1
    escaner = _Escaner()
    escaner.feed(xml)
    escaner.close()
    rasgos = boe_xml.rasgos(xml)
    # El detector de coherencia interna: lo que el documento DECLARA contra lo que
    # el conversor PRODUCE. Se emparejan por orden, que es el mismo en los dos.
    crudas = re.findall(r"<table\b.*?</table>", xml, re.S | re.I)
    discrepancias = [
        {"tabla": i, "colgroup": dec, "n_cols": t.n_cols}
        for i, (t, cruda) in enumerate(zip(tablas, crudas, strict=False))
        if (dec := columnas_declaradas(cruda)) is not None and dec != t.n_cols and t.cells
    ]
    return {
        "n_tablas_crudo": rasgos.n_tablas,
        "n_tablas_from_html": len(tablas),
        "n_celdas": sum(len(t.cells) for t in tablas),
        "n_cabecera_from_html": sum(sum(1 for c in t.cells if c.is_header) for t in tablas),
        "tablas_fatales": tablas_fatales,
        "codigos": dict(codigos),
        "lineas": dict(lineas),
        "tablas_con_celdas": con_tablas_con_celdas,
        # El denominador HONESTO para una tasa de este defecto: sólo aquí puede
        # ocurrir. Sobre las 2.135 se diluye un factor 6,5.
        "tablas_con_rowspan": con_rowspan,
        "th": escaner.th,
        "thead": escaner.thead,
        "td_en_thead": escaner.td_en_thead,
        "th_fuera_de_thead": escaner.th_fuera_de_thead,
        "img_en_celda": escaner.img_en_celda,
        "celdas_solo_img": escaner.celdas_solo_img,
        "cdata": xml.count("<![CDATA["),
        "prefijo_en_tabla": len(re.findall(r"<\w+:(?:table|tr|td|th)\b", xml)),
        "estratos": sorted(boe_xml.estratos(rasgos)),
        "colgroup_discrepa": discrepancias,
    }


def main() -> int:
    inicio = time.monotonic()
    manifiesto = json.loads((RAIZ / "runs" / "l3" / "manifiesto.json").read_text(encoding="utf-8"))
    docs = exige(RAIZ / "runs" / "l3" / "docs")
    filas: list[dict[str, object]] = []
    sin_fichero: list[str] = []

    for i, d in enumerate(manifiesto["documentos"], 1):
        ident = str(d["external_id"])
        ruta = docs / f"{ident}.xml"
        if not ruta.is_file():
            sin_fichero.append(ident)
            continue
        fila = _mide(ruta.read_text(encoding="utf-8", errors="replace"))
        fila["external_id"] = ident
        fila["n_pages"] = d["n_pages"]
        fila["estratos_manifiesto"] = sorted(d["strata"])
        filas.append(fila)
        if i % 200 == 0:
            print(f"    {i}/{len(manifiesto['documentos'])}")

    salida = agregar(filas, sin_fichero, manifiesto, time.monotonic() - inicio)
    SALIDA.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    imprimir(salida, SALIDA.relative_to(RAIZ))
    return 1 if sin_fichero else 0


if __name__ == "__main__":
    sys.exit(main())
