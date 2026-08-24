"""Los adaptadores falsos que **incumplen a propósito**, y qué incumple cada uno.

Separados de los que cumplen por dos razones. La de fondo: una suite que sólo se
prueba contra adaptadores buenos **no está validada** —sale verde igual si no
comprueba nada—, así que estos no son un extra, son la mitad que demuestra que la
otra mitad sirve. Es el mismo argumento que los tests de degradación de §14.

La práctica: juntos pasaban de 300 líneas.

| Falso | Qué rompe | Quién lo caza |
|---|---|---|
| `SinVersion` | no declara `benchcore_api` | el registro, en carga |
| `VersionIncompatible` | declara un mayor que no se sirve | el registro, en carga |
| `VersionEnInit` | la declara en `__init__` | el registro, por «no la declara» |
| `ConstruirTocaElMundo` | su `__init__` lanza | **si algo lo construye, el test se cae** |
| `VersionSoloEnInstancia` | la versión sólo en la instancia | la suite de conformidad |
| `AdaptadorRoto` | cinco aros del contrato a la vez | la suite de conformidad |
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from hashlib import sha256

from _adaptadores_falsos import CARPETA, FECHA_FIJA, AdaptadorCarpeta
from benchcore.types import LicenseDecl, PrivacyDecl

from docbench_es.types import DocRef, Glossary, RawDoc, TruthMode


class SinVersion:
    """No declara `benchcore_api`. **El registro tiene que rechazarlo en carga.**"""

    id = "sin-version"


class VersionIncompatible:
    """Declara un mayor que este `benchcore` no sirve. Rechazado en carga."""

    id = "version-incompatible"
    benchcore_api = "2.x"


class VersionEnInit:
    """Declara la versión en `__init__`, que es el error que ADR-0036 nombra.

    No se rechaza «tarde»: **no llega a cargarse**, porque en carga no hay
    instancia y el registro no ve versión ninguna.
    """

    id = "version-en-init"

    def __init__(self) -> None:
        self.benchcore_api = "1.x"


class ConstruirTocaElMundo:
    """Su `__init__` lanza. **Si el descubrimiento construyera, el test se cae.**

    Es la forma de demostrar *«descubrir no construye»* (ADR-0036) en vez de
    afirmarlo: un adaptador real abre ficheros o pide un perfil al construirse, y
    `docbench entity list` no puede pagar eso por cada entidad registrada.
    """

    id = "construir-toca-el-mundo"
    benchcore_api = "1.x"

    def __init__(self) -> None:
        raise AssertionError("el descubrimiento ha construido el adaptador, y no debe")


class AdaptadorRoto:
    """Incumple **cinco aros a la vez**, y por eso vale más que los otros tres.

    Una suite que sólo se prueba contra adaptadores buenos no está validada: sale
    verde igual si no comprueba nada. Éste es el equivalente para el contrato de
    entidad de los tests de degradación de §14 — se rompe a propósito y se exige
    que la métrica lo note.
    """

    id = "roto-falso"
    display_name = "Adaptador roto a propósito"
    language = "es"
    truth_mode: TruthMode = "DERIVED"
    benchcore_api = "1.x"

    def __init__(self) -> None:
        self._llamadas = 0

    def discover(self, since: date, until: date, **filtros: object) -> Iterable[DocRef]:
        """**Roto 1:** devuelve la ventana entera materializada, no un iterador."""
        del filtros
        return [
            DocRef(entity=self.id, external_id=n, published_on=f, url=None, kind="pdf")
            for n, (f, _) in sorted(CARPETA.items())
            if since <= f <= until
        ]

    def fetch(self, ref: DocRef) -> RawDoc:
        """**Roto 2 y 3:** no es idempotente, y el `sha256` no es el del contenido."""
        self._llamadas += 1
        contenido = CARPETA[ref.external_id][1] + str(self._llamadas).encode()
        return RawDoc(
            ref=ref,
            primary=contenido,
            primary_mime="application/pdf",
            companions={},
            sha256=sha256(f"{ref.external_id}{self._llamadas}".encode()).hexdigest(),
            fetched_at=FECHA_FIJA,
            n_pages=1,
        )

    def truth(self, ref: DocRef) -> object | None:
        """**Roto 4:** modo `DERIVED` y sin verdad. Promete donde no hay."""
        del ref
        return None

    def license(self) -> LicenseDecl:
        return LicenseDecl(
            name="interna",
            may_redistribute_content=False,
            may_redistribute_derived=False,
            attribution=None,
            source_url="file:///corpus",
            verified_on=date(2026, 8, 23),
        )

    def privacy(self) -> PrivacyDecl:
        return PrivacyDecl(contains_personal_data=False)

    def glossary(self) -> Glossary:
        return Glossary(
            entity=self.id, version=1, updated=date(2026, 8, 23), terms=(), confusables=()
        )

    def strata(self, ref: DocRef, doc: RawDoc) -> frozenset[str]:
        """**Roto 5:** no determinista. Cambia de etiqueta según cuántas veces se llame."""
        del ref, doc
        self._llamadas += 1
        return frozenset({"escaneado" if self._llamadas % 2 else "nacido-digital"})


class VersionSoloEnInstancia:
    """Los siete métodos bien, pero `benchcore_api` **sólo en la instancia**.

    Es el error que ADR-0036 nombra y el que peor se diagnostica solo: el registro
    lo rechaza por *«no declara `benchcore_api`»* cuando quien lo escribió está
    mirando la línea donde la declara. Aquí la suite lo dice con todas las letras.

    Delega en `AdaptadorCarpeta` en vez de heredar **a propósito**: heredando se
    quedaría con el atributo de clase de la madre y el fallo desaparecería, que es
    justo el que se quiere reproducir.
    """

    def __init__(self) -> None:
        self._real = AdaptadorCarpeta()
        self.benchcore_api = "1.x"
        self.id = self._real.id
        self.display_name = self._real.display_name
        self.language = self._real.language
        self.truth_mode: TruthMode = self._real.truth_mode

    def discover(self, since: date, until: date, **filtros: object) -> Iterable[DocRef]:
        return self._real.discover(since, until, **filtros)

    def fetch(self, ref: DocRef) -> RawDoc:
        return self._real.fetch(ref)

    def truth(self, ref: DocRef) -> object | None:
        return self._real.truth(ref)

    def license(self) -> LicenseDecl:
        return self._real.license()

    def privacy(self) -> PrivacyDecl:
        return self._real.privacy()

    def glossary(self) -> Glossary:
        return self._real.glossary()

    def strata(self, ref: DocRef, doc: RawDoc) -> frozenset[str]:
        return self._real.strata(ref, doc)
