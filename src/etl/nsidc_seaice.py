# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Conector NSIDC Sea Ice Index v4 (extension mensual, hemisferios norte y sur).

Formato verificado en vivo el 2026-11-14
(`https://noaadata.apps.nsidc.org/NOAA/G02135/{north|south}/monthly/data/{N|S}_{MM}_extent_v4.0.csv`):

    year, mo,source_dataset, region, extent,   area
    1979,  9,    NSIDC-0051,      N,   7.05,   4.58

- 12 ficheros por hemisferio, uno por mes: se piden todos y se ordenan.
- `extent` en millones de km^2 (la columna `area` es la superficie con hielo).
- La columna `source_dataset` cambia a mitad de serie (NSIDC-0051 -> NSIDC-0803):
  se anota en `provenance` como aviso de continuidad.
"""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timezone

from . import cache, catalog
from .errors import DataUnavailable
from .http import UpstreamError, UpstreamTimeout, get as http_get

BASE = "https://noaadata.apps.nsidc.org/NOAA/G02135"
CACHE_TTL_DAYS = 30.0
CITATION = "NSIDC Sea Ice Index, Version 4; https://nsidc.org/data/g02135"


def _hemisphere(card: dict) -> tuple[str, str]:
    param = str(card.get("connector_param") or "").lower()
    if param.startswith("south") or param == "s":
        return "south", "S"
    return "north", "N"


def _url(hemisphere: str, letter: str, month: int) -> str:
    return f"{BASE}/{hemisphere}/monthly/data/{letter}_{month:02d}_extent_v4.0.csv"


def _fetch_csv(url: str) -> tuple[str, dict]:
    cached = cache.load(url, ttl_days=CACHE_TTL_DAYS)
    if cached is not None:
        body, meta = cached["body"], cached["meta"]
    else:
        try:
            resp = http_get(url)
        except UpstreamTimeout as exc:
            raise DataUnavailable("UPSTREAM_TIMEOUT", f"{url}: {exc}") from exc
        except UpstreamError as exc:
            raise DataUnavailable("UPSTREAM_ERROR", f"{url}: {exc}") from exc
        if resp.status_code != 200:
            raise DataUnavailable("UPSTREAM_ERROR", f"HTTP {resp.status_code} {url}")
        body = resp.content
        meta = cache.store(url, body, status=resp.status_code)
    return body.decode("utf-8", errors="replace"), meta


def parse_csv(text: str) -> list[dict]:
    """Parsea un fichero mensual de NSIDC -> [{'date','value','area','source'}]."""
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        clean = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        try:
            year = int(clean["year"])
            month = int(clean["mo"])
            extent = float(clean["extent"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append(
            {
                "date": f"{year:04d}-{month:02d}",
                "value": extent,
                "area": float(clean.get("area") or "nan"),
                "source": clean.get("source_dataset"),
            }
        )
    return rows


def series(variable_id: str, *, lat=None, lon=None, bbox=None, start=None, end=None) -> dict:
    card = catalog.get_variable(variable_id)
    if card.get("connector") != "nsidc_seaice":
        raise DataUnavailable("VARIABLE_UNKNOWN", f"{variable_id} no es de NSIDC")
    if (lat is not None or lon is not None or bbox is not None) and card.get("region_fixed") is None:
        raise DataUnavailable("OUT_OF_COVERAGE", "NSIDC Sea Ice Index es hemisferico, no por punto")

    hemisphere, letter = _hemisphere(card)
    merged: dict[str, dict] = {}
    hashes: list[str] = []
    retrieved: list[str] = []
    last_meta = None
    for month in range(1, 13):
        url = _url(hemisphere, letter, month)
        text, meta = _fetch_csv(url)
        hashes.append(f"{url.rsplit('/', 1)[-1]}:{meta.get('sha256', '')[:16]}")
        retrieved.append(str(meta.get("fetched_at")))
        last_meta = meta
        for row in parse_csv(text):
            merged[row["date"]] = row
    if not merged:
        raise DataUnavailable("UPSTREAM_ERROR", "NSIDC devolvio CSV vacios")
    dates = sorted(merged)
    if start:
        lo = str(start)[:7]
        dates = [d for d in dates if d >= lo]
    if end:
        hi = str(end)[:7]
        dates = [d for d in dates if d <= hi]
    if len(dates) < 12:
        raise DataUnavailable("OUT_OF_COVERAGE", f"solo {len(dates)} meses entre {start} y {end}")

    sources = sorted({merged[d]["source"] for d in dates if merged[d]["source"]})
    provenance = {
        "kind": "nasa_file",
        "source": "NSIDC Sea Ice Index v4",
        "underlying": ", ".join(sources) if sources else None,
        "request_url": _url(hemisphere, letter, 1),
        "request_urls_pattern": f"{BASE}/{hemisphere}/monthly/data/{letter}_{{MM}}_extent_v4.0.csv",
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": hashlib.sha256("|".join(hashes).encode()).hexdigest(),
        "native_resolution": "hemispheric monthly index",
        "citation": CITATION,
        "files_fetched": len(hashes),
        "files_retrieved_at": retrieved[0] if retrieved else None,
    }
    if len(sources) > 1:
        provenance["source_splice"] = sources
        provenance["source_splice_note"] = (
            "the NSIDC monthly files change source_dataset mid-series; no data were adjusted"
        )
    return {
        "schema": "timeseries/2",
        "variable_id": variable_id,
        "unit": card.get("unit") or "million km2",
        "cadence": "monthly",
        "region": {
            "kind": "named",
            "name": card.get("region_fixed"),
            "lat": None,
            "lon": None,
            "bbox": None,
        },
        "aggregation": "point",
        "data": [{"date": d, "value": merged[d]["value"]} for d in dates],
        "provenance": provenance,
    }
