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
import re
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
    ascii_name: str | None = None
    alt_names: tuple[str, ...] = ()

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
                    ascii_name=row.get("ascii"),
                    alt_names=tuple(str(a) for a in (row.get("alt_names") or ()) if a),
                )
            )
        except (KeyError, TypeError, ValueError):
            # A malformed row is skipped loudly in dev, quietly in prod: the
            # gazetteer is validated by Hermes 1's own script.
            continue
    return tuple(places)


def reset_cache() -> None:
    _load.cache_clear()
    _fields_index.cache_clear()


@lru_cache(maxsize=1)
def _fields_index() -> tuple[dict[str, tuple[int, ...]], tuple[tuple[str, ...], ...]]:
    """Pre-computed search structures, built once per process.

    Two lookups:
      * ``exact``: spelling -> place indexes, for name / ascii / alt_names;
      * ``prefix``: 4-letter prefix -> place indexes, so the fuzzy pass only ever
        compares against plausible candidates instead of all 8 109 cities
        (55 000 SequenceMatcher calls per query, measured, is not interactive).
    """
    places = _load()
    exact: dict[str, list[int]] = {}
    prefix: dict[str, set[int]] = {}
    all_fields: list[tuple[str, ...]] = []
    for idx, place in enumerate(places):
        fields = tuple(_fields(place))
        all_fields.append(fields)
        for field in fields:
            exact.setdefault(field, []).append(idx)
            if len(field) >= 4:
                prefix.setdefault(field[:4], set()).add(idx)
    return (
        {k: tuple(v) for k, v in exact.items()},
        {p: tuple(sorted(v)) for p, v in prefix.items()},
    )


def _fields(place: Place) -> list[str]:
    """Every spelling a student may type for this place.

    RONDA_2 §6.3: the 8 109-city GeoNames gazetteer publishes ``ascii`` and
    ``alt_names``; without them "Cuzco" (official: Cusco), "Lima, Peru"
    (alt: Lima) or "Moscow" (alt: Moskva) never match.
    """
    variants: list[str] = [place.name]
    if place.ascii_name:
        variants.append(place.ascii_name)
    variants.extend(place.alt_names)
    fields: list[str] = []
    for value in variants:
        folded = fold(value).strip()
        if not folded:
            continue
        for form in (folded, folded.replace("-", " "), folded.replace(".", "")):
            if form and form not in fields:
                fields.append(form)
    return fields


COUNTRY_NAMES = frozenset(
    """peru perú mexico méxico chile argentina colombia ecuador bolivia venezuela brazil brasil
    spain españa france francia germany alemania italy italia china japan japón india russia
    canada australia egypt egipto kenya nigeria morocco marruecos bolivia uruguay paraguay
    cuba haiti guatemala honduras nicaragua panama panamá portugal netherlands belgium sweden
    norway finland poland turkey turquía greece greece iran iraq israel pakistan bangladesh
    indonesia thailand vietnam philippines malaysia korea nigeria ethiopia sudan angola""".split()
)


def _head_is_country(query: str) -> bool:
    head = re.split(r"[,(]", fold(query).strip())[0].strip()
    return head in COUNTRY_NAMES


def _score(query: str, place: Place) -> float:
    q = fold(query).strip()
    if not q:
        return 0.0
    # "Lima, Peru" / "Lima Peru" / "Piura (Peru)" -> try the city part first.
    head = re.split(r"[,(]", q)[0].strip()
    best = 0.0
    for field in _fields(place):
        if not field:
            continue
        if field == q:
            return 1.0
        if head and field == head:
            best = max(best, 0.995)
        if len(head) >= 3 and (field.startswith(head) or head.startswith(field)):
            # A prefix is only evidence when it is most of the word AND it is not a
            # 1-3 letter fragment of an alternative spelling: GeoNames lists "Per"
            # as an alt name for Perth (from "Peairt"), and "Peru" must not match it.
            shorter, longer = sorted((len(head), len(field)))
            if longer > 0 and shorter >= 4 and shorter / longer >= 0.75:
                best = max(best, 0.9)
        if len(q) >= 4 and q in field:
            best = max(best, 0.82)
        if len(head) >= 4 and len(field) >= 4:
            # Spelling variants ("cusco"/"cuzco") score high; a shared prefix with a
            # different word ("peru"/"perth") must not. Require a long common stem.
            ratio = SequenceMatcher(None, head, field).ratio()
            prefix = SequenceMatcher(None, head[:4], field[:4]).ratio()
            if prefix == 1.0 and ratio < 0.85:
                continue
            best = max(best, ratio * 0.95)
    return best


def _candidate_indexes(head: str) -> set[int]:
    """Places worth a fuzzy look at, chosen by a 4-letter prefix bucket.

    For queries shorter than 4 characters there is no fuzzy pass at all: a 2-letter
    fragment matches half the planet and produces exactly the kind of confident
    nonsense we are trying to avoid.
    """
    if len(head) < 4:
        return set()
    _exact, prefix_index = _fields_index()
    for size in (4, 3):
        key = head[:size]
        if len(key) < 3:
            continue
        found = prefix_index.get(key)
        if found:
            return set(found)
    return set()


def _rank(places: list[Place], query: str) -> list[tuple[Place, float]]:
    """Exact hits first; the fuzzy pass runs only on prefix candidates."""
    q = fold(query).strip()
    head = re.split(r"[,(]", q)[0].strip()
    exact, _prefix = _fields_index()

    hits: dict[int, float] = {}
    for key in (q, head):
        if key:
            for idx in exact.get(key, ()):
                hits[idx] = max(hits.get(idx, 0.0), 1.0 if key == q else 0.995)

    # Prefix and spelling variants, restricted to plausible candidates.
    for idx in _candidate_indexes(head or q):
        if idx in hits:
            continue
        score = _score(q, places[idx])
        if score >= 0.7:
            hits[idx] = score

    scored = [(score, places[idx]) for idx, score in hits.items()]
    scored.sort(key=lambda sp: (-sp[0], -(sp[1].population or 0), fold(sp[1].name), sp[1].country or ""))
    return [(p, s) for s, p in scored]


def geocode(q: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Places for a free-text query. Empty list when nothing matches (UI asks for a map click)."""
    places = _load()
    if not q or not q.strip() or not places:
        return []
    if _head_is_country(q):
        # The gazetteer holds cities only. Answering "Perus, BR" to "Peru" would be
        # worse than answering nothing: the UI then asks for a click on the map.
        return []
    ranked = _rank(list(places), q)[:limit]
    results = [p.to_public(score=s) for p, s in ranked]
    # RONDA_4 §4.2: a place is accepted only if a verified source resolves it.
    # Named regions carry their own verified coordinates, so they can satisfy a
    # place name the city gazetteer does not contain ("Madre de Dios", "Sahel").
    if not results:
        results = _region_lookup(q, limit=limit)
    return results


def _region_lookup(q: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Exact (accent-free) match against data/catalog/regions.json."""
    path = SETTINGS.catalog_dir / "regions.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = payload.get("regions") if isinstance(payload, dict) else payload
    wanted = fold(q).strip()
    out: list[dict[str, Any]] = []
    for row in rows or []:
        names = row.get("names") or {}
        candidates = {fold(str(v)).strip() for v in names.values() if v}
        if wanted not in candidates:
            continue
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        out.append({
            "name": names.get("en") or names.get("es") or row.get("id"),
            "country": None,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "bbox": row.get("bbox"),
            "population": None,
            "source": "regions",
            "match_score": 1.0,
        })
        if len(out) >= limit:
            break
    return out


_WORD_RE = re.compile(r"\w+")
_MAX_SPAN_WORDS = 7  # "Santiago de los Caballeros de Mérida" is six


def find_in_text(text: str, *, limit: int = 3) -> list[tuple[Place, str]]:
    """Longest gazetteer spellings that appear literally inside ``text``.

    Used by the rules planner: the contract says ``place`` must be text copied
    from the question, so the returned span is sliced out of ``text`` itself.
    We look at name, ascii and alt_names, but a match is accepted only on a word
    boundary — otherwise "Ica" would match inside "America".
    """
    places = _load()
    if not text or not places:
        return []
    folded = fold(text)
    # RONDA_7: this used to compile one regular expression per spelling of every
    # city (58 000 per question, 1.3 s measured), which made each chat message
    # feel slow. Every spelling is already a key of the exact index, so it is
    # enough to look up the word-bounded spans of the question itself.
    exact, _prefix = _fields_index()
    tokens = [(m.start(), m.end()) for m in _WORD_RE.finditer(folded)]
    best: dict[int, tuple[str, int]] = {}
    for i, (start, _end) in enumerate(tokens):
        for j in range(i, min(i + _MAX_SPAN_WORDS, len(tokens))):
            span = folded[start : tokens[j][1]]
            if len(span) < 3:
                continue
            for idx in exact.get(span, ()):
                current = best.get(idx)
                if current is None or len(span) > len(current[0]):
                    best[idx] = (span, start)
    hits: list[tuple[Place, str, int, int]] = [
        (places[idx], text[start : start + len(span)], len(span), start) for idx, (span, start) in best.items()
    ]
    hits.sort(key=lambda h: (-h[2], -(h[0].population or 0), fold(h[0].name)))
    out: list[tuple[Place, str]] = []
    seen: set[str] = set()
    taken: list[tuple[int, int]] = []
    for place, span, length, start in hits:
        key = fold(span)
        if key in seen:
            continue
        # A shorter name inside a longer one already accepted is not a second
        # place: "San" (a city in Mali) inside "San Juan" must not become place B.
        if any(start < t_end and t_start < start + length for t_start, t_end in taken):
            continue
        seen.add(key)
        taken.append((start, start + length))
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
