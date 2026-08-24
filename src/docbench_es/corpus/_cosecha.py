"""Los tipos de resultado de la cosecha y su condición de parada.

Separado de `harvest.py` por el límite de 300 líneas del repo, y la partición sale
sola: allí está **cómo se cosecha** —el recorrido, los reintentos, la caché— y aquí
**qué sale de la cosecha** y cuándo hay que parar. Lo de aquí no toca la red y se
prueba con enteros.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

from docbench_es.corpus.manifest import Procedencia
from docbench_es.errors import AdapterError, ContractViolation

__all__ = ["MINIMO_PARA_PARAR", "UMBRAL_PARADA", "Cosecha", "ParadaPorFallos", "Ritmo"]


UMBRAL_PARADA = 0.05
"""Fracción de documentos intentados que puede agotar reintentos antes de parar."""

MINIMO_PARA_PARAR = 20
"""Documentos intentados por debajo de los cuales la fracción no significa nada.

Sin este suelo **el primer documento que fallara pararía la cosecha**: 1 de 1 es el
100%. Mismo argumento por el que una tasa sobre n=3 no se publica."""


class ParadaPorFallos(AdapterError):
    """El origen falla más de lo tolerado: **se para y se pregunta.**

    Hereda de `AdapterError` —código 4— porque no es un resultado de medición: es
    que no se puede llegar al corpus en condiciones. Seguir cosechando produciría
    mil documentos de los que una parte desconocida faltan por una causa que nadie
    ha mirado.
    """


@dataclass(frozen=True)
class Ritmo:
    """El ritmo REAL, medido como espaciado. Nunca como `N/T`."""

    espaciado_mediano_s: float | None
    espaciado_minimo_s: float | None
    n_peticiones: int


@dataclass(frozen=True)
class Cosecha:
    """Lo que salió de una ventana. **Cuadra o no se construye.**"""

    intentados: int
    aceptados: tuple[Procedencia, ...]
    por_causa: Mapping[str, int]
    dias_sin_boletin: tuple[date, ...]
    ritmo: Ritmo
    reintentos_agotados: int
    descargados_ahora: int = 0
    """Bajados **en esta corrida**: es trabajo, no corpus. Los heredados del
    manifiesto cuentan en `aceptados`, no aquí."""

    def __post_init__(self) -> None:
        descartes = sum(self.por_causa.values())
        if len(self.aceptados) + descartes != self.intentados:
            raise ContractViolation(
                f"la cosecha no cuadra: {len(self.aceptados)} + {descartes} != "
                f"{self.intentados}. Un documento que sale sin contarse se lleva por "
                "delante el denominador de la tasa que se publica"
            )

    @property
    def tasa_descarte(self) -> float:
        """Sin intervalo: es un censo (ADR-0015). **Y nunca se publica sola** (ADR-0030)."""
        descartes = sum(self.por_causa.values())
        return descartes / self.intentados if self.intentados else 0.0


@dataclass
class _Contador:
    """El estado mutable de la cosecha, separado para que `cosechar` se lea."""

    intentados: int = 0
    agotados: int = 0
    descargados: int = 0
    inicios: list[float] = field(default_factory=list)
    causas: dict[str, int] = field(default_factory=dict)

    def anota(self, causa: str) -> None:
        self.causas[causa] = self.causas.get(causa, 0) + 1

    def vigila_parada(self) -> None:
        """La condición 5, viva. Se mira **después de cada documento**."""
        if self.intentados < MINIMO_PARA_PARAR:
            return
        if self.agotados / self.intentados > UMBRAL_PARADA:
            raise ParadaPorFallos(
                f"{self.agotados} de {self.intentados} documentos han agotado sus "
                f"reintentos ({self.agotados / self.intentados:.1%}), por encima del "
                f"{UMBRAL_PARADA:.0%} tolerado. La cosecha PARA: seguir produciría un "
                "corpus al que le falta una parte desconocida por una causa que nadie "
                "ha mirado. Mira el origen y vuelve a lanzar; lo bajado no se pierde"
            )
