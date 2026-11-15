# SI-assisted: cfable (Claude Fable 5.2)
"""Evaluation of RAG retrieval across the five cities (RONDA_7 §5).

    python scripts/eval_cities.py              # evaluate all 60 golden questions
    python scripts/eval_cities.py --markdown   # output GitHub-flavored Markdown table
    python scripts/eval_cities.py --city lima  # evaluate only one city
    python scripts/eval_cities.py --json       # dump metrics as JSON

Measures whether retrieve() returns a document matching the expected city
and the expected theme within the top 3 ranks (Hit@3 / Precision@3).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.detective import retrieve  # noqa: E402
from src.detective.rag import reset_cache  # noqa: E402

GOLDEN_DEFAULT = ROOT / "data" / "knowledge" / "golden_cities.jsonl"

CITIES = {
    "lima": "Lima",
    "huancayo": "Huancayo",
    "andahuaylas": "Andahuaylas",
    "ica": "Ica",
    "ayacucho": "Ayacucho",
}

THEME_KEYWORDS: dict[int, list[str]] = {
    1: ["ubicacion", "altitud", "relieve", "cuenca", "msnm", "valle", "vertiente", "cordillera", "geografia", "watershed", "elevation", "altitude", "basin", "relief"],
    2: ["temperatura", "termica", "normal", "climatologica", "maxima", "minima", "media", "estacion", "verano", "invierno", "temperature", "seasonal", "warm", "cold"],
    3: ["lluvia", "precipitacion", "pluvial", "garua", "llovizna", "milimetros", "estacionalidad", "humedo", "seco", "rain", "rainfall", "precipitation", "drizzle", "wet", "dry"],
    4: ["helada", "friaje", "ola de calor", "huaico", "inundacion", "aluvion", "desborde", "granizo", "sequia", "extremo", "frost", "cold wave", "heatwave", "flood", "landslide", "hail", "drought", "extreme"],
    5: ["el nino", "la nina", "enso", "enfen", "nino costero", "1982", "1983", "1997", "1998", "2017", "2023", "2024", "anomalia termica"],
    6: ["rio", "glaciar", "nevado", "laguna", "lago", "acuifero", "subterranea", "freatica", "embalse", "represa", "caudal", "hidrologia", "river", "glacier", "snow", "aquifer", "groundwater", "reservoir", "lake"],
    7: ["agricultura", "cultivo", "cosecha", "siembra", "calendario agricola", "papa", "maiz", "vid", "esparrago", "riego", "agricola", "agriculture", "crop", "harvest", "farming", "irrigation"],
    8: ["calidad del aire", "material particulado", "pm2.5", "pm10", "polvo", "aerosol", "aod", "radiacion uv", "indice uv", "ozono", "nubosidad", "nubes", "air quality", "particulate", "dust", "uv radiation", "ozone", "cloud"],
    9: ["vegetacion", "ndvi", "verdor", "cobertura vegetal", "deforestacion", "bosque", "suelo", "humedad del suelo", "expansion urbana", "lomas", "vegetation", "soil", "urban expansion", "greenness"],
    10: ["tendencia", "trend", "decada", "decenio", "por decada", "calentamiento", "disminucion", "aumento", "estudio", "senamhi", "inaigem", "ipcc", "cifras", "decadal", "/decade", "/decada", "trendmap"],
    11: ["estacion", "senamhi", "observatorio", "huayao", "campo de marte", "humboldt", "pluviometro", "estacion meteorologica", "celda satelital", "resolucion", "weather station", "meteorological station"],
    12: ["poblacion", "habitantes", "vulnerabilidad", "vulnerable", "riesgo", "exposicion", "damnificados", "salud", "censo", "inei", "cenepred", "indeci", "population", "exposure", "people", "settlements"],
}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def has_word(haystack: str, word: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(fold(word)) + r"(?!\w)", fold(haystack)) is not None


def matches_city(doc: dict[str, Any], city: str) -> bool:
    city_norm = fold(city)
    places = [fold(p) for p in (doc.get("places") or [])]
    if city_norm in places:
        return True
    doc_id = str(doc.get("id") or "").lower()
    if doc_id.startswith(f"region-{city_norm}") or doc_id.startswith(f"fact-{city_norm}"):
        return True
    city_name = CITIES.get(city, city)
    title = str(doc.get("title") or "")
    text = str(doc.get("text") or "")
    return has_word(title, city_name) or has_word(text, city_name)


def matches_theme(doc: dict[str, Any], theme: int, expected_vars: list[str]) -> bool:
    # 1. Direct theme field if present
    doc_theme = doc.get("theme")
    if doc_theme is not None:
        try:
            if int(doc_theme) == theme:
                return True
        except (ValueError, TypeError):
            pass

    # 2. Variable intersection
    if expected_vars:
        doc_vars = set(doc.get("variables") or [])
        if any(v in doc_vars for v in expected_vars):
            return True

    # 3. Theme keywords
    title = str(doc.get("title") or "")
    text = str(doc.get("text") or "")
    doc_id = str(doc.get("id") or "")
    combined = fold(f"{doc_id} {title} {text}")
    keywords = THEME_KEYWORDS.get(theme, [])
    matches = sum(1 for kw in keywords if kw in combined)
    return matches >= 1


@dataclass
class CityResult:
    city: str
    n: int = 0
    hit1: int = 0
    hit3: int = 0
    relevant_in_top3: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)

    @property
    def hit1_pct(self) -> float:
        return (self.hit1 / self.n * 100.0) if self.n else 0.0

    @property
    def hit3_pct(self) -> float:
        return (self.hit3 / self.n * 100.0) if self.n else 0.0

    @property
    def precision_at_3(self) -> float:
        return (self.relevant_in_top3 / (self.n * 3)) if self.n else 0.0


def load_golden_cities(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or GOLDEN_DEFAULT
    if not target.exists():
        raise FileNotFoundError(f"Golden cities dataset not found at {target}")
    rows = []
    with target.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{target.name}:{lineno} invalid JSON: {exc}") from exc
    return rows


def evaluate_cities(
    path: Path | None = None,
    *,
    k: int = 3,
    target_city: str | None = None,
) -> dict[str, Any]:
    reset_cache()
    rows = load_golden_cities(path)
    if target_city:
        rows = [r for r in rows if r.get("city") == target_city]

    results: dict[str, CityResult] = {city: CityResult(city=city) for city in CITIES}
    if target_city and target_city in results:
        results = {target_city: results[target_city]}

    for row in rows:
        city = row["city"]
        theme = row["theme"]
        q_text = row["question"]
        lang = row.get("lang", "es")
        expected_vars = row.get("expected_variable_ids", [])

        res = results.setdefault(city, CityResult(city=city))
        res.n += 1

        docs = retrieve(q_text, lang=lang, k=k)
        hit_at_1 = False
        hit_at_3 = False
        rel_count = 0

        for rank, doc in enumerate(docs, 1):
            c_match = matches_city(doc, city)
            t_match = matches_theme(doc, theme, expected_vars)
            if c_match and t_match:
                rel_count += 1
                hit_at_3 = True
                if rank == 1:
                    hit_at_1 = True

        if hit_at_1:
            res.hit1 += 1
        if hit_at_3:
            res.hit3 += 1
        res.relevant_in_top3 += rel_count

        if not hit_at_3:
            res.failures.append({
                "id": row.get("id"),
                "question": q_text,
                "theme": theme,
                "theme_name": row.get("theme_name"),
                "retrieved": [{"id": d.get("id"), "title": d.get("title")} for d in docs],
            })

    # Overall aggregates
    total_n = sum(r.n for r in results.values())
    total_hit1 = sum(r.hit1 for r in results.values())
    total_hit3 = sum(r.hit3 for r in results.values())
    total_rel = sum(r.relevant_in_top3 for r in results.values())

    summary = {
        "cities": {c: {
            "n": r.n,
            "hit1": r.hit1,
            "hit1_pct": round(r.hit1_pct, 1),
            "hit3": r.hit3,
            "hit3_pct": round(r.hit3_pct, 1),
            "precision_at_3": round(r.precision_at_3, 3),
            "failure_count": len(r.failures),
            "failures": r.failures,
        } for c, r in results.items()},
        "total": {
            "n": total_n,
            "hit1": total_hit1,
            "hit1_pct": round((total_hit1 / total_n * 100.0) if total_n else 0.0, 1),
            "hit3": total_hit3,
            "hit3_pct": round((total_hit3 / total_n * 100.0) if total_n else 0.0, 1),
            "precision_at_3": round((total_rel / (total_n * 3)) if total_n else 0.0, 3),
        },
    }
    return summary


def format_markdown_table(summary: dict[str, Any]) -> str:
    lines = [
        "| Ciudad | Preguntas | Hit@1 | Hit@1 % | Hit@3 | Hit@3 % | Precision@3 |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for city, data in summary["cities"].items():
        city_display = CITIES.get(city, city.capitalize())
        lines.append(
            f"| **{city_display}** | {data['n']} | {data['hit1']} | {data['hit1_pct']}% | "
            f"{data['hit3']} | {data['hit3_pct']}% | {data['precision_at_3']:.3f} |"
        )
    tot = summary["total"]
    lines.append(
        f"| **TOTAL** | **{tot['n']}** | **{tot['hit1']}** | **{tot['hit1_pct']}%** | "
        f"**{tot['hit3']}** | **{tot['hit3_pct']}%** | **{tot['precision_at_3']:.3f}** |"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=GOLDEN_DEFAULT, help="Path to golden questions JSONL")
    parser.add_argument("--city", choices=list(CITIES.keys()), help="Filter evaluation by city")
    parser.add_argument("--json", action="store_true", help="Print summary as JSON")
    parser.add_argument("--markdown", action="store_true", help="Print summary as Markdown table")
    parser.add_argument("--quiet", action="store_true", help="Suppress failure details")
    args = parser.parse_args(argv)

    summary = evaluate_cities(path=args.path, target_city=args.city)

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    table = format_markdown_table(summary)
    print("\n" + table + "\n")

    if not args.quiet and not args.markdown:
        total_fails = sum(len(c["failures"]) for c in summary["cities"].values())
        if total_fails > 0:
            print(f"Detalle de preguntas sin acierto en Top 3 ({total_fails} pendientes):")
            for city, cdata in summary["cities"].items():
                for f in cdata["failures"]:
                    print(f"  - [{city}] Tema {f['theme']}: {f['question']}")
                    if f["retrieved"]:
                        first = f["retrieved"][0]
                        print(f"      Top 1 devuelto: {first.get('id')} — {first.get('title')}")
                    else:
                        print("      Top 1 devuelto: (ninguno)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
