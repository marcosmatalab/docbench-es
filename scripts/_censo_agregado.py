"""El agregado del censo del corpus, separado por el límite de 300 líneas.

La partición sale sola: en `censo_corpus.py` está **cómo se mide un documento** —el
parser, `from_html`, `validate`— y aquí **cómo se suman los mil y cómo se
imprimen**. Nada de aquí abre un fichero del corpus.

**Los dos repartos van separados a propósito.** Mezclar fatales con informativos
convertiría `FILA_VACIA` —que es HTML legal y cotidiano en el BOE— en algo que
suena a bug, y escondería un `SOLAPE` entre ruido.
"""

from __future__ import annotations

import sys
import time
from collections import Counter
from math import sqrt
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from docbench_es.types import HallazgoTabla  # noqa: E402
from sello import sello  # noqa: E402

Fila = dict[str, object]
BANDAS = (("corto", 1, 4), ("medio", 5, 12), ("largo", 13, 10**9))


def _n(f: Fila, k: str) -> int:
    v = f.get(k)
    return v if isinstance(v, int) else 0


def wilson(exitos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson al 95%. **Wald no vale aquí y por eso no se usa.**

    Con 3 de 338 la aproximación normal da un intervalo que incluye valores
    negativos, y una tasa negativa de documentos no significa nada. Wilson se
    comporta con proporciones pequeñas, que es exactamente el caso.

    Y lleva intervalo porque **es una estimación**: la tasa de una ventana de 34
    días leída como propiedad del BOE. La regla de oro 2 no admite estimación sin
    intervalo (ADR-0015).
    """
    if n == 0:
        return (0.0, 0.0)
    p = exitos / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    medio = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centro - medio), min(1.0, centro + medio))


def _cuantos(d: dict[str, object], k: str) -> int:
    v = d.get(k)
    return len(v) if isinstance(v, list) else 0


def _dicts(f: Fila, k: str) -> list[Fila]:
    v = f.get(k)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _lista(f: Fila, k: str) -> list[str]:
    v = f.get(k)
    return [str(x) for x in v] if isinstance(v, list) else []


def banda(paginas: int) -> str:
    for nombre, a, b in BANDAS:
        if a <= paginas <= b:
            return nombre
    return "?"


def agregar(
    filas: list[Fila],
    sin_fichero: list[str],
    manifiesto: dict[str, object],
    segundos: float,
) -> dict[str, object]:
    """El agregado, **con los dos repartos separados y los denominadores dichos**."""
    codigos: Counter[str] = Counter()
    lineas: Counter[str] = Counter()
    for f in filas:
        for destino, clave in ((codigos, "codigos"), (lineas, "lineas")):
            cod = f.get(clave)
            if isinstance(cod, dict):
                destino.update({str(k): int(x) for k, x in cod.items() if isinstance(x, int)})
    fatales = {c: n for c, n in codigos.items() if HallazgoTabla(c).es_fatal}
    informativos = {c: n for c, n in codigos.items() if not HallazgoTabla(c).es_fatal}
    con_solape = [
        f
        for f in filas
        if isinstance(f.get("codigos"), dict) and "SOLAPE" in f["codigos"]  # type: ignore[operator]
    ]
    n_tablas = sum(_n(f, "n_tablas_from_html") for f in filas)
    con_tabla = sum(1 for f in filas if _n(f, "n_tablas_from_html"))
    con_hallazgo = sorted({str(f.get("external_id")) for f in filas if f.get("codigos")})
    return {
        "condiciones": {
            "ejecutado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sello": sello(),
            "comando": "uv run python scripts/censo_corpus.py",
            "manifiesto": "runs/l3/manifiesto.json",
            "documentos_en_manifiesto": _cuantos(manifiesto, "documentos"),
            "documentos_medidos": len(filas),
            "sin_fichero": sin_fichero,
            "segundos": round(segundos, 1),
        },
        "limite_30_solape": {
            "documentos_con_solape": len(con_solape),
            "denominador_documentos": len(filas),
            # El denominador que importa: 629 de los 1.000 no tienen ni una tabla,
            # así que no pueden tener SOLAPE. Sobre los 1.000 la tasa se diluye.
            "denominador_documentos_CON_TABLA": con_tabla,
            "intervalo_wilson_95": [round(x, 5) for x in wilson(len(con_solape), con_tabla)],
            "denominador": len(filas),
            "identificadores": [f["external_id"] for f in con_solape],
            "tablas_fatales": sum(_n(f, "tablas_fatales") for f in filas),
            "tablas_totales": n_tablas,
        },
        "validate": {
            "tablas_evaluadas": n_tablas,
            "tablas_con_celdas": sum(_n(f, "tablas_con_celdas") for f in filas),
            "documentos_con_tabla": con_tabla,
            "tablas_con_rowspan_mayor_que_uno": sum(_n(f, "tablas_con_rowspan") for f in filas),
            # UNIDAD DECLARADA en el nombre de la clave, no en una nota al pie.
            "FATALES_por_TABLA": dict(sorted(fatales.items())),
            "informativos_por_TABLA": dict(sorted(informativos.items())),
            "TODOS_por_LINEA": dict(sorted(lineas.items())),
            "documentos_con_algun_hallazgo": con_hallazgo,
        },
        "limite_45_cabeceras": {
            "thead": sum(_n(f, "thead") for f in filas),
            "th": sum(_n(f, "th") for f in filas),
            "is_header_from_html": sum(_n(f, "n_cabecera_from_html") for f in filas),
            # Los DOS sumandos por separado. La igualdad de totales no demuestra
            # que sean las mismas celdas: un `<th>` sin marcar más un `<td>` de
            # `<thead>` marcado dan el mismo total.
            "td_dentro_de_thead": sum(_n(f, "td_en_thead") for f in filas),
            "th_fuera_de_thead": sum(_n(f, "th_fuera_de_thead") for f in filas),
            "documentos_con_td_en_thead": sum(1 for f in filas if _n(f, "td_en_thead")),
        },
        "limite_33_imagenes": {
            "img_dentro_de_celda": sum(_n(f, "img_en_celda") for f in filas),
            "celdas_SOLO_img": sum(_n(f, "celdas_solo_img") for f in filas),
            "documentos_afectados": sum(1 for f in filas if _n(f, "celdas_solo_img")),
        },
        "silencios": {
            "cdata": sum(_n(f, "cdata") for f in filas),
            "prefijo_en_tabla": sum(_n(f, "prefijo_en_tabla") for f in filas),
            # `<table` en el crudo contra tablas que `from_html` devuelve. Cualquier
            # diferencia es una tabla que desapareció sin que nada se pusiera rojo.
            "tablas_crudo": sum(_n(f, "n_tablas_crudo") for f in filas),
            "tablas_from_html": n_tablas,
            "documentos_con_discrepancia": [
                f["external_id"]
                for f in filas
                if _n(f, "n_tablas_crudo") != _n(f, "n_tablas_from_html")
            ],
        },
        "colgroup": {
            # LO QUE EL DOCUMENTO DECLARA CONTRA LO QUE EL CONVERSOR PRODUCE. Dos
            # caminos independientes sobre el mismo fichero: cuando discrepan, una
            # de las dos está mal, y no hace falta mirar ninguna rejilla a mano.
            "tablas_con_colgroup": sum(1 for f in filas if _n(f, "n_tablas_from_html")),
            "discrepancias": [
                {"external_id": f.get("external_id"), **d}
                for f in filas
                for d in _dicts(f, "colgroup_discrepa")
            ],
        },
        "estratos": {
            "recalculado": dict(
                Counter(e for f in filas for e in _lista(f, "estratos")).most_common()
            ),
            "del_manifiesto": dict(
                Counter(e for f in filas for e in _lista(f, "estratos_manifiesto")).most_common()
            ),
            "documentos_que_discrepan": [
                f["external_id"] for f in filas if f["estratos"] != f["estratos_manifiesto"]
            ],
        },
        "bandas": dict(Counter(banda(_n(f, "n_pages")) for f in filas).most_common()),
        "por_documento": filas,
    }


def imprimir(salida: dict[str, object], ruta: Path) -> None:
    """El resumen por pantalla. **Los porcentajes con su denominador al lado.**"""

    def bloque(k: str) -> Fila:
        v = salida.get(k)
        return v if isinstance(v, dict) else {}

    c, l30, v = bloque("condiciones"), bloque("limite_30_solape"), bloque("validate")
    l45, l33 = bloque("limite_45_cabeceras"), bloque("limite_33_imagenes")
    sil, est = bloque("silencios"), bloque("estratos")
    n = _n(l30, "denominador_documentos_CON_TABLA") or 1
    solape = _n(l30, "documentos_con_solape")
    ic = l30.get("intervalo_wilson_95")
    print(
        f"\n  {c.get('documentos_medidos')} documentos medidos en "
        f"{c.get('segundos')} s · sello {c.get('sello')}"
    )
    banda = f" IC95 [{ic[0]:.2%}, {ic[1]:.2%}]" if isinstance(ic, list) and len(ic) == 2 else ""
    todos = _n(l30, "denominador_documentos") or 1
    print(
        f"\n  LIMITE 30 · SOLAPE en {solape} de {n} documentos CON TABLA = {solape / n:.2%}{banda}"
    )
    print(f"    (sobre los {todos} del corpus: {solape / todos:.2%} — DILUIDO)")
    print(f"    tablas fatales {l30.get('tablas_fatales')} de {l30.get('tablas_totales')} tablas")
    print(
        f"\n  validate() sobre {v.get('tablas_evaluadas')} tablas "
        f"({v.get('tablas_con_celdas')} con celdas · "
        f"{v.get('tablas_con_rowspan_mayor_que_uno')} con rowspan>1)"
    )
    print(f"    FATALES, por TABLA ..: {v.get('FATALES_por_TABLA') or '{}'}")
    print(f"    informativos, x TABLA: {v.get('informativos_por_TABLA') or '{}'}")
    print(f"    TODOS, por LINEA ....: {v.get('TODOS_por_LINEA') or '{}'}")
    print(f"\n  LIMITE 45 · <td> dentro de <thead>: {l45.get('td_dentro_de_thead')}")
    print(
        f"    <th> {l45.get('th')} · is_header {l45.get('is_header_from_html')} · "
        f"<thead> {l45.get('thead')}"
    )
    print(f"\n  LIMITE 33 · celdas cuyo unico contenido es <img>: {l33.get('celdas_SOLO_img')}")
    print(f"    <img> dentro de celda: {l33.get('img_dentro_de_celda')}")
    print(
        f"\n  silencios · CDATA {sil.get('cdata')} · prefijo en tabla {sil.get('prefijo_en_tabla')}"
    )
    print(f"    tablas crudo {sil.get('tablas_crudo')} vs from_html {sil.get('tablas_from_html')}")
    cg = bloque("colgroup")
    disc = cg.get("discrepancias")
    n_disc = len(disc) if isinstance(disc, list) else 0
    print(f"\n  COLGROUP · tablas donde lo declarado != n_cols producido: {n_disc}")
    if isinstance(disc, list):
        for d in disc[:8]:
            print(f"    {d}")
    print(f"\n  estratos {est.get('recalculado')}")
    print(f"  bandas   {salida.get('bandas')}")
    print(f"\n  escrito {ruta}")
