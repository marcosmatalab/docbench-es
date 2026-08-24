"""§10.4 y ADR-0033 · El manifiesto, que **nace publicable**.

> *«Publicarlo después es gratis si el manifiesto nace con lo necesario dentro, y
> es otro hito si no.»*

No existe un corpus español de extracción documental con verdad derivada, así que
el que sale de L3 puede acabar siendo más citado que la propia tabla de
resultados. Y la asimetría que lo decide todo: **la fecha de última actualización
y la sección no se pueden reconstruir sin volver al origen**, y volver al origen
seis meses después no devuelve lo mismo.

## Los cuatro requisitos de ADR-0033, y dónde está cada uno

1. **Procedencia por documento**, no agregada → `Procedencia`, un registro por
   documento, con su fecha de sumario y su sección.
2. **La atribución literal** de la licencia, dentro → `Manifiesto.atribucion`, y
   `crear` **se niega a construir** si viene vacía.
3. **Licencia del corpus separada de la del código** → dos campos,
   `licencia_corpus` y `licencia_codigo`.
4. **Formato de máquina desde el primer día** → `a_json()`, con `ESQUEMA`
   declarado dentro; el markdown se renderiza a partir de él.

## Precondiciones declaradas

- **El manifiesto no descarga nada ni sabe de red.** Recibe lo cosechado. Es de
  `corpus` y no de `entity` porque describe **la campaña**, no la entidad.
- **`a_json` es la fuente y el markdown el derivado**, nunca al revés. Si algún día
  el informe en markdown lleva un dato que no está en el JSON, ese dato no se puede
  publicar como dataset y el requisito 4 deja de cumplirse.
- **No valida la licencia**: la copia tal cual la declara el adaptador. Comprobar
  que una licencia permite lo que dice es de `publish`, y su hito es L8.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from benchcore.types import LicenseDecl

from docbench_es.errors import ContractViolation

__all__ = ["ESQUEMA", "LICENCIA_DEL_CODIGO", "Manifiesto", "Procedencia", "crear"]

ESQUEMA = "docbench-es.manifiesto/1"
"""El identificador de esquema, dentro del propio JSON.

Un dataset sin versión de esquema obliga a adivinar qué campos tenía cuando se
escribió. Va como cadena y no como número para que se pueda leer sin contexto."""

LICENCIA_DEL_CODIGO = "Apache-2.0"
"""La del repositorio, y **no la del corpus**. Requisito 3 de ADR-0033.

Confundirlas es lo que hace impublicable un dataset: el código es Apache-2.0 y el
corpus está sujeto a lo que permita cada entidad, que en el BOE exige atribución.
Sale de `pyproject.toml`, donde está declarada."""


@dataclass(frozen=True)
class Procedencia:
    """De dónde salió UN documento. Requisito 1: por documento, no agregada.

    `fecha_sumario` y `seccion` están aquí y no en un agregado por una razón
    concreta: **sin la sección no se puede re-derivar la población del
    denominador**, y sin la fecha del sumario no se sabe de qué ventana salió cada
    documento — que es lo que ADR-0030 exige para publicar cualquier tasa.

    `actualizado_en` es la **fecha de última actualización** que exigen las
    condiciones de reutilización del BOE. Sin ella el manifiesto no cumple la
    licencia, y no se puede reconstruir sin volver al origen.
    """

    external_id: str
    fecha_sumario: date
    seccion: str
    url_pdf: str
    url_xml: str
    sha256: str
    n_pages: int | None
    strata: frozenset[str]
    fetched_at: datetime
    actualizado_en: date


@dataclass(frozen=True)
class Manifiesto:
    """La campaña entera, en un objeto que sabe convertirse en JSON.

    `ventana` va dentro **por requisito**, no por adorno: toda tasa de descarte que
    salga de aquí se publica con su ventana (ADR-0030), y si el manifiesto no la
    guardara habría que reconstruirla de las fechas de los documentos — que no es
    lo mismo, porque un día sin boletín no deja documento.
    """

    entidad: str
    desde: date
    hasta: date
    documentos: tuple[Procedencia, ...]
    licencia_corpus: LicenseDecl
    atribucion: str
    licencia_codigo: str
    umbral_coherencia: float
    intentados: int
    por_causa: Mapping[str, int]
    dias_sin_boletin: tuple[date, ...]
    espaciado_mediano_s: float | None

    @property
    def n_descartados(self) -> int:
        return sum(self.por_causa.values())

    @property
    def tasa_descarte(self) -> float:
        """Sobre el censo completo de la campaña, así que **sin intervalo** (ADR-0015).

        Y **nunca se publica sola**: quien la imprima tiene que sacar al lado la
        ventana, el umbral y el denominador, que están todos en este objeto porque
        ADR-0030 los exige juntos.
        """
        return self.n_descartados / self.intentados if self.intentados else 0.0

    def a_json(self) -> dict[str, object]:
        """**Requisito 4**: formato de máquina desde el primer día.

        El markdown del informe se renderiza a partir de esto, nunca al revés. Así
        publicar el corpus es un paso de renderizado y no un reescribido — que es
        exactamente la diferencia entre una decisión y un hito.
        """
        return {
            "esquema": ESQUEMA,
            "entidad": self.entidad,
            "ventana": {"desde": self.desde.isoformat(), "hasta": self.hasta.isoformat()},
            "licencia_corpus": {
                "name": self.licencia_corpus.name,
                "source_url": self.licencia_corpus.source_url,
                "verified_on": self.licencia_corpus.verified_on.isoformat(),
                "may_redistribute_content": self.licencia_corpus.may_redistribute_content,
                "may_redistribute_derived": self.licencia_corpus.may_redistribute_derived,
            },
            "atribucion": self.atribucion,
            "licencia_codigo": self.licencia_codigo,
            "emparejado": {
                "umbral_coherencia": self.umbral_coherencia,
                "intentados": self.intentados,
                "aceptados": len(self.documentos),
                "descartados": self.n_descartados,
                "tasa_descarte": self.tasa_descarte,
                "por_causa": dict(self.por_causa),
            },
            "dias_sin_boletin": [d.isoformat() for d in self.dias_sin_boletin],
            "ritmo": {"espaciado_mediano_s": self.espaciado_mediano_s},
            "documentos": [
                {
                    "external_id": d.external_id,
                    "fecha_sumario": d.fecha_sumario.isoformat(),
                    "seccion": d.seccion,
                    "url_pdf": d.url_pdf,
                    "url_xml": d.url_xml,
                    "sha256": d.sha256,
                    "n_pages": d.n_pages,
                    "strata": sorted(d.strata),
                    "fetched_at": d.fetched_at.isoformat(),
                    "actualizado_en": d.actualizado_en.isoformat(),
                }
                for d in self.documentos
            ],
        }

    def a_texto(self) -> str:
        """El JSON serializado, estable entre corridas: claves ordenadas y UTF-8.

        Estable porque el manifiesto se versiona: si el orden de las claves cambiara
        entre dos corridas idénticas, cada campaña produciría un `diff` enorme y
        nadie podría ver qué cambió de verdad.
        """
        return json.dumps(self.a_json(), ensure_ascii=False, indent=2, sort_keys=True)


def crear(
    *,
    entidad: str,
    desde: date,
    hasta: date,
    documentos: Sequence[Procedencia],
    licencia: LicenseDecl,
    umbral_coherencia: float,
    intentados: int,
    por_causa: Mapping[str, int],
    dias_sin_boletin: Sequence[date],
    espaciado_mediano_s: float | None,
) -> Manifiesto:
    """Construye el manifiesto **exigiendo lo que ADR-0033 pide**, o no construye.

    Las dos comprobaciones son puertas, no cortesías:

    - **Sin atribución no hay manifiesto.** El requisito 2 pide el texto literal
      dentro, no una referencia a dónde leerlo. Un corpus publicado sin la
      atribución que su licencia exige incumple la licencia — y el momento de
      notarlo es al construirlo, no al publicarlo.
    - **`aceptados + descartes == intentados`.** Si no cuadra, hay documentos que
      salieron de la cosecha sin aparecer en ningún lado, y la tasa que este objeto
      publica estaría calculada sobre una población que nadie declaró.
    """
    if not (licencia.attribution or "").strip():
        raise ContractViolation(
            f"la licencia de {entidad!r} no trae `attribution` y el manifiesto la exige "
            "LITERAL dentro (ADR-0033, requisito 2). Publicar el corpus sin ella "
            "incumpliría su licencia, y eso se nota al construirlo o no se nota"
        )
    descartes = sum(por_causa.values())
    if len(documentos) + descartes != intentados:
        raise ContractViolation(
            f"la cosecha no cuadra: {len(documentos)} aceptados + {descartes} descartados "
            f"!= {intentados} intentados. Faltan documentos por contar, y un descarte que "
            "desaparece se lleva por delante el denominador de la tasa publicada"
        )
    return Manifiesto(
        entidad=entidad,
        desde=desde,
        hasta=hasta,
        documentos=tuple(documentos),
        licencia_corpus=licencia,
        atribucion=licencia.attribution or "",
        licencia_codigo=LICENCIA_DEL_CODIGO,
        umbral_coherencia=umbral_coherencia,
        intentados=intentados,
        por_causa=dict(por_causa),
        dias_sin_boletin=tuple(dias_sin_boletin),
        espaciado_mediano_s=espaciado_mediano_s,
    )
