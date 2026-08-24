"""Lanza la cosecha del BOE segun `runs/l3/plan.yaml`. **El unico sitio con red.**

    uv run python scripts/cosechar_boe.py --piloto            # 3 dias, ~50 peticiones
    uv run python scripts/cosechar_boe.py                     # la ventana del plan
    uv run python scripts/cosechar_boe.py --reanudar runs/l3/piloto.json

**El piloto primero, y no es ceremonia.** Antes de 2.000 peticiones que no se
deshacen, el pipeline entero corre sobre 3 dias: si algo esta mal se descubre por
50 peticiones y con un manifiesto real delante, en vez de por 2.000.

**La reanudacion no desperdicia nada**: lo que ya esta en el manifiesto que se le
pase con `--reanudar` no se vuelve a bajar (ADR-0031, condicion 4), asi que el
piloto es trabajo adelantado de la cosecha completa y no un coste aparte.

## De donde sale el texto del PDF, y por que no esta en `src/`

`corpus.harvest` recibe los dos textos **inyectados**: no importa ninguna libreria
de PDF. Aqui se usa `pypdf`, que vive en `dev`. Ese texto **no puntua a nadie** —
sirve solo para decidir si el PDF y el XML son el mismo documento— asi que la regla
de oro 1 sigue en pie: esto es preparacion de corpus, no un extractor del banco.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from docbench_es.corpus.harvest import ParadaPorFallos, cosechar  # noqa: E402
from docbench_es.corpus.manifest import Procedencia, crear  # noqa: E402
from docbench_es.entity.base import cargar_perfil  # noqa: E402
from docbench_es.entity.boe import BoeAdapter  # noqa: E402
from docbench_es.entity.boe_xml import texto_plano  # noqa: E402
from docbench_es.types import DocRef, RawDoc  # noqa: E402

ILEGIBLES: list[str] = []
"""Los identificadores cuyo PDF llego y `pypdf` no supo abrir. Lista y no
contador: quien lo lea querra mirar UNO."""


def _textos(doc: RawDoc) -> tuple[str | None, str | None]:
    """`(texto_pdf, texto_xml)`. Un PDF ilegible se ANOTA y devuelve cadena vacia.

    **`None` aqui significaria «no habia PDF», y eso es falso**: el PDF llego, se
    bajo y esta en disco; lo que fallo es abrirlo. Devolver `None` lo mandaba al
    enum como `sin_pdf`, o sea a la causa que manda a mirar el origen cuando el
    problema esta en el lector de texto. Ahora sale como `pdf_sin_texto` con su
    identificador anotado aparte, que es lo que se puede afirmar sin mentir.
    """
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    try:
        lector = PdfReader(io.BytesIO(doc.primary))
        pdf = "\n".join(p.extract_text() or "" for p in lector.pages)
    except (PyPdfError, ValueError, OSError):
        ILEGIBLES.append(doc.ref.external_id)
        pdf = ""
    xml = texto_plano(doc.companions.get("xml", b"").decode("utf-8", errors="replace"))
    return pdf, xml


def _guardador(directorio: Path) -> Callable[[DocRef, RawDoc], None]:
    """Escribe cada documento ACEPTADO: el PDF y su XML, por identificador.

    Sin esto la cosecha produce un manifiesto de un corpus que no existe en ningun
    sitio, y §16 pide un corpus **descargado**. Los descartados no se guardan:
    dejarlos en disco daria un corpus distinto del que el manifiesto publica.

    **El nombre es el contrato.** `<external_id>.pdf` y `<external_id>.xml`, y de
    ahi los lee `scripts/verificar_corpus.py` para rehacer los `sha256` contra los
    bytes. Es un acoplamiento entre dos scripts, asi que va escrito en los dos: si
    cambia aqui, alli deja de encontrar el corpus y dice que falta entero.
    """
    directorio.mkdir(parents=True, exist_ok=True)

    def guardar(ref: DocRef, doc: RawDoc) -> None:
        (directorio / f"{ref.external_id}.pdf").write_bytes(doc.primary)
        (directorio / f"{ref.external_id}.xml").write_bytes(doc.companions.get("xml", b""))

    return guardar


def _procedencias(ruta: Path | None) -> dict[str, Procedencia]:
    """Lo ya cosechado, para no volver a bajarlo."""
    if ruta is None or not ruta.exists():
        return {}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    from datetime import datetime

    return {
        d["external_id"]: Procedencia(
            external_id=d["external_id"],
            fecha_sumario=date.fromisoformat(d["fecha_sumario"]),
            seccion=d["seccion"],
            url_pdf=d["url_pdf"],
            url_xml=d["url_xml"],
            sha256=d["sha256"],
            n_pages=d["n_pages"],
            strata=frozenset(d["strata"]),
            fetched_at=datetime.fromisoformat(d["fetched_at"]),
            cosechado_en=date.fromisoformat(d["cosechado_en"]),
        )
        for d in datos["documentos"]
    }


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--plan", type=Path, default=RAIZ / "runs" / "l3" / "plan.yaml")
    partes.add_argument("--piloto", action="store_true", help="3 dias del plan")
    partes.add_argument(
        "--objetivo",
        type=int,
        default=None,
        help="corta al llegar a N aceptados; en el piloto acota el gasto de peticiones",
    )
    partes.add_argument("--reanudar", type=Path, default=None)
    partes.add_argument("--salida", type=Path, default=None)
    partes.add_argument(
        "--docs",
        type=Path,
        default=None,
        help="donde se escriben los bytes; por defecto `docs/` junto al manifiesto",
    )
    args = partes.parse_args()

    if (
        args.reanudar is not None
        and args.salida is None
        and args.reanudar.name
        in {
            "manifiesto.json",
            "piloto.json",
        }
    ):
        # Reanudar leyendo `manifiesto.json` y escribir en `manifiesto.json` PISA LA
        # EVIDENCIA versionada con un manifiesto de otra corrida —otro ritmo, otros
        # dias sin boletin—. Rehidratar no es re-cosechar: quien rehidrata comprueba
        # contra el manifiesto publicado, no lo reescribe.
        print(f"NO: --reanudar {args.reanudar.name} escribiria encima de si mismo.")
        print("  Rehidratar NO reescribe el manifiesto publicado: comprueba contra el.")
        print(f"  Usa --salida otra-ruta.json, o `verificar_corpus.py {args.reanudar}`")
        print("  despues de bajar los bytes, que es lo que dice runs/l3/README.md.")
        return 2

    crudo_plan = args.plan.read_bytes()
    plan = yaml.safe_load(crudo_plan.decode("utf-8"))
    perfil = cargar_perfil(RAIZ / "entities" / "boe.yaml")
    desde = plan["ventana"]["desde"]
    hasta = desde + timedelta(days=2) if args.piloto else plan["ventana"]["hasta"]
    objetivo = args.objetivo or (None if args.piloto else int(plan["objetivo_emparejados"]))
    salida = args.salida or RAIZ / "runs" / "l3" / (
        "piloto.json" if args.piloto else "manifiesto.json"
    )
    # UN solo directorio para el piloto y para la cosecha: los 25 del piloto son
    # parte del corpus final —para eso existe `--reanudar`—, y separarlos dejaria
    # el manifiesto completo apuntando a bytes que estan en otra carpeta.
    docs = args.docs or salida.parent / "docs"

    print(f"{'PILOTO' if args.piloto else 'COSECHA'} · {desde} a {hasta} · objetivo {objetivo}")
    print(
        f"  ritmo {perfil.ritmo.rps} rps · umbral {perfil.umbral_coherencia}\n"
        f"  {perfil.ritmo.user_agent}"
    )

    adaptador = BoeAdapter(perfil)
    try:
        cosecha = cosechar(
            adaptador,
            desde=desde,
            hasta=hasta,
            textos=_textos,
            umbral_coherencia=perfil.umbral_coherencia,
            cosechado_en=date.today(),
            ya_en_manifiesto=_procedencias(args.reanudar),
            # «Esta en el manifiesto» y «esta en disco» NO son lo mismo. Sin esto,
            # rehidratar un corpus publicado —manifiesto si, bytes no— da cero
            # descargas y un `docs/` vacio.
            ya_en_disco=lambda ident: (
                (docs / f"{ident}.pdf").is_file() and (docs / f"{ident}.xml").is_file()
            ),
            objetivo=objetivo,
            guardar=_guardador(docs),
        )
    except ParadaPorFallos as parada:
        print(f"\nPARADA: {parada}")
        return 2

    manifiesto = crear(
        entidad=adaptador.id,
        plan_hash=hashlib.sha256(crudo_plan).hexdigest(),
        desde=desde,
        hasta=hasta,
        documentos=cosecha.aceptados,
        licencia=adaptador.license(),
        umbral_coherencia=perfil.umbral_coherencia,
        intentados=cosecha.intentados,
        por_causa=cosecha.por_causa,
        dias_sin_boletin=cosecha.dias_sin_boletin,
        espaciado_mediano_s=cosecha.ritmo.espaciado_mediano_s,
        espaciado_minimo_s=cosecha.ritmo.espaciado_minimo_s,
        n_espaciados=cosecha.ritmo.n_espaciados,
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(manifiesto.a_texto(), encoding="utf-8")

    if ILEGIBLES:
        print(f"\n  PDF que `pypdf` no supo abrir: {len(ILEGIBLES)} · {ILEGIBLES[:5]}")
    print(
        f"\n  intentados {cosecha.intentados} · aceptados {len(cosecha.aceptados)} · "
        f"descartes {cosecha.por_causa or '{}'} · tasa {cosecha.tasa_descarte:.2%}"
    )
    print(
        f"  bajados ahora {cosecha.descargados_ahora} · reintentos agotados "
        f"{cosecha.reintentos_agotados} · dias sin boletin {len(cosecha.dias_sin_boletin)}"
    )
    print(
        f"  espaciado mediano {cosecha.ritmo.espaciado_mediano_s} s · minimo "
        f"{cosecha.ritmo.espaciado_minimo_s} s · n={cosecha.ritmo.n_espaciados} espaciados"
    )
    ficheros = list(docs.glob("*"))
    en_disco = sum(f.stat().st_size for f in ficheros)
    n_docs = len(cosecha.aceptados)
    print(
        f"  en disco {en_disco / 1e6:.1f} MB en {len(ficheros)} ficheros"
        + (f" · {en_disco / n_docs / 1e3:.0f} KB/documento" if n_docs else "")
    )
    print(f"  manifiesto en {salida.relative_to(RAIZ)} · documentos en {docs.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
