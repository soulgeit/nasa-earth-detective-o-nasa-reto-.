# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Pruebas de la API v2: contrato §7, errores y ausencia de sustitución silenciosa."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    """Cliente de pruebas con los módulos reales tal como estén en la rama."""
    from src.api import cache, modules

    monkeypatch.setenv("ALLOW_FIXTURES", "0")
    modules.clear_cache()
    cache.analysis_cache.clear()
    import src.api.main as main_mod

    importlib.reload(main_mod)
    return TestClient(main_mod.app)


@pytest.fixture()
def fixture_client(monkeypatch) -> TestClient:
    """Cliente con los dobles de prueba leyendo `tests/fixtures/real/`."""
    from src.api import cache, modules

    monkeypatch.setenv("ALLOW_FIXTURES", "1")
    modules.clear_cache()
    cache.analysis_cache.clear()
    import src.api.main as main_mod

    importlib.reload(main_mod)
    return TestClient(main_mod.app)


def _assert_error_shape(payload: dict) -> None:
    assert set(payload) == {"error"}
    err = payload["error"]
    assert set(err) >= {"code", "message", "hint"}
    assert isinstance(err["code"], str) and err["code"]
    assert set(err["message"]) == {"es", "en"}
    assert all(isinstance(v, str) and v for v in err["message"].values())
    assert isinstance(err["hint"], str)


def test_health_reports_modules_and_ai_mode(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ai_mode"] in {"full", "extractive", "off"}
    assert set(body["sources_up"]) == {"etl", "stats", "detective"}
    assert body["version"]


def test_catalog_serves_seed_once(client: TestClient) -> None:
    r = client.get("/api/catalog/variables", params={"lang": "en"})
    assert r.status_code == 200
    body = r.json()
    ids = {v["id"] for v in body["variables"]}
    assert {"T2M", "PRECTOTCORR", "GISTEMP_TANOM"} <= ids
    assert body["catalog"]["source"] in {"seed", "catalog"}


def test_unknown_variable_is_404_not_a_substitute(client: TestClient) -> None:
    r = client.get("/api/analyze", params={"variable_id": "NOT_A_VARIABLE", "lat": -12.05, "lon": -77.03})
    assert r.status_code == 404
    _assert_error_shape(r.json())
    assert r.json()["error"]["code"] == "VARIABLE_UNKNOWN"


def test_missing_coordinates_is_400(client: TestClient) -> None:
    r = client.get("/api/analyze", params={"variable_id": "T2M"})
    assert r.status_code == 400
    _assert_error_shape(r.json())
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_without_etl_module_returns_503_never_fixture_data(client: TestClient) -> None:
    """Con ALLOW_FIXTURES apagado y sin ETL real no se sirve ningún dato."""
    r = client.get("/api/series", params={"variable_id": "T2M", "lat": -12.05, "lon": -77.03})
    assert r.status_code == 503
    _assert_error_shape(r.json())
    assert r.json()["error"]["code"] == "DATA_UNAVAILABLE"


def test_fixture_mode_series_is_explicitly_fixture(fixture_client: TestClient) -> None:
    r = fixture_client.get("/api/series", params={"variable_id": "T2M", "lat": -12.05, "lon": -77.03})
    assert r.status_code == 200
    body = r.json()
    assert body["schema"] == "timeseries/2"
    assert body["provenance"]["kind"] == "fixture"
    assert len(body["data"]) == 540
    assert body["data"][0] == {"date": "1981-01", "value": 18.41}


def test_fixture_mode_rejects_other_variables(fixture_client: TestClient) -> None:
    r = fixture_client.get("/api/series", params={"variable_id": "SEAICE_EXTENT_N", "lat": 80, "lon": 0})
    assert r.status_code == 503
    _assert_error_shape(r.json())


@pytest.mark.parametrize(
    "params",
    [
        {"variable_id": "T2M", "lat": 91, "lon": 0},
        {"variable_id": "T2M", "lat": 0, "lon": 181},
        {"variable_id": "T2M", "bbox": "10,0,-10,20"},
        {"variable_id": "T2M", "bbox": "0,20,10,-20"},
        {"variable_id": "T2M", "bbox": "0,0,10"},
        {"variable_id": "T2M", "lat": 0, "lon": 0, "start": "2025-01", "end": "2000-01"},
        {"variable_id": "T2M", "lat": 0, "lon": 0, "start": "2025-13"},
    ],
)
def test_invalid_requests_are_rejected(client: TestClient, params: dict) -> None:
    r = client.get("/api/series", params=params)
    assert r.status_code in {400, 422}
    _assert_error_shape(r.json())


def test_bbox_too_large_is_422(client: TestClient) -> None:
    r = client.get("/api/series", params={"variable_id": "T2M", "bbox": "-170,-80,170,80"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] in {"BBOX_TOO_LARGE", "INVALID_REQUEST"}


def test_ai_endpoints_degrade_cleanly(client: TestClient) -> None:
    r = client.post("/api/ai/plan", params={"question": "is it raining less in Piura?", "lang": "en"})
    assert r.status_code in {503, 200}
    if r.status_code == 503:
        assert r.json()["error"]["code"] == "AI_UNAVAILABLE"


def test_frozen_cases_are_explicitly_unavailable(client: TestClient) -> None:
    r = client.get("/api/cases")
    assert r.status_code in {200, 503}
    if r.status_code == 503:
        _assert_error_shape(r.json())


def test_upload_rejects_binary(client: TestClient) -> None:
    r = client.post(
        "/api/analyze/upload",
        files={"file": ("x.csv", b"\xff\xfe\x00binary", "text/csv")},
    )
    assert r.status_code in {400, 503, 422}
    if r.status_code != 503:
        _assert_error_shape(r.json())


def test_root_serves_ui_or_metadata(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.text
