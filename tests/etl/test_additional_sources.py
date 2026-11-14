# SI-assisted: Antigravity 1 (Gemini 3.8 Flash); adaptado por Antigravity 1 (Claude Opus 5.5)
"""
Pruebas unitarias para conectores adicionales: NASA GISTEMP v4 y NSIDC Sea Ice Index v4.
Verifica cumplimiento estricto del esquema timeseries/2 y reglas de integridad.
"""

import pytest
from src.etl.registry import get_series as get_gistemp_series
from src.etl.registry import get_series as get_nsidc_series
from src.etl.registry import get_series


@pytest.mark.live
def test_gistemp_series_structure():
    """Verifica que GISTEMP v4 genera una serie válida bajo timeseries/2."""
    res = get_gistemp_series("GISTEMP_TANOM", start="1970-01", end="2024-12")
    assert res["schema"] == "timeseries/2"
    assert res["variable_id"] == "GISTEMP_TANOM"
    assert res["unit"].startswith("°C")
    assert res["cadence"] == "monthly"
    assert res["region"]["kind"] == "named"
    assert res["aggregation"] == "area_mean_coslat"

    data = res["data"]
    assert len(data) == 55 * 12  # 1970 a 2024 = 55 años * 12 = 660 meses
    assert data[0]["date"] == "1970-01"
    assert data[-1]["date"] == "2024-12"

    # Verificar que no hay -999 y que las fechas son estrictamente crecientes
    for i in range(1, len(data)):
        assert data[i]["date"] > data[i - 1]["date"]
        val = data[i]["value"]
        assert val != -999.0
        if val is not None:
            assert isinstance(val, (int, float))

    prov = res["provenance"]
    assert prov["kind"] in ("nasa_api", "nasa_file")
    assert "GISTEMP" in prov["source"]
    assert len(prov["sha256"]) == 64


@pytest.mark.live
def test_nsidc_arctic_and_antarctic_series():
    """Verifica series de hielo marino para Ártico (N) y Antártico (S)."""
    # Ártico
    res_n = get_nsidc_series("SEAICE_EXTENT_N", start="1979-01", end="2024-12")
    assert res_n["schema"] == "timeseries/2"
    assert res_n["variable_id"] == "SEAICE_EXTENT_N"
    assert "km" in res_n["unit"]
    assert "Arctic" in res_n["region"]["name"]
    data_n = res_n["data"]
    assert len(data_n) >= 46 * 12
    # El hielo de septiembre en el ártico suele estar entre 3 y 8 millones de km²
    sept_1979 = [d for d in data_n if d["date"] == "1979-09"][0]
    assert sept_1979["value"] == pytest.approx(7.05, 0.1)

    # Antártico
    res_s = get_nsidc_series("SEAICE_EXTENT_S", start="1979-01", end="2024-12")
    assert res_s["schema"] == "timeseries/2"
    assert res_s["variable_id"] == "SEAICE_EXTENT_S"
    assert "Antarctic" in res_s["region"]["name"]
    data_s = res_s["data"]
    assert len(data_s) >= 46 * 12
    # El hielo antártico en septiembre suele estar entre 17 y 20 millones de km²
    sept_1979_s = [d for d in data_s if d["date"] == "1979-09"][0]
    assert sept_1979_s["value"] == pytest.approx(18.20, 0.1)


@pytest.mark.live
def test_registry_dispatch_gistemp_and_nsidc():
    """Verifica que el dispatcher central src.etl.registry.get_series enruta correctamente."""
    # GISTEMP
    s_gis = get_series("GISTEMP_TANOM", start="1980-01", end="2020-12")
    assert s_gis["variable_id"] == "GISTEMP_TANOM"
    assert s_gis["data"][0]["date"] == "1980-01"
    assert s_gis["data"][-1]["date"] == "2020-12"

    # NSIDC Arctic
    s_arc = get_series("SEAICE_EXTENT_N", start="1980-01", end="2020-12")
    assert s_arc["variable_id"] == "SEAICE_EXTENT_N"
    assert s_arc["data"][0]["date"] == "1980-01"

    # NSIDC Antarctic
    s_ant = get_series("SEAICE_EXTENT_S", start="1980-01", end="2020-12")
    assert s_ant["variable_id"] == "SEAICE_EXTENT_S"
    assert s_ant["data"][0]["date"] == "1980-01"
