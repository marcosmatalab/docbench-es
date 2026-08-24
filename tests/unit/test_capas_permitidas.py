"""Las direcciones que el contrato de capas **PERMITE**, fijadas con el grafo real.

**El hueco que cierra, y ya se ha caído dos veces por él, en direcciones opuestas.**
`.importlinter` tiene cuatro contratos y todos dicen lo que está **prohibido**;
sus controles negativos demuestran que una violación se pone roja. **Nada fijaba lo
que está permitido**, así que cualquiera que diseñara encima del contrato podía
suponerse una prohibición que no existe, y nada le contradecía:

| Cuándo | La suposición falsa | Qué era |
|---|---|---|
| ADR-0027 | «los hermanos no pueden importarse» | falso: con `:` **sí pueden** |
| Diseño de L4 | «`truth` está por encima de `entity`» | falso: **misma línea** |

**Y la lectura completa, que salió al escribir este test:** los OCHO módulos de la
línea `ask : truth : extract : corpus : entity : sources : glossary : sample` son
**una sola capa plana**. `:` no ordena nada — sólo lista hermanos que pueden
importarse entre sí, en cualquier dirección. Así que `entity` puede importar `ask`,
y `sample` puede importar `truth`. Lo que ordena son las LÍNEAS.

Las dos se descubrieron **ejecutando**, no leyendo, y las dos costaron un rediseño
que no hacía falta. Es la misma forma que la tabla `ARTEFACTOS` del barrido de
referencias: **la dirección de fallo que nadie comprueba**. Allí era «un artefacto
que SÍ aparece en git»; aquí es «una dirección que SÍ está permitida».

**Cómo se comprueba, y por qué así.** Se construye el grafo **real** del paquete con
`grimp`, se le añade el import que se quiere probar y se evalúa el **contrato real**
de `.importlinter` sobre él. No se lee el fichero de configuración ni se
reimplementa la regla de capas: si alguien cambia el contrato, este test cambia con
él. Leer el `.importlinter` y razonar sobre su texto es justo lo que falló dos veces.
"""

from __future__ import annotations

import configparser
from pathlib import Path

import grimp
import pytest
from importlinter.application.app_config import settings
from importlinter.configuration import configure
from importlinter.contracts.layers import LayersContract

RAIZ = Path(__file__).resolve().parents[2]

PERMITIDAS = [
    # (quien importa, a quien, por qué importa que esté permitido)
    ("entity", "truth", "L4: entity.boe.truth() ensambla con truth.derived"),
    ("corpus", "entity", "L3: la cosecha consume el adaptador de entidad"),
    ("truth", "core", "L4: la verdad derivada valida con core.canonical"),
    ("extract", "core", "L5: un extractor produce CanonicalTable"),
    ("entity", "core", "L3: boe_xml parsea con from_html"),
]
"""Las direcciones que hay que poder usar. Cada una con el hito que la necesita:
una entrada sin consumidor sería una regla que nadie ha ejercido."""

PROHIBIDAS = [
    ("core", "entity", "el núcleo es puro: se prueba sin red"),
    ("core", "truth", "idem"),
    ("entity", "report", "una capa NO importa hacia arriba: `report` está en otra línea"),
]
"""El otro lado, sin el cual lo de arriba lo pasaría un test que dijera «permitido»
a cualquier cosa. Es el mismo argumento que `siempre_ok` contra `siempre_roto`."""


def _contrato() -> LayersContract:
    """El contrato de capas **leído de `.importlinter`**, no reescrito aquí."""
    configure()  # type: ignore[no-untyped-call]  # import-linter no lleva tipos
    cfg = configparser.ConfigParser()
    cfg.read(RAIZ / ".importlinter")
    seccion = next(s for s in cfg.sections() if cfg[s].get("type") == "layers")
    crudo = cfg[seccion]
    return LayersContract(
        name=crudo.get("name", "capas"),
        session_options={"root_packages": ["docbench_es"]},
        contract_options={
            "layers": [x for x in crudo["layers"].splitlines() if x.strip()],
            "containers": [x for x in crudo["containers"].splitlines() if x.strip()],
            "exhaustive": crudo.get("exhaustive", "false"),
        },
    )


def _permite(importador: str, importado: str) -> bool:
    """¿El contrato REAL acepta ese import sobre el grafo REAL?"""
    grafo = grimp.build_graph("docbench_es")
    grafo.add_import(
        importer=f"docbench_es.{importador}",
        imported=f"docbench_es.{importado}",
        line_number=1,
        line_contents="(import de prueba)",
    )
    settings.configure(GRAPH_BUILDER=None, PRINTER=None, TIMER=None, USER_OPTIONS_READERS=[])
    return bool(_contrato().check(grafo, verbose=False).kept)


@pytest.mark.parametrize(("importador", "importado", "razon"), PERMITIDAS)
def test_una_direccion_permitida_sigue_estando_permitida(
    importador: str, importado: str, razon: str
) -> None:
    """**El aro que faltaba.** Si esto se pone rojo, alguien estrechó el contrato y
    hay un hito que deja de poder construirse — no un problema de estilo."""
    assert _permite(importador, importado), (
        f"`{importador}` YA NO puede importar `{importado}`, y lo necesita: {razon}"
    )


@pytest.mark.parametrize(("importador", "importado", "razon"), PROHIBIDAS)
def test_una_direccion_prohibida_sigue_estando_prohibida(
    importador: str, importado: str, razon: str
) -> None:
    """La otra dirección, sin la cual lo de arriba lo pasaría un test que aceptara
    cualquier import. Un detector que sólo se ha visto decir «sí» no ha demostrado
    que sepa decir «no»."""
    assert not _permite(importador, importado), f"`{importador}` -> `{importado}`: {razon}"
