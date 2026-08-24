"""Las comprobaciones sueltas de la suite de entidad, una por aro de §7.1.

Están aquí y no en `conformance.py` por el límite de 300 líneas del repo: juntas
se iban a 330. La partición no es arbitraria — **`conformance` es la política**
(qué severidad hace fallar, qué se considera «sin comprobar») y esto es **la
mecánica** (qué se le pide a cada método).

`Hallazgo` y `Severidad` viven aquí porque los producen estas funciones, y
`conformance` los reexporta: son parte de su API pública, no de la de un módulo
con guion bajo delante.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from itertools import islice
from typing import Literal, get_args

from docbench_es.entity.base import EntityAdapter
from docbench_es.types import DocRef, RawDoc, TruthMode

__all__ = ["MIEMBROS", "Hallazgo", "Severidad"]

Severidad = Literal["FALLA", "AVISO", "NO_EJECUTADA"]

MIEMBROS: tuple[str, ...] = (
    "id",
    "display_name",
    "language",
    "truth_mode",
    "benchcore_api",
    "discover",
    "fetch",
    "truth",
    "license",
    "privacy",
    "glossary",
    "strata",
)
"""Los cinco atributos y los siete métodos de §7.1, para poder decir **cuál** falta."""


@dataclass(frozen=True)
class Hallazgo:
    """Una comprobación con su resultado y el porqué, en castellano."""

    comprobacion: str
    severidad: Severidad
    detalle: str


def _forma(adaptador: object) -> Hallazgo | None:
    """Los doce miembros de §7.1. Sin esto, el resto no se puede ni intentar."""
    faltan = [n for n in MIEMBROS if not hasattr(adaptador, n)]
    if faltan:
        return Hallazgo("forma", "FALLA", f"no cumple `EntityAdapter`: falta {', '.join(faltan)}")
    return None


def _identidad(adaptador: EntityAdapter) -> Iterator[Hallazgo]:
    """`id`, `language` y `truth_mode`. El `truth_mode` decide si habrá exactitud."""
    if not adaptador.id.strip():
        yield Hallazgo("identidad", "FALLA", "`id` vacío: es la clave de todo el corpus")
    modos = get_args(TruthMode)
    if adaptador.truth_mode not in modos:
        yield Hallazgo(
            "identidad",
            "FALLA",
            f"`truth_mode`={adaptador.truth_mode!r} no es uno de {modos}",
        )
    if not adaptador.language.strip():
        yield Hallazgo("identidad", "AVISO", "`language` vacío: el glosario se apoya en él")


def _api_de_clase(adaptador: EntityAdapter) -> Iterator[Hallazgo]:
    """ADR-0036: `benchcore_api` **de clase**, o el registro no lo ve nunca.

    El registro comprueba la versión *en carga*, y en carga no hay instancia. Un
    adaptador que la asigne en `__init__` no se rechaza tarde: **no llega a
    cargarse**, y encima el mensaje habla de una versión ausente. Es un fallo
    confuso, y por eso se caza aquí, donde sí hay instancia con la que comparar.
    """
    de_clase = getattr(type(adaptador), "benchcore_api", None)
    if de_clase is None:
        yield Hallazgo(
            "benchcore_api",
            "FALLA",
            "declarado en la instancia y no en la clase: el registro no lo verá "
            "en carga y rechazará el adaptador por «no declara `benchcore_api`» (ADR-0036)",
        )
    elif de_clase != adaptador.benchcore_api:
        yield Hallazgo(
            "benchcore_api",
            "FALLA",
            f"la clase declara {de_clase!r} y la instancia {adaptador.benchcore_api!r}: "
            "el registro usa el de la clase, así que el otro es una versión que nadie mira",
        )


def _descubrir(
    adaptador: EntityAdapter, desde: date, hasta: date, maximo: int
) -> tuple[list[DocRef], list[Hallazgo]]:
    """`discover` perezoso y coherente. **No se comprueba que no descargue.**

    Que el tráfico sea el mínimo (§7.1) exige medirlo, y medirlo exige red — que
    esta suite no tiene, para poder vivir en la puerta (ADR-0032). Lo que sí se
    comprueba es la **pereza**, que es su condición observable: devolver una lista
    ya construida significa haber recorrido la ventana entera antes de que nadie
    pida el primer documento. Un generador que baje cada documento conforme emite
    su referencia pasa por aquí: es perezoso y descarga. **Límite 58**, con su
    precio y su hito.
    """
    hallazgos: list[Hallazgo] = []
    salida = adaptador.discover(desde, hasta)
    if isinstance(salida, Sequence):
        hallazgos.append(
            Hallazgo(
                "discover perezoso",
                "FALLA",
                f"devuelve {type(salida).__name__}, o sea la ventana entera ya "
                "materializada. Un año son decenas de miles de referencias",
            )
        )
    refs = list(islice(iter(salida), maximo))
    ajenas = [r.entity for r in refs if r.entity != adaptador.id]
    if ajenas:
        hallazgos.append(
            Hallazgo(
                "discover coherente",
                "FALLA",
                f"referencias con `entity` ajeno: {sorted(set(ajenas))} en vez de {adaptador.id!r}",
            )
        )
    fuera = [r.external_id for r in refs if r.published_on and not desde <= r.published_on <= hasta]
    if fuera:
        hallazgos.append(
            Hallazgo(
                "discover coherente",
                "FALLA",
                f"documentos fuera de la ventana pedida: {fuera}",
            )
        )
    return refs, hallazgos


def _fetch(adaptador: EntityAdapter, refs: Sequence[DocRef]) -> tuple[list[RawDoc], list[Hallazgo]]:
    """Idempotente **por `sha256`**, no por conducta de red (ADR-0032).

    Y el `sha256` que el adaptador declara tiene que ser el del contenido que
    entrega: si no, el manifiesto de la campaña no sirve para reproducir nada, que
    es justo para lo que existe.
    """
    hallazgos: list[Hallazgo] = []
    docs: list[RawDoc] = []
    for ref in refs:
        uno = adaptador.fetch(ref)
        docs.append(uno)
        if uno.sha256 != adaptador.fetch(ref).sha256:
            hallazgos.append(
                Hallazgo("fetch idempotente", "FALLA", f"dos `sha256` distintos para {ref.key()}")
            )
        real = sha256(uno.primary).hexdigest()
        if uno.sha256 != real:
            hallazgos.append(
                Hallazgo(
                    "fetch íntegro",
                    "FALLA",
                    f"{ref.key()} declara {uno.sha256[:12]}… y su contenido es {real[:12]}…",
                )
            )
        if uno.ref != ref:
            hallazgos.append(
                Hallazgo("fetch íntegro", "FALLA", f"{ref.key()} devuelve otra `ref`: {uno.ref}")
            )
    return docs, hallazgos


def _verdad(adaptador: EntityAdapter, refs: Sequence[DocRef]) -> Iterator[Hallazgo]:
    """`None` **si y sólo si** `truth_mode != DERIVED`. El «sólo si» es la mitad que se olvida."""
    for ref in refs:
        verdad = adaptador.truth(ref)
        if adaptador.truth_mode == "DERIVED" and verdad is None:
            yield Hallazgo(
                "truth sii DERIVED",
                "FALLA",
                f"modo DERIVED y `truth({ref.key()})` es None: promete verdad donde no la hay",
            )
        if adaptador.truth_mode != "DERIVED" and verdad is not None:
            yield Hallazgo(
                "truth sii DERIVED",
                "FALLA",
                f"modo {adaptador.truth_mode} y `truth({ref.key()})` devuelve algo: "
                "una verdad que el motor no puede saber de dónde sale",
            )


def _declaraciones(adaptador: EntityAdapter) -> Iterator[Hallazgo]:
    """Licencia, privacidad y glosario, **estables entre llamadas**.

    Estables porque son código que el motor hace cumplir (regla de oro 5): una
    licencia que cambia entre dos llamadas es una licencia que se puede ablandar
    justo antes de publicar.
    """
    if adaptador.license() != adaptador.license():
        yield Hallazgo("license estable", "FALLA", "dos llamadas devuelven licencias distintas")
    if adaptador.privacy() != adaptador.privacy():
        yield Hallazgo("privacy estable", "FALLA", "dos llamadas devuelven privacidades distintas")
    glosario = adaptador.glossary()
    if glosario.entity != adaptador.id:
        yield Hallazgo(
            "glossary coherente",
            "AVISO",
            f"el glosario dice ser de {glosario.entity!r} y el adaptador es {adaptador.id!r}",
        )


def _estratos(
    adaptador: EntityAdapter,
    refs: Sequence[DocRef],
    docs: Sequence[RawDoc],
    etiquetas_perfil: frozenset[str] | None,
) -> Iterator[Hallazgo]:
    """Determinista y subconjunto del perfil. **No se exige ninguna etiqueta concreta.**

    Es la fila más dura de ADR-0032: `celdas-combinadas`, `multipagina` y
    `sin-tabla` exigen ver tablas, y ver tablas exige un extractor que el núcleo no
    puede importar. Un contrato que las pidiera sería incumplible por una carpeta
    de PDFs.
    """
    if etiquetas_perfil is None:
        # NO_EJECUTADA y no un `skip` silencioso: sin las etiquetas del perfil, el
        # subconjunto NO se comprueba, y `pasa` se quedaba en True habiendo omitido
        # el aro que ADR-0032 llama «la fila más dura». Va ANTES del bucle porque
        # con cero documentos el cuerpo no se ejecuta y el aviso no saldría nunca.
        yield Hallazgo(
            "estratos dentro del perfil",
            "NO_EJECUTADA",
            "sin `etiquetas_perfil` no se comprueba que lo que emite `strata` esté "
            "declarado en el perfil. Pásalas, o el informe no puede decir que cumple",
        )
    for ref, doc in zip(refs, docs, strict=True):
        etiquetas = adaptador.strata(ref, doc)
        if etiquetas != adaptador.strata(ref, doc):
            yield Hallazgo(
                "strata determinista",
                "FALLA",
                f"dos conjuntos distintos para el mismo `RawDoc` de {ref.key()}",
            )
        if etiquetas_perfil is not None and not etiquetas <= etiquetas_perfil:
            yield Hallazgo(
                "strata dentro del perfil",
                "FALLA",
                f"{ref.key()} emite {sorted(etiquetas - etiquetas_perfil)}, "
                "que el perfil no declara",
            )
