"""La página entera. **La plantilla no sabe aritmética y no escribe ningún número.**

Cada cifra entra por `marca(...)`, que la saca de `_cifras.cifras()` por su clave y la
imprime dentro de un elemento con `data-cifra`. Si una clave no existe, esto **revienta**
en vez de imprimir un hueco: un `KeyError` en la generación es barato, y un número que
falta en la portada no se ve.

## El orden de las secciones es la mitad del trabajo, y va escrito

1. **qué es**, y quién lo publica — que no vende extracción documental;
2. **el titular**, con el panel DENTRO de la etiqueta y la monotonía atada al número;
3. **el acuerdo por bandas**, con la no-monotonía y el hueco declarado;
4. **las cuatro notas**, con la cobertura en la columna de al lado y el aviso en el
   `caption`, que es donde lo lee quien va a mirar la tabla y no debajo, que es donde lo
   lee quien ya se ha hecho una idea;
5. **la errata**, con el titular tachado — y va **antes** del método, no después. Un repo
   que dice «tengo N mutantes» es uno más; uno que enseña su titular tachado y **luego**
   dice que tiene N mutantes se lee de otra manera;
6. el **método** en seis líneas;
7. **cuatro límites**, los que más cambian cómo se leen los números de arriba;
8. **cuatro puertas** a la profundidad.
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

from docbench_es.report.portada._cierre import limites, pie, puertas
from docbench_es.report.portada._estilo import ESTILO, FUENTES

if TYPE_CHECKING:  # pragma: no cover - sólo para tipar
    from collections.abc import Mapping

    from docbench_es.report.portada._cifras import Cifra

__all__ = ["marca", "pagina"]


def _v(cifras: Mapping[str, Cifra], clave: str) -> str:
    return escape(cifras[clave].valor)


def marca(cifras: Mapping[str, Cifra], clave: str, tag: str = "span", clase: str = "") -> str:
    """Una cifra, dentro de un elemento que dice cuál es. **La marca es el contrato.**

    Sin `data-cifra`, R9 tendría que buscar «¿aparece 103 en el HTML?», y 103 aparece
    también en el pie y en cualquier tabla: un guardián que no puede distinguir el
    titular de una coincidencia no vigila el titular.
    """
    c = f' class="{clase}"' if clase else ""
    return f'<{tag} data-cifra="{clave}"{c}>{_v(cifras, clave)}</{tag}>'


def _cabecera(c: Mapping[str, Cifra]) -> str:
    tiras = " ".join(
        f"<span>{etiqueta} {marca(c, clave, 'b')}</span>"
        for etiqueta, clave in (
            ("cerrado el", "fecha"),
            ("sello", "sello_corrida"),
            ("unidades", "unidades"),
            ("fallos", "fallos"),
            ("coste", "coste"),
        )
    )
    return f"""<header class="masthead">
  <h1 class="wordmark">docbench&#8209;es <span>· nivel 1 · {marca(c, "hito")}</span></h1>
  <p class="standfirst">El primer banco de pruebas de extracción documental en español,
  medido sobre el BOE. <strong>Lo publica alguien que no vende extracción
  documental</strong>: aquí el juez no es concursante y no hay extractor propio en la
  tabla.</p>
  <div class="strip">{tiras}</div>
</header>"""


def _titular(c: Mapping[str, Cifra]) -> str:
    """El titular, **con el panel dentro de la etiqueta y la monotonía atada al número**.

    Las dos cosas viven en el mismo bloque que la cifra y no en una nota al pie, y es la
    decisión entera del límite 113: «N de 338» sin decir sobre qué panel está
    **incompleto**, porque es una intersección sobre tantos conjuntos como extractores
    tenga el panel, y añadir uno sólo puede bajarlo.
    """
    return f"""<section>
  <p class="eyebrow">El titular</p>
  <div class="figure">
    {marca(c, "titular", "span", "n")}
    <p class="q">documentos con tabla en los que los
    <strong>{marca(c, "panel_n")}</strong> extractores coinciden con la referencia en
    <strong>cuántas tablas hay</strong>. <em>El {marca(c, "titular_pct")}.</em></p>
    <p class="bind"><b>Sobre el panel de {marca(c, "panel_n")}</b> —
    <code data-cifra="panel">{_v(c, "panel")}</code>. El panel va dentro de la etiqueta
    porque el número <b>sólo sabe bajar</b> al añadir un extractor: es una intersección,
    no una nota. Dos valores con paneles distintos no son comparables y no van en la
    misma serie.</p>
  </div>
  <p>En el {marca(c, "titular_resto_pct")} restante, al menos uno de los
  {marca(c, "panel_n")} discrepa en el <strong>paso previo a cualquier métrica de
  calidad</strong>. Antes de discutir si una tabla está bien extraída hay que estar de
  acuerdo en cuántas tablas hay.</p>
{_bandas(c)}
</section>"""


def _bandas(c: Mapping[str, Cifra]) -> str:
    """La tabla del acuerdo por banda. **Se destacan el máximo y el mínimo, no una fila
    elegida**: son los dos extremos que sostienen la frase de abajo —que no es monótono—
    y marcar cualquier otra cosa sería subrayar una lectura."""
    claves = [k for k in c if k.endswith("_tasa") and k.startswith("banda")]
    valores = {k: float(c[k].valor.rstrip("%").replace(",", ".")) for k in claves}
    extremos = {min(valores, key=lambda k: valores[k]), max(valores, key=lambda k: valores[k])}
    filas = []
    for i in range(len(claves)):
        filas.append(
            "        <tr>"
            + marca(c, f"banda{i}_nombre", "td")
            + marca(c, f"banda{i}_poblacion", "td")
            + marca(c, f"banda{i}_coinciden", "td")
            + marca(c, f"banda{i}_tasa", "td", "lead" if f"banda{i}_tasa" in extremos else "")
            + "</tr>"
        )
    return f"""  <div class="scroll">
    <table>
      <caption><b>El acuerdo por longitud del documento.</b> El mínimo <b>no</b> está en
      los documentos largos.</caption>
      <thead>
        <tr><th>Banda de páginas</th><th>Documentos</th><th>Coinciden todos</th><th>Tasa</th></tr>
      </thead>
      <tbody>
{chr(10).join(filas)}
      </tbody>
    </table>
  </div>
  <p class="nota"><strong>No es monótono con la longitud</strong>, así que la explicación
  fácil —«los documentos largos son más difíciles»— está descartada por la propia tabla.
  <strong>Qué lo ordena de verdad no está medido</strong>, y eso se publica como hueco y
  no como hipótesis: hay un candidato escrito, con el cruce que lo confirmaría o lo
  descartaría, y no está hecho.</p>"""


def _notas(c: Mapping[str, Cifra], extractores: list[str]) -> str:
    filas = [
        "        <tr>"
        + f'<td data-cifra="nota_{n}_nombre">{escape(n)}</td>'
        + marca(c, f"nota_{n}_teds", "td")
        + marca(c, f"nota_{n}_teds_s", "td")
        + marca(c, f"nota_{n}_cell_f1", "td")
        + marca(c, f"nota_{n}_cobertura", "td", "cov")
        + marca(c, f"nota_{n}_latencia", "td", "cov")
        + "</tr>"
        for n in extractores
    ]
    return f"""<section>
  <p class="eyebrow">Las notas, con lo que las califica</p>
  <h2>Ninguna de estas notas es comparable con las otras</h2>
  <div class="scroll">
    <table>
      <caption>Cada TEDS se calcula sobre las tablas que ese extractor <b>pudo
      evaluar</b>, y esa fracción va de {marca(c, "cobertura_min")} a
      {marca(c, "cobertura_max")}. Ordenar esta columna produciría un ranking falso: los
      denominadores no son el mismo conjunto. La comparación que sí vale es la cara a
      cara sobre los {marca(c, "cara_a_cara_n")} documentos que puntuaron todos, y ahí
      <b>el orden cambia</b>. <b>Esto no es un ranking</b>: la ordenación con su potencia
      llega en L6.</caption>
      <thead>
        <tr><th>Extractor</th><th>TEDS</th><th>TEDS&#8209;S</th><th>F1 celda</th>
        <th>Cobertura evaluable</th><th>Latencia mediana</th></tr>
      </thead>
      <tbody>
{chr(10).join(filas)}
      </tbody>
    </table>
  </div>
</section>"""


def _errata(c: Mapping[str, Cifra], cuantas: int) -> str:
    return f"""<section>
  <p class="eyebrow">Por qué creérselo</p>
  <h2>El titular de este hito se publicó mal, y la corrección está en la historia de git</h2>
  <div class="errata">
    <p class="tag">Errata</p>
    <div class="swap">
      {marca(c, "errata_antes", "span", "was")}
      <span class="arrow">&rarr;</span>
      {marca(c, "errata_ahora", "span", "now")}
    </div>
    <p><strong>Era otra cuenta.</strong> El número tachado existe y es correcto
    <strong>para otra pregunta</strong>: son los documentos donde todos
    <strong>puntuaron</strong>. El titular decía «coinciden en cuántas tablas hay», que
    es otra. Los {marca(c, "errata_diferencia")} de diferencia son documentos donde
    <strong>todos acertaron el recuento</strong> y al menos uno no pudo evaluar ni una
    tabla, porque la verdad trae celdas combinadas y él no expresa <code>rowspan</code>.
    Se publicaban como desacuerdo.</p>
    <p><strong>Ningún fixture tenía una celda combinada</strong>, y en ese mundo «acertar
    el recuento» y «puntuar» son literalmente el mismo conjunto: ninguna aserción posible
    sobre esos datos de prueba podía distinguirlos. No faltaba un test, faltaba un caso.
    Lo encontró un escrutinio adversarial leyendo, no ejecutando.</p>
    <p><strong>El commit con el titular falso sigue en la historia</strong>, con la
    corrección detrás. Borrarlo habría sido más limpio y menos cierto.</p>
  </div>
  <p>Ése es el mecanismo del proyecto entero funcionando sobre su propio peor caso. Lo
  que lo sostiene el resto del tiempo:</p>
{_metodo(c, cuantas)}
</section>"""


def _puerta(c: Mapping[str, Cifra]) -> str:
    """La línea de la puerta, **y dice si la alarma está sonando o no**.

    Publicar «p90 de 7.845 ms» cuando el último medido son 8.438 sería escribir en
    presente lo que ya no se mide, en la puerta de entrada del proyecto — que es lo que
    este repo llama el peor fallo posible, más grave que un bug. Así que los dos números
    van juntos y **la frase la decide la comparación**, no quien escribe la plantilla.

    Y cuando suena se dice **por qué no se ha apagado**: subir un techo después de
    romperlo es la salida cómoda que ADR-0022 prohíbe. Una alarma que se apaga sola no es
    una alarma.

    **Desde ADR-0048 el número publicado es el PEOR de las dos series**, no el de una:
    publicar el mejor sería elegir el que conviene y la media escondería la cola. Va el
    peor, que es hacia donde redondea un techo.
    """
    p90 = int(c["p90"].valor.replace(".", ""))
    techo = int(c["techo"].valor.replace(".", ""))
    baja = (
        f"El techo <b>bajó</b> de {marca(c, 'techo_anterior')} a {marca(c, 'techo')} ms "
        "este hito, por una regla escrita antes de medirlo: es la primera vez que baja."
    )
    if p90 <= techo:
        return (
            f"p90 de {marca(c, 'p90', 'b')} ms, <b>el peor de dos series</b> de 40 "
            f"corridas en frío: las dos por debajo del techo, que es lo que hace falta "
            f"para no darlo por roto (ADR-0048). {baja}"
        )
    return (
        f"{baja} Y el peor p90 de las dos últimas series son {marca(c, 'p90', 'b')} ms, "
        "o sea <b>por encima del techo</b>. No se sube un techo para que deje de avisar: "
        "la decisión está abierta y escrita, con el coste medido y atribuido."
    )


def _metodo(c: Mapping[str, Cifra], cuantas: int) -> str:
    filas = (
        (
            "pre-registro",
            "Cada criterio se escribe <b>antes</b> de medir, con su comando. Cuando sale "
            "en contra, sale publicado en contra: este hito declaró <b>inválido</b> uno "
            "de sus propios criterios porque no nombraba la columna que lo medía.",
        ),
        (
            "mutantes",
            f"{marca(c, 'mutantes', 'b')} mutantes contra el código de producción, todos "
            "mueren, y un <b>control negativo</b> que demuestra que la suite no mata por "
            "accidente. Uno de ellos le quita el panel a esta misma página.",
        ),
        (
            "derivadas",
            f"Un número derivado <b>no se teclea</b>. Las <b>{cuantas}</b> cifras de esta "
            "página las recalcula la puerta contra <code>runs/l5/informe.json</code> y "
            "contra el censo del repo: ni una está escrita en la plantilla.",
        ),
        (
            "límites",
            f"{marca(c, 'limites', 'b')} cosas que este banco <b>no</b> mide, escritas el "
            "día que se descubren y no al final.",
        ),
        ("la puerta", _puerta(c)),
        (
            "coste",
            f"{marca(c, 'coste', 'b')}, medido y no supuesto. Y la predicción del reloj "
            f"falló: {marca(c, 'error_estimador', 'b')} contra lo medido, publicado con "
            "sus dos operandos sin redondear.",
        ),
    )
    cuerpo = "\n".join(f"    <div><dt>{t}</dt><dd>{d}</dd></div>" for t, d in filas)
    return f'  <dl class="method">\n{cuerpo}\n  </dl>'


def pagina(cifras: Mapping[str, Cifra], extractores: list[str], base: str) -> str:
    """La portada entera, en una cadena. `base` es el prefijo de los enlaces al repo."""
    cuerpo = "\n\n".join(
        (
            _cabecera(cifras),
            _titular(cifras),
            _notas(cifras, extractores),
            _errata(cifras, len(cifras)),
            limites(cifras),
            puertas(cifras, base),
            pie(cifras),
        )
    )
    return (
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>docbench-es · banco de extracción documental en español</title>\n"
        f"{FUENTES}\n<style>\n{ESTILO}</style>\n</head>\n<body>\n"
        f'<div class="wrap">\n\n{cuerpo}\n\n</div>\n</body>\n</html>\n'
    )
