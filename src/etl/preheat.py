# SI-assisted: antigravity-1 (Gemini 3.8 Flash)
"""
Precalienta la cache en disco de los casos de demostracion oficiales (Ronda 2 §6).

Casos:
- Lima, Peru: T2M (punto -12.05, -77.03)
- Piura, Peru: PRECTOTCORR (punto -5.19, -80.63)
- Svalbard, Noruega: T2M (punto 78.22, 15.65)
- Artico: SEAICE_EXTENT_N
- Antartico: SEAICE_EXTENT_S
- Global: GISTEMP_TANOM
- Rejilla Piura (TrendMap): T2M en [-82.0, -7.0, -78.0, -3.0]
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any

from src.etl.registry import get_grid, get_series

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preheat")

DEMO_CASES = [
    {"id": "lima-t2m", "var": "T2M", "lat": -12.05, "lon": -77.03, "kind": "point"},
    {"id": "piura-prectotcorr", "var": "PRECTOTCORR", "lat": -5.19, "lon": -80.63, "kind": "point"},
    {"id": "svalbard-t2m", "var": "T2M", "lat": 78.22, "lon": 15.65, "kind": "point"},
    {"id": "arctic-seaice", "var": "SEAICE_EXTENT_N", "kind": "hemisphere"},
    {"id": "antarctic-seaice", "var": "SEAICE_EXTENT_S", "kind": "hemisphere"},
    {"id": "gistemp-global", "var": "GISTEMP_TANOM", "kind": "global"},
]

DEMO_GRIDS = [
    {"id": "piura-grid-t2m", "var": "T2M", "bbox": [-82.0, -7.0, -78.0, -3.0]},
]


def preheat_all() -> dict[str, Any]:
    results = {}
    total = len(DEMO_CASES) + len(DEMO_GRIDS)
    success = 0

    logger.info("Iniciando precalentamiento de cache para %d casos de demostracion...", total)

    for case in DEMO_CASES:
        cid = case["id"]
        var = case["var"]
        logger.info("Precalentando serie: %s (%s)...", cid, var)
        try:
            if case["kind"] == "point":
                ts = get_series(var, lat=case["lat"], lon=case["lon"])
            else:
                ts = get_series(var)

            data_pts = len(ts.get("data", []))
            prov_kind = ts.get("provenance", {}).get("kind", "unknown")
            sha = ts.get("provenance", {}).get("sha256", "")[:12]
            results[cid] = {"status": "ok", "points": data_pts, "provenance": prov_kind, "sha": sha}
            logger.info("  -> OK: %s (%d puntos, %s, sha=%s)", cid, data_pts, prov_kind, sha)
            success += 1
        except Exception as exc:
            logger.error("  -> ERROR en %s: %s", cid, exc)
            results[cid] = {"status": "error", "error": str(exc)}

        # Pausa respetuosa de 1 segundo entre llamadas de red
        time.sleep(1.0)

    for grid in DEMO_GRIDS:
        gid = grid["id"]
        var = grid["var"]
        bbox = grid["bbox"]
        logger.info("Precalentando rejilla: %s (%s, bbox=%s)...", gid, var, bbox)
        try:
            res = get_grid(var, bbox)
            n_dates = len(res.get("dates", []))
            n_lats = len(res.get("lats", []))
            n_lons = len(res.get("lons", []))
            results[gid] = {"status": "ok", "dates": n_dates, "lats": n_lats, "lons": n_lons}
            logger.info("  -> OK: %s (%d fechas, %dx%d celdas)", gid, n_dates, n_lats, n_lons)
            success += 1
        except Exception as exc:
            logger.error("  -> ERROR en %s: %s", gid, exc)
            results[gid] = {"status": "error", "error": str(exc)}
        time.sleep(1.0)

    logger.info("Precalentamiento finalizado: %d/%d completados con exito.", success, total)
    return results


if __name__ == "__main__":
    res = preheat_all()
    failed = [k for k, v in res.items() if v.get("status") != "ok"]
    if failed:
        sys.exit(1)
    sys.exit(0)
