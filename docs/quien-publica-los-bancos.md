# Quién publica los ocho bancos

La regla de oro 1 de este repo —**no construye ni construirá un extractor propio**,
porque si lo hiciera su ranking valdría cero— suena a precaución teórica.

En agosto de 2026, de los ocho bancos de extracción documental que cubren tablas o
parseo multilingüe, **tres los publica quien vende lo que el banco mide**:

- **ExtractBench** lo publica **LlamaIndex**. Lo encabeza LlamaExtract Agentic Plus
  con **95,6 de value F1** y la mejor relación coste-exactitud del banco. Entre sus
  cinco autores está **Simon Suo, cofundador y CTO de LlamaIndex**.
- **PulseBench-Tab** lo publica **Pulse AI**, que vende extracción documental.
- **MORE** lo publican **nueve autores de Tencent**, la compañía que desarrolla
  HunyuanOCR — el sistema que sale primero en su tabla de español, con 97,25.

OmniDocBench, DocVQA y MDPBench son académicos, y Dr. DocBench es un consorcio de once
instituciones.

**El octavo es de otra clase, y es peor.** Los tres de arriba tienen un conflicto de
interés —eligen el corpus y su producto gana— pero **el banco existe**: cualquiera
puede recorrerlo, rehacer las cuentas y discutirlas. **XDocParse no está publicado.** Se
describe, se puntúa contra él y el modelo de sus autores lo encabeza por +7,4 puntos.
Eso no es un conflicto de interés: es una **afirmación que no se puede falsar**.

Verificado el 25 de agosto de 2026; el criterio de búsqueda y los seis con su reparto
por idioma están en §1.2 del [manual](../MANUAL.md).

## Y ninguno de los dos que ordenan publica un intervalo

**Comprobado el 27 de agosto de 2026**, porque se iba a afirmar en la cabecera de la
tabla de L5 y aquí una afirmación sin lo que la comprueba al lado no se publica.

**ExtractBench**, contra su propio repositorio
([`run-llama/ExtractBench`](https://github.com/run-llama/ExtractBench)):

```bash
head -1 leaderboard.csv | tr ',' '\n' | grep -icE "ci|conf|interval|std|error"   # -> 0 de 27 columnas
grep -icE "confidence interval|error bar|variance|bootstrap" README.md            # -> 0
```

**PulseBench-Tab** (arXiv 2606.07534): sólo estimaciones puntuales. Ni intervalos, ni
barras de error, ni desviaciones, en ningún punto del artículo. Una fila suya es
literalmente:

> `1 | Pulse Ultra 2 | 0.935 | 1.000 | 100.0% | 57.9%`

Y ahí está otra vez el patrón de arriba, ahora con su número: **el producto de Pulse AI
encabezando el banco de Pulse AI.**

**Por qué esto importa para lo que publica este repo.** Los dos ordenan —catorce
sistemas y nueve— sin decir si las diferencias significan algo. La tabla de L5 hace lo
contrario: publica los números con su cobertura y sus denominadores y **se niega a
ordenar**, porque ordenar exige una potencia que L5 no ha calculado y L6 sí calculará
(McNemar y bootstrap agrupado por documento, ADR-0009). Es la diferencia entre un banco
y un *leaderboard*, y sale gratis de haber sido honesto.

Este documento **acumula**: crece cada vez que aparece un banco nuevo o cambia quién lo
publica. Por eso vive aparte de [cómo se mide aquí](como-se-mide-aqui.md), que
**sostiene** y lleva tope de líneas. Un documento o acumula o sostiene, y no puede hacer
las dos.
