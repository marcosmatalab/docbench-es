"""Los recuentos volátiles del repo, calculados en cada colección.

**El problema que resuelve.** El cierre de L2 pasó los mutantes de 12 a 18 y los
tests fuera del arnés de 38 a 23. La corrección se escribió en `RESULTS.md` con su
nota al lado… y **se quedó vieja en `LIMITS.md` 51, en `ESTADO.md` y en
`.claude/skills/cerrar/SKILL.md`**, los tres dentro del mismo commit. `unica()`
impide editar a ciegas UN documento; nada impedía corregir uno y olvidar tres.

**Por qué se calcula aquí y no en un fichero generado.** Un JSON que escribe
`matar.py` sólo está al día si alguien se acuerda de correr `matar.py`, y entonces
el fichero es una cuarta copia que puede quedarse vieja — el mismo fallo una capa
más abajo. `pytest_collection_modifyitems` corre **en cada `pytest tests/unit`**,
o sea en cada `make fast`: los números no pueden estar viejos porque no están
almacenados en ningún sitio. Y el recuento es **exacto**, con la parametrización
ya resuelta, que es lo que un `grep "def test_"` no puede dar.

**Y aquí vive también la fixture `registrar`.** No tiene nada que ver con los
recuentos: está aquí porque la usan DOS ficheros de test —el del registro y el de
la conformidad— y una fixture compartida vive en `conftest.py` o se duplica.

**La precondición, que la primera versión no declaró y por eso se rompió.** Estos
recuentos salen de lo COLECTADO. `pytest tests/unit/test_recuentos.py` colecta 5
tests y da `dentro=0`, `total=5`: cifras ciertas sobre esa corrida y **falsas
sobre el repo**. La primera versión las usaba igual y se ponía roja hablando de
una desincronización que no existía. Ahora eso lo resuelve `recuentos()`.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from docbench_es.entity.registry import GRUPO

RAIZ = Path(__file__).resolve().parents[2]
UNIT = RAIZ / "tests" / "unit"

COLECTADOS: dict[str, int] = {}
"""Lo que salió de la colección de ESTA corrida. Puede ser parcial: ver `COMPLETA`."""

FUERA_POR_FICHERO: dict[str, int] = {}
"""Fichero de test -> nº de tests, sólo para los que NINGÚN mutante apunta."""

COMPLETA = False
"""¿La colección cubrió `tests/unit` ENTERO?

Con `pytest tests/unit/test_x.py`, o con `-k`, los recuentos son los de esa
selección y no los del repo. Quien compare contra documentos publicados tiene que
saberlo, o acaba declarando que todos los documentos mienten.
"""

_RECUPERADOS: dict[str, int] = {}


class RecuentoDegenerado(RuntimeError):
    """Los recuentos no cumplen sus invariantes estructurales.

    No es lo mismo que «un documento cita un número viejo». Esto dice que **la
    medición no se hizo**, y las dos cosas se leen igual en un fallo si no se
    distinguen — que es exactamente el error que `matar.py` ya documenta cuando
    pytest no recoge ni un test.
    """


def _plan() -> tuple[set[str], int]:
    """Los ficheros de test a los que apunta algún mutante, y cuántos mutantes hay.

    Se lee el `PLAN` de `matar.py` directamente en vez de copiarlo: es la
    definición de «dentro del arnés», y copiarla aquí crearía justo la segunda
    fuente de verdad que este fichero existe para evitar.
    """
    ruta = RAIZ / "scripts" / "mutantes" / "matar.py"
    spec = importlib.util.spec_from_file_location("_matar", ruta)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    plan: list[tuple[str, str]] = modulo.PLAN
    return {Path(f).name for _, suite in plan for f in suite.split()}, len(plan)


CONTROLES_NEGATIVOS: dict[str, str] = {
    "test_entity_conformance.py": "test_el_adaptador_roto_se_cae_por_los_cinco_aros_que_rompe",
    "test_entity_registry.py": "test_el_rechazo_por_version_ocurre_al_cargar",
    "test_barreras.py": "test_el_barrido_dice_que_no_ante_una_referencia_rota",
    "test_barreras_documentos.py": "test_las_derivadas_publicadas_salen_de_su_fuente",
    "test_limite_lineas.py": "test_ningun_fichero_de_codigo_pasa_de_300_lineas",
    "test_reglas_parseables.py": "test_una_regla_rota_se_detecta_nombrandola",
    "test_extractor_contrato.py": "test_al_que_le_falta_un_solo_miembro_no_cumple",
    "test_conjunto_conformidad.py": "test_un_conjunto_sin_combinadas_lo_dice_en_vez_de_callarselo",
    "test_extractor_conformidad.py": "test_el_bueno_pasa",
    "test_formatos_spans.py": "test_from_dataframe_no_expresa_spans_y_la_lista_lo_dice",
    "test_estimador_computo.py": "test_una_pendiente_positiva_delata_un_preregistro_falso",
    "test_boe_api.py": "test_bajar_una_url_que_ningun_sumario_ha_dado_es_violacion_de_politica",
    "test_boe.py": "test_fetch_de_una_ref_inventada_es_violacion_de_politica",
    "test_boe_xml.py": "test_solo_cuentan_los_spans_mayores_que_uno",
    "test_pairing.py": "test_un_par_que_no_dice_lo_mismo_se_descarta_con_su_causa",
    "test_policy.py": "test_la_campana_no_arranca_con_un_extractor_por_api_y_la_fuente_cerrada",
    "test_harvest.py": "test_la_cosecha_para_si_mas_del_cinco_por_ciento_agota_reintentos",
    "test_manifest.py": "test_requisito_2_sin_atribucion_no_hay_manifiesto",
    "test_verificar_corpus.py": "test_un_descarte_que_desaparece_del_denominador_pone_rojo",
    "test_sellar_xml.py": "test_un_xml_que_falta_no_se_salta_en_silencio",
    "test_types_invariantes.py": "test_un_fallo_sin_causa_no_se_puede_construir",
    "test_capas_permitidas.py": "test_una_direccion_prohibida_sigue_estando_prohibida",
    "test_comparar_verdad.py": "test_una_celda_movida_de_columna_se_detecta",
    "test_tope_area.py": "test_una_tabla_que_se_pasa_del_tope_sale_fatal_nombrando_el_area",
    "test_ancla.py": "test_un_ancla_que_no_existe_aborta_en_vez_de_borrar_hasta_el_final",
    "test_types.py": "test_todo_el_modelo_de_datos_es_inmutable",
    "test_sin_consumidor.py": "test_from_html_si_tiene_consumidor_y_por_eso_no_esta_en_la_lista",
    "test_congelados_l4.py": "test_un_fixture_manipulado_no_cuadra_con_su_huella",
    "test_guardianes_l4.py": "test_re_congelar_aborta_sin_correccion_registrada",
    "test_guardianes_por_glob.py": "test_si_el_glob_se_rompe_el_recuento_lo_delata",
    "test_documentos_que_sostienen.py": "test_un_documento_que_acumula_no_lleva_tope",
    # L5 · el primer extractor real, su registro, su arnés y el almacén que los alimenta
    "test_extract_registry.py": "test_el_control_negativo_de_lo_anterior_detecta_un_import_arriba",
    "test_cli.py": "test_hay_al_menos_un_subcomando_y_se_dicen_cuales",
    "test_pdfplumber.py": "test_expresses_spans_no_esta_tecleado_sino_derivado",
    "test_extractor_arnes.py": "test_el_control_negativo_del_desenvolver_no_inventa_causas",
    "test_corpus_store.py": "test_carga_un_documento_entero_con_lo_que_dice_el_manifiesto",
    "test_conjunto.py": "test_el_conjunto_bueno_se_monta_y_dice_su_denominador",
    "test_corredor.py": "test_reanudar_sobre_otro_arbol_se_rechaza",
    "test_diario.py": "test_una_causa_que_no_es_del_enum_cerrado_no_se_reconstruye",
    "test_aro_del_techo.py": "test_una_medida_caliente_no_vale_por_buena_que_sea",
    "test_pymupdf4llm.py": "test_un_pdf_corrupto_no_lanza_y_se_cuenta_con_su_causa",
    "test_canonical_texto_de_celda.py": "test_lo_que_no_se_toca_no_se_toca",
    "test_camelot.py": "test_read_pdf_recibe_pages_y_flavor_explicitos",
    "test_censo_capa_texto.py": "test_encuentra_una_pagina_sin_capa_de_texto",
    "test_docling.py": "test_no_hay_ninguna_llamada_a_extract_en_este_fichero",
    "test_metricas_regimen.py": "test_un_censo_con_intervalo_tampoco",
    # El control de `procedencia` tiene que ser un arbol SUCIO: la afirmacion util del
    # modulo es «no difieren», y un `difieren()` vacio la cumpliria siempre. Con el arbol
    # sucio los tres campos tienen que moverse, y eso es lo que un vacio no puede fingir.
    "test_procedencia.py": "test_un_arbol_sucio_si_mueve_la_huella",
    "test_nivel1.py": "test_el_documento_que_no_cuadra_no_cuenta_como_cero",
    "test_tabla_nivel1.py": "test_un_no_aplicable_se_imprime_n_a_y_nunca_cero",
}
"""Fichero de test -> el test suyo que **ejerce el sujeto contra algo
deliberadamente malo y afirma que lo rechaza**.

**Por qué existe esta tabla.** «El arnés cubre N de M» mide *el arnés*, no la
protección: hay ficheros fuera del arnés que llevan su control negativo **dentro**,
y contarlos como desprotegidos exagera el hueco tanto como ignorarlo lo esconde.
Publicar sólo la cobertura del arnés era el mismo error que publicar el total sin
la velocidad, un nivel más arriba.

**El criterio es comprobable, y sólo hasta cierto punto.** Lo que se verifica por
ejecución es que **el test nombrado existe y se colecta**
(`test_cada_control_negativo_declarado_existe_de_verdad`). Lo que NINGUNA
comprobación puede decidir es si ese test es *fuerte*: eso lo demuestra un mutante,
y por eso la cobertura del arnés se sigue publicando al lado como submedida. Está
en `LIMITS.md` 60.

**`test_errors.py` no está aquí a propósito.** Sus tres tests afirman la forma de
la jerarquía y del enum —estructura—, no que algo rechace una entrada mala. Es el
único fichero de la suite sin nada que demuestre que se pondría rojo, y la lista
lo dice en vez de estirarse para taparlo."""


def _reglas() -> int:
    """Cuántas reglas con `paths:` hay en `.claude/rules/`.

    **No es un recuento de tests, y por eso está aquí.** `CLAUDE.md` dice cuántas
    hay y las enumera, y ese número se quedó viejo en el mismo commit que añadió
    la cuarta: entró `entidad-corpus.md` y la frase siguió diciendo «3». Es el
    peor sitio donde puede vivir una cifra falsa, porque `CLAUDE.md` es lo primero
    que lee **toda** sesión — antes que `RESULTS.md` y antes que nada.

    Se calcula igual que los demás: contando, en cada colección, para que no haya
    ninguna copia que pueda quedarse vieja.
    """
    return len(list((RAIZ / ".claude" / "rules").glob("*.md")))


def _cuadrar(por_fichero: dict[str, int]) -> tuple[dict[str, int], dict[str, int]]:
    dentro_de, n_mutantes = _plan()
    fuera = {f: n for f, n in por_fichero.items() if f not in dentro_de}
    return (
        {
            "mutantes": n_mutantes,
            "total": sum(por_fichero.values()),
            "dentro": sum(n for f, n in por_fichero.items() if f in dentro_de),
            "fuera": sum(fuera.values()),
            "reglas": _reglas(),
            # La contabilidad reconciliada: protegido por el arnés O por un control
            # negativo declarado en su propio fichero. Ver `CONTROLES_NEGATIVOS`.
            "protegidos": sum(
                n for f, n in por_fichero.items() if f in dentro_de or f in CONTROLES_NEGATIVOS
            ),
            "sin_nada": sum(
                n
                for f, n in por_fichero.items()
                if f not in dentro_de and f not in CONTROLES_NEGATIVOS
            ),
        },
        fuera,
    )


def exigir_sano(cuenta: dict[str, int]) -> dict[str, int]:
    """Rechaza los recuentos DEGENERADOS antes de que nadie compare contra ellos.

    Son invariantes estructurales, no umbrales inventados:

    - `total == dentro + fuera`, porque cada test cae en un lado o en el otro;
    - `mutantes >= 1`, o el `PLAN` está vacío;
    - `dentro >= 1`, o no se colectó ni un fichero del arnés;
    - `fuera >= 1`, porque este mismo fichero está fuera del arnés;
    - `reglas >= 1`, o el directorio de reglas no se leyó;
    - `protegidos + sin_nada == total`, porque cada test cae en un lado o en otro
      **de la segunda contabilidad también**, y las dos tienen que cuadrar contra
      el mismo total o no son dos vistas de lo mismo.

    Sin esto, una colección parcial produce `dentro=0` y la comparación acusa a
    todos los documentos de mentir. Un recuento degenerado **no es un desacuerdo**:
    es que no hay medición, y decir «no hay medición» es distinto de decir «el
    documento está mal».
    """
    if not cuenta:
        raise RecuentoDegenerado("los recuentos están vacíos: la colección no llegó a correr")
    esperado = cuenta["dentro"] + cuenta["fuera"]
    problemas = [
        f"total={cuenta['total']} pero dentro+fuera={esperado}"
        if cuenta["total"] != esperado
        else "",
        "mutantes=0: el PLAN de matar.py está vacío" if cuenta["mutantes"] < 1 else "",
        "dentro=0: no se colectó ni un fichero del arnés" if cuenta["dentro"] < 1 else "",
        "fuera=0: ni siquiera este fichero se contó" if cuenta["fuera"] < 1 else "",
        "reglas=0: no se vio ni una regla en .claude/rules/" if cuenta.get("reglas", 0) < 1 else "",
        f"protegidos+sin_nada={cuenta.get('protegidos', 0) + cuenta.get('sin_nada', -1)} "
        f"pero total={cuenta['total']}"
        if cuenta["total"] != cuenta.get("protegidos", 0) + cuenta.get("sin_nada", -1)
        else "",
    ]
    rotos = [p for p in problemas if p]
    if rotos:
        raise RecuentoDegenerado(
            f"recuentos degenerados, no hay medición: {'; '.join(rotos)} · {cuenta}"
        )
    return cuenta


def _recuperar() -> dict[str, int]:
    """Colecta `tests/unit` ENTERO en un subproceso. **233 ms medidos.**

    Es lo que permite que la comprobación viva también en las corridas parciales
    en vez de saltarse, que es lo que hacía la primera versión. Se paga sólo
    cuando la selección **incluye** estos tests: si `-k` los deselecciona, no
    llegan a ejecutarse y no hay coste.
    """
    if _RECUPERADOS:
        return _RECUPERADOS
    salida = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=False,
    )
    por_fichero = {
        m.group(1): int(m.group(2))
        for linea in salida.stdout.splitlines()
        if (m := re.match(r"^tests/unit/(test_\w+\.py): (\d+)$", linea))
    }
    if not por_fichero:
        raise RecuentoDegenerado(
            "el subproceso de colección no devolvió ni un fichero; sin eso no hay "
            f"recuento que comparar.\nrc={salida.returncode}\n{salida.stdout[-600:]}"
        )
    cuenta, fuera = _cuadrar(por_fichero)
    FUERA_POR_FICHERO.clear()
    FUERA_POR_FICHERO.update(fuera)
    _RECUPERADOS.update(exigir_sano(cuenta))
    return _RECUPERADOS


def recuentos() -> dict[str, int]:
    """Los recuentos VERDADEROS del repo, venga la corrida como venga.

    Completa: los de la colección, gratis. Parcial: se recuperan con un
    subproceso. En ningún caso se devuelven cifras de una selección parcial, que
    es lo que rompió la primera versión.
    """
    if COMPLETA:
        return exigir_sano(COLECTADOS)
    return _recuperar()


def fuera_por_fichero() -> dict[str, int]:
    """El desglose de los que quedan fuera del arnés, **ya recuperado si hacía falta**.

    Existe para que nadie lea `FUERA_POR_FICHERO` directamente: en una corrida
    parcial ese diccionario trae el desglose de la selección, no el del repo, y
    sólo se rellena de verdad al llamar a `recuentos()`.
    """
    recuentos()
    return dict(FUERA_POR_FICHERO)


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    del session, config
    por_fichero: dict[str, int] = {}
    for item in items:
        nombre = Path(str(item.path)).name
        por_fichero[nombre] = por_fichero.get(nombre, 0) + 1

    global COMPLETA
    en_disco = {p.name for p in UNIT.glob("test_*.py")}
    COMPLETA = en_disco == set(por_fichero)

    cuenta, fuera = _cuadrar(por_fichero)
    FUERA_POR_FICHERO.clear()
    FUERA_POR_FICHERO.update(fuera)
    COLECTADOS.clear()
    COLECTADOS.update(cuenta)


Registrar = Callable[[str, str], None]


@pytest.fixture
def registrar(tmp_path: Path) -> Iterator[Registrar]:
    """Instala adaptadores falsos en el grupo real, y los desinstala al salir.

    El directorio se quita de `sys.path` en el `finally` **siempre**: un test que
    dejara su distribución falsa puesta contaminaría a los demás, y el fallo
    aparecería en otro fichero.
    """
    raiz = tmp_path / "site-packages"
    raiz.mkdir()
    sys.path.insert(0, str(raiz))

    def _registrar(nombre: str, destino: str) -> None:
        info = raiz / f"{nombre.replace('-', '_')}-0.0.dist-info"
        info.mkdir()
        (info / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: {nombre}\nVersion: 0.0\n", encoding="utf-8"
        )
        (info / "entry_points.txt").write_text(
            f"[{GRUPO}]\n{nombre} = {destino}\n", encoding="utf-8"
        )
        # Sin esto, `importlib.metadata` puede servir el listado que cacheó antes
        # de que existiera el directorio.
        importlib.invalidate_caches()

    try:
        yield _registrar
    finally:
        sys.path.remove(str(raiz))
        importlib.invalidate_caches()
