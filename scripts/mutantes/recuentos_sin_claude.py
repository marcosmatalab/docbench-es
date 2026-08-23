"""La comprobación de recuentos deja de mirar `.claude/`.

Ahí estaba el tercer «12» del cierre de L2, y ahí vive el guion que la siguiente
sesión ejecuta. Un recorrido que se quedara en los `*.md` de la raíz seguiría
pasando en verde sobre menos ficheros de los que dice cubrir.
"""


def pytest_collection_modifyitems(session: object, config: object, items: object) -> None:
    import test_recuentos

    original = test_recuentos._documentos
    test_recuentos._documentos = lambda: [d for d in original() if ".claude" not in str(d)]
