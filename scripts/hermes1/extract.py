# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""HTML -> (title, main text, date) extraction for the NASA pages we may cite.

Every extractor works on the HTML that was downloaded and cached, so the stored
text can be traced back to the bytes whose sha256 is recorded in the document.
"""

from __future__ import annotations

import json
import html
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from .fetch_common import clean_text


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


ARTICLE_BLOCK_SELECTORS = [
    "article .entry-content",
    "article",
    "main",
    "#main-content",
    "#content",
    "body",
]


def _main_node(soup: BeautifulSoup):
    for selector in ARTICLE_BLOCK_SELECTORS:
        node = soup.select_one(selector)
        if node is not None and len(clean_text(node.get_text(" "))) > 200:
            return node
    return soup.body or soup


def page_title(soup: BeautifulSoup) -> str | None:
    for selector in ("h1.entry-title", "h1", "meta[property='og:title']"):
        node = soup.select_one(selector)
        if node is None:
            continue
        if selector.startswith("meta"):
            value = node.get("content")
        else:
            value = node.get_text(" ", strip=True)
        if value:
            return clean_text(html.unescape(value))
    if soup.title:
        return clean_text(html.unescape(soup.title.get_text(" ", strip=True)))
    return None


DATE_PATTERNS = [
    (r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', "iso"),
    (r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})', "iso"),
    (r'content="(\d{4}-\d{2}-\d{2})', "iso"),
]


def page_date(soup: BeautifulSoup, html: str) -> str | None:
    """Return an ISO date string if the page states one, else None."""
    for node in soup.find_all("time"):
        dt = node.get("datetime")
        if dt and re.match(r"^\d{4}-\d{2}-\d{2}", dt):
            return dt[:10]
    for pattern, _ in DATE_PATTERNS:
        m = re.search(pattern, html)
        if m:
            return m.group(1)
    return None


def article_paragraphs(soup: BeautifulSoup, min_len: int = 80) -> list[str]:
    """Paragraphs of the article body, in page order, without captions or nav."""
    node = _main_node(soup)
    paragraphs: list[str] = []
    for p in node.find_all("p"):
        if p.find_parent(["figure", "figcaption", "nav", "aside", "footer"]):
            continue
        text = clean_text(p.get_text(" "))
        if len(text) >= min_len and not text.lower().startswith(("image credit", "credit:", "caption:")):
            paragraphs.append(text)
    return paragraphs


def article_text(soup: BeautifulSoup) -> str:
    """Primary article text as one normalised string."""
    return clean_text(" ".join(article_paragraphs(soup)))


def json_ld(soup: BeautifulSoup) -> dict[str, Any]:
    """First JSON-LD block on the page, if any."""
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    return item
        elif isinstance(data, dict):
            return data
    return {}


def parse_iso_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None
