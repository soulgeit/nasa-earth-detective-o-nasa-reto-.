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


# --------------------------------------------------------------------------
# RONDA_7 — chat y escaneo
# --------------------------------------------------------------------------


def test_benjamini_hochberg_matches_the_textbook_values() -> None:
    from src.api.service import _benjamini_hochberg

    q = _benjamini_hochberg([0.01, 0.04, 0.03, 0.005])
    assert [round(v, 4) for v in q] == [0.02, 0.04, 0.04, 0.02]
    assert _benjamini_hochberg([]) == []
    # un valor q nunca baja del valor p ni pasa de 1
    p = [0.2, 0.9, 0.5]
    assert all(pi <= qi <= 1.0 for pi, qi in zip(p, _benjamini_hochberg(p)))


def test_scan_runs_every_point_variable_and_corrects_for_multiple_tests(wired: TestClient) -> None:
    from src.api import catalog

    r = wired.get("/api/scan", params={"lat": -12.07, "lon": -75.21, "place": "Huancayo"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema"] == "scan/1"
    expected = {c["id"] for c in catalog.all_variables() if not catalog.is_planned(c) and c.get("connector") == "power"}
    assert {row["variable_id"] for row in body["rows"]} == expected
    assert body["n_variables"] == len(expected) >= 30
    assert body["multiple_testing"]["method"] == "Benjamini-Hochberg"
    tested = [row for row in body["rows"] if row["status"] == "ok"]
    assert tested, body["rows"][:2]
    for row in tested:
        assert row["p_value"] <= row["q_value"] <= 1.0
        # confirmada exige las dos cosas: veredicto del motor y valor q
        assert row["confirmed"] == (row["is_significant"] and row["q_value"] < 0.05)
    # las confirmadas van primero
    flags = [row["confirmed"] for row in tested]
    assert flags == sorted(flags, reverse=True)
    # las series globales (GISTEMP, hielo marino) no son de un punto: no entran
    assert "GISTEMP_TANOM" not in expected and "SEAICE_EXTENT_N" not in expected


def test_scan_survives_a_variable_that_fails(wired: TestClient) -> None:
    doubles.BEHAVIOR["WS2M"] = "upstream_timeout"
    doubles.BEHAVIOR["FROST_DAYS"] = "short"
    try:
        r = wired.get("/api/scan", params={"lat": -12.07, "lon": -75.21})
    finally:
        doubles.BEHAVIOR.clear()
    assert r.status_code == 200, r.text
    rows = {row["variable_id"]: row for row in r.json()["rows"]}
    assert rows["WS2M"]["status"] == "error" and rows["WS2M"]["code"] == "UPSTREAM_TIMEOUT"
    assert rows["FROST_DAYS"]["status"] != "ok"
    assert rows["T2M"]["status"] == "ok"
    # lo que falla va al final y no cuenta como prueba hecha
    assert r.json()["n_tested"] == sum(1 for row in rows.values() if row["status"] == "ok")


def test_chat_route_answers_twice_in_a_row(monkeypatch) -> None:
    """Regresión: un submódulo llamado como la función dejaba el chat sin servicio
    a partir del segundo mensaje («src.detective.chat is not importable»)."""
    from src.api import modules

    modules.clear_cache()
    import src.api.main as main_mod

    main_mod.limiter.reset()
    client = TestClient(main_mod.app)
    first = client.post("/api/ai/chat", json={"message": "hola", "lang": "es"})
    assert first.status_code == 200, first.text
    assert first.json()["kind"] == "greeting"
    second = client.post(
        "/api/ai/chat",
        json={"message": "¿y en Huancayo?", "lang": "es", "context": {"place": "Ica", "variable_id": "PRECTOTCORR"}},
    )
    assert second.status_code == 200, second.text
    assert second.json()["plan"]["place"] == "Huancayo"
    assert client.post("/api/ai/chat", json={"nope": 1}).status_code == 400
    bad = client.post("/api/ai/chat", content=b"not json", headers={"content-type": "application/json"})
    assert bad.status_code == 400
    # "hi" ya no es un error de validación en el planificador
    assert client.post("/api/ai/plan", params={"question": "hi", "lang": "en"}).status_code == 200
