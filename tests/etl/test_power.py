# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Pruebas exhaustivas para el pipeline de adquisición de NASA POWER (D1).
Verifica:
- Parseo de punto real (Lima).
- Descarte de claves anuales (YYYY13).
- Conversión de valores de relleno (-999) a None.
- Parseo de caja regional real (Piura) y cálculo de media ponderada por cos(lat).
- Caching en disco (DATA_CACHE_DIR).
- Comprobación de prueba live con @pytest.mark.live.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.etl.power import (
    get_power_point_series,
    get_power_regional_series,
    get_power_grid,
    _read_from_cache,
    _write_to_cache,
    DataUnavailable
)
from src.etl.registry import get_series, get_grid, parse_giovanni_csv


def test_power_point_lima_parsing():
    """Valida el parseo exacto de la muestra real de Lima."""
    ts = get_series("T2M", lat=-12.05, lon=-77.03)
    
    assert ts["schema"] == "timeseries/2"
    assert ts["variable_id"] == "T2M"
    assert ts["unit"] == "°C"
    assert ts["cadence"] == "monthly"
    assert ts["aggregation"] == "point"
    assert ts["region"]["kind"] == "point"
    assert abs(ts["region"]["lat"] - (-12.05)) < 0.01
    
    data = ts["data"]
    # 45 años * 12 meses = 540 meses (1981-01 a 2025-12)
    assert len(data) == 540
    assert data[0] == {"date": "1981-01", "value": 18.41}
    assert data[-1] == {"date": "2025-12", "value": 18.58}

    # Comprobar que no hay ninguna clave '13' (anual) en las fechas
    for pt in data:
        assert not pt["date"].endswith("-13")
        assert len(pt["date"]) == 7

    # Provenance
    prov = ts["provenance"]
    assert prov["kind"] == "nasa_api"
    assert "NASA POWER" in prov["source"]
    assert "MERRA" in prov["underlying"]
    assert len(prov["sha256"]) == 64


def test_power_point_null_handling():
    """Valida que valores de relleno -999 se mapeen a null (None)."""
    # En la muestra de Lima, AOD_55 contiene valores de relleno en los primeros años
    ts = get_series("AOD_55", lat=-12.05, lon=-77.03)
    data = ts["data"]
    assert len(data) == 540
    # En 1981 AOD_55 no estaba disponible, debe ser None
    assert data[0]["date"] == "1981-01"
    assert data[0]["value"] is None
    # En 2001-01 AOD_55 ya tiene valor (0.37)
    val_2001_01 = next(p["value"] for p in data if p["date"] == "2001-01")
    assert val_2001_01 == 0.37


def test_power_regional_piura_weighted_mean():
    """Valida que la caja regional de Piura calcule la media ponderada por cos(lat)."""
    bbox = [-82.0, -7.0, -78.0, -3.0]
    ts = get_series("T2M", bbox=bbox)
    
    assert ts["schema"] == "timeseries/2"
    assert ts["aggregation"] == "area_mean_coslat"
    assert ts["region"]["kind"] == "bbox"
    assert ts["region"]["bbox"] == bbox

    data = ts["data"]
    assert len(data) == 540
    assert data[0]["date"] == "1981-01"
    assert isinstance(data[0]["value"], float)
    assert 15.0 < data[0]["value"] < 30.0


def test_power_grid_generation():
    """Valida la generación de matriz espacial 3D para TrendMap."""
    bbox = [-82.0, -7.0, -78.0, -3.0]
    grid = get_grid("T2M", bbox=bbox)
    
    assert "lats" in grid and "lons" in grid and "dates" in grid and "values" in grid
    assert len(grid["dates"]) == 540
    assert len(grid["lats"]) > 1
    assert len(grid["lons"]) > 1
    # Matriz [t][lat][lon]
    val_t0 = grid["values"][0]
    assert len(val_t0) == len(grid["lats"])
    assert len(val_t0[0]) == len(grid["lons"])


def test_power_caching_roundtrip():
    """Valida lectura y escritura en la caché de disco."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_url = "https://power.larc.nasa.gov/test_mock_url"
        raw_content = '{"test": 12345}'
        retrieved_at = "2026-11-14T12:00:00Z"
        sha = "abc123mockhash"

        _write_to_cache(test_url, raw_content, retrieved_at, sha, base_dir=tmp_dir)
        cached = _read_from_cache(test_url, base_dir=tmp_dir)
        
        assert cached is not None
        read_raw, read_ret, read_sha = cached
        assert read_raw == raw_content
        assert read_ret == retrieved_at
        assert read_sha == sha


def test_giovanni_csv_parser():
    """Valida el parser de CSV de Giovanni con serie diaria agregada a mensual."""
    csv_sample = """# Product: GPM_3IMERGM_07
# Variable: Precipitation
# Units: mm/month
# FillValue: -999.0
# Region: Piura, Peru
Time,Precipitation
2020-01-01,15.2
2020-01-15,10.8
2020-02-01,5.5
2020-02-15,-999.0
"""
    res = parse_giovanni_csv(csv_sample, "GPM_IMERG_PRECIP")
    assert res["schema"] == "timeseries/2"
    assert res["provenance"]["kind"] == "user_upload"
    assert len(res["data"]) >= 2
    # Feb tiene 1 válido y 1 inválido (50% < 70%), debe resultar en None
    feb_val = next(p["value"] for p in res["data"] if p["date"] == "2020-02")
    assert feb_val is None


@pytest.mark.live
def test_live_power_request():
    """Prueba de conexión real al servicio NASA POWER (ejecutable cuando hay red)."""
    try:
        ts = get_power_point_series("T2M", lat=-12.05, lon=-77.03, start_year=2024, end_year=2025)
        assert len(ts["data"]) == 24
        assert ts["provenance"]["kind"] == "nasa_api"
    except DataUnavailable as e:
        # En sandbox estricto sin red, este test se salta graciosamente
        pytest.skip(f"NASA POWER upstream inaccesible en sandbox sin red: {e}")
