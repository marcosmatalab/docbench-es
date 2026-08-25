"""B5-bis · Cuánto cuesta correr los CAROS. El comando.

    uv run --extra extract-local python scripts/computo_l5.py          # sigue donde iba
    uv run --extra extract-local python scripts/computo_l5.py --maximo 6
    uv run python scripts/computo_l5.py --informe                      # sin medir nada

## Por qué este script existe aparte del humo

`humo_l5.py` midió **`pdfplumber`, el más barato de los ocho**: 0,522 s/documento. De
ahí a *«los ocho sobre los mil caben»* hay una extrapolación desde el suelo, y no es de
matiz: `pdfplumber` y `pymupdf4llm` son parseo puro, **`docling` y `marker` cargan
modelos**, `camelot` detecta por página, `tesseract` es OCR y `grobid` es un servicio.

**El coste de OCR y de detección escala con PÁGINAS, no con documentos**, así que
medirlo sólo en cortos daría un techo falso. Por eso la muestra cubre **las tres bandas
de longitud** y el resultado se publica en **segundos por documento Y por página**: es
lo que hace que el total salga de **sumar** y no de multiplicar el suelo por ocho.

La regla de decisión —**si no cabe, se recortan EXTRACTORES, no documentos**— está
congelada en `runs/l5/computo.yaml`, **escrita y commiteada antes de correr esto**.

## Cómo está partido, y por qué

Una unidad = **un extractor sobre un documento, en su propio proceso** (ver
`unidad_computo.py`), bajo el gobernador térmico de `gobernador.py` y dentro del sobre
declarado en `runs/l5/termica.yaml`. Cada unidad terminada se escribe en el punto de
control, así que esto **se puede matar en cualquier segundo y continuar** sin repetir
nada. Las unidades van en **vueltas**: la primera pasada ya cubre los cuatro
extractores por las tres bandas, así que un corte temprano no deja un hueco de forma.

La moneda primaria son **segundos de CPU**, no de reloj: el gobernador para el proceso
con `SIGSTOP` y eso corrompe el reloj y no la CPU. El porqué está en `termica.yaml`.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))

from gobernador import Muestreo, Registro, Termica, correr, descansa  # noqa: E402
from informe_computo import informe, numero  # noqa: E402
from termometro import leer  # noqa: E402
from unidad_computo import EXTRACTORES  # noqa: E402

DOCS = RAIZ / "runs" / "l3" / "docs"
SOBRE = RAIZ / "runs" / "l5" / "termica.yaml"
PUNTO = RAIZ / "runs" / "l5" / "computo.json"
BANDAS = {"corto": (1, 4), "medio": (5, 12), "largo": (13, 10_000)}
POR_BANDA = 4


@dataclass
class Estado:
    """El punto de control. Lo que hace que esto se pueda matar y continuar."""

    medidas: list[Registro] = field(default_factory=list)
    termica: Registro = field(default_factory=dict)

    @classmethod
    def cargar(cls) -> Estado:
        if not PUNTO.exists():
            return cls()
        crudo = json.loads(PUNTO.read_text(encoding="utf-8"))
        if not isinstance(crudo, dict):
            raise TypeError(f"{PUNTO} no contiene un objeto JSON")
        medidas = [m for m in crudo.get("medidas", []) if isinstance(m, dict)]
        termica = crudo.get("termica", {})
        return cls(medidas, termica if isinstance(termica, dict) else {})

    def guardar(self) -> None:
        PUNTO.write_text(
            json.dumps(
                {
                    "regla": "runs/l5/computo.yaml",
                    "sobre": "runs/l5/termica.yaml",
                    "medidas": self.medidas,
                    "termica": self.termica,
                },
                indent=1,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def muestra() -> list[tuple[str, int, str]]:
    """~12 documentos, cuatro por banda. **Los más largos de cada banda**, a propósito:
    si el coste escala con páginas, medir el extremo de cada banda da el techo de la
    banda y no su suelo."""
    man = json.loads((RAIZ / "runs" / "l3" / "manifiesto.json").read_text(encoding="utf-8"))
    docs = [d for d in man["documentos"] if (DOCS / f"{d['external_id']}.pdf").exists()]
    fuera = []
    for banda, (lo, hi) in BANDAS.items():
        dentro = sorted(
            (d for d in docs if lo <= int(d["n_pages"]) <= hi),
            key=lambda d: -int(d["n_pages"]),
        )
        fuera += [(d["external_id"], int(d["n_pages"]), banda) for d in dentro[:POR_BANDA]]
    return fuera


def unidades(docs: list[tuple[str, int, str]]) -> list[tuple[str, str, int, str]]:
    """El orden de trabajo: por VUELTAS, no por extractor.

    La primera vuelta son 12 unidades que ya cubren los cuatro extractores por las tres
    bandas. Si esto se corta a la mitad —y está pensado para poder cortarse—, lo medido
    sigue teniendo la forma completa en vez de cuatro extractores y una sola banda.
    """
    por_banda: dict[str, list[tuple[str, int, str]]] = {b: [] for b in BANDAS}
    for ident, paginas, banda in docs:
        por_banda[banda].append((ident, paginas, banda))
    fuera = []
    for vuelta in range(POR_BANDA):
        for extractor in EXTRACTORES:
            for banda in BANDAS:
                if vuelta < len(por_banda[banda]):
                    ident, paginas, _ = por_banda[banda][vuelta]
                    fuera.append((extractor, ident, paginas, banda))
    return fuera


def sobre(vigilado: bool) -> tuple[Termica, dict[str, float]]:
    """El sobre térmico, LEÍDO de `runs/l5/termica.yaml`. Un número derivado no se teclea."""
    d = yaml.safe_load(SOBRE.read_text(encoding="utf-8"))
    lim, carga = d["limites"], d["carga"]
    t = Termica(
        hilos=int(carga["hilos_con_termometro" if vigilado else "hilos_sin_termometro"]),
        techo=float(lim["techo_c"]),
        reanudar=float(lim["reanudar_c"]),
        objetivo_media=float(lim["objetivo_media_c"]),
        vigilado=vigilado,
    )
    ritmo = {
        "base": float(carga["descanso_base"]) if vigilado else 1.0,
        "tope": float(carga["descanso_tope_s"]),
        "unidad": float(carga["tope_unidad_min"]) * 60.0,
    }
    return t, ritmo


def factor_de_descanso(base: float, actual: float, media: float | None, objetivo: float) -> float:
    """La pausa se alarga si la media de la sesión pasa del objetivo y se acorta si va
    holgada. Es el único lazo que controla la MEDIA; el pico lo controla el `SIGSTOP`."""
    if media is None:
        return actual
    if media > objetivo:
        return min(actual * 1.4, 4.0)
    if media < objetivo - 6.0:
        return max(base, actual / 1.3)
    return actual


def _sin_termometro(motivo: str) -> int:
    print(f"\n  SIN TERMÓMETRO · {motivo}\n")
    print("  No voy a correr un guardián de 80 °C que no puede leer 80 °C.")
    print("  Abre HWiNFO64 en modo Sensors-only, clic derecho sobre la fila")
    print("  «CPU (Tctl/Tdie)» → «Add to Registry», y vuelve a lanzar esto.")
    print("  O acepta correr a ciegas, con 2 hilos y sin acotar el pico:")
    print("      uv run --extra extract-local python scripts/computo_l5.py --sin-termometro\n")
    return 2


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="B5-bis · el coste de los caros")
    ap.add_argument("--maximo", type=int, default=0, help="corta tras N unidades")
    ap.add_argument("--informe", action="store_true", help="sólo imprime lo ya medido")
    ap.add_argument(
        "--sin-termometro",
        action="store_true",
        help="acepta correr a ciegas, con 2 hilos y sin acotar el pico",
    )
    args = ap.parse_args(argv)

    estado = Estado.cargar()
    if args.informe:
        informe(estado)
        return 0

    lectura = leer()
    if not lectura and not args.sin_termometro:
        return _sin_termometro(lectura.motivo)

    t, ritmo = sobre(vigilado=bool(lectura))
    base = factor = ritmo["base"]

    # DOS CORRIDAS DISTINTAS NO SE PRESENTAN COMO UNA. El coste depende de los hilos
    # y de si el gobernador paró el proceso: continuar un punto de control medido con
    # otra carga daría una mediana sobre dos poblaciones. Se detecta y se para.
    otras = sorted({int(numero(m, "hilos")) for m in estado.medidas} - {t.hilos})
    if otras and not args.mezclar:
        print(
            f"\n  EL PUNTO DE CONTROL TIENE MEDIDAS CON {otras} HILOS y ahora tocarían "
            f"{t.hilos}.\n  Serían dos poblaciones bajo una sola mediana. O empiezas "
            f"limpio:\n      rm {PUNTO.relative_to(RAIZ)}\n  o lo aceptas a sabiendas "
            "y queda anotado en cada registro:  --mezclar\n"
        )
        return 3

    docs = muestra()
    hechas = {(m.get("extractor"), m.get("documento")) for m in estado.medidas}
    pendientes = [u for u in unidades(docs) if (u[0], u[1]) not in hechas]
    print(
        f"\n  {len(docs)} documentos, {sum(p for _, p, _ in docs)} páginas · "
        f"{len(hechas)} unidades hechas, {len(pendientes)} pendientes"
    )
    print(
        f"  térmica: {t.hilos} hilos · techo {t.techo:.0f} °C · reanudar "
        f"{t.reanudar:.0f} °C · media objetivo {t.objetivo_media:.0f} °C · "
        f"vigilado {'SÍ' if t.vigilado else 'NO'} · tope {ritmo['unidad'] / 60:.0f} min"
    )
    print(
        f"  ahora mismo: {lectura.etiqueta} {lectura.grados:.1f} °C\n"
        if lectura
        else "  a ciegas: no se afirma ningún grado en el informe\n"
    )

    sesion = Muestreo()
    for i, (extractor, ident, paginas, banda) in enumerate(pendientes, 1):
        if args.maximo and i > args.maximo:
            print(
                f"\n  corte por --maximo {args.maximo}. Quedan "
                f"{len(pendientes) - args.maximo} unidades pendientes."
            )
            break
        unidad = Muestreo()
        t0 = time.perf_counter()
        print(
            f"  [{i}/{len(pendientes)}] {extractor} · {ident} ({banda}, {paginas} pág)", flush=True
        )
        registro = correr(extractor, ident, t, unidad, ritmo["unidad"])
        trabajo = time.perf_counter() - t0
        sesion.grados.extend(unidad.grados)
        media = statistics.fmean(sesion.grados) if sesion.grados else None
        factor = factor_de_descanso(base, factor, media, t.objetivo_media)
        registro |= {
            "paginas": paginas,
            "banda": banda,
            "hilos": t.hilos,
            "temperatura": unidad.resumen(),
            "descanso_factor": round(factor, 2),
        }
        estado.medidas.append(registro)
        estado.termica = {
            "hilos": t.hilos,
            "techo_c": t.techo,
            "reanudar_c": t.reanudar,
            "vigilado": t.vigilado,
            "sesion": sesion.resumen(),
        }
        estado.guardar()
        print(
            f"      {numero(registro, 'cpu_s'):.1f} s CPU · "
            f"{numero(registro, 'reloj_s'):.1f} s reloj · {registro['pausas']} pausas · "
            f"{unidad.resumen()}",
            flush=True,
        )
        pausa = descansa(trabajo, factor, sesion, ritmo["tope"])
        cola = (
            f" · media de sesión {statistics.fmean(sesion.grados):.1f} °C" if sesion.grados else ""
        )
        print(f"      descanso {pausa:.0f} s (x{factor:.2f}){cola}", flush=True)

    informe(estado)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
