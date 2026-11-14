# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Catálogo de variables (§8).

Fuente: `data/catalog/variables.json` (Hermes 1). Mientras ese archivo no exista,
se usa la semilla `data/catalog/variables.seed.json`, cuyos ids son los mismos
que comparten todos los agentes. La API **no inventa** tarjetas: solo normaliza
la forma de la semilla y marca de dónde salió.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from .config import CATALOG_DIR
from .errors import ApiError

CATALOG_PATH = CATALOG_DIR / "variables.json"
SEED_PATH = CATALOG_DIR / "variables.seed.json"


def _read_json(path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _bilingual(text: str) -> dict[str, str]:
    return {"es": text, "en": text}


def _from_seed_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Convierte una entrada de la semilla en tarjeta §8 con lo que se sabe.

    Los campos que la semilla no trae (definiciones largas, DOI) quedan en
    `null`/vacío: preferimos una tarjeta incompleta y honesta a una inventada.
    """
    longname = entry.get("power_longname") or entry["id"]
    return {
        "id": entry["id"],
        "connector": entry.get("connector"),
        "connector_param": entry.get("connector_param"),
        "names": _bilingual(longname),
        "simple_definition": _bilingual(longname),
        "unit": entry.get("unit", ""),
        "ratio_scale": bool(entry.get("ratio_scale", False)),
        "sphere": entry.get("sphere"),
        "source": {
            "model_or_mission": entry.get("challenge_named_source"),
            "instrument": None,
            "via": "NASA POWER" if entry.get("connector") == "power" else entry.get("connector"),
            "challenge_named_source": entry.get("challenge_named_source"),
            "native_resolution": "0.5° x 0.625°" if entry.get("connector") == "power" else None,
            "start": entry.get("start"),
            "homogeneous_since": entry.get("homogeneous_since"),
            "doi": None,
            "url": None,
        },
        "what_up_means": {},
        "what_down_means": {},
        "typical_drivers": {},
        "caveats": {},
        "keywords": {},
        "verified": {
            "by": "seed",
            "at": None,
            "evidence_url": None,
        },
        "_catalog_source": "seed",
    }


@lru_cache(maxsize=1)
def _load() -> tuple[list[dict[str, Any]], str, str]:
    """Devuelve (tarjetas, nombre de fuente, fecha de lectura ISO)."""
    full = _read_json(CATALOG_PATH)
    if full and isinstance(full.get("variables"), list):
        cards = [dict(v, _catalog_source="catalog") for v in full["variables"]]
        return cards, "catalog", datetime.now(timezone.utc).isoformat(timespec="seconds")

    seed = _read_json(SEED_PATH)
    if seed is None:
        raise ApiError(
            "DATA_UNAVAILABLE",
            message={"es": "No hay catálogo de variables.", "en": "No variable catalog is available."},
            hint="data/catalog/variables.json or variables.seed.json is missing.",
        )
    cards = [_from_seed_entry(e) for e in seed.get("live", [])]
    cards += [_from_seed_entry(e) for e in seed.get("planned_giovanni", [])]
    return cards, "seed", datetime.now(timezone.utc).isoformat(timespec="seconds")


def all_variables() -> list[dict[str, Any]]:
    return _load()[0]


def catalog_meta() -> dict[str, Any]:
    _cards, source, loaded_at = _load()
    return {
        "source": source,
        "loaded_at": loaded_at,
        "is_complete": source == "catalog",
        "n_variables": len(_cards),
    }


def variable_ids() -> set[str]:
    return {c["id"] for c in all_variables()}


def get_variable(variable_id: str) -> dict[str, Any]:
    for card in all_variables():
        if card["id"] == variable_id:
            return card
    raise ApiError(
        "VARIABLE_UNKNOWN",
        message={
            "es": f"La variable '{variable_id}' no está en el catálogo.",
            "en": f"The variable '{variable_id}' is not in the catalog.",
        },
        hint="GET /api/catalog/variables",
    )


def has_connector(card: dict[str, Any], connector: str) -> bool:
    return (card.get("connector") or "") == connector


def reload() -> None:
    _load.cache_clear()
