"""¿Cumple este corpus el criterio de aceptación de L3? **El comando que lo dice.**

§16 pide *«1.000 documentos emparejados PDF/XML, con manifiesto y tasa de
descarte»*, y hasta hoy **ese criterio no tenía comando**: se cosechaba, se
miraba el JSON y se declaraba cumplido a ojo. La regla de oro 2 dice que todo
número publicado lleva su comando, y un criterio de aceptación es el número más
importante del hito.

    uv run python scripts/verificar_corpus.py runs/l3/manifiesto.json
    uv run python scripts/verificar_corpus.py runs/l3/manifiesto.json --plan runs/l3/plan.yaml

Devuelve **1 si algo falla** y lista **todos** los fallos, no el primero: quien
acaba de gastar cuarenta minutos de cosecha quiere verlo todo de una vez.

## Qué comprueba, y por qué cada cosa

| Comprobación | Qué se caería sin ella |
|---|---|
| `aceptados + descartes == intentados` | un descarte fuera del denominador |
| la tasa **con** ventana, umbral y denominador | una cifra del calendario con cara de corpus |
| atribución literal, licencias separadas | un dataset que incumple su licencia |
| procedencia completa por documento | una población no re-derivable sin volver al origen |
| `sha256` con forma y **sin repetir** | dos entradas que son el mismo fichero |
| las URLs, del dominio del origen | una URL construida a mano (ADR-0031, cond. 1) |
| el espaciado medido **≥ el declarado** | haber cosechado más rápido de lo prometido |
| el manifiesto **contra el plan congelado** | un plan escrito después de ver los resultados |
| **cada `sha256` contra los bytes en disco** | un manifiesto que describe un corpus vacío |

## Por qué la última es la que hace que esto pruebe algo

Las ocho primeras miran **el manifiesto**, y un manifiesto se escribe entero sin
que exista ni un fichero. El bug del 24 ago 2026 —`corpus.harvest` bajaba,
comprobaba coherencia y **tiraba los bytes**— habría pasado las ocho, y se cazó
mirando el disco a mano, que no es un método. La novena no pregunta si el fichero
está: **pregunta si es el que dice ser**.

**Una comprobación que no se ejecuta no es una que pasa.** Sin el directorio esto
no calla: `NO EJECUTADA` y rc=1, como la severidad homónima de `entity.conformance`.

## Precondiciones declaradas

- **El corpus en disco se nombra por identificador**: `<external_id>.pdf` y
  `.xml`, que es lo que escribe `_guardador` de `scripts/cosechar_boe.py`. Es un
  acoplamiento entre dos scripts y va escrito en los dos. Buscar «el fichero cuyo
  hash cuadre» sería circular: no diría **de quién** es lo que falta.
- **El manifiesto sólo pone hash al PDF.** `Procedencia.sha256` es el del
  `primary` de §7.1 y el XML viaja como acompañante sin hash propio, así que del
  XML se comprueba que **está y no está vacío** —la otra mitad del bug— pero no
  que sea el que se bajó. Es el límite 62.
- **Lo que NO comprueba**: que los documentos sean los correctos. Que el PDF y el
  XML digan lo mismo lo decidió `corpus.pairing`, y su tasa es lo que este script
  exige que esté publicada.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _contra_el_plan import _fallos_contra_el_plan

RAIZ = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ESQUEMA_ESPERADO = "docbench-es.manifiesto/1"

Json = dict[str, object]
"""El manifiesto viene de fuera. Tipado como `object` y no como `Any`: un `Any`
apagaría el comprobador justo en la frontera donde los datos pueden no tener la
forma esperada, que es lo que este script existe para detectar."""


def _mapa(d: Json, clave: str) -> Json:
    valor = d.get(clave)
    return valor if isinstance(valor, dict) else {}


def _lista(d: Json, clave: str) -> list[Json]:
    valor = d.get(clave)
    return [x for x in valor if isinstance(x, dict)] if isinstance(valor, list) else []


def _texto(d: Json, clave: str) -> str:
    valor = d.get(clave)
    return valor if isinstance(valor, str) else ""


def _entero(d: Json, clave: str) -> int:
    valor = d.get(clave)
    return valor if isinstance(valor, int) else -1


def _real(d: Json, clave: str) -> float | None:
    valor = d.get(clave)
    return float(valor) if isinstance(valor, int | float) else None


def _fallos_de_forma(m: Json) -> list[str]:
    """Esquema, invariante y la tasa con sus acompañantes obligatorios."""
    fuera: list[str] = []
    if _texto(m, "esquema") != ESQUEMA_ESPERADO:
        fuera.append(f"esquema {m.get('esquema')!r}, esperado {ESQUEMA_ESPERADO!r}")

    emp = _mapa(m, "emparejado")
    aceptados, descartados = _entero(emp, "aceptados"), _entero(emp, "descartados")
    intentados = _entero(emp, "intentados")
    if aceptados + descartados != intentados:
        fuera.append(
            f"no cuadra: {aceptados} aceptados + {descartados} descartados != "
            f"{intentados} intentados. Un descarte fuera del denominador"
        )
    if aceptados != len(_lista(m, "documentos")):
        fuera.append(f"dice {aceptados} aceptados y trae {len(_lista(m, 'documentos'))}")

    # ADR-0030: la tasa nunca viaja sola. Y ANTES QUE ESO: que sea la tasa. Aquí
    # sólo se comprobaban los acompañantes, así que un manifiesto que publicara
    # `tasa_descarte: 0.005` con 43 descartes de 1.043 salía CUMPLE con 0 fallos:
    # el número que da nombre al criterio de aceptación era el único sin comprobar.
    tasa = _real(emp, "tasa_descarte")
    if intentados > 0 and tasa is not None and abs(tasa - descartados / intentados) > 1e-9:
        fuera.append(
            f"la tasa publicada ({tasa:.4%}) NO es {descartados}/{intentados} "
            f"({descartados / intentados:.4%}). El número del criterio, mal"
        )
    # Y el invariante contra el DESGLOSE, no contra el total declarado: con
    # `por_causa: {}` los 43 descartes cuadraban igual y desaparecían de su causa,
    # que es la mitad que exige la regla de oro 6.
    por_causa = _mapa(emp, "por_causa")
    suma = sum(v for v in por_causa.values() if isinstance(v, int))
    if suma != descartados:
        fuera.append(
            f"{descartados} descartados pero `por_causa` suma {suma}: hay descartes "
            "sin causa del enum cerrado, y la tasa por causa es un resultado"
        )
    if _real(emp, "umbral_coherencia") is None:
        fuera.append("la tasa se publica sin `umbral_coherencia` (ADR-0030)")
    if intentados < 0:
        fuera.append("la tasa se publica sin su denominador (ADR-0030)")
    ventana = _mapa(m, "ventana")
    if not _texto(ventana, "desde") or not _texto(ventana, "hasta"):
        fuera.append("la tasa se publica sin su VENTANA (ADR-0030)")
    return fuera


def _fallos_de_licencia(m: Json) -> list[str]:
    """ADR-0033, requisitos 2 y 3: la atribución literal y las dos licencias."""
    fuera: list[str] = []
    if not _texto(m, "atribucion").strip():
        fuera.append("sin `atribucion` literal dentro: el corpus incumpliría su licencia")
    if not _texto(_mapa(m, "licencia_corpus"), "name"):
        fuera.append("sin licencia del corpus declarada")
    if not _texto(m, "licencia_codigo"):
        fuera.append("sin licencia del código, que va SEPARADA de la del corpus")
    return fuera


def _fallos_de_documentos(m: Json, dominio: str) -> list[str]:
    """ADR-0033, requisito 1: procedencia completa, y los hashes sanos."""
    fuera: list[str] = []
    vistos: dict[str, str] = {}
    for doc in _lista(m, "documentos"):
        ident = _texto(doc, "external_id") or "(sin id)"
        for campo in ("fecha_sumario", "seccion", "url_pdf", "url_xml", "cosechado_en"):
            if not _texto(doc, campo).strip():
                fuera.append(f"{ident}: sin `{campo}`, y no se reconstruye sin volver al origen")
        sha = _texto(doc, "sha256")
        if not SHA256.match(sha):
            fuera.append(f"{ident}: `sha256` con forma rara: {sha[:16]!r}")
        elif sha in vistos:
            fuera.append(f"{ident}: mismo `sha256` que {vistos[sha]} — son el mismo fichero")
        else:
            vistos[sha] = ident
        for campo in ("url_pdf", "url_xml"):
            url = _texto(doc, campo)
            if url and not url.startswith(dominio):
                fuera.append(f"{ident}: `{campo}` fuera de {dominio}: {url[:60]}")
    return fuera


def _fallos_de_disco(m: Json, docs: Path) -> list[str]:
    """Los `sha256` del manifiesto **contra los bytes reales**. No que existan.

    Que el fichero esté es lo de menos: un fichero vacío está, y el de otro
    documento también. Se comprueba que **el contenido produce el hash publicado**,
    que es lo que convierte el manifiesto en prueba y no en descripción. Los dos
    fallos van separados porque se arreglan distinto: *falta* se vuelve a bajar;
    *no es el que dice ser* significa que algo tocó el corpus tras publicarlo.
    """
    fuera: list[str] = []
    for doc in _lista(m, "documentos"):
        ident = _texto(doc, "external_id") or "(sin id)"
        pdf, declarado = docs / f"{ident}.pdf", _texto(doc, "sha256")
        if not pdf.is_file():
            fuera.append(
                f"{ident}: el manifiesto lo publica y NO ESTA EN DISCO ({pdf}). "
                "Un manifiesto sin sus bytes describe, no prueba"
            )
        elif (real := hashlib.sha256(pdf.read_bytes()).hexdigest()) != declarado:
            fuera.append(
                f"{ident}: en disco NO ES EL QUE DICE SER — el manifiesto declara "
                f"{declarado[:12]}… y los bytes dan {real[:12]}…"
            )
        xml = docs / f"{ident}.xml"
        if not xml.is_file():
            fuera.append(f"{ident}: falta su XML en disco ({xml}), y el corpus es PDF+XML")
        elif xml.stat().st_size == 0:
            fuera.append(f"{ident}: su XML esta VACIO en disco: el emparejado no existe")
    return fuera


def verificar(
    manifiesto: Json,
    plan: Json | None = None,
    docs: Path | None = None,
    ruta_plan: Path | None = None,
) -> list[str]:
    """Todos los fallos, no el primero. Lista vacía = el corpus cumple.

    `docs` a `None` **salta la comprobación de disco**, y por eso `main` no la deja
    saltar en silencio: con `None` se verifica un manifiesto, no un corpus.
    """
    dominio = _texto(plan or {}, "dominio") or "https://www.boe.es"
    fuera = (
        _fallos_de_forma(manifiesto)
        + _fallos_de_licencia(manifiesto)
        + _fallos_de_documentos(manifiesto, dominio)
    )
    if docs is not None:
        fuera += _fallos_de_disco(manifiesto, docs)
    if plan is not None:
        fuera += _fallos_contra_el_plan(manifiesto, plan, ruta_plan)
    return fuera


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("manifiesto", type=Path)
    partes.add_argument("--plan", type=Path, default=None)
    partes.add_argument(
        "--docs",
        type=Path,
        default=None,
        help="directorio del corpus en disco (por defecto, `docs/` junto al manifiesto)",
    )
    args = partes.parse_args()

    manifiesto = json.loads(args.manifiesto.read_text(encoding="utf-8"))
    plan = None
    if args.plan is not None:
        import yaml

        plan = yaml.safe_load(args.plan.read_text(encoding="utf-8"))

    emp = _mapa(manifiesto, "emparejado")
    ventana = _mapa(manifiesto, "ventana")
    print(
        f"{manifiesto.get('entidad')} · {ventana.get('desde')} a {ventana.get('hasta')} · "
        f"{emp.get('aceptados')} emparejados de {emp.get('intentados')} intentados"
    )
    print(
        f"  descarte {emp.get('tasa_descarte', 0):.2%} con umbral "
        f"{emp.get('umbral_coherencia')} · por causa: {emp.get('por_causa') or '{}'}"
    )
    print(
        f"  espaciado mediano {_mapa(manifiesto, 'ritmo').get('espaciado_mediano_s')} s · "
        f"dias sin boletin: {len(manifiesto.get('dias_sin_boletin') or [])}"
    )

    docs = args.docs or args.manifiesto.parent / "docs"
    if not docs.is_dir():
        # Una comprobación que no corre NO es una comprobación que pasa. Salir con 0
        # aquí diría «el corpus cumple» sobre un corpus que nadie ha mirado.
        print(f"\n  NO EJECUTADA  la comprobación de disco: {docs} no existe")
        print("  Pasa --docs con el directorio del corpus. Sin ella el manifiesto")
        print("  se verifica contra sí mismo, y describiría igual un corpus vacío.")
        return 1

    fallos = verificar(manifiesto, plan, docs, args.plan)
    for f in fallos:
        print(f"    FALLA  {f}")
    if plan is None:
        # No es un fallo —verificar la forma sin el plan es legítimo— pero SÍ es una
        # comprobación que no se ha hecho, y el resumen no puede sonar igual que
        # cuando sí se hizo.
        print("    NO EJECUTADA  el manifiesto contra el plan congelado: falta --plan")
    n_docs = len(_lista(manifiesto, "documentos"))
    print(f"  {n_docs} documentos comprobados byte a byte contra {docs}")
    veredicto = "NO CUMPLE" if fallos else ("CUMPLE, sin el plan" if plan is None else "CUMPLE")
    print(f"\n{veredicto} el criterio · {len(fallos)} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
