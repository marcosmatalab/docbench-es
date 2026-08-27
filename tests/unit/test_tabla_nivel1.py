"""La tabla de nivel 1: **ninguna columna sale sin su denominador.**

Lo que estos tests impiden son tres lecturas falsas que este repo ya ha visto:

* **una nota sin su cobertura.** Un TEDS de 0,91 sobre el 40% de las tablas y otro de 0,88
  sobre el 95% no se ordenan;
* **un recuento de tablas leído como calidad.** Por eso no hay columna de «tablas
  encontradas»: hay **acuerdo con la referencia**, que lleva la verdad dentro;
* **un `NO_APLICABLE` impreso como `0,00`.** Decisión B3: un cero sólo puede significar
  que se midió cero.

Y comprueban que el **régimen** y el **agregado** salen escritos, que es lo que ADR-0045
metió dentro de la métrica precisamente para que no dependieran de la memoria de quien
escribe la tabla.
"""

from __future__ import annotations

from benchcore.types import Cost

from docbench_es.report.nivel1 import Deteccion, Nivel1
from docbench_es.report.tables import tabla_nivel1
from docbench_es.types import StructureMetrics


def _fila(**cambios: object) -> Nivel1:
    base: dict[str, object] = {
        "teds": 0.9123,
        "teds_s": 0.9456,
        "cell_f1": 0.8899,
        "evaluable_coverage": 0.372,
        "failures": {"corrupt_pdf": 2},
        "n_documents": 300,
        "agregado": "POR_DOCUMENTO",
        "regimen": "CENSO",
    }
    base.update(cambios)
    return Nivel1(
        metricas=StructureMetrics(**base),  # type: ignore[arg-type]
        deteccion=Deteccion(
            documentos=338,
            con_recuento_igual=300,
            tablas_de_mas=17,
            tablas_de_menos=41,
            tablas_de_la_verdad=2135,
        ),
        teds_por_pagina=0.8765,
        coste=Cost(wall_ms=1234),
        latencia_mediana_ms=412,
        n_extracciones=616,
        paginas=8733,
        por_documento=dict.fromkeys((f"D{i}" for i in range(300)), 0.9123),
    )


def test_la_nota_y_su_cobertura_van_en_la_misma_fila() -> None:
    """La cobertura no es una nota al pie: es de la fila, o la nota se lee sola."""
    texto = tabla_nivel1({"pdfplumber": _fila()}, {"pdfplumber": "0.11.9+ad1"})
    fila = next(x for x in texto.splitlines() if "pdfplumber" in x)
    assert "0,9123" in fila
    assert "37,2%" in fila, fila
    assert "0.11.9+ad1" in fila, "la versión también: sin ella, dos configuraciones se funden"


def test_un_no_aplicable_se_imprime_n_a_y_nunca_cero() -> None:
    """**Decisión B3 en el renderizado.** Es el último sitio donde un `None` puede
    convertirse en un cero, y por eso se comprueba aquí y no sólo en el tipo."""
    texto = tabla_nivel1(
        {"x": _fila(teds=None, teds_s=None, cell_f1=None, n_documents=0)}, {"x": "1"}
    )
    fila = next(x for x in texto.splitlines() if "| `x` |" in x)
    assert fila.count("n/a") == 3, fila
    assert "0,0000" not in fila


def test_el_acuerdo_de_recuento_no_se_llama_tablas_encontradas() -> None:
    """Contar tablas no es calidad: uno que parte una tabla en tres encuentra más y uno
    que fusiona dos encuentra menos **y puede estar acertando**."""
    texto = tabla_nivel1({"x": _fila()}, {"x": "1"})
    assert "acuerdo de recuento" in texto
    assert "tablas encontradas" not in texto
    assert "+17/-41" in texto
    assert "NO es una columna de calidad" in texto


def test_el_regimen_y_el_agregado_salen_escritos() -> None:
    """ADR-0045: viajan dentro de la métrica para no depender de quien escribe la tabla."""
    texto = tabla_nivel1({"x": _fila()}, {"x": "1"})
    assert "POR_DOCUMENTO" in texto
    assert "CENSO" in texto
    assert "no llevan intervalo" in texto


def test_los_denominadores_de_las_dos_coberturas_estan_dichos() -> None:
    """Son dos y son distintas: la evaluable es sobre TABLAS y el acuerdo sobre
    DOCUMENTOS. Sin decirlo, un lector supone que son la misma."""
    texto = tabla_nivel1({"x": _fila()}, {"x": "1"})
    assert "338" in texto and "2135" in texto
    assert "sobre tablas" in texto and "sobre documentos" in texto


def test_cero_fallos_se_imprime_cero_y_no_vacio() -> None:
    """Un hueco se lee como «no se miró». La tasa de fallo es un resultado publicado."""
    texto = tabla_nivel1({"x": _fila(failures={})}, {"x": "1"})
    fila = next(x for x in texto.splitlines() if "| `x` |" in x)
    assert "| 0 |" in fila, fila


def test_una_tabla_sin_extractores_lo_dice_en_vez_de_salir_en_blanco() -> None:
    """El caso degenerado: cero filas no es «todo bien», es que no se midió nada."""
    texto = tabla_nivel1({}, {})
    assert "no es un resultado" in texto


def test_la_cara_a_cara_sale_debajo_y_con_su_n() -> None:
    """Va en la MISMA tabla y no en un documento aparte: separarla es cómo se acaba
    citando la que no toca."""
    texto = tabla_nivel1({"a": _fila(), "b": _fila()}, {})
    assert "Cara a cara" in texto
    assert "300 de 338" in texto, texto
    assert "sesgo de supervivencia" in texto
    assert "no es un ranking" in texto.lower()


def test_sin_interseccion_la_tabla_dice_que_no_hay_comparacion() -> None:
    """No es un empate ni un cero: es que no se pueden comparar. Y es un resultado sobre
    el corpus, no un fallo de la tabla."""
    a = _fila()
    b = _fila()
    object.__setattr__(b, "por_documento", {"OTRO": 0.5})
    texto = tabla_nivel1({"a": a, "b": b}, {})
    assert "No hay intersección" in texto
    assert "no es un empate" in texto.lower()


def test_las_filas_salen_en_orden_estable() -> None:
    """Dos corridas del mismo informe dan el mismo fichero: si no, un `diff` entre
    campañas sería ruido."""
    filas = {"zeta": _fila(), "alfa": _fila()}
    primero = tabla_nivel1(filas, {})
    assert primero == tabla_nivel1(dict(reversed(list(filas.items()))), {})
    assert primero.index("`alfa`") < primero.index("`zeta`")


def test_la_tabla_dice_en_su_cabecera_que_no_es_un_ranking() -> None:
    """**En la cabecera, no en una nota al pie.** Un lector casual que sólo lee lo de
    arriba tiene que salir sabiendo que esto no ordena a nadie; si la advertencia vive al
    final, la tabla ya se leyó como un ranking antes de llegar a ella."""
    texto = tabla_nivel1({"a": _fila(), "b": _fila()}, {})
    cabeza = texto.split("| extractor |")[0]
    assert "ESTO NO ES UN RANKING" in cabeza, cabeza
    assert "necesario y no suficiente" in cabeza
    assert "L6" in cabeza, "el hito que lo cierra va al lado, o la negativa parece un hueco"
    assert "ADR-0009" in cabeza


def test_ninguna_de_las_dos_tablas_ordena_las_filas_por_nota() -> None:
    """**Ordenar por nota ES ordenar**, diga lo que diga el texto de al lado. Es la única
    forma de que la cabecera y el renderizado no se contradigan — y se contradecían: la
    cara a cara salía con `key=lambda x: -x[1]` debajo de la frase «no se ordena a nadie».
    """
    peor, mejor = _fila(), _fila()
    object.__setattr__(peor, "por_documento", dict.fromkeys((f"D{i}" for i in range(300)), 0.10))
    object.__setattr__(mejor, "por_documento", dict.fromkeys((f"D{i}" for i in range(300)), 0.99))
    texto = tabla_nivel1({"zeta_mejor": mejor, "alfa_peor": peor}, {})
    assert texto.index("`alfa_peor`") < texto.index("`zeta_mejor`"), (
        "el que puntúa 0,10 va primero porque se llama alfa, no porque puntúe peor"
    )
    cara = texto.split("### Cara a cara")[1]
    assert cara.index("`alfa_peor`") < cara.index("`zeta_mejor`"), cara
    assert "Alfabético, no por nota" in cara


def test_el_coste_va_en_su_propio_bloque_con_su_propio_denominador() -> None:
    """**Misma fila implica mismo denominador**, y aquí no lo es: el TEDS se cuenta sobre
    el conjunto evaluable de cada extractor —≤338 y distinto para cada uno— y el coste
    sobre los 616, porque un documento cuesta tiempo aunque no puntúe. Meterlos en la
    misma fila sería el 2.283 con otra cara."""
    texto = tabla_nivel1({"x": _fila()}, {"x": "1"}, {"cpus": 14, "carga": 1.39})
    coste = texto.split("### Coste")[1]
    assert "616 documentos y 8733 páginas" in coste, coste
    assert "No es la n del TEDS" in coste
    assert "s/página" in coste and "s/documento" in coste
    assert "14 CPU visibles" in coste
    assert "1,39" in coste, "coma decimal, como el resto de la tabla — no 1.39"


def test_cero_euros_es_un_cero_medido_y_no_un_hueco() -> None:
    """La misma distinción que separa `n/a` de `0,00`, un eje más allá: estos cuatro
    corren en local y no gastan, y eso es un dato."""
    coste = tabla_nivel1({"x": _fila()}, {"x": "1"}, {}).split("### Coste")[1]
    assert "0,00 €" in coste, coste
    assert "cero MEDIDO" in coste


def test_un_sello_sin_modelo_de_cpu_lo_dice_en_vez_de_leerlo_de_la_maquina() -> None:
    """El informe se regenera meses después y en otra máquina. Rellenar el hueco con lo
    que haya debajo publicaría la CPU equivocada como si fuera la de la corrida."""
    coste = tabla_nivel1({"x": _fila()}, {"x": "1"}, {"cpus": 14}).split("### Coste")[1]
    assert "no registrado" in coste, coste
