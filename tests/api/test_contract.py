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
    """Cliente con los dobles de prueba leyendo `tests/fixtures/real/`.

    Fuerza el ETL ausente: si el módulo real está fusionado gana siempre, y
    estas pruebas existen justo para cubrir el camino de respaldo.
    """
    from src.api import cache, modules

    monkeypatch.setenv("ALLOW_FIXTURES", "1")
    monkeypatch.setattr(modules, "_try_import", lambda name: (None, f"disabled for fixture test: {name}"))
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


def test_series_endpoint_serves_real_power_data(client: TestClient) -> None:
    """Con el ETL fusionado, `/api/series` devuelve datos de POWER con su procedencia.

    Sin red este servicio responde 503/504: el contrato prohíbe servir un
    fixture disfrazado de `nasa_api` para «que pase la prueba».
    """
    r = client.get("/api/series", params={"variable_id": "T2M", "lat": -12.05, "lon": -77.03})

    if r.status_code in {503, 504}:
        _assert_error_shape(r.json())
        assert r.json()["error"]["code"] in {"DATA_UNAVAILABLE", "UPSTREAM_TIMEOUT", "UPSTREAM_ERROR"}
        pytest.skip("NASA POWER inaccesible en este entorno (sin red y sin caché).")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema"] == "timeseries/2"
    assert body["provenance"]["kind"] == "nasa_api"
    assert len(body["data"]) == 540
    assert body["data"][0] == {"date": "1981-01", "value": 18.41}


def test_fixture_mode_series_is_explicitly_fixture(fixture_client: TestClient) -> None:
    r = fixture_client.get("/api/series", params={"variable_id": "T2M", "lat": -12.05, "lon": -77.03})
    assert r.status_code == 200
    body = r.json()
    assert body["schema"] == "timeseries/2"
    assert body["provenance"]["kind"] == "fixture"
    assert len(body["data"]) == 540
    assert body["data"][0] == {"date": "1981-01", "value": 18.41}


def test_fixture_mode_rejects_other_variables(fixture_client: TestClient) -> None:
    """Un id real del catálogo que la muestra local no cubre no se inventa."""
    r = fixture_client.get("/api/series", params={"variable_id": "GISTEMP_TANOM", "lat": 80, "lon": 0})
    assert r.status_code == 503
    _assert_error_shape(r.json())
    assert r.json()["error"]["code"] == "DATA_UNAVAILABLE"


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


# --- UI servida por el mismo servicio (A5) --------------------------------


def test_ui_is_served_from_root_with_relative_assets(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert r.headers["cache-control"] == "no-cache"


def test_ui_assets_are_served_with_the_right_media_type(client: TestClient) -> None:
    r = client.get("/app.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert "max-age" in r.headers["cache-control"]


def test_missing_asset_is_json_404_not_html(client: TestClient) -> None:
    """Un 200 con HTML donde el navegador espera JS rompe la página en silencio."""
    r = client.get("/nope.js")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_api_routes_win_over_the_spa_fallback(client: TestClient) -> None:
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/does-not-exist").status_code == 404


def test_unknown_page_falls_back_to_the_spa(client: TestClient) -> None:
    r = client.get("/some/deep/link")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


# --- Ronda 3: variables sin lugar, nombre del lugar, eco del id -----------


def test_placeless_variables_need_no_coordinates(client: TestClient) -> None:
    """GISTEMP y el hielo marino son globales/hemisféricos: pedir lat/lon es un 400 artificial."""
    for variable_id in ("GISTEMP_TANOM", "SEAICE_EXTENT_N", "SEAICE_EXTENT_S"):
        r = client.get("/api/analyze", params={"variable_id": variable_id})
        assert r.status_code == 200, f"{variable_id}: {r.text[:200]}"
        body = r.json()
        assert body["region"]["name"], f"{variable_id} sin nombre de región"
        assert body["period"]["n_obs"] > 0


def test_variable_with_place_still_requires_coordinates(client: TestClient) -> None:
    """El cambio anterior no puede relajar las variables que sí son locales."""
    r = client.get("/api/analyze", params={"variable_id": "T2M"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_REQUEST"


def test_place_reaches_the_answer_text(client: TestClient) -> None:
    """`place` (lo que devuelve /api/geocode) sustituye al «None» del ETL."""
    r = client.get(
        "/api/analyze",
        params={"variable_id": "T2M", "lat": -12.05, "lon": -77.03, "place": "Lima, Peru"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["region"]["name"] == "Lima, Peru"
    assert "Lima" in body["answers"]["where"]["en"]
    assert "None" not in body["answers"]["where"]["en"]


def test_series_endpoint_accepts_place(client: TestClient) -> None:
    r = client.get(
        "/api/series",
        params={"variable_id": "T2M", "lat": -12.05, "lon": -77.03, "place": "Lima, Peru"},
    )
    if r.status_code in {503, 504}:
        pytest.skip("NASA POWER inaccesible en este entorno.")
    assert r.status_code == 200, r.text
    assert r.json()["region"]["name"] == "Lima, Peru"


def test_trendmap_echoes_the_requested_variable_id(client: TestClient) -> None:
    """El motor ponía `"VAR"` cuando la rejilla no traía id (RONDA_3 §2.5)."""
    r = client.get("/api/trendmap", params={"variable_id": "T2M", "bbox": "-82,-7,-78,-3"})
    if r.status_code in {503, 504}:
        pytest.skip("POWER regional inaccesible en este entorno.")
    assert r.status_code == 200, r.text
    assert r.json()["variable_id"] == "T2M"


def test_catalog_publishes_availability_flags(client: TestClient) -> None:
    """`planned` y `available` explícitos: la UI no debe adivinar qué se puede analizar."""
    r = client.get("/api/catalog/variables", params={"lang": "en"})
    assert r.status_code == 200
    variables = r.json()["variables"]
    assert variables
    for card in variables:
        assert isinstance(card.get("available"), bool), card.get("id")
        assert isinstance(card.get("planned"), bool), card.get("id")


# --- Ronda 4: regla 19, una planned nunca se analiza -----------------------


def test_planned_variables_published_apart(monkeypatch) -> None:
    from src.api import catalog as cat
    import src.api.main as main_mod

    cards = cat.all_variables() + [{
        "id": "GPM_IMERG_PRECIP",
        "connector": "giovanni_csv",
        "connector_param": "precip",
        "names": {"es": "Precipitación GPM", "en": "GPM precipitation"},
        "available": False,
        "planned": True,
        "unit": "mm/day",
        "_catalog_source": "catalog",
    }]
    monkeypatch.setattr(cat, "all_variables", lambda: cards)
    main_mod.catalog.reload()

    r = TestClient(main_mod.app).get("/api/catalog/variables", params={"lang": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["catalog"]["n_available"] == len(body["variables"])
    assert body["catalog"]["n_planned"] == len(body["planned"])
    planned_ids = {v["id"] for v in body["planned"]}
    avail_ids = {v["id"] for v in body["variables"]}
    assert "GPM_IMERG_PRECIP" in planned_ids
    assert "GPM_IMERG_PRECIP" not in avail_ids


def test_analyze_rejects_a_planned_variable(monkeypatch) -> None:
    from src.api import catalog as cat
    import src.api.main as main_mod

    cards = cat.all_variables() + [{
        "id": "MODIS_LST_DAY",
        "connector": "giovanni_csv",
        "connector_param": "lst",
        "names": {"es": "Temperatura MODIS", "en": "MODIS temperature"},
        "available": False,
        "planned": True,
        "unit": "K",
        "_catalog_source": "catalog",
    }]
    monkeypatch.setattr(cat, "all_variables", lambda: cards)
    main_mod.catalog.reload()

    client = TestClient(main_mod.app)
    for path in ("/api/analyze", "/api/series"):
        r = client.get(path, params={"variable_id": "MODIS_LST_DAY"})
        assert r.status_code == 409, f"{path}: {r.text[:150]}"
        err = r.json()["error"]
        assert err["code"] == "VARIABLE_PLANNED"
        assert "Giovanni" in err["message"]["en"]

    # En el idioma pedido
    r = client.get("/api/report", params={"variable_id": "MODIS_LST_DAY", "lang": "es"})
    assert r.status_code == 409
    assert "Giovanni" in r.json()["error"]["message"]["es"]


# --- caso congelado completo (arquitecto, Ronda 5) ---------------------------

def test_frozen_case_is_served_as_it_was_frozen(client: TestClient) -> None:
    """La galeria abre el caso guardado: mismas cifras que el archivo, sin recalcular."""
    import json as _json

    from src.api.config import CASES_DIR

    listing = client.get("/api/cases")
    if listing.status_code == 503:
        pytest.skip("no hay casos congelados en esta rama")
    cases = listing.json()["cases"]
    assert cases, "el indice de casos esta vacio"
    for case in cases:
        r = client.get(f"/api/cases/{case['id']}")
        assert r.status_code == 200, (case["id"], r.text[:200])
        body = r.json()
        assert body["case"]["id"] == case["id"]
        analysis = body["analysis"]
        on_disk = _json.loads((CASES_DIR / case["id"] / "analysis.json").read_text(encoding="utf-8"))
        assert analysis["schema"] == "analysis/2"
        # Lo congelado no se toca: tendencia, veredicto, serie y procedencia son los del archivo.
        for key in ("trend", "significance", "tests", "series", "provenance", "period"):
            assert analysis[key] == on_disk[key], (case["id"], key)
        # Lo unico que se anade es rotulo: la tarjeta del catalogo y el nombre del lugar.
        assert analysis["variable"]["id"] == case["variable_id"]
        assert analysis["region"].get("name")
        # Regla 12: ningun valor centinela llega a la pantalla.
        raw = [v for v in analysis["series"]["raw"] if v is not None]
        assert min(raw) > -900, (case["id"], min(raw))


def test_unknown_frozen_case_is_a_contract_error(client: TestClient) -> None:
    if client.get("/api/cases").status_code == 503:
        pytest.skip("no hay casos congelados en esta rama")
    for bad in ("no-such-case", "..%2F..%2Frequirements.txt", "lima-t2m%2F..%2F..%2F..%2FREADME.md"):
        r = client.get(f"/api/cases/{bad}")
        assert r.status_code == 404, (bad, r.status_code)
        _assert_error_shape(r.json())
        assert r.json()["error"]["code"] == "NOT_FOUND"


# --- la seccion `planned` del catalogo REAL (arquitecto, Ronda 5) ------------
# Las dos pruebas de arriba inyectan una tarjeta planned de mentira. Con el
# archivo real la API publicaba 0 planned y respondia VARIABLE_UNKNOWN: el
# catalogo las guarda en una clave aparte (`planned`) que el cargador no leia.

def _real_planned_ids() -> list[str]:
    import json as _json

    from src.api.catalog import CATALOG_PATH

    if not CATALOG_PATH.exists():
        return []
    raw = _json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [v["id"] for v in (raw.get("planned") or []) if isinstance(v, dict) and v.get("id")]


def test_real_catalog_planned_section_is_published(client: TestClient) -> None:
    planned_ids = _real_planned_ids()
    if not planned_ids:
        pytest.skip("el catalogo de esta rama no trae seccion planned")
    body = client.get("/api/catalog/variables", params={"lang": "en"}).json()
    published = {v["id"] for v in body["planned"]}
    assert published == set(planned_ids)
    assert body["catalog"]["n_planned"] == len(planned_ids)
    available = {v["id"] for v in body["variables"]}
    assert not (published & available)
    for card in body["planned"]:
        assert card["planned"] is True and card["available"] is False, card["id"]


def test_real_planned_variable_is_refused_with_how_to_load_it(client: TestClient) -> None:
    planned_ids = _real_planned_ids()
    if not planned_ids:
        pytest.skip("el catalogo de esta rama no trae seccion planned")
    for vid in planned_ids:
        r = client.get("/api/analyze", params={"variable_id": vid, "lat": -12.05, "lon": -77.03})
        assert r.status_code == 409, (vid, r.status_code, r.text[:160])
        err = r.json()["error"]
        assert err["code"] == "VARIABLE_PLANNED", vid
        assert "Giovanni" in err["message"]["en"]
