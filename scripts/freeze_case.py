# SI-assisted: hermes-2 (Claude Sonnet 5.5)
"""S2 - Freeze a real case: series + analysis + case description.

Calls `get_series` (src/etl) and `analyze_series` (src/stats) exactly as the
contract specifies, then writes:

    data/cases/<id>/series.json    TimeSeries v2 (or TrendMap v2 for grids)
    data/cases/<id>/analysis.json  AnalysisResult v2
    data/cases/<id>/case.json      titles and story steps (both languages)

The story text is left as "TODO_HUMANO" where a human must approve it: the
prompt says the human writes or approves the narrative.

Usage:
    python scripts/freeze_case.py --id lima-t2m --variable T2M --lat -12.05 --lon -77.03 \
        --name-es "Lima" --name-en "Lima" --story-es "..." --story-en "..."
    python scripts/freeze_case.py --list-cases
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CASES_DIR = os.path.join(ROOT, "data", "cases")
TODAY = "2026-11-14"

# Technical cases the prompt names for testing the flow.
TECHNICAL_CASES = [
    {"id": "lima-t2m", "variable": "T2M", "lat": -12.05, "lon": -77.03,
     "name_es": "Lima, Perú", "name_en": "Lima, Peru"},
    {"id": "svalbard-t2m", "variable": "T2M", "lat": 78.22, "lon": 15.65,
     "name_es": "Svalbard, Noruega", "name_en": "Svalbard, Norway"},
    {"id": "piura-prectotcorr", "variable": "PRECTOTCORR", "lat": -5.19, "lon": -80.63,
     "name_es": "Piura, Perú", "name_en": "Piura, Peru"},
    # NSIDC Sea Ice Index is hemispheric: it takes no coordinates.
    {"id": "arctic-seaice", "variable": "SEAICE_EXTENT_N",
     "name_es": "Hielo marino del Ártico", "name_en": "Arctic sea ice"},
    {"id": "antarctic-seaice", "variable": "SEAICE_EXTENT_S",
     "name_es": "Hielo marino del Antártico", "name_en": "Antarctic sea ice"},
]

# Variables whose connector is defined over a whole hemisphere.
HEMISPHERIC_VARIABLES = {"SEAICE_EXTENT_N", "SEAICE_EXTENT_S", "GISTEMP_TANOM"}


def load_modules():
    """Import the ETL and stats modules, failing loudly if a contract is missing."""
    try:
        from src.etl.registry import DataUnavailable, get_series  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"src.etl.registry no disponible: {exc}") from exc

    analyze_series = None
    import_error = None
    try:
        from src.stats.trend_engine import analyze_series  # type: ignore
    except Exception as exc:  # noqa: BLE001
        import_error = str(exc)
        try:
            from src.stats.trend_engine import analyze as _analyze  # type: ignore

            def analyze_series(ts: dict, **_kwargs) -> dict:  # type: ignore
                """Adapter for the current `analyze(series, variable_id, ...)`.

                The contract function is `analyze_series(ts, **kwargs)`; the
                engine at this commit still exposes the older `analyze`, so the
                adapter maps one to the other without changing any number.
                """
                card = ts.get("variable") or {}
                return _analyze(
                    ts["data"],
                    ts.get("variable_id", ""),
                    card.get("name") or ts.get("variable_id", ""),
                    ts.get("unit", ""),
                    ts.get("region") or {},
                    ts.get("provenance") or {},
                )

        except Exception as exc2:  # noqa: BLE001
            import_error = f"{import_error}; {exc2}"

    if analyze_series is None:
        raise SystemExit(f"src.stats.trend_engine.analyze_series no disponible: {import_error}")
    return get_series, DataUnavailable, analyze_series


def fetch_series(variable: str, lat: float | None, lon: float | None, bbox: list[float] | None) -> dict:
    get_series, _, _ = load_modules()
    kwargs: dict[str, Any] = {}
    if variable in HEMISPHERIC_VARIABLES:
        pass  # hemispheric connectors take no location
    elif bbox:
        kwargs["bbox"] = bbox
    else:
        kwargs["lat"], kwargs["lon"] = lat, lon
    return get_series(variable, **kwargs)


def analyze(ts: dict, variable: str) -> dict:
    _, _, analyze_series = load_modules()
    return analyze_series(ts)


def validate_series(ts: dict) -> list[str]:
    """Minimum checks from the contract before spending a request budget."""
    problems: list[str] = []
    if ts.get("schema") != "timeseries/2":
        problems.append(f"schema is {ts.get('schema')!r}, expected 'timeseries/2'")
    prov = ts.get("provenance") or {}
    if prov.get("kind") not in ("nasa_api", "nasa_file"):
        problems.append(f"provenance.kind is {prov.get('kind')!r}")
    if not prov.get("sha256"):
        problems.append("provenance.sha256 missing")
    dates = [point.get("date") for point in ts.get("data", [])]
    if dates != sorted(dates):
        problems.append("dates are not increasing")
    if len(set(dates)) != len(dates):
        problems.append("duplicate dates")
    values = [point.get("value") for point in ts.get("data", [])]
    if any(v == -999 for v in values):
        problems.append("raw -999 found (must be null)")
    if len(dates) < 120:
        problems.append(f"only {len(dates)} months (>= 120 required)")
    return problems


def write_case(case_id: str, ts: dict, analysis: dict, meta: dict[str, Any]) -> str:
    case_dir = os.path.join(CASES_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)

    series_path = os.path.join(case_dir, "series.json")
    analysis_path = os.path.join(case_dir, "analysis.json")
    case_path = os.path.join(case_dir, "case.json")

    with open(series_path, "w", encoding="utf-8") as fh:
        json.dump(ts, fh, ensure_ascii=False, indent=1)
    with open(analysis_path, "w", encoding="utf-8") as fh:
        json.dump(analysis, fh, ensure_ascii=False, indent=1)

    case = {
        "id": case_id,
        "variable_id": meta["variable"],
        "region": ts.get("region") or {},
        "names": {"es": meta["name_es"], "en": meta["name_en"]},
        "titles": {
            "es": meta.get("title_es") or "TODO_HUMANO",
            "en": meta.get("title_en") or "TODO_HUMANO",
        },
        "story": {
            "es": meta.get("story_es") or ["TODO_HUMANO"],
            "en": meta.get("story_en") or ["TODO_HUMANO"],
        },
        "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "kind": (ts.get("provenance") or {}).get("kind"),
            "source": (ts.get("provenance") or {}).get("source"),
            "request_url": (ts.get("provenance") or {}).get("request_url"),
        },
        "significance": (analysis.get("significance") or {}),
    }
    with open(case_path, "w", encoding="utf-8") as fh:
        json.dump(case, fh, ensure_ascii=False, indent=1)
    return case_dir


def freeze_one(case: dict[str, Any]) -> bool:
    print(f"--- {case['id']} ({case['variable']})")
    try:
        ts = fetch_series(case["variable"], case.get("lat"), case.get("lon"), case.get("bbox"))
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR get_series: {type(exc).__name__}: {exc}")
        return False

    problems = validate_series(ts)
    if problems:
        print("  series fails validation:")
        for p in problems:
            print("   -", p)
        return False

    try:
        analysis = analyze(ts, case["variable"])
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR analyze_series: {type(exc).__name__}: {exc}")
        return False

    case_dir = write_case(case["id"], ts, analysis, case)
    sig = (analysis.get("significance") or {}).get("verdict_code")
    print(f"  wrote {case_dir} (verdict={sig}, n={len(ts['data'])})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze a real case with series and analysis")
    parser.add_argument("--id")
    parser.add_argument("--variable")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"))
    parser.add_argument("--name-es", default="TODO_HUMANO")
    parser.add_argument("--name-en", default="TODO_HUMANO")
    parser.add_argument("--title-es")
    parser.add_argument("--title-en")
    parser.add_argument("--story-es", nargs="*")
    parser.add_argument("--story-en", nargs="*")
    parser.add_argument("--technical", action="store_true", help="freeze the five technical cases")
    parser.add_argument("--list-cases", action="store_true")
    args = parser.parse_args()

    if args.list_cases:
        for case in TECHNICAL_CASES:
            print(case["id"], case["variable"], case.get("lat"), case.get("lon"))
        return 0

    if args.technical:
        ok = sum(1 for case in TECHNICAL_CASES if freeze_one(case))
        print(f"\n{ok}/{len(TECHNICAL_CASES)} technical cases frozen")
        return 0 if ok == len(TECHNICAL_CASES) else 1

    if not (args.id and args.variable):
        parser.error("--id and --variable are required (or use --technical)")
    if not args.bbox and args.variable not in HEMISPHERIC_VARIABLES and (args.lat is None or args.lon is None):
        parser.error("give --lat/--lon or --bbox (hemispheric variables need neither)")

    case = {
        "id": args.id,
        "variable": args.variable,
        "lat": args.lat,
        "lon": args.lon,
        "bbox": args.bbox,
        "name_es": args.name_es,
        "name_en": args.name_en,
        "title_es": args.title_es,
        "title_en": args.title_en,
        "story_es": args.story_es,
        "story_en": args.story_en,
    }
    return 0 if freeze_one(case) else 1


if __name__ == "__main__":
    raise SystemExit(main())
