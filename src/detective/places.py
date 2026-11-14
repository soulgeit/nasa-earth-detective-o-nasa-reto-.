# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Place extraction from free text, in the rules path (contract R3/R4).

Hard rule: the detective never produces coordinates. This module only finds the
*span of text* that names a place, so the plan can say ``place: "Piura"`` (a
substring of the question, as §10 requires). Turning that span into lat/lon is
``geocode()``'s job: gazetteer first, map click as the honest fallback.

Two sources, in order:
  1. the gazetteer (when Hermes 1 has written ``data/catalog/gazetteer.json``);
  2. a grammatical heuristic over capitalised words after a location preposition
     ("en Piura", "de Lima", "in the Amazon", "near Iquitos").
"""

from __future__ import annotations

import re

from .gazetteer import find_in_text

# Prepositions that introduce a place, Spanish and English.
_PREP_ES = r"(?:en|de|del|desde|hacia|para|cerca de|alrededor de|sobre)"
_PREP_EN = r"(?:in|of|from|near|around|at|over|across)"
_PREP = rf"(?:{_PREP_ES}|{_PREP_EN})"

# Capitalised run, optionally multi-word, allowing accents. The connector list
# includes conjunctions so that "en Lima y Cusco" is captured whole and then
# split into two literal substrings by _split_coordination().
_CONNECTOR = r"(?:de|del|la|el|los|las|the|of|and|y|e|vs\.?|versus)"
_PLACE_RE = re.compile(
    rf"\b{_PREP}\s+(?P<place>(?:[A-ZÁÉÍÓÚÑÜ][\wáéíóúñü'’.-]+)(?:\s+{_CONNECTOR}\s*[A-ZÁÉÍÓÚÑÜ][\wáéíóúñü'’.-]+)?)",
    re.UNICODE,
)

# Words that look capitalised at the start of a sentence but are not places.
_FALSE_FRIENDS = {
    "que", "como", "cuando", "donde", "porque", "pero", "este", "esta", "esto",
    "what", "how", "why", "when", "where", "which", "the", "there", "nasa",
}

_STOP_SUFFIXES = ("?", "!", ";", ":", ",")


def _clean(span: str) -> str:
    span = span.strip()
    for suffix in _STOP_SUFFIXES:
        span = span.rstrip(suffix).strip()
    return span


def extract_place_spans(text: str, *, limit: int = 3) -> list[str]:
    """Candidate place strings, copied verbatim from ``text`` (best first)."""
    if not text:
        return []

    # 1) Gazetteer: exact occurrence of a known place name inside the question.
    known = [span for _place, span in find_in_text(text, limit=limit)]
    # A conjunction between two places ("Lima y Cusco", "Piura, Peru") splits
    # gazetteer hits into separate places; keep both sides when they are.
    split = _split_coordination(known, text)
    if split:
        return split[:limit]
    if known:
        return known

    # 2) Grammar: "en <Proper noun>".
    out: list[str] = []
    for match in _PLACE_RE.finditer(text):
        span = _clean(match.group("place"))
        if not span:
            continue
        first = span.split()[0]
        if first.lower() in _FALSE_FRIENDS:
            continue
        if span not in out:
            out.append(span)
        if len(out) >= limit:
            break
    return _split_coordination(out, text)[:limit]


_COORD_SPLIT = re.compile(r"\s*(?:,| y | e | and | vs\.? | versus )\s*", re.IGNORECASE)


def _split_coordination(spans: list[str], original: str = "") -> list[str]:
    """'Lima y Cusco' -> ['Lima', 'Cusco'].

    Spans must stay literal substrings of the question (contract §10), so the
    split only happens when the conjunction is really in ``original``
    ('¡llueve menos en Piura que en Tumbes?' splits; a gazetteer span like
    'Lima' followed by ', Peru' does not invent anything).
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
    spans = extract_place_spans(text, limit=limit + 1)
    cleaned: list[str] = []
    for span in spans:
        if span not in cleaned:
            cleaned.append(span)
    return cleaned[:limit]
