"""§7.1 · El cliente de la API del BOE. **El único fichero del proyecto con `httpx`.**

Aquí se hacen cumplir, en código, las cinco condiciones de
[ADR-0031](../../../docs/adr/0031-el-xml-del-boe-se-baja-por-la-url-que-da-su-api.md).
No son adorno: el ADR dice que **si alguna se rompe, el argumento se cae entero**.

| Condición de ADR-0031 | Dónde vive |
|---|---|
| 1 · descubrir **sólo por la API** | **aquí**: `descargar` rechaza lo que no dio un sumario |
| 2 · 1 rps, sin paralelismo | el perfil; lo aplica `_espaciar` |
| 3 · `User-Agent` del proyecto | el perfil, y va en **cada** petición |
| 4 · caché: no rebajar lo que hay | **no aquí**: es de `corpus.harvest`, que tiene el manifiesto |
| 5 · atribución exacta | el perfil, y sale por `license()` |

## La condición 1, que es la que sostiene a las demás

La defensa de ADR-0031 es *«soy cliente de una API documentada, no un
rastreador»*, y **enumerar identificadores o seguir enlaces la vuelve falsa de
golpe**. Así que no se deja en una buena intención: este cliente **sólo baja URLs
que ha visto en un sumario**, y cualquier otra levanta `PolicyViolation` —código
2, la campaña no arranca—. La única URL que se construye es la del **endpoint del
sumario**, que es el que la documentación oficial publica.

Es una barrera, o sea que su único trabajo es ponerse roja. Su control negativo
está en `tests/unit/test_boe_api.py`, en el mismo hito.

## Precondiciones declaradas

- **No cachea.** Dos `descargar` de la misma URL son dos peticiones. La caché es
  de `corpus.harvest`, que es quien tiene el manifiesto con los hashes.
- **No reintenta.** Un fallo se devuelve como fallo con su causa; decidir si se
  reintenta es de quien orquesta la cosecha, que es quien sabe cuánto le queda de
  presupuesto de peticiones.
- **No interpreta el documento.** Devuelve el JSON del sumario y los bytes tal
  cual. Convertirlos en `DocRef` y en `RawDoc` es de `entity.boe`.
- **El espaciado es entre INICIOS de petición**, no una pausa después: un promedio
  sobre una ventana permitiría ráfagas, y una ráfaga es lo que un servidor nota.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import date

import httpx

from docbench_es.entity._sumario import Sumario, urls_de
from docbench_es.entity.base import RitmoPeticion
from docbench_es.errors import AdapterError, PolicyViolation

__all__ = ["SUMARIO_API", "BoeApi"]

SUMARIO_API = "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"
"""**La única URL que este proyecto construye**, y es el endpoint que documenta la
API oficial. Todo lo demás sale de un campo de la respuesta."""

ESPERA_HTTP_S = 45.0
"""Timeout por petición. El mismo que usó el sondeo sobre este origen."""


class BoeApi:
    """Cliente de la API del BOE con el ritmo y la identificación del perfil.

    `cliente`, `reloj` y `dormir` entran por parámetro para que la suite pueda
    correr **sin red y sin esperar de verdad**: con `httpx.MockTransport` y un
    reloj falso, los tests de ritmo tardan microsegundos. Un cliente que sólo se
    puede probar con red es un cliente que no se prueba en la puerta.
    """

    def __init__(
        self,
        ritmo: RitmoPeticion,
        cliente: httpx.Client | None = None,
        reloj: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._ritmo = ritmo
        self._cliente = cliente or httpx.Client(headers={"User-Agent": ritmo.user_agent})
        self._reloj = reloj
        self._dormir = dormir
        self._ultima: float | None = None
        self._autorizadas: set[str] = set()
        self._espaciados: list[float] = []

    @property
    def autorizadas(self) -> frozenset[str]:
        """Las URLs que algún sumario ha entregado. **Lo demás no se baja.**"""
        return frozenset(self._autorizadas)

    @property
    def espaciados(self) -> list[float]:
        """Los huecos MEDIDOS entre peticiones consecutivas, en segundos.

        **La unidad es la petición, no el documento.** Un documento del BOE son dos
        peticiones —PDF y XML—, así que medir entre documentos daría el doble y
        pasaría un umbral de 1 s con un ritmo real de 0,5. Es un error de unidad, y
        los errores grandes de este repo han sido de unidad: por eso el número sale
        de aquí, que es lo único que ve las peticiones sueltas.
        """
        return list(self._espaciados)

    def _espaciar(self) -> None:
        """Espera lo que falte para respetar el ritmo. **Antes** de pedir, no después."""
        ahora = self._reloj()
        if self._ultima is not None:
            falta = self._ritmo.espaciado_s - (ahora - self._ultima)
            if falta > 0:
                self._dormir(falta)
            self._espaciados.append(self._reloj() - self._ultima)
        self._ultima = self._reloj()

    def _pedir(self, url: str) -> bytes:
        """Una petición, con su ritmo, y con el código comprobado.

        **Nada de esto se apoya en «no ha lanzado excepción»**: un 404 o un 500
        llegan con `raise_for_status` desactivado y hay que mirarlos. Un fallo se
        convierte en `AdapterError` —código 4, infraestructura— porque que no se
        pueda llegar al corpus no es un resultado de medición.
        """
        respuesta = self._get(url)
        if respuesta.status_code != 200:
            raise AdapterError(f"{url} devolvió HTTP {respuesta.status_code}")
        return respuesta.content

    def _get(self, url: str, acepta: str | None = None) -> httpx.Response:
        """La petición cruda, con su ritmo. **El código lo mira quien llama.**

        Separado de `_pedir` porque un 404 no significa lo mismo en todas partes:
        en un documento es un fallo, y en un sumario es **un día sin boletín**
        —domingos y festivos—. Tratarlos igual haría que `discover` se muriera el
        primer domingo del rango.

        `acepta` no es decoración: **el endpoint del sumario devuelve HTTP 400 sin
        `Accept: application/json`**. Medido contra el origen real el 24 ago 2026,
        en la primera petición del piloto. Los documentos —PDF y XML— no lo llevan:
        son binarios y el servidor los sirve tal cual.
        """
        self._espaciar()
        # La identificacion va en CADA peticion y no en el cliente: si sólo la
        # pusiera el cliente que construye este objeto, un cliente inyectado —el de
        # los tests, o el de quien quiera reutilizar una sesión— saldría a la red
        # como `python-httpx/…`, y la condición 3 de ADR-0031 dejaría de cumplirse
        # sin que nada se pusiera rojo. Medido: pasaba.
        cabeceras = {"User-Agent": self._ritmo.user_agent}
        if acepta:
            cabeceras["Accept"] = acepta
        try:
            return self._cliente.get(
                url, timeout=ESPERA_HTTP_S, follow_redirects=True, headers=cabeceras
            )
        except httpx.HTTPError as exc:
            raise AdapterError(f"no se pudo pedir {url}: {exc}") from exc

    def sumario(self, dia: date) -> Sumario | None:
        """El sumario de un día, y **autoriza todas las URLs que trae dentro**.

        Es el único sitio donde crece `_autorizadas`. Que la autorización nazca
        aquí y no en un `add` suelto es lo que hace que la condición 1 no dependa
        de que alguien se acuerde de llamarlo.

        **`None` si ese día no hay boletín** (HTTP 404): domingos y festivos. Es un
        estado válido del origen, no un fallo, y quien recorre un rango tiene que
        contarlo aparte — *«un día que no se pudo consultar no es un descarte»*.
        Cualquier otro código sí es `AdapterError`.
        """
        respuesta = self._get(
            SUMARIO_API.format(fecha=dia.strftime("%Y%m%d")), acepta="application/json"
        )
        if respuesta.status_code == 404:
            return None
        if respuesta.status_code != 200:
            raise AdapterError(f"el sumario de {dia} devolvió HTTP {respuesta.status_code}")
        crudo = respuesta.content
        try:
            datos = json.loads(crudo)
        except json.JSONDecodeError as exc:
            raise AdapterError(f"el sumario de {dia} no es JSON: {exc}") from exc
        if not isinstance(datos, dict):
            raise AdapterError(f"el sumario de {dia} no es un mapa, es {type(datos).__name__}")
        self._autorizadas.update(urls_de(datos))
        datos_de = datos.get("data")
        dentro = datos_de.get("sumario") if isinstance(datos_de, dict) else None
        return dentro if isinstance(dentro, dict) else {}

    def descargar(self, url: str) -> bytes:
        """Baja una URL **que un sumario haya entregado**. Lo demás se rechaza.

        La condición 1 de ADR-0031, ejecutable. No es una comprobación de formato:
        una URL construida a mano puede ser perfectamente válida y aun así rompe el
        argumento entero con el que este proyecto justifica bajar el XML.
        """
        if url not in self._autorizadas:
            raise PolicyViolation(
                f"{url} no la ha entregado ningún sumario. ADR-0031, condición 1: el "
                "descubrimiento es SÓLO por la API — ni enlaces, ni identificadores "
                "adivinados, ni recorrido del sitio. Pide primero el sumario del día."
            )
        return self._pedir(url)
