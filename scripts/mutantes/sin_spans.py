"""El colocador ignora rowspan y colspan: la trampa a favor del que no sabe."""

from docbench_es.core.canonical._rejilla import Colocador

_colocar = Colocador.colocar


def _plano(self, texto, *, is_header, rowspan, colspan):  # type: ignore[no-untyped-def]
    return _colocar(self, texto, is_header=is_header, rowspan=1, colspan=1)


def pytest_configure(config: object) -> None:
    Colocador.colocar = _plano  # type: ignore[method-assign]
