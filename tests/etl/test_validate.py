# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""Tests del validador de datasets (esquema timeseries/2)."""

import json

from src.etl.validate import validate_document


def good_doc(**over):
    doc = {
        "schema": "timeseries/2",
        "variable_id": "T2M",
        "unit": "C",
        "cadence": "monthly",
        "region": {"kind": "point", "name": None, "lat": -12.05, "lon": -77.03, "bbox": None},
        "aggregation": "point",
        "data": [{"date": f"{1981 + i // 12:04d}-{i % 12 + 1:02d}", "value": 18.0} for i in range(120)],
        "provenance": {
            "kind": "nasa_api",
            "source": "NASA POWER v2.10.0",
            "request_url": "https://power.larc.nasa.gov/api/temporal/monthly/point?...",
            "retrieved_at": "2026-11-14T17:22:00Z",
            "sha256": "a" * 64,
        },
    }
    doc.update(over)
    return doc


def test_good_document_passes():
    assert validate_document(good_doc()) == []


def test_wrong_schema():
    errors = validate_document(good_doc(schema="timeseries/1"))
    assert any("timeseries/2" in e for e in errors)


def test_fixture_requires_env(monkeypatch):
    monkeypatch.delenv("ALLOW_FIXTURES", raising=False)
    doc = good_doc()
    doc["provenance"]["kind"] = "fixture"
    assert any("fixture" in e for e in validate_document(doc))
    monkeypatch.setenv("ALLOW_FIXTURES", "1")
    assert validate_document(doc) == []


def test_missing_sha256():
    doc = good_doc()
    del doc["provenance"]["sha256"]
    assert any("sha256" in e for e in validate_document(doc))


def test_minus_999_rejected():
    doc = good_doc()
    doc["data"][5]["value"] = -999
    assert any("-999" in e for e in validate_document(doc))


def test_duplicate_and_unordered_dates():
    doc = good_doc()
    doc["data"][10]["date"] = doc["data"][9]["date"]
    assert any("no creciente" in e for e in validate_document(doc))


def test_too_short_series():
    doc = good_doc()
    doc["data"] = doc["data"][:60]
    assert any("minimo 120" in e for e in validate_document(doc))


def test_bad_month():
    doc = good_doc()
    doc["data"][0]["date"] = "1981-13"
    assert any("YYYY-MM" in e for e in validate_document(doc))


def test_nasa_source_requires_url():
    doc = good_doc()
    doc["provenance"]["request_url"] = None
    assert any("request_url" in e for e in validate_document(doc))


def test_validator_cli_exit_codes(tmp_path):
    import subprocess
    import sys
    import os

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    good.write_text(json.dumps(good_doc()), encoding="utf-8")
    broken = good_doc()
    broken["data"] = broken["data"][:3]
    bad.write_text(json.dumps(broken), encoding="utf-8")
    ok = subprocess.run([sys.executable, "scripts/validate_datasets.py", str(good)], cwd=root)
    fail = subprocess.run([sys.executable, "scripts/validate_datasets.py", str(bad)], cwd=root)
    assert ok.returncode == 0
    assert fail.returncode != 0
