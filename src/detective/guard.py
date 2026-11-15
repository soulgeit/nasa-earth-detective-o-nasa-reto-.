# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""The guard: code, not a model (contract R6).

Every explanation this app shows has to pass here before the student sees it:

  1. every number in the text must exist in the facts (rounding-tolerant) or be a year
     that the facts actually contain;
  2. every citation marker [n] must point to a passage that was really given;
  3. the language must be the one requested;
  4. if the verdict is not significant, causal-overclaim words are rejected
     ("demuestra", "prueba", "sin duda", "proves", "confirms", ...).

The guard is deliberately numbers-only and deterministic: no model runs here, so a
jailbroken or hallucinating model cannot talk its way past it.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .text_norm import detect_language, fold

# --- language ---------------------------------------------------------------
_CAUSAL_WORDS = {
    "es": (
        "demuestra", "demuestran", "prueba que", "prueban", "sin duda", "sin lugar a dudas",
        "indudablemente", "definitivamente", "confirma", "confirman", "está demostrado",
        "está probado", "causa directa", "es causado por", "es culpa de", "garantiza",
        "seguro que", "por supuesto que", "claramente demuestra",
    ),
    "en": (
        "proves", "prove that", "confirms", "confirm that", "undoubtedly", "without a doubt",
        "definitely", "clearly demonstrates", "it is proven", "it is proved", "causes",
        "is caused by", "guarantees", "of course it", "certainly proves",
    ),
}

HEDGES = {
    "es": ("compatible con", "podría", "podrian", "puede indicar", "sugiere", "es posible",
           "no se puede descartar", "hipótesis", "no permite afirmar"),
    "en": ("compatible with", "could", "may indicate", "suggests", "it is possible",
           "cannot rule out", "hypothesis", "does not allow us to say"),
}

NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")
CITATION_RE = re.compile(r"\[(\d{1,2})\]")
YEAR_RE = re.compile(r"\b(1[6-9]\d{2}|20\d{2}|2100)\b")
# Identifiers that are not claims: [3] is a citation marker, T2M/AOD_55 are
# variable ids. Counting them as "numbers the model made up" would produce
# false rejections of perfectly correct answers.
_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b|\bT2M\b|\bTS\b|\bNO2\b|\bCO2\b|\bO3\b")
_UNIT_RE = re.compile(r"\d+\s*(?:m\b|km\b|mm\b|cm\b|kg\b|DU\b|MJ\b|W\b|hPa\b|%|°)?")
# A URL is a pointer to a source, not a claim: its digits (article ids, DOIs,
# page numbers) must never be read as "a number the writer invented".
_URL_RE = re.compile(r"https?://\S+|www\.\S+|doi:\s*\S+", re.IGNORECASE)


def strip_non_claims(text: str) -> str:
    """Remove citation markers, URLs and identifier-shaped tokens before number checks."""
    text = _URL_RE.sub(" ", text)
    text = CITATION_RE.sub(" ", text)
    text = _IDENTIFIER_RE.sub(" ", text)
    return text


@dataclass
class GuardResult:
    numbers_ok: bool
    citations_ok: bool
    language_ok: bool
    no_overclaim: bool
    reasons: list[str] = field(default_factory=list)
    retries: int = 0

    @property
    def ok(self) -> bool:
        return self.numbers_ok and self.citations_ok and self.language_ok and self.no_overclaim

    def to_public(self) -> dict[str, Any]:
        return {
            "numbers_ok": self.numbers_ok,
            "citations_ok": self.citations_ok,
            "language_ok": self.language_ok,
            "no_overclaim": self.no_overclaim,
            "retries": self.retries,
            "reasons": self.reasons,
        }


def _parse_number(token: str) -> float:
    return float(token.replace(",", "."))


def collect_numbers(value: Any, *, _depth: int = 0) -> set[float]:
    """All numeric leaves of a facts structure, recursively."""
    found: set[float] = set()
    if _depth > 8:
        return found
    if isinstance(value, bool):
        return found
    if isinstance(value, (int, float)):
        found.add(float(value))
        return found
    if isinstance(value, str):
        for token in NUMBER_RE.findall(value):
            try:
                found.add(_parse_number(token))
            except ValueError:
                continue
        return found
    if isinstance(value, dict):
        for item in value.values():
            found |= collect_numbers(item, _depth=_depth + 1)
        return found
    if isinstance(value, (list, tuple)):
        for item in value:
            found |= collect_numbers(item, _depth=_depth + 1)
    return found


def collect_years(value: Any) -> set[int]:
    years: set[int] = set()
    if isinstance(value, str):
        years |= {int(y) for y in YEAR_RE.findall(value)}
    elif isinstance(value, dict):
        for item in value.values():
            years |= collect_years(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            years |= collect_years(item)
    return years


def _decimals(token: str) -> int:
    token = token.replace(",", ".")
    return len(token.split(".")[1]) if "." in token else 0


def _truncate(value: float, decimals: int) -> float:
    """Cut extra digits, the way a written number is cut — not banker's rounding.

    ``round(0.1585, 3)`` is 0.159 (and 0.158 only by luck of the binary
    representation), while the engine's own template writes "+0.158 °C/década".
    Both are honest renderings of 0.1585, so the guard must accept either: it
    compares at the token's precision with the last written digit free to be a
    rounded-up one. Anything further away is still rejected.
    """
    scaled = 10.0 ** decimals
    return math.floor(value * scaled + 1e-9) / scaled


def _number_allowed(token: str, facts: set[float], years: set[int]) -> bool:
    """A number is allowed only when it is a rendering of a fact at its precision.

    Tolerance comes from the *token's own* precision, never from a blanket
    percentage window: "0.3" is an acceptable rendering of 0.31, but "1999" is not
    a rendering of 1981 and "0.0001" is not a rendering of 0.01. A blanket ±1 %
    window would let both through, which is exactly what this guard exists to stop.
    """
    try:
        value = _parse_number(token)
    except ValueError:
        return False
    if value == int(value) and int(value) in years:
        return True
    decimals = min(_decimals(token), 6)
    tolerance = 0.5 * 10.0 ** (-decimals) * 1.01 + 1e-9
    for fact in facts:
        if abs(value - fact) <= tolerance:
            return True
        if abs(value - _truncate(fact, decimals)) <= tolerance:
            return True
    return False


_QUOTED_RE = re.compile(r'"[^"\n]{1,600}"|“[^”\n]{1,600}”')


def split_quotes(text: str) -> tuple[str, list[str]]:
    """Separate the writer's own prose from verbatim quotations.

    A quoted passage is copied from a source, so its numbers belong to that source
    (`Aerosol Optical Depth 55`). They are validated against the passages, not
    against the facts — and the writer's prose is validated against the facts.
    """
    quoted = _QUOTED_RE.findall(text)
    prose = _QUOTED_RE.sub(" ", text)
    return prose, quoted


_REF_LINE_RE = re.compile(r"^\s*\[\d{1,2}\].*$", re.MULTILINE)


def _strip_passage_labels(prose: str, passages: Iterable[dict[str, Any]]) -> str:
    """Drop the reference lines before checking the writer's prose.

    A line like ``[2] Flood Waters — NASA Earth Observatory:`` is attribution
    metadata (a title, a publisher such as "Hermes 1", a URL), not a claim the
    writer makes. Its digits must not be read as invented figures. The quoted
    sentence on that line is still checked, against the passages it came from.
    """
    prose = _REF_LINE_RE.sub(" ", prose)
    for passage in passages:
        title = str(passage.get("title") or "").strip()
        if title:
            prose = prose.replace(title, " ")
        publisher = str(passage.get("publisher") or "").strip()
        if publisher:
            prose = prose.replace(publisher, " ")
    return prose


def check_numbers(text: str, facts: Any, *, passages: Iterable[dict[str, Any]] | None = None) -> tuple[bool, list[str]]:
    values = collect_numbers(facts)
    years = collect_years(facts)
    passage_list = list(passages or [])
    if passage_list:
        quote_values = collect_numbers([p.get("title", "") + " " + p.get("text", "") for p in passage_list])
        quote_years = collect_years([p.get("title", "") + " " + p.get("text", "") for p in passage_list])
    else:
        quote_values, quote_years = set(), set()

    bad: list[str] = []
    prose, quotes = split_quotes(text)
    prose = _strip_passage_labels(prose, passage_list)
    # 1) What the writer asserts must be justified by the facts.
    for token in NUMBER_RE.findall(strip_non_claims(prose)):
        if not _number_allowed(token, values, years):
            bad.append(token)
    # 2) Numbers inside quotation marks must exist in the passages quoted.
    for quote in quotes:
        for token in NUMBER_RE.findall(strip_non_claims(quote)):
            if _number_allowed(token, quote_values, quote_years) or _number_allowed(token, values, years):
                continue
            bad.append(token)
    return (not bad), bad


def check_citations(text: str, passages: Iterable[dict[str, Any]]) -> tuple[bool, list[str]]:
    valid = {i for i, _ in enumerate(passages, start=1)}
    used = {int(n) for n in CITATION_RE.findall(text)}
    unknown = sorted(used - valid)
    return (not unknown), [f"[{n}] has no passage" for n in unknown]


def check_language(text: str, lang: str) -> tuple[bool, list[str]]:
    detected = detect_language(text)
    if detected == lang:
        return True, []
    return False, [f"text looks {detected}, expected {lang}"]


def check_no_overclaim(text: str, *, lang: str, is_significant: bool | None) -> tuple[bool, list[str]]:
    """Reject causal certainty when the verdict does not support it.

    Both language lists are always checked: a model that answers in Spanish while
    slipping in "proves" must be caught as surely as one that writes
    "demuestra". ``lang`` is kept in the signature because the guard reports which
    language the answer was meant to be in.
    """
    if is_significant:
        return True, []
    folded = fold(text)
    hits: list[str] = []
    for words in _CAUSAL_WORDS.values():
        hits.extend(w for w in words if fold(w) in folded)
    return (not hits), [f"causal overclaim: {h}" for h in hits]


def run_guard(
    text: str,
    *,
    facts: Any,
    passages: Iterable[dict[str, Any]],
    lang: str,
    is_significant: bool | None,
    retries: int = 0,
) -> GuardResult:
    passages = list(passages)
    n_ok, bad_numbers = check_numbers(text, facts, passages=passages)
    c_ok, bad_cites = check_citations(text, passages)
    l_ok, bad_lang = check_language(text, lang)
    o_ok, bad_over = check_no_overclaim(text, lang=lang, is_significant=is_significant)
    reasons: list[str] = []
    if not n_ok:
        reasons.append("unverified numbers: " + ", ".join(bad_numbers[:8]))
    reasons.extend(bad_cites)
    reasons.extend(bad_lang)
    reasons.extend(bad_over)
    return GuardResult(
        numbers_ok=n_ok,
        citations_ok=c_ok,
        language_ok=l_ok,
        no_overclaim=o_ok,
        reasons=reasons,
        retries=retries,
    )


def has_hedge(text: str, *, lang: str) -> bool:
    folded = fold(text)
    return any(fold(h) in folded for h in HEDGES.get(lang, HEDGES["en"]))
