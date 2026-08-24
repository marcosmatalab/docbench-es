"""Un BOE falso con la FORMA REAL de su sumario, y sin red.

**Por qué la forma importa tanto como el contenido.** Las tres rarezas del sumario
del BOE —`url_pdf` que es un objeto y no una cadena, los niveles que colapsan a
`dict` cuando tienen un elemento, y la clave `texto` que aparece a veces en
cualquier nivel— **no se descubren leyendo la documentación**: salieron de ejecutar
contra el origen. Un doble que no las reprodujera dejaría el adaptador verde en la
puerta y roto en la primera cosecha.

Así que este sumario falso las trae las tres, a propósito:

| Rareza | Dónde está aquí |
|---|---|
| `url_pdf` es objeto con `texto`, `pagina_inicial`, `pagina_final` | en los tres items |
| `url_xml` sí es cadena | en los tres items |
| un nivel colapsado a `dict` en vez de lista | `diario` |
| la clave `texto` entre dos niveles | dentro de `seccion` 3 |
| un `BOE-S-*`, que es el sumario del día y no un documento | sección 1 |

`httpx.MockTransport` hace el resto: **la suite no toca la red y no espera de
verdad**, porque el reloj y el `sleep` también entran por parámetro.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

import httpx

SUMARIO_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/20260803"
XML_URL = "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-17075"
PDF_URL = "https://www.boe.es/boe/dias/2026/08/03/pdfs/BOE-A-2026-17075.pdf"
XML_URL_2 = "https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-17076"
PDF_URL_2 = "https://www.boe.es/boe/dias/2026/08/03/pdfs/BOE-A-2026-17076.pdf"

XML_CON_TABLA = (
    '<?xml version="1.0" encoding="UTF-8"?><documento><texto>'
    "<p>Resolución de prueba con su tabla.</p>"
    "<table><thead><tr><th>Concepto</th><th>Importe</th></tr></thead>"
    '<tbody><tr><td rowspan="2">Tasa</td><td>10,00</td></tr>'
    "<tr><td>20,00</td></tr></tbody></table>"
    "</texto></documento>"
)
"""Con `rowspan="2"`, o sea estrato `celdas-combinadas`."""

XML_SIN_TABLA = (
    '<?xml version="1.0" encoding="UTF-8"?><documento><texto>'
    "<p>Anuncio sin tablas, sólo texto corrido.</p></texto></documento>"
)

PDF_FALSO = b"%PDF-1.7\n" + b"contenido que nadie parsea aqui\n" * 4


def _item(ident: str, xml: str, pdf: str, inicial: int, final: int) -> dict[str, object]:
    """Un item con las dos formas de URL que el BOE usa de verdad."""
    return {
        "identificador": ident,
        "titulo": f"Documento {ident}",
        "url_xml": xml,
        "url_pdf": {
            "texto": pdf,
            "szBytes": "232100",
            "pagina_inicial": str(inicial),
            "pagina_final": str(final),
        },
    }


SUMARIO: Mapping[str, object] = {
    "data": {
        "sumario": {
            # `diario` colapsado a dict: la lista de un elemento llega así.
            "diario": {
                "seccion": [
                    {
                        "codigo": "1",
                        "nombre": "I. Disposiciones generales",
                        "departamento": {
                            "nombre": "MINISTERIO DE HACIENDA",
                            "item": [
                                _item("BOE-A-2026-17075", XML_URL, PDF_URL, 100, 102),
                                # El sumario del día: NO es un documento.
                                _item("BOE-S-2026-186", XML_URL, PDF_URL, 1, 1),
                            ],
                        },
                    },
                    {
                        "codigo": "3",
                        "nombre": "III. Otras disposiciones",
                        # La clave `texto` entre dos niveles, que a veces está.
                        "texto": {
                            "departamento": {
                                "nombre": "MINISTERIO DE JUSTICIA",
                                "epigrafe": {
                                    "nombre": "Resoluciones",
                                    "item": _item(
                                        "BOE-A-2026-17076", XML_URL_2, PDF_URL_2, 200, 200
                                    ),
                                },
                            }
                        },
                    },
                    {
                        "codigo": "5",
                        "nombre": "V. Anuncios",
                        "departamento": {
                            "nombre": "AYUNTAMIENTOS",
                            "item": _item(
                                "BOE-B-2026-30000",
                                "https://www.boe.es/diario_boe/xml.php?id=BOE-B-2026-30000",
                                "https://www.boe.es/boe/dias/2026/08/03/pdfs/BOE-B-2026-30000.pdf",
                                1,
                                1,
                            ),
                        },
                    },
                ]
            }
        }
    }
}
"""Cinco items en tres secciones. Con el filtro `["1", "3"]` del perfil entran dos:
el `BOE-S-*` se descarta por ser el sumario y la sección 5 por el filtro."""

RESPUESTAS: dict[str, tuple[int, bytes]] = {
    SUMARIO_URL: (200, json.dumps(SUMARIO).encode("utf-8")),
    XML_URL: (200, XML_CON_TABLA.encode("utf-8")),
    PDF_URL: (200, PDF_FALSO),
    XML_URL_2: (200, XML_SIN_TABLA.encode("utf-8")),
    PDF_URL_2: (200, PDF_FALSO),
}


class Origen:
    """Un BOE falso que además **cuenta las peticiones**.

    El recuento no es decoración: es lo que permite comprobar que `fetch` no baja
    de más y que el ritmo se aplica entre peticiones, sin esperar de verdad.
    """

    def __init__(self, respuestas: dict[str, tuple[int, bytes]] | None = None) -> None:
        self.respuestas = dict(RESPUESTAS if respuestas is None else respuestas)
        self.pedidas: list[str] = []
        self.cabeceras: list[dict[str, str]] = []
        """Las cabeceras de cada peticion. El sumario del BOE devuelve **400** sin
        `Accept: application/json`, medido contra el origen real, asi que hay que
        poder comprobar que sale."""

    def _responder(self, peticion: httpx.Request) -> httpx.Response:
        url = str(peticion.url)
        self.pedidas.append(url)
        self.cabeceras.append(dict(peticion.headers))
        codigo, cuerpo = self.respuestas.get(url, (404, b""))
        return httpx.Response(codigo, content=cuerpo)

    def cliente(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self._responder))


class Reloj:
    """Reloj y `sleep` falsos. Lo que se duerme se anota, no se espera."""

    def __init__(self) -> None:
        self.ahora = 0.0
        self.dormido: list[float] = []

    def leer(self) -> float:
        return self.ahora

    def dormir(self, segundos: float) -> None:
        self.dormido.append(segundos)
        self.ahora += segundos
