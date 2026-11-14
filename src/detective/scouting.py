# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Place scouting (contract R5).

    lat/lon ─► monthly climatology (via src/etl) ─► Köppen-Geiger rules
            ─► gazetteer facts (big city within 50 km, polar/coastal)
            ─► retrieve over biome profiles and articles ─► 3 candidate variables,
               each with WHY (a sentence taken from the cited source) and its link.

The model never describes the place. The only prose here is either (a) quoted
from a retrieved document, or (b) a deterministic rendering of numbers the ETL
returned. If the ETL is not ready (Antigravity 1's lane), we say so explicitly
and still return the documentary candidates.
"""

from __future__ import annotations

import json
import math
from typing import Any, Callable

from .config import SETTINGS
from .gazetteer import _load as _gazetteer_places
from .koppen import InsufficientClimatology, from_monthly_series
from .rag import retrieve

# Variables the climatology needs. Both are live POWER parameters (seed + fixture).
TEMP_VAR = "T2M"
PRECIP_VAR = "PRECTOTCORR"

BIG_CITY_POPULATION = 1_000_000
BIG_CITY_KM = 50.0
# Regions are published as centre points, not polygons, so "coastal" is approximate.
COASTAL_KM = 60.0


def _etl_get_series() -> Callable[..., dict[str, Any]] | None:
    """The contract's ETL entry point, when Antigravity 1 has landed it."""
    try:
        from src.etl.registry import get_series  # type: ignore

        return get_series
    except Exception:  # ImportError or a half-written module
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def _monthly_mean_by_month(series: dict[str, Any]) -> dict[int, float | None]:
    """Average every calendar month over the record; null stays null."""
    buckets: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    for point in series.get("data") or []:
        value = point.get("value")
        if value is None:
            continue
        try:
            month = int(str(point["date"]).split("-")[1])
        except (KeyError, IndexError, ValueError):
            continue
        if 1 <= month <= 12:
            buckets[month].append(float(value))
    out: dict[int, float | None] = {}
    for month, values in buckets.items():
        out[month] = (sum(values) / len(values)) if values else None
    return out


def _monthly_total_by_month(series: dict[str, Any]) -> dict[int, float | None]:
    """Mean monthly *total* for a rate series given in unit/day (POWER convention).

    POWER PRECTOTCORR is mm/day as a monthly mean, so the monthly total is
    multiplied by the number of days in that month. We use the mean length for a
    leap cycle (365.25/12) and say so in the payload: this is a documented
    approximation of the source semantics, not invented data.
    """
    means = _monthly_mean_by_month(series)
    days = 365.25 / 12.0
    return {m: (v * days if v is not None else None) for m, v in means.items()}


def _gazetteer_facts(lat: float, lon: float) -> dict[str, Any]:
    nearest: list[dict[str, Any]] = []
    places = _gazetteer_places()
    for place in places:
        km = haversine_km(lat, lon, place.lat, place.lon)
        if km <= BIG_CITY_KM:
            nearest.append({"name": place.name, "country": place.country, "km": round(km, 1),
                            "population": place.population})
    nearest.sort(key=lambda c: (-(c["population"] or 0), c["km"]))
    big = [c for c in nearest if (c["population"] or 0) >= BIG_CITY_POPULATION]
    return {
        "big_city_nearby": big[0] if big else None,
        "cities_within_50km": nearest[:3],
        "gazetteer_available": bool(places),
    }


def _coastal_region(lat: float, lon: float) -> dict[str, Any] | None:
    """Nearest region whose biome is `coast`, and how far it is.

    `data/catalog/regions.json` (Hermes 1) has named regions with a centre point,
    not polygons, so this is a documented approximation: a point within
    COASTAL_KM of a coast region's centre inherits the flag. We report the
    distance so the UI can show what the claim rests on.
    """
    path = SETTINGS.catalog_dir / "regions.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rows = payload.get("regions") if isinstance(payload, dict) else payload
    best: dict[str, Any] | None = None
    for row in rows or []:
        if str(row.get("biome") or "") != "coast":
            continue
        try:
            km = haversine_km(lat, lon, float(row["lat"]), float(row["lon"]))
        except (KeyError, TypeError, ValueError):
            continue
        if best is None or km < best["km"]:
            name = row.get("names") or {}
            best = {"region": name.get("en") or name.get("es") or row.get("id"), "km": round(km, 1)}
    return best


def _polar_or_coastal(lat: float, lon: float, *, climate_code: str | None) -> dict[str, Any]:
    """Deterministic flags. Polar comes from latitude; coastal from the regions file."""
    flags: dict[str, Any] = {"polar": abs(lat) >= 66.56, "coastal": None}
    coast = _coastal_region(lat, lon)
    if coast is not None:
        # True only when a coast region's centre is close. False would claim "not
        # coastal", which we cannot know from 11 centre points.
        flags["coastal"] = coast["km"] <= COASTAL_KM or None
        flags["coastal_evidence"] = coast
    if climate_code:
        flags["polar_climate"] = climate_code.startswith("E")
    return flags


def _climate_caveats(
    climate: dict[str, Any], lat: float, lon: float, temp_series: dict[str, Any]
) -> list[dict[str, str]]:
    """Say out loud where the classification may not describe the place.

    Measured on 2026-11-14: POWER's cell for Cusco (-13.53, -71.97) is 3 739.76 m
    high with a warmest month of 9.1 °C, so it classifies ET, while the city at
    ~3 350 m is not tundra. The code is right for the cell; the caveat is what
    keeps the app from presenting it as a fact about the city.
    """
    notes: list[dict[str, str]] = []
    resolution = ((temp_series.get("provenance") or {}).get("native_resolution")) or "0.5° x 0.625°"
    notes.append({
        "code": "CELL_RESOLUTION",
        "es": f"El clima se calcula con la celda de POWER de {resolution}, no con el punto exacto. "
              "En relieve abrupto la celda puede caer en una ladera o cima distinta de la ciudad.",
        "en": f"The climate is computed from POWER's {resolution} cell, not from the exact point. "
              "In steep terrain the cell may sit on a different slope or summit than the city.",
    })
    code = str(climate.get("code") or "")
    if code.startswith("E") and abs(lat) < 60:
        notes.append({
            "code": "POLAR_CODE_AT_LOW_LATITUDE",
            "es": "La celda clasifica como polar; a esta latitud eso suele indicar altitud, "
                  "no un clima polar real. Compruébalo con la elevación de la celda.",
            "en": "The cell classifies as polar; at this latitude that usually means altitude, "
                  "not a true polar climate. Check it against the cell elevation.",
        })
    return notes


def _biome_query(climate: dict[str, Any] | None, flags: dict[str, Any], lang: str) -> str:
    parts: list[str] = []
    if climate and climate.get("code") and climate["code"] != "UNKNOWN":
        parts.append(str(climate["code"]))
        parts.append(str(climate["names"].get(lang)))
        if climate.get("group"):
            parts.append({"A": "tropical", "B": "arid desert steppe", "C": "temperate",
                          "D": "cold continental", "E": "polar ice"}[climate["group"]])
    if flags.get("polar"):
        parts.append("polar" if lang == "en" else "polar")
    if flags.get("coastal"):
        parts.append("coast estuary" if lang == "en" else "costa estuario")
    if flags.get("big_city_nearby"):
        parts.append("big city air quality" if lang == "en" else "gran ciudad aire")
    return " ".join(p for p in parts if p)


def _why_and_source(doc: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """A sentence taken verbatim from the document, plus its link.

    When the document is only a catalogue card (Hermes 1's richer biome profiles
    have not landed yet) the quoted fragment is short; we say so in
    ``why_kind`` instead of padding it with words no source said.
    """
    text = " ".join(str(doc.get("text") or "").split())
    sentences = [s.strip() for s in text.replace("\n", ". ").split(". ") if s.strip()]
    # Prefer a sentence with some substance; fall back to the first fragment.
    sentence = next((s for s in sentences if len(s) >= 40), sentences[0] if sentences else "")
    if sentence and not sentence.endswith((".", "!", "?")):
        sentence += "."
    kind = "quoted_sentence" if len(sentence) >= 40 else "catalog_card_fragment"
    return sentence, {"title": doc.get("title"), "url": doc.get("url"), "type": doc.get("type"), "why_kind": kind}


def scout(lat: float, lon: float, *, lang: str = "es") -> dict[str, Any]:
    """Characterise a point with data and return 3 sourced candidate variables."""
    lang = lang if lang in ("es", "en") else "es"
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return {"error": {"code": "INVALID_COORDINATES", "message": {
            "es": "Latitud y longitud deben ser números.",
            "en": "Latitude and longitude must be numbers."}}, "candidates": []}

    profile: dict[str, Any] = {
        "lat": round(lat_f, 4),
        "lon": round(lon_f, 4),
        "climatology": None,
        "climate": None,
        "flags": {},
        "etl": {"available": False, "reason": None},
    }

    get_series = _etl_get_series()
    if get_series is None:
        profile["etl"]["reason"] = "src/etl/registry.py::get_series not available yet (lane: Antigravity 1)"
    else:
        try:
            temp_series = get_series(TEMP_VAR, lat=lat_f, lon=lon_f)
            precip_series = get_series(PRECIP_VAR, lat=lat_f, lon=lon_f)
            temp_by_month = _monthly_mean_by_month(temp_series)
            precip_by_month = _monthly_total_by_month(precip_series)
            climate = from_monthly_series(temp_by_month, precip_by_month)
            profile["climatology"] = {
                "temp_var": TEMP_VAR, "precip_var": PRECIP_VAR,
                "monthly_temp_c": {m: (round(v, 2) if v is not None else None) for m, v in temp_by_month.items()},
                "monthly_precip_mm": {m: (round(v, 2) if v is not None else None) for m, v in precip_by_month.items()},
                "precip_convention": "monthly total = mean mm/day x 365.25/12 days",
                "provenance": {"temp": temp_series.get("provenance"), "precip": precip_series.get("provenance")},
            }
            profile["climate"] = climate
            profile["climate"]["caveats"] = _climate_caveats(climate, lat_f, lon_f, temp_series)
            profile["etl"]["available"] = True
        except InsufficientClimatology as exc:
            profile["etl"]["reason"] = f"INSUFFICIENT_CLIMATOLOGY: {exc}"
        except Exception as exc:  # DataUnavailable or upstream failure
            code = getattr(exc, "code", type(exc).__name__)
            profile["etl"]["reason"] = f"{code}: {exc}"

    profile["flags"] = _gazetteer_facts(lat_f, lon_f)
    profile["flags"].update(
        _polar_or_coastal(lat_f, lon_f, climate_code=(profile["climate"] or {}).get("code"))
    )

    query = _biome_query(profile["climate"], profile["flags"], lang)
    docs = retrieve(query, lang=lang, k=8) if query else []
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for doc in docs:
        if doc["type"] == "variable_card" and doc.get("variables"):
            vid = doc["variables"][0]
            if vid in seen:
                continue
            seen.add(vid)
            why, source = _why_and_source(doc)
            candidates.append({
                "variable_id": vid,
                "title": doc["title"],
                "why": why,
                "source": source,
                "score": doc["score"],
            })
        if len(candidates) >= 3:
            break

    return {
        "place": profile,
        "candidates": candidates,
        "query_used": query,
        "method": {
            "climate": "Köppen-Geiger by Peel et al. (2007), computed from NASA POWER monthly climatology",
            "candidates": "retrieval over the verified corpus; every 'why' is quoted from its source",
        },
    }
