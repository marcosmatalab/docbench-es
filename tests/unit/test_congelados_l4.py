"""Los 30 fixtures de L4 contra su manifiesto de huellas, **en la puerta**.

## Por qué esto es un test y no un hook

El límite 27 lo dejó escrito: los dos hooks son *prevención parcial más detección*,
y ninguno cubre el cambio hecho en el mismo turno en que ve el fichero por primera
vez. Su cierre de verdad, literal, era **«un test de la puerta que compare los
congelados contra un manifiesto de hashes versionado y publicado, no más hooks»**.

Y hasta ahora los fixtures de L4 **no los cubría ninguno de los dos**: los `matcher`
y los globs de `guard-frozen.sh` y `stop-gate.sh` son `tests/fixtures/{pubtabnet,
tablas,quickstart}` y `*/plan.yaml`, y estos viven en `runs/l4/fixtures/`. O sea que
el repo afirmaba «congeladas con hash» y no había nada que lo hiciera cumplir, que
es exactamente el fallo que la regla que gobierna el repo llama el más grave.

## Los tres candados, y cada uno dice una cosa distinta

1. **Las 30 coinciden con `recongelacion.json`.** Si alguien cambia una celda, rojo.
2. **27 de 30 conservan la huella de ANTES de la primera comparación.** Esto es lo
   que sostiene que la transcripción fue ciega: no basta con que hoy cuadren entre
   sí, tienen que cuadrar con el sello de `congelacion.json`, que se escribió antes
   de comparar ni una vez.
3. **Las 3 que cambiaron tienen su corrección registrada, y el texto que hay hoy en
   la celda es el que la corrección dice.** Un manifiesto que se rehace sin dejar
   rastro no congela nada.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
L4 = RAIZ / "runs" / "l4"
FIXTURES = L4 / "fixtures"


def _huella(nombre: str, carpeta: Path = FIXTURES) -> str:
    """El SUJETO: la huella de un fixture. `carpeta` existe para que el control
    negativo pueda apuntarlo a un fixture manipulado — sin eso, el control tendría
    que rehacer el cálculo por su cuenta y estaría probando `hashlib`, no esto."""
    return hashlib.sha256((carpeta / nombre).read_bytes()).hexdigest()


# Sin envoltorio tipado a propósito: `json.loads` devuelve `Any` y este repo
# prohíbe el `Any` EXPLÍCITO en anotaciones, así que una función que lo declarase
# pondría `mypy --strict` en rojo. Se leen aquí, una vez, y se usan como datos.
ORIGINAL = json.loads((L4 / "congelacion.json").read_text(encoding="utf-8"))
ACTUAL = json.loads((L4 / "recongelacion.json").read_text(encoding="utf-8"))
CORRECCIONES = json.loads((L4 / "correcciones.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("nombre", sorted(ACTUAL["huellas"]))
def test_cada_fixture_coincide_con_su_huella(nombre: str) -> None:
    """El candado 1. Si un test falla contra un congelado, el fallo está en el código."""
    assert _huella(nombre) == ACTUAL["huellas"][nombre], (
        f"{nombre} ha cambiado y su huella no. Si el cambio es legítimo va por"
        " scripts/corregir_fixtures_l4.py, con su evidencia contra el PDF"
    )


def test_los_26_no_tocados_conservan_la_huella_de_antes_de_comparar() -> None:
    """El candado 2, que es el que sostiene que la transcripción fue ciega."""
    intactos = [n for n in ORIGINAL["huellas"] if n not in ACTUAL["cambiados"]]

    assert len(intactos) == 26
    for nombre in intactos:
        assert _huella(nombre) == ORIGINAL["huellas"][nombre], (
            f"{nombre} no se tocó y aun así ha cambiado desde el congelado original"
        )


def test_los_4_cambiados_estan_respaldados_por_evidencia_o_son_solo_anotacion() -> None:
    """El candado 3: ninguna huella se mueve sin algo que la explique, **y las dos
    formas de explicarla son distintas y no se confunden**.

    - **corrección**: cambia una celda transcrita → exige evidencia contra el PDF.
    - **anotación**: la transcripción queda byte a byte igual → no la exige, porque
      no hay nada que evidenciar. Es lo que permitió marcar el fixture contaminado
      sin registrar una corrección falsa ni dejarlo sin marcar.
    """
    con_evidencia = {f"{c['fixture']}.json" for c in CORRECCIONES["correcciones"]}
    anotados = set(ACTUAL["por_anotacion_sin_tocar_la_transcripcion"])

    assert set(ACTUAL["por_correccion_con_evidencia"]) == con_evidencia
    assert anotados == {"BOE-A-2026-5979-t15.json"}
    assert set(ACTUAL["cambiados"]) == con_evidencia | anotados
    assert not (con_evidencia & anotados), "una corrección NO puede contarse como anotación"
    for c in CORRECCIONES["correcciones"]:
        assert c["evidencia"]["el_pdf_contiene_el_corregido"] is True
        assert c["evidencia"]["el_pdf_contiene_lo_que_puse"] is False


def test_la_anotacion_no_toco_ni_una_celda_de_la_transcripcion() -> None:
    """Lo que hace legítima la categoría «anotación»: se comprueba, no se promete.

    Si esto falla, alguien coló un cambio de contenido por la puerta de las
    anotaciones — que es exactamente la puerta que esa categoría abre.
    """
    import subprocess

    for nombre in ACTUAL["por_anotacion_sin_tocar_la_transcripcion"]:
        hecho = subprocess.run(
            ["git", "show", f"HEAD:runs/l4/fixtures/{nombre}"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=True,
        )
        viejo = json.loads(hecho.stdout)
        nuevo = json.loads((FIXTURES / nombre).read_text(encoding="utf-8"))

        for clave in ("filas", "ultima_fila", "spans", "dimension"):
            assert viejo.get(clave) == nuevo.get(clave), f"{nombre}: la anotación tocó {clave}"


def test_la_celda_corregida_dice_hoy_lo_que_la_correccion_afirma() -> None:
    """La cadena entera, comprobada sobre el fichero y no sobre el registro."""
    for c in CORRECCIONES["correcciones"]:
        fx = json.loads((FIXTURES / f"{c['fixture']}.json").read_text(encoding="utf-8"))
        fila, col = c["pos"]

        assert fx["filas"][fila][col] == c["el_pdf_dice"]
        assert fx["filas"][fila][col] != c["puse"]


def test_el_recuento_de_celdas_transcritas_no_ha_cambiado() -> None:
    """Corregir el TEXTO de 6 celdas no puede alterar cuántas hay: el denominador
    de «11 de 1.213» tiene que seguir siendo el mismo o el número no es comparable."""
    celdas = 0
    for nombre in sorted(ACTUAL["huellas"]):
        fx = json.loads((FIXTURES / nombre).read_text(encoding="utf-8"))
        celdas += sum(len(f) for f in fx["filas"]) + len(fx.get("ultima_fila", []))

    assert celdas == ORIGINAL["celdas_transcritas"] == 1213


def test_el_comparador_y_lo_que_mide_siguen_siendo_los_congelados() -> None:
    """Los 4 controles negativos de `test_comparar_verdad.py` sólo dicen algo si
    corrieron sobre **este** comparador y **esta** verdad derivada.

    `runs/l4/congelacion_comparador.json` selló cuatro ficheros antes de la primera
    comparación: el comparador, `truth.derived`, las reglas (ADR-0040) y la propia
    suite de controles. Si cualquiera de los cuatro cambia sin re-sellar, «los
    cuatro controles pasan» pasa a hablar de otro programa — y eso no se nota
    leyendo el número, que es lo peligroso.

    **Dos sellos, y el segundo no sustituye al primero.** `comparar_verdad.py` se
    tocó después de medir, para que emitiera su informe; los otros tres NO. Así que
    lo que se exige es lo fuerte: **los tres intactos siguen cuadrando con el sello
    ORIGINAL** —o sea que las reglas, la verdad derivada y la suite de controles son
    exactamente las de antes de la primera comparación— y el que cambió cuadra con
    el re-sello, que lleva escrito qué cambió y la prueba de que el número no se
    movió.
    """
    original = json.loads((L4 / "congelacion_comparador.json").read_text(encoding="utf-8"))
    resello = json.loads((L4 / "resello_comparador.json").read_text(encoding="utf-8"))

    assert resello["cambiados"] == ["scripts/comparar_verdad.py"], (
        "si cambia otro de los cuatro, el re-sello tiene que decirlo aquí: un cambio"
        " en ADR-0040, en truth.derived o en la suite de controles NO es «sólo salida»"
    )
    for fichero in resello["intactos"]:
        real = hashlib.sha256((RAIZ / fichero).read_bytes()).hexdigest()
        assert real == original["huellas"][fichero], (
            f"{fichero} está declarado INTACTO y no cuadra con el sello de antes de"
            " la primera comparación"
        )
    for fichero, esperado in resello["huellas"].items():
        real = hashlib.sha256((RAIZ / fichero).read_bytes()).hexdigest()
        assert real == esperado, f"{fichero} ha cambiado desde el re-sello"


def test_el_desglose_publicado_sale_del_informe_y_no_de_atar_cabos() -> None:
    """**21 limpias + 1 contaminada + 3 corregidas**, leído del artefacto.

    Antes esto se deducía cruzando a mano la lista de fixtures con discrepancia
    contra un `"contaminadas": 1` que no decía cuál era, y por eso se llegó a
    publicar una horquilla —«21 o 22»— sobre algo **completamente determinado por
    dos artefactos que ya existían**. La lección, que vale para cualquier cifra:
    **antes de declarar algo NO MEDIBLE, comprueba si es DERIVABLE de lo que ya está
    medido.**
    """
    informe = json.loads((L4 / "informe.json").read_text(encoding="utf-8"))
    desglose = informe["desglose_de_los_que_coinciden"]

    assert informe["coinciden"] == 25
    assert desglose == {"limpias": 21, "contaminadas": 1, "corregidas_tras_adjudicar": 3}
    assert sum(desglose.values()) == informe["coinciden"], "el desglose tiene que sumar"
    assert informe["contaminadas_declaradas"] == ["BOE-A-2026-5979-t15"]
    # Y la contaminada está entre las que COINCIDEN, que es lo que cierra la horquilla.
    fila = next(r for r in informe["por_fixture"] if r["contaminada"])
    assert fila["coincide"] is True


def test_un_fixture_manipulado_no_cuadra_con_su_huella(tmp_path: Path) -> None:
    """**EL CONTROL NEGATIVO, y sin él los cinco de arriba no dicen nada.**

    Los otros tests afirman que hoy todo cuadra. Un comprobador que dijera «cuadra»
    ante cualquier cosa los pasaría los cinco, y entonces «los 30 fixtures están
    congelados» sería una etiqueta, no una comprobación.

    Aquí se manipula un fixture de verdad —sobre una copia en `tmp_path`, que los
    originales están congelados— cambiando **un solo carácter de una celda**, que es
    la forma exacta que tendría «ajustar el fixture hasta que pase», y se exige que
    la huella deje de cuadrar.
    """
    nombre = "BOE-A-2026-6957-t0.json"
    copia = tmp_path / nombre
    fx = json.loads((FIXTURES / nombre).read_text(encoding="utf-8"))
    assert fx["filas"][7][0].endswith("Catauña."), "el fixture ya no dice lo que se corrigió"
    fx["filas"][7][0] = fx["filas"][7][0].replace("Catauña.", "Cataluña.")
    copia.write_text(json.dumps(fx, indent=1, ensure_ascii=False), encoding="utf-8")

    # **Se llama al SUJETO**, `_huella`, apuntado a la copia manipulada. La primera
    # versión de este control calculaba el sha256 a mano y por eso no probaba nada:
    # con `_huella` sustituida por «devuelve lo que dice el manifiesto» —o sea sin
    # abrir el fichero jamás— los 36 tests pasaban en verde. Detectado en el
    # escrutinio adversarial de este mismo cierre.
    manipulada = _huella(nombre, tmp_path)
    intacta = _huella(nombre)

    assert intacta == ACTUAL["huellas"][nombre], "el aro en la dirección buena"
    assert manipulada != ACTUAL["huellas"][nombre], (
        "un fixture con una celda cambiada da la misma huella: `_huella` no lee el fichero"
    )
    assert manipulada != ORIGINAL["huellas"][nombre], "tampoco puede cuadrar con la de antes"
