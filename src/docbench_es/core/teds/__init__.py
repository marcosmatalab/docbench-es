"""§9.2 · `core.teds` — la métrica de estructura. Puro: entran tablas, sale un número.

    TEDS = 1 - distancia_de_edición(pred, gold) / max(nodos(pred), nodos(gold))

**Validado contra la implementación de referencia de PubTabNet sobre sus propios
casos**, los 20 de `src/sample_gt.json` y `src/sample_pred.json` de su repo,
congelados en `tests/fixtures/pubtabnet/` con su procedencia y su licencia. §9.2
lo dice sin rodeos: *«Si no reproduce sus números, la implementación está mal»*, y
*«no se valida a ojo»*, porque TEDS no tiene valores intuibles.

**Qué se valida exactamente, que es la parte que se puede leer mal.** La
referencia trabaja sobre HTML crudo y **no normaliza nada**: tokeniza la celda en
caracteres sueltos y compara con Levenshtein. Este proyecto trabaja sobre
`CanonicalTable`, cuyo texto ya pasó por las seis normalizaciones de L1. Para que
la comparación mida el ALGORITMO y no la convención, los golden se generan dando
a la referencia **el mismo contenido** que ve este código: el render canónico de
las mismas tablas. La diferencia que introduce normalizar está medida aparte y
publicada en `RESULTS.md`; ver ADR-0020.

**Casos degenerados**, que manda §12 y donde la referencia hace otra cosa:

- las dos tablas vacías → **1.0**. La referencia devuelve `0.0` para dos cadenas
  vacías y **revienta con `ZeroDivisionError`** ante `<table></table>`, porque
  divide por un número de nodos que es cero. §12 define el caso y §12 gana.
- una vacía y la otra no → **0.0**, que sí coincide con la referencia.
"""

from __future__ import annotations

from collections.abc import Iterable

from docbench_es.core.teds._arbol import Nodo, a_arbol, a_html, n_nodos
from docbench_es.core.teds._distancia import distancia
from docbench_es.types import CanonicalTable, TedsReport

__all__ = [
    "SUELO_DE_PUBLICACION",
    "Nodo",
    "a_arbol",
    "a_html",
    "n_nodos",
    "para_publicar",
    "teds",
    "teds_batch",
    "teds_struct",
]

SUELO_DE_PUBLICACION = 0.0
"""El suelo que se aplica **al publicar**, nunca al calcular (ADR-0023)."""


def _puntuar(pred: CanonicalTable, gold: CanonicalTable, *, solo_estructura: bool) -> float:
    arbol_pred = a_arbol(pred, solo_estructura=solo_estructura)
    arbol_gold = a_arbol(gold, solo_estructura=solo_estructura)
    total = max(n_nodos(arbol_pred), n_nodos(arbol_gold))
    if total == 0:
        # Las dos vacías. §12: «se define como 1 si las dos lo están». Sin esta
        # rama sería una división por cero, que es justo lo que le pasa a la
        # implementación de referencia.
        return 1.0
    if n_nodos(arbol_pred) == 0 or n_nodos(arbol_gold) == 0:
        return 0.0
    return 1.0 - distancia(arbol_pred, arbol_gold) / total


def para_publicar(valor: float) -> float:
    """El TEDS tal y como va a una tabla de resultados: recortado por abajo a 0.

    **Es una decisión de PRESENTACIÓN y sólo de presentación** (ADR-0023). El
    valor calculado no se toca nunca: `teds()` devuelve el número de la
    referencia, negativo incluido, y esta función existe para que el recorte
    tenga un solo sitio, un nombre y un test, en vez de aparecer disperso en el
    informe de L5.

    **Qué significa un TEDS negativo, en una frase:** convertir la tabla predicha
    en la real cuesta más ediciones que nodos tiene la mayor de las dos, o sea
    que la predicción es **peor que no haber predicho nada** —una predicción
    vacía puntúa 0—.

    Quien publique tiene que aplicar el mismo criterio a los valores por
    documento **y** al agregado, y **decir cuántos se recortaron**. Publicar una
    media sobre valores crudos junto a una columna recortada sería mezclar dos
    escalas en la misma tabla. Ver LIMITS 46, que lo deja como requisito de L5.
    """
    return max(valor, SUELO_DE_PUBLICACION)


def teds(pred: CanonicalTable, gold: CanonicalTable) -> float:
    """TEDS entre la tabla predicha y la real. 1 es idéntica.

    **El rango real es [-1, 1], no [0, 1].** La distancia se calcula sobre los
    árboles con su raíz y el denominador cuenta sólo los descendientes, así que
    entre dos tablas suficientemente distintas la distancia se pasa del
    denominador. Medido: -0,142857 sobre el par congelado en `casos_limite.json`,
    y **la implementación de referencia devuelve exactamente lo mismo**. Aquí no
    se recorta: para publicar está `para_publicar()` (ADR-0023).

    **PRECONDICIÓN, y no se comprueba aquí.** `teds` asume que las dos tablas
    **pasan `core.canonical.validate()` sin hallazgos fatales**. En concreto
    asume que ninguna celda solapa con otra, que ningún span sale del rango y que
    ningún span es menor que 1.

    **Qué NO comprueba:** nada de lo anterior. Si la precondición no se cumple,
    `teds` **devuelve un número igualmente**, y ese número **no es
    interpretable**: la rejilla de la que sale no corresponde a ninguna tabla.
    Medido: una tabla con `SOLAPE` saca **0,75** contra una tabla buena, que es
    una nota de aspecto perfectamente normal.

    No se valida dentro por lo mismo que decidió ADR-0019 —los invariantes se
    detectan a posteriori, no se impiden— y porque §9.2 fija la firma en
    `-> float`: validar aquí obligaría a lanzar o a devolver `None`. Pero ADR-0019
    permite no validar, **no permite no declararlo**, y por eso la precondición
    está aquí y no en un comentario. Quien puntúa comprueba: LIMITS 47.
    """
    return _puntuar(pred, gold, solo_estructura=False)


def teds_struct(pred: CanonicalTable, gold: CanonicalTable) -> float:
    """TEDS-S: sólo estructura, ignora el contenido de las celdas.

    Es donde se ve la diferencia entre un HUECO y una CELDA VACÍA: con el
    contenido ignorado, una celda vacía es idéntica a una llena y la tabla puntúa
    1,0, mientras que el hueco —un `<td>` que no existe— sigue costando un nodo.
    Medido contra la referencia: 1,000000 contra 0,857143 sobre el mismo par.
    """
    return _puntuar(pred, gold, solo_estructura=True)


def _es_evaluable(pred: CanonicalTable, gold: CanonicalTable) -> bool:
    """Si el par se puede puntuar sin castigar al extractor por su formato.

    ADR-0006 y la regla de oro 4: **un extractor que no expresa `rowspan` sale
    `NO_APLICABLE`, no cero**. Un cero diría que lo intentó y falló; lo que pasa
    es que su formato no puede con lo que la verdad tiene. La condición es que la
    tabla real traiga celdas combinadas y el predicho declare que no sabe
    expresarlas.
    """
    gold_combina = any(c.rowspan > 1 or c.colspan > 1 for c in gold.cells)
    return not (gold_combina and not pred.expresses_spans)


def teds_batch(
    pairs: Iterable[tuple[str, CanonicalTable, CanonicalTable]],
    *,
    solo_estructura: bool = False,
) -> TedsReport:
    """TEDS por documento, con su cobertura evaluable y sus `NO_APLICABLE`.

    Cada par es `(clave, predicha, real)`. La clave es la del documento, no la de
    la tabla: es la unidad de agrupación del bootstrap de L6, y por eso viaja
    hasta aquí en vez de reconstruirse después.

    **El agregado es `None` si no hay un solo par evaluable**, y nunca cero: cero
    diría que todos fallaron. Y la cobertura sale siempre al lado, porque una nota
    calculada sobre un subconjunto no se compara con otra sin decirlo.

    **Un documento puede traer VARIAS tablas, y ninguna se pierde.** La clave es
    la del documento, así que varios pares la comparten; la nota del documento es
    **la media de sus tablas evaluables**. Antes esto era un `dict[clave] = nota`
    y el par repetido **sobrescribía al anterior en silencio**: la tabla mal
    extraída desaparecía del informe y `evaluable_coverage` seguía diciendo 1,0.
    Eso rompía la regla de oro 6 y sesgaba el agregado hacia arriba justo en los
    documentos con más tablas, que son los peores. Ver ADR-0024.

    **La cobertura se cuenta sobre TABLAS, no sobre documentos**, que es lo que
    dice §6: *«sobre cuántas tablas se pudo calcular»*. Con una tabla por
    documento las dos cuentas coinciden, y por eso el fallo no se veía.
    """
    notas: dict[str, list[float]] = {}
    tablas_por_documento: dict[str, int] = {}
    no_evaluables = 0
    for clave, pred, gold in pairs:
        notas.setdefault(clave, [])
        tablas_por_documento[clave] = tablas_por_documento.get(clave, 0) + 1
        if _es_evaluable(pred, gold):
            notas[clave].append(_puntuar(pred, gold, solo_estructura=solo_estructura))
        else:
            no_evaluables += 1
    por_documento: dict[str, float | None] = {
        clave: sum(vs) / len(vs) if vs else None for clave, vs in notas.items()
    }
    evaluables = [v for v in por_documento.values() if v is not None]
    n_tablas = sum(tablas_por_documento.values())
    return TedsReport(
        per_document=por_documento,
        aggregate=sum(evaluables) / len(evaluables) if evaluables else None,
        evaluable_coverage=(n_tablas - no_evaluables) / n_tablas if n_tablas else 0.0,
        not_applicable=tuple(c for c, v in por_documento.items() if v is None),
    )
