# SI-assisted: hermes-2 (Claude Sonnet 5.5)
"""S3 - Build a global TrendMap v2 for one variable (data/atlas/<ID>.json).

Order the prompt asks for:
1. GISTEMP_TANOM first: it comes from one file and takes minutes.
2. Then POWER regional variables in tiles, serially, resumable and with
   progress logging, respecting the documented request limits.
3. If the output is over 3 MB, group cells 2x2 by averaging the series BEFORE
   analysing (never average slopes or p-values).

The statistics come from `src.stats.analyze_grid` when it exists (contract
section 6). Until Antigravity 2 ships it, a local per-cell implementation of
the same contract is used: Sen slope and Mann-Kendall per cell, with
Benjamini-Hochberg FDR across cells. It is marked as such in the output.

Usage:
    python scripts/build_atlas.py --variable GISTEMP_TANOM
    python scripts/build_atlas.py --variable T2M --bbox -82 -18 -68 -2 --tile 4
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ATLAS_DIR = os.path.join(ROOT, "data", "atlas")
CACHE_DIR = os.path.join(ROOT, "data", "cache")
POWER_TILE_DEG = 4.0          # recommended tile per POWER docs
POWER_PAUSE_SECONDS = 2.0     # be polite; POWER allows ~30 requests/min
MEGABYTE = 1024 * 1024


def log(message: str) -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def load_etl():
    try:
        from src.etl.registry import DataUnavailable, get_grid  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"no puedo importar src.etl.registry: {exc}") from exc
    return get_grid, DataUnavailable


def load_grid_analysis():
    """analyze_grid from the stats lane, or a documented local fallback."""
    try:
        from src.stats.trend_engine import analyze_grid  # type: ignore
        return analyze_grid, "src.stats.analyze_grid"
    except Exception:  # noqa: BLE001
        pass

    # Fallback: same contract, implemented here with numpy (the pure-Python
    # loop is far too slow for a 90x180 x 1762-month grid).
    def analyze_grid(grid: dict, *, alpha: float = 0.05, fdr_q: float = 0.10) -> dict:
        import numpy as np

        lat_axis = grid["lats"]
        lon_axis = grid["lons"]
        dates = grid["dates"]
        arr = np.array(grid["values"], dtype=float)  # [t][lat][lon]
        n_lat, n_lon = len(lat_axis), len(lon_axis)

        # Time as decimal years, and annual means: 45 values per cell instead
        # of 1762 months. This is the same reduction the contract applies for
        # the annual Mann-Kendall test, and it makes a global grid tractable.
        years = np.array([int(d[:4]) for d in dates])
        unique_years = np.unique(years)
        annual = np.full((len(unique_years), n_lat, n_lon), np.nan)
        for k, year in enumerate(unique_years):
            block = arr[years == year]
            with np.errstate(invalid="ignore"):
                counts = np.sum(~np.isnan(block), axis=0)
                sums = np.nansum(block, axis=0)
                annual[k] = np.where(counts >= 10, sums / np.maximum(counts, 1), np.nan)
        t_years = unique_years.astype(float)

        slope = np.full((n_lat, n_lon), np.nan)
        pval = np.full((n_lat, n_lon), np.nan)

        for i in range(n_lat):
            block = annual[:, i, :]  # [year][lon]
            for j in range(n_lon):
                y = block[:, j]
                mask = ~np.isnan(y)
                n = int(mask.sum())
                if n < 25:
                    continue
                x = t_years[mask]
                yy = y[mask]
                slope[i, j] = _sen_slope_np(x, yy) * 10.0  # per decade
                pval[i, j] = _mk_p_np(yy)

        flat = [
            (i, j, float(pval[i, j]))
            for i in range(n_lat) for j in range(n_lon)
            if not np.isnan(pval[i, j])
        ]
        significant = _bh_significant(flat, fdr_q)
        sig_matrix = [[False] * n_lon for _ in range(n_lat)]
        for i, j in significant:
            sig_matrix[i][j] = True

        n_cells = int(np.sum(~np.isnan(slope)))
        n_sig = len(significant)
        up = sum(1 for i, j in significant if float(slope[i, j]) > 0)
        down = n_sig - up

        def clean(matrix):
            return [
                [None if (isinstance(v, float) and math.isnan(v)) else float(v) for v in row]
                for row in matrix
            ]

        return {
            "schema": "trendmap/2",
            "variable_id": grid.get("variable_id") or "",
            "unit_per_decade": (grid.get("unit") or "") + "/decade",
            "bbox": grid.get("bbox"),
            "lats": lat_axis,
            "lons": lon_axis,
            "slope_per_decade": clean(slope),
            "p_value": clean(pval),
            "significant_fdr": sig_matrix,
            "fdr_q": fdr_q,
            "n_cells": n_cells,
            "n_significant": n_sig,
            "period": {"start": dates[0], "end": dates[-1]},
            "summary": {
                "share_up_significant": round(up / n_cells, 4) if n_cells else 0.0,
                "share_down_significant": round(down / n_cells, 4) if n_cells else 0.0,
            },
            "provenance": grid.get("provenance") or {},
            "method_note": "local per-cell Sen slope + Mann-Kendall with BH FDR; "
                           "replace with src.stats.analyze_grid when available",
        }

    return analyze_grid, "local fallback (build_atlas.py)"


def slopegrid_value(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _sen_slope_np(x, y) -> float:
    """Median of pairwise slopes, computed with broadcasting (n up to ~1800)."""
    import numpy as np

    # Pairwise differences: (n, n) matrices of dx and dy.
    dx = x[None, :] - x[:, None]
    dy = y[None, :] - y[:, None]
    upper = np.triu_indices(len(x), k=1)
    valid = dx[upper] != 0
    if not np.any(valid):
        return 0.0
    slopes = dy[upper][valid] / dx[upper][valid]
    return float(np.median(slopes))


def _mk_p_np(values) -> float:
    """Mann-Kendall p-value, vectorised with numpy."""
    import numpy as np

    n = len(values)
    if n < 3:
        return 1.0
    # Count concordant pairs per element: sum of signs of later - earlier.
    x = values[:, None]
    y = values[None, :]
    signs = np.sign(y - x)
    upper = np.triu_indices(n, k=1)
    s = float(np.sum(signs[upper]))
    var = n * (n - 1) * (2 * n + 5) / 18.0
    if var <= 0:
        return 1.0
    if s > 0:
        z = (s - 1) / math.sqrt(var)
    elif s < 0:
        z = (s + 1) / math.sqrt(var)
    else:
        z = 0.0
    return math.erfc(abs(z) / math.sqrt(2))


def _bh_significant(flat: list[tuple[int, int, float]], q: float) -> list[tuple[int, int]]:
    """Benjamini-Hochberg: return the cells whose null is rejected at FDR q."""
    entries = sorted(flat, key=lambda item: item[2])
    m = len(entries)
    keep = 0
    for rank, (_, _, p) in enumerate(entries, start=1):
        if p <= q * rank / m:
            keep = rank
    return [(i, j) for i, j, _ in entries[:keep]]


def tile_bboxes(bbox: list[float], tile: float) -> list[list[float]]:
    west, south, east, north = bbox
    boxes = []
    lat = south
    while lat < north:
        lat2 = min(lat + tile, north)
        lon = west
        while lon < east:
            lon2 = min(lon + tile, east)
            boxes.append([lon, lat, lon2, lat2])
            lon = lon2
        lat = lat2
    return boxes


def progress_path(variable: str, bbox: list[float] | None) -> str:
    key = variable if not bbox else variable + "_box"
    return os.path.join(CACHE_DIR, f"atlas_{key}.npz")


def load_progress(path: str) -> tuple[set[str], list[dict]]:
    """Resume support. Grids are stored compressed in .npz: a global grid as
    JSON is hundreds of megabytes, which is both slow and wasteful."""
    import numpy as np

    if not os.path.exists(path):
        return set(), []
    with np.load(path, allow_pickle=True) as data:
        done = set(str(x) for x in data["done_tiles"])
        lats = data["lats"]
        lons = data["lons"]
        dates = [str(x) for x in data["dates"]]
        unit = str(data["unit"]) if "unit" in data else None
        values = data["values"]
        provenance = json.loads(str(data["provenance"])) if "provenance" in data else {}
    grids = [{
        "lats": lats.tolist(),
        "lons": lons.tolist(),
        "dates": dates,
        "values": values.tolist(),
        "unit": unit,
        "provenance": provenance,
    }]
    return done, grids


def save_progress(path: str, done: set[str], grids: list[dict]) -> None:
    import numpy as np

    os.makedirs(os.path.dirname(path), exist_ok=True)
    merged = grids[0] if len(grids) == 1 else merge_grids(grids)
    np.savez_compressed(
        path,
        done_tiles=np.array(sorted(done)),
        lats=np.array(merged["lats"]),
        lons=np.array(merged["lons"]),
        dates=np.array(merged["dates"]),
        values=np.array(merged["values"], dtype=np.float32),
        unit=np.array(merged.get("unit") or ""),
        provenance=np.array(json.dumps(merged.get("provenance") or {})),
    )


def merge_grids(grids: list[dict]) -> dict:
    """Union of tiles on a shared lat/lon axis; missing cells stay null."""
    lats = sorted({round(v, 4) for g in grids for v in g["lats"]})
    lons = sorted({round(v, 4) for g in grids for v in g["lons"]})
    dates = grids[0]["dates"]
    index_lat = {v: i for i, v in enumerate(lats)}
    index_lon = {v: i for i, v in enumerate(lons)}
    values = [
        [[None for _ in lons] for _ in lats]
        for _ in dates
    ]
    for g in grids:
        for a, lat in enumerate(g["lats"]):
            ia = index_lat[round(lat, 4)]
            for b, lon in enumerate(g["lons"]):
                ib = index_lon[round(lon, 4)]
                for t in range(len(dates)):
                    values[t][ia][ib] = g["values"][t][a][b]
    return {
        "lats": lats,
        "lons": lons,
        "dates": dates,
        "values": values,
        "unit": grids[0].get("unit"),
        "provenance": grids[0].get("provenance"),
    }


def downsample_2x2(grid: dict) -> dict:
    """Average each 2x2 block of series BEFORE analysis, as required."""
    lats, lons, dates, values = grid["lats"], grid["lons"], grid["dates"], grid["values"]
    new_lats, new_lons = [], []
    out_values: list[list[list[float | None]]] = []
    for i in range(0, len(lats), 2):
        new_lats.append(lats[i])
    for j in range(0, len(lons), 2):
        new_lons.append(lons[j])
    for t in range(len(dates)):
        block_row = []
        for i in range(0, len(lats), 2):
            row = []
            for j in range(0, len(lons), 2):
                cell = [
                    values[t][a][b]
                    for a in (i, i + 1) if a < len(lats)
                    for b in (j, j + 1) if b < len(lons)
                    if values[t][a][b] is not None
                ]
                row.append(sum(cell) / len(cell) if cell else None)
            block_row.append(row)
        out_values.append(block_row)
    return {"lats": new_lats, "lons": new_lons, "dates": dates,
            "values": out_values, "unit": grid.get("unit"),
            "provenance": grid.get("provenance")}


def build(variable: str, bbox: list[float] | None, tile: float, limit_minutes: float) -> int:
    get_grid, DataUnavailable = load_etl()
    analyze_grid, method_source = load_grid_analysis()
    log(f"variable={variable} bbox={bbox} tile={tile} method={method_source}")

    started = time.time()
    deadline = started + limit_minutes * 60

    if variable == "GISTEMP_TANOM":
        target_bbox = bbox or [-180, -90, 180, 90]
        tiles = [target_bbox]
    else:
        if not bbox:
            raise SystemExit("POWER regional needs --bbox; global POWER is not attempted "
                             "because it would exceed the request budget")
        tiles = tile_bboxes(bbox, tile)

    log(f"{len(tiles)} tile(s) to fetch")
    path = progress_path(variable, bbox)
    done, grids = load_progress(path)

    for idx, box in enumerate(tiles, start=1):
        key = ",".join(f"{v:g}" for v in box)
        if key in done:
            log(f"tile {idx}/{len(tiles)} {key} already done")
            continue
        if time.time() > deadline:
            log("time budget reached; stopping before next tile (resumable)")
            break
        log(f"tile {idx}/{len(tiles)} {key} …")
        try:
            grid = get_grid(variable, box)
        except DataUnavailable as exc:
            log(f"  DataUnavailable: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            log(f"  ERROR {type(exc).__name__}: {exc}")
            continue
        grids.append(grid)
        done.add(key)
        save_progress(path, done, grids)
        log(f"  ok: {len(grid['lats'])}x{len(grid['lons'])} cells, {len(grid['dates'])} months")
        if variable != "GISTEMP_TANOM":
            time.sleep(POWER_PAUSE_SECONDS)

    if not grids:
        log("no grids fetched; nothing to write")
        return 1

    merged = grids[0] if len(grids) == 1 else merge_grids(grids)
    merged["variable_id"] = variable
    merged["bbox"] = bbox

    result = analyze_grid(merged, fdr_q=0.10)
    os.makedirs(ATLAS_DIR, exist_ok=True)
    out_path = os.path.join(ATLAS_DIR, variable + ".json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False)
    size = os.path.getsize(out_path)
    elapsed = (time.time() - started) / 60

    if size > 3 * MEGABYTE:
        log(f"{size / MEGABYTE:.1f} MB > 3 MB: averaging 2x2 blocks before analysing again")
        coarse = downsample_2x2(merged)
        result = analyze_grid(coarse, fdr_q=0.10)
        result["downsampled"] = "2x2 block mean of series before analysis"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False)
        size = os.path.getsize(out_path)

    log(f"wrote {out_path}")
    log(f"size={size / MEGABYTE:.2f} MB cells={result['n_cells']} "
        f"significant={result['n_significant']} "
        f"({(100 * result['n_significant'] / max(1, result['n_cells'])):.1f}%) "
        f"elapsed={elapsed:.1f} min")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a TrendMap v2 atlas file")
    parser.add_argument("--variable", required=True)
    parser.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"))
    parser.add_argument("--tile", type=float, default=POWER_TILE_DEG)
    parser.add_argument("--limit-minutes", type=float, default=60.0)
    args = parser.parse_args()
    return build(args.variable, args.bbox, args.tile, args.limit_minutes)


if __name__ == "__main__":
    raise SystemExit(main())
