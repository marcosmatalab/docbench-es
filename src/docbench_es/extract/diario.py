"""El diario de una corrida: **una línea por unidad, escrita en cuanto termina.**

Una campaña de cuatro horas se cae. Este módulo existe para que caerse cueste **una
unidad** y no la corrida entera, y la forma más barata de conseguirlo es que el punto de
control y el resultado sean **el mismo fichero**: un JSONL por extractor, en modo
apéndice, con `flush` después de cada línea. Reanudar es leer qué identificadores ya
están y saltárselos. No hay un estado aparte que pueda desincronizarse del resultado,
porque no hay estado aparte.

El formato —y su vuelta, que es la que sostiene *«el núcleo se puede reejecutar sobre
extracciones viejas»*— vive en `extract._json`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from docbench_es.errors import ContractViolation
from docbench_es.extract._json import a_json, de_json, identificador

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from pathlib import Path

    from docbench_es.types import Extraction

__all__ = ["Diario", "Leido", "a_json", "de_json"]


@dataclass(frozen=True)
class Leido:
    """Las extracciones de un diario **y cuántas líneas no se pudieron leer**."""

    extracciones: tuple[Extraction, ...]
    ilegibles: int

    def __str__(self) -> str:
        return f"{len(self.extracciones)} extracciones · {self.ilegibles} líneas ilegibles"


@dataclass
class Diario:
    """El JSONL de UN extractor. Sabe qué ya está hecho y añade una línea por unidad."""

    ruta: Path

    def hechos(self) -> set[str]:
        """Los `external_id` que ya tienen línea. **El punto de control, leído.**

        Una línea ilegible —el corte a mitad de escritura de una corrida que murió— se
        **descarta y se rehace**, no se da por buena: media línea es media extracción.
        """
        if not self.ruta.exists():
            return set()
        fuera: set[str] = set()
        for linea in self.ruta.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            try:
                fuera.add(identificador(json.loads(linea)))
            except (ValueError, KeyError, TypeError, ContractViolation):
                continue
        return fuera

    def anotar(self, ex: Extraction) -> None:
        """Una línea, y `flush`: si el proceso muere ahora, esta unidad ya está."""
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps(a_json(ex), ensure_ascii=False) + "\n")
            f.flush()

    def leer(self) -> Leido:
        """Lo que consume el núcleo puro, **con lo que no se pudo leer al lado**.

        No devuelve un generador a propósito. Una línea cortada —el corte de una corrida
        que murió escribiendo— **se salta**, porque en la reanudación esa unidad se
        rehízo y su línea buena está más abajo; pero saltársela en silencio encogería el
        denominador sin que nadie se enterase, que es la peor forma de equivocarse aquí.
        Así que se cuentan y viajan pegadas al resultado.

        **Un documento repetido sí levanta.** El bootstrap remuestrea DOCUMENTOS (regla
        de oro 3), así que el mismo documento dos veces no es un dato de más: es una
        unidad de remuestreo duplicada, que estrecha el intervalo y publica más precisión
        de la que hay.
        """
        if not self.ruta.exists():
            return Leido((), 0)
        buenas: list[Extraction] = []
        ilegibles = 0
        for linea in self.ruta.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            try:
                buenas.append(de_json(json.loads(linea)))
            except (ValueError, KeyError, TypeError, ContractViolation):
                ilegibles += 1
        claves = [e.doc_ref.key() for e in buenas]
        repetidas = sorted({k for k in claves if claves.count(k) > 1})
        if repetidas:
            raise ContractViolation(
                f"{self.ruta}: {len(repetidas)} documentos con más de una línea "
                f"({repetidas[:5]}). El bootstrap remuestrea DOCUMENTOS: uno repetido "
                f"estrecha el intervalo y publica más precisión de la que hay"
            )
        return Leido(tuple(buenas), ilegibles)
