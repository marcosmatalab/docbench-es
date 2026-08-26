"""El corredor de una campaña: N extractores sobre M documentos, **reanudable**.

Cuatro horas desatendidas es tiempo de sobra para que algo se caiga. Este módulo está
escrito con esa premisa, no contra ella, y de ahí salen sus dos reglas:

## 1 · El sello se escribe ANTES de empezar

Si se escribiera al terminar, una corrida interrumpida no sabría **de qué árbol venía**, y
lo que quedara en disco sería indistinguible de un resultado sobre un árbol que ya nadie
tiene. Se escribe primero, con el commit, los ficheros sucios, las CPU visibles, la carga
y el `sha256` de cada entrada.

Y por lo mismo, **reanudar sobre un árbol distinto se rechaza**. Es la regla que
`scripts/medir_puerta.py` ya aplica a la puerta: una serie medida mitad sobre un árbol y
mitad sobre otro no es una serie. Aquí sería peor, porque las dos mitades acaban en el
mismo fichero y en la misma media.

## 2 · El punto de control es el resultado, no un fichero aparte

Cada unidad se anota en el diario de su extractor **en cuanto termina**, y reanudar es
saltarse los identificadores que ya tienen línea. No hay un `estado.json` que pueda
desincronizarse del resultado, porque no hay un `estado.json`.

## Documento a documento, no extractor a extractor

Se carga el documento una vez y lo ven los N extractores. Se ahorran N-1 lecturas y N-1
`sha256` de 361 MB, y de paso una corrida a medias tiene **todos** los extractores sobre
un prefijo de los documentos, que es comparable — en vez de un extractor completo y tres
a cero, que no lo es.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from docbench_es.errors import ContractViolation
from docbench_es.extract.diario import Diario
from docbench_es.extract.sello import arbol, sello_de_corrida

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from docbench_es.corpus.store import Almacen
    from docbench_es.extract.base import Extractor

__all__ = ["Resumen", "correr", "sellar"]


@dataclass
class Resumen:
    """Lo que hizo un extractor, **con su denominador y su tasa de fallo**."""

    extractor: str
    version: str
    pedidas: int
    hechas: int = 0
    reanudadas: int = 0
    tablas: int = 0
    segundos: float = 0.0
    por_causa: dict[str, int] = field(default_factory=dict)

    @property
    def fallidas(self) -> int:
        return sum(self.por_causa.values())

    def __str__(self) -> str:
        tasa = f"{100 * self.fallidas / self.pedidas:.1f}%" if self.pedidas else "n/a"
        causas = ", ".join(f"{c}={n}" for c, n in sorted(self.por_causa.items())) or "ninguna"
        return (
            f"{self.extractor} {self.version}: {self.hechas} hechas + {self.reanudadas} "
            f"ya estaban, de {self.pedidas} · {self.tablas} tablas · "
            f"{self.segundos:.1f} s · fallo {tasa} ({causas})"
        )


def sellar(destino: Path, que: str, entradas: dict[str, Path], extra: dict[str, object]) -> Path:
    """Escribe el sello **antes de la primera unidad**, o rechaza reanudar sobre otro árbol.

    Devuelve la ruta del sello. Si ya había uno y el árbol se movió, levanta: la
    alternativa —anotarlo y seguir— produce un fichero de resultados cuya mitad no se
    puede atribuir a ningún commit, y ésa es la clase de número que este repo llama
    irrepetible en vez de reproducible.
    """
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / "sello.json"
    ahora = sello_de_corrida(que, entradas, None)
    ahora.update(extra)
    if ruta.exists():
        antes = json.loads(ruta.read_text(encoding="utf-8"))
        ahora_arbol = arbol()
        movido = {k: (antes.get(k), v) for k, v in ahora_arbol.items() if antes.get(k) != v}
        if movido:
            raise ContractViolation(
                f"la corrida de {ruta} empezó sobre otro árbol: {movido}. Una campaña "
                f"medida mitad sobre un árbol y mitad sobre otro no es una campaña. "
                f"Deja el árbol quieto, o borra {destino} y empieza de nuevo"
            )
        return ruta
    ruta.write_text(json.dumps(ahora, indent=1, ensure_ascii=False), encoding="utf-8")
    return ruta


def correr(
    extractores: Sequence[Extractor],
    almacen: Almacen,
    ids: Sequence[str],
    destino: Path,
    *,
    que: str,
    entradas: dict[str, Path],
    eco: Callable[[str], None] = print,
    cada: int = 25,
) -> list[Resumen]:
    """La campaña entera. Devuelve un `Resumen` por extractor, en el orden en que entraron.

    `extract` no lanza —lo hace cumplir la suite de conformidad—, así que aquí no hay
    `except` alrededor de la extracción: un fallo llega como `Extraction(failed=True)` y
    **se cuenta**. Lo que sí puede levantar es el almacén, y debe: un corpus que no cuadra
    con su manifiesto no da una nota mala, da un número no atribuible.
    """
    if not extractores:
        raise ContractViolation("una campaña sin extractores no es una campaña vacía: es un error")
    ruta_sello = sellar(
        destino,
        que,
        entradas,
        {
            "extractores": [{"id": e.id, "version": e.version} for e in extractores],
            "documentos": len(ids),
            "unidades": len(ids) * len(extractores),
        },
    )
    eco(f"  sello escrito ANTES de empezar: {ruta_sello}")

    diarios = {e.id: Diario(destino / f"{e.id}.jsonl") for e in extractores}
    hechos = {e.id: diarios[e.id].hechos() for e in extractores}
    resumenes = {
        e.id: Resumen(extractor=e.id, version=e.version, pedidas=len(ids)) for e in extractores
    }
    for e in extractores:
        ya = len(hechos[e.id] & set(ids))
        resumenes[e.id].reanudadas = ya
        eco(f"  {e.id}: {ya} de {len(ids)} ya estaban en {diarios[e.id].ruta.name}")

    arranque = time.monotonic()
    for i, ident in enumerate(ids, start=1):
        pendientes = [e for e in extractores if ident not in hechos[e.id]]
        if not pendientes:
            continue
        doc = almacen.cargar(ident)
        for extractor in pendientes:
            reloj = time.monotonic()
            ex = extractor.extract(doc)
            diarios[extractor.id].anotar(ex)
            r = resumenes[extractor.id]
            r.hechas += 1
            r.tablas += len(ex.tables)
            r.segundos += time.monotonic() - reloj
            if ex.failed and ex.failure_reason is not None:
                r.por_causa[ex.failure_reason] = r.por_causa.get(ex.failure_reason, 0) + 1
        if i % cada == 0 or i == len(ids):
            transcurrido = time.monotonic() - arranque
            eco(f"  {i}/{len(ids)} documentos · {transcurrido:.0f} s")
    return [resumenes[e.id] for e in extractores]
