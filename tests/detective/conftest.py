# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Keep the detective's tests hermetic: no network, no model server, extractive mode.

Autouse fixture, so a developer with AI_MODE=full in their .env cannot accidentally
turn the unit suite into a live-model benchmark.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def _hermetic_env(monkeypatch):
    monkeypatch.setenv("AI_MODE", "extractive")
    monkeypatch.setenv("EMBED_MODEL", "")
    from src.detective import config as cfg

    monkeypatch.setattr(cfg, "SETTINGS", cfg.load_settings(), raising=False)
    yield


@pytest.fixture()
def power_fixture():
    """The real NASA POWER sample checked into tests/fixtures/real/ (read-only)."""
    import json

    path = REPO_ROOT / "tests" / "fixtures" / "real" / "power_monthly_point_lima.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def fixture_get_series(power_fixture):
    """Contract-shaped get_series over the real fixture (NOT synthetic data)."""
    def get_series(variable_id, *, lat=None, lon=None, bbox=None, start=None, end=None):
        params = power_fixture["properties"]["parameter"][variable_id]
        data = [
            {"date": f"{k[:4]}-{k[4:6]}", "value": None if v == -999.0 else v}
            for k, v in params.items()
            if not k.endswith("13")
        ]
        return {
            "schema": "timeseries/2",
            "variable_id": variable_id,
            "unit": "°C" if variable_id == "T2M" else "mm/day",
            "cadence": "monthly",
            "region": {"kind": "point", "name": "Lima, Peru", "lat": lat, "lon": lon, "bbox": None},
            "aggregation": "point",
            "data": data,
            "provenance": {
                "kind": "fixture",
                "source": "NASA POWER v2.10.0",
                "request_url": "https://power.larc.nasa.gov/api/temporal/monthly/point?...",
                "retrieved_at": "2026-11-14T17:22:00Z",
            },
        }

    return get_series


@pytest.fixture()
def analysis_result():
    """A minimal AnalysisResult v2 with numbers we can check the guard against.

    Hand-written fixture inside tests/ — allowed by the rules (rule 1 forbids
    invented numbers outside tests/). Values deliberately round and distinct.
    """
    return {
        "schema": "analysis/2",
        "variable": {"id": "T2M", "names": {"es": "Temperatura del aire a 2 m", "en": "Air temperature at 2 m"},
                     "unit": "°C"},
        "region": {"kind": "point", "name": "Lima, Peru", "lat": -12.05, "lon": -77.03, "bbox": None},
        "period": {"start": "1981-01", "end": "2025-12", "years": 45.0, "n_obs": 540, "n_missing": 0,
                   "coverage": 1.0},
        "method": {"alpha": 0.05, "deseasonalized": True},
        "trend": {"direction": "up", "sen_slope_per_decade": 0.31, "sen_ci95_per_decade": [0.22, 0.40],
                  "ols_slope_per_decade": 0.30, "r_squared": 0.28, "total_change": 1.40},
        "tests": {"mann_kendall": {"tau": 0.25, "p_value": 1.1e-09}},
        "significance": {"is_significant": True, "verdict_code": "SIGNIFICANT_STRONG", "level": "p<0.01"},
        "detectability": {"years_needed": 14.2, "years_available": 45.0},
        "answers": {
            "what": {"es": "La temperatura del aire subió 0.31 °C por década.", "en": "Air temperature rose 0.31 °C per decade."},
            "where": {"es": "En Lima, Peru.", "en": "In Lima, Peru."},
            "how_much": {"es": "Cambio total de 1.40 °C en 45 años.", "en": "Total change of 1.40 °C over 45 years."},
            "significant": {"es": "La tendencia es significativa (p<0.01).", "en": "The trend is significant (p<0.01)."},
            "detectability": {"es": "Hay 45 años de datos; se necesitan 14.2.", "en": "45 years of data; 14.2 are needed."},
        },
        "warnings": [],
        "provenance": {"kind": "fixture", "source": "NASA POWER v2.10.0"},
    }
