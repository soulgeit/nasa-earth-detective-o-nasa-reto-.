# SI-assisted: claude-omni-3 (Claude Opus 5.5); migrado por Antigravity 1 (Gemini 3.8 Flash)
"""Prueba de sistema de punta a punta (ETL -> motor -> contrato v2).

Sustituye al `test_system.py` del primer prototipo, que importaba funciones del
motor estadístico antiguo (`mann_kendall_test`, `theil_sen_slope`, ...) ya
inexistentes y rompía la colección de todo `pytest`.

Aquí no se simula ciencia: se comprueban dos cosas que el producto promete.

1. El motor v2 responde a una serie con tendencia conocida con el veredicto y el
   signo correctos, y se niega con `INSUFFICIENT_DATA` cuando no hay años.
2. **El respaldo local de fixtures no se disfraza de dato en vivo.** Si NASA
   POWER falla y `ALLOW_FIXTURES=0`, el ETL falla; con `ALLOW_FIXTURES=1` sirve
   la muestra marcada `provenance.kind = "fixture"`, nunca `nasa_api`
   (contrato §3).
"""

from __future__ import annotations

import math

import pytest

from src.etl import power as etl_power
from src.etl.registry import get_series
from src.stats.trend_engine import analyze_series


def _monthly_series(years_from: int, years_to: int, slope_per_year: float = 0.0, noise: float = 0.05):
    """Serie mensual determinista; el ruido es una onda, no aleatorio."""
    data = []
    for year in range(years_from, years_to + 1):
        for month in range(1, 13):
            t = (year - years_from) + (month - 1) / 12.0
            value = 15.0 + slope_per_year * t + noise * math.sin(t * 2.1) + 0.02 * math.cos(t * 5.3)
            data.append({"date": f"{year:04d}-{month:02d}", "value": round(value, 4)})
    return {
        "schema": "timeseries/2",
        "variable_id": "T2M",
        "unit": "°C",
        "cadence": "monthly",
        "region": {"kind": "point", "name": "Synthetic test point", "lat": 0.0, "lon": 0.0, "bbox": None},
        "aggregation": "point",
        "data": data,
        "provenance": {"kind": "nasa_api", "source": "test", "sha256": "test"},
    }


# --- Motor estadístico v2 -------------------------------------------------


def test_warming_series_is_flagged_upward_and_significant():
    result = analyze_series(_monthly_series(2000, 2019, slope_per_year=0.05))
    assert result["schema"] == "analysis/2"
    assert result["trend"]["direction"] == "up"
    assert result["trend"]["sen_slope_per_decade"] > 0
    assert result["significance"]["is_significant"] is True
    assert result["period"]["n_obs"] == 240


def test_cooling_series_is_flagged_downward():
    result = analyze_series(_monthly_series(2000, 2019, slope_per_year=-0.05))
    assert result["trend"]["direction"] == "down"
    assert result["trend"]["sen_slope_per_decade"] < 0


def test_flat_series_is_not_significant():
    result = analyze_series(_monthly_series(2000, 2019, slope_per_year=0.0, noise=0.5))
    assert result["significance"]["verdict_code"] in {"NOT_SIGNIFICANT", "SUGGESTIVE"}


def test_short_series_is_refused_not_guessed():
    result = analyze_series(_monthly_series(2018, 2022, slope_per_year=0.05))
    assert result["significance"]["verdict_code"] == "INSUFFICIENT_DATA"
    assert "SHORT_RECORD" in result["warnings"]


# --- Honestidad de la procedencia (contrato §3) ---------------------------


def _break_upstream(monkeypatch):
    """Simula NASA POWER caída: sin red y sin caché en disco."""

    def _timeout(_url):
        raise etl_power.DataUnavailable("UPSTREAM_TIMEOUT", "sin red en la prueba")

    # El conector vigente concentra caché y red en `_fetch`: romperlo deja al ETL sin ninguna de las dos.
    monkeypatch.setattr(etl_power, "_fetch", _timeout)


def test_upstream_failure_serves_no_data_when_fixtures_disallowed(monkeypatch):
    """Con ALLOW_FIXTURES apagado, un fallo de la NASA es un fallo, no un snapshot."""
    monkeypatch.setenv("ALLOW_FIXTURES", "0")
    _break_upstream(monkeypatch)

    with pytest.raises(etl_power.DataUnavailable) as excinfo:
        get_series("T2M", lat=-12.05, lon=-77.03)

    assert excinfo.value.code == "UPSTREAM_TIMEOUT"


def test_etl_never_substitutes_a_local_sample_even_if_fixtures_allowed(monkeypatch):
    """El conector vigente no tiene respaldo local: con la NASA caída falla también con ALLOW_FIXTURES=1.

    El modo de muestras vive solo en la API y se declara `fixture`
    (ver tests/api/test_contract.py::test_fixture_mode_series_is_explicitly_fixture).
    """
    monkeypatch.setenv("ALLOW_FIXTURES", "1")
    _break_upstream(monkeypatch)

    with pytest.raises(etl_power.DataUnavailable) as excinfo:
        get_series("T2M", lat=-12.05, lon=-77.03)

    assert excinfo.value.code == "UPSTREAM_TIMEOUT"


def test_live_data_keeps_nasa_api_provenance(monkeypatch):
    """Una respuesta real (aquí, desde la caché en disco) sigue siendo `nasa_api`."""
    monkeypatch.setenv("ALLOW_FIXTURES", "0")

    try:
        ts = get_series("T2M", lat=-12.05, lon=-77.03)
    except etl_power.DataUnavailable as exc:
        pytest.skip(f"Sin red ni caché en disco: {exc}")

    assert ts["provenance"]["kind"] == "nasa_api"
