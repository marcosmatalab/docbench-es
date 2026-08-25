"""Censo de 50 documentos del BOE: lo que L3 tiene que medir ANTES de cosechar.

Tres preguntas, y cualquiera de las tres puede parar el hito:

1. **¿El XML del BOE trae CDATA o prefijos de namespace?** `from_html` se traga el
   texto de una celda con CDATA, y una etiqueta con prefijo hace desaparecer la
   tabla entera —el documento pasaría a contarse como `sin-tabla` sin que nada se
   ponga rojo—. Reproducidos los dos en el árbol limpio. Si aparecen en el corpus,
   se arregla `from_html` con su mutante **antes de bajar un documento más**.
2. **¿Cuánto ocupa en disco?** El sondeo de agosto **no guardó ni un byte**, así
   que 1.000 documentos son un tamaño que nadie ha medido.
3. **¿`from_html` ve las mismas tablas que un parser XML estricto?** Es el hueco
   que L2 destapó con `is_header`: la suite de L1 en verde y el primer consumidor
   real encontrando el fallo.

**Descubrimiento SÓLO por la API** (ADR-0031, condición 1): toda URL que se pide
sale de un campo del sumario. Nunca se construye un identificador ni se sigue un
enlace. Es lo que sostiene el argumento entero de ADR-0031.

    uv run --with pypdf python scripts/censo_boe_50.py
    uv run --with pypdf python scripts/censo_boe_50.py --n 10 --solo-xml
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Protocol

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "runs" / "censos" / "censo-boe-50.json"
API = "https://www.boe.es/datosabiertos/api/boe/sumario/"
UA = "docbench-es/0.1 (banco de extraccion documental; +https://github.com/marcosmatalab/docbench-es)"
SECCIONES = {"1", "3"}
SEMILLA = 20260823
RPS = 1.0

_ultima = 0.0
_intervalos: list[float] = []


class _Respuesta(Protocol):
    status: int


def _pide(url: str, accept: str) -> tuple[int, bytes]:
    """Una petición, respetando el ritmo declarado. Nunca en paralelo."""
    global _ultima
    if _ultima:
        espera = (1.0 / RPS) - (time.monotonic() - _ultima)
        if espera > 0:
            time.sleep(espera)
        _intervalos.append(time.monotonic() - _ultima)
    _ultima = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def _items(sumario: object) -> list[dict[str, object]]:
    """Aplana el sumario a items, arrastrando el código de sección.

    La forma real, comprobada sobre el sumario del 2026-08-03 antes de escribir
    esto: `data.sumario.diario[].seccion[].departamento[].epigrafe[].item[]`, con
    los niveles intermedios **a veces dict y a veces lista**. Y `url_pdf` **no es
    una cadena**: es un objeto con `szBytes`, `pagina_inicial`, `pagina_final` y
    `texto`, que es la URL. `url_xml` sí es cadena.

    Que `szBytes` venga en el sumario es lo que permite medir el tamaño en disco
    **sin bajar un solo PDF**: 50 peticiones menos.
    """
    fuera: list[dict[str, object]] = []

    def anda(nodo: object, seccion: str) -> None:
        if isinstance(nodo, dict):
            if "identificador" in nodo and "url_xml" in nodo:
                pdf = nodo.get("url_pdf")
                fuera.append(
                    {
                        "ident": str(nodo["identificador"]),
                        "seccion": seccion,
                        "url_xml": str(nodo["url_xml"]),
                        "url_pdf": str(pdf.get("texto", "")) if isinstance(pdf, dict) else "",
                        "bytes_pdf": int(pdf["szBytes"]) if isinstance(pdf, dict) else 0,
                        "paginas": _paginas(pdf),
                    }
                )
                return
            sub = (
                str(nodo["codigo"])
                if {"codigo", "nombre", "departamento"} <= set(nodo)
                else seccion
            )
            for v in nodo.values():
                anda(v, sub)
        elif isinstance(nodo, list):
            for x in nodo:
                anda(x, seccion)

    anda(sumario, "?")
    return fuera


def _paginas(pdf: object) -> int:
    if not isinstance(pdf, dict):
        return 0
    try:
        return int(pdf["pagina_final"]) - int(pdf["pagina_inicial"]) + 1
    except (KeyError, ValueError, TypeError):
        return 0


def _universo(desde: date, dias: int) -> list[dict[str, object]]:
    todo: list[dict[str, object]] = []
    codigos: dict[str, int] = {}
    for i in range(dias):
        f = (desde + timedelta(days=i)).strftime("%Y%m%d")
        st, body = _pide(API + f, "application/json")
        codigos[f] = st
        if st != 200:
            continue
        for it in _items(json.loads(body)):
            if it["seccion"] in SECCIONES:
                todo.append(it)
    print(f"  sumarios pedidos: {len(codigos)} · códigos {sorted(set(codigos.values()))}")
    print(f"  universo secciones I+III: {len(todo)}")
    return todo


def _mide(crudo: bytes) -> dict[str, object]:
    """Lo que hay que saber ANTES de fiarse de `from_html` sobre esto."""
    texto = crudo.decode("utf-8", "replace")
    from docbench_es.core.canonical import from_html

    tablas = from_html(texto)
    return {
        "bytes_xml": len(crudo),
        "sha256": hashlib.sha256(crudo).hexdigest(),
        "cdata": texto.count("<![CDATA["),
        "prefijo_en_tabla": len(re.findall(r"<\w+:(?:table|tr|td|th)\b", texto)),
        "prefijo_cualquiera": len(set(re.findall(r"<(\w+):\w+", texto))),
        "tablas_from_html": len(tablas),
        "tablas_regex": len(re.findall(r"<table\b", texto, re.I)),
        "celdas_from_html": sum(len(t.cells) for t in tablas),
        "celdas_regex": len(re.findall(r"<t[dh]\b", texto, re.I)),
        "cabecera_from_html": sum(sum(1 for c in t.cells if c.is_header) for t in tablas),
        "th_regex": len(re.findall(r"<th\b", texto, re.I)),
        "thead_regex": len(re.findall(r"<thead\b", texto, re.I)),
        # LÍMITE 45 por CONJUNTOS, no por totales. La igualdad de recuentos
        # —323 `<th>` y 323 `is_header`— no demuestra que sean las MISMAS celdas:
        # un `<th>` sin marcar más un `<td>` dentro de `<thead>` marcado dan el
        # mismo total. Aquí se cuentan las dos discrepancias por separado.
        **_cabeceras(texto),
    }


def _cabeceras(texto: str) -> dict[str, int]:
    """Las celdas de cabecera del XML contra las que marca `from_html`.

    `celdas_thead_no_th` es **exactamente el número que pedía el límite 45**:
    cuántas cabeceras del BOE viajaban sin marcar antes de que L2 arreglara el
    `<thead><td>`. Antes del arreglo `is_header` era `tag == "th"` a secas, así
    que una celda dentro de `<thead>` que no fuera `<th>` salía sin marcar.
    """
    dentro = 0
    for bloque in re.findall(r"<thead\b.*?</thead>", texto, re.I | re.S):
        dentro += len(re.findall(r"<td\b", bloque, re.I))
    th_fuera_de_thead = len(re.findall(r"<th\b", texto, re.I)) - sum(
        len(re.findall(r"<th\b", b, re.I))
        for b in re.findall(r"<thead\b.*?</thead>", texto, re.I | re.S)
    )
    return {
        "celdas_thead_no_th": dentro,
        "th_fuera_de_thead": th_fuera_de_thead,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=50)
    p.add_argument("--desde", default="2026-08-03")
    p.add_argument("--dias", type=int, default=3)
    args = p.parse_args()

    inicio = time.monotonic()
    desde = date.fromisoformat(args.desde)
    universo = _universo(desde, args.dias)
    if len(universo) < args.n:
        print(f"UNIVERSO INSUFICIENTE: {len(universo)} < {args.n}. Amplía --dias.")
        return 1
    muestra = random.Random(SEMILLA).sample(sorted(universo, key=lambda x: x["ident"]), args.n)

    docs: list[dict[str, object]] = []
    for i, it in enumerate(muestra, 1):
        st, crudo = _pide(it["url_xml"], "application/xml")
        fila: dict[str, object] = {**it, "http_xml": st}
        if st == 200:
            fila.update(_mide(crudo))
        docs.append(fila)
        if i % 10 == 0:
            print(f"    {i}/{args.n}")

    peticiones = args.dias + args.n  # el tamaño del PDF viene en el sumario
    reloj = time.monotonic() - inicio
    salida = {
        "condiciones": {
            "ejecutado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "desde": args.desde,
            "dias": args.dias,
            "n": args.n,
            "semilla": SEMILLA,
            "rps_declarado": RPS,
            "user_agent": UA,
            "descubrimiento": "solo API de sumarios (ADR-0031 condicion 1)",
            "peticiones": peticiones,
            "segundos_reloj": round(reloj, 1),
            # El ritmo honesto es el ESPACIADO entre peticiones, no `n/T`: con n
            # peticiones hay n-1 intervalos, así que `n/T` sobreestima en n/(n-1)
            # —con 4 peticiones en 3 s daba «1,275 rps» estando bien espaciadas—.
            "intervalo_mediano_s": round(statistics.median(_intervalos), 3)
            if _intervalos
            else None,
            "intervalo_minimo_s": round(min(_intervalos), 3) if _intervalos else None,
            "rps_real": round(1 / statistics.median(_intervalos), 3) if _intervalos else None,
        },
        "documentos": docs,
    }
    SALIDA.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n  escrito {SALIDA.relative_to(RAIZ)} · {peticiones} peticiones en {reloj:.0f} s")
    if _intervalos:
        med = statistics.median(_intervalos)
        print(
            f"  ritmo REAL: intervalo mediano {med:.3f} s = {1 / med:.3f} rps "
            f"(declarado {RPS}) · mínimo {min(_intervalos):.3f} s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
