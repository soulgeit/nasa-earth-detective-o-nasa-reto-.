# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Lectura del catalogo de variables (contrato v2 §8).

Usa `data/catalog/variables.json` (Hermes 1) si existe; mientras no exista,
cae a `data/catalog/variables.seed.json`, que fija los mismos `variable_id`.
"""

from __future__ import annotations

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
CATALOG_PATH = os.path.join(_ROOT, "data", "catalog", "variables.json")
SEED_PATH = os.path.join(_ROOT, "data", "catalog", "variables.seed.json")


def _load(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    if isinstance(doc, list):
        return doc
    cards = doc.get("variables") or doc.get("live") or []
    planned = doc.get("planned_giovanni") or []
    return list(cards) + list(planned)


def catalog_source() -> str:
    return CATALOG_PATH if os.path.exists(CATALOG_PATH) else SEED_PATH


def variables() -> list[dict]:
    return _load(catalog_source())


def get_variable(variable_id: str) -> dict:
    for card in variables():
        if card.get("id") == variable_id:
            return card
    from .errors import DataUnavailable

    raise DataUnavailable("VARIABLE_UNKNOWN", f"variable_id {variable_id!r} no esta en el catalogo")
