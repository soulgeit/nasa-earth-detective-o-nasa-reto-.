# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Corpus loading for the detective RAG (contract §9).

Sources, in order of preference:
  1. ``data/knowledge/docs.jsonl``      — Hermes 1's verified corpus (one JSON per line).
  2. ``data/catalog/variables.json``    — full catalogue cards (contract §8).
  3. ``data/catalog/variables.seed.json`` — the shared seed (ids, names, units only).

Nothing is synthesised: a document only exists if some file in the repo provides
it. Cards derived from the catalogue carry ``derived_from`` so the UI and the
guard can tell them apart from downloaded NASA pages.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .config import SETTINGS
from .text_norm import fold

VALID_TYPES = (
    "variable_card",
    "biome_profile",
    "region_note",
    "nasa_article",
    "paper_abstract",
    "method_note",
    "glossary",
)

POWER_PARAMS_URL = "https://power.larc.nasa.gov/parameters/"


@dataclass
class Document:
    id: str
    type: str
    title: str
    url: str | None
    text: str
    lang: str
    publisher: str | None = None
    date: str | None = None
    variables: list[str] = field(default_factory=list)
    biomes: list[str] = field(default_factory=list)
    license: str | None = None
    derived_from: str | None = None
    # A document whose text is our own summary, not a literal quotation of the page.
    # RONDA_5 §2.15: a summary must never be shown between quotation marks.
    is_quotation: bool = True
    summary_by: str | None = None
    # True when the app can actually fetch this variable today (a `live`
    # connector), False for `planned_giovanni` cards that depend on a CSV the
    # human has not exported yet. The planner prefers what we can deliver.
    available: bool = True

    def searchable(self) -> str:
        """Text that BM25 sees: title repeated, then body, then controlled tags."""
        parts = [self.title, self.title, self.text]
        if self.variables:
            parts.append(" ".join(self.variables))
        if self.biomes:
            parts.append(" ".join(self.biomes))
        return "\n".join(p for p in parts if p)

    def to_public(self, score: float) -> dict[str, Any]:
        return {
            "id": self.id,
            "score": round(float(score), 6),
            "title": self.title,
            "url": self.url,
            "type": self.type,
            "lang": self.lang,
            "date": self.date,
            "publisher": self.publisher,
            "variables": list(self.variables),
            # RONDA_4 rule 19: a planned product is documented but never analysable.
            "available": self.available,
            "is_quotation": self.is_quotation,
            "summary_by": self.summary_by,
            "text": self.text,
            "available": bool(self.available),
        }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:  # explicit, never silent
                raise ValueError(f"{path.name}:{lineno} is not valid JSON: {exc}") from exc
    return rows


def _doc_from_jsonl(row: dict[str, Any], *, source: Path) -> Document:
    missing = [k for k in ("id", "type", "title", "text", "lang") if not row.get(k)]
    if missing:
        raise ValueError(f"{source.name}: document {row.get('id', '?')} is missing {missing}")
    if row["type"] not in VALID_TYPES:
        raise ValueError(f"{source.name}: document {row['id']} has unknown type {row['type']!r}")
    return Document(
        id=str(row["id"]),
        type=str(row["type"]),
        title=str(row["title"]),
        url=row.get("url"),
        text=str(row["text"]),
        lang=str(row["lang"]),
        publisher=row.get("publisher"),
        date=row.get("date"),
        variables=list(row.get("variables") or []),
        biomes=list(row.get("biomes") or []),
        license=row.get("license"),
        is_quotation=bool(row.get("is_quotation", True)),
        summary_by=row.get("summary_by"),
    )


def _pick(field_value: Any, lang: str) -> str:
    """Bilingual field -> string. Accepts {'es','en'} or a plain string."""
    if isinstance(field_value, str):
        return field_value
    if isinstance(field_value, dict):
        return str(field_value.get(lang) or field_value.get("en") or field_value.get("es") or "")
    if isinstance(field_value, list):
        return "; ".join(str(x) for x in field_value)
    return ""


def _card_to_doc(card: dict[str, Any], lang: str, *, derived_from: str, available: bool = True) -> Document:
    vid = str(card["id"])
    name = _pick(card.get("names") or card.get("power_longname") or vid, lang)
    unit = card.get("unit") or ""
    source = card.get("source") or {}
    bits: list[str] = []
    definition = _pick(card.get("simple_definition") or "", lang)
    if definition:
        bits.append(definition)
    if unit:
        bits.append(("Unidad: " if lang == "es" else "Unit: ") + str(unit))
    if source.get("model_or_mission"):
        bits.append(("Fuente: " if lang == "es" else "Source: ") + str(source["model_or_mission"]))
    for key, label_es, label_en in (
        ("what_up_means", "Si sube puede indicar", "If it rises it may indicate"),
        ("what_down_means", "Si baja puede indicar", "If it falls it may indicate"),
    ):
        value = _pick(card.get(key) or "", lang)
        if value:
            bits.append((label_es if lang == "es" else label_en) + ": " + value)
    drivers = _pick(card.get("typical_drivers") or "", lang)
    if drivers:
        bits.append(("Suele cambiar por: " if lang == "es" else "Typically driven by: ") + drivers)
    caveats = _pick(card.get("caveats") or "", lang)
    if caveats:
        bits.append(("Ojo: " if lang == "es" else "Caveat: ") + caveats)
    keywords = _pick(card.get("keywords") or "", lang)
    if keywords:
        bits.append(keywords)
    if not bits:
        bits.append(card.get("power_longname") or vid)

    uid = f"card-{vid.lower()}-{lang}"
    return Document(
        id=uid,
        type="variable_card",
        title=name,
        url=(source.get("url") if isinstance(source, dict) else None) or POWER_PARAMS_URL,
        text="\n".join(bits),
        lang=lang,
        publisher=str(source.get("via")) if source.get("via") else "NASA POWER",
        variables=[vid],
        license="NASA (public domain)",
        derived_from=derived_from,
        available=available,
    )


def load_catalog_cards() -> list[tuple[dict[str, Any], bool]]:
    """(card, available) pairs. ``available`` is False for planned Giovanni products.

    RONDA_3 §4 (claude-omni-1b's approved proposal): the full catalogue carries a
    ``planned`` section for the mission products we do not have yet. We read it so
    the detective can say "that variable exists but is not loaded — upload the
    Giovanni CSV" instead of pretending it does not exist. A catalogue without the
    section (the current 15-variable file) keeps working unchanged.
    """
    full = SETTINGS.catalog_dir / "variables.json"
    seed = SETTINGS.catalog_dir / "variables.seed.json"
    if full.exists():
        payload = json.loads(full.read_text(encoding="utf-8"))
        cards = payload.get("variables") if isinstance(payload, dict) else payload
        available = [(c, True) for c in (cards or []) if c.get("id")]
        planned = [
            (dict(c, available=False), False)
            for c in ((payload.get("planned") if isinstance(payload, dict) else None) or [])
            if c.get("id")
        ]
        return available + planned
    if seed.exists():
        payload = json.loads(seed.read_text(encoding="utf-8"))
        live = [(c, True) for c in (payload.get("live") or [])]
        planned = [(dict(c, available=False), False) for c in (payload.get("planned_giovanni") or [])]
        return live + planned
    return []


def load_corpus(langs: Iterable[str] = ("es", "en")) -> list[Document]:
    """Return every document available in the repo. Deterministic order."""
    docs: list[Document] = []
    knowledge = SETTINGS.knowledge_dir / "docs.jsonl"
    if knowledge.exists():
        for row in _read_jsonl(knowledge):
            doc = _doc_from_jsonl(row, source=knowledge)
            if doc.lang in ("es", "en"):
                docs.append(doc)

    # Hermes 1's docs.jsonl now carries a verified card per variable per language.
    # A card derived from data/catalog/variables.json would be a second, poorer copy
    # of the same thing, so we only derive cards for variables the corpus still lacks.
    covered = {(doc.variables[0], doc.lang) for doc in docs if doc.type == "variable_card" and doc.variables}
    for card, available in load_catalog_cards():
        if not card.get("id"):
            continue
        for lang in langs:
            if (str(card["id"]), lang) in covered:
                continue
            docs.append(_card_to_doc(card, lang, derived_from="catalog", available=available))

    # de-duplicate by id, keeping the first occurrence (knowledge file wins)
    seen: set[str] = set()
    unique: list[Document] = []
    for doc in docs:
        if doc.id in seen:
            continue
        seen.add(doc.id)
        unique.append(doc)
    return unique


def corpus_fingerprint(docs: list[Document]) -> str:
    h = hashlib.sha256()
    for doc in sorted(docs, key=lambda d: d.id):
        h.update(doc.id.encode())
        h.update(fold(doc.searchable()).encode())
    return h.hexdigest()
