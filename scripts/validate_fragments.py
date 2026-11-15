# SI-assisted: cfable (Claude Fable 5.2)
"""Strict gate for the knowledge fragments (RONDA_7).

    python scripts/validate_fragments.py                # every fragment, offline
    python scripts/validate_fragments.py regions/lima   # one lane
    python scripts/validate_fragments.py --online       # also checks every URL answers
    python scripts/validate_fragments.py --stats        # coverage table per city

A fragment is ``data/knowledge/<regions|facts|resources>/<name>.jsonl`` with one
JSON object per line. In ``regions/`` and ``facts/`` the name is ``<city>`` (the
owner lane) or ``<city>-por-<lane>`` (a reinforcement from another lane); every id
starts with ``region-<name>-`` / ``fact-<name>-`` / ``res-<name>-``. The app loads fragments defensively (a bad row is skipped),
so THIS script is what keeps a lane honest: run it before every push. Exit code
is 0 only when there is nothing to fix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "data" / "knowledge"
CATALOG = ROOT / "data" / "catalog" / "variables.json"

# The five cities of the round. id -> the name that must appear in the title.
CITIES = {
    "lima": "Lima",
    "huancayo": "Huancayo",
    "andahuaylas": "Andahuaylas",
    "ica": "Ica",
    "ayacucho": "Ayacucho",
}

# folder -> (id prefix, allowed document types)
LANES = {
    "regions": ("region", {"region_note", "nasa_article", "paper_abstract", "data_note"}),
    "facts": ("fact", {"region_note"}),
    "resources": ("res", {"method_note", "nasa_article", "glossary", "paper_abstract"}),
}

REQUIRED = (
    "id", "type", "title", "url", "publisher", "lang", "text",
    "variables", "license", "fetched_at", "sha256", "is_quotation",
)
TEXT_MIN, TEXT_MAX = 200, 1500
ID_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$")


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def has_word(haystack: str, word: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(fold(word)) + r"(?!\w)", fold(haystack)) is not None


def catalog_ids() -> set[str]:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    ids = {str(c["id"]) for c in payload.get("variables", []) if c.get("id")}
    ids |= {str(c["id"]) for c in payload.get("planned", []) if c.get("id")}
    return ids


def legacy_ids() -> set[str]:
    path = KNOWLEDGE / "docs.jsonl"
    ids: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                ids.add(str(json.loads(line).get("id")))
    return ids


def fragment_paths(only: list[str]) -> list[Path]:
    paths: list[Path] = []
    for folder in LANES:
        base = KNOWLEDGE / folder
        if base.is_dir():
            paths.extend(sorted(p for p in base.glob("*.jsonl") if not p.name.startswith("_")))
    if only:
        wanted = {o.replace("\\", "/").removesuffix(".jsonl") for o in only}
        paths = [p for p in paths if f"{p.parent.name}/{p.stem}" in wanted]
    return paths


def check_row(row: dict, *, folder: str, stem: str, variables: set[str]) -> list[str]:
    """Everything wrong with one document (empty list = valid)."""
    problems: list[str] = []
    prefix, allowed_types = LANES[folder]

    for key in REQUIRED:
        if key not in row or row[key] in (None, "") and key not in ("variables",):
            problems.append(f"missing field {key!r}")
    if problems:
        return problems

    doc_id = str(row["id"])
    expected = f"{prefix}-{stem}-"
    city_token = stem.split("-")[0]
    # A data note may carry its source in the id ("giovanni-merra2-ica-tair-es") as
    # long as the city is a whole token, so the lane that owns it stays identifiable.
    token_ok = row.get("type") == "data_note" and re.search(
        r"(?:^|-)" + re.escape(city_token) + r"(?:-|$)", doc_id
    )
    if not doc_id.startswith(expected) and not token_ok:
        problems.append(f"id must start with {expected!r}")
    if not ID_RE.match(doc_id):
        problems.append("id must be lowercase letters, digits and single hyphens")
    if row["type"] not in allowed_types:
        problems.append(f"type {row['type']!r} not allowed in {folder}/ (use {sorted(allowed_types)})")
    if row["lang"] not in ("es", "en"):
        problems.append("lang must be 'es' or 'en'")
    if not isinstance(row["is_quotation"], bool):
        problems.append("is_quotation must be true or false")
    elif row["is_quotation"] is False and not row.get("summary_by"):
        problems.append("a summary (is_quotation=false) needs summary_by")

    url = str(row["url"])
    if not re.match(r"^https?://[^\s/]+\.[^\s/]+", url):
        problems.append("url must be an absolute http(s) link to the source page")
    if any(host in url for host in ("localhost", "127.0.0.1", "example.com")):
        problems.append("url points to a placeholder host")

    text = str(row["text"])
    if not (TEXT_MIN <= len(text) <= TEXT_MAX):
        problems.append(f"text has {len(text)} characters (allowed {TEXT_MIN}-{TEXT_MAX})")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if str(row["sha256"]).lower() != digest:
        problems.append("sha256 does not match the text (recompute: sha256 of the UTF-8 text)")
    if re.search(r"lorem ipsum|TODO|XXX|\[citation needed\]", text, re.IGNORECASE):
        problems.append("text contains a placeholder")

    if not isinstance(row["variables"], list):
        problems.append("variables must be a list")
    else:
        # A data note names the dataset's own variables (Tair, Rainf...), not catalogue ids.
        unknown = [] if row["type"] == "data_note" else [v for v in row["variables"] if v not in variables]
        if unknown:
            problems.append(f"variables not in the catalogue: {unknown}")

    if not STAMP_RE.match(str(row["fetched_at"])):
        problems.append("fetched_at must be an ISO date or timestamp, e.g. 2026-11-15T19:30:00Z")
    if row.get("date") and not DATE_RE.match(str(row["date"])):
        problems.append("date must be YYYY, YYYY-MM or YYYY-MM-DD (or null)")

    places = row.get("places") or []
    if folder in ("regions", "facts"):
        # <city>.jsonl is the owner's file; <city>-por-<lane>.jsonl is a reinforcement
        # written by another lane (it never edits the owner's file).
        city = stem.split("-")[0]
        if city not in CITIES:
            problems.append(f"file name must start with one of {sorted(CITIES)}")
        else:
            if places != [city] and city not in places:
                problems.append(f"places must include {city!r}")
            if not has_word(str(row["title"]), CITIES[city]):
                problems.append(f"title must name the city ({CITIES[city]!r})")
            if not has_word(text, CITIES[city]):
                problems.append(f"text must name the city ({CITIES[city]!r})")
    if folder == "facts":
        if row["is_quotation"] is not False:
            problems.append("computed facts are never quotations (is_quotation=false)")
        if not row.get("generated_from"):
            problems.append("computed facts need generated_from (the script or endpoint)")
        if not row["variables"]:
            problems.append("a computed fact must name its variable")

    supersedes = row.get("supersedes")
    if supersedes is not None:
        if not isinstance(supersedes, list) or not all(isinstance(x, str) for x in supersedes):
            problems.append("supersedes must be a list of document ids")
        elif supersedes and not row.get("supersedes_reason"):
            problems.append("supersedes needs supersedes_reason")
    return problems


def check_online(urls: dict[str, list[str]]) -> list[str]:
    try:
        import certifi
        import requests
    except ImportError:
        return ["--online needs the 'requests' and 'certifi' packages"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EarthTrendDetective/0.3"}
    problems: list[str] = []
    for url, owners in sorted(urls.items()):
        status: object = None
        for _attempt in range(3):
            try:
                resp = requests.get(url, timeout=(10, 40), headers=headers, verify=certifi.where(), stream=True)
                status = resp.status_code
                resp.close()
                break
            except Exception as exc:  # noqa: BLE001 - reported, never swallowed
                status = type(exc).__name__
        if status != 200:
            problems.append(f"{owners[0]}: {url} answered {status}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("lanes", nargs="*", help="e.g. regions/lima facts/ica (default: all)")
    parser.add_argument("--online", action="store_true", help="also check that every URL answers 200")
    parser.add_argument("--stats", action="store_true", help="print a coverage table")
    args = parser.parse_args(argv)

    variables = catalog_ids()
    seen_ids: dict[str, str] = {doc_id: "docs.jsonl" for doc_id in legacy_ids()}
    seen_text: dict[str, str] = {}
    urls: dict[str, list[str]] = {}
    failures: list[str] = []
    table: dict[str, dict[str, int]] = {}
    total = 0

    all_paths = fragment_paths([])
    chosen = {p for p in fragment_paths(args.lanes)}
    if args.lanes and not chosen:
        print(f"no fragment matches {args.lanes}", file=sys.stderr)
        return 2

    for path in all_paths:
        label = f"{path.parent.name}/{path.name}"
        report = path in chosen
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            if report:
                failures.append(f"{label}: not valid UTF-8 (save without BOM, UTF-8)")
            continue
        stats = table.setdefault(label, {"docs": 0, "es": 0, "en": 0, "urls": 0, "quotes": 0})
        file_urls: set[str] = set()
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            where = f"{label}:{lineno}"
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                if report:
                    failures.append(f"{where}: not valid JSON ({exc.msg})")
                continue
            if not isinstance(row, dict):
                if report:
                    failures.append(f"{where}: each line must be one JSON object")
                continue
            problems = check_row(row, folder=path.parent.name, stem=path.stem, variables=variables)
            doc_id = str(row.get("id"))
            if doc_id in seen_ids:
                problems.append(f"id {doc_id!r} already used in {seen_ids[doc_id]}")
            else:
                seen_ids[doc_id] = label
            text_key = hashlib.sha256(fold(str(row.get("text", ""))).encode("utf-8")).hexdigest()
            if text_key in seen_text and seen_text[text_key] != where:
                problems.append(f"same text as {seen_text[text_key]}")
            else:
                seen_text[text_key] = where
            if report:
                failures.extend(f"{where} [{doc_id}]: {p}" for p in problems)
                total += 1
            if not problems:
                stats["docs"] += 1
                stats[row["lang"]] += 1
                stats["quotes"] += 1 if row["is_quotation"] else 0
                file_urls.add(str(row["url"]))
                urls.setdefault(str(row["url"]), []).append(where)
        stats["urls"] = len(file_urls)

    # supersedes must point at documents that exist somewhere else
    for path in all_paths:
        if path not in chosen:
            continue
        label = f"{path.parent.name}/{path.name}"
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            try:
                row = json.loads(line) if line.strip() else None
            except json.JSONDecodeError:
                continue
            for old in (row or {}).get("supersedes") or []:
                if old not in seen_ids:
                    failures.append(f"{label}:{lineno}: supersedes unknown id {old!r}")
                elif seen_ids[old] == label:
                    failures.append(f"{label}:{lineno}: supersedes {old!r} from its own file (edit it instead)")

    if args.online and not failures:
        failures.extend(check_online(urls))

    if args.stats or not failures:
        print(f"{'fragment':34} {'docs':>5} {'es':>4} {'en':>4} {'urls':>5} {'quotes':>6}")
        for label in sorted(table):
            s = table[label]
            print(f"{label:34} {s['docs']:>5} {s['es']:>4} {s['en']:>4} {s['urls']:>5} {s['quotes']:>6}")

    if failures:
        print(f"\n{len(failures)} problem(s) in {total} document(s):", file=sys.stderr)
        for item in failures:
            print("  - " + item, file=sys.stderr)
        return 1
    print(f"\nOK: {total} document(s) valid in {len(chosen)} fragment file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
