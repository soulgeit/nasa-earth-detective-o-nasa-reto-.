# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""Tests del conector NASA POWER contra las dos muestras reales (sin red)."""

import json
import os

import pytest

from src.etl import power
from src.etl.errors import DataUnavailable

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.join(os.path.dirname(HERE), "fixtures", "real")
POINT = os.path.join(REAL, "power_monthly_point_lima.json")
REGIONAL = os.path.join(REAL, "power_monthly_regional_piura_T2M.json")


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# parsing de muestras reales
# --------------------------------------------------------------------------- #
def test_parse_point_real_fixture():
    doc = load(POINT)
    parsed = power.parse_point_response(doc, "T2M")
    assert parsed["unit"] == "C"
    assert parsed["fill"] == -999.0
    # 45 anios * 12 meses; la clave YYYY13 (anual) se descarta.
    assert len(parsed["dates"]) == 540
    assert parsed["dates"][0] == "1981-01"
    assert parsed["dates"][-1] == "2025-12"
    assert parsed["values"][0] == 18.41
    assert not any(d.endswith("-13") for d in parsed["dates"])


def test_parse_point_real_fixture_has_nulls_not_minus_999():
    doc = load(POINT)
    parsed = power.parse_point_response(doc, "AOD_55")
    # AOD_55: relleno de 1981-01 a 2000-12 (240 meses) segun el README de fixtures.
    nulls = [v for v in parsed["values"] if v is None]
    assert len(nulls) == 240
    assert -999.0 not in parsed["values"]
    # El primer dato real aparece en 2001-01.
    first_real = next(i for i, v in enumerate(parsed["values"]) if v is not None)
    assert parsed["dates"][first_real] == "2001-01"


def test_annual_key_13_discarded_explicitly():
    doc = {"header": {"fill_value": -999.0}, "parameters": {"T2M": {"units": "C"}},
           "properties": {"parameter": {"T2M": {"202001": 1.0, "202002": 2.0, "202013": 99.0}}}}
    parsed = power.parse_point_response(doc, "T2M")
    assert parsed["dates"] == ["2020-01", "2020-02"]
    assert parsed["values"] == [1.0, 2.0]


def test_bad_parameter_raises_variable_unknown():
    doc = load(POINT)
    with pytest.raises(DataUnavailable) as exc:
        power.parse_point_response(doc, "NOT_A_PARAM")
    assert exc.value.code == "VARIABLE_UNKNOWN"


def test_parse_regional_real_fixture():
    doc = load(REGIONAL)
    parsed = power.parse_regional_response(doc, "T2M")
    assert len(parsed["cells"]) == 63
    lats = {c["lat"] for c in parsed["cells"]}
    lons = {c["lon"] for c in parsed["cells"]}
    assert lats == {-7.0, -6.5, -6.0, -5.5, -5.0, -4.5, -4.0, -3.5, -3.0}
    assert len(lons) == 7
    cell = next(c for c in parsed["cells"] if c["lat"] == -7.0 and c["lon"] == -81.875)
    assert cell["values"][0] == 22.51
    assert len(cell["dates"]) == 540


# --------------------------------------------------------------------------- #
# media ponderada por cos(lat)
# --------------------------------------------------------------------------- #
def test_coslat_weighted_mean():
    grid = {
        "dates": ["2020-01"],
        "cells": [
            {"lat": 0.0, "lon": 0.0, "values": [10.0]},
            {"lat": 60.0, "lon": 0.0, "values": [20.0]},
        ],
    }
    means, cover = power._coslat_mean(grid)
    assert cover == [2]
    expected = (10.0 * 1.0 + 20.0 * 0.5) / (1.0 + 0.5)
    assert means[0] == pytest.approx(expected, abs=1e-6)


def test_coslat_mean_skips_missing_cells():
    grid = {
        "dates": ["2020-01", "2020-02"],
        "cells": [
            {"lat": 0.0, "lon": 0.0, "values": [10.0, None]},
            {"lat": 60.0, "lon": 0.0, "values": [None, 20.0]},
        ],
    }
    means, cover = power._coslat_mean(grid)
    assert means[0] == pytest.approx(10.0)
    assert means[1] == pytest.approx(20.0)
    assert cover == [1, 1]


def test_coslat_mean_all_missing_is_null():
    grid = {"dates": ["2020-01"], "cells": [{"lat": 10.0, "lon": 0.0, "values": [None]}]}
    means, cover = power._coslat_mean(grid)
    assert means == [None]
    assert cover == [0]


# --------------------------------------------------------------------------- #
# troceo de cajas y limites verificados
# --------------------------------------------------------------------------- #
def test_tiles_respect_ten_degree_limit():
    tiles = power._tiles([-75.0, -15.0, -45.0, 15.0])
    assert len(tiles) == 9  # 30x30 grados -> 3x3 teselas
    for west, south, east, north in tiles:
        assert north - south <= power.REGIONAL_MAX_DEGREES + 1e-9
        assert east - west <= power.REGIONAL_MAX_DEGREES + 1e-9


def test_tiles_single_small_box():
    tiles = power._tiles([-82.0, -7.0, -78.0, -3.0])
    assert tiles == [(-82.0, -7.0, -78.0, -3.0)]


def test_tiles_cover_whole_bbox():
    bbox = [-70.0, 10.0, -55.0, 20.0]
    tiles = power._tiles(bbox)
    assert min(t[0] for t in tiles) == pytest.approx(bbox[0])
    assert max(t[2] for t in tiles) == pytest.approx(bbox[2])
    assert min(t[1] for t in tiles) == pytest.approx(bbox[1])
    assert max(t[3] for t in tiles) == pytest.approx(bbox[3])


def test_point_url_has_required_arguments():
    url = power.point_url("T2M", -12.05, -77.03, "1981-01", "2025-12")
    assert url.startswith("https://power.larc.nasa.gov/api/temporal/monthly/point?")
    for part in ("parameters=T2M", "community=AG", "latitude=-12.05", "longitude=-77.03",
                 "start=1981", "end=2025", "format=JSON"):
        assert part in url


def test_unknown_variable_raises_before_network():
    with pytest.raises(DataUnavailable) as exc:
        power.series("NOT_IN_CATALOG", lat=0, lon=0)
    assert exc.value.code == "VARIABLE_UNKNOWN"


def test_missing_coordinates_raises():
    with pytest.raises(DataUnavailable) as exc:
        power.series("T2M")
    assert exc.value.code == "OUT_OF_COVERAGE"


# --------------------------------------------------------------------------- #
# adaptadores de compatibilidad que usa el motor v2 (src/api/main.py)
# --------------------------------------------------------------------------- #
def test_year_to_month_accepts_all_shapes():
    assert power._year_to_month(2000) == "2000-01"
    assert power._year_to_month("2000") == "2000-01"
    assert power._year_to_month(202412) == "2024-12"
    assert power._year_to_month("2024-12") == "2024-12"
    assert power._year_to_month(None) is None


def test_period_end_year_means_december():
    # Bug real: "2024-12" mide 7 caracteres y caia en la rama de ano -> 2024-01.
    assert power._period(2000, 2024) == ("2000-01", "2024-12")
    assert power._period(2000, "2024-12") == ("2000-01", "2024-12")
    assert power._period(2000, 202412) == ("2000-01", "2024-12")
    assert power._period(2000, None) == ("2000-01", None)


def test_compat_wrapper_signature_matches_motor():
    assert callable(power.get_power_grid)
