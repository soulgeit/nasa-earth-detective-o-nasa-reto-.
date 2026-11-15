# SI-assisted: cfable (Claude Fable 5.2)
"""Tests for the golden cities benchmark dataset and evaluation engine (RONDA_7 §5)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.eval_cities import (
    CITIES,
    GOLDEN_DEFAULT,
    evaluate_cities,
    load_golden_cities,
    matches_city,
    matches_theme,
)
from src.detective.config import SETTINGS

CATALOG_PATH = SETTINGS.data_dir / "catalog" / "variables.json"


def test_golden_cities_file_exists_and_has_60_questions():
    assert GOLDEN_DEFAULT.exists(), f"Golden cities file not found at {GOLDEN_DEFAULT}"
    rows = load_golden_cities(GOLDEN_DEFAULT)
    assert len(rows) == 60, f"Expected exactly 60 questions, got {len(rows)}"


def test_golden_cities_cities_and_themes_coverage():
    rows = load_golden_cities(GOLDEN_DEFAULT)
    city_counts = Counter(r["city"] for r in rows)
    expected_cities = {"lima", "huancayo", "andahuaylas", "ica", "ayacucho"}
    assert set(city_counts.keys()) == expected_cities, f"Cities mismatch: {set(city_counts.keys())}"

    for city, count in city_counts.items():
        assert count == 12, f"City {city} must have exactly 12 questions, got {count}"
        city_rows = [r for r in rows if r["city"] == city]
        themes = {r["theme"] for r in city_rows}
        assert themes == set(range(1, 13)), f"City {city} must cover themes 1 to 12, got {themes}"

        langs = {r["lang"] for r in city_rows}
        assert langs == {"es", "en"}, f"City {city} must contain both 'es' and 'en' questions"


def test_golden_cities_ids_unique_and_valid():
    rows = load_golden_cities(GOLDEN_DEFAULT)
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "All question ids must be unique"
    for r in rows:
        assert r["id"].startswith(f"golden-{r['city']}-"), f"Invalid id prefix: {r['id']}"
        assert len(r["question"]) >= 20, f"Question too short: {r['question']}"
        assert r["expected_places"] == [r["city"]], f"Expected places must match city for {r['id']}"


def test_golden_cities_variables_exist_in_catalogue():
    if not CATALOG_PATH.exists():
        pytest.skip("variables.json catalogue not found")
    cat = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    valid_vars = {v["id"] for v in cat.get("variables", [])}
    valid_vars |= {v["id"] for v in cat.get("planned", [])}

    rows = load_golden_cities(GOLDEN_DEFAULT)
    for r in rows:
        for var_id in r.get("expected_variable_ids", []):
            assert var_id in valid_vars, f"Unknown variable {var_id!r} in question {r['id']}"


def test_matches_city_logic():
    doc_place = {"places": ["huancayo"], "title": "Nota del valle", "text": "Texto sin lugar"}
    assert matches_city(doc_place, "huancayo") is True
    assert matches_city(doc_place, "lima") is False

    doc_id = {"places": [], "id": "region-ica-vientos-01", "title": "Vientos", "text": "Texto"}
    assert matches_city(doc_id, "ica") is True

    doc_text = {"places": [], "id": "res-general", "title": "Estudios en Ayacucho", "text": "Texto"}
    assert matches_city(doc_text, "ayacucho") is True


def test_matches_theme_logic():
    # Direct theme match
    doc_theme = {"theme": 4, "title": "Nota", "text": "Texto"}
    assert matches_theme(doc_theme, 4, []) is True
    assert matches_theme(doc_theme, 5, []) is False

    # Variable intersection match
    doc_var = {"variables": ["PRECTOTCORR"], "title": "Nota", "text": "Texto"}
    assert matches_theme(doc_var, 3, ["PRECTOTCORR", "GPM_IMERG_PRECIP"]) is True

    # Keyword match
    doc_kw = {"variables": [], "title": "Heladas y friajes en la zona", "text": "Temperatura bajo cero"}
    assert matches_theme(doc_kw, 4, ["T2M"]) is True


def test_eval_cities_runner_returns_valid_structure():
    summary = evaluate_cities(k=3, target_city="lima")
    assert "cities" in summary
    assert "total" in summary
    assert "lima" in summary["cities"]
    lima_data = summary["cities"]["lima"]
    assert lima_data["n"] == 12
    assert 0 <= lima_data["hit1"] <= 12
    assert 0 <= lima_data["hit3"] <= 12
    assert 0.0 <= lima_data["precision_at_3"] <= 1.0
