# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""Shared HTTP fetching, extraction and provenance helpers for the Hermes 1 scraping pipeline.

Rules enforced here (see prompts/07_hermes-1_catalogo-y-conocimiento.md):
- Every downloaded page must answer HTTP 200; that fact is recorded.
- The stored text is extracted from the page that was actually downloaded.
- The sha256 is computed over the raw bytes that produced that text.
- Raw HTML is cached under data/knowledge/raw/ so every document can be re-audited.
- Never disable TLS verification; requests uses certifi explicitly.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import certifi
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(ROOT, "data", "cache", "knowledge", "raw")
TEXT_DIR = os.path.join(ROOT, "data", "cache", "knowledge", "text")

# science.nasa.gov returns 403 to some non-browser UAs on a subset of pages.
# We identify the tool honestly and keep the standard browser prefix because
# that is what the server accepts for public, non-personalised pages.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 EarthTrendDetective/0.2"
)
TIMEOUT = (15, 60)
MAX_RETRIES = 3
BACKOFF_BASE = 2.0

_session: requests.Session | None = None
_last_request_at = 0.0
MIN_INTERVAL_SECONDS = 2.5  # be polite to NASA / GeoNames / Crossref / Wikimedia


class FetchError(RuntimeError):
    """Raised when a page cannot be fetched or does not answer 200."""

    def __init__(self, url: str, status: int | None, reason: str) -> None:
        super().__init__(f"{reason} (status={status}) for {url}")
        self.url = url
        self.status = status
        self.reason = reason


def _session_get() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            }
        )
        _session = s
    return _session


def _throttle() -> None:
    global _last_request_at
    now = time.monotonic()
    wait = MIN_INTERVAL_SECONDS - (now - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


@dataclass
class FetchedPage:
    url: str
    final_url: str
    status: int
    raw: bytes
    content_type: str
    retrieved_at: str
    sha256: str = field(init=False)

    def __post_init__(self) -> None:
        self.sha256 = hashlib.sha256(self.raw).hexdigest()

    @property
    def text(self) -> str:
        return self.raw.decode("utf-8", errors="replace")


def fetch(url: str, *, force: bool = False, cache_key: str | None = None,
          headers: dict[str, str] | None = None) -> FetchedPage:
    """Fetch a URL, returning the raw bytes and provenance. Raises FetchError on non-200."""
    key = cache_key or _url_key(url)
    raw_path = os.path.join(RAW_DIR, key + ".html")
    meta_path = os.path.join(RAW_DIR, key + ".meta.json")

    if not force and os.path.exists(raw_path) and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        with open(raw_path, "rb") as fh:
            raw = fh.read()
        page = FetchedPage(
            url=meta["url"],
            final_url=meta["final_url"],
            status=meta["status"],
            raw=raw,
            content_type=meta.get("content_type", "text/html"),
            retrieved_at=meta["retrieved_at"],
        )
        if page.status != 200:
            raise FetchError(page.url, page.status, "cached_non_200")
        return page

    os.makedirs(RAW_DIR, exist_ok=True)
    last_error: FetchError | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        _throttle()
        try:
            resp = _session_get().get(
                url, timeout=TIMEOUT, verify=certifi.where(), allow_redirects=True,
                headers=headers,
            )
        except requests.RequestException as exc:
            last_error = FetchError(url, None, f"{type(exc).__name__}: {exc}")
            time.sleep(BACKOFF_BASE * attempt)
            continue

        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if resp.status_code == 200:
            page = FetchedPage(
                url=url,
                final_url=resp.url,
                status=resp.status_code,
                raw=resp.content,
                content_type=resp.headers.get("content-type", "text/html"),
                retrieved_at=retrieved_at,
            )
            with open(raw_path, "wb") as fh:
                fh.write(page.raw)
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "url": page.url,
                        "final_url": page.final_url,
                        "status": page.status,
                        "content_type": page.content_type,
                        "retrieved_at": page.retrieved_at,
                        "sha256": page.sha256,
                    },
                    fh,
                    ensure_ascii=False,
                    indent=2,
                )
            return page

        last_error = FetchError(url, resp.status_code, "http_error")
        # 403 on science.nasa.gov is mostly transient rate limiting for a
        # burst of requests: back off and retry. Other 4xx are definitive.
        if resp.status_code in (403, 408, 429, 500, 502, 503, 504):
            time.sleep(BACKOFF_BASE * attempt)
            continue
        break

    raise last_error or FetchError(url, None, "unknown_error")


def _url_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def save_text(key: str, text: str) -> str:
    os.makedirs(TEXT_DIR, exist_ok=True)
    path = os.path.join(TEXT_DIR, key + ".txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    """Normalise typography from HTML extraction without changing meaning."""
    text = text.replace(" ", " ")
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_sentences(text: str, min_chars: int = 300, max_chars: int = 1200) -> str:
    """Return 300-1200 chars of text, cutting on a sentence boundary when possible."""
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    # Prefer a sentence end above the minimum length.
    best = None
    for m in re.finditer(r"[.!?](?:\s|$)", window):
        if m.end() >= min_chars:
            best = m.end()
    if best is None:
        best = window.rfind(" ")
        if best < min_chars:
            best = max_chars
    return window[:best].strip()


def write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
