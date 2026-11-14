# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""Tests de cache, HTTP y errores del ETL."""

import json
import os
import time

import pytest

from src.etl import cache
from src.etl.errors import CODES, DataUnavailable


def test_cache_roundtrip(tmp_path):
    directory = str(tmp_path)
    assert cache.load("https://x/y", directory=directory) is None
    meta = cache.store("https://x/y", b'{"a":1}', status=200, directory=directory)
    assert len(meta["sha256"]) == 64
    assert meta["bytes"] == 7
    hit = cache.load("https://x/y", directory=directory)
    assert hit is not None
    assert hit["body"] == b'{"a":1}'
    assert hit["meta"]["status"] == 200


def test_cache_key_is_url_hash():
    assert cache.cache_key("https://x/y") != cache.cache_key("https://x/z")
    assert len(cache.cache_key("https://x/y")) == 64


def test_cache_expires_after_ttl(tmp_path):
    directory = str(tmp_path)
    now = time.time()
    cache.store("https://x/y", b"body", status=200, directory=directory, fetched_at_epoch=now)
    assert cache.load("https://x/y", directory=directory, now=now + 10 * 86400) is not None
    assert cache.load("https://x/y", directory=directory, now=now + 31 * 86400) is None


def test_cache_stores_raw_bytes(tmp_path):
    directory = str(tmp_path)
    raw = b'{"keep": "exact\\u00e1"}'
    cache.store("https://x/raw", raw, status=200, directory=directory)
    assert cache.load("https://x/raw", directory=directory)["body"] == raw


def test_cache_missing_sidecar_is_a_miss(tmp_path):
    directory = str(tmp_path)
    cache.store("https://x/y", b"body", status=200, directory=directory)
    key = cache.cache_key("https://x/y")
    os.remove(os.path.join(directory, key + ".meta.json"))
    assert cache.load("https://x/y", directory=directory) is None


def test_dataunavailable_codes():
    assert "UPSTREAM_TIMEOUT" in CODES
    with pytest.raises(ValueError):
        DataUnavailable("NOPE")
    err = DataUnavailable("OUT_OF_COVERAGE", "detalle")
    assert err.code == "OUT_OF_COVERAGE"
    assert "detalle" in str(err)
