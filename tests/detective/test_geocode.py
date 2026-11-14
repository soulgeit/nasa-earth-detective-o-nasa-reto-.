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


def test_population_breaks_ties(gazetteer):
    # "San" prefixes several places; the biggest population must win when scores tie.
    result = geo.geocode("San")
    assert result[0]["name"] == "San Miguel de Tucumán"


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
