# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Place extraction from free text, in the rules path (contract R3/R4).

Hard rules, from RONDA_4 §4.2 and §2.6:

  * a place is accepted **only if a verified source resolves it** — the GeoNames
    gazetteer (`data/catalog/gazetteer.json`, 8 109 cities) or the named regions
    (`data/catalog/regions.json`, 67 regions with verified coordinates);
  * the span returned is copied verbatim from the question (contract §10);
  * no source, no place: an unrecognised capitalised word is not a place.

The previous version had a grammatical fallback ("any capitalised word after a
preposition"), which produced ``place: "sea"`` and ``place_b: "Has"`` for "Has
Arctic sea ice shrunk since 1980?". That fallback is gone: it was the defect.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from .config import SETTINGS
from .gazetteer import find_in_text
from .text_norm import fold

_STOP_SUFFIXES = ("?", "!", ";", ":", ",")


@lru_cache(maxsize=1)
def _region_names() -> tuple[str, ...]:
    """Named regions with verified coordinates, most specific first.

    `data/catalog/regions.json` is claude-omni-1b's file; we only read it. Names
    come in both languages, so "Amazon Basin" and "Amazonía" both resolve.
    """
    path = SETTINGS.catalog_dir / "regions.json"
    if not path.exists():
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    rows = payload.get("regions") if isinstance(payload, dict) else payload
    names: list[str] = []
    for row in rows or []:
        for value in (row.get("names") or {}).values():
            if value and str(value) not in names:
                names.append(str(value))
    names.sort(key=len, reverse=True)
    return tuple(names)


def reset_cache() -> None:
    _region_names.cache_clear()


def _clean(span: str) -> str:
    span = span.strip()
    for suffix in _STOP_SUFFIXES:
        span = span.rstrip(suffix).strip()
    return span


def _region_spans(text: str) -> list[tuple[str, int]]:
    """Region names that appear literally, with their length (best first)."""
    folded = fold(text)
    hits: list[tuple[str, int]] = []
    for name in _region_names():
        needle = fold(name)
        if len(needle) < 4:
            continue
        for match in re.finditer(rf"(?<!\w){re.escape(needle)}(?!\w)", folded):
            hits.append((text[match.start():match.end()], len(needle)))
            break
    hits.sort(key=lambda item: -item[1])
    return hits


def resolve_place(span: str) -> bool:
    """True when a verified source resolves this span as a *place name*.

    ``geocode()`` is a user-facing search: it is generous on purpose (fuzzy,
    alt_names) so a student typing "Piur" finds Piura. That generosity is wrong
    here — GeoNames' alt_names map "Sea" to Seattle and "Los" to Lagos, which
    would make "Has Arctic sea ice shrunk?" produce ``place: "sea"``.

    A place in a plan must equal the canonical name (or a region name), accent-
    and case-insensitive. Nothing vaguer.
    """
    from .gazetteer import _load as _gazetteer_places
    from .gazetteer import _region_lookup

    wanted = fold(_clean(span)).strip()
    if len(wanted) < 3:
        return False
    if _region_lookup(span):
        return True
    for place in _gazetteer_places():
        for canonical in (place.name, place.ascii_name):
            if canonical and fold(str(canonical)).strip() == wanted:
                return True
    return False


def extract_place_spans(text: str, *, limit: int = 3) -> list[str]:
    """Place strings resolved by a verified source, copied verbatim from ``text``."""
    if not text:
        return []

    # 1) Gazetteer cities, 2) named regions. Each hit carries its position so the
    #    order in the question is preserved ("Piura y Tumbes" -> Piura, Tumbes).
    located: list[tuple[int, str]] = []
    for _place, span in find_in_text(text, limit=limit + 1):
        idx = fold(text).find(fold(span))
        located.append((idx if idx >= 0 else 10**6, span))
    for span, _len in _region_spans(text):
        idx = fold(text).find(fold(span))
        located.append((idx if idx >= 0 else 10**6, span))

    # Longest name wins over a fragment at the same position, then keep the
    # left-to-right order the student wrote.
    located.sort(key=lambda item: (item[0], -len(item[1])))
    ordered: list[str] = []
    for _idx, span in located:
        cleaned = _clean(span)
        if cleaned and cleaned not in ordered:
            ordered.append(cleaned)
    return _split_coordination(ordered, text)[:limit]


_COORD_SPLIT = re.compile(r"\s*(?:,| y | e | and | vs\.? | versus )\s*", re.IGNORECASE)


def _split_coordination(spans: list[str], original: str = "") -> list[str]:
    """'Lima y Cusco' -> ['Lima', 'Cusco'].

    Spans must stay literal substrings of the question (contract §10), so the
    split only happens when each part really appears in ``original``.
    """
    out: list[str] = []
    for span in spans:
        parts = [p for p in _COORD_SPLIT.split(span) if p.strip()]
        if len(parts) <= 1:
            out.append(span)
            continue
        for part in parts:
            part = part.strip()
            if part and (not original or part in original):
                out.append(part)
    seen: list[str] = []
    for item in out:
        if item not in seen:
            seen.append(item)
    return seen


def extract_places(text: str, *, limit: int = 2) -> list[str]:
    """Up to ``limit`` distinct places (for the `compare` intent)."""
    return extract_place_spans(text, limit=limit)
