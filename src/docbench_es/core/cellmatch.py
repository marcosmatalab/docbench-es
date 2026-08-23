"""§12 · Exactitud celda a celda: `celdas correctas / celdas de la verdad`.

TEDS dice cuánto se parecen dos tablas; esto dice **cuántas celdas acertó**, que
es lo que un lector entiende sin haber leído un paper. Las dos van juntas en el
nivel 1 por eso: TEDS es sensible a la estructura y no tiene valores intuibles,
la exactitud de celda es intuible y no ve la estructura.

**El emparejado es por POSICIÓN**, que es lo que dice §12 —*«emparejado por
posición tras alinear»*—: dos celdas se corresponden si originan en la misma
`(fila, columna)`. No hay alineamiento difuso ni búsqueda del mejor emparejado:
una celda desplazada una columna cuenta como fallo, y eso es deliberado, porque
en una tabla de importes una columna de más cambia a qué concepto pertenece cada
número.

**Caso degenerado, que manda §12: sin celdas en la verdad, `NO_APLICABLE`.**
Devuelve `None`, nunca cero. Cero diría que falló todas.
"""

from __future__ import annotations

from dataclasses import dataclass

from docbench_es.types import CanonicalCell, CanonicalTable

_Firma = tuple[int, int, int, int, str]


@dataclass(frozen=True)
class Emparejado:
    """El recuento crudo, para que cada tasa se pueda recalcular sin volver a medir."""

    aciertos: int
    en_prediccion: int
    en_verdad: int

    @property
    def precision(self) -> float | None:
        """Aciertos sobre lo que el extractor dijo. `None` si no dijo nada."""
        return self.aciertos / self.en_prediccion if self.en_prediccion else None

    @property
    def exhaustividad(self) -> float | None:
        """Aciertos sobre lo que había. `None` si la verdad no tiene celdas."""
        return self.aciertos / self.en_verdad if self.en_verdad else None

    @property
    def f1(self) -> float | None:
        """La media armónica. `None` si alguna de las dos no está definida.

        Y `0.0` —no `None`— si las dos están definidas pero no hubo ni un
        acierto: ahí sí hubo medición, y el resultado es que falló todas.
        """
        p, r = self.precision, self.exhaustividad
        if p is None or r is None:
            return None
        return 2 * p * r / (p + r) if p + r else 0.0


def _firma(celda: CanonicalCell) -> _Firma:
    """Qué tiene que coincidir para que dos celdas sean «la misma».

    Posición, los dos spans y el texto. El texto ya viene normalizado por el
    conversor (L1), así que aquí no se normaliza nada: hacerlo otra vez sería una
    segunda normalización sin declarar, que es justo lo que prohíbe la regla de
    oro 7.

    **`is_header` queda fuera A PROPÓSITO, y esto es lo que lo justifica.** Sin
    decirlo, la omisión se lee como un olvido —y sería grave, porque L2 descubrió
    que `is_header` salía mal en el 100% de las cabeceras de PubTabNet—. Pero el
    error de cabecera **ya se mide, en TEDS**: `is_header` decide el corte
    `<thead>`/`<tbody>` del árbol (ADR-0021), así que una cabecera mal marcada
    cambia la forma del árbol. Medido sobre dos tablas que sólo difieren en el
    flag: `cell_accuracy` = **1,0** y `teds` = **0,5**.

    Meterlo también aquí sería contar el mismo fallo dos veces, que es justo lo
    que §12 se cuida de evitar: *«son dos preguntas distintas»*. La exactitud de
    celda responde **«¿transcribiste la celda?»**; el papel de la celda en la
    tabla lo responde TEDS. `test_dos_tablas_que_solo_difieren_en_is_header` fija
    las dos mitades, y se cae si alguien cambia una sin la otra.
    """
    return (celda.row, celda.col, celda.rowspan, celda.colspan, celda.text)


def emparejar(pred: CanonicalTable, gold: CanonicalTable) -> Emparejado:
    """Cuenta aciertos por posición, sin dejar que una celda cuente dos veces.

    Se emparejan multiconjuntos: si la predicción repite una celda idéntica —lo
    que sólo puede pasar en una tabla con `SOLAPE`, que `validate` ya marca como
    fatal—, la repetición no suma dos aciertos.
    """
    pendientes: dict[_Firma, int] = {}
    for celda in gold.cells:
        pendientes[_firma(celda)] = pendientes.get(_firma(celda), 0) + 1
    aciertos = 0
    for celda in pred.cells:
        clave = _firma(celda)
        if pendientes.get(clave, 0) > 0:
            pendientes[clave] -= 1
            aciertos += 1
    return Emparejado(aciertos, len(pred.cells), len(gold.cells))


def cell_accuracy(pred: CanonicalTable, gold: CanonicalTable) -> float | None:
    """La fórmula literal de §12: celdas correctas / celdas de la verdad.

    `None` es `NO_APLICABLE`: la verdad no tiene celdas y no hay denominador.
    """
    return emparejar(pred, gold).exhaustividad


def cell_f1(pred: CanonicalTable, gold: CanonicalTable) -> float | None:
    """El F1 que consume `StructureMetrics.cell_f1`.

    Va además de la exactitud porque la exactitud sola premia al extractor que
    escupe celdas de más: con la verdad como denominador, inventarse veinte
    celdas no baja la nota. El F1 sí lo penaliza.
    """
    return emparejar(pred, gold).f1
