# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""Tests del recorrido global reanudable (sin red: se simula `power.grid`)."""

import json
import os

import pytest

from src.etl import sweep


def test_tiles_cover_planet_without_gaps():
    tiles = sweep.tiles_global(2.0)
    assert len(tiles) == 90 * 180
    assert tiles[0] == (-180.0, -90.0, -178.0, -88.0)
    assert tiles[-1] == (178.0, 88.0, 180.0, 90.0)
    # Contiguas: cada caja empieza donde acaba la anterior.
    assert tiles[1][0] == tiles[0][2]
    assert tiles[180][1] == tiles[0][3]


def test_tiles_reject_bad_step():
    with pytest.raises(ValueError):
        sweep.tiles_global(7.0)


def test_tile_filenames_are_unique(tmp_path):
    names = {os.path.basename(sweep._tile_path(str(tmp_path), t)) for t in sweep.tiles_global(2.0)}
    assert len(names) == 90 * 180


def test_run_is_resumable(tmp_path, monkeypatch):
    calls = []

    def fake_grid(variable_id, bbox, *, start=None, end=None):
        calls.append(bbox)
        return {
            "lats": [bbox[1] + 1.0],
            "lons": [bbox[0] + 1.0],
            "dates": ["2020-01"],
            "values": [[[1.5]]],
            "unit": "C",
            "provenance": {"kind": "nasa_api", "source": "NASA POWER test",
                           "request_url": "https://example/x", "retrieved_at": "2026-11-14T00:00:00Z",
                           "sha256": "b" * 64},
        }

    monkeypatch.setattr(sweep.power, "grid", fake_grid)
    out = str(tmp_path / "sweep")
    logs = []

    first = sweep.run("T2M", out, max_tiles=3, pause_seconds=0, log=logs.append)
    assert first["processed_this_run"] == 3
    assert first["stopped_by"] == "max_tiles"
    assert len(calls) == 3

    second = sweep.run("T2M", out, max_tiles=2, pause_seconds=0, log=logs.append)
    assert second["processed_this_run"] == 2
    assert second["tiles_done"] == 5
    assert len(calls) == 5  # no se repiten las cajas ya hechas
    assert calls[3] != calls[0]


def test_run_deadline_stops_cleanly(tmp_path, monkeypatch):
    def slow_grid(variable_id, bbox, *, start=None, end=None):
        return {"lats": [0.0], "lons": [0.0], "dates": ["2020-01"], "values": [[[1.0]]],
                "unit": "C", "provenance": {"kind": "nasa_api", "sha256": "c" * 64,
                                            "request_url": "https://example/x",
                                            "retrieved_at": "2026-11-14T00:00:00Z", "source": "x"}}

    monkeypatch.setattr(sweep.power, "grid", slow_grid)
    out = str(tmp_path / "sweep")
    summary = sweep.run("T2M", out, deadline_seconds=0, pause_seconds=0, log=lambda *_: None)
    assert summary["processed_this_run"] == 0
    assert summary["stopped_by"] == "deadline"


def test_empty_tile_is_recorded_not_retried(tmp_path, monkeypatch):
    from src.etl.errors import DataUnavailable

    def raising_grid(variable_id, bbox, *, start=None, end=None):
        raise DataUnavailable("OUT_OF_COVERAGE", "sin celdas")

    monkeypatch.setattr(sweep.power, "grid", raising_grid)
    out = str(tmp_path / "sweep")
    summary = sweep.run("T2M", out, max_tiles=1, pause_seconds=0, log=lambda *_: None)
    assert summary["empty_this_run"] == 1
    files = [f for f in os.listdir(out) if f.endswith(".json")]
    assert len(files) == 1
    with open(os.path.join(out, files[0]), encoding="utf-8") as fh:
        assert json.load(fh)["status"] == "empty"
    # Al reanudar, la caja vacia no se vuelve a pedir.
    again = sweep.run("T2M", out, max_tiles=1, pause_seconds=0, log=lambda *_: None)
    assert again["tiles_done"] == 2


def test_cli_rejects_non_power_variable(tmp_path):
    code = sweep.main(["--variable", "GISTEMP_TANOM", "--out", str(tmp_path)])
    assert code == 2
