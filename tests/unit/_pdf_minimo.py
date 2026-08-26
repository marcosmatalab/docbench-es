"""Un PDF de verdad, construido a mano, para que los extractores tengan qué morder.

**Por qué a mano y no un fichero versionado.** El corpus de L3 no está en git —son 361 MB,
LIMITS 74— así que un test que necesite un PDF real o se salta en cualquier clon, o lo
fabrica. Fabricarlo cuesta 800 bytes de sintaxis PDF y hace que la conducta de `extract()`
se compruebe **en cualquier máquina que tenga la biblioteca**, sin corpus.

**Y no es un fixture congelado.** Sale determinista de este código, así que no hay verdad
de referencia que se pueda tocar para que salgan los números: si un test falla contra él,
el fallo está en el código o está aquí, y las dos cosas se leen.

Lo que NO es: una muestra representativa. Un PDF de una página con una tabla de 2x2 sirve
para «¿devuelve lo que dice devolver?», no para puntuar a nadie. La puntuación sale del
corpus, y sus tests viven en `tests/contract`.
"""

from __future__ import annotations

CAJA = (200, 100)
"""La página, en puntos. Pequeña a propósito: lo que se mira es la forma, no el contenido."""


def _ensamblar(flujo: bytes) -> bytes:
    """Los cinco objetos de un PDF mínimo, con su `xref` y sus desplazamientos reales.

    El `xref` se calcula, no se aproxima: `pdfminer` sabe reconstruirlo si está mal, y
    entonces este molde estaría comprobando el modo de recuperación en vez del normal.
    """
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>" % CAJA,
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(flujo), flujo),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = bytearray(b"%PDF-1.4\n")
    desplazamientos: list[int] = []
    for i, cuerpo in enumerate(objetos, start=1):
        desplazamientos.append(len(salida))
        salida += b"%d 0 obj\n" % i + cuerpo + b"\nendobj\n"
    inicio = len(salida)
    salida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for d in desplazamientos:
        salida += b"%010d 00000 n \n" % d
    salida += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        inicio,
    )
    return bytes(salida)


def solo_texto(texto: bytes = b"HOLA MUNDO") -> bytes:
    """Una página con texto y **sin una sola línea**: ninguna tabla que detectar."""
    return _ensamblar(b"BT /F1 12 Tf 20 60 Td (%s) Tj ET" % texto)


def con_tabla(celdas: tuple[bytes, bytes, bytes, bytes] = (b"A", b"B", b"C", b"D")) -> bytes:
    """Una página con una rejilla de 2x2 dibujada con líneas, que es como se detecta.

    `pdfplumber` no adivina tablas del texto: busca **rayas**. Sin las seis de aquí,
    `extract_tables()` devuelve la lista vacía y este molde no probaría nada.
    """
    lineas = [b"20 %d m 180 %d l S" % (y, y) for y in (20, 50, 80)]
    lineas += [b"%d 20 m %d 80 l S" % (x, x) for x in (20, 100, 180)]
    sitios = ((25, 60), (105, 60), (25, 30), (105, 30))
    textos = [
        b"BT /F1 8 Tf %d %d Td (%s) Tj ET" % (x, y, t)
        for (x, y), t in zip(sitios, celdas, strict=True)
    ]
    return _ensamblar(b"0.7 w\n" + b"\n".join(lineas + textos))


def roto() -> bytes:
    """Bytes que dicen ser un PDF y no lo son. Es lo que come el aro hostil."""
    return b"%PDF-1.4\nesto no es un PDF\n%%EOF"
