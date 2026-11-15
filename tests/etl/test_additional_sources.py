# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
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


def test_nsidc_parse_csv_fill_values_and_satellite_gap():
    """Valida que parse_csv enmascara -9999 y que el hueco satelital (1987-12, 1988-01) resulta en None."""
    from pathlib import Path
    from src.etl.nsidc_seaice import parse_csv

    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "real" / "nsidc_seaice_N_monthly_all.csv"
    assert fixture_path.exists(), f"Fixture no encontrado: {fixture_path}"

    text = fixture_path.read_text(encoding="utf-8")
    rows = parse_csv(text)
    assert len(rows) > 120

    # 1. Ningún valor numérico puede ser negativo (regla 12)
    for r in rows:
        val = r["value"]
        if val is not None:
            assert val >= 0, f"Valor de hielo marino negativo detectado en {r['date']}: {val}"

    # 2. Los meses del hueco satelital (1987-12 y 1988-01) deben tener value is None
    by_date = {r["date"]: r["value"] for r in rows}
    assert "1987-12" in by_date
    assert by_date["1987-12"] is None, f"1987-12 debió ser None, obtuvo {by_date['1987-12']}"
    assert "1988-01" in by_date
    assert by_date["1988-01"] is None, f"1988-01 debió ser None, obtuvo {by_date['1988-01']}"

    # 3. Comprobar formato crudo con -9999 explícito
    raw_sample = (
        "year, mo,source_dataset, region, extent,   area\n"
        "1987, 11,    NSIDC-0051,      N,  11.22,   9.80\n"
        "1987, 12,         -9999,      N, -9999.00, -9999.00\n"
        "1988, 01,         -9999,      N, -9999.00, -9999.00\n"
        "1988, 02,    NSIDC-0051,      N,  15.58,  13.20\n"
    )
    parsed_sample = parse_csv(raw_sample)
    assert len(parsed_sample) == 4
    sample_by_date = {r["date"]: r for r in parsed_sample}
    assert sample_by_date["1987-11"]["value"] == 11.22
    assert sample_by_date["1987-12"]["value"] is None
    assert sample_by_date["1987-12"]["area"] is None
    assert sample_by_date["1987-12"]["source"] is None
    assert sample_by_date["1988-01"]["value"] is None
    assert sample_by_date["1988-02"]["value"] == 15.58


def test_nsidc_underlying_sources_deduplicated_and_spaced(monkeypatch):
    """Valida que underlying y source_splice dividen fuentes compuestas, eliminan repetidos y añaden espacios."""
    from src.etl import nsidc_seaice

    raw_sample = (
        "year, mo,source_dataset, region, extent,   area\n"
        "1987, 01,    NSIDC-0051,      S,  11.22,   9.80\n"
        "1987, 02,    NSIDC-0051,NSIDC-0081, S,  12.34,  10.50\n"
        "1987, 03,    NSIDC-0803,      S,  13.45,  11.20\n"
    )
    # Rellenar 12 meses para pasar el umbral mínimo
    for m in range(4, 13):
        raw_sample += f"1987, {m:02d},    NSIDC-0803,      S,  14.00,  12.00\n"

    def fake_fetch_csv(url):
        # Generar un mes correspondiente
        m_str = url.split("_extent_v4.0.csv")[0][-2:]
        m_int = int(m_str)
        if m_int == 1:
            content = "year, mo,source_dataset, region, extent, area\n1987, 01, NSIDC-0051, S, 11.22, 9.80\n"
        elif m_int == 2:
            content = 'year, mo,source_dataset, region, extent, area\n1987, 02, "NSIDC-0051,NSIDC-0081", S, 12.34, 10.50\n'
        else:
            content = f"year, mo,source_dataset, region, extent, area\n1987, {m_int:02d}, NSIDC-0803, S, 14.00, 12.00\n"
        return content, {"sha256": "fake_hash", "fetched_at": "2026-11-15T00:00:00Z"}

    monkeypatch.setattr(nsidc_seaice, "_fetch_csv", fake_fetch_csv)
    s = nsidc_seaice.series("SEAICE_EXTENT_S")
    prov = s["provenance"]

    assert prov["underlying"] == "NSIDC-0051, NSIDC-0081, NSIDC-0803"
    assert prov["source_splice"] == ["NSIDC-0051", "NSIDC-0081", "NSIDC-0803"]
    assert "NSIDC-0051, NSIDC-0051" not in prov["underlying"]
    assert ",NSIDC" not in prov["underlying"]

