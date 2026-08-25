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

Este documento **acumula**: crece cada vez que aparece un banco nuevo o cambia quién lo
publica. Por eso vive aparte de [cómo se mide aquí](como-se-mide-aqui.md), que
**sostiene** y lleva tope de líneas. Un documento o acumula o sostiene, y no puede hacer
las dos.
