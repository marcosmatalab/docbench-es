"""La aritmética de B5-bis, comprobada antes de que vea una sola medida real.

## Por qué existe este fichero

El estimador produce **el número que decide B1** —si L5 corre sobre los 1.000
documentos o sobre una muestra—. Un error en el estimador de razón o en el bootstrap
no se vería: saldría un número plausible con un intervalo plausible. Es exactamente
la clase de fallo que la regla de oro 2 existe para cerrar.

## Las tres cosas que se afirman aquí

1. **La suma pondera por páginas**, no por documentos. Un coste por página constante
   sobre las tres bandas tiene que dar exactamente las páginas del censo.
2. **El estimador de banda es de razón**, `Σcoste / Σpáginas`, y **no** la media de
   los cocientes por documento. Las dos coinciden cuando todos los documentos miden
   lo mismo, así que el caso de prueba tiene que ser uno donde NO coincidan.
3. **El bootstrap remuestrea DOCUMENTOS**, que es la regla de oro 3. Su firma
   observable: una banda con **un solo documento** no aporta ninguna anchura, porque
   remuestrearla siempre devuelve el mismo documento. Si remuestreara páginas, sí
   aportaría — y ése es el intervalo falsamente estrecho que la regla prohíbe.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from estimar_computo import intervalo, pendiente, razon, total  # noqa: E402


def test_un_coste_por_pagina_de_uno_da_exactamente_las_paginas_del_censo() -> None:
    """La suma pondera por PÁGINAS. Si el coste por página vale 1 en las tres bandas,
    el total tiene que ser el número de páginas, venga como venga repartido."""
    pesos = {"a": 3199, "b": 3329, "c": 3770}
    por_b = {b: [(10.0, 10.0), (4.0, 4.0)] for b in pesos}  # 1,0 por página en todas
    assert total(por_b, pesos) == float(sum(pesos.values()))


def test_la_banda_pondera_por_paginas_y_no_es_la_media_de_los_cocientes() -> None:
    """Un documento de 10 páginas a 2,0 y uno de 1 página a 1,0.

    Estimador de razón: 21/11 = 1,909. Media de los cocientes: 1,5. **Son distintos**,
    y el que corresponde a una suma ponderada por páginas es el primero: el documento
    largo aporta diez veces más páginas al total, así que pesa diez veces más.
    """
    docs = [(20.0, 10.0), (1.0, 1.0)]
    assert razon(docs) == 21.0 / 11.0
    media_de_cocientes = (20.0 / 10.0 + 1.0 / 1.0) / 2
    assert media_de_cocientes == 1.5
    assert razon(docs) != media_de_cocientes


def test_el_bootstrap_remuestrea_documentos_y_no_paginas() -> None:
    """La firma observable de la regla de oro 3.

    Banda `sola`: **un** documento de 500 páginas. Remuestrear documentos con
    reemplazo dentro de ella devuelve siempre ese mismo documento, así que **no aporta
    anchura**. Banda `varias`: documentos con coste por página distinto, así que sí.
    """
    pesos = {"sola": 1000, "varias": 1000}
    sola = {"sola": [(500.0, 500.0)], "varias": [(1.0, 1.0)]}
    lo, hi = intervalo(sola, pesos, semilla=1)
    assert hi - lo == 0.0, (
        f"con un documento por banda el intervalo no puede tener anchura: {lo}-{hi}"
    )

    varias = {"sola": [(500.0, 500.0)], "varias": [(1.0, 1.0), (9.0, 1.0), (5.0, 1.0)]}
    lo2, hi2 = intervalo(varias, pesos, semilla=1)
    assert hi2 - lo2 > 0.0, "con documentos distintos el intervalo tiene que tener anchura"


def test_el_intervalo_es_reproducible_y_rodea_al_punto() -> None:
    """Misma semilla, mismo intervalo — o el número no se puede reproducir, que es la
    regla de oro 2. Y el punto tiene que caer dentro."""
    pesos = {"a": 500, "b": 500}
    por_b = {"a": [(2.0, 1.0), (8.0, 1.0), (4.0, 1.0)], "b": [(1.0, 1.0), (3.0, 1.0), (5.0, 1.0)]}
    primero = intervalo(por_b, pesos, semilla=7)
    assert primero == intervalo(por_b, pesos, semilla=7)
    punto = total(por_b, pesos)
    assert primero[0] <= punto <= primero[1]


def test_con_n_pequena_los_percentiles_saturan_y_eso_fija_la_resolucion() -> None:
    """**Una propiedad del método que hay que saber antes de publicar el intervalo.**

    Con 3 documentos por banda, la distribución de remuestreos es tan discreta que los
    percentiles 2,5 y 97,5 caen en los mismos extremos **con cualquier semilla**. No es
    un fallo del estimador: es que su resolución la fija `n`, y con `n` pequeña el
    intervalo no es continuo. Se descubrió aquí, porque una versión anterior de este
    fichero afirmaba «semillas distintas dan intervalos distintos» y se cayó.

    Con `n` mayor deja de saturar, y eso es lo que se afirma en la segunda mitad.
    """
    pesos = {"a": 500, "b": 500}
    chica = {"a": [(2.0, 1.0), (8.0, 1.0), (4.0, 1.0)], "b": [(1.0, 1.0), (3.0, 1.0), (5.0, 1.0)]}
    assert intervalo(chica, pesos, semilla=7) == intervalo(chica, pesos, semilla=8), (
        "con n=3 los percentiles deberían saturar; si esto deja de pasar, el comentario "
        "de arriba es falso y hay que reescribirlo"
    )

    grande = {b: [(float(i % 7 + 1), 1.0) for i in range(30)] for b in pesos}
    assert intervalo(grande, pesos, semilla=7) != intervalo(grande, pesos, semilla=8), (
        "con n=30 el bootstrap tiene que ser estocástico de verdad"
    )


def test_una_pendiente_positiva_delata_un_preregistro_falso() -> None:
    """**El control negativo.**

    El pre-registro afirma, ANTES de medir, que excluir el documento de 309 páginas
    sesga el total al alza —o sea conservador— porque el coste por página **baja** con
    la longitud cuando hay un coste fijo por documento. Eso es una afirmación falsable,
    y ésta es la comprobación: si la pendiente sale positiva, era falsa.

    Sin este test, `pendiente` podría devolver siempre un número negativo y el informe
    diría «el argumento se sostiene» sin haber mirado nada.
    """
    # coste/página que BAJA con las páginas: 10/10=1,0 · 15/20=0,75 · 20/40=0,5
    baja = [(10.0, 10.0), (15.0, 20.0), (20.0, 40.0)]
    assert pendiente(baja) < 0

    # coste/página que SUBE: 5/10=0,5 · 20/20=1,0 · 60/40=1,5
    sube = [(5.0, 10.0), (20.0, 20.0), (60.0, 40.0)]
    assert pendiente(sube) > 0, (
        "una pendiente que sube tiene que salir positiva, o el informe miente"
    )
