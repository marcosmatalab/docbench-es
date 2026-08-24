"""Los adaptadores de entidad FALSOS contra los que corre la conformidad.

Un adaptador falso no está aquí para tener cobertura: está para **fijar el
contrato**. Si mañana alguien lo endurece de una forma que uno de éstos no pueda
cumplir, se cae un test en la puerta —en segundos y sin red— en vez de caerse un
hito dentro de dos meses, que es lo que ADR-0032 evita.

`AdaptadorCarpeta` es el cuarto de ADR-0032: **el que no tiene API ni verdad**.
Es el que más restringe lo que la suite puede exigir, y por eso es el que más
vale: `truth_mode = NONE`, glosario vacío, cero tráfico y dos etiquetas de estrato
—las únicas que se calculan sin ver tablas—.

Aquí están sólo los que **cumplen**. Los que incumplen a propósito —y son la
mitad que valida la suite— están en `_adaptadores_rotos.py`, con la tabla de qué
rompe cada uno y quién lo caza.

Viven en módulos aparte y no dentro del fichero de test por dos razones: los
importan varios tests, y **uno de ellos los registra por entry point**, o sea que
tienen que ser módulos importables por su nombre.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime
from hashlib import sha256

from benchcore.types import LicenseDecl, PrivacyDecl

from docbench_es.types import DocRef, Glossary, RawDoc, Truth, TruthMode

CARPETA: Mapping[str, tuple[date, bytes]] = {
    "informe-2026-01.pdf": (date(2026, 1, 15), b"%PDF-1.7\n" + b"texto de verdad. " * 40),
    "acta-2026-02.pdf": (date(2026, 2, 3), b"%PDF-1.7\n" + b"acta con su texto. " * 40),
    "escaneo-2026-02.pdf": (date(2026, 2, 20), b"%PDF-1.7\n"),
}
"""La «carpeta», en memoria. Determinista y sin disco: la suite corre en la puerta.

El tercero no tiene capa de texto a propósito — es el que separa `escaneado` de
`nacido-digital` sin necesitar extractor."""

FECHA_FIJA = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)
"""`fetched_at` fijo. Un `datetime.now()` haría que dos `fetch` del mismo
documento devolvieran objetos distintos, y la suite comprueba idempotencia."""


class AdaptadorCarpeta:
    """Una carpeta de PDFs: sin API, sin verdad y sin glosario (ADR-0032).

    `benchcore_api` es **atributo de clase** a propósito (ADR-0036): el registro
    comprueba la versión en carga, y en carga no hay instancia que mirar.
    """

    id = "carpeta-falsa"
    display_name = "Carpeta de PDFs (falsa)"
    language = "es"
    truth_mode: TruthMode = "NONE"
    benchcore_api = "1.x"

    umbral_capa_texto = 100
    """Caracteres no blancos por página. Vendría del perfil; aquí va fijo porque
    este falso no carga YAML."""

    def discover(self, since: date, until: date, **filtros: object) -> Iterable[DocRef]:
        """Perezoso de verdad: un generador, no una lista ya construida."""
        del filtros
        for nombre, (fecha, _) in sorted(CARPETA.items()):
            if since <= fecha <= until:
                yield DocRef(
                    entity=self.id,
                    external_id=nombre,
                    published_on=fecha,
                    url=None,
                    kind="pdf",
                )

    def fetch(self, ref: DocRef) -> RawDoc:
        """Del disco —aquí de un dict—, así que idempotente por construcción."""
        fecha, contenido = CARPETA[ref.external_id]
        del fecha
        return RawDoc(
            ref=ref,
            primary=contenido,
            primary_mime="application/pdf",
            companions={},
            sha256=sha256(contenido).hexdigest(),
            fetched_at=FECHA_FIJA,
            n_pages=1,
        )

    def truth(self, ref: DocRef) -> object | None:
        """`None` siempre, y es correcto: su modo es `NONE`, no `DERIVED`."""
        del ref
        return None

    def license(self) -> LicenseDecl:
        """La típica de una carpeta ajena: interna y sin redistribución."""
        return LicenseDecl(
            name="interna",
            may_redistribute_content=False,
            may_redistribute_derived=False,
            attribution=None,
            source_url="file:///corpus",
            verified_on=date(2026, 8, 23),
            notes="Adaptador falso: no hay licencia que verificar",
        )

    def privacy(self) -> PrivacyDecl:
        """Sin categorías especiales: éste es el falso que PASA la puerta.

        El hostil con `special_categories=True` es de L8 y vive en
        `tests/hostile/`, que es donde se demuestra que la política bloquea.
        """
        return PrivacyDecl(
            contains_personal_data=False,
            may_send_to_third_party=False,
        )

    def glossary(self) -> Glossary:
        """Vacío, que es una respuesta válida y no un hueco."""
        return Glossary(
            entity=self.id,
            version=1,
            updated=date(2026, 8, 23),
            terms=(),
            confusables=(),
        )

    def strata(self, ref: DocRef, doc: RawDoc) -> frozenset[str]:
        """Sólo lo que se calcula **sin ver tablas**, o sea sin extractor.

        `celdas-combinadas`, `multipagina` y `sin-tabla` no salen de aquí, y el
        contrato no puede exigirlas: es la fila más dura de ADR-0032.
        """
        del ref
        legibles = sum(1 for b in doc.primary if not chr(b).isspace())
        return frozenset({"nacido-digital" if legibles >= self.umbral_capa_texto else "escaneado"})


class AdaptadorDerivado(AdaptadorCarpeta):
    """El que **sí** produce verdad: modo `DERIVED`, como el BOE con su XML.

    Hereda de la carpeta porque lo único que cambia es de dónde sale la verdad, y
    duplicar los otros seis métodos crearía dos contratos que mantener.
    """

    id = "derivado-falso"
    display_name = "Entidad con XML (falsa)"
    truth_mode: TruthMode = "DERIVED"

    def truth(self, ref: DocRef) -> object | None:
        """Verdad para **todos**, que es lo que el modo promete."""
        return Truth(
            mode="DERIVED",
            doc_ref=ref,
            tables=(),
            facts=(),
            confidence=None,
            n_annotators=None,
            discordance_rate=None,
            built_at=FECHA_FIJA,
        )


class AdaptadorAnotado(AdaptadorCarpeta):
    """Modo `ANNOTATED`: la verdad la pone una persona, así que `truth()` es `None`."""

    id = "anotado-falso"
    display_name = "Entidad anotada a mano (falsa)"
    truth_mode: TruthMode = "ANNOTATED"
