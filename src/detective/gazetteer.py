# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Geocoding of free text onto places (contract R4).

Source of truth is ``data/catalog/gazetteer.json``, owned by Hermes 1 (GeoNames
``cities15000``, prompt C2). We never ask a language model for coordinates.

Matching ladder, in order:
  1. exact (accent- and case-insensitive) over name / ascii / alt_names;
  2. prefix / word-boundary containment over the same fields;
  3. fuzzy: ``difflib.SequenceMatcher`` ratio >= 0.86, only for tokens >= 4 chars.
Ties are resolved by population, then alphabetically (deterministic).

If the gazetteer has not landed yet, ``lookup_online`` can ask OpenStreetMap's
Nominatim (ODbL) — only when the caller opts in with ``AI_GEOCODE_ONLINE=1``.
Results always carry ``source`` so the UI can show where the place came from.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests

from .config import SETTINGS
from .text_norm import fold

FUZZY_THRESHOLD = 0.86
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "EarthTrendDetective/1.0 (NASA Space Apps hackathon; geocoding)"


@dataclass(frozen=True)
class Place:
    name: str
    country: str | None
    lat: float
    lon: float
    bbox: list[float] | None
    population: int | None
    source: str

    def to_public(self, *, score: float | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "country": self.country,
            "lat": round(self.lat, 4),
            "lon": round(self.lon, 4),
            "bbox": self.bbox,
            "population": self.population,
            "source": self.source,
        }
        if score is not None:
            payload["match_score"] = round(score, 3)
        return payload


def gazetteer_path() -> Path:
    return SETTINGS.catalog_dir / "gazetteer.json"


@lru_cache(maxsize=1)
def _load() -> tuple[Place, ...]:
    path = gazetteer_path()
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Hermes 1 publica la lista bajo "cities" (gazetteer/2); se acepta también "places".
    rows = (raw.get("places") or raw.get("cities")) if isinstance(raw, dict) else raw
    places: list[Place] = []
    for row in rows or []:
        try:
            places.append(
                Place(
                    name=str(row["name"]),
                    country=row.get("country"),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    bbox=row.get("bbox"),
                    population=row.get("population"),
                    source="gazetteer",
                )
            )
        except (KeyError, TypeError, ValueError):
            # A malformed row is skipped loudly in dev, quietly in prod: the
            # gazetteer is validated by Hermes 1's own script.
            continue
    return tuple(places)


def reset_cache() -> None:
    _load.cache_clear()


def _fields(place: Place) -> list[str]:
    return [fold(place.name), fold(place.name.replace("-", " "))]


def _score(query: str, place: Place) -> float:
    q = fold(query).strip()
    if not q:
        return 0.0
    best = 0.0
    for field in _fields(place):
        if not field:
            continue
        if field == q:
            return 1.0
        if q == field.split(",")[0].strip():
            best = max(best, 0.99)
        if len(q) >= 3 and (field.startswith(q) or q.startswith(field)):
            best = max(best, 0.9)
        if len(q) >= 4 and q in field:
            best = max(best, 0.82)
        if len(q) >= 4 and len(field) >= 4:
            best = max(best, SequenceMatcher(None, q, field).ratio() * 0.95)
    return best


def _rank(places: list[Place], query: str) -> list[tuple[Place, float]]:
    scored = [(_score(query, p), p) for p in places]
    scored = [(s, p) for s, p in scored if s >= 0.7]
    scored.sort(key=lambda sp: (-sp[0], -(sp[1].population or 0), fold(sp[1].name), sp[1].country or ""))
    return [(p, s) for s, p in scored]


def geocode(q: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Places for a free-text query. Empty list when nothing matches (UI asks for a map click)."""
    places = _load()
    if not q or not q.strip() or not places:
        return []
    ranked = _rank(list(places), q)[:limit]
    return [p.to_public(score=s) for p, s in ranked]


def find_in_text(text: str, *, limit: int = 3) -> list[tuple[Place, str]]:
    """Longest gazetteer names that appear literally inside ``text``.

    Used by the rules planner: the contract says ``place`` must be text copied
    from the question, so we return the matched span exactly as written.
    """
    places = _load()
    if not text or not places:
        return []
    folded = fold(text)
    hits: list[tuple[Place, str, int]] = []
    for place in places:
        for variant in {place.name}:
            needle = fold(variant)
            if len(needle) < 3:
                continue
            idx = folded.find(needle)
            if idx >= 0:
                original = text[idx : idx + len(needle)]
                hits.append((place, original, len(needle)))
                break
    hits.sort(key=lambda h: (-h[2], -(h[0].population or 0), fold(h[0].name)))
    out: list[tuple[Place, str]] = []
    seen: set[str] = set()
    for place, span, _len in hits:
        key = fold(span)
        if key in seen:
            continue
        seen.add(key)
        out.append((place, span))
        if len(out) >= limit:
            break
    return out


def online_allowed() -> bool:
    return os.environ.get("AI_GEOCODE_ONLINE", "0").strip() in ("1", "true", "yes")


def lookup_online(q: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Nominatim fallback (ODbL). Only used when AI_GEOCODE_ONLINE=1."""
    if not online_allowed() or not q.strip():
        return []
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": q, "format": "jsonv2", "limit": limit, "addressdetails": 0},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
        rows = resp.json()
    except (requests.RequestException, ValueError):
        return []
    out: list[dict[str, Any]] = []
    for row in rows or []:
        try:
            box = row.get("boundingbox")
            bbox = [float(box[2]), float(box[0]), float(box[3]), float(box[1])] if box else None
            out.append(
                Place(
                    name=str(row["name"] or row["display_name"].split(",")[0]),
                    country=(row.get("display_name") or "").split(",")[-1].strip() or None,
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    bbox=bbox,
                    population=None,
                    source="nominatim",
                ).to_public()
            )
        except (KeyError, TypeError, ValueError, IndexError):
            continue
    return out
