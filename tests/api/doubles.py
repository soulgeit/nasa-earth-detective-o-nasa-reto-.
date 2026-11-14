# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Dobles de prueba para la API.

No son datos de demostración ni un ETL de mentira que pueda colarse en
producción: solo existen dentro de `tests/` y la API solo los usa cuando la
prueba los inyecta a mano en el resolvedor. Sirven para ejercitar la
orquestación (`service.py`) mientras los carriles de datos y estadística no han
empujado sus módulos reales.
"""

from __future__ import annotations

from typing import Any


class DataUnavailable(Exception):
    """Reproduce el contrato §6: `DataUnavailable.code`."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


#: Comportamiento por `variable_id` (todos son ids reales del catálogo, porque la
#: API valida el catálogo antes de llegar al ETL). Vacío = serie normal.
BEHAVIOR: dict[str, str] = {}

#: Ids reales del catálogo que usan los tests.
UPSTREAM_FAIL = "PRECTOTCORR"   # POWER caído
SWAPS_VARIABLE = "TS"           # devuelve datos de otra variable
SHORT_RECORD = "RH2M"           # menos de 24 meses
EMPTY = "TO3"                   # serie vacía


def _series(variable_id: str, values: list[float | None], start_year: int = 2000) -> dict[str, Any]:
    data = []
    for i, value in enumerate(values):
        year = start_year + i // 12
        month = i % 12 + 1
        data.append({"date": f"{year:04d}-{month:02d}", "value": value})
    return {
        "schema": "timeseries/2",
        "variable_id": variable_id,
        "unit": "°C",
        "cadence": "monthly",
        "region": {"kind": "point", "name": "Test Point", "lat": -12.05, "lon": -77.03, "bbox": None},
        "aggregation": "point",
        "data": data,
        "provenance": {
            "kind": "nasa_api",
            "source": "NASA POWER v2.10.0",
            "underlying": "MERRA-2",
            "request_url": "https://power.larc.nasa.gov/api/temporal/monthly/point?test",
            "retrieved_at": "2026-11-14T17:22:00Z",
            "sha256": "0123456789abcdef",
            "native_resolution": "0.5° x 0.625°",
            "citation": "Data: NASA POWER",
        },
    }


def get_series(
    variable_id: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    bbox: list[float] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """Serie normal, salvo que el test active un comportamiento para ese id."""
    mode = BEHAVIOR.get(variable_id)
    if mode == "unknown":
        raise DataUnavailable("VARIABLE_UNKNOWN", variable_id)
    if mode == "swaps_variable":
        # Devuelve a propósito otra variable: la API debe rechazarlo, no corregirlo.
        return _series("T2M", [float(i % 12) for i in range(36)])
    if mode == "short":
        return _series(variable_id, [1.0, 2.0, 3.0])
    if mode == "empty":
        return _series(variable_id, [])
    if mode == "upstream_timeout":
        raise DataUnavailable("UPSTREAM_TIMEOUT", "power.larc.nasa.gov")
    values = [10.0 + 0.05 * i + (i % 12) * 0.4 for i in range(240)]
    series = _series(variable_id, values)
    if start or end:
        series["data"] = [p for p in series["data"] if (not start or p["date"] >= start) and (not end or p["date"] <= end)]
        if not series["data"]:
            raise DataUnavailable("OUT_OF_COVERAGE", f"{start}..{end}")
    return series


def get_grid(variable_id: str, bbox: list[float], *, start: str | None = None, end: str | None = None):
    if variable_id == "EMPTY":
        raise DataUnavailable("OUT_OF_COVERAGE", "empty grid")
    return {
        "lats": [-5.0, -4.5],
        "lons": [-80.0, -79.0],
        "dates": ["2000-01", "2000-02"],
        "values": [[[1.0, 2.0], [3.0, 4.0]], [[1.1, 2.1], [3.1, 4.1]]],
        "unit": "°C",
        "provenance": {"kind": "nasa_api", "source": "NASA POWER regional"},
    }


def parse_giovanni_csv(text: str, variable_id: str | None = None) -> dict[str, Any]:
    lines = [ln for ln in text.strip().splitlines() if ln.strip() and not ln.startswith("#")]
    values: list[float | None] = []
    for line in lines[1:]:
        parts = line.split(",")
        values.append(None if parts[1].strip() in {"", "nan", "-999"} else float(parts[1]))
    series = _series(variable_id or "GPM_IMERG_PRECIP", values, start_year=2000)
    series["provenance"]["kind"] = "user_upload"
    return series


# --- motor estadístico -----------------------------------------------------


def analyze_series(ts: dict[str, Any], *, alpha: float = 0.05, ratio_scale: bool = False,
                   homogeneous_since: str | None = None) -> dict[str, Any]:
    values = [p["value"] for p in ts["data"] if p["value"] is not None]
    if len(values) < 24:
        exc = Exception("INSUFFICIENT_DATA:needs 24 monthly observations")
        exc.code = "INSUFFICIENT_DATA"  # type: ignore[attr-defined]
        raise exc
    n = len(values)
    mean = sum(values) / n
    xs = [i / 12 for i in range(n)]
    mx = sum(xs) / n
    slope = sum((x - mx) * (y - mean) for x, y in zip(xs, values)) / max(
        sum((x - mx) ** 2 for x in xs), 1e-12
    )
    per_decade = slope * 10
    dates = [p["date"] for p in ts["data"] if p["value"] is not None]
    return {
        "schema": "analysis/2",
        "region": ts["region"],
        "period": {
            "start": dates[0],
            "end": dates[-1],
            "years": round(n / 12, 2),
            "n_obs": n,
            "n_missing": len(ts["data"]) - n,
            "coverage": round(n / len(ts["data"]), 4) if ts["data"] else 0.0,
        },
        "method": {
            "deseasonalized": True,
            "climatology": "monthly mean of the analysed period",
            "alpha": alpha,
            "autocorrelation": {"lag1": 0.1, "n_eff": n},
            "references": ["Mann 1945", "Kendall 1975", "Sen 1968"],
        },
        "trend": {
            "direction": "up" if per_decade > 0 else "down",
            "sen_slope_per_decade": round(per_decade, 4),
            "sen_ci95_per_decade": [round(per_decade * 0.8, 4), round(per_decade * 1.2, 4)],
            "ols_slope_per_decade": round(per_decade, 4),
            "ols_ci95_per_decade": [round(per_decade * 0.7, 4), round(per_decade * 1.3, 4)],
            "r_squared": 0.5,
            "total_change": round(per_decade * n / 12 / 10, 4),
            "percent_per_decade": round(per_decade * 100, 2) if ratio_scale else None,
        },
        "tests": {
            "mann_kendall": {"tau": 0.3, "z": 2.0, "p_value": 0.01, "p_value_autocorr": 0.02, "correction": "hamed_rao"},
            "mann_kendall_annual": {"n": 20, "tau": 0.4, "p_value": 0.005},
            "t_test_ols": {"t": 3.0, "df": n - 2, "p_value": 0.003, "adjusted_for_autocorrelation": True},
        },
        "significance": {"is_significant": True, "verdict_code": "SIGNIFICANT", "level": "p<0.05", "tests_agree": True},
        "detectability": {"years_needed": 10.0, "years_available": round(n / 12, 2), "more_years_needed": 0.0,
                          "method": "Weatherhead et al. 1998"},
        "series": {
            "dates": dates,
            "raw": values,
            "climatology": [round(mean, 4)] * n,
            "anomalies": [round(v - mean, 4) for v in values],
            "trend_line": [round(mean + slope * (x - mx), 4) for x in xs],
            "trend_ci_low": [round(mean + slope * (x - mx) - 1, 4) for x in xs],
            "trend_ci_high": [round(mean + slope * (x - mx) + 1, 4) for x in xs],
            "annual": [],
        },
        "answers": {
            "what": {"es": "la temperatura sube", "en": "temperature rises"},
            "where": {"es": "en el punto", "en": "at the point"},
            "how_much": {"es": f"{per_decade:.2f} por década", "en": f"{per_decade:.2f} per decade"},
            "significant": {"es": "significativo", "en": "significant"},
            "detectability": {"es": "suficientes años", "en": "enough years"},
        },
        "warnings": [],
        "provenance": ts["provenance"],
    }


def analyze_grid(grid: dict[str, Any], *, alpha: float = 0.05, fdr_q: float = 0.10) -> dict[str, Any]:
    n_lat, n_lon = len(grid["lats"]), len(grid["lons"])
    zeros = [[0.01] * n_lon for _ in range(n_lat)]
    return {
        "schema": "trendmap/2",
        "variable_id": "T2M",
        "unit_per_decade": "°C/decade",
        "bbox": [-180.0, -90.0, 180.0, 90.0],
        "lats": grid["lats"],
        "lons": grid["lons"],
        "slope_per_decade": zeros,
        "p_value": [[0.01] * n_lon for _ in range(n_lat)],
        "significant_fdr": [[True] * n_lon for _ in range(n_lat)],
        "fdr_q": fdr_q,
        "n_cells": n_lat * n_lon,
        "n_significant": n_lat * n_lon,
        "period": {"start": grid["dates"][0], "end": grid["dates"][-1]},
        "summary": {"share_up_significant": 1.0, "share_down_significant": 0.0},
        "provenance": grid["provenance"],
    }


def compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    sa = a["trend"]["sen_slope_per_decade"]
    sb = b["trend"]["sen_slope_per_decade"]
    return {
        "opposite": (sa or 0) * (sb or 0) < 0,
        "difference_significant": False,
        "z": 0.5,
        "statement": {"es": "tendencias distintas", "en": "different trends"},
    }


RETURN_WRONG_SCHEMA = False


def analyze_series_wrong_schema(ts: dict[str, Any], **kwargs) -> dict[str, Any]:
    return {"schema": "analysis/1", "bad": True}
