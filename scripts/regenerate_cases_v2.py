# SI-assisted: hermes-2 (Claude Sonnet 5.5)
"""Regenerate the five frozen cases with the real analysis/2 engine.

This calls `get_series` (real NASA data) and `analyze_series` from main, then
writes `series.json`, `analysis.json`, `case.json` and `data/cases/index.json`.
It does not translate an old JSON: it recomputes every number.

Usage:
    python scripts/regenerate_cases_v2.py            # all five technical cases
    python scripts/regenerate_cases_v2.py --id lima-t2m
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
CATALOG = os.path.join(ROOT, "data", "catalog", "variables.json")
FROZEN_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Hemispheric connectors take no point: calling them with lat/lon fails.
HEMISPHERIC = {"SEAICE_EXTENT_N", "SEAICE_EXTENT_S", "GISTEMP_TANOM"}

CASES: list[dict[str, Any]] = [
    {"id": "lima-t2m", "variable": "T2M", "lat": -12.05, "lon": -77.03,
     "name_es": "Lima, Perú", "name_en": "Lima, Peru", "region_kind": "point"},
    {"id": "svalbard-t2m", "variable": "T2M", "lat": 78.22, "lon": 15.65,
     "name_es": "Svalbard, Noruega", "name_en": "Svalbard, Norway", "region_kind": "point"},
    {"id": "piura-prectotcorr", "variable": "PRECTOTCORR", "lat": -5.19, "lon": -80.63,
     "name_es": "Piura, Perú", "name_en": "Piura, Peru", "region_kind": "point"},
    {"id": "arctic-seaice", "variable": "SEAICE_EXTENT_N",
     "name_es": "Hielo marino del Ártico", "name_en": "Arctic sea ice", "region_kind": "named"},
    {"id": "antarctic-seaice", "variable": "SEAICE_EXTENT_S",
     "name_es": "Hielo marino del Antártico", "name_en": "Antarctic sea ice", "region_kind": "named"},
    # Ronda 3: los dos CSV reales exportados de Giovanni (MERRA-2 via GES DISC),
    # misma caja y periodo. La procedencia lleva la "URL to Reproduce Results".
    {"id": "amazonia-t2m", "variable": "T2M", "region_kind": "named",
     "giovanni_csv": "data/raw/giovanni/T2M__amazonia.csv",
     "name_es": "Amazonía (cuenca baja del Amazonas)", "name_en": "Amazon (lower Amazon basin)"},
    {"id": "amazonia-prectotcorr", "variable": "PRECTOTCORR", "region_kind": "named",
     "giovanni_csv": "data/raw/giovanni/PRECTOTCORR__amazonia.csv",
     "name_es": "Amazonía (cuenca baja del Amazonas)", "name_en": "Amazon (lower Amazon basin)"},
]


def load_card(variable_id: str) -> dict[str, Any]:
    """Catalogue card; ratio_scale decides whether % change is meaningful."""
    if os.path.exists(CATALOG):
        with open(CATALOG, encoding="utf-8") as fh:
            data = json.load(fh)
        cards = data.get("variables") if isinstance(data, dict) else data
        for card in cards or []:
            if card.get("id") == variable_id:
                return card
    seed = os.path.join(ROOT, "data", "catalog", "variables.seed.json")
    if os.path.exists(seed):
        with open(seed, encoding="utf-8") as fh:
            data = json.load(fh)
        for card in data.get("live", []):
            if card.get("id") == variable_id:
                return card
    return {}


def build_one(case: dict[str, Any]) -> dict[str, Any]:
    from src.etl.registry import get_series
    from src.stats.trend_engine import analyze_series

    card = load_card(case["variable"])
    if case.get("giovanni_csv"):
        # Fuente: CSV real exportado de Giovanni. Se lee tal cual; el parser
        # convierte el relleno de la cabecera en null y declara user_upload.
        from src.etl.registry import parse_giovanni_csv

        path = os.path.join(ROOT, case["giovanni_csv"])
        with open(path, encoding="utf-8") as fh:
            ts = parse_giovanni_csv(fh.read(), case["variable"])
        ts["region"]["name"] = case["name_en"]
    else:
        kwargs: dict[str, Any] = {}
        if case["variable"] in HEMISPHERIC:
            pass
        else:
            kwargs["lat"], kwargs["lon"] = case["lat"], case["lon"]
        ts = get_series(case["variable"], **kwargs)

    # Ronda 5: el texto "donde" debe nombrar el lugar. El motor usa un unico
    # region.name para los dos idiomas; se deja el nombre en ingles (el que
    # consume la API por defecto) y el texto de cada idioma se fija abajo con
    # su nombre, sin tocar ninguna cifra.
    if not ts["region"].get("name"):
        ts["region"]["name"] = case["name_en"]

    analysis = analyze_series(
        ts,
        ratio_scale=bool(card.get("ratio_scale", False)),
        homogeneous_since=((card.get("source") or {}).get("homogeneous_since")),
    )

    answers = analysis.get("answers") or {}
    if answers.get("where") is not None:
        where_es = f"Observado en {case['name_es']}."
        where_en = f"Observed in {case['name_en']}."
        if case.get("giovanni_csv") or ts["region"].get("kind") == "bbox":
            # Una caja no es un lugar con nombre de ciudad: se dice que es un area.
            where_es = f"Observado en el área de {case['name_es']}."
            where_en = f"Observed in the {case['name_en']} area."
        analysis["answers"]["where"] = {"es": where_es, "en": where_en}

    case_dir = os.path.join(CASES_DIR, case["id"])
    os.makedirs(case_dir, exist_ok=True)
    with open(os.path.join(case_dir, "series.json"), "w", encoding="utf-8") as fh:
        json.dump(ts, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(case_dir, "analysis.json"), "w", encoding="utf-8") as fh:
        json.dump(analysis, fh, ensure_ascii=False, indent=1)

    names = card.get("names") or {}
    case_doc = {
        "id": case["id"],
        "variable_id": case["variable"],
        "variable_name": {"es": names.get("es") or case["variable"], "en": names.get("en") or case["variable"]},
        "region": ts.get("region") or {},
        "names": {"es": case["name_es"], "en": case["name_en"]},
        "titles": {"es": "TODO_HUMANO", "en": "TODO_HUMANO"},
        "story": {"es": ["TODO_HUMANO"], "en": ["TODO_HUMANO"]},
        "frozen_at": FROZEN_AT,
        "verdict_code": (analysis.get("significance") or {}).get("verdict_code"),
        "provenance": ts.get("provenance") or {},
    }
    with open(os.path.join(case_dir, "case.json"), "w", encoding="utf-8") as fh:
        json.dump(case_doc, fh, ensure_ascii=False, indent=1)
    return case_doc


def write_index(cases: list[dict[str, Any]]) -> str:
    """The API reads data/cases/index.json and requires provenance per item."""
    items = []
    for case in cases:
        provenance = case.get("provenance") or {}
        items.append({
            "id": case["id"],
            "variable_id": case["variable_id"],
            "names": case["names"],
            "variable_name": case["variable_name"],
            "region": case["region"],
            "verdict_code": case.get("verdict_code"),
            "frozen_at": case.get("frozen_at"),
            "paths": {
                "series": f"data/cases/{case['id']}/series.json",
                "analysis": f"data/cases/{case['id']}/analysis.json",
                "case": f"data/cases/{case['id']}/case.json",
            },
            "provenance": {
                "kind": provenance.get("kind"),
                "source": provenance.get("source"),
                "request_url": provenance.get("request_url"),
                "retrieved_at": provenance.get("retrieved_at"),
            },
        })
    path = os.path.join(CASES_DIR, "index.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"cases": items}, fh, ensure_ascii=False, indent=1)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id")
    args = parser.parse_args()

    selected = [c for c in CASES if not args.id or c["id"] == args.id]
    if not selected:
        raise SystemExit(f"unknown case id {args.id!r}")

    done: list[dict[str, Any]] = []
    failed = 0
    for case in selected:
        print(f"--- {case['id']} ({case['variable']})", flush=True)
        try:
            doc = build_one(case)
        except Exception as exc:  # noqa: BLE001
            print(f"    ERROR {type(exc).__name__}: {exc}")
            failed += 1
            continue
        sig = doc.get("verdict_code")
        print(f"    OK verdict={sig} n={len(json.load(open(os.path.join(CASES_DIR, case['id'], 'series.json'), encoding='utf-8'))['data'])}")
        done.append(doc)

    # The index always lists every case present on disk, so a partial run does
    # not drop the others.
    existing = []
    for case in CASES:
        path = os.path.join(CASES_DIR, case["id"], "case.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                existing.append(json.load(fh))
    index_path = write_index(existing)
    print(f"wrote {index_path} ({len(existing)} cases)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
