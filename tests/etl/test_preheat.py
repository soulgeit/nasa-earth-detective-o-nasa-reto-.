# SI-assisted: antigravity-1 (Gemini 3.8 Flash)
"""Pruebas unitarias para el script de precalentamiento de cache."""

from unittest.mock import MagicMock, patch

from src.etl.preheat import DEMO_CASES, DEMO_GRIDS, preheat_all


def test_preheat_all_mocked():
    with patch("src.etl.preheat.get_series") as mock_series, patch("src.etl.preheat.get_grid") as mock_grid:
        mock_series.return_value = {
            "schema": "timeseries/2",
            "data": [{"date": "2020-01", "value": 1.0}],
            "provenance": {"kind": "nasa_api", "sha256": "abcdef1234567890"},
        }
        mock_grid.return_value = {
            "dates": ["2020-01"],
            "lats": [0.0],
            "lons": [0.0],
            "values": [[[1.0]]],
        }

        res = preheat_all()
        assert len(res) == len(DEMO_CASES) + len(DEMO_GRIDS)
        for cid in res:
            assert res[cid]["status"] == "ok"
