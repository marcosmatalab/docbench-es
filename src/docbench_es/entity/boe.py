"""§7.1 · El adaptador del BOE: los siete métodos. **La entidad de referencia.**

El motor no sabe nada del BOE: sabe de `EntityAdapter`. Este fichero es la prueba
de que ese contrato es implementable contra un organismo real, y es el que hace que
la verdad sea `DERIVED` —transcripción del XML oficial— en vez de la extracción de
otro concursante (regla de oro 1).

## Lo que decide el perfil y no este fichero

`entities/boe.yaml`: el ritmo, la identificación, los dos umbrales, el filtro de
secciones, la licencia y la privacidad. Ninguno de esos números aparece aquí, y el
constructor **exige que el perfil y esta clase digan lo mismo** — si divergen,
`ContractViolation` en construcción, no una sorpresa a mitad de cosecha.

## Las precondiciones, declaradas

- **`fetch` sólo sirve refs que haya devuelto `discover`.** No es una comodidad de
  implementación: es la condición 1 de ADR-0031 —descubrimiento sólo por la API—
  llevada hasta el final. Un `DocRef` fabricado a mano no tiene URLs autorizadas y
  se rechaza con `PolicyViolation`.
- **Se memoriza el ÚLTIMO documento bajado, y sólo uno.** `truth(ref)` necesita el
  XML que ya bajó `fetch(ref)`, y el orden natural es `fetch` y luego `truth` sobre
  el mismo documento. Guardar los mil sería quedarse sin memoria; guardar cero
  duplicaría las peticiones al origen.
- **`truth` devuelve las TABLAS del XML oficial, con `facts` vacío.** Los hechos de
  §6.4 —`Fact`, con su `path` y su procedencia— son de **L4**, `truth.derived`.
  Aquí está lo que hace falta para que el modo `DERIVED` sea cierto: que haya
  verdad, y que salga del documento oficial.
- **`strata` emite lo que se puede decidir desde el XML**: los cuatro estratos de
  tabla. `escaneado` necesita la capa de texto del PDF y `multipagina` necesita
  páginas, que el XML no tiene. No se aproximan.
- **Un día sin boletín no es un fallo.** Domingos y festivos devuelven 404 y se
  cuentan aparte en `dias_sin_boletin`: *«un día que no se pudo consultar no es un
  descarte»*, y confundirlos mueve el denominador de todo lo que se publique.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

from benchcore.types import LicenseDecl, PrivacyDecl

from docbench_es.entity import boe_xml
from docbench_es.entity._sumario import items_del_sumario, paginas_de, url_de
from docbench_es.entity.base import PerfilEntidad
from docbench_es.entity.boe_api import BoeApi
from docbench_es.errors import ContractViolation, PolicyViolation
from docbench_es.types import DocRef, Glossary, RawDoc, Truth, TruthMode

__all__ = ["BoeAdapter"]


class BoeAdapter:
    """El adaptador del BOE. `benchcore_api` es atributo de clase (ADR-0036)."""

    id = "boe"
    display_name = "Boletín Oficial del Estado"
    language = "es"
    truth_mode: TruthMode = "DERIVED"
    benchcore_api = "1.x"

    def __init__(self, perfil: PerfilEntidad, api: BoeApi | None = None) -> None:
        _exigir_que_el_perfil_cuadre(perfil)
        self._perfil = perfil
        self._api = api if api is not None else BoeApi(perfil.ritmo)
        self._urls: dict[str, tuple[str, str]] = {}
        self._paginas: dict[str, int | None] = {}
        self._secciones: dict[str, str] = {}
        self._ultimo: tuple[str, RawDoc] | None = None
        self.dias_sin_boletin: list[date] = []
        self.sin_urls: list[str] = []
        """Ítems del sumario que traían identificador pero **no las dos URLs**.

        **SE RECOGEN Y TODAVÍA NO SE PUBLICAN, y esto decía que sí.** Nadie lee este
        campo —ni en `src`, ni en `tests`, ni en `scripts`—, así que la frase «se
        publican al lado de `intentados`» era falsa: encontrada en la auditoría en
        frío de `a0d85ed`. Se conserva la recolección porque es gratis y el dato hace
        falta el día que el informe lo lleve; lo que se quita es la afirmación. Va
        como deuda en `ESTADO.md`, no como promesa aquí.

        Cuando se publiquen, el argumento es el de siempre: si no, **desaparecen del
        denominador antes de existir**: no son un descarte —nunca se intentaron—
        pero tampoco son nada, y un origen que empezara a servir el `url_pdf` con
        otra forma vaciaría el corpus sin que ninguna cifra se moviera. Medido
        sobre la ventana de L3: **0 de 1.043**.

        Y `dias_sin_boletin` son los días del rango sin boletín: **se cuentan, no se
        tragan.**"""

    def discover(self, since: date, until: date, **filtros: object) -> Iterable[DocRef]:
        """Los documentos del rango, día a día y **perezosamente**.

        Un `Iterable` que se consume a demanda, no una lista: una ventana de un año
        son decenas de miles de referencias, y materializarlas para quedarse con
        mil es tráfico y memoria a cambio de nada.

        **Un filtro desconocido revienta en vez de ignorarse.** Hoy no se admite
        ninguno: el filtro de secciones es del perfil, porque cambiarlo cambia la
        población y eso no puede decidirlo quien llama sin dejar rastro.
        """
        if filtros:
            raise ContractViolation(
                f"`discover` no admite {sorted(filtros)}: el filtro de secciones vive en "
                "el perfil (§10.1) porque cambia la definición del corpus. Ignorarlo en "
                "silencio dejaría dos campañas con el mismo nombre midiendo poblaciones distintas"
            )
        return self._recorrer(since, until)

    def _recorrer(self, since: date, until: date) -> Iterator[DocRef]:
        dia = since
        while dia <= until:
            sumario = self._api.sumario(dia)
            if sumario is None:
                self.dias_sin_boletin.append(dia)
            else:
                yield from self._del_dia(sumario, dia)
            dia += timedelta(days=1)

    def _del_dia(self, sumario: object, dia: date) -> Iterator[DocRef]:
        secciones = self._perfil.filtro_secciones
        for item in items_del_sumario(sumario if isinstance(sumario, dict) else {}):
            ident = str(item.get("identificador", ""))
            # `BOE-S-*` es el sumario del día, no un documento. Contarlo metería un
            # índice en el corpus y en el denominador de todas las tasas.
            if not ident or ident.startswith("BOE-S-"):
                # `BOE-S-` es el sumario del propio día, no un documento: sale por
                # definición del corpus y por eso no se cuenta como descartado.
                continue
            if secciones and str(item.get("_seccion", "")) not in secciones:
                continue
            pdf, xml = url_de(item, "url_pdf"), url_de(item, "url_xml")
            if pdf is None or xml is None:
                # NO en silencio: un ítem que se cae aquí nunca es `intentado`,
                # nunca tiene causa y nunca sale en el informe — o sea, desaparece
                # del denominador antes de existir. Y la forma del sumario ya ha
                # cambiado dos veces sobre el origen real (`_sumario.py`), así que
                # esto no es hipotético.
                self.sin_urls.append(ident)
                continue
            self._urls[ident] = (pdf, xml)
            self._paginas[ident] = paginas_de(item)
            self._secciones[ident] = str(item.get("_seccion", ""))
            yield DocRef(entity=self.id, external_id=ident, published_on=dia, url=pdf, kind="pdf")

    def fetch(self, ref: DocRef) -> RawDoc:
        """El PDF y su XML, del mismo identificador. Idempotente por `sha256`.

        El XML viaja en `companions["xml"]` y el PDF es el `primary`: el PDF es lo
        que se le da a un extractor y el XML es la verdad contra la que se le mide.
        Meterlos al revés invertiría el banco entero.
        """
        try:
            url_pdf, url_xml = self._urls[ref.external_id]
        except KeyError:
            raise PolicyViolation(
                f"{ref.key()} no ha salido de `discover`, así que sus URLs no las ha "
                "entregado ningún sumario. ADR-0031, condición 1: ni identificadores "
                "adivinados ni enlaces seguidos. Recorre el día que lo contiene"
            ) from None
        pdf = self._api.descargar(url_pdf)
        xml = self._api.descargar(url_xml)
        doc = RawDoc(
            ref=ref,
            primary=pdf,
            primary_mime="application/pdf",
            companions={"xml": xml},
            sha256=sha256(pdf).hexdigest(),
            fetched_at=datetime.now(UTC),
            n_pages=self._paginas.get(ref.external_id),
        )
        self._ultimo = (ref.key(), doc)
        return doc

    def truth(self, ref: DocRef) -> object | None:
        """La verdad de referencia: **las tablas del XML oficial**.

        Nunca `None`, porque el modo es `DERIVED` y prometer verdad donde no la hay
        es la mitad del contrato que se olvida. Si el documento no tiene tablas, la
        verdad son cero tablas — que es una respuesta, no una ausencia.
        """
        doc = self._doc_de(ref)
        xml = doc.companions.get("xml", b"").decode("utf-8", errors="replace")
        return Truth(
            mode="DERIVED",
            doc_ref=ref,
            tables=tuple(boe_xml.tablas(xml)),
            facts=(),
            confidence=None,
            n_annotators=None,
            discordance_rate=None,
            built_at=datetime.now(UTC),
        )

    def _doc_de(self, ref: DocRef) -> RawDoc:
        """El último documento bajado si es éste; si no, se baja. Ver precondiciones."""
        if self._ultimo is not None and self._ultimo[0] == ref.key():
            return self._ultimo[1]
        return self.fetch(ref)

    def seccion_de(self, ref: DocRef) -> str:
        """La sección del sumario de la que salió. **El manifiesto la exige.**

        ADR-0033, requisito 1: *«sin la sección no se puede re-derivar la población
        del denominador»*. El contrato de §7.1 no tiene sitio para ella —`DocRef`
        lleva `kind`, no sección— así que `corpus.harvest` la lee por el `Protocol`
        opcional `AdaptadorConProcedencia`. Es un hueco del contrato, escrito.
        """
        return self._secciones.get(ref.external_id, "")

    def urls_de(self, ref: DocRef) -> tuple[str, str]:
        """Las dos URLs del sumario, `(pdf, xml)`. También del requisito 1.

        `DocRef.url` sólo tiene sitio para una, y el manifiesto necesita las dos:
        el PDF es lo que se extrae y el XML es de donde sale la verdad.
        """
        return self._urls.get(ref.external_id, (ref.url or "", ""))

    def espaciados_peticion(self) -> list[float]:
        """Los huecos medidos entre PETICIONES, que es la unidad de ADR-0031.

        `corpus.harvest` sólo ve documentos, y un documento del BOE son **dos**
        peticiones. Publicar el hueco entre documentos como si fuera el ritmo daría
        el doble y dejaría pasar un ritmo real la mitad de lento que el prometido.
        """
        return self._api.espaciados

    def license(self) -> LicenseDecl:
        """La del perfil, sin tocar. Es código, no un README (regla de oro 5)."""
        return self._perfil.licencia

    def privacy(self) -> PrivacyDecl:
        """La del perfil, sin tocar."""
        return self._perfil.privacidad

    def glossary(self) -> Glossary:
        """Vacío hasta **L11**, que es el hito que mide cuántos puntos aporta.

        Devolver términos inventados aquí haría que L11 midiera la ganancia de un
        glosario que nadie ha construido.
        """
        return Glossary(
            entity=self.id, version=0, updated=date(2026, 8, 24), terms=(), confusables=()
        )

    def strata(self, ref: DocRef, doc: RawDoc) -> frozenset[str]:
        """Los estratos que salen del XML. Determinista sobre el mismo `RawDoc`.

        Sin XML devuelve el conjunto vacío: es lo que se sabe, y el contrato no
        exige ninguna etiqueta concreta (ADR-0032).
        """
        del ref
        xml = doc.companions.get("xml")
        if not xml:
            return frozenset()
        return boe_xml.estratos(boe_xml.rasgos(xml.decode("utf-8", errors="replace")))


def _exigir_que_el_perfil_cuadre(perfil: PerfilEntidad) -> None:
    """La identidad vive en dos sitios, así que se comprueba que digan lo mismo.

    Los cinco atributos son de clase porque el registro los lee **sin instancia**
    (ADR-0036), y a la vez están en el perfil porque §10.1 dice que las decisiones
    de la entidad viven en el YAML. Dos copias del mismo dato es exactamente el bug
    que este repo persigue en los documentos; en el código se cierra igual: **con
    una comprobación que se pone roja**, y en construcción, no a mitad de campaña.
    """
    esperado = {
        "id": BoeAdapter.id,
        "display_name": BoeAdapter.display_name,
        "language": BoeAdapter.language,
        "truth_mode": BoeAdapter.truth_mode,
        "benchcore_api": BoeAdapter.benchcore_api,
    }
    difieren = {k: (v, getattr(perfil, k)) for k, v in esperado.items() if getattr(perfil, k) != v}
    if difieren:
        raise ContractViolation(
            f"el perfil y `BoeAdapter` no dicen lo mismo: {difieren}. Son dos copias del "
            "mismo dato y no pueden divergir: la clase la lee el registro sin instancia y "
            "el perfil lo lee todo lo demás"
        )
