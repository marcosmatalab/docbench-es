"""Genera `tests/fixtures/pubtabnet/casos.json` con la implementación de REFERENCIA.

Se ejecuta **a mano y una sola vez**; el fixture que produce queda congelado. No
corre en la puerta: necesita `apted`, `distance` y `lxml`, que son de la
referencia y no de este proyecto —el núcleo es puro y no depende de ellas—.

    uv run --with apted --with distance --with lxml \\
        python scripts/pubtabnet_golden.py

Qué escribe, y por qué dos juegos de números:

- **`canonico`** — la referencia sobre el **render canónico** de las mismas
  tablas. Es el golden del criterio de aceptación: los dos lados ven el MISMO
  contenido, así que lo que se compara es el algoritmo y no la convención de
  normalización ni la forma del HTML. Ver ADR-0020.
- **`original`** — la referencia sobre el HTML crudo de PubTabNet. No es un
  golden: es la medida de **cuánto mueven el número** las seis normalizaciones de
  L1 más la forma canónica. Se publica en `RESULTS.md` para que la decisión de
  ADR-0020 tenga precio visible en vez de ser una nota al pie.

La referencia se descarga en el momento y **no se redistribuye**: su código es
Apache-2.0 y sus casos también, pero copiar su `metric.py` al repo obligaría a
mantenerlo. Se copian los CASOS, que son datos, con su procedencia.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ancla import unica
from docbench_es.core.canonical import from_html
from docbench_es.core.teds import a_html
from docbench_es.types import CanonicalTable

RAIZ = Path(__file__).resolve().parents[1]
FIXTURES = RAIZ / "tests" / "fixtures" / "pubtabnet"
BASE = "https://raw.githubusercontent.com/ibm-aur-nlp/PubTabNet/master/src/"

# La huella EXACTA del `metric.py` con el que se generó el golden congelado.
# `master` es una rama MÓVIL: sin esto, el día que IBM toque su `metric.py` este
# script generaría un golden distinto y «reproducible» seguiría pareciendo cierto.
# Y ojo con el orden de las garantías: **la huella es la que manda**, no una URL
# fijada a un commit. Una URL con commit sigue confiando en que el servidor
# devuelva los mismos bytes; la huella lo comprueba.
HUELLA_METRIC_PY = "a9aedd313678b42e55b06c4b0a365d658ef495aaf3abb7fd6012a6e9f334f9f9"
VACIA = "<html><body><table></table></body></html>"


class Evaluador(Protocol):
    def evaluate(self, pred: str, true: str) -> float: ...


def _referencia() -> tuple[Evaluador, Evaluador]:
    """Baja `metric.py` y lo carga, recortado a lo que L2 valida.

    Se le quitan los imports de `parallel` y `tqdm` y el `batch_evaluate` que los
    usa. **La lógica de `evaluate`, `CustomConfig` y `load_html_tree` no se toca
    ni una línea**: es lo que se está validando.
    """
    bytes_crudos = urllib.request.urlopen(BASE + "metric.py", timeout=30).read()
    huella = hashlib.sha256(bytes_crudos).hexdigest()
    if huella != HUELLA_METRIC_PY:
        raise SystemExit(
            f"`metric.py` de PubTabNet ha CAMBIADO.\n"
            f"  esperada: {HUELLA_METRIC_PY}\n"
            f"  recibida: {huella}\n"
            "El golden congelado se generó con la otra. Antes de regenerar nada: mira el\n"
            "diff, decide si el cambio afecta a `evaluate`/`CustomConfig`/`load_html_tree`,\n"
            "y si se acepta, actualiza HUELLA_METRIC_PY y dilo en CHANGELOG."
        )
    crudo = bytes_crudos.decode()
    recortado = crudo.replace("from parallel import parallel_process\n", "").replace(
        "from tqdm import tqdm\n", ""
    )
    # Por `unica` y no por `.index`: si el ancla desapareciera, `.index` revienta,
    # pero si apareciera DOS veces cortaría por la primera y se llevaría por
    # delante media clase sin avisar. Es la misma clase de fallo que duplicó 230
    # líneas de `RESULTS.md`. Ver `scripts/ancla.py`.
    recortado = recortado[: unica(recortado, "    def batch_evaluate(")]
    espacio: dict[str, object] = {}
    exec(compile(recortado, "metric.py de PubTabNet", "exec"), espacio)
    teds_cls = espacio["TEDS"]
    return teds_cls(), teds_cls(structure_only=True)  # type: ignore[operator]


def _primera(html: str) -> CanonicalTable | None:
    tablas = from_html(html)
    return tablas[0] if tablas else None


def _serializar(t: CanonicalTable | None) -> dict[str, object] | None:
    if t is None:
        return None
    return {
        "cells": [[c.row, c.col, c.rowspan, c.colspan, c.text, c.is_header] for c in t.cells],
        "n_rows": t.n_rows,
        "n_cols": t.n_cols,
    }


# Casos límite escritos a mano. No salen de PubTabNet: salen de lo que encontró
# `hypothesis` y de las decisiones de ADR-0021, y están aquí para que cada
# afirmación de los docstrings tenga un número de la REFERENCIA detrás en vez de
# uno calculado por el código que se está validando.
LIMITE = {
    "teds_negativo": (
        "<html><body><table><thead><tr><td></td><td></td><td></td><td></td>"
        "</tr></thead></table></body></html>",
        '<html><body><table><thead><tr><td rowspan="2"></td></tr></thead>'
        "<tbody><tr></tr><tr><td></td></tr></tbody></table></body></html>",
    ),
    "hueco_contra_completa": (
        "<html><body><table><tbody><tr><td>a</td><td>b</td></tr>"
        "<tr><td>c</td></tr></tbody></table></body></html>",
        "<html><body><table><tbody><tr><td>a</td><td>b</td></tr>"
        "<tr><td>c</td><td>d</td></tr></tbody></table></body></html>",
    ),
    "celda_vacia_contra_completa": (
        "<html><body><table><tbody><tr><td>a</td><td>b</td></tr>"
        "<tr><td>c</td><td></td></tr></tbody></table></body></html>",
        "<html><body><table><tbody><tr><td>a</td><td>b</td></tr>"
        "<tr><td>c</td><td>d</td></tr></tbody></table></body></html>",
    ),
    "celda_vacia_contra_hueco": (
        "<html><body><table><tbody><tr><td>a</td><td>b</td></tr>"
        "<tr><td>c</td><td></td></tr></tbody></table></body></html>",
        "<html><body><table><tbody><tr><td>a</td><td>b</td></tr>"
        "<tr><td>c</td></tr></tbody></table></body></html>",
    ),
    # Los dos siguientes existen para documentar que la forma canónica ERASE una
    # distinción que la referencia sí ve, y que eso es lo que se quiere: un
    # extractor no debe pagar por omitir un <tbody>. Su `teds` canónico es 1,0 y
    # su `referencia_sobre_el_crudo` es 0,667, y esa pareja de números ES la
    # evidencia de ADR-0021.
    "tbody_de_mas": (
        "<html><body><table><tr><td>a</td></tr></table></body></html>",
        "<html><body><table><tbody><tr><td>a</td></tr></tbody></table></body></html>",
    ),
    "th_donde_va_td": (
        "<html><body><table><tbody><tr><th>a</th></tr></tbody></table></body></html>",
        "<html><body><table><tbody><tr><td>a</td></tr></tbody></table></body></html>",
    ),
}


def _limite(completo: Evaluador, estructura: Evaluador) -> dict[str, object]:
    """Los casos límite, con lo que dice la REFERENCIA sobre cada uno.

    Incluido el que revienta: `<table></table>` contra sí mismo divide por cero
    nodos. Se registra la excepción en vez de esconderla, porque es la razón de
    que §12 mande sobre la referencia en los degenerados.
    """
    salida: dict[str, object] = {}
    for nombre, (pred, gold) in LIMITE.items():
        t_pred, t_gold = _primera(pred), _primera(gold)
        html_pred = a_html(t_pred) if t_pred else VACIA
        html_gold = a_html(t_gold) if t_gold else VACIA
        salida[nombre] = {
            "pred": pred,
            "gold": gold,
            # Misma disciplina que los 20 casos (ADR-0020): la referencia recibe
            # el render canónico, no el HTML crudo. Si no, se compararían
            # contenidos distintos y el número no diría nada del algoritmo.
            "teds": completo.evaluate(html_pred, html_gold),
            "teds_s": estructura.evaluate(html_pred, html_gold),
            "referencia_sobre_el_crudo": completo.evaluate(pred, gold),
        }
    vacia = "<html><body><table></table></body></html>"
    try:
        resultado: object = completo.evaluate(vacia, vacia)
    except ZeroDivisionError as e:
        resultado = f"{type(e).__name__}: {e}"
    salida["dos_vacias"] = {"pred": vacia, "gold": vacia, "referencia": resultado}
    return salida


def main() -> int:
    completo, estructura = _referencia()
    casos: dict[str, object] = {}
    for nombre in ("sample_gt.json", "sample_pred.json"):
        destino = FIXTURES / nombre
        if not destino.exists():
            destino.write_bytes(urllib.request.urlopen(BASE + nombre, timeout=30).read())
    gt = json.loads((FIXTURES / "sample_gt.json").read_text())
    pred = json.loads((FIXTURES / "sample_pred.json").read_text())

    for clave in sorted(gt):
        t_gold = _primera(gt[clave]["html"])
        t_pred = _primera(pred.get(clave, ""))
        html_gold = a_html(t_gold) if t_gold else VACIA
        html_pred = a_html(t_pred) if t_pred else VACIA
        casos[clave] = {
            "gold": _serializar(t_gold),
            "pred": _serializar(t_pred),
            "html_canonico_gold": html_gold,
            "html_canonico_pred": html_pred,
            "canonico": {
                "teds": completo.evaluate(html_pred, html_gold),
                "teds_s": estructura.evaluate(html_pred, html_gold),
            },
            "original": {
                "teds": completo.evaluate(pred.get(clave, ""), gt[clave]["html"]),
                "teds_s": estructura.evaluate(pred.get(clave, ""), gt[clave]["html"]),
            },
        }
    (FIXTURES / "casos.json").write_text(json.dumps(casos, indent=1, ensure_ascii=False))
    (FIXTURES / "casos_limite.json").write_text(
        json.dumps(_limite(completo, estructura), indent=1, ensure_ascii=False)
    )
    print(f"escritos {len(casos)} casos en {FIXTURES / 'casos.json'}")
    for clave, caso in list(casos.items())[:3]:
        c, o = caso["canonico"], caso["original"]  # type: ignore[index]
        print(f"  {clave:<26} canonico={c['teds']:.6f}  original={o['teds']:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
