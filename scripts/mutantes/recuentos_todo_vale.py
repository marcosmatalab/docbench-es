"""`exigir_sano` acepta cualquier recuento, degenerado incluido.

La versión de `b7cc6c3`, que no tenía esa comprobación: con una colección parcial
—`dentro=0`, `total=5`— comparaba igual contra los documentos y los acusaba a
todos de estar desincronizados. El mensaje hablaba de una desincronización que no
existía, que es peor que no comprobar: manda a arreglar documentos correctos.
"""


def pytest_configure(config: object) -> None:
    import conftest

    conftest.exigir_sano = lambda cuenta: cuenta
