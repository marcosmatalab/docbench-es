"""§9.4 · La cosecha: **aquí nacen las cifras de L3, y no son reversibles.**

Todo lo demás de este hito se puede reescribir. Esto no: sus decisiones quedan
congeladas en un corpus de 1.000 documentos, y equivocarse significa volver a
pedirle 2.000 ficheros a un origen ajeno. Cada punto de abajo tiene su test antes
de que se baje el primer documento.

## Lo que este módulo hace cumplir

1. **La tasa es del CORPUS, no del proceso** (ADR-0030, punto 5). En una
   reanudación cuenta el **estado final** de cada documento: uno que agotó
   reintentos ayer y baja bien hoy es un aceptado, no un descarte. Si no, la cifra
   publicada dependería de cuántas veces alguien le dio a reintentar.
2. **`aceptados + descartes == intentados`**, sobre la cosecha entera y no sólo
   sobre el emparejado. Lo comprueba `Cosecha` al construirse.
3. **Los días sin boletín salen del denominador** y se cuentan aparte: un día que
   no se pudo consultar no es un documento descartado, y confundirlos mueve el
   denominador de todo lo publicado.
4. **El ritmo se publica como ESPACIADO entre peticiones consecutivas**, no como
   `N/T`: un promedio permite ráfagas, y con `N/T` una pausa larga tapa diez
   peticiones seguidas.
5. **Condición de parada VIVA**: si más del 5% de los documentos intentados agota
   sus reintentos, esto **para y lanza**. En el código, no en un ADR.
6. **Nunca se rebaja lo que ya está en el manifiesto** (ADR-0031, condición 4).
7. **Cada fallo con su causa del enum cerrado.** No hay ningún `except` que se
   trague nada: sólo se capturan los errores declarados del adaptador.

## Precondiciones declaradas

- **Este módulo NO escribe en disco.** Baja, comprueba y anota la procedencia; los
  bytes se van con el `RawDoc`. Quien quiera conservarlos pasa `guardar`, que se
  llama **sólo con los aceptados** — guardar los descartados sería guardar
  documentos que el manifiesto dice que no están. Sin `guardar`, la cosecha produce
  un manifiesto de un corpus que no existe en ningún sitio, y el criterio de §16
  dice *«descargado»*: si nadie lo pasa, no hay corpus.
- **De dónde salen los dos textos es de quien llama.** `textos` recibe el `RawDoc`
  y devuelve `(texto_pdf, texto_xml)`. Depende de la entidad, y sacar texto de un
  PDF necesita una librería que el núcleo no importa. **Es obligatorio**: sin los
  dos textos no hay tasa de descarte, y sin ella la cosecha no es publicable.
- **El contrato de §7.1 no tiene sitio para la sección ni para los días sin
  boletín.** Los dos hacen falta en el manifiesto (ADR-0033, requisito 1) y los dos
  son de la entidad. Se leen por `AdaptadorConProcedencia`, un `Protocol` opcional
  y explícito: un adaptador que no lo cumpla cosecha igual, con la sección vacía.
  Es un hueco del contrato, no un accidente de aquí.
- **La unidad de la condición de parada son DOCUMENTOS, no peticiones HTTP.** Este
  módulo no ve las peticiones sueltas, así que el 5% se mide sobre documentos
  intentados. Se declara porque los errores grandes de este repo han sido de unidad.
"""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import date
from itertools import pairwise
from typing import Protocol, runtime_checkable

from docbench_es.corpus._cosecha import (
    UMBRAL_PARADA,
    Cosecha,
    ParadaPorFallos,
    Ritmo,
    _Contador,
)
from docbench_es.corpus.manifest import Procedencia
from docbench_es.corpus.pairing import juzgar
from docbench_es.errors import AdapterError
from docbench_es.types import DocRef, RawDoc

__all__ = [
    "UMBRAL_PARADA",
    "Adaptador",
    "AdaptadorConProcedencia",
    "Cosecha",
    "ParadaPorFallos",
    "Ritmo",
    "cosechar",
]
"""`Cosecha`, `Ritmo` y `ParadaPorFallos` viven en `_cosecha` y se reexportan aquí:
son el resultado de cosechar, así que su sitio de import es éste."""


class Adaptador(Protocol):
    """Lo único que la cosecha usa de §7.1: tres de los siete métodos.

    Es tipado estructural y **no un import de `entity`** a propósito: `corpus` y
    `entity` son capas hermanas, y pedir aquí el `Protocol` entero ataría la
    cosecha a la entidad para usar tres métodos. Lo que este módulo necesita, lo
    declara.
    """

    def discover(self, since: date, until: date) -> Iterable[DocRef]: ...

    def fetch(self, ref: DocRef) -> RawDoc: ...

    def strata(self, ref: DocRef, doc: RawDoc) -> frozenset[str]: ...


@runtime_checkable
class AdaptadorConProcedencia(Protocol):
    """Lo que el contrato de §7.1 **no** tiene y el manifiesto sí necesita.

    Opcional a propósito: un adaptador que no lo cumpla se cosecha igual. Lo que no
    vale es sacarlo con `getattr` y una cadena mágica, porque entonces el hueco del
    contrato no se ve al leer el código.
    """

    dias_sin_boletin: list[date]

    def seccion_de(self, ref: DocRef) -> str: ...

    def urls_de(self, ref: DocRef) -> tuple[str, str]: ...

    def espaciados_peticion(self) -> list[float]: ...


def _ritmo(de_peticion: Sequence[float] | None, inicios: Sequence[float]) -> Ritmo:
    """Espaciado. **Nunca `N/T`, y en la unidad correcta: la PETICIÓN.**

    Con `N/T`, diez peticiones seguidas y una pausa larga dan el mismo número que
    once bien espaciadas, y sólo una de las dos es cosechar de forma responsable.

    **La unidad importa tanto como el método.** Este módulo sólo ve documentos, y
    un documento puede ser varias peticiones —el BOE son dos, PDF y XML—: publicar
    el hueco entre documentos como ritmo daría el doble y dejaría pasar un ritmo
    real la mitad de lento que el prometido. Medido en el piloto: 1,99 s entre
    documentos con 1 rps declarado. Así que si el adaptador sabe medir peticiones,
    manda su número; si no, se usa el de documentos y **se dice**.

    Con menos de dos muestras no hay espaciado: `None`, no cero.
    """
    muestras = list(de_peticion) if de_peticion else list(inicios)
    if de_peticion:
        huecos = muestras
    elif len(muestras) >= 2:
        huecos = [b - a for a, b in pairwise(muestras)]
    else:
        return Ritmo(None, None, len(muestras))
    if not huecos:
        return Ritmo(None, None, len(muestras))
    return Ritmo(statistics.median(huecos), min(huecos), len(huecos) + (0 if de_peticion else 1))


def _baja(adaptador: Adaptador, ref: DocRef, reintentos: int) -> RawDoc | None:
    """Baja con reintentos. `None` si los agota. **Sólo captura `AdapterError`.**

    Un `except Exception` convertiría un fallo de programación en «descartado por
    descarga», y el bug viviría escondido dentro de una tasa publicada.
    """
    for intento in range(reintentos + 1):
        try:
            doc = adaptador.fetch(ref)
        except AdapterError:
            if intento == reintentos:
                return None
        else:
            return doc
    return None  # pragma: no cover - inalcanzable, el bucle siempre decide


def cosechar(
    adaptador: Adaptador,
    *,
    desde: date,
    hasta: date,
    textos: Callable[[RawDoc], tuple[str | None, str | None]],
    umbral_coherencia: float,
    actualizado_en: date,
    ya_en_manifiesto: Mapping[str, Procedencia] | None = None,
    objetivo: int | None = None,
    guardar: Callable[[DocRef, RawDoc], None] | None = None,
    reintentos: int = 2,
    reloj: Callable[[], float] = time.monotonic,
) -> Cosecha:
    """Recorre la ventana y devuelve lo cosechado, con todo contado.

    `ya_en_manifiesto` es la caché de ADR-0031, condición 4: lo que ya está **no se
    vuelve a bajar**, y entra en `aceptados` porque **sigue siendo parte del
    corpus**. Ésa es la diferencia entre una tasa del corpus y una tasa del
    proceso: si los heredados no contaran, reanudar cambiaría el denominador.

    `objetivo` corta **por documentos aceptados**, no por intentos. La ventana se
    dimensiona con margen y el corte garantiza el criterio aunque el descarte real
    no sea el proyectado.

    `guardar` recibe cada documento **aceptado** con sus bytes, y es lo único que
    convierte esto en un corpus en disco. Sin él sale un manifiesto de un corpus
    que no existe.
    """
    heredados = dict(ya_en_manifiesto or {})
    tope = objetivo if objetivo is not None else -1
    cuenta = _Contador()
    aceptados: list[Procedencia] = []
    for ref in adaptador.discover(desde, hasta):
        # El corte es por ACEPTADOS y no por intentos: así el objetivo se cumple
        # aunque la tasa de descarte no sea la proyectada. Dimensionar por intentos
        # —«1.045 para 1.000 al 4%»— deja el corpus en 960 si el descarte sale al
        # 8%, y volver a pedirle mil documentos más al origen no es gratis.
        if tope >= 0 and len(aceptados) >= tope:
            break
        cuenta.intentados += 1
        previo = heredados.get(ref.external_id)
        if previo is not None:
            aceptados.append(previo)
            continue

        cuenta.inicios.append(reloj())
        doc = _baja(adaptador, ref, reintentos)
        if doc is None:
            cuenta.agotados += 1
            cuenta.anota("descarga")
            cuenta.vigila_parada()
            continue
        cuenta.descargados += 1

        texto_pdf, texto_xml = textos(doc)
        veredicto = juzgar(texto_pdf, texto_xml, umbral=umbral_coherencia)
        if not veredicto.acepta:
            cuenta.anota(str(veredicto.causa))
            continue
        if guardar is not None:
            guardar(ref, doc)
        aceptados.append(_procedencia(adaptador, ref, doc, actualizado_en))

    return Cosecha(
        intentados=cuenta.intentados,
        aceptados=tuple(aceptados),
        por_causa=dict(sorted(cuenta.causas.items())),
        dias_sin_boletin=tuple(
            adaptador.dias_sin_boletin if isinstance(adaptador, AdaptadorConProcedencia) else ()
        ),
        ritmo=_ritmo(
            adaptador.espaciados_peticion()
            if isinstance(adaptador, AdaptadorConProcedencia)
            else None,
            cuenta.inicios,
        ),
        reintentos_agotados=cuenta.agotados,
        descargados_ahora=cuenta.descargados,
    )


def _procedencia(
    adaptador: Adaptador, ref: DocRef, doc: RawDoc, actualizado_en: date
) -> Procedencia:
    """La fila del manifiesto de un documento aceptado (ADR-0033, requisito 1).

    La sección y las dos URLs salen de `AdaptadorConProcedencia`, porque el
    contrato de §7.1 no tiene sitio para ellas y el manifiesto las exige. Un
    adaptador que no lo cumpla deja la sección vacía: es **menos manifiesto, pero
    es verdad**, en vez de un campo inventado.
    """
    if isinstance(adaptador, AdaptadorConProcedencia):
        seccion, urls = adaptador.seccion_de(ref), adaptador.urls_de(ref)
    else:
        seccion, urls = "", (ref.url or "", "")
    return Procedencia(
        external_id=ref.external_id,
        fecha_sumario=ref.published_on or actualizado_en,
        seccion=seccion,
        url_pdf=urls[0],
        url_xml=urls[1],
        sha256=doc.sha256,
        n_pages=doc.n_pages,
        strata=adaptador.strata(ref, doc),
        fetched_at=doc.fetched_at,
        actualizado_en=actualizado_en,
    )
