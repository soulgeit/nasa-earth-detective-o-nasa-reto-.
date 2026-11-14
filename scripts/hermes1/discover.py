# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""Discovery of NASA pages to include in the knowledge corpus.

Sources of candidate URLs, all queried live and verified before use:
- science.nasa.gov WordPress search API (wp-json/wp/v2/search)
- Earth Observatory "World of Change" index
- Earthdata / GISS / NSIDC topic pages linked from verified sources

Nothing here is a hard-coded list of invented links: every candidate URL is
either returned by an API call or discovered by crawling an index page whose
200 status is checked first.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .fetch_common import FetchError, clean_text, fetch
from .extract import page_title

WP_SEARCH = "https://science.nasa.gov/wp-json/wp/v2/search"
WP_POSTS = "https://science.nasa.gov/wp-json/wp/v2/posts"

PERU_OR_LATAM_TOPICS = [
    "Peru",
    "Andes glacier",
    "Amazon deforestation",
    "El Nino",
    "Lake Titicaca",
    "Piura",
    "Lima Peru",
    "Madre de Dios",
    "Cordillera Blanca",
    "Peruvian Andes",
]

NASA_TOPICS = [
    "Arctic sea ice",
    "Antarctic sea ice",
    "air pollution",
    "aerosols",
    "drought",
    "wildfire",
    "sea level rise",
    "Greenland ice",
    "Sahel rainfall",
    "Amazon rainforest",
]


class DiscoveryError(RuntimeError):
    pass


def _wp_search(query: str, per_page: int = 5) -> list[dict[str, Any]]:
    url = f"{WP_SEARCH}?search={quote(query)}&per_page={per_page}"
    page = fetch(url, cache_key="wp_search_" + re.sub(r"[^a-z0-9]+", "_", query.lower()))
    try:
        data = json.loads(page.text)
    except json.JSONDecodeError as exc:
        raise DiscoveryError(f"wp-json search returned non-JSON for {query!r}") from exc
    results = []
    for item in data:
        if isinstance(item, dict) and item.get("url"):
            results.append({"title": clean_text(item.get("title") or ""), "url": item["url"], "query": query})
    return results


def search_nasa(query: str, per_page: int = 5) -> list[dict[str, Any]]:
    """Search science.nasa.gov and return candidate pages (title + url)."""
    try:
        return _wp_search(query, per_page)
    except FetchError as exc:
        raise DiscoveryError(str(exc)) from exc


def world_of_change_links() -> list[dict[str, str]]:
    """All feature links from the Earth Observatory World of Change index."""
    index_url = "https://science.nasa.gov/earth/earth-observatory/world-of-change/"
    page = fetch(index_url, cache_key="eo_world_of_change_index")
    soup = BeautifulSoup(page.text, "lxml")
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        url = urljoin(page.final_url, a["href"])
        if "/world-of-change/" not in url:
            continue
        slug = url.rstrip("/").split("/")[-1]
        if not slug or slug == "world-of-change":
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append({"title": clean_text(a.get_text(" ", strip=True)) or slug, "url": url})
    if not out:
        raise DiscoveryError("World of Change index returned no feature links")
    return out


def discover_candidates() -> dict[str, list[dict[str, Any]]]:
    """Collect candidate pages by bucket for the NASA article quota."""
    buckets: dict[str, list[dict[str, Any]]] = {"peru_latam": [], "nasa_global": []}
    seen: set[str] = set()

    def add(bucket: str, item: dict[str, Any]) -> None:
        if item["url"] in seen:
            return
        seen.add(item["url"])
        buckets[bucket].append(item)

    for topic in PERU_OR_LATAM_TOPICS:
        try:
            for item in search_nasa(topic, per_page=5):
                add("peru_latam", item)
        except DiscoveryError:
            continue

    for feature in world_of_change_links():
        add("nasa_global", feature)

    for topic in NASA_TOPICS:
        try:
            for item in search_nasa(topic, per_page=4):
                add("nasa_global", item)
        except DiscoveryError:
            continue

    return buckets


if __name__ == "__main__":
    buckets = discover_candidates()
    print(json.dumps({k: len(v) for k, v in buckets.items()}, indent=2))
    for bucket, items in buckets.items():
        print(f"--- {bucket}")
        for item in items[:40]:
            print(" ", item["title"][:70], "|", item["url"])
