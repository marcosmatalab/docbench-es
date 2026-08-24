"""Que el criterio de aceptación de L3 **tiene comando, y que el comando dice que no**.

§16 pide *«1.000 documentos emparejados PDF/XML, con manifiesto y tasa de
descarte»*, y hasta hoy ese criterio **no tenía comando**: se podía cosechar,
mirar el JSON y declararlo cumplido a ojo. La regla de oro 2 dice que todo número
publicado lleva su comando de reproducción, y el criterio de aceptación es el
número más importante del hito.

`scripts/verificar_corpus.py` es una barrera: su único trabajo es ponerse roja
cuando el corpus no cumple. Su silencio se leería como «el corpus cumple el
criterio», que es la frase con la que se cierra el hito. Así que va con las dos
direcciones, aro por aro.
"""

from __future__ import annotations

import sys
from copy import deepcopy
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from verificar_corpus import verificar  # noqa: E402

from docbench_es.corpus.manifest import Procedencia, crear  # noqa: E402
from docbench_es.entity.base import cargar_perfil  # noqa: E402

PERFIL = cargar_perfil(RAIZ / "entities" / "boe.yaml")
SHA = "a" * 64


def _manifiesto(n: int = 2) -> dict[str, object]:
    docs = [
        Procedencia(
            external_id=f"BOE-A-2026-{i:05d}",
            fecha_sumario=date(2026, 8, 3),
            seccion="1",
            url_pdf=f"https://www.boe.es/boe/dias/2026/08/03/pdfs/BOE-A-2026-{i:05d}.pdf",
            url_xml=f"https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-{i:05d}",
            sha256=f"{i:064d}",
            n_pages=2,
            strata=frozenset({"tabla-simple"}),
            fetched_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
            cosechado_en=date(2026, 8, 24),
        )
        for i in range(n)
    ]
    return crear(
        entidad="boe",
        plan_hash="f" * 64,
        desde=date(2026, 8, 3),
        hasta=date(2026, 8, 3),
        documentos=docs,
        licencia=PERFIL.licencia,
        umbral_coherencia=PERFIL.umbral_coherencia,
        intentados=n + 1,
        por_causa={"incoherente": 1},
        dias_sin_boletin=[date(2026, 8, 4)],
        espaciado_mediano_s=1.0,
        espaciado_minimo_s=1.0,
        n_espaciados=3,
    ).a_json()


def test_un_manifiesto_bien_formado_cumple() -> None:
    """La dirección que evita que la barrera se consiga diciendo «no» a todo.

    Sin este test, un verificador que fallara siempre pasaría todos los demás y
    dejaría el hito sin poder cerrarse nunca.
    """
    assert verificar(_manifiesto()) == []


def test_un_descarte_que_desaparece_del_denominador_pone_rojo() -> None:
    """**El fallo más grave que puede tener un corpus publicado.**

    Si `aceptados + descartes` no da `intentados`, hay documentos que salieron de
    la cosecha sin aparecer en ningún lado, y la tasa de descarte que se publica
    está calculada sobre una población que nadie declaró.
    """
    roto = _manifiesto()
    roto["emparejado"]["intentados"] = 99  # type: ignore[index]

    fallos = verificar(roto)

    assert any("no cuadra" in f for f in fallos)


def test_una_tasa_sin_su_ventana_pone_rojo() -> None:
    """ADR-0030: una tasa sin ventana es **una propiedad del calendario disfrazada
    de propiedad del corpus**, y está medido que entre ventanas hay un factor 2,75."""
    roto = _manifiesto()
    roto["ventana"] = {"desde": "", "hasta": ""}

    assert any("VENTANA" in f for f in verificar(roto))


def test_sin_atribucion_literal_pone_rojo() -> None:
    """ADR-0033, requisito 2. Publicar el corpus así incumpliría su licencia."""
    roto = _manifiesto()
    roto["atribucion"] = "  "

    assert any("atribucion" in f for f in verificar(roto))


def test_un_documento_sin_seccion_o_sin_fecha_pone_rojo() -> None:
    """Requisito 1, y la razón: **no se reconstruyen sin volver al origen**, y
    volver seis meses después no devuelve lo mismo."""
    roto = _manifiesto()
    roto["documentos"][0]["seccion"] = ""  # type: ignore[index]
    roto["documentos"][1]["fecha_sumario"] = ""  # type: ignore[index]

    fallos = verificar(roto)

    assert sum("sin `seccion`" in f or "sin `fecha_sumario`" in f for f in fallos) == 2


def test_dos_documentos_con_el_mismo_sha_ponen_rojo() -> None:
    """Dos entradas con el mismo hash **son el mismo fichero**.

    No es una curiosidad: significa que el emparejado ha asignado el mismo PDF a
    dos identificadores, y entonces la verdad de uno de los dos juzga al documento
    equivocado. Un corpus así envenena en silencio.
    """
    roto = _manifiesto()
    roto["documentos"][1]["sha256"] = roto["documentos"][0]["sha256"]  # type: ignore[index]

    assert any("mismo `sha256`" in f for f in verificar(roto))


def test_una_url_construida_a_mano_pone_rojo() -> None:
    """ADR-0031, condición 1: toda URL viene de un campo del sumario.

    Una URL de otro dominio en el manifiesto significa que alguien la fabricó, y
    con ella se cae el argumento entero con el que este proyecto justifica bajar
    el XML del BOE.
    """
    roto = _manifiesto()
    roto["documentos"][0]["url_pdf"] = "https://otro-sitio.example/BOE-A-2026-00000.pdf"  # type: ignore[index]

    assert any("fuera de https://www.boe.es" in f for f in verificar(roto))


def test_el_manifiesto_se_compara_contra_el_plan_congelado() -> None:
    """**La comprobación que convierte el plan en algo más que un documento.**

    Si la ventana cosechada no es la del plan, lo que hay en disco no es lo que se
    planeó — y un plan que se ajusta después de ver los resultados no es un plan
    (§16 congela el de muestreo antes de medir, por lo mismo).
    """
    plan = {
        "ventana": {"desde": "2026-02-16", "hasta": "2026-03-21"},
        "objetivo_emparejados": 1045,
        "filtro_secciones": ["1", "3"],
        "ritmo_minimo_s": 1.0,
    }

    fallos = verificar(_manifiesto(), plan)

    assert any("no es la del plan" in f for f in fallos)
    assert any("por debajo del objetivo" in f for f in fallos)


def test_cosechar_mas_rapido_de_lo_prometido_pone_rojo() -> None:
    """El ritmo declarado es un compromiso con un origen ajeno, no una preferencia.

    Si el espaciado medido baja del declarado, se ha pedido más deprisa de lo que
    el perfil promete — y eso invalida la condición 2 de ADR-0031, que es una de
    las cinco que sostienen el argumento para bajar el XML.
    """
    plan = {
        "ventana": {"desde": "2026-08-03", "hasta": "2026-08-03"},
        "objetivo_emparejados": 1,
        "ritmo_minimo_s": 1.0,
    }
    rapido = deepcopy(_manifiesto())
    rapido["ritmo"] = {"espaciado_mediano_s": 0.2}

    assert any("más rápido de lo prometido" in f for f in verificar(rapido, plan))
    assert verificar(_manifiesto(), plan) == [], "y al ritmo prometido, pasa"


# ---------------------------------------------------------------- disco
# Las ocho comprobaciones de arriba miran el manifiesto, y un manifiesto se
# escribe entero sin que exista un solo fichero: el bug del 24 ago 2026 —la
# cosecha tiraba los bytes— las habría pasado todas. Estos cuatro tests son la
# barrera de esa barrera, y van en las dos direcciones porque un verificador que
# fallara siempre pasaría los negativos sin comprobar nada.


def _corpus_en_disco(tmp: Path, n: int = 2) -> tuple[dict[str, object], Path]:
    """Un manifiesto **y sus bytes de verdad**, con los hashes que les tocan."""
    import hashlib

    docs = tmp / "docs"
    docs.mkdir()
    procedencias = []
    for i in range(n):
        ident = f"BOE-A-2026-{i:05d}"
        crudo = f"%PDF-1.4 documento {i}".encode()
        (docs / f"{ident}.pdf").write_bytes(crudo)
        (docs / f"{ident}.xml").write_bytes(b"<documento><texto/></documento>")
        procedencias.append(
            Procedencia(
                external_id=ident,
                fecha_sumario=date(2026, 8, 3),
                seccion="1",
                url_pdf=f"https://www.boe.es/boe/dias/2026/08/03/pdfs/{ident}.pdf",
                url_xml=f"https://www.boe.es/diario_boe/xml.php?id={ident}",
                sha256=hashlib.sha256(crudo).hexdigest(),
                n_pages=2,
                strata=frozenset({"tabla-simple"}),
                fetched_at=datetime(2026, 8, 3, 9, 0, tzinfo=UTC),
                cosechado_en=date(2026, 8, 24),
            )
        )
    manifiesto = crear(
        entidad="boe",
        plan_hash="f" * 64,
        desde=date(2026, 8, 3),
        hasta=date(2026, 8, 3),
        documentos=procedencias,
        licencia=PERFIL.licencia,
        umbral_coherencia=PERFIL.umbral_coherencia,
        intentados=n + 1,
        por_causa={"incoherente": 1},
        dias_sin_boletin=[date(2026, 8, 4)],
        espaciado_mediano_s=1.0,
        espaciado_minimo_s=1.0,
        n_espaciados=3,
    ).a_json()
    return manifiesto, docs


def test_un_corpus_que_esta_entero_en_disco_cumple(tmp_path: Path) -> None:
    """El aro en la dirección buena: sin él, los tres de abajo los pasaría un
    verificador que dijera «falla» a cualquier cosa."""
    manifiesto, docs = _corpus_en_disco(tmp_path)

    assert verificar(manifiesto, docs=docs) == []


def test_borrar_un_fichero_lo_caza_nombrandolo(tmp_path: Path) -> None:
    """**El bug del 24 ago 2026, exactamente.** La cosecha bajaba los documentos,
    decidía si emparejaban y tiraba los bytes: el manifiesto salía perfecto y el
    corpus no existía en ningún sitio.

    Y tiene que decir CUÁL falta: un «faltan ficheros» obliga a comparar mil
    entradas contra mil ficheros a mano para saber cuáles volver a bajar.
    """
    manifiesto, docs = _corpus_en_disco(tmp_path)
    (docs / "BOE-A-2026-00001.pdf").unlink()

    fallos = verificar(manifiesto, docs=docs)

    assert any("BOE-A-2026-00001" in f and "NO ESTA EN DISCO" in f for f in fallos)
    assert not any("BOE-A-2026-00000" in f for f in fallos), "sólo el que falta"


def test_cambiar_un_byte_lo_caza_por_hash(tmp_path: Path) -> None:
    """La otra dirección, y la que justifica rehacer el hash en vez de mirar si el
    fichero está: **el fichero está, y no es el que el manifiesto publica.**

    Un corpus con un byte cambiado sigue teniendo mil ficheros y mil entradas. Sin
    el hash, la única señal de que la verdad de referencia ya no es la que se midió
    sería que los números salieran raros seis meses después.
    """
    manifiesto, docs = _corpus_en_disco(tmp_path)
    victima = docs / "BOE-A-2026-00000.pdf"
    crudo = bytearray(victima.read_bytes())
    crudo[-1] ^= 0x01  # un bit
    victima.write_bytes(bytes(crudo))

    fallos = verificar(manifiesto, docs=docs)

    assert any("BOE-A-2026-00000" in f and "NO ES EL QUE DICE SER" in f for f in fallos)
    assert not any("NO ESTA EN DISCO" in f for f in fallos), "está: lo que pasa es que no es él"


def test_un_xml_vacio_es_medio_emparejado_y_pone_rojo(tmp_path: Path) -> None:
    """La otra mitad del bug: el PDF cuadra y el XML es de cero bytes.

    Pasaría el hash —el manifiesto sólo pone hash al PDF, límite 62— y el corpus
    sería mil PDFs sin verdad de referencia, que es la mitad de §16.
    """
    manifiesto, docs = _corpus_en_disco(tmp_path)
    (docs / "BOE-A-2026-00001.xml").write_bytes(b"")

    assert any("VACIO" in f for f in verificar(manifiesto, docs=docs))


def test_sin_directorio_no_dice_que_cumple_dice_no_ejecutada(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Una comprobación que no corre no es una comprobación que pasa.**

    Es el fallo de diseño más fácil de cometer aquí: si al no encontrar el
    directorio esto se saltara la comprobación y devolviera 0, imprimiría «CUMPLE»
    sobre un corpus que nadie ha mirado, y sería peor que no tenerla — porque
    además tranquiliza. Mismo criterio que la severidad `NO_EJECUTADA` de
    `entity.conformance`, donde `pasa` exige cero de ésas.
    """
    import json as _json

    import verificar_corpus

    manifiesto, docs = _corpus_en_disco(tmp_path)
    ruta = tmp_path / "manifiesto.json"
    ruta.write_text(_json.dumps(manifiesto, default=str), encoding="utf-8")
    for f in docs.iterdir():
        f.unlink()
    docs.rmdir()
    monkeypatch.setattr(sys, "argv", ["verificar_corpus.py", str(ruta)])

    codigo = verificar_corpus.main()

    assert codigo == 1
    assert "NO EJECUTADA" in capsys.readouterr().out
