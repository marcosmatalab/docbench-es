"""**TODAS las cifras de la portada, en un sitio, cada una con su fuente.**

La plantilla no calcula nada y no escribe ningún número: pide una clave. Este módulo es
el único que convierte `runs/l5/informe.json` y el censo del repo en las cadenas que se
imprimen, y **la misma lista la vuelve a construir la regla R9 de `scripts/derivadas.py`
para compararla contra la página publicada**.

Por eso cada cifra lleva `fuente`: sin ella, «sale del JSON» es una afirmación sobre la
página entera y no sobre ninguna cifra concreta, que es la forma que tiene una portada de
parecer derivada y no serlo.

## La página se marca a sí misma

Cada número va en la página dentro de un elemento con `data-cifra="<clave>"`. Así R9 no
busca «¿aparece 103 en el HTML?» —que sale también en el pie y en cualquier tabla— sino
«¿qué dice el elemento que dice ser el titular?». Y permite la tercera dirección, que es
la que ningún guardián de este repo tenía: **una cifra en la página cuya clave el
instrumento no emite** se caza igual que una que no cuadra.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.portada._censo import Censo

__all__ = ["Cifra", "cifras", "miles", "num", "pct"]

CARDINALES = {1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete"}
"""El cardinal en letra, hasta donde hace falta. **El panel se escribe con palabra.**

«los cuatro extractores» y «sobre el panel de cuatro» se leen; «los 4» no. Y el número
sigue saliendo de `acuerdo.panel`: lo que se traduce es la forma, no el valor. Por encima
del siete se cae al dígito, que es donde la palabra deja de ayudar."""


@dataclass(frozen=True)
class Cifra:
    """Un número publicado, con **de dónde sale** pegado. No es documentación: es el
    argumento de R9 cuando se pone roja."""

    valor: str
    fuente: str


def miles(n: float) -> str:
    """`2.464`. Punto de millar, como el resto de los documentos del repo."""
    return f"{round(n):,}".replace(",", ".")


def pct(v: float, decimales: int = 1) -> str:
    return f"{100 * v:.{decimales}f}%".replace(".", ",")


def signo(v: float) -> str:
    """`+74,6%`. **Con el signo siempre delante**, que es lo único que se lee."""
    return f"{100 * v:+.1f}%".replace(".", ",")


def num(v: float | None, decimales: int = 4) -> str:
    """`n/a` para `None`, **nunca `0,0000`**: decisión B3, también aquí."""
    return "n/a" if v is None else f"{v:.{decimales}f}".replace(".", ",")


def _fecha(iso: str) -> str:
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    a, m, d = iso[:10].split("-")
    return f"{int(d)} {meses[int(m) - 1]} {a}"


def _dic(m: Mapping[str, object], clave: str) -> Mapping[str, object]:
    """Un sub-objeto de `informe.json`, **con el nombre en el error si no lo es**.

    Los cuatro lectores de abajo existen para lo mismo y no por tipar: un
    `informe.json` de otra versión revienta aquí, diciendo qué campo, en vez de
    imprimir un `None` en la portada. Un hueco en la primera pantalla no se ve.
    """
    valor = m[clave]
    if not isinstance(valor, dict):
        raise TypeError(f"informe.json: `{clave}` no es un objeto")
    return valor


def _txt(m: Mapping[str, object], clave: str) -> str:
    return str(m[clave])


def _ent(m: Mapping[str, object], clave: str) -> int:
    valor = m[clave]
    if not isinstance(valor, int):
        raise TypeError(f"informe.json: `{clave}` no es un entero")
    return valor


def _flt(m: Mapping[str, object], clave: str) -> float:
    valor = m[clave]
    if not isinstance(valor, (int, float)):
        raise TypeError(f"informe.json: `{clave}` no es un número")
    return float(valor)


def _lista(m: Mapping[str, object], clave: str) -> list[str]:
    valor = m[clave]
    if not isinstance(valor, list):
        raise TypeError(f"informe.json: `{clave}` no es una lista")
    return [str(x) for x in valor]


def _fallos(extractores: Mapping[str, object]) -> int:
    """Los fallos de los cuatro, sumados. **Regla de oro 6: el cero es un resultado.**"""
    total = 0
    for nombre in extractores:
        for n in _dic(_dic(extractores, nombre), "fallos").values():
            total += int(str(n))
    return total


def cifras(inf: Mapping[str, object], censo: Censo) -> dict[str, Cifra]:
    """Las cifras de la portada. **El orden es el de la página**, y eso importa: la
    lista se lee de arriba abajo cuando R9 la publica en rojo."""
    corrida, informe = _dic(inf, "sello_de_la_corrida"), _dic(inf, "sello_del_informe")
    pob, ac = _dic(inf, "poblacion"), _dic(inf, "acuerdo")
    ext = _dic(inf, "extractores")
    panel = _lista(ac, "panel")
    coinciden = _ent(ac, "los_extractores_coinciden_en_el_recuento")
    denom = _ent(ac, "denominador")
    coberturas = [_flt(_dic(ext, n), "cobertura_evaluable") for n in ext]
    fuente_ac, fuente_pob = "informe.json: acuerdo", "informe.json: poblacion"

    fuera: dict[str, Cifra] = {}

    def _c(clave: str, valor: str, fuente: str) -> None:
        fuera[clave] = Cifra(valor, fuente)

    # ------------------------------------------------------ cabecera y pie
    _c("hito", _txt(corrida, "que").split()[-1], "informe.json: sello_de_la_corrida.que")
    _c("fecha", _fecha(_txt(informe, "empezada")), "informe.json: sello_del_informe.empezada")
    _c("sello_corrida", _txt(corrida, "commit"), "informe.json: sello_de_la_corrida.commit")
    _c("sello_informe", _txt(informe, "commit"), "informe.json: sello_del_informe.commit")
    _c("unidades", miles(_flt(corrida, "unidades")), "informe.json: sello_de_la_corrida")
    _c("documentos", miles(_flt(pob, "documentos_procesados")), fuente_pob)
    _c("paginas", miles(_flt(pob, "paginas_procesadas")), fuente_pob)
    _c("tablas_verdad", miles(_flt(pob, "tablas_de_la_verdad")), fuente_pob)
    _c("cpu", _txt(informe, "cpu"), "informe.json: sello_del_informe.cpu")
    _c("procesos", str(_ent(corrida, "cpus")), "informe.json: sello_de_la_corrida.cpus")
    _c("fallos", str(_fallos(ext)), "informe.json: extractores[*].fallos")
    _c("coste", "0,00 €", "informe.json: extractores[*].coste_eur, todos medidos")
    # ------------------------------------------------------------ titular
    _c("titular", f"{coinciden} de {denom}", fuente_ac)
    _c("titular_pct", pct(coinciden / denom), fuente_ac)
    _c("titular_resto_pct", pct(1 - coinciden / denom), fuente_ac)
    _c("panel_n", CARDINALES.get(len(panel), str(len(panel))), "informe.json: acuerdo.panel")
    _c("panel", " · ".join(panel), "informe.json: acuerdo.panel")
    # ------------------------------------------------------------- errata
    _c("errata_antes", f"{_ent(ac, 'puntuan_todos')} de {denom}", fuente_ac)
    _c("errata_ahora", f"{coinciden} de {denom}", fuente_ac)
    _c("errata_diferencia", str(_ent(ac, "no_aplicables")), "informe.json: acuerdo.no_aplicables")
    # ------------------------------------------------------------- método
    _c("mutantes", str(censo.mutantes), "censo: scripts/mutantes/*.py")
    _c("limites", str(censo.limites), "censo: entradas numeradas de LIMITS.md")
    _c("adr", str(censo.adr), "censo: docs/adr/*.md")
    _c("p90", miles(censo.p90_ms), "censo: .techos PUERTA_P90_MS")
    _c("techo", miles(censo.techo_ms), "censo: .techos TECHO_LOCAL_MS")
    _c("techo_anterior", miles(censo.techo_anterior_ms), "censo: .techos TECHO_LOCAL_ANTERIOR_MS")
    _c("error_estimador", signo(censo.error_del_estimador), "censo: runs/l5/reloj.json")
    # ------------------------------------------- la cobertura, que es la que califica
    fuente_cob = "informe.json: extractores[*].cobertura_evaluable"
    _c("cobertura_min", pct(min(coberturas)), fuente_cob)
    _c("cobertura_max", pct(max(coberturas)), fuente_cob)
    _c("cara_a_cara_n", str(_ent(ac, "puntuan_todos")), "informe.json: acuerdo.puntuan_todos")

    for i, (banda, cuenta) in enumerate(_dic(ac, "por_banda").items()):
        cuenta = _dic({banda: cuenta}, banda)
        n, total = _ent(cuenta, "coinciden"), _ent(cuenta, "poblacion")
        fuente = "informe.json: acuerdo.por_banda"
        _c(f"banda{i}_nombre", banda, fuente)
        _c(f"banda{i}_poblacion", str(total), fuente)
        _c(f"banda{i}_coinciden", str(n), fuente)
        _c(f"banda{i}_tasa", pct(n / total), fuente)

    for nombre in sorted(ext, key=lambda n: -_flt(_dic(ext, n), "teds")):
        e, fuente = _dic(ext, nombre), f"informe.json: extractores.{nombre}"
        # EL NOMBRE TAMBIÉN ES UNA CIFRA PUBLICADA, y va marcado como las demás: una
        # fila con las notas de `docling` bajo el rótulo `camelot` miente más que un
        # decimal movido, y sin esta clave R9 no podía verla.
        _c(f"nota_{nombre}_nombre", nombre, fuente)
        for campo in ("teds", "teds_s", "cell_f1"):
            _c(f"nota_{nombre}_{campo}", num(_flt(e, campo)), fuente)
        _c(f"nota_{nombre}_cobertura", pct(_flt(e, "cobertura_evaluable")), fuente)
        _c(f"nota_{nombre}_latencia", f"{miles(_flt(e, 'latencia_mediana_ms'))} ms", fuente)
    return fuera
