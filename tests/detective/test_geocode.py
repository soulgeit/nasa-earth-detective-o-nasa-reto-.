# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Geocoder: exact, accent-free, fuzzy and population tie-breaks (contract R4).

The gazetteer is Hermes 1's deliverable. These tests build a temporary one so the
matching logic is verifiable before that file lands; nothing here is production data.
"""

from __future__ import annotations

import json

import pytest

import src.detective.gazetteer as geo

PLACES = [
    {"name": "Piura", "country": "Peru", "lat": -5.1945, "lon": -80.6328, "population": 484475},
    {"name": "Lima", "country": "Peru", "lat": -12.0464, "lon": -77.0428, "population": 10476000},
    {"name": "Iquitos", "country": "Peru", "lat": -3.7491, "lon": -73.2538, "population": 441649},
    {"name": "San Miguel de Tucumán", "country": "Argentina", "lat": -26.8241, "lon": -65.2226, "population": 548866},
]


@pytest.fixture()
def gazetteer(tmp_path, monkeypatch):
    path = tmp_path / "gazetteer.json"
    path.write_text(json.dumps({"places": PLACES}), encoding="utf-8")
    monkeypatch.setattr(geo, "gazetteer_path", lambda: path)
    geo.reset_cache()
    yield path
    geo.reset_cache()


def test_exact_match(gazetteer):
    result = geo.geocode("Piura")
    assert result and result[0]["name"] == "Piura"
    assert result[0]["lat"] == pytest.approx(-5.1945)


def test_accent_and_case_insensitive(gazetteer):
    assert geo.geocode("PIURA")[0]["name"] == "Piura"
    assert geo.geocode("san miguel de tucuman")[0]["name"].startswith("San Miguel")


def test_fuzzy_match_without_gazetteer(gazetteer):
    result = geo.geocode("Piur")
    assert result and result[0]["name"] == "Piura"


def test_population_breaks_ties(gazetteer, tmp_path, monkeypatch):
    # Two real cities with the same name: the more populated one must win.
    places = [
        {"name": "Riobamba", "country": "EC", "lat": -1.67, "lon": -78.65, "population": 124478},
        {"name": "Riobamba", "country": "PE", "lat": -6.10, "lon": -77.20, "population": 2200000},
    ]
    path = tmp_path / "gaz2.json"
    path.write_text(json.dumps({"cities": places}), encoding="utf-8")
    monkeypatch.setattr(geo, "gazetteer_path", lambda: path)
    geo.reset_cache()
    try:
        result = geo.geocode("Riobamba")
        assert result[0]["country"] == "PE", result
    finally:
        geo.reset_cache()


def test_unknown_place_returns_empty_list(gazetteer):
    """No match must be an empty list: the UI then asks for a map click."""
    assert geo.geocode("Zzzqqq") == []
    assert geo.geocode("") == []


def test_shape_matches_the_contract(gazetteer):
    for place in geo.geocode("Piura"):
        assert {"name", "country", "lat", "lon", "bbox"} <= set(place)


def test_online_lookup_is_opt_in(monkeypatch, gazetteer):
    """Nominatim is only used when AI_GEOCODE_ONLINE=1; tests never hit the network."""
    monkeypatch.delenv("AI_GEOCODE_ONLINE", raising=False)
    assert geo.lookup_online("Piura") == []


def test_find_in_text_returns_literal_span(gazetteer):
    text = "¿está lloviendo menos en Piura?"
    hits = geo.find_in_text(text)
    assert hits and hits[0][1] == "Piura"
    assert hits[0][1] in text


# --- RONDA_2 §6.3: the real GeoNames gazetteer (8109 cities) ----------------
# These use data/catalog/gazetteer.json as published; they are skipped if the
# file is not there so the suite never depends on another lane's file by accident.
import pytest as _pytest


def _has_real_gazetteer() -> bool:
    from src.detective.config import SETTINGS

    return (SETTINGS.catalog_dir / "gazetteer.json").exists()


real = _pytest.mark.skipif(not _has_real_gazetteer(), reason="gazetteer.json not published yet")


@real
def test_real_gazetteer_matches_alt_names():
    from src.detective import gazetteer as real_geo

    real_geo.reset_cache()
    # "Cuzco" is a spelling variant of the official "Cusco".
    result = real_geo.geocode("Cuzco", limit=3)
    assert result and result[0]["name"] == "Cusco", result
    assert result[0]["country"] == "PE"


@real
def test_real_gazetteer_handles_peru_with_country_suffix():
    from src.detective import gazetteer as real_geo

    real_geo.reset_cache()
    assert real_geo.geocode("Lima, Peru")[0]["name"] == "Lima"


@real
def test_real_gazetteer_does_not_answer_a_country_with_a_city():
    from src.detective import gazetteer as real_geo

    real_geo.reset_cache()
    # A city gazetteer has no country polygons; answering would be a lie.
    assert real_geo.geocode("Peru") == []


@real
def test_real_gazetteer_keeps_the_written_span():
    from src.detective import gazetteer as real_geo
    from src.detective.places import extract_places

    real_geo.reset_cache()
    question = "¿hace más calor en Cuzco?"
    places = extract_places(question, limit=2)
    assert places == ["Cuzco"], places   # literal substring, contract §10
    assert places[0] in question


@real
def test_real_gazetteer_speeds():
    """8 109 cities must be usable interactively (once loaded)."""
    import time

    from src.detective import gazetteer as real_geo

    real_geo.reset_cache()
    start = time.perf_counter()
    real_geo.geocode("Piura")
    first = time.perf_counter() - start
    start = time.perf_counter()
    real_geo.geocode("Tumbes")
    second = time.perf_counter() - start
    assert second < 1.0, f"cached lookup too slow: {second:.2f}s (first call {first:.2f}s)"
