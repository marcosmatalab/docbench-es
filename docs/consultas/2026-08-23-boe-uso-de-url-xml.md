# Consulta al BOE · uso de `url_xml` a través de la API de datos abiertos

**Estado:** redactada el 2026-08-23, **pendiente de enviar**. No bloquea nada
(ADR-0031). Cuando haya respuesta, **su respuesta vale más que el ADR** y se
transcribe aquí con su fecha.

**Cauce:** el de datos abiertos del BOE, desde <https://www.boe.es/datosabiertos/>.

---

**Asunto:** Consulta sobre el uso previsto del campo `url_xml` de la API de sumarios

Buenos días:

Estoy construyendo un banco de pruebas abierto para comparar herramientas de
extracción de tablas en documentos administrativos en español. El proyecto es
público y sin ánimo de lucro:
<https://github.com/marcosmatalab/docbench-es>.

Uso la API de sumarios del BOE documentada en `APIsumarioBOE.pdf`. Para cada
documento, la API entrega los campos `url_pdf`, `url_html` y `url_xml`, y necesito
la versión XML porque es la que permite derivar automáticamente la estructura de
las tablas sin anotarlas a mano.

Al preparar la descarga he encontrado una duda que prefiero resolver antes de
hacer ninguna cosecha:

- La documentación oficial de la API especifica `url_xml` como campo obligatorio,
  con el ejemplo `https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-10761`.
- El `robots.txt` de `www.boe.es` incluye la directiva
  `Disallow: /diario_boe/xml.php?`, junto a otras que parecen dirigidas a evitar
  la indexación de representaciones alternativas del mismo documento
  (`txt.php?*lang=ca`, `*lang=gl`, etc.).

Mi lectura es que el `robots.txt` es una directiva de indexación para buscadores y
no una restricción de reutilización, y que el uso previsto de `url_xml` es
precisamente el que hace un cliente de la API. **Pero prefiero preguntarlo que
suponerlo.**

Si es así, mi intención es descargar con estas condiciones:

- descubrimiento **únicamente** a través de la API de sumarios, sin recorrer el
  sitio ni construir identificadores;
- **una petición por segundo**, sin paralelismo;
- `User-Agent` identificando el proyecto y su repositorio;
- caché: ningún documento se descarga dos veces;
- atribución en todo lo que se publique, con la fórmula de obra derivada que
  indican las condiciones de reutilización: «Basado en datos de la Agencia Estatal
  Boletín Oficial del Estado», con la fecha de última actualización.

¿Es ése el uso previsto? Y si prefieren otro ritmo, otra ventana horaria u otra
vía de acceso al XML, la adopto sin problema.

Muchas gracias por el trabajo de publicar el BOE en abierto: sin el XML este
proyecto no sería posible.

Un saludo,

Marcos Mata García
<https://github.com/marcosmatalab/docbench-es>

---

## Qué se hace con la respuesta

| Si contestan | Qué se hace |
|---|---|
| Que sí, es el uso previsto | Se transcribe aquí con su fecha y **sustituye al argumento de ADR-0031** |
| Que prefieren otro ritmo o ventana | Se cambia `entities/boe.yaml` y se dice en `RESULTS.md` |
| Que no | **Se para la cosecha** y se reabre la decisión de ADR-0031 con la alternativa `url_html` |
| No contestan | ADR-0031 sigue en pie, y esta consulta queda como evidencia de que se preguntó |
