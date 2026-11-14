# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""Configuracion de pytest: marca `live` y ruta raiz del proyecto."""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def pytest_addoption(parser):
    parser.addoption(
        "--live", action="store_true", default=False,
        help="incluye los tests marcados `live` (llaman de verdad a la NASA)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live: llama de verdad a los servicios de la NASA (requiere red)"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live"):
        return
    skip = pytest.mark.skip(reason="test live: usa --live para ejecutarlo")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    """Cada test usa su propia cache: no ensucia data/cache ni depende de ella."""
    monkeypatch.setenv("DATA_CACHE_DIR", str(tmp_path / "cache"))
    yield
