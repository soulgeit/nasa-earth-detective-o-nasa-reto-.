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
