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
sólo comprueba que se copiaron bien.

**Descartado: que `matar.py` escriba los recuentos a un JSON.** Ese JSON sólo
está al día si alguien se acuerda de correr `matar.py`. Sería una **quinta copia
capaz de quedarse vieja**, o sea el mismo fallo una capa más abajo, y encima con
más apariencia de autoridad.

**Elegido: calcularlos donde no pueden estar viejos.** `tests/unit/conftest.py`
los computa en `pytest_collection_modifyitems`, o sea **en cada `make fast`**: no
hay fichero almacenado, así que no hay nada que sincronizar. Y son exactos, con la
parametrización ya resuelta — un `grep "def test_"` daría otro número. El
`PLAN` de `matar.py` se lee directamente, que es **la definición** de «dentro del
arnés», en vez de copiarla aquí.

Coste: un fichero de test y un hook de colección. No añade tiempo medible a la
puerta porque no ejecuta nada, sólo cuenta lo ya colectado.
"""

from __future__ import annotations

import re
from pathlib import Path

import conftest
import pytest
from conftest import FUERA_POR_FICHERO, RECUENTOS

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
    "veintitrés": 23,
}
"""Este repo escribe los números en prosa tanto como en cifra —«los dieciocho
mutantes del repo mueren»—, así que un patrón que sólo mire dígitos deja fuera
justo las frases de titular."""

_N = r"(\d+|[a-záéíóúñ]+)"

# Cada patrón exige ADYACENCIA con una palabra que sólo aparece en una afirmación
# de RECUENTO. Sin eso, «los dos mutantes» —que en este repo es el NOMBRE de una
# regla de `/cerrar`, no una cantidad— se leería como el recuento y el test
# pediría que hubiera dos mutantes en el repo.
PATRONES: tuple[tuple[str, str], ...] = (
    ("mutantes", rf"{_N} mutantes(?: del repo)? mueren"),
    ("mutantes", rf"[Ss]on {_N} mutantes"),
    ("mutantes", rf"{_N} mutantes existentes"),
    ("mutantes", rf"{_N} mutantes (?:están versionados|se versionan)"),
    ("mutantes", rf"[Ll]os {_N} mutantes apuntan"),
    # «cubre N de M» sin exigir qué palabra va antes: el control negativo destapó
    # que `arn[eé]s cubr` no casaba con «El arnés DE MUTANTES cubre 107 de 176», y
    # que exigir «tests» detrás dejaba pasar «149 de 176.» con punto. Un patrón
    # que sólo caza la redacción que ya existe no protege de la siguiente.
    ("dentro", rf"cubr[eí]a?n? {_N} de \d+"),
    ("dentro", rf"suite entera: {_N} de \d+"),
    ("total", rf"suite entera: \d+ de {_N}"),
    ("dentro", rf"0 (?:muertes )?de {_N} tests"),
    ("dentro", rf"control negativo 0 de {_N}"),
    ("fuera", rf"{_N} tests restantes"),
    ("fuera", rf"[Ll]os {_N} restantes"),
    ("fuera", rf"esos {_N} tests"),
    ("fuera", rf"{_N} quedaban fuera"),
    ("total", rf"cubr[eí]a?n? \d+ de {_N}"),
    ("total", rf"suite ya en {_N} tests"),
)

HISTORICOS: dict[str, str] = {
    # El contexto va SIN comillas invertidas ni asteriscos, porque se compara
    # contra el texto ya aplanado por `_plano`. Escribirlo con el markdown puesto
    # hacía que la excepción no casara nunca y los dos históricos se contaran como
    # error — que es un falso positivo, pero del lado seguro.
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
es lo que se quiere. Eximir el fichero entero, en cambio, escondería también los
errores nuevos, y `RESULTS.md` es justo donde más números viven."""


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
    """Sin asteriscos y con los espacios colapsados.

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
    """Las citas que no coinciden con el recuento real. Vacío = todo cuadra."""
    fallos: list[str] = []
    for nombre, texto in documentos:
        plano = _plano(texto)
        for clave, patron in PATRONES:
            for m in re.finditer(patron, plano):
                frase = m.group(0)
                if HISTORICOS.get(frase, "\0") in plano:
                    continue
                valor = _valor(m.group(1))
                if valor is not None and valor != esperado[clave]:
                    fallos.append(f"{nombre}: «{frase}» pero {clave} es {esperado[clave]}")
    return fallos


def _leidos() -> list[tuple[str, str]]:
    return [(str(d.relative_to(RAIZ)), d.read_text(encoding="utf-8")) for d in _documentos()]


def test_ningun_documento_publicado_cita_un_recuento_viejo() -> None:
    """**La comprobación.** Cuatro copias del mismo número, una sola verdad.

    **Sólo vale sobre `tests/unit` entero**, y por eso se salta si no lo es: con
    `pytest tests/unit/test_recuentos.py` el recuento colectado son 4 tests, y
    compararlo contra los documentos declararía que todos mienten. Saltarlo con
    su motivo es lo honesto; dejarlo pasar en verde sobre una colección parcial
    sería un test que dice más de lo que ha mirado.

    Si esto se cae, el arreglo NO es tocar el número del documento hasta que pase:
    es mirar cuál de los dos es cierto. El de `RECUENTOS` sale de contar lo que
    pytest acaba de colectar y del `PLAN` de `matar.py`, así que normalmente el
    que está mal es el documento — pero conviene mirarlo, porque un `PLAN` mal
    escrito también movería este número.
    """
    if not conftest.COMPLETA:
        pytest.skip("colección parcial: este recuento sólo vale sobre tests/unit entero")
    fallos = desacuerdos(_leidos(), RECUENTOS)
    assert fallos == [], "recuentos desincronizados entre documentos:\n  " + "\n  ".join(fallos)


def test_la_comprobacion_se_cae_con_una_cifra_desincronizada() -> None:
    """**El control negativo.** Sin esto, un patrón roto da la misma luz verde.

    Es el mismo argumento que el control negativo del arnés de mutantes: un
    detector que nunca ha demostrado que sabe decir «no» no ha demostrado nada.
    """
    viejo = "Los 12 mutantes mueren, y el arnés cubre 107 de 145 tests."
    fallos = desacuerdos([("inventado.md", viejo)], RECUENTOS)
    assert len(fallos) == 3, f"tendría que cazar mutantes, dentro y total: {fallos}"
    assert all("inventado.md" in f for f in fallos)

    # Y la otra mitad: sobre el texto correcto NO inventa un desacuerdo.
    bueno = (
        f"Los {RECUENTOS['mutantes']} mutantes mueren, "
        f"y el arnés cubre {RECUENTOS['dentro']} de {RECUENTOS['total']} tests."
    )
    assert desacuerdos([("inventado.md", bueno)], RECUENTOS) == []


def test_la_comprobacion_mira_de_verdad_dentro_de_claude() -> None:
    """`.claude/` es donde estaba el tercer «12», y donde nadie mira.

    Sin esto, `_documentos()` podría dejar de recorrer `.claude/` —un `rglob` mal
    escrito, un directorio renombrado— y los dos tests de arriba seguirían verdes
    sobre menos ficheros de los que dicen cubrir.
    """
    if not conftest.COMPLETA:
        pytest.skip("colección parcial: este recuento sólo vale sobre tests/unit entero")
    revisados = [n for n, _ in _leidos()]
    del_claude = [n for n in revisados if n.startswith(".claude/")]
    assert del_claude, "no se está mirando .claude/, que es donde vive el guion de /cerrar"

    citas = sum(
        len(re.findall(patron, _plano(Path(RAIZ / n).read_text(encoding="utf-8"))))
        for n in del_claude
        for _, patron in PATRONES
    )
    assert citas >= 1, "ningún fichero de .claude/ cita un recuento: la cobertura sería vacía"


def test_cada_recuento_lo_caza_algun_patron_en_al_menos_dos_documentos() -> None:
    """**El candado contra el fallo silencioso del propio mecanismo.**

    El límite real de esto es que sólo caza los **fraseos que alguien previó**.
    Medido durante su construcción: desincronizando una cifra a propósito en cuatro
    documentos, la primera versión cazó 2, la segunda 3, y la cuarta hizo falta
    porque «no cubre la suite entera: 149 de 176» no se parecía a ningún patrón.

    Eso no se puede cerrar del todo —el español no se enumera— pero sí se puede
    cerrar su **forma peligrosa**: que un patrón deje de casar en todas partes y
    el test siga verde sin comprobar nada. Aquí se exige que cada uno de los
    cuatro recuentos aparezca cazado en **dos documentos distintos como mínimo**,
    que es la situación real —los cuatro viven repartidos— y la que hace útil la
    comparación. Si alguien reescribe una sección y el patrón deja de casar, esto
    se cae en vez de pasar en verde sobre cero citas.

    Lo que queda sin cubrir, en `LIMITS.md` 54: una redacción nueva en un
    documento nuevo, si ningún patrón la reconoce, no se comprueba. El
    procedimiento que lo detecta es el control negativo a mano, y es un paso de
    `/cerrar`.
    """
    if not conftest.COMPLETA:
        pytest.skip("colección parcial: este recuento sólo vale sobre tests/unit entero")
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

    `LIMITS.md` 51 y `ESTADO.md` no sólo decían «38»: **nombraban a
    `teds_limites` y `teds_batch` como módulos sin mutante**, y los dos ya tenían
    uno. Un total correcto con una lista falsa es peor que un total falso, porque
    manda a alguien a escribir trabajo que ya existe — que es exactamente lo que
    la deuda 7 de `ESTADO.md` mandaba hacer.
    """
    if not conftest.COMPLETA:
        pytest.skip("colección parcial: este recuento sólo vale sobre tests/unit entero")
    limits = _plano((RAIZ / "LIMITS.md").read_text(encoding="utf-8"))
    trozo = limits[limits.index("51. La suite no está medida por mutación") :][:700]
    for fichero, n in FUERA_POR_FICHERO.items():
        corto = fichero.removeprefix("test_").removesuffix(".py")
        assert f"{corto} ({n})" in trozo, (
            f"el límite 51 no nombra a `{corto}` con sus {n} tests: {trozo[:300]}"
        )
    dentro_del_plan = {"teds_limites", "teds_batch", "cellmatch", "canonical"}
    for nombre in dentro_del_plan:
        assert f"`{nombre}`" not in trozo or nombre in {
            f.removeprefix("test_").removesuffix(".py") for f in FUERA_POR_FICHERO
        }, f"el límite 51 nombra `{nombre}` como sin mutante, y sí lo tiene"
