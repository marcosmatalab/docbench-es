"""El reloj de la campaña de L5 contra su predicción, **como fichero**. El comando.

    uv run python scripts/error_del_estimador.py            # imprime y comprueba
    uv run python scripts/error_del_estimador.py --escribir # emite runs/l5/reloj.json

## Por qué existe: el mismo error se publicó con dos valores

`+74,5%` en `RESULTS.md` (tres veces), en la tabla de estimadores de `ESTADO.md` y en
`docs/metrics.md`; `+74,6%` en la fila de L5 de `ESTADO.md`, escrita en el commit de
cierre. **Seis copias, dos valores, y ni una de las seis salía de un fichero.**

**No son dos mediciones: son la misma división con el dividendo redondeado y sin
redondear.** El instrumento —`scripts/poblacion_l5.py`— emite **14.439,4 s**; publicarlo
como «4,01 h» y volver a segundos da 14.436 s, y ese redondeo, y sólo ése, baja el
cociente de 74,558% a 74,516%: **74,6% contra 74,5%**. El divisor no era el problema —ya
se usaba sin redondear, 8.272 s y no 2,30 h—, aunque redondearlo *también* lo mueve: con
2,30 h saldría 74,4%. Con los dos redondeos, 74,3%.

    (14.439,4 - 8.272) / 8.272 = 0,74558  ->  +74,6%      <- lo que emite el instrumento
    (14.436   - 8.272) / 8.272 = 0,74516  ->  +74,5%      <- el dividendo redondeado

## Qué es medida y qué es derivada, porque no se tratan igual

**Medido, y por tanto declarado aquí con su método:** el reloj de pared de la campaña,
`time` alrededor de `docbench run`, **n=1**, anotado al segundo. Es el único dato de este
fichero que no se puede recomputar: la campaña costó 2,30 h y no se vuelve a correr para
mirarlo (LIMITS 109). Va con su resolución, y la resolución **no cambia el titular**: con
el segundo a favor o en contra, el error sigue siendo 74,6% —±0,01 puntos—.

**Derivado, y por tanto recomputado en cada corrida de este script:** la predicción, que
sale entera de `poblacion_l5.horas()` sobre el modelo de coste de `computo_base_2hilos.json`;
y los dos errores, cada uno con su fórmula.

**Y una tercera cifra que NO es el reloj, y va al lado para que no se confunda con él:**
la suma de los `coste_ms` de `runs/l5/informe.json`, que es `perf_counter` **dentro** de
cada `extract`. Son 8.267,5 s. Los 4,5 s de diferencia son todo lo que la campaña hace
fuera de extraer —abrir el almacén, escribir los diarios— y dividir por esa cifra daría
**+74,7%**: una cuarta copia del mismo titular, con la etiqueta de otra magnitud.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from censo_paginas import paginas  # noqa: E402
from poblacion_l5 import coste_por_pagina, horas, muestra_sin_tabla, poblaciones  # noqa: E402

SALIDA = RAIZ / "runs" / "l5" / "reloj.json"
INFORME = RAIZ / "runs" / "l5" / "informe.json"

RELOJ_DE_PARED_S = 8272
"""**LA ÚNICA COPIA DEL DATO MEDIDO.** Segundos de reloj de pared de la campaña de L5.

`time` alrededor de `uv run docbench run`, **n=1**, anotado al segundo entero sobre el
árbol `819c06f` el 27 ago 2026. No es una estimación —es el reloj de una corrida
concreta— así que no lleva intervalo (ADR-0015); lleva su condición de máquina, que está
en `runs/l5/campana/sello.json`: 14 CPU visibles, carga 1,39, un solo proceso y
secuencial.

**Vive aquí y en ningún otro sitio.** Antes vivía tecleado en cuatro documentos, y de ahí
salieron las dos versiones del error.
"""

RESOLUCION_S = 1
"""Al segundo, que es como se anotó. Mueve el error ±0,01 puntos: no lo cambia."""


def prediccion_s() -> float:
    """Los segundos pre-registrados, **como los emite el instrumento y sin redondear**.

    Es `poblacion_l5.horas()` sobre los 616 documentos elegidos, o sea exactamente lo
    que imprime la línea `TOTAL de la campaña` de `scripts/poblacion_l5.py` — que la
    imprime con dos decimales de hora, y ese redondeo es el que produjo el 74,5%.
    """
    pag = paginas()
    con, _ = poblaciones()
    elegidos = con + [i for ids in muestra_sin_tabla().values() for i in ids]
    return horas(elegidos, pag, coste_por_pagina()) * 3600


def suma_de_extract_s() -> float | None:
    """`sum(coste_ms)` del informe. **No es el reloj de pared**: ver el docstring."""
    if not INFORME.exists():
        return None
    datos = json.loads(INFORME.read_text(encoding="utf-8"))
    return sum(float(e["coste_ms"]) for e in datos["extractores"].values()) / 1000


def reloj() -> dict[str, object]:
    """El fichero entero. **Cada error con su fórmula al lado, no en la prosa.**"""
    predicho, real = prediccion_s(), float(RELOJ_DE_PARED_S)
    return {
        "que": "el reloj de la campaña de L5 contra su predicción pre-registrada",
        "prediccion": {
            "instrumento": "scripts/poblacion_l5.py",
            "modelo_de_coste": "runs/l5/computo_base_2hilos.json",
            "segundos": predicho,
            "horas": predicho / 3600,
            "derivada": True,
        },
        "real": {
            "instrumento": "time alrededor de `uv run docbench run`",
            "n": 1,
            "resolucion_s": RESOLUCION_S,
            "segundos": real,
            "horas": real / 3600,
            "derivada": False,
        },
        "error_contra_lo_medido": {
            "formula": "(predicho \u2212 real) / real",
            "valor": (predicho - real) / real,
        },
        "sobra_de_la_prediccion": {
            "formula": "(real \u2212 predicho) / predicho",
            "valor": (real - predicho) / predicho,
        },
        "no_es_el_reloj": {
            "que": "suma de los coste_ms de runs/l5/informe.json: perf_counter DENTRO de extract",
            "segundos": suma_de_extract_s(),
        },
    }


def _pct(valor: float) -> str:
    return f"{valor * 100:+.1f}%".replace(".", ",")


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--escribir", action="store_true")
    args = partes.parse_args()
    datos = reloj()
    pred = datos["prediccion"]["segundos"]  # type: ignore[index]
    real = datos["real"]["segundos"]  # type: ignore[index]
    print(f"\n  pre-registrado  {pred:>12.3f} s = {pred / 3600:.6f} h   (derivado, sin redondear)")
    print(f"  real            {real:>12.3f} s = {real / 3600:.6f} h   (medido, n=1, ±1 s)")
    print(f"  error contra lo medido   {_pct(datos['error_contra_lo_medido']['valor'])}")  # type: ignore[index]
    print(f"  sobra de la predicción   {_pct(datos['sobra_de_la_prediccion']['valor'])}")  # type: ignore[index]
    otra = datos["no_es_el_reloj"]["segundos"]  # type: ignore[index]
    if otra is not None:
        print(
            f"\n  (dentro de `extract`: {otra:.3f} s. NO es el reloj:"
            f" daría {_pct((pred - otra) / otra)})"
        )
    if args.escribir:
        SALIDA.write_text(json.dumps(datos, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\n  escrito {SALIDA.relative_to(RAIZ)}\n")
        return 0
    if not SALIDA.exists():
        print(f"\n  NO EXISTE {SALIDA.relative_to(RAIZ)}. Emítelo con --escribir\n")
        return 1
    viejo = json.loads(SALIDA.read_text(encoding="utf-8"))
    if viejo != datos:
        print(f"\n  {SALIDA.relative_to(RAIZ)} ESTÁ RANCIO. Regenéralo con --escribir\n")
        return 1
    print(f"\n  {SALIDA.relative_to(RAIZ)} coincide con el instrumento.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
