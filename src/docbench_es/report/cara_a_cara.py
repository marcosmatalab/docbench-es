"""§12 · La cara a cara: **las mismas puntuaciones sobre el mismo denominador.**

Va aparte de `nivel1.py` por el límite de 300 líneas de `CLAUDE.md`, y la costura cae
donde tenía que caer: allí está lo que se mide **de cada extractor por separado**, y aquí
lo único que se puede decir **comparándolos**.

## Por qué existe

La regla de emparejado de `runs/l5/emparejado.yaml` tiene un sesgo de supervivencia
declarado: un extractor que detecta mal las tablas falla el recuento en más documentos,
ésos salen de SU cuenta, y su nota acaba calculada sobre **otro subconjunto, elegido por
él mismo**.

## El mecanismo es real; su DIRECCIÓN no lo era, y esto está medido

`emparejado.yaml` escribió *«cuanto peor detecta, más se le excluye y mejor pinta lo que
queda»*, cuya consecuencia comprobable es: al pasar al denominador común las notas bajan,
y bajan más las de menos cobertura. Medido en L5 sobre los cuatro, **dos suben y dos
bajan**, y la que más sube es la del extractor de cobertura **más baja**. O sea que ni el
sesgo tiene una dirección común ni la intersección es sin más «los documentos fáciles».
Las cuatro cifras y sus deltas, en la sección «La cara a cara» de `RESULTS.md`.

**Y de ahí sale por qué esto es un DENOMINADOR y no un factor de corrección.** Un sesgo
de signo conocido se corrige con una fórmula; uno cuyo signo no se sabe **ni por
extractor** sólo se puede evitar midiendo a todos sobre el mismo conjunto.

Que `evaluable_coverage` viaje pegado a la nota hace el sesgo **legible**, no lo quita.
Esto lo quita para la comparación: se puntúa a todos sobre **la intersección**.

**Y no es una segunda medida**: son las mismas puntuaciones con otro denominador.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.nivel1 import Nivel1

__all__ = ["BANDAS", "CaraACara", "cara_a_cara"]


@dataclass(frozen=True)
class CaraACara:
    """El mismo denominador para todos. **La única cuenta que contesta «cuál es mejor».**

    La regla de emparejado tiene un sesgo de supervivencia declarado en
    `runs/l5/emparejado.yaml`: un extractor que detecta mal las tablas falla el recuento en
    más documentos, ésos salen de SU cuenta, y **su TEDS acaba calculándose sobre otro
    subconjunto**. La DIRECCIÓN de ese sesgo se declaró y **no se cumplió**: está medida en
    el docstring del módulo, y es la razón por la que aquí hay un denominador y no una
    corrección.

    Que `evaluable_coverage` viaje pegado a la nota hace el sesgo **legible**, no lo quita.
    Esto lo quita para la comparación: se puntúa a todos sobre **la intersección**, los
    documentos donde **todos** acertaron el recuento.

    **`n` es un dato en sí.** Si de 338 los cuatro coinciden en el recuento en 150, eso
    dice algo sobre la dificultad del corpus que ninguna nota de TEDS dice — y se publica
    también, y sobre todo, si sale baja.

    **Lo que esto NO afirma: un ranking.** Mismo denominador es necesario y no suficiente;
    decir «A es mejor que B» exige la comparación pareada con su potencia, que es lo que
    L6 existe para hacer (ADR-0009).
    """

    extractores: tuple[str, ...]
    documentos: tuple[str, ...]
    teds: Mapping[str, float]
    poblacion: int
    """Los documentos con tabla en la verdad. El denominador de `n`."""
    suyo: Mapping[str, float | None]
    """Extractor → su TEDS sobre SU PROPIO conjunto evaluable. **El otro denominador.**

    Viaja aquí para que el salto entre los dos denominadores sea un NÚMERO y no una
    lectura: `teds[n] - suyo[n]` es lo que le cuesta —o le regala— a cada extractor pasar
    al conjunto común. Es aritmética sobre las mismas puntuaciones, no una medida nueva, y
    por eso sale del informe con su comando en vez de restarse a mano.

    **Y hace falta porque el signo de ese salto no es predecible**, que es lo que se midió
    en L5: `emparejado.yaml` declaró que todos los deltas serían negativos y más negativos
    cuanto menor la cobertura, y salieron de los dos signos.
    """
    por_banda: Mapping[str, tuple[int, int]]
    """Banda de páginas → (documentos donde coinciden TODOS, población de la banda).

    **Es lo que convierte el titular en un diagnóstico.** «Los cuatro coinciden en el
    recuento en el 24% de los documentos» dice que hay un problema; el desglose por banda
    dice **dónde**: si en los de una página coinciden siempre y en los largos casi nunca,
    la discrepancia es de LONGITUD y no de herramienta — y eso cambia a quién hay que
    mirar.

    **Medido en L5, ese ejemplo NO es lo que pasa.** El acuerdo no es monótono en las
    páginas: baja hasta su mínimo en la banda intermedia y **recupera** en la larga, así
    que la banda de páginas no es el factor que lo ordena. El candidato —declarado y **sin
    comprobar**— es la MORFOLOGÍA de las tablas, y el cruce que lo decidiría está escrito
    en `docs/metrics.md`, no aquí.
    """

    @property
    def n(self) -> int:
        return len(self.documentos)

    def delta(self, extractor: str) -> float | None:
        """Lo que le cuesta a `extractor` pasar al denominador común. **`None` no es 0,0.**

        Si le falta cualquiera de los dos lados no hay resta que hacer, y decirlo con un
        cero sería publicar «no le cuesta nada» donde lo que pasa es que no se ha medido.
        """
        comun, propio = self.teds.get(extractor), self.suyo.get(extractor)
        if comun is None or propio is None:
            return None
        return comun - propio

    def __str__(self) -> str:
        """**Sin intersección no hay empate: no hay comparación**, y se dice así.

        Un «0,0% sobre 338» se leería como un resultado malo; lo que pasa es que no hay
        ningún documento donde todos acertaran el recuento, o sea que no se les puede
        poner sobre el mismo denominador. Es la misma distinción que `NO_APLICABLE`
        contra `0,00`, un nivel más arriba.
        """
        if self.n == 0:
            return f"cara a cara: NO HAY COMPARACIÓN · 0 de {self.poblacion} documentos"
        return (
            f"cara a cara sobre {self.n} de {self.poblacion} documentos "
            f"({100 * self.n / self.poblacion:.1f}%) · {len(self.extractores)} extractores"
        )


BANDAS: tuple[tuple[str, int, int], ...] = (
    ("una página", 1, 1),
    ("2-10", 2, 10),
    ("11-50", 11, 50),
    (">50", 51, 10**9),
)
"""Las bandas del acuerdo. **La de UNA página va sola a propósito**: es donde el recuento
es trivial —o hay una tabla o no la hay— y por tanto donde un desacuerdo sería del
extractor y no del documento. Separarla es lo que permite decir si la discrepancia crece
con la longitud o no."""


def _banda(paginas: int) -> str:
    for nombre, lo, hi in BANDAS:
        if lo <= paginas <= hi:
            return nombre
    return "(sin páginas)"


def cara_a_cara(filas: Mapping[str, Nivel1], paginas: Mapping[str, int] | None = None) -> CaraACara:
    """Las mismas puntuaciones sobre la INTERSECCIÓN. **No es una segunda medida.**

    Con un solo extractor la intersección es su propio conjunto y la cara a cara no aporta
    nada; se calcula igual, y su `n` lo dice.

    `paginas` es opcional porque el desglose por banda es **información añadida**, no parte
    del número: sin él la cara a cara sigue siendo válida y `por_banda` sale vacío en vez
    de inventarse una banda.
    """
    if not filas:
        return CaraACara(extractores=(), documentos=(), teds={}, poblacion=0, por_banda={}, suyo={})
    comunes = set.intersection(*(set(f.por_documento) for f in filas.values()))
    documentos = tuple(sorted(comunes))
    poblacion = sorted({d for f in filas.values() for d in f.poblacion_documentos})
    por_banda: dict[str, tuple[int, int]] = {}
    if paginas:
        for nombre, _, _ in (*BANDAS, ("(sin páginas)", 0, 0)):
            de_la_banda = [d for d in poblacion if _banda(paginas.get(d, 0)) == nombre]
            if de_la_banda:
                coinciden = sum(1 for d in de_la_banda if d in comunes)
                por_banda[nombre] = (coinciden, len(de_la_banda))
    return CaraACara(
        extractores=tuple(sorted(filas)),
        documentos=documentos,
        teds={
            nombre: sum(f.por_documento[d] for d in documentos) / len(documentos)
            for nombre, f in sorted(filas.items())
            if documentos
        },
        poblacion=len(poblacion),
        por_banda=por_banda,
        suyo={nombre: f.metricas.teds for nombre, f in sorted(filas.items())},
    )
