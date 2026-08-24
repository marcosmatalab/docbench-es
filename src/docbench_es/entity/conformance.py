"""§14 · La suite de conformidad de entidad: el mismo aro para el propio y el ajeno.

*«El motor es agnóstico a la entidad»* sin suite es una frase de folleto. Esto es
lo que la hace verificable, y §14 la declara **obligatoria por adaptador**: uno que
no ha pasado por aquí no es un adaptador que cumple, es uno que todavía no se ha
mirado.

**Qué puede exigir y qué no** está decidido en ADR-0032 y escrito con su tabla en
`entity.base`. No se repite aquí: la versión corta es que el contrato general no
puede pedir etiquetas de estrato concretas ni conducta de red, porque hay que
poder cumplirlo con una carpeta de PDFs.

## Devuelve hallazgos; no lanza en el primero

Igual que `benchcore.conform`: quien está escribiendo un adaptador quiere ver
**todo** lo que le falta de una vez, no descubrirlo de uno en uno separado por una
corrida de tests.

## Tres severidades, y la tercera es la que importa

`benchcore.conform` tiene dos —`FALLA` y `AVISO`— y le bastan, porque mira la
**forma** del contrato y la forma siempre se puede mirar. Esta suite **ejecuta el
adaptador contra documentos**, así que aparece un tercer resultado que allí no
existe: **`NO_EJECUTADA`**.

Si `discover` no trae ni un documento en la ventana pedida, la idempotencia de
`fetch` no falla — **es que no se ha comprobado**. Un informe que contara eso como
aprobado estaría *publicando como observado algo que no se observó*, que es la
familia de fallos que este repo persigue. Por eso `pasa` exige **cero `FALLA` y
cero `NO_EJECUTADA`**: un aro por el que no se ha pasado no está superado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from docbench_es.entity._comprobaciones import (
    Hallazgo,
    Severidad,
    _api_de_clase,
    _declaraciones,
    _descubrir,
    _estratos,
    _fetch,
    _forma,
    _identidad,
    _verdad,
)
from docbench_es.entity.base import EntityAdapter

__all__ = ["Hallazgo", "InformeConformidad", "Severidad", "comprobar"]


@dataclass(frozen=True)
class InformeConformidad:
    """Lo que la suite vio, incluido lo que NO pudo ver."""

    adaptador_id: str
    n_documentos: int
    hallazgos: tuple[Hallazgo, ...]

    @property
    def pasa(self) -> bool:
        """Cero fallos **y** cero comprobaciones sin ejecutar. Ver el docstring del módulo."""
        return not any(h.severidad in ("FALLA", "NO_EJECUTADA") for h in self.hallazgos)

    def resumen(self) -> str:
        """Una línea por hallazgo, para que un fallo en CI se lea sin abrir nada."""
        cabecera = f"{self.adaptador_id}: {'PASA' if self.pasa else 'NO PASA'}"
        return "\n".join(
            [f"{cabecera} · {self.n_documentos} documentos"]
            + [f"  [{h.severidad}] {h.comprobacion}: {h.detalle}" for h in self.hallazgos]
        )


def comprobar(
    adaptador: object,
    *,
    desde: date,
    hasta: date,
    maximo: int = 3,
    etiquetas_perfil: frozenset[str] | None = None,
) -> InformeConformidad:
    """Corre la suite entera contra un adaptador **ya construido con su perfil**.

    `maximo` acota cuántos documentos se tocan: la suite demuestra que el contrato
    se cumple, no mide un corpus. Con un adaptador real, cada documento de más es
    una petición de más a un origen ajeno.
    """
    ident = str(getattr(adaptador, "id", "(sin id)"))
    roto = _forma(adaptador)
    if roto is not None or not isinstance(adaptador, EntityAdapter):
        detalle = roto or Hallazgo("forma", "FALLA", "no cumple `EntityAdapter`")
        return InformeConformidad(ident, 0, (detalle,))

    hallazgos = [*_identidad(adaptador), *_api_de_clase(adaptador), *_declaraciones(adaptador)]
    refs, del_discover = _descubrir(adaptador, desde, hasta, maximo)
    hallazgos += del_discover

    if not refs:
        hallazgos.append(
            Hallazgo(
                "documentos",
                "NO_EJECUTADA",
                f"`discover({desde}, {hasta})` no trajo ninguno, así que fetch, truth y "
                "strata no se han comprobado. No es un aprobado: es que no se ha mirado",
            )
        )
        return InformeConformidad(ident, 0, tuple(hallazgos))

    docs, del_fetch = _fetch(adaptador, refs)
    hallazgos += del_fetch
    hallazgos += _verdad(adaptador, refs)
    hallazgos += _estratos(adaptador, refs, docs, etiquetas_perfil)
    return InformeConformidad(ident, len(refs), tuple(hallazgos))
