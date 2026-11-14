# SI-assisted: Antigravity 1 (Claude Opus 5.5 / Gemini 3.8 Flash)
"""Conectores ETL de datos NASA (contrato v2 §3 y §6).

Punto de entrada publico: `src.etl.registry`.
"""

from .errors import DataUnavailable
from .registry import (
    get_grid,
    get_series,
    parse_giovanni_csv,
    load_catalog,
    list_variables,
)

__all__ = [
    "DataUnavailable",
    "get_series",
    "get_grid",
    "parse_giovanni_csv",
    "load_catalog",
    "list_variables",
]
