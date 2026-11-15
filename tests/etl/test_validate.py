# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
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
    assert any("relleno" in e or "-999" in e for e in validate_document(doc))


def test_sentinel_fill_and_physical_range_rejected():
    # 1. -9999 rechazado
    doc_fill = good_doc()
    doc_fill["data"][5]["value"] = -9999.0
    errs_fill = validate_document(doc_fill)
    assert any("-9999" in e for e in errs_fill)

    # 2. Hielo marino con valor negativo o fuera de rango físico (0 - 30)
    doc_ice = good_doc(variable_id="SEAICE_EXTENT_N")
    doc_ice["data"][2]["value"] = -0.5
    errs_ice = validate_document(doc_ice)
    assert any("fuera del rango físico" in e for e in errs_ice)

    # 3. Temperatura fuera de rango físico (-90 a 65)
    doc_temp = good_doc(variable_id="T2M")
    doc_temp["data"][3]["value"] = 120.0
    errs_temp = validate_document(doc_temp)
    assert any("fuera del rango físico" in e for e in errs_temp)

    # 4. Viento WS2M fuera de rango físico (0 a 150 m/s)
    doc_wind_neg = good_doc(variable_id="WS2M")
    doc_wind_neg["data"][0]["value"] = -5.0
    assert any("fuera del rango físico" in e for e in validate_document(doc_wind_neg))

    doc_wind_high = good_doc(variable_id="WS2M")
    doc_wind_high["data"][0]["value"] = 250.0
    assert any("fuera del rango físico" in e for e in validate_document(doc_wind_high))

    doc_wind_ok = good_doc(variable_id="WS2M")
    doc_wind_ok["data"][0]["value"] = 12.5
    assert validate_document(doc_wind_ok) == []


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


def test_validator_cli_expands_wildcards_itself(tmp_path):
    """PowerShell y cmd no expanden `*`: el script recibe el patron tal cual (QA D3)."""
    import subprocess
    import sys
    import os

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for name in ("a", "b"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "series.json").write_text(json.dumps(good_doc()), encoding="utf-8")
    pattern = str(tmp_path / "*" / "series.json")
    ok = subprocess.run(
        [sys.executable, "scripts/validate_datasets.py", pattern],
        cwd=root, capture_output=True, text=True,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "2/2" in ok.stdout
    # Un patron que no encuentra nada es un fallo visible, no un exito vacio.
    none = subprocess.run(
        [sys.executable, "scripts/validate_datasets.py", str(tmp_path / "*" / "nothing.json")],
        cwd=root, capture_output=True, text=True,
    )
    assert none.returncode != 0
