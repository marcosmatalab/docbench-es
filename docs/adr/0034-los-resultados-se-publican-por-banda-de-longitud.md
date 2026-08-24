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

## El dominio de validez, que hay que declarar antes de que alguien consulte

**Estas bandas están calibradas sobre documentos tipo BOE, con mediana de 6
páginas.** No son universales, y compararlas con las de fuera lo deja claro.
ExtractBench parte por **≤10 / 11–50 / >50**. Medido sobre las tres ventanas del
sondeo (n=600):

| Banda de ExtractBench | Qué proporción del BOE cae ahí |
|---|---|
| **corto (≤10)** | **80,2%** |
| medio (11–50) | 17,7% |
| largo (>50) | 2,2% |

**Cuatro de cada cinco documentos del BOE son «cortos» para ellos**, y el p90 del
BOE son 15 páginas. O sea que **mis tres bandas viven casi enteras dentro de su
primera**: la escala no es la misma porque la población no es la misma.

**La consecuencia, que es sobre lo único que hace usable la herramienta:** si
alguien apunta `docbench` a una carpeta de documentos empresariales —contratos,
pólizas, expedientes—, **el 100% le cae en la banda `largo`**, que es la que menos
documentos tiene aquí (15,2%) y cuyo extremo superior no está medido. Devolverle
una recomendación sería **extrapolar muy fuera del rango medido y presentarlo con
cara de medición**.

**Por eso `route` avisa, no extrapola.** Es la misma regla de declarar la
precondición que se aplicó a `teds()` —que asume tablas válidas y no lo comprueba—
sólo que aquí la precondición es del corpus del usuario, no de un argumento:

- `route` compara la distribución de páginas de la carpeta del usuario con el
  rango medido de la banda que le tocaría;
- si la mediana del usuario cae fuera, **lo dice y no recomienda como si midiera**;
- y el aviso lleva el número: *«tus documentos tienen mediana N páginas; esta banda
  se calibró sobre documentos de mediana 6»*.

**Requisito para L17**, que es donde vive `route.recommend` —el hito que emite
`routing.yaml` ejecutable, §16—. Sin esto, la herramienta da su respuesta más
segura justo donde menos sabe.

> **Corrección de hito, 23 ago 2026, el mismo día.** Este párrafo decía «L15».
> L15 es `sources` de plataforma; `route.recommend` es **L17**. El requisito no
> cambia y sigue siendo de **quien consulte la tabla por banda**: sólo cambia a
> qué hito se le exige. Se anota en vez de sobrescribirse porque un requisito
> colgado del hito equivocado es un requisito que nadie recoge.

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
