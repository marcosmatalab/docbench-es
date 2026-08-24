"""§7.1 · El contrato que cumple todo adaptador de entidad, y su perfil declarativo.

Un **adaptador de entidad** responde a *«qué documentos hay, cómo se bajan, y qué
sé de ellos»*. El motor no sabe nada del BOE: sabe de `EntityAdapter`. Ésa es la
afirmación que la suite de conformidad tiene que hacer verificable, porque
*«el motor es agnóstico a la entidad»* sin suite es una frase de folleto.

## Por qué NO es un `Plugin` de `benchcore` · **ADR-0035**

**Porque el eje de entidad tendría exactamente un consumidor, y siempre.**
`benchcore` sirve a `docbench-es` y a `gonogo`, y `gonogo` tiene jueces y tareas,
no entidades. El D-003 de `benchcore` dice que un contrato diseñado sin un
consumidor que lo pruebe es un contrato a ciegas; la regla espejo es que **un
contrato compartido con un solo consumidor no está compartido: está mal
colocado**. Sería una interfaz cuyo único implementador y único llamador viven
aquí, y cada cambio costaría dos PR en dos repos.

El impedimento técnico existe y está comprobado sobre la versión instalada
—`Plugin` exige `capabilities()` y `probe()`, y `Capabilities.axis` es un
`Literal["datos", "computo", "ejecucion", "salida"]`, **cerrado y sin
`entidad`**—, pero **ése es el argumento débil**: se cae con un commit de una
línea en otro repo. El de arriba no.

**El contraste lo confirma:** `sources/` —los conectores de plataforma de L15— sí
son `DataSource`, un eje que **sí** existe y que **sí** tiene dos consumidores
posibles: bajar bytes de SharePoint o de S3 le sirve igual a `gonogo`. La
separación es real: un `DataSource` dice *de dónde salen los bytes*; un
`EntityAdapter` dice además *qué son* —verdad, glosario, estratos, licencia—, y
eso sólo significa algo dentro de un banco documental.

**Lo que sí se comparte es el apretón de manos de versión:** `benchcore_api` se
declara igual, como manda §7.1. Y de ahí sale la consecuencia directa —quién
descubre entonces un adaptador—, que se decide en **ADR-0036** y vive en
`entity/registry.py`: grupo propio `docbench.entity`, la mecánica de
`benchcore.registry` reusada tal cual, y rechazo en carga.

## La precondición de todo esto, declarada

Este módulo **no comprueba** que un adaptador cumpla el contrato: sólo lo
describe. Quien lo comprueba es `entity.conformance`, y correrlo es obligatorio
por adaptador (§14). Un adaptador que no ha pasado la suite **no es un adaptador
que cumple**, es uno que todavía no se ha mirado.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml
from benchcore.types import LicenseDecl, PrivacyDecl

from docbench_es.types import DocRef, Glossary, RawDoc, TruthMode

__all__ = ["EntityAdapter", "PerfilEntidad", "RitmoPeticion", "cargar_perfil"]


@dataclass(frozen=True)
class RitmoPeticion:
    """A qué ritmo se le pide a un origen, y cómo nos identificamos.

    **Vive en el perfil y nunca en el código** (`.claude/rules/entidad-corpus.md`).
    Tener derecho a los datos y saber pedirlos son cosas distintas: la licencia es
    lo primero y esto es lo segundo.

    `rps` es **peticiones por segundo**, y se implementa como espaciado mínimo
    entre peticiones consecutivas — no como un promedio sobre una ventana. La
    diferencia importa: un promedio permite ráfagas, y una ráfaga es justo lo que
    un servidor nota.

    `paralelismo` sólo admite 1 a propósito. Un campo que se puede subir es un
    campo que alguien sube.
    """

    rps: float
    user_agent: str
    paralelismo: int = 1

    def __post_init__(self) -> None:
        if self.rps <= 0:
            raise ValueError(f"rps tiene que ser positivo, no {self.rps}")
        if self.paralelismo != 1:
            raise ValueError(
                f"paralelismo={self.paralelismo}: sólo se admite 1. Pedir en paralelo a "
                "un origen ajeno multiplica la carga que ve por algo que aquí nadie ha medido"
            )
        if "http" not in self.user_agent:
            raise ValueError(
                f"el user_agent tiene que llevar una URL de contacto: {self.user_agent!r}. "
                "Es lo que separa a quien cosecha de forma responsable de un scraper anónimo"
            )

    @property
    def espaciado_s(self) -> float:
        """Segundos mínimos entre el inicio de dos peticiones consecutivas."""
        return 1.0 / self.rps


@dataclass(frozen=True)
class PerfilEntidad:
    """§10.1 · El perfil declarativo. **Aquí viven las decisiones de la entidad.**

    Lo que está aquí y no en el código, y por qué cada cosa:

    - **`filtro_secciones`** — no es una optimización, es **parte de la definición
      del corpus**: sin él, tres de cada cuatro documentos del BOE son anuncios sin
      tabla. Cambiarlo cambia la población, y la población es lo que da sentido a
      cualquier tasa que se publique.
    - **`umbral_capa_texto`** — caracteres no blancos por página. Decide **a la vez**
      el estrato `escaneado` y la causa de fallo `no_text_layer` (§9.4 y §6.9): un
      solo número para el mismo hecho medido, para que un documento no pueda ser
      `nacido-digital` y hacer fallar a un extractor por falta de capa de texto.
    - **`umbral_coherencia`** — por debajo de él, el PDF y el XML no dicen lo mismo
      y el par **se descarta y se cuenta**. Un emparejado silenciosamente incorrecto
      envenena todo el banco.
    - **`ritmo`** — ver `RitmoPeticion`.
    - **`licencia` y `privacidad`** — son **código**, no un README (regla de oro 5).
    """

    id: str
    display_name: str
    language: str
    truth_mode: TruthMode
    benchcore_api: str
    ritmo: RitmoPeticion
    licencia: LicenseDecl
    privacidad: PrivacyDecl
    umbral_capa_texto: int = 100
    umbral_coherencia: float = 0.85
    filtro_secciones: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not 0.0 <= self.umbral_coherencia <= 1.0:
            raise ValueError(f"umbral_coherencia fuera de [0,1]: {self.umbral_coherencia}")
        if self.umbral_capa_texto < 0:
            raise ValueError(f"umbral_capa_texto negativo: {self.umbral_capa_texto}")


@runtime_checkable
class EntityAdapter(Protocol):
    """Los siete métodos de §7.1. El motor no conoce otra cosa de una entidad.

    **Lo que la suite de conformidad puede exigir, y lo que NO** (ADR-0032):

    | Puede exigir | No puede exigir |
    |---|---|
    | `discover` no descarga | que haya paginación, ni que exista un «sumario» |
    | `fetch` es idempotente por `sha256` | caché HTTP, `ETag` ni reintentos |
    | `truth` es `None` sii `truth_mode != DERIVED` | — |
    | `license`/`privacy` estables entre llamadas | que la licencia sea pública |
    | `strata` determinista y subconjunto del perfil | **un conjunto FIJO de etiquetas** |

    La última fila es la que más cuesta y la que más importa: `celdas-combinadas`,
    `multipagina` y `sin-tabla` exigen **ver tablas**, y ver tablas exige un
    extractor que el núcleo no puede importar. Un contrato que las pidiera sería
    incumplible por una carpeta de PDFs — que es justo el adaptador que convierte
    esto en herramienta.
    """

    id: str
    display_name: str
    language: str
    truth_mode: TruthMode
    benchcore_api: str
    """**Atributo de CLASE**, no asignado en `__init__` (ADR-0036).

    El registro comprueba la versión *en carga*, y en carga no hay instancia. Un
    adaptador que lo asigne en el constructor **no llega a cargarse**: comprobado,
    lo rechaza por *«no declara `benchcore_api`»* — falla cerrado, pero con un
    mensaje que habla de una versión ausente y no de la que el adaptador creía
    declarar. Por eso la conformidad lo comprueba: el fallo es confuso, no
    silencioso."""

    def discover(self, since: date, until: date, **filtros: object) -> Iterable[DocRef]:
        """Qué documentos hay. **NO descarga.** Perezoso y paginable.

        Perezoso de verdad: un `Iterable` que se consume a demanda, no una lista
        construida entera. Una ventana de un año son decenas de miles de
        referencias, y materializarlas todas para quedarse con mil es tráfico y
        memoria a cambio de nada.
        """
        ...

    def fetch(self, ref: DocRef) -> RawDoc:
        """Baja el documento. **Idempotente**, con caché por hash de contenido."""
        ...

    def truth(self, ref: DocRef) -> object | None:
        """La verdad de referencia, si su modo la produce automáticamente.

        `None` **si y sólo si** `truth_mode != "DERIVED"`. El «sólo si» es la mitad
        que se olvida: un adaptador `DERIVED` que devuelve `None` para algunos
        documentos está diciendo que no hay verdad donde el modo promete que la hay.
        """
        ...

    def license(self) -> LicenseDecl:
        """Estable entre llamadas. Es código: el motor la hace cumplir."""
        ...

    def privacy(self) -> PrivacyDecl:
        """Estable entre llamadas."""
        ...

    def glossary(self) -> Glossary:
        """La capa semántica de la entidad. Vacía es una respuesta válida."""
        ...

    def strata(self, ref: DocRef, doc: RawDoc) -> frozenset[str]:
        """Etiquetas de dificultad, **determinista** sobre el documento ya bajado.

        Determinista quiere decir: dos llamadas con el mismo `RawDoc` devuelven el
        mismo conjunto. No que devuelva siempre las mismas etiquetas para
        documentos distintos, y tampoco que emita todas las del perfil.
        """
        ...


def cargar_perfil(ruta: Path) -> PerfilEntidad:
    """Lee un perfil de `entities/*.yaml` y lo valida al construirlo.

    **Falla al cargar, no al usar.** Un umbral fuera de rango o un `user_agent` sin
    contacto revientan aquí, antes de la primera petición, y no a mitad de una
    cosecha de mil documentos.
    """
    crudo = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if not isinstance(crudo, dict):
        raise ValueError(f"{ruta}: el perfil tiene que ser un mapa, no {type(crudo).__name__}")
    lic = dict(crudo["license"])
    priv = dict(crudo["privacy"])
    ritmo = dict(crudo["ritmo"])
    return PerfilEntidad(
        id=str(crudo["id"]),
        display_name=str(crudo["display_name"]),
        language=str(crudo["language"]),
        truth_mode=crudo["truth_mode"],
        benchcore_api=str(crudo["benchcore_api"]),
        ritmo=RitmoPeticion(
            rps=float(ritmo["rps"]),
            user_agent=str(ritmo["user_agent"]),
            paralelismo=int(ritmo.get("paralelismo", 1)),
        ),
        licencia=LicenseDecl(
            name=str(lic["name"]),
            may_redistribute_content=bool(lic["may_redistribute_content"]),
            may_redistribute_derived=bool(lic["may_redistribute_derived"]),
            attribution=lic.get("attribution"),
            source_url=str(lic["source_url"]),
            verified_on=date.fromisoformat(str(lic["verified_on"])),
            notes=str(lic.get("notes", "")),
        ),
        privacidad=PrivacyDecl(
            contains_personal_data=bool(priv["contains_personal_data"]),
            categories=frozenset(priv.get("categories", [])),
            special_categories=bool(priv.get("special_categories", False)),
            lawful_basis=str(priv.get("lawful_basis", "")),
            redaction_required=bool(priv.get("redaction_required", False)),
            redaction_profile=priv.get("redaction_profile"),
            # POR DEFECTO **false**, al revés que `PrivacyDecl` (ADR-0037): un perfil
            # que se olvida del campo no ha contestado la pregunta, y no contestarla
            # no puede valer como un sí. Falla cerrado.
            may_send_to_third_party=bool(priv.get("may_send_to_third_party", False)),
            dpa_reference=priv.get("dpa_reference"),
        ),
        umbral_capa_texto=int(crudo.get("umbral_capa_texto", 100)),
        umbral_coherencia=float(crudo.get("umbral_coherencia", 0.85)),
        filtro_secciones=frozenset(str(x) for x in crudo.get("filtro_secciones", [])),
    )
