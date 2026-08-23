"""Un recuento volátil no puede decir una cosa en un documento y otra en el resto.

**El fallo que cierra, con su fecha.** El cierre de L2 subió los mutantes de 12 a
18 y los tests fuera del arnés de 38 a 23. La corrección se escribió en
`RESULTS.md`, con su nota explicando el cambio… y **se quedó vieja en `LIMITS.md`
51, en `ESTADO.md` y en `.claude/skills/cerrar/SKILL.md`**, los tres dentro del
mismo commit, uno de ellos afirmando además que `teds_batch` no tenía mutante
cuando `batch_sobrescribe` ya apuntaba a él.

`scripts/ancla.py` impide editar a ciegas **un** documento. Nada impedía corregir
uno y olvidar tres, y eso es una clase distinta: no es un error de edición, es que
**el mismo número vive en cuatro sitios y sólo uno se actualiza**.

## Por qué ESTE mecanismo y no otro

**Descartado: comparar entre documentos por regex** —«que todas las cifras que
aparecen en más de un sitio concuerden»—. Habría cazado *este* caso, pero no el
peor: **si los cuatro documentos dicen 12 y la realidad es 18, concuerdan y el
test pasa en verde**. Comparar copias entre sí no comprueba nada contra el mundo;
sólo comprueba que se copiaron bien. (Verificado por la auditoría de `b7cc6c3`:
metiendo un mutante de más en el `PLAN` sin tocar ningún documento, esto se pone
rojo y nombra las seis apariciones.)

**Descartado: que `matar.py` escriba los recuentos a un JSON.** Ese JSON sólo está
al día si alguien se acuerda de correr `matar.py`. Sería una **quinta copia capaz
de quedarse vieja**, o sea el mismo fallo una capa más abajo, y con más apariencia
de autoridad.

**Elegido: calcularlos donde no pueden estar viejos.** `conftest.py` los computa
en `pytest_collection_modifyitems`, o sea **en cada `make fast`**, leyendo el
`PLAN` de `matar.py`. No hay fichero almacenado, así que no hay nada que
sincronizar, y el recuento es exacto con la parametrización ya resuelta.

## El criterio con el que se escriben los patrones

**Ante la duda, el patrón se ESTRECHA, no se ensancha.** Un patrón laxo se pone
rojo contra prosa correcta, y un candado que da rojos falsos enseña a ignorar el
color — que es el argumento del límite 25 de este repo. Un patrón estrecho, en
cambio, deja una redacción sin comprobar, y **eso ya está declarado en el límite
54**. Entre un hueco declarado y un falso rojo, el hueco.

Corolario: cuando una redacción de un documento no casa con ningún patrón, la
respuesta por defecto es **cambiar la redacción a la canónica**, no aflojar el
patrón para que quepa.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from conftest import RecuentoDegenerado, exigir_sano, fuera_por_fichero, recuentos

RAIZ = Path(__file__).resolve().parents[2]

PALABRAS = {
    "cero": 0,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciséis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "veintiocho": 28,
}
"""Este repo escribe los números en prosa tanto como en cifra —«los dieciocho
mutantes del repo mueren»—, así que un patrón que sólo mire dígitos deja fuera
justo las frases de titular."""

_N = r"(\d+|[a-záéíóúñ]+)"

PATRONES: tuple[tuple[str, str], ...] = (
    # ---- mutantes: el número va SIEMPRE pegado a la palabra `mutantes` ----
    ("mutantes", rf"{_N} mutantes(?: del repo)? mueren"),
    ("mutantes", rf"[Ss]on {_N} mutantes, no \d+"),
    # `{_N} mutantes existentes` a secas casaba con «Los 12 mutantes existentes
    # antes de este cierre», que es prosa histórica correcta. «sobre los» fija
    # que la frase habla del censo de HOY, que es lo único que este test sabe.
    ("mutantes", rf"sobre los {_N} mutantes existentes"),
    ("mutantes", rf"{_N} mutantes (?:están versionados|se versionan)"),
    ("mutantes", rf"[Ll]os {_N} mutantes apuntan"),
    # La forma de `ESTADO.md`:15 —«21 mutantes, todos mueren»—, que la coma y el
    # «todos» dejaban escapar: era un PUNTO CIEGO en el documento que el hook
    # `SessionStart` inyecta entero en cada sesión. Reproducido antes de taparlo:
    # subiendo el PLAN a 22 sin tocar documentos, el mensaje de error nombraba
    # RESULTS x3, LIMITS y la skill, y **no ESTADO**.
    ("mutantes", rf"{_N} mutantes, todos mueren"),
    # ---- dentro / total: sólo la forma canónica «cubre N de M tests» ----
    # `cubre {_N} de \d+` a secas casaba con «cubre 3 de 7 casos», que no habla de
    # tests. Exigir `tests` detrás obliga a que la prosa sea canónica, y ésa es la
    # dirección correcta: se arregla la frase del documento, no el patrón.
    ("dentro", rf"cubr[eí]a?n? {_N} de \d+ tests"),
    ("total", rf"cubr[eí]a?n? \d+ de {_N} tests"),
    # ---- el control negativo del arnés: `muertes` es obligatorio ----
    # Era `0 (?:muertes )?de {_N} tests`, y el «muertes» opcional lo hacía casar
    # con CUALQUIER «0 de N tests». Con `dentro=0` de una colección parcial, el
    # propio texto de prueba «el arnés cubre 0 de 5 tests» capturaba el 5 y se
    # comparaba contra dentro. Lo reportó la auditoría en frío de `b7cc6c3`.
    ("dentro", rf"0 muertes de {_N} tests"),
    ("dentro", rf"control negativo 0 de {_N}"),
    # ---- fuera: siempre pegado a `tests` o a una forma inequívoca ----
    # `[Ll]os {_N} restantes` a secas casaría con «los cinco conversores
    # restantes», que es prosa correcta de este repo y no habla de tests.
    ("fuera", rf"{_N} tests restantes"),
    ("fuera", rf"[Ll]os {_N} tests que quedan fuera"),
    ("fuera", rf"esos {_N} tests"),
    ("fuera", rf"{_N} tests quedaban fuera"),
    ("total", rf"suite ya en {_N} tests"),
    ("total", rf"suite entera: \d+ de {_N} tests"),
    ("dentro", rf"suite entera: {_N} de \d+ tests"),
)

NOMBRES_PROPIOS = frozenset({"los dos mutantes"})
"""Frases que en este repo son un NOMBRE, no una cantidad.

**«Los dos mutantes» es el paso 2 de `/cerrar`** —`siempre_ok` x `siempre_roto`—,
y aparece con ese sentido en seis sitios: el título del paso en la skill, el de la
sección de `RESULTS.md`, dos veces en `CHANGELOG.md`, y en dos tests. No es
hipotético: `CHANGELOG.md` dice hoy «Los dos mutantes van versionados y **mueren**
en 20 y 7 tests», y **quitar «van versionados y» al reescribir esa línea pondría
la puerta roja con una frase cierta**.

**La adyacencia NO cierra este riesgo**, y creer que sí lo cerraba fue un error
publicado: en cuanto la frase sigue con el verbo natural —«los dos mutantes
mueren»— casa y captura el 2. Lo que la adyacencia hace es distinto y más
modesto: impide que un número **suelto** cerca de la palabra se lea como recuento.
Contra un nombre propio que YA lleva el número dentro no puede hacer nada, porque
la forma es idéntica a la del recuento. Por eso hace falta una lista, y por eso la
lista es explícita en vez de un patrón más retorcido.

Se comprueba contra la ventana que rodea al match, no contra la frase entera: así
«Los 21 mutantes apuntan…» no se ve afectado."""


def _es_nombre_propio(plano: str, inicio: int, fin: int) -> bool:
    ventana = plano[max(0, inicio - 6) : fin].lower()
    return any(nombre in ventana for nombre in NOMBRES_PROPIOS)


HISTORICOS: dict[str, str] = {
    # El contexto va SIN comillas invertidas ni asteriscos, porque se compara
    # contra el texto ya aplanado por `_plano`. Escribirlo con el markdown puesto
    # hacía que la excepción no casara nunca.
    "nueve mutantes están versionados": (
        "Los nueve mutantes están versionados en scripts/mutantes/, porque la regla"
    ),
    "nueve mutantes se versionan": (
        "Los nueve mutantes se versionan en scripts/mutantes/, con matar.py"
    ),
}
"""Citas de un número **superado**, en la sección del hito que lo midió.

Las dos son de L1, que cerró con nueve mutantes. La clave es la frase que casa; el
valor es **la oración entera que tiene que seguir estando ahí**. Si alguien
reescribe esa oración, la excepción deja de aplicarse y el test **se cae** — que
es lo que se quiere. Eximir el fichero entero escondería también los errores
nuevos, y `RESULTS.md` es justo donde más números viven."""


def _documentos() -> list[Path]:
    """Todo lo que este repo publica, `.claude/` INCLUIDO.

    `.claude/skills/` no es documentación de adorno: es el guion que la siguiente
    sesión ejecuta. El tercer «12» del cierre de L2 estaba ahí, y una comprobación
    que sólo mirara `*.md` de la raíz lo habría dejado pasar.
    """
    sueltos = [
        RAIZ / n for n in ("RESULTS.md", "LIMITS.md", "ESTADO.md", "CHANGELOG.md", "MANUAL.md")
    ]
    return (
        sueltos + sorted((RAIZ / "docs").rglob("*.md")) + sorted((RAIZ / ".claude").rglob("*.md"))
    )


def _plano(texto: str) -> str:
    """Sin asteriscos, sin comillas invertidas y con los espacios colapsados.

    Las tres cosas hacen falta y las tres salieron de fallar: el énfasis de
    markdown parte `**18 mutantes**` por sitios distintos según dónde caiga la
    negrita; las comillas invertidas rompen `` `ancla` (5) `` contra `ancla (5)`;
    y **una frase repartida en dos líneas no casa con un patrón de una línea** —
    así se escapó `LIMITS.md` 51 la primera vez que probé esto.
    """
    return re.sub(r"\s+", " ", texto.replace("*", "").replace("`", ""))


def _valor(token: str) -> int | None:
    return int(token) if token.isdigit() else PALABRAS.get(token.lower())


def desacuerdos(documentos: list[tuple[str, str]], esperado: dict[str, int]) -> list[str]:
    """Las citas que no coinciden con el recuento real. Vacío = todo cuadra.

    **Exige recuentos sanos antes de mirar nada**: comparar contra cifras
    degeneradas produce una lista de acusaciones falsas contra documentos
    correctos, que es peor que no comprobar.
    """
    exigir_sano(esperado)
    fallos: list[str] = []
    for nombre, texto in documentos:
        plano = _plano(texto)
        for clave, patron in PATRONES:
            for m in re.finditer(patron, plano):
                frase = m.group(0)
                if HISTORICOS.get(frase, "\0") in plano:
                    continue
                if _es_nombre_propio(plano, m.start(), m.end()):
                    continue
                valor = _valor(m.group(1))
                if valor is not None and valor != esperado[clave]:
                    fallos.append(f"{nombre}: «{frase}» pero {clave} es {esperado[clave]}")
    return fallos


def _leidos() -> list[tuple[str, str]]:
    return [(str(d.relative_to(RAIZ)), d.read_text(encoding="utf-8")) for d in _documentos()]


def test_ningun_documento_publicado_cita_un_recuento_viejo() -> None:
    """**La comprobación.** Cuatro copias del mismo número, una sola verdad.

    Si esto se cae, el arreglo NO es tocar el número del documento hasta que pase:
    es mirar cuál de los dos es cierto. El de `recuentos()` sale de contar la
    colección y del `PLAN` de `matar.py`, así que normalmente el que está mal es el
    documento — pero conviene mirarlo, porque un `PLAN` mal escrito también movería
    este número.
    """
    fallos = desacuerdos(_leidos(), recuentos())
    assert fallos == [], (
        "recuentos desincronizados entre documentos:\n  "
        + "\n  ".join(fallos)
        + "\n\n  ESTA LISTA NO ESTÁ COMPLETA. El guardián sólo caza los fraseos"
        "\n  previstos: 7 de 18 formas naturales se le escapan (LIMITS 54,"
        "\n  `uv run python scripts/cobertura_patrones.py --detalle`). Corregir sólo"
        "\n  lo enumerado aquí es exactamente el fallo que este test existe para"
        "\n  evitar: busca el mismo recuento en los demás documentos a mano."
    )


def test_la_comprobacion_se_cae_con_una_cifra_desincronizada() -> None:
    """**Control negativo 1: cifras DESINCRONIZADAS.**

    Un detector que nunca ha demostrado que sabe decir «no» no ha demostrado nada.
    Es el mismo argumento que el control negativo del arnés de mutantes.
    """
    reales = recuentos()
    viejo = "Los 12 mutantes mueren, y el arnés cubre 107 de 145 tests."
    fallos = desacuerdos([("inventado.md", viejo)], reales)
    assert len(fallos) == 3, f"tendría que cazar mutantes, dentro y total: {fallos}"
    assert all("inventado.md" in f for f in fallos)

    bueno = (
        f"Los {reales['mutantes']} mutantes mueren, "
        f"y el arnés cubre {reales['dentro']} de {reales['total']} tests."
    )
    assert desacuerdos([("inventado.md", bueno)], reales) == [], (
        "sobre el texto CORRECTO no puede inventar un desacuerdo: eso es lo que "
        "pasaba cuando `0 (?:muertes )?de N tests` casaba con «cubre 0 de 5 tests»"
    )


def test_la_forma_de_estado_md_esta_vigilada() -> None:
    """Control negativo del punto ciego de `ESTADO.md`, que era el peor de todos.

    `ESTADO.md`:15 publica «N mutantes, todos mueren», y la coma y el «todos»
    rompían la adyacencia de todos los patrones de la familia. **Reproducido antes
    de taparlo**: subiendo el `PLAN` a 22 sin tocar ningún documento, el mensaje de
    error nombraba `RESULTS.md` x3, `LIMITS.md` y la skill — y **no `ESTADO.md`**.
    El humano corrige lo enumerado y `ESTADO.md` se queda en verde mintiendo, que
    es el fallo original reproducido por el mensaje de error del mecanismo.

    Y era el documento donde más duele: el hook `SessionStart` lo inyecta entero,
    así que la sesión siguiente lo lee antes que nada.
    """
    reales = recuentos()
    # La frase de prueba lleva SÓLO esta forma. La primera versión decía
    # «…, todos mueren, control negativo 0 de 1», y ese «0 de 1» casaba con otro
    # patrón: el test pasaba aunque se borrara el patrón que dice comprobar.
    # Comprobado quitándolo: la suite entera seguía verde.
    viejo = f"{reales['mutantes'] + 1} mutantes, todos mueren"
    assert desacuerdos([("estado_falso.md", viejo)], reales), (
        "la forma de ESTADO.md:15 tiene que estar vigilada"
    )
    bueno = f"{reales['mutantes']} mutantes, todos mueren"
    assert desacuerdos([("estado_bueno.md", bueno)], reales) == []


def test_el_nombre_propio_no_se_lee_como_recuento() -> None:
    """Control negativo del otro arreglo: «los dos mutantes» es un NOMBRE.

    Es el paso 2 de `/cerrar`, en seis sitios del repo. `CHANGELOG.md` dice hoy
    «Los dos mutantes van versionados y **mueren** en 20 y 7 tests»: **quitar tres
    palabras al reescribir esa línea pondría la puerta roja con una frase cierta**,
    y un candado que da rojos falsos deja de leerse.

    Las dos mitades: las variantes razonables del nombre no disparan, y un recuento
    de verdad con la misma forma sí.
    """
    reales = recuentos()
    for nombre in (
        "Los dos mutantes van versionados y mueren en 20 y 7 tests.",
        "Los dos mutantes mueren en 20 y 7 tests.",
        "Los dos mutantes están versionados en scripts/mutantes/.",
        "Los dos mutantes apuntan a _arbol.py.",
    ):
        assert desacuerdos([("changelog_falso.md", nombre)], reales) == [], (
            f"«{nombre}» es el nombre de la regla, no un recuento"
        )

    # Y la otra mitad, sin la cual la excepción taparía errores de verdad:
    assert desacuerdos([("x.md", "Los 2 mutantes del repo mueren.")], reales), (
        "un recuento con cifra SÍ tiene que compararse: la excepción es para el nombre"
    )


def test_la_comprobacion_se_niega_con_recuentos_degenerados() -> None:
    """**Control negativo 2: cifras DEGENERADAS.** El caso 3 de `/adversarial`.

    El primero cubría «los números no cuadran entre documentos». Éste cubre la
    otra mitad, que es la que rompió el mecanismo en `b7cc6c3`: **que los números
    contra los que se compara no sean una medición**.

    Una colección parcial da `dentro=0` y `total=5`. La primera versión los usaba
    tal cual y acusaba a los documentos correctos de estar desincronizados — un
    mensaje que hablaba de una desincronización que no existía. Ahora se distingue:
    *«no hay medición»* no es *«el documento está mal»*.
    """
    descuadrado = {"mutantes": 18, "total": 999, "dentro": 149, "fuera": 28}
    with pytest.raises(RecuentoDegenerado, match=r"total=999"):
        exigir_sano(descuadrado)

    sin_plan = {"mutantes": 0, "total": 177, "dentro": 149, "fuera": 28}
    with pytest.raises(RecuentoDegenerado, match=r"PLAN de matar\.py está vacío"):
        exigir_sano(sin_plan)

    parcial = {"mutantes": 18, "total": 5, "dentro": 0, "fuera": 5}
    with pytest.raises(RecuentoDegenerado, match="dentro=0"):
        exigir_sano(parcial)

    # Y la otra mitad, sin la cual esto pasaría por rechazarlo todo:
    assert exigir_sano(recuentos()) == recuentos()


def test_desacuerdos_se_niega_a_comparar_contra_recuentos_degenerados() -> None:
    """El segundo asesino de `recuentos_todo_vale`, por otra puerta.

    El de arriba comprueba `exigir_sano` en directo. Éste comprueba que
    **`desacuerdos` lo llama antes de mirar un solo documento**, que es lo que de
    verdad importa: una guarda que existe y que nadie invoca no guarda nada. Los
    dos hacen falta, y por eso van separados en vez de en el mismo test.
    """
    parcial = {"mutantes": 18, "total": 5, "dentro": 0, "fuera": 5}
    with pytest.raises(RecuentoDegenerado, match="dentro=0"):
        desacuerdos([("da_igual.md", "Los 18 mutantes mueren")], parcial)

    with pytest.raises(RecuentoDegenerado, match="la colección no llegó a correr"):
        desacuerdos([("da_igual.md", "")], {})


def test_una_corrida_parcial_recupera_los_recuentos_de_verdad() -> None:
    """**La precondición, resuelta en vez de declarada.**

    `pytest tests/unit/test_recuentos.py` colecta 5 tests: `dentro=0`, `total=5`.
    Esas cifras son ciertas sobre la corrida y **falsas sobre el repo**.

    Las dos salidas que se plantearon:

    | | Coste |
    |---|---|
    | **saltar** si la corrida es parcial | un guardián que se salta es un guardián |
    | | muerto en todo contexto que no sea CI |
    | **fallar** con «exige la suite entera» | pone rojo el desarrollo normal, y un |
    | | rojo que no es un bug enseña a ignorar el color |

    **Se eligió una tercera, que quita el dilema**: recuperar los recuentos de
    verdad con un `--collect-only` en un subproceso. **233 ms medidos**, y sólo se
    pagan cuando la selección INCLUYE estos tests — si `-k` los deselecciona, no se
    ejecutan y no hay coste. Así el guardián vive en **todas** las corridas.

    Este test comprueba que la recuperación funciona: sea cual sea la corrida,
    `recuentos()` devuelve cifras sanas y coherentes con el disco.
    """
    cuenta = recuentos()
    exigir_sano(cuenta)
    ficheros_en_disco = len(list((RAIZ / "tests" / "unit").glob("test_*.py")))
    assert cuenta["total"] > ficheros_en_disco, (
        f"total={cuenta['total']} con {ficheros_en_disco} ficheros de test: "
        "eso no es el repo entero, la recuperación no funcionó"
    )
    assert set(fuera_por_fichero()) <= {p.name for p in (RAIZ / "tests" / "unit").glob("test_*.py")}


def test_el_guardian_corre_donde_importa_y_no_solo_donde_se_le_llama() -> None:
    """La contrapartida de recuperar en vez de saltar: **comprobar dónde vive**.

    Aunque la recuperación hace que funcione en cualquier corrida, lo que de verdad
    impide que un número viejo llegue a `main` es que **la puerta lo ejecute**. Si
    alguien estrecha el `pytest` del Makefile a un subconjunto, o CI deja de llamar
    a `make fast`, el guardián sigue verde y deja de guardar.

    Esto se cae ese día, que es el único momento en que sirve de algo.
    """
    makefile = (RAIZ / "Makefile").read_text(encoding="utf-8")
    fast = makefile[makefile.index("\nfast:") :]
    fast = fast[: fast.index("\n\n")]
    assert "pytest tests/unit" in fast, f"la puerta ya no corre tests/unit entero:\n{fast}"
    assert "test_recuentos" not in fast, "la puerta selecciona ficheros sueltos, no el directorio"

    ci = (RAIZ / ".github" / "workflows" / "fast.yml").read_text(encoding="utf-8")
    assert "make fast" in ci, "el CI ya no llama a `make fast`: el guardián se quedó sin casa"


def test_la_comprobacion_mira_de_verdad_dentro_de_claude() -> None:
    """`.claude/` es donde estaba el tercer «12», y donde nadie mira.

    Sin esto, `_documentos()` podría dejar de recorrer `.claude/` —un `rglob` mal
    escrito, un directorio renombrado— y los tests de arriba seguirían verdes sobre
    menos ficheros de los que dicen cubrir.
    """
    revisados = [n for n, _ in _leidos()]
    del_claude = [n for n in revisados if n.startswith(".claude/")]
    assert del_claude, "no se está mirando .claude/, que es donde vive el guion de /cerrar"


def test_claude_aporta_al_menos_una_cita_de_recuento() -> None:
    """Segundo asesino de `recuentos_sin_claude`, y otra pregunta.

    El de arriba comprueba que `.claude/` **está en la lista**. Éste, que además
    **aporta algo**: un `.claude/` recorrido pero sin ninguna cita daría la misma
    luz verde que no recorrerlo, y entonces la afirmación «cubre `.claude/`» sería
    cierta y vacía a la vez.
    """
    del_claude = [n for n, _ in _leidos() if n.startswith(".claude/")]
    citas = sum(
        len(re.findall(patron, _plano((RAIZ / n).read_text(encoding="utf-8"))))
        for n in del_claude
        for _, patron in PATRONES
    )
    assert citas >= 1, "ningún fichero de .claude/ cita un recuento: la cobertura sería vacía"


def test_plano_colapsa_los_saltos_de_linea_y_no_solo_los_espacios() -> None:
    """Segundo asesino de `recuentos_plano_flojo`, y la razón por la que existe.

    Los documentos de este repo van a 80 columnas, así que **casi toda frase larga
    está partida**. Un `_plano` que colapsara sólo espacios y tabuladores dejaría
    de casar con `LIMITS.md` 51 —cuyo «Los / 21 mutantes apuntan» cruza una línea—
    y también rompería las excepciones de `HISTORICOS`, que se comparan contra el
    texto aplanado: medido, ese mutante convierte las dos citas históricas de L1 en
    dos falsos positivos.

    El otro asesino es la comprobación entera; éste mira la pieza sola, que es lo
    que permite saber **cuál** de las dos cosas se rompió.
    """
    assert _plano("Los\n21 mutantes") == "Los 21 mutantes"
    assert _plano("uno\n\n  dos\ttres") == "uno dos tres"
    assert _plano("**negrita** y `código`") == "negrita y código"


def test_cada_recuento_lo_caza_algun_patron_en_al_menos_dos_documentos() -> None:
    """**El candado contra el fallo silencioso del propio mecanismo.**

    El límite real de esto es que sólo caza los **fraseos que alguien previó**.
    Medido durante su construcción: desincronizando una cifra a propósito en cuatro
    documentos, la primera versión cazó 2, la segunda 3, y la cuarta hizo falta
    porque «no cubre la suite entera: 149 de 177» no se parecía a nada previsto.

    Eso no se puede cerrar del todo —el español no se enumera— pero sí se puede
    cerrar su **forma peligrosa**: que un patrón deje de casar en todas partes y el
    test siga verde sin comprobar nada. Aquí se exige que cada uno de los cuatro
    recuentos aparezca cazado en **dos documentos distintos como mínimo**.

    Lo que queda sin cubrir, en `LIMITS.md` 54.
    """
    cobertura: dict[str, set[str]] = {clave: set() for clave, _ in PATRONES}
    for nombre, texto in _leidos():
        plano = _plano(texto)
        for clave, patron in PATRONES:
            if re.search(patron, plano):
                cobertura[clave].add(nombre)
    flojos = {c: sorted(d) for c, d in cobertura.items() if len(d) < 2}
    assert flojos == {}, (
        f"estos recuentos se citan en menos de dos documentos, así que la "
        f"comprobación no está comparando nada: {flojos}"
    )


def test_el_desglose_de_los_que_quedan_fuera_es_el_que_publica_limits() -> None:
    """La lista de ficheros, no sólo el total. Es lo que estaba mal de verdad.

    `LIMITS.md` 51 y `ESTADO.md` no sólo decían «38»: **nombraban a `teds_limites`
    y `teds_batch` como módulos sin mutante**, y los dos ya tenían uno. Un total
    correcto con una lista falsa es peor que un total falso, porque manda a alguien
    a escribir trabajo que ya existe — que es lo que la deuda 7 de `ESTADO.md`
    mandaba hacer.
    """
    limits = _plano((RAIZ / "LIMITS.md").read_text(encoding="utf-8"))
    trozo = limits[limits.index("51. La suite no está medida por mutación") :][:700]
    for fichero, n in fuera_por_fichero().items():
        corto = fichero.removeprefix("test_").removesuffix(".py")
        assert f"{corto} ({n})" in trozo, (
            f"el límite 51 no nombra a `{corto}` con sus {n} tests: {trozo[:300]}"
        )
