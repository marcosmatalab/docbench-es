"""§7.2 · La suite de conformidad de extractores: el mismo aro para el propio y el ajeno.

*«Ocho bibliotecas que no se parecen en nada compiten bajo las mismas reglas»* sin suite
es una frase de folleto. Esto es lo que la hace verificable. Y el criterio de terminado
de un extractor nuevo es **uno solo**: esta suite en verde. Nada más, y nada menos.

La regla que la mantiene honesta: **el extractor de un cliente pasa exactamente por el
mismo aro que los del banco.** Si alguna vez hay un camino privilegiado, la promesa de
extensibilidad del proyecto es mentira.

## Devuelve hallazgos; no lanza en el primero

Igual que `entity.conformance` y que `benchcore.conform`: quien está escribiendo un
extractor quiere ver **todo** lo que le falta de una vez, no descubrirlo de uno en uno
separado por una corrida de tests.

## Tres severidades, y `NO_EJECUTADA` es la que decide

`pasa` exige **cero `FALLA` y cero `NO_EJECUTADA`**. Un aro por el que no se ha pasado no
está superado, y contarlo como aprobado sería publicar como observado algo que no se
observó. Aquí eso pasa en dos sitios concretos:

* **sin documentos**, no se ha comprobado ninguna conducta;
* **sin ocasión** —ningún documento con celdas combinadas en la verdad de referencia—,
  `expresses_spans=False` no se puede confirmar y sale `SIN_EVIDENCIA`.

Por eso el conjunto de conformidad **se elige y declara qué veredictos puede producir**:
`runs/l5/conformidad.yaml`, comprobado contra los fixtures congelados de L4 por
`scripts/conjunto_conformidad.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from docbench_es.extract import _aros
from docbench_es.extract._spans import VeredictoSpans, veredicto_de_spans
from docbench_es.types import Hallazgo

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Sequence

    from docbench_es.types import RawDoc

__all__ = ["Caso", "InformeConformidadExtractor", "comprobar"]


@dataclass(frozen=True)
class Caso:
    """Un documento del conjunto **con lo que la verdad de referencia dice de él**.

    `trae_combinadas` no lo decide quien corre la suite: sale de los `spans` de un
    fixture congelado de L4. Es lo que hace posible distinguir un extractor que aplana
    los `rowspan` —honesto— de uno al que no le tocó ninguno —no medido—.
    """

    doc: RawDoc
    trae_combinadas: bool


@dataclass(frozen=True)
class InformeConformidadExtractor:
    """Lo que la suite vio, **incluido lo que no pudo ver**."""

    extractor_id: str
    n_documentos: int
    hubo_ocasion: bool
    veredicto_spans: VeredictoSpans | None
    hallazgos: tuple[Hallazgo, ...]

    @property
    def pasa(self) -> bool:
        """Cero `FALLA` y cero `NO_EJECUTADA`. Los `AVISO` no bloquean."""
        return not any(h.severidad in ("FALLA", "NO_EJECUTADA") for h in self.hallazgos)

    def __str__(self) -> str:
        """El denominador delante, que es la regla de la casa."""
        veredicto = "veredicto de spans: " + (self.veredicto_spans or "no alcanzado")
        return (
            f"{self.extractor_id}: {'PASA' if self.pasa else 'NO PASA'} · "
            f"{self.n_documentos} documentos, ocasión de spans "
            f"{'sí' if self.hubo_ocasion else 'NO'} · {veredicto} · "
            f"{len(self.hallazgos)} hallazgos"
        )


def _hostil(modelo: RawDoc) -> RawDoc:
    """Un documento deliberadamente corrupto, con la forma del real.

    Se construye desde uno de verdad para que sólo cambien los bytes: si se inventara la
    `DocRef` entera, un extractor podría fallar por el identificador y no por el PDF, y
    el aro estaría midiendo otra cosa.
    """
    from dataclasses import replace

    return replace(modelo, primary=b"%PDF-1.4\nesto no es un PDF\n%%EOF", n_pages=None)


def comprobar(extractor: object, casos: Sequence[Caso]) -> InformeConformidadExtractor:
    """Corre la suite entera contra un extractor **ya construido**.

    No construye nada: recibe la instancia. Descubrir sin construir es cosa del registro
    y usa `cumple_la_forma`; aquí ya hay que ejecutar, así que ya hay instancia.
    """
    ident = str(getattr(extractor, "id", "(sin id)"))
    hallazgos: list[Hallazgo] = []

    roto = _aros.aro_forma(extractor)
    if roto is not None:
        return InformeConformidadExtractor(ident, len(casos), False, None, (roto,))

    for aro in (_aros.aro_probe_no_procesa(extractor),):
        if aro is not None:
            hallazgos.append(aro)

    if not casos:
        hallazgos.append(
            Hallazgo(
                "conducta",
                "NO_EJECUTADA",
                "sin documentos no se ha comprobado ninguna conducta: ni que `extract` "
                "no lanza, ni las tablas, ni el coste, ni los spans",
            )
        )
        return InformeConformidadExtractor(ident, 0, False, None, tuple(hallazgos))

    hostil = _aros.aro_extract_no_lanza(extractor, _hostil(casos[0].doc))
    if hostil is not None:
        hallazgos.append(hostil)

    hubo_ocasion = any(c.trae_combinadas for c in casos)
    emitio = False
    formatos: set[str] = set()
    for caso in casos:
        ex = extractor.extract(caso.doc)  # type: ignore[attr-defined]
        if ex.failed:
            hallazgos.append(
                Hallazgo("extraccion", "AVISO", f"{caso.doc.ref.key()}: {ex.failure_reason}")
            )
            continue
        formatos.add(ex.native_format)
        emitio = emitio or _aros.spans_emitidos(ex)
        for aro in (
            _aros.aro_la_extraccion_se_identifica(extractor, ex),
            _aros.aro_formato_canonico(ex),
            _aros.aro_tablas_bien_formadas(ex),
            _aros.aro_cost_of_es_pura(extractor, ex),
        ):
            if aro is not None:
                hallazgos.append(aro)

    veredicto = _veredicto(extractor, formatos, emitio, hubo_ocasion, hallazgos)
    return InformeConformidadExtractor(ident, len(casos), hubo_ocasion, veredicto, tuple(hallazgos))


def _veredicto(
    extractor: object,
    formatos: set[str],
    emitio: bool,
    hubo_ocasion: bool,
    hallazgos: list[Hallazgo],
) -> VeredictoSpans | None:
    """El contraste de `expresses_spans`, o el motivo por el que no se pudo hacer.

    Devuelve `None` sólo cuando **no se pudo llegar** —sin extracciones buenas o con un
    formato no canónico—, y en ese caso deja un `NO_EJECUTADA`: un aro no corrido no es
    un aro superado.
    """
    if not formatos:
        hallazgos.append(
            Hallazgo("spans", "NO_EJECUTADA", "ninguna extracción salió bien: sin formato")
        )
        return None
    if len(formatos) > 1:
        hallazgos.append(
            Hallazgo(
                "spans",
                "FALLA",
                f"el extractor devolvió formatos distintos entre documentos: "
                f"{sorted(formatos)}. `expresses_spans` es una declaración del extractor, "
                "así que su formato nativo tiene que ser uno",
            )
        )
        return None
    formato = formatos.pop()
    if not _aros.formato_utilizable_desde(formato):
        hallazgos.append(
            Hallazgo("spans", "NO_EJECUTADA", f"formato {formato!r} no canónico: no se pudo")
        )
        return None
    declarado = bool(getattr(extractor, "expresses_spans", False))
    veredicto = veredicto_de_spans(declarado, formato, emitio, hubo_ocasion)
    if veredicto in ("CONTRADICCION", "ESCONDIDO"):
        hallazgos.append(Hallazgo("spans", "FALLA", f"{veredicto} con formato {formato!r}"))
    elif veredicto == "SIN_EVIDENCIA":
        hallazgos.append(
            Hallazgo(
                "spans",
                "NO_EJECUTADA",
                "declara expresses_spans=False y el conjunto no traía ni una celda "
                "combinada: no se puede distinguir si las aplana o si no le tocó ninguna",
            )
        )
    return veredicto
