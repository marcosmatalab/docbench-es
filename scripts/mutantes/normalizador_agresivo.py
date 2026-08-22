"""La normalizacion que el manual prohibe: quita acentos, pliega mayusculas y
repara el separador decimal anglosajon. Es la trampa silenciosa a favor de un
extractor de la regla de oro 7."""

import unicodedata

import docbench_es.core.canonical as canonical

_original = canonical.normalize_cell_text


def _agresivo(s: str) -> str:
    limpio = _original(s)
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", limpio) if unicodedata.category(c) != "Mn"
    )
    return sin_acentos.lower().replace(",", "").replace(".", ",")


def pytest_configure(config: object) -> None:
    canonical.normalize_cell_text = _agresivo
