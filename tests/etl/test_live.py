# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""Tests que llaman de verdad a la NASA (`pytest -m live`).

Se saltan por defecto para que la suite normal sea rapida y offline.
"""

import pytest

from src.etl import registry
from src.etl.errors import DataUnavailable


@pytest.mark.live
def test_live_power_point_lima_matches_d1_acceptance():
    s = registry.get_series("T2M", lat=-12.05, lon=-77.03)
    assert s["schema"] == "timeseries/2"
    assert s["provenance"]["kind"] == "nasa_api"
    assert s["provenance"]["sha256"]
    assert len(s["data"]) == 540
    assert s["data"][0] == {"date": "1981-01", "value": 18.41}
    assert not any(p["value"] == -999 for p in s["data"])


@pytest.mark.live
def test_live_power_regional_box():
    s = registry.get_series("T2M", bbox=[-82, -7, -78, -3])
    assert s["aggregation"] == "area_mean_coslat"
    assert len(s["data"]) == 540


@pytest.mark.live
def test_live_seaice_north_is_declining_but_this_is_not_a_trend_test():
    s = registry.get_series("SEAICE_EXTENT_N")
    assert s["provenance"]["kind"] == "nasa_file"
    assert len(s["data"]) >= 500


@pytest.mark.live
def test_live_gistemp_piura_el_nino():
    s = registry.get_series("GISTEMP_TANOM", bbox=[-82, -7, -78, -3], start="1997-01", end="1998-12")
    values = {p["date"]: p["value"] for p in s["data"]}
    # 1997-98 fue un El Nino fuerte: la anomalia en Piura debe ser positiva y alta.
    assert values["1997-12"] > 2.0


@pytest.mark.live
def test_live_error_code_for_bad_variable():
    with pytest.raises(DataUnavailable):
        registry.get_series("NOPE", lat=0, lon=0)
