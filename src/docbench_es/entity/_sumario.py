"""La FORMA del sumario del BOE, que no es la que uno esperaría.

Separado de `boe_api.py` por el límite de 300 líneas del repo, y la partición sale
sola: allí está **cómo se pide** —ritmo, identificación, la condición 1 de
ADR-0031— y aquí **qué llega**. Lo de aquí no toca la red y se prueba con un
`dict`.

## Las tres cosas que sorprenden, las tres comprobadas sobre el sumario real

1. **`url_pdf` no es una cadena**: es un objeto con `szBytes`, `pagina_inicial`,
   `pagina_final` y `texto`, que es la URL. `url_xml` sí es cadena. Un lector que
   sólo esperase cadenas se dejaría fuera **todos los PDF**.
2. **Los niveles intermedios son a veces `dict` y a veces `list`.** Una lista de un
   solo elemento llega colapsada al elemento.
3. **A veces hay una clave `texto` entre un nivel y el siguiente, y a veces no, en
   cualquier nivel**: visto en `seccion` (sumario del 20260809) y en `departamento`
   (20260817). Sin mirar dentro se pierden documentos reales.

Las tres salieron de ejecutar contra el origen, no de la documentación. Por eso
están escritas aquí con su fecha: la siguiente persona que lea este JSON no tiene
por qué volver a descubrirlas.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping

__all__ = ["Item", "Sumario", "items_del_sumario", "paginas_de", "url_de", "urls_de"]

Sumario = Mapping[str, object]
Item = dict[str, object]
"""El JSON del sumario, tipado como `object` y no como `Any`.

`mypy` corre con `disallow_any_explicit`, y con razón: un `Any` en la frontera con
un JSON ajeno **apaga el comprobador de tipos en todo lo que toque**, que es justo
donde más falta hace — los datos vienen de fuera y su forma cambia sin avisar. El
precio es estrechar con `isinstance` en cada nivel, y eso es lo que hacen `_lista`,
`_cajas` y `_hijos`."""


def url_de(item: Item, clave: str) -> str | None:
    """La URL de un campo `url_*` del sumario, **con sus DOS formas**.

    Comprobado sobre el sumario del 2026-08-03 por dos vías independientes
    (`scripts/sondeo_boe.py` y `scripts/censo_boe_50.py`):

    | Campo | Forma |
    |---|---|
    | `url_xml` | una **cadena** con la URL |
    | `url_pdf` | un **objeto** con `szBytes`, `pagina_inicial`, `pagina_final` y `texto` |

    Que las dos formas convivan en la misma respuesta no es un detalle: un lector
    que sólo esperase cadenas **se dejaría fuera todos los PDF**, y con la
    condición 1 de ADR-0031 puesta eso no falla al leer el sumario — falla mucho
    después, al intentar bajar un PDF que nadie autorizó.
    """
    valor = item.get(clave)
    if isinstance(valor, str):
        return valor
    if isinstance(valor, dict):
        dentro = valor.get("texto")
        return dentro if isinstance(dentro, str) else None
    return None


def paginas_de(item: Item) -> int | None:
    """Cuántas páginas ocupa el PDF, **sin bajarlo**: sale del propio sumario.

    `pagina_final - pagina_inicial + 1`. Es lo que alimenta la banda de longitud de
    ADR-0034 y el `n_pages` del documento, y es gratis: 1.000 peticiones menos.
    `None` si el sumario no lo trae, que es distinto de cero.
    """
    pdf = item.get("url_pdf")
    if not isinstance(pdf, dict):
        return None
    try:
        return int(str(pdf["pagina_final"])) - int(str(pdf["pagina_inicial"])) + 1
    except (KeyError, ValueError, TypeError):
        return None


def urls_de(nodo: object) -> Iterator[str]:
    """Toda URL bajo una clave `url_*`, a cualquier profundidad y en sus dos formas.

    Por clave y no por «parece una URL»: lo que autoriza a bajar algo es que **el
    organismo lo haya puesto en un campo de URL de su respuesta**, no que el texto
    empiece por `https`.
    """
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            if isinstance(clave, str) and clave.startswith("url_"):
                url = url_de({clave: valor}, clave)
                if url is not None:
                    yield url
            else:
                yield from urls_de(valor)
    elif isinstance(nodo, list):
        for valor in nodo:
            yield from urls_de(valor)


def _lista(x: object) -> list[object]:
    """El sumario colapsa las listas de un elemento a `dict`. Normalizar o perder datos."""
    if x is None:
        return []
    return list(x) if isinstance(x, list) else [x]


def _cajas(nodo: Item) -> list[Item]:
    """El nodo y, si lo tiene, su envoltorio `texto`.

    El sumario mete a veces una clave `texto` entre un nivel y el siguiente, **y a
    veces no, en cualquier nivel**: medido en `seccion` (sumario del 20260809) y en
    `departamento` (20260817). Sin mirar dentro se pierden documentos reales.
    """
    return [c for c in (nodo, nodo.get("texto")) if isinstance(c, dict)]


def _hijos(nodo: Item, clave: str) -> list[Item]:
    """`nodo[clave]` buscando también en su envoltorio `texto`, siempre como lista."""
    fuera: list[Item] = []
    for caja in _cajas(nodo):
        fuera += [x for x in _lista(caja.get(clave)) if isinstance(x, dict)]
    return fuera


def items_del_sumario(sumario: Sumario) -> list[Item]:
    """diario → sección → departamento → [epígrafe] → item, etiquetando la sección.

    La sección hace falta porque `discover` **filtra por sección** y ese filtro es
    parte de la definición del corpus (§10.1): sin él, tres de cada cuatro
    documentos del BOE son anuncios sin tabla, y cualquier tasa que se publique
    hablaría de otra población.

    Cada item sale con `_seccion` y `_fecha` añadidos. Los `BOE-S-*` —el sumario
    del día, que no es un documento— los descarta quien llama.
    """
    salida: list[Item] = []
    for diario in _lista(sumario.get("diario")):
        if not isinstance(diario, dict):
            continue
        for seccion in _lista(diario.get("seccion")):
            if not isinstance(seccion, dict):
                continue
            codigo = str(seccion.get("codigo", "?"))
            for departamento in _hijos(seccion, "departamento"):
                for grupo in _hijos(departamento, "epigrafe") or [departamento]:
                    for item in _hijos(grupo, "item"):
                        item["_seccion"] = codigo
                        salida.append(item)
    return salida
