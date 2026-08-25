# ADR-0042 · L7 antes que L6: se prioriza la demostrabilidad sobre el plan de muestreo

**Fecha:** 2026-08-25 · **Estado:** aceptada. **Contradice el orden de §16** y por eso
se transcribe al manual en este mismo commit

## Contexto

§16 ordena `L5 → L6 → L7`:

| Hito | Contenido | Horas |
|---|---|---|
| **L6** | `sample` con McNemar + bootstrap agrupado | 8-10 |
| **L7** | Quickstart: 20 documentos versionados + `make quickstart` | 6-8 |

**Para la validez de una campaña seria, L6 va antes**: sin plan de muestreo congelado,
la primera campaña no tiene potencia declarada ni efecto mínimo detectable.

**Para el artefacto, L7 vale mucho más**, y la diferencia es de clase: L6 hace que un
número futuro sea defendible; **L7 es la diferencia entre que alguien lea que mides y
que lo vea medir en su máquina en tres minutos.** Hoy el repo tiene instrumento,
verdad de referencia, métricas, arnés y 82 límites declarados, y **cero mediciones de
lo que promete medir**. Quien lo abra treinta segundos ve un andamio.

## Decisión

**Se intercambian: `L5 → L7 → L6`.**

**Y el intercambio es gratis, comprobado contra §16 antes de aceptarlo:** el criterio
de L7 —*«de clone a tabla en menos de 3 minutos, sin red y sin gastar»*— depende de
**L5**, que le da los ocho extractores, y **no depende de L6 en nada**. L6 no produce
nada que L7 consuma.

**Lo que se prioriza, dicho con todas las letras: la demostrabilidad sobre el plan de
muestreo.** Y lo que eso cuesta va escrito abajo.

## Qué NO cambia, y es la mitad de la decisión

**L6 entra antes de la primera campaña seria**, que es cuando su ausencia costaría
algo. Adelantar L7 **no** autoriza a publicar una comparación entre extractores sin
plan de muestreo: eso sigue prohibido por §16 y por el límite 10, que ya declara que
la primera campaña es de precisión y no de contraste.

**El riesgo real del intercambio, y por eso se escribe:** que un quickstart que
funciona invite a leer sus números como resultados. `make quickstart` corre sobre 20
documentos elegidos para que quepan en tres minutos, no para representar nada. **Su
salida lleva su límite en la cabecera** —igual que el informe en `--offline` lleva el
suyo— y eso es requisito de L7, no una nota.

## Alternativa descartada

**Dejar el orden de §16.** Es lo correcto si lo único que importa es la validez del
primer número serio. Se descarta porque el proyecto está en el punto donde **nadie
puede ver funcionar nada**, y un plan de muestreo perfecto sobre un banco que no
demuestra medir no convence a nadie ni sirve para decidir si merece seguir.

## Trade-off

Lo que se paga: **el plan de muestreo llega 6-8 horas más tarde**, y durante ese
tiempo existe un quickstart cuyos números hay que defender de ser citados como
resultado.

Lo que se compra: que la frase *«esto mide»* pase de ser una promesa a algo que
cualquiera comprueba en su máquina en tres minutos, **antes** de que el proyecto
gaste otras 8-10 horas en algo que sólo se ve por dentro.
