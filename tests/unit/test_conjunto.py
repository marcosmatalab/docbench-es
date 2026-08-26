"""El conjunto de conformidad **se elige, no se toma** — y aquí se comprueba que no cede.

Si el conjunto no trajera ni una celda combinada, `veredicto_de_spans` devolvería
`SIN_EVIDENCIA` para todo extractor honesto y **el veredicto no discriminaría nada**: una
comprobación cuyo verde no significa lo que parece.

De ahí las dos cosas que estos tests sostienen, y ninguna es sobre leer un YAML:

1. **`trae_combinadas` sale del fixture congelado, no del YAML.** El YAML dice lo que cree;
   la verdad de L4 dice lo que hay. Si no cuadran, levanta.
2. **Un fixture que desaparece levanta en vez de valer 0 spans.** Ése es el agujero que
   `Elegido.cuadra` tenía en `scripts/conjunto_conformidad.py` hasta que se le puso
   `fixture_existe` delante: un fichero borrado degradaba el conjunto en silencio.

Corren en la puerta con un corpus de juguete, porque el de L3 no está en git (LIMITS 74).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from _corpus_falso import montar
from docbench_es.corpus.store import Almacen
from docbench_es.errors import ContractViolation
from docbench_es.extract.conjunto import cargar_conjunto, veredictos_posibles


def _montar(
    tmp_path: Path, *, spans_de: dict[str, int], plan: object
) -> tuple[Path, Almacen, Path]:
    """El corpus de juguete **más** los fixtures congelados que declaran sus spans."""
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    for tabla, spans in spans_de.items():
        (fixtures / f"{tabla}.json").write_text(
            json.dumps({"dimension": {"n_rows": 2, "n_cols": 2}, "spans": [{}] * spans}),
            encoding="utf-8",
        )
    almacen = montar(tmp_path, [t.rsplit("-t", 1)[0] for t in spans_de])
    ruta_plan = tmp_path / "conformidad.yaml"
    ruta_plan.write_text(yaml.safe_dump(plan), encoding="utf-8")
    return ruta_plan, almacen, fixtures


def _plan(con: list[str], sin: list[str]) -> dict[str, list[dict[str, str]]]:
    return {
        "con_celdas_combinadas": [{"id": t.rsplit("-t", 1)[0], "tabla": t} for t in con],
        "sin_celdas_combinadas": [{"id": t.rsplit("-t", 1)[0], "tabla": t} for t in sin],
    }


def test_el_conjunto_bueno_se_monta_y_dice_su_denominador(tmp_path: Path) -> None:
    """El control positivo. Sin él, los tests de «levanta» pasarían con una función que
    levantara siempre."""
    plan, almacen, fixtures = _montar(
        tmp_path, spans_de={"A-t0": 3, "B-t0": 0}, plan=_plan(["A-t0"], ["B-t0"])
    )
    conjunto = cargar_conjunto(plan, almacen, fixtures)
    assert len(conjunto.casos) == 2
    assert conjunto.con_combinadas == 1
    assert conjunto.hay_ocasion is True
    assert [c.trae_combinadas for c in conjunto.casos] == [True, False]
    assert "1 con celdas combinadas" in str(conjunto)
    assert "ESCONDIDO" in str(conjunto)


def test_un_fixture_que_desaparece_levanta_en_vez_de_valer_cero(tmp_path: Path) -> None:
    """**El agujero exacto**: sin fixture, `spans=0`, o sea «no trae combinadas», o sea un
    conjunto degradado a uno que ya no puede confirmar un `False` honesto."""
    plan, almacen, fixtures = _montar(
        tmp_path, spans_de={"A-t0": 3, "B-t0": 0}, plan=_plan(["A-t0"], ["B-t0"])
    )
    (fixtures / "A-t0.json").unlink()
    with pytest.raises(ContractViolation, match="A-t0"):
        cargar_conjunto(plan, almacen, fixtures)


def test_si_el_yaml_dice_una_cosa_y_la_verdad_congelada_otra_levanta(tmp_path: Path) -> None:
    """El YAML no es la última palabra: la tiene el fixture de L4, que está congelado."""
    plan, almacen, fixtures = _montar(
        tmp_path, spans_de={"A-t0": 0, "B-t0": 0}, plan=_plan(["A-t0"], ["B-t0"])
    )
    with pytest.raises(ContractViolation) as caido:
        cargar_conjunto(plan, almacen, fixtures)
    assert "A-t0" in str(caido.value)
    assert "con_celdas_combinadas" in str(caido.value)


def test_y_tambien_al_reves(tmp_path: Path) -> None:
    """Declararse «sin combinadas» trayéndolas también miente, y de esa se aprovecharía
    quien quisiera un conjunto que no puede producir `ESCONDIDO`."""
    plan, almacen, fixtures = _montar(
        tmp_path, spans_de={"A-t0": 1, "B-t0": 2}, plan=_plan(["A-t0"], ["B-t0"])
    )
    with pytest.raises(ContractViolation, match="B-t0"):
        cargar_conjunto(plan, almacen, fixtures)


@pytest.mark.parametrize(
    ("ocasion", "espera"),
    [(True, "ESCONDIDO"), (False, "SIN_EVIDENCIA")],
)
def test_los_veredictos_posibles_dependen_de_si_hay_ocasion(ocasion: bool, espera: str) -> None:
    """El denominador del conjunto. `CONTRADICCION` no depende de él —sale de lo que el
    extractor declare—; `ESCONDIDO` sí, porque hace falta que el documento las traiga."""
    posibles = veredictos_posibles(ocasion)
    assert espera in posibles
    assert "CONTRADICCION" in posibles
    assert "COHERENTE" in posibles
    assert ("SIN_EVIDENCIA" in posibles) is not ocasion
