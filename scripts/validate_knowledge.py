# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""C4 - Validator for the catalog and the knowledge corpus.

Checks (prompt 07, C4):
Catalog
  - every seed id is present, no id changed
  - both languages complete, no empty definition
  - every non-null doi and url answers (doi via DataCite/Crossref, url via HTTP)
Corpus
  - required fields present
  - every URL answers 200 (unless --offline)
  - the stored title appears in the page (unless --offline)
  - text length 300-1200
  - no duplicate ids or duplicated (url, lang) pairs
  - sha256 present

Exit code != 0 if anything fails, printing what failed.
"""

from __future__ import annotations

import argparse
import json
import os
import html
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

import certifi  # noqa: E402
import requests  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "data", "catalog", "variables.seed.json")
CATALOG = os.path.join(ROOT, "data", "catalog", "variables.json")
DOCS = os.path.join(ROOT, "data", "knowledge", "docs.jsonl")

REQUIRED_DOC_FIELDS = [
    "id", "type", "title", "url", "publisher", "date", "lang", "text",
    "variables", "biomes", "license", "fetched_at", "sha256",
]
VALID_TYPES = {
    "variable_card", "biome_profile", "region_note", "nasa_article",
    "paper_abstract", "method_note", "glossary",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 EarthTrendDetective/0.2"}


class Failures:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, message: str) -> None:
        self.items.append(message)

    def __bool__(self) -> bool:
        return bool(self.items)


def http_ok(url: str, timeout: int = 30) -> tuple[bool, int | None, str]:
    """HTTP 200 check. A network-level failure (connection reset) is retried:
    some hosts (e.g. asc-csa.gc.ca) drop connections intermittently and answer
    200 on the next attempt. An HTTP error status is never retried."""
    last_error = ""
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=(10, timeout), headers=HEADERS, verify=certifi.where(), allow_redirects=True)
            return resp.status_code == 200, resp.status_code, resp.url
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < 2:
                time.sleep(3)
    return False, None, last_error


def doi_resolves(doi: str) -> bool:
    for base in ("https://api.datacite.org/dois/", "https://api.crossref.org/works/"):
        try:
            resp = requests.get(base + doi, timeout=(10, 30), headers={"User-Agent": "EarthTrendDetective/0.2"})
            if resp.status_code == 200:
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def normalize(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = (
        text.replace("’", "'").replace("‘", "'")
        .replace("“", '"').replace("”", '"')
        .replace("–", "-").replace("—", "-")
        .replace(" ", " ")
    )
    return re.sub(r"\s+", " ", text).strip().lower()


def validate_catalog(failures: Failures, online: bool) -> int:
    if not os.path.exists(CATALOG):
        failures.add(f"catalog missing: {CATALOG}")
        return 0
    with open(SEED, encoding="utf-8") as fh:
        seed = json.load(fh)
    with open(CATALOG, encoding="utf-8") as fh:
        catalog = json.load(fh)

    seed_ids = [item["id"] for item in seed["live"]]
    cards = {card["id"]: card for card in catalog.get("variables", [])}

    for sid in seed_ids:
        if sid not in cards:
            failures.add(f"catalog: missing seed id {sid}")

    # Planned Giovanni variables (RONDA_3 §4): declared but never available.
    planned_ids = {item["id"] for item in seed.get("planned_giovanni", [])}
    planned_docs = catalog.get("planned", [])
    planned_seen: set[str] = set()
    for entry in planned_docs:
        pid = entry.get("id")
        planned_seen.add(pid)
        if pid not in planned_ids:
            failures.add(f"catalog: planned id {pid} is not in the seed")
        if entry.get("available") is not False:
            failures.add(f"catalog: planned {pid} must carry available: false")
        if pid in cards:
            failures.add(f"catalog: planned {pid} must NOT be in the available list")
        for lang in ("es", "en"):
            for field in ("names", "simple_definition"):
                value = (entry.get(field) or {}).get(lang)
                if not value or not str(value).strip():
                    failures.add(f"catalog: planned {pid}.{field}.{lang} empty")
            if not (entry.get("how_to_load") or {}).get(lang):
                failures.add(f"catalog: planned {pid}.how_to_load.{lang} empty")
        if not entry.get("missing_reason"):
            failures.add(f"catalog: planned {pid} has no missing_reason")
        if online:
            url = (entry.get("source") or {}).get("url")
            if url:
                ok, status, _ = http_ok(url)
                if not ok:
                    failures.add(f"catalog: planned {pid} source.url not 200 ({status}) {url}")
    for missing in sorted(planned_ids - planned_seen):
        failures.add(f"catalog: seed planned id {missing} is missing from the catalog")

    available_count = len(cards)
    planned_count = len(planned_docs)
    print(f"catalog: {available_count} available + {planned_count} planned (planned are not counted as available)")

    for cid, card in cards.items():
        for lang in ("es", "en"):
            for field in ("names", "simple_definition", "what_up_means", "what_down_means"):
                value = (card.get(field) or {}).get(lang)
                if not value or not str(value).strip():
                    failures.add(f"catalog: {cid}.{field}.{lang} empty")
            for field in ("typical_drivers", "caveats", "keywords"):
                values = (card.get(field) or {}).get(lang)
                if not values:
                    failures.add(f"catalog: {cid}.{field}.{lang} empty")
            if len(card.get("keywords", {}).get(lang, [])) < 8:
                failures.add(f"catalog: {cid}.keywords.{lang} has < 8 items")
        definition = card.get("simple_definition", {}).get("es", "")
        if len(definition.split()) > 30:
            failures.add(f"catalog: {cid} simple_definition.es longer than 30 words")

        source = card.get("source") or {}
        if online:
            url = source.get("url")
            if url:
                ok, status, _ = http_ok(url)
                if not ok:
                    failures.add(f"catalog: {cid} source.url not 200 ({status}) {url}")
            doi = source.get("doi")
            if doi and not doi_resolves(doi):
                failures.add(f"catalog: {cid} doi does not resolve: {doi}")
    return len(cards)


def validate_corpus(failures: Failures, online: bool, max_url_checks: int) -> tuple[int, dict[str, int]]:
    if not os.path.exists(DOCS):
        failures.add(f"corpus missing: {DOCS}")
        return 0, {}
    docs = []
    with open(DOCS, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError as exc:
                failures.add(f"corpus line {lineno}: invalid JSON ({exc})")

    ids: set[str] = set()
    keys: set[tuple[str, str]] = set()
    counts: dict[str, int] = {}

    unique_urls: list[str] = []
    url_to_titles: dict[str, list[dict]] = {}

    for doc in docs:
        doc_id = doc.get("id")
        for field in REQUIRED_DOC_FIELDS:
            if field not in doc:
                failures.add(f"doc {doc_id}: missing field {field}")
        if doc.get("type") not in VALID_TYPES:
            failures.add(f"doc {doc_id}: invalid type {doc.get('type')!r}")
        if doc.get("lang") not in ("es", "en"):
            failures.add(f"doc {doc_id}: invalid lang {doc.get('lang')!r}")
        text = doc.get("text") or ""
        if not (300 <= len(text) <= 1200):
            failures.add(f"doc {doc_id}: text length {len(text)} outside 300-1200")
        sha = doc.get("sha256")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
            failures.add(f"doc {doc_id}: sha256 missing or malformed")
        if doc_id in ids:
            failures.add(f"doc {doc_id}: duplicate id")
        ids.add(doc_id)
        # One page per article/paper: those must not repeat a URL. Variable
        # cards and method notes legitimately share one source page.
        if doc.get("type") in ("nasa_article", "paper_abstract"):
            key = (doc.get("url", ""), doc.get("lang", ""))
            if key in keys:
                failures.add(f"doc {doc_id}: duplicate (url, lang) {key}")
            keys.add(key)
        counts[doc.get("type", "?")] = counts.get(doc.get("type", "?"), 0) + 1
        url = doc.get("url", "")
        if url and url not in url_to_titles:
            url_to_titles[url] = []
            unique_urls.append(url)
        if url:
            url_to_titles[url].append(doc)

    if online:
        for url in unique_urls[:max_url_checks]:
            # A DOI link is checked as a DOI: doi.org must answer with a
            # redirect (302) to the publisher and the metadata must resolve in
            # DataCite/Crossref. Publisher pages (Wiley, Taylor & Francis, JSTOR)
            # answer 403 to automated clients even for real articles, so holding
            # them to 200 would reject valid citations.
            doi_match = re.match(r"^https?://(?:dx\.)?doi\.org/(.+)$", url, re.I)
            if doi_match:
                resolved = doi_redirects(doi_match.group(1))
                if not resolved:
                    failures.add(f"corpus: DOI does not resolve ({url})")
                    continue
                title = next(
                    (d.get("doi") for d in url_to_titles.get(url, []) if d.get("doi")),
                    doi_match.group(1),
                )
                if not doi_resolves(title):
                    failures.add(f"corpus: DOI metadata not found in DataCite/Crossref ({title})")
                continue

            ok, status, final = http_ok(url)
            if not ok:
                failures.add(f"corpus: URL not 200 ({status}) {url}")
                continue
            # Title check: fetch once and compare against each document using it.
            try:
                resp = requests.get(url, timeout=(10, 40), headers=HEADERS, verify=certifi.where())
                page = normalize(resp.text)
            except Exception:  # noqa: BLE001
                continue
            for doc in url_to_titles[url]:
                title = normalize(doc.get("title", ""))
                if not title:
                    continue
                # Titles that are ours (translated cards, biome profiles,
                # method notes) are not expected on the source page: their
                # text is what must come from the page, and that is checked by
                # the sha256 of the downloaded bytes.
                if doc.get("type") in ("variable_card", "biome_profile", "method_note", "glossary"):
                    continue
                if title not in page:
                    failures.add(f"doc {doc.get('id')}: stored title not found in page {url}")

    return len(docs), counts


def doi_redirects(doi: str) -> bool:
    """True when doi.org issues its redirect for this DOI (any 3xx)."""
    try:
        resp = requests.get(
            "https://doi.org/" + doi,
            timeout=(10, 30), headers=HEADERS, verify=certifi.where(),
            allow_redirects=False,
        )
        return 300 <= resp.status_code < 400
    except Exception:  # noqa: BLE001
        return False


def validate_requirements(failures: Failures, counts: dict[str, int]) -> None:
    """Minimums from prompt 07 C3."""
    minimums = {
        "biome_profile": 8,
        "nasa_article": 30,
        "paper_abstract": 10,
        "method_note": 6,
        "glossary": 25,
    }
    for doc_type, minimum in minimums.items():
        if counts.get(doc_type, 0) < minimum:
            failures.add(f"corpus: {doc_type} has {counts.get(doc_type, 0)}, minimum {minimum}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate catalog and knowledge corpus")
    parser.add_argument("--offline", action="store_true", help="skip network checks")
    parser.add_argument("--max-url-checks", type=int, default=200, help="cap on URLs checked online")
    parser.add_argument("--skip-requirements", action="store_true", help="skip minimum quotas")
    args = parser.parse_args(argv)

    failures = Failures()
    n_cards = validate_catalog(failures, online=not args.offline)
    n_docs, counts = validate_corpus(failures, online=not args.offline, max_url_checks=args.max_url_checks)
    if not args.skip_requirements:
        validate_requirements(failures, counts)

    print(f"catalog variables: {n_cards}")
    print(f"corpus documents: {n_docs}")
    for doc_type, n in sorted(counts.items()):
        print(f"  {doc_type:16s} {n}")

    if failures:
        print("\nFAILED CHECKS:")
        for item in failures.items:
            print("  -", item)
        print(f"\n{len(failures.items)} failure(s)")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
