# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""Tests del parser de CSV de Giovanni con un CSV sintetico de formato plausible.

OJO: estos CSV NO son exportaciones reales de Giovanni (no hay ninguna en
`data/raw/giovanni/`). Solo fijan el comportamiento acordado: cabecera antes de
la tabla, relleno, agregacion diaria->mensual con >=70 % de dias. El parser debe
revalidarse contra una exportacion real (tarea D5).
"""

import pytest

from src.etl.giovanni import parse_csv
from src.etl.errors import DataUnavailable

SAMPLE = """# Product: GPM_3IMERGM_07
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


def test_metadata_header_and_units():
    res = parse_csv(SAMPLE, "GPM_IMERG_PRECIP")
    assert res["schema"] == "timeseries/2"
    assert res["provenance"]["kind"] == "user_upload"
    assert res["unit"] == "mm/month"
    assert len(res["provenance"]["header_metadata"]) >= 4


def test_first_data_row_is_not_eaten():
    # El bug original: la primera fila se tomaba como cabecera y se perdia.
    res = parse_csv(SAMPLE, "GPM_IMERG_PRECIP")
    months = {p["date"]: p["value"] for p in res["data"]}
    assert months["2020-01"] == pytest.approx((15.2 + 10.8) / 2)
    # Febrero tiene 1 valido de 2 (50 % < 70 %) -> null explicito, no cero ni interpolado.
    assert months["2020-02"] is None


def test_fill_value_from_header_becomes_null():
    res = parse_csv(SAMPLE, "GPM_IMERG_PRECIP")
    assert all(p["value"] != -999 for p in res["data"])


def test_without_header_raises_instead_of_guessing():
    with pytest.raises(DataUnavailable) as exc:
        parse_csv("2020-01-01,1.0\n2020-01-02,2.0\n", "X")
    assert exc.value.code == "UPSTREAM_ERROR"


def test_empty_raises():
    with pytest.raises(DataUnavailable):
        parse_csv("   ", "X")


def test_monthly_series_kept_as_is():
    text = "# Product: MODIS_NDVI\nTime,NDVI\n2000-01,0.82\n2000-02,0.81\n2000-03,-999.0\n"
    res = parse_csv(text, "MODIS_NDVI")
    assert [p["date"] for p in res["data"]] == ["2000-01", "2000-02", "2000-03"]
    assert res["data"][0]["value"] == 0.82
    assert res["data"][2]["value"] is None


def test_parse_real_giovanni_official_format():
    """Valida el formato oficial de exportación de NASA Giovanni (GES DISC)."""
    raw = '''Title:,"Time Series, Area-Averaged of Bias corrected total surface precipitation monthly 0.5 x 0.625 (monthly)"
User Start Date:,1980-01-01T00:00:00Z
User End Date:,1980-03-31T23:59:59Z
User Bounding Box:,"-71,0.85,-69.84,1.7"
Data Bounding Box:,"-70.625,1,-70,1.5"
URL to Reproduce Results:,"https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs&data=M2TMNXFLX(units%3Dmm%2Fday)&portal=GIOVANNI"
Fill Value (M2TMNXFLX):, 1000000000000000

time, M2TMNXFLX
1980-01-01 00:00:00,7.14807415
1980-02-01 00:00:00,3.67127633
1980-03-01 00:00:00,1000000000000000
'''
    res = parse_csv(raw, "M2TMNXFLX")
    assert res["schema"] == "timeseries/2"
    assert res["unit"] == "mm/day"
    assert res["region"]["bbox"] == [-71.0, 0.85, -69.84, 1.7]
    assert len(res["data"]) == 3
    assert res["data"][0] == {"date": "1980-01", "value": 7.148074}
    assert res["data"][1] == {"date": "1980-02", "value": 3.671276}
    assert res["data"][2] == {"date": "1980-03", "value": None}
    assert res["provenance"]["kind"] == "user_upload"
    assert "giovanni.gsfc.nasa.gov" in res["provenance"]["request_url"]

