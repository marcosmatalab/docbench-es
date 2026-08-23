# ADR-0034 · Los resultados se publican también por BANDA DE LONGITUD, y las bandas se definen ahora

**Fecha:** 2026-08-23 · **Estado:** aceptada en L3, **se implementa en L5**.
Amplía §12: la tabla de resultados gana un corte que no depende de la entidad

## Contexto

ADR-0032 dejó escrito que **la suite de conformidad no puede exigir un conjunto
fijo de estratos**, porque `celdas-combinadas`, `multipagina` y `sin-tabla` exigen
ver tablas, y ver tablas exige un extractor que el núcleo no puede importar.

**La consecuencia que no se sacó allí, y que condiciona L5:** un adaptador de
carpeta de PDFs sólo puede calcular los ejes que **no** necesitan extracción — si
hay capa de texto, cuántas páginas, cuánto ocupa. Así que **el día que alguien
apunte `docbench` a SU carpeta, sólo se le puede clasificar por esos ejes.**

Y si la tabla de resultados de L5 se publica **únicamente por estrato**, ese
alguien **no tiene nada que consultar**: sus documentos no están clasificados en
los estratos que la tabla usa, y la herramienta se queda en banco de pruebas.

Hay precedente de fuera: la tabla de cabecera de **ExtractBench** parte por
**Overall / Short / Medium / Long**. Parten por longitud porque es el eje que se
puede calcular **sin verdad de referencia y sin extractor**, o sea el único que
sobrevive en la carpeta de un desconocido.

## Decisión

**Además de por estrato, los resultados se publican por banda de longitud.** Las
bandas se definen **aquí y ahora**, no cuando toque:

| Banda | Páginas | % del BOE (n=600) |
|---|---|---|
| **corto** | 1 – 4 | 37,0% |
| **medio** | 5 – 12 | 47,8% |
| **largo** | 13 o más | 15,2% |

**Por qué en páginas absolutas y no en terciles del corpus.** Un tercil es una
propiedad del BOE; «1 a 4 páginas» significa lo mismo en la carpeta de cualquiera.
El eje existe precisamente para ser portable, así que definirlo por cuantiles de
nuestro corpus lo haría inútil para el caso que lo justifica.

**Por qué estos cortes.** Sobre las tres ventanas del sondeo (n=600): el corte en
4 es el percentil 33 y el corte en 13 está cerca del 87. Reparten
37 / 48 / 15, y en un corpus de 1.000 dejan **~370 / ~478 / ~152** documentos, o
sea n suficiente en las tres para publicar con intervalo.

**Y la banda no es un sustituto pobre del estrato: lleva señal medida.**

| Estrato | Mediana de páginas | % en banda larga |
|---|---|---|
| `sin-tabla` | 5 | **6,2%** |
| `tabla-simple` | 7 | 28,9% |
| `celdas-combinadas` | 9 | 32,3% |
| `anexo-png` | 13 | **54,5%** |

La longitud **correlaciona con la dificultad** sin necesitar extractor. No la
sustituye —un documento corto con celdas combinadas sigue siendo difícil— pero
ordena, y ordenar sin verdad de referencia es exactamente lo que hace falta para
recomendar sobre una carpeta ajena.

**La longitud sale del sumario gratis**: la API entrega `pagina_inicial` y
`pagina_final` en `url_pdf`, así que no hay que abrir un PDF para calcularla. En
una carpeta ajena sale del propio PDF, que es una lectura de metadatos.

## Alternativas descartadas

**Publicar sólo por estrato.** Es lo que dice §12 hoy y es lo que deja la
herramienta sin respuesta para un desconocido. El coste de añadir la banda ahora
es una columna; el de añadirla después es re-publicar todas las campañas.

**Definir las bandas en L5, con el corpus delante.** Tentador y equivocado: en L5
habría resultados, y elegir los cortes viendo los resultados es elegir los cortes
que favorecen la conclusión. Es el mismo argumento por el que §16 congela el plan
de muestreo **antes** de medir. Por eso se definen aquí, con el sondeo, y no allí.

**Partir por tamaño en bytes en vez de por páginas.** Descartada: el tamaño
depende de la compresión y de si hay imágenes, así que dos documentos igual de
largos pueden diferir en un orden de magnitud. Las páginas son lo que el lector
entiende y lo que el extractor paga.

## Trade-off

Lo que se paga: **la tabla de resultados dobla de ancho**, y cada cifra por banda
lleva su intervalo, así que hay tres veces más números que sostener. Y las bandas
son un corte **arbitrario en el margen**: un documento de 12 páginas y otro de 13
caen en bandas distintas.

Lo que se compra: que el proyecto pueda responder *«para tus documentos, usa
esto»* a alguien que no tiene verdad de referencia, que es la diferencia entre un
banco de pruebas y una herramienta.
