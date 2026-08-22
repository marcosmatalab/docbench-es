"""Los cinco conversores devuelven lista vacia."""

import docbench_es.core.canonical as canonical


def pytest_configure(config: object) -> None:
    for nombre in ("from_html", "from_markdown", "from_tei", "from_text_heuristic"):
        setattr(canonical, nombre, lambda *a, **k: [])
    canonical.from_dataframe = lambda *a, **k: []
