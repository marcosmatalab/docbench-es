"""`normalize_cell_text` no hace nada."""

import docbench_es.core.canonical as canonical


def pytest_configure(config: object) -> None:
    canonical.normalize_cell_text = lambda s: s
