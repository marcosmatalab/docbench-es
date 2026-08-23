"""Distancia de edición de árbol, con el coste EXACTO de la referencia.

La referencia usa APTED con un `CustomConfig`. Aquí va **Zhang-Shasha**, que es
el algoritmo clásico y resuelve el mismo problema —distancia de edición óptima
entre árboles ORDENADOS con costes de borrado, inserción y renombrado—, así que
da el mismo número. APTED es más rápido; Zhang-Shasha cabe en un fichero, no
añade dependencia al núcleo puro y es lo que permite que `make fast` no necesite
red ni ruedas compiladas.

**Que den el mismo número no se supone: se mide.** Los golden de
`tests/fixtures/pubtabnet/` los calcula APTED, y el criterio de aceptación de L2
es que esto coincida con ellos a cuatro decimales.

El coste, copiado de `CustomConfig` línea a línea:

- borrar o insertar un nodo: **1**.
- renombrar: **1** si cambia la etiqueta, el `colspan` o el `rowspan`.
- si los dos son `td` con la misma forma y **alguno** tiene contenido: la
  distancia de Levenshtein entre sus contenidos **normalizada por la longitud del
  más largo**, o sea un número entre 0 y 1.
- si los dos están vacíos: **0**. Es el `if node1.content or node2.content` de la
  referencia, y no es un detalle: sin él, dos celdas vacías costarían 0/0.
"""

from __future__ import annotations

from docbench_es.core.teds._arbol import Nodo

BORRAR = 1.0
INSERTAR = 1.0


def _levenshtein(a: tuple[str, ...], b: tuple[str, ...]) -> int:
    """Levenshtein sobre secuencias de TOKENS, no sobre cadenas.

    La referencia tokeniza la celda en caracteres sueltos —`list(node.text)`— y
    llama a `distance.levenshtein` sobre esa lista. Con texto plano coincide con
    la distancia sobre la cadena, pero la unidad declarada es el token, que es lo
    que importa el día que una celda traiga marcado inline.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previa = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        actual = [i]
        for j, cb in enumerate(b, start=1):
            actual.append(min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + (ca != cb)))
        previa = actual
    return previa[-1]


def renombrar(a: Nodo, b: Nodo) -> float:
    """El coste de convertir `a` en `b` sin tocar sus hijos."""
    if a.tag != b.tag or a.colspan != b.colspan or a.rowspan != b.rowspan:
        return 1.0
    if a.tag == "td" and (a.contenido or b.contenido):
        uno = a.contenido or ()
        otro = b.contenido or ()
        return _levenshtein(uno, otro) / max(len(uno), len(otro))
    return 0.0


def _postorden(raiz: Nodo) -> tuple[list[Nodo], list[int]]:
    """Los nodos en postorden y, para cada uno, su hoja más a la izquierda.

    Es la preparación de Zhang-Shasha: `izquierda[i]` es el índice en postorden
    de la hoja más a la izquierda del subárbol de `i`, y con eso los subbosques
    se identifican por un intervalo.
    """
    nodos: list[Nodo] = []
    izquierda: list[int] = []

    def visita(n: Nodo) -> int:
        primera = -1
        for h in n.hijos:
            indice = visita(h)
            if primera < 0:
                # La hoja más a la izquierda del PRIMER HIJO, no el primer hijo.
                # Son cosas distintas en cuanto hay un nivel más de profundidad, y
                # confundirlas rompe el índice del subbosque: `table` tendría como
                # hoja izquierda a `tbody` en vez de a su primera celda.
                primera = izquierda[indice]
        nodos.append(n)
        yo = len(nodos) - 1
        izquierda.append(primera if primera >= 0 else yo)
        return yo

    visita(raiz)
    return nodos, izquierda


def _claves(izquierda: list[int]) -> list[int]:
    """Los `keyroots`: los nodos que no son el hijo más a la izquierda de nadie."""
    vistos: set[int] = set()
    claves: list[int] = []
    for i in range(len(izquierda) - 1, -1, -1):
        if izquierda[i] not in vistos:
            vistos.add(izquierda[i])
            claves.append(i)
    return sorted(claves)


def distancia(a: Nodo, b: Nodo) -> float:
    """Zhang-Shasha entre dos árboles de TEDS.

    Coste: O(|a|·|b|·altura(a)·altura(b)) en el peor caso, y **medido**
    (`scripts/coste_teds.py`, mediana de 3): 101 ms a 20x8, **1617 ms a 60x10** y
    **4712 ms a 100x10**.

    Aquí decía «para una tabla de documento es inmediato» y que sólo lo dispararía
    «una tabla de miles de filas». **Las dos cosas eran falsas y ninguna estaba
    medida**: bastan 100 filas para pasar de 4 s. Ver `LIMITS.md` 42, donde está
    la decisión que L5 tiene que tomar con estos números delante.
    """
    nodos_a, izq_a = _postorden(a)
    nodos_b, izq_b = _postorden(b)
    n, m = len(nodos_a), len(nodos_b)
    arbol = [[0.0] * m for _ in range(n)]

    for i in _claves(izq_a):
        for j in _claves(izq_b):
            # Distancia entre los subbosques que cuelgan de `i` y de `j`.
            base_i, base_j = izq_a[i], izq_b[j]
            alto, ancho = i - base_i + 2, j - base_j + 2
            bosque = [[0.0] * ancho for _ in range(alto)]
            for x in range(1, alto):
                bosque[x][0] = bosque[x - 1][0] + BORRAR
            for y in range(1, ancho):
                bosque[0][y] = bosque[0][y - 1] + INSERTAR
            for x in range(1, alto):
                for y in range(1, ancho):
                    ni, nj = base_i + x - 1, base_j + y - 1
                    borrar = bosque[x - 1][y] + BORRAR
                    insertar = bosque[x][y - 1] + INSERTAR
                    if izq_a[ni] == base_i and izq_b[nj] == base_j:
                        # Los dos son árboles enteros: se pueden emparejar.
                        cambiar = bosque[x - 1][y - 1] + renombrar(nodos_a[ni], nodos_b[nj])
                        bosque[x][y] = min(borrar, insertar, cambiar)
                        arbol[ni][nj] = bosque[x][y]
                    else:
                        anterior = bosque[izq_a[ni] - base_i][izq_b[nj] - base_j]
                        bosque[x][y] = min(borrar, insertar, anterior + arbol[ni][nj])
    return arbol[n - 1][m - 1]
