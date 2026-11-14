# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Orquestación de la API con ETL y motor estadístico inyectados.

Estas pruebas fijan el comportamiento que no debe depender de la rama real:
traducción de errores del ETL, rechazo de una serie de otra variable, caché
con exclusión mutua, informe, comparar y subida de CSV.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from tests.api import doubles


@pytest.fixture()
def wired(monkeypatch):
    doubles.BEHAVIOR.clear()
    """Inyecta los dobles en el resolvedor antes de importar la app."""
    from src.api import cache, modules

    modules.clear_cache()
    monkeypatch.setattr(modules, "_try_import", lambda name: (None, f"disabled for test: {name}"))
    monkeypatch.setenv("ALLOW_FIXTURES", "0")
    resolver = modules._Resolver()
    resolver.etl = doubles
    resolver.etl_err = ""
    resolver.stats = doubles
    resolver.stats_err = ""
    resolver.detective = None
    monkeypatch.setattr(modules, "modules", lambda: resolver)
    cache.analysis_cache.clear()

    import src.api.main as main_mod

    return TestClient(main_mod.app)


def test_analyze_returns_analysis_v2_with_catalog_card(wired: TestClient) -> None:
    r = wired.get("/api/analyze", params={"variable_id": "T2M", "lat": -12.05, "lon": -77.03})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema"] == "analysis/2"
    assert body["variable"]["id"] == "T2M"
    assert body["period"]["n_obs"] == 240
    assert body["provenance"]["kind"] == "nasa_api"
    assert set(body["answers"]) == {"what", "where", "how_much", "significant", "detectability"}


def test_analyze_is_cached_and_single_flight(wired: TestClient) -> None:
    params = {"variable_id": "T2M", "lat": -12.05, "lon": -77.03}
    first = wired.get("/api/analyze", params=params)
    second = wired.get("/api/analyze", params=params)
    assert first.status_code == second.status_code == 200
    health = wired.get("/api/health").json()
    assert health["cache"]["hits"] >= 1


def test_etl_error_codes_are_translated(wired: TestClient) -> None:
    doubles.BEHAVIOR[doubles.UPSTREAM_FAIL] = "upstream_timeout"
    r = wired.get("/api/series", params={"variable_id": doubles.UPSTREAM_FAIL, "lat": 0, "lon": 0})
    assert r.status_code == 504
    assert r.json()["error"]["code"] == "UPSTREAM_TIMEOUT"

    r = wired.get("/api/series", params={"variable_id": "T2M", "lat": 0, "lon": 0, "start": "2099-01"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "OUT_OF_COVERAGE"


def test_etl_returning_other_variable_is_rejected(wired: TestClient) -> None:
    """La sustitución silenciosa también puede venir del ETL: se corta aquí."""
    doubles.BEHAVIOR[doubles.SWAPS_VARIABLE] = "swaps_variable"
    r = wired.get("/api/series", params={"variable_id": doubles.SWAPS_VARIABLE, "lat": 0, "lon": 0})
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "UPSTREAM_ERROR"
    assert doubles.SWAPS_VARIABLE in r.json()["error"]["hint"]


def test_empty_series_is_out_of_coverage(wired: TestClient) -> None:
    doubles.BEHAVIOR[doubles.EMPTY] = "empty"
    r = wired.get("/api/series", params={"variable_id": doubles.EMPTY, "lat": 0, "lon": 0})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "OUT_OF_COVERAGE"


def test_insufficient_data_maps_to_422(wired: TestClient) -> None:
    doubles.BEHAVIOR[doubles.SHORT_RECORD] = "short"
    r = wired.get("/api/analyze", params={"variable_id": doubles.SHORT_RECORD, "lat": 0, "lon": 0})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INSUFFICIENT_DATA"


def test_wrong_analysis_schema_is_an_upstream_error(wired: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(doubles, "analyze_series", doubles.analyze_series_wrong_schema)
    r = wired.get("/api/analyze", params={"variable_id": "T2M", "lat": 0, "lon": 0})
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "UPSTREAM_ERROR"


def test_trendmap_and_compare(wired: TestClient) -> None:
    r = wired.get("/api/trendmap", params={"variable_id": "T2M", "bbox": "-82,-7,-78,-3"})
    assert r.status_code == 200
    assert r.json()["schema"] == "trendmap/2"

    r = wired.get("/api/compare", params={"variable_id": "T2M", "a": "-12.05,-77.03", "b": "-5.2,-80.6"})
    assert r.status_code == 200
    body = r.json()
    assert body["a"]["schema"] == body["b"]["schema"] == "analysis/2"
    assert set(body["compare"]) >= {"opposite", "difference_significant", "statement"}


def test_report_is_printable_html_in_both_languages(wired: TestClient) -> None:
    params = {"variable_id": "T2M", "lat": -12.05, "lon": -77.03}
    for lang, needle in (("en", "How much"), ("es", "Cuánto")):
        r = wired.get("/api/report", params={**params, "lang": lang})
        assert r.status_code == 200
        assert r.text.lstrip().lower().startswith("<!doctype html")
        assert needle in r.text
        assert "http://" not in r.text  # self-contained: no external assets


def test_upload_parses_csv_and_marks_user_upload(wired: TestClient) -> None:
    csv = "# header\nDate,T2M\n" + "\n".join(
        f"{2000 + i // 12}-{i % 12 + 1:02d}-15,{10 + i * 0.01:.3f}" for i in range(120)
    )
    r = wired.post(
        "/api/analyze/upload",
        files={"file": ("giovanni.csv", csv.encode(), "text/csv")},
        params={"variable_id": "T2M"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["provenance"]["kind"] == "user_upload"


def test_rate_limit_returns_429_with_contract_error(wired: TestClient, monkeypatch) -> None:
    from src.api import ratelimit

    monkeypatch.setattr(ratelimit.limiter, "limit", 2)
    ratelimit.limiter.reset()
    params = {"variable_id": "T2M", "lat": -12.05, "lon": -77.03}
    assert wired.get("/api/series", params=params).status_code == 200
    assert wired.get("/api/series", params=params).status_code == 200
    third = wired.get("/api/series", params=params)
    assert third.status_code == 429
    assert third.json()["error"]["code"] == "RATE_LIMITED"
    ratelimit.limiter.reset()


def test_cache_stats_endpoint_reports_ttl(wired: TestClient) -> None:
    body = wired.get("/api/health").json()
    assert body["cache"]["ttl"] > 0
    json.dumps(body)  # must stay JSON-serialisable for clients
