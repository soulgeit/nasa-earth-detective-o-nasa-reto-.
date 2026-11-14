# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""C2 - Gazetteer from GeoNames and natural regions with verified coordinates.

Sources (each verified live in this run):
- GeoNames cities15000: https://download.geonames.org/export/dump/cities15000.zip
  Licence CC BY 4.0, see https://www.geonames.org/export/
- Wikipedia API (prop=coordinates) for each natural region centre point.
  Wikipedia's coordinates are a point, not a polygon, so no bounding box is
  invented: `bbox` stays null unless a real polygon source is used.

All geocoding is done with a policy-compliant User-Agent and batched
requests, because both services rate-limit hard and reset connections when
hammered.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import zipfile
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hermes1.fetch_common import ROOT, fetch  # noqa: E402

GEONAMES_ZIP = "https://download.geonames.org/export/dump/cities15000.zip"
GEONAMES_LICENSE = "https://www.geonames.org/export/"
WIKI_API = "https://en.wikipedia.org/w/api.php"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

TODAY = "2026-11-14"
TOP_CITIES = 8000
PERU_CODE = "PE"

# Natural regions: (id, name_es, name_en, wiki_title, biome, nominatim_query)
# biome matches the 8 biome profiles used by the knowledge corpus.
REGIONS: list[tuple[str, str, str, str, str, str]] = [
    ("amazonia", "Amazonía", "Amazon Basin", "Amazon basin", "tropical_forest", "Amazon basin"),
    ("sahel", "Sahel", "Sahel", "Sahel", "savanna", "Sahel"),
    ("aral-sea", "Mar de Aral", "Aral Sea", "Aral Sea", "desert", "Aral Sea"),
    ("arctic", "Océano Ártico", "Arctic Ocean", "Arctic Ocean", "polar", "Arctic Ocean"),
    ("antarctica", "Antártida", "Antarctica", "Antarctica", "polar", "Antarctica"),
    ("greenland", "Groenlandia", "Greenland", "Greenland", "polar", "Greenland"),
    ("greenland-ice-sheet", "Capa de hielo de Groenlandia", "Greenland Ice Sheet", "Greenland ice sheet", "polar", "Greenland ice sheet"),
    ("himalaya", "Himalaya", "Himalaya", "Himalayas", "high_mountain", "Himalayas"),
    ("great-barrier-reef", "Gran Barrera de Coral", "Great Barrier Reef", "Great Barrier Reef", "coast", "Great Barrier Reef"),
    ("cordillera-blanca", "Cordillera Blanca", "Cordillera Blanca", "Cordillera Blanca", "high_mountain", "Cordillera Blanca, Peru"),
    ("lago-titicaca", "Lago Titicaca", "Lake Titicaca", "Lake Titicaca", "high_mountain", "Lake Titicaca"),
    ("madre-de-dios", "Madre de Dios", "Madre de Dios", "Department of Madre de Dios", "tropical_forest", "Madre de Dios Region, Peru"),
    ("desierto-sechura", "Desierto de Sechura", "Sechura Desert", "Sechura Desert", "desert", "Sechura Desert, Peru"),
    ("valle-ica", "Valle de Ica", "Ica Valley", "Ica, Peru", "agricultural_valley", "Ica, Peru"),
    ("loreto", "Loreto", "Loreto Region", "Department of Loreto", "tropical_forest", "Loreto Region, Peru"),
    ("sahara", "Sáhara", "Sahara", "Sahara", "desert", "Sahara"),
    ("gobi", "Desierto de Gobi", "Gobi Desert", "Gobi Desert", "desert", "Gobi Desert"),
    ("atacama", "Desierto de Atacama", "Atacama Desert", "Atacama Desert", "desert", "Atacama Desert"),
    ("patagonia", "Patagonia", "Patagonia", "Patagonia", "savanna", "Patagonia"),
    ("cerrado", "Cerrado", "Cerrado", "Cerrado", "savanna", "Cerrado"),
    ("pantanal", "Pantanal", "Pantanal", "Pantanal", "savanna", "Pantanal"),
    ("congo-basin", "Cuenca del Congo", "Congo Basin", "Congo Basin", "tropical_forest", "Congo Basin"),
    ("nile-delta", "Delta del Nilo", "Nile Delta", "Nile Delta", "agricultural_valley", "Nile Delta"),
    ("indus-river", "Río Indo", "Indus River", "Indus River", "agricultural_valley", "Indus River"),
    ("ganges-delta", "Delta del Ganges", "Ganges Delta", "Ganges Delta", "coast", "Ganges Delta"),
    ("mekong-delta", "Delta del Mekong", "Mekong Delta", "Mekong Delta", "coast", "Mekong Delta"),
    ("yamal", "Península de Yamal", "Yamal Peninsula", "Yamal Peninsula", "polar", "Yamal Peninsula"),
    ("tibetan-plateau", "Meseta del Tíbet", "Tibetan Plateau", "Tibetan Plateau", "high_mountain", "Tibetan Plateau"),
    ("andes", "Cordillera de los Andes", "Andes", "Andes", "high_mountain", "Andes"),
    ("altiplano", "Altiplano andino", "Altiplano", "Altiplano", "high_mountain", "Altiplano"),
    ("amazon-rainforest", "Selva amazónica", "Amazon rainforest", "Amazon rainforest", "tropical_forest", "Amazon rainforest"),
    ("atlantic-forest", "Mata Atlántica", "Atlantic Forest", "Atlantic Forest", "tropical_forest", "Atlantic Forest"),
    ("pampas", "Pampas", "Pampas", "Pampas", "agricultural_valley", "Pampas"),
    ("chaco", "Gran Chaco", "Gran Chaco", "Gran Chaco", "savanna", "Gran Chaco"),
    ("caatinga", "Caatinga", "Caatinga", "Caatinga", "desert", "Caatinga"),
    ("orinoco-basin", "Cuenca del Orinoco", "Orinoco Basin", "Orinoco", "savanna", "Orinoco"),
    ("lake-maracaibo", "Lago de Maracaibo", "Lake Maracaibo", "Lake Maracaibo", "coast", "Lake Maracaibo"),
    ("everglades", "Everglades", "Everglades", "Everglades", "coast", "Everglades"),
    ("mississippi-delta", "Delta del Misisipi", "Mississippi Delta", "Mississippi River Delta", "coast", "Mississippi River Delta"),
    ("colorado-delta", "Delta del Colorado", "Colorado River Delta", "Colorado River Delta", "desert", "Colorado River Delta"),
    ("salton-sea", "Mar de Salton", "Salton Sea", "Salton Sea", "desert", "Salton Sea"),
    ("central-valley", "Valle Central de California", "California Central Valley", "Central Valley (California)", "agricultural_valley", "Central Valley California"),
    ("rocky-mountains", "Montañas Rocosas", "Rocky Mountains", "Rocky Mountains", "high_mountain", "Rocky Mountains"),
    ("great-plains", "Grandes Llanuras", "Great Plains", "Great Plains", "savanna", "Great Plains"),
    ("north-slope", "North Slope de Alaska", "Alaska North Slope", "Alaska North Slope", "polar", "North Slope Alaska"),
    ("larsen-ice-shelf", "Barrera de hielo Larsen", "Larsen Ice Shelf", "Larsen Ice Shelf", "polar", "Larsen Ice Shelf"),
    ("ross-ice-shelf", "Barrera de hielo Ross", "Ross Ice Shelf", "Ross Ice Shelf", "polar", "Ross Ice Shelf"),
    ("weddell-sea", "Mar de Weddell", "Weddell Sea", "Weddell Sea", "polar", "Weddell Sea"),
    ("barents-sea", "Mar de Barents", "Barents Sea", "Barents Sea", "polar", "Barents Sea"),
    ("svalbard", "Svalbard", "Svalbard", "Svalbard", "polar", "Svalbard"),
    ("iceland", "Islandia", "Iceland", "Iceland", "polar", "Iceland"),
    ("alps", "Alpes", "Alps", "Alps", "high_mountain", "Alps"),
    ("mediterranean", "Cuenca del Mediterráneo", "Mediterranean Basin", "Mediterranean Sea", "coast", "Mediterranean Basin"),
    ("danube-delta", "Delta del Danubio", "Danube Delta", "Danube Delta", "coast", "Danube Delta"),
    ("dead-sea", "Mar Muerto", "Dead Sea", "Dead Sea", "desert", "Dead Sea"),
    ("caspian-sea", "Mar Caspio", "Caspian Sea", "Caspian Sea", "coast", "Caspian Sea"),
    ("lake-chad", "Lago Chad", "Lake Chad", "Lake Chad", "savanna", "Lake Chad"),
    ("kilimanjaro", "Kilimanjaro", "Kilimanjaro", "Mount Kilimanjaro", "high_mountain", "Mount Kilimanjaro"),
    ("serengeti", "Serengeti", "Serengeti", "Serengeti", "savanna", "Serengeti"),
    ("kalahari", "Kalahari", "Kalahari", "Kalahari Desert", "desert", "Kalahari Desert"),
    ("madagascar", "Madagascar", "Madagascar", "Madagascar", "tropical_forest", "Madagascar"),
    ("sundarbans", "Sundarbans", "Sundarbans", "Sundarbans", "coast", "Sundarbans"),
    ("borneo", "Borneo", "Borneo", "Borneo", "tropical_forest", "Borneo"),
    ("sumatra", "Sumatra", "Sumatra", "Sumatra", "tropical_forest", "Sumatra"),
    ("murray-darling", "Cuenca Murray-Darling", "Murray-Darling Basin", "Murray–Darling basin", "agricultural_valley", "Murray-Darling Basin"),
    ("antarctic-peninsula", "Península Antártica", "Antarctic Peninsula", "Antarctic Peninsula", "polar", "Antarctic Peninsula"),
    ("namib", "Desierto del Namib", "Namib Desert", "Namib", "desert", "Namib Desert"),
    ("greater-antilles", "Grandes Antillas", "Greater Antilles", "Greater Antilles", "coast", "Greater Antilles"),
]


def download_geonames() -> list[dict[str, Any]]:
    page = fetch(GEONAMES_ZIP, cache_key="geonames_cities15000")
    zf = zipfile.ZipFile(io.BytesIO(page.raw))
    name = "cities15000.txt"
    if name not in zf.namelist():
        raise SystemExit(f"unexpected GeoNames archive contents: {zf.namelist()}")

    rows: list[dict[str, Any]] = []
    with zf.open(name) as fh:
        reader = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter="\t")
        for row in reader:
            if len(row) < 15:
                continue
            rows.append(
                {
                    "geonameid": int(row[0]),
                    "name": row[1],
                    "ascii": row[2],
                    "alt_names": [n for n in (row[3] or "").split(",") if n.strip()],
                    "lat": float(row[4]),
                    "lon": float(row[5]),
                    "country": row[8],
                    "population": int(row[14] or 0),
                }
            )
    return rows


def select_cities(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    peru = [r for r in rows if r["country"] == PERU_CODE]
    ranked = sorted(rows, key=lambda r: r["population"], reverse=True)[:TOP_CITIES]
    chosen: dict[int, dict[str, Any]] = {r["geonameid"]: r for r in ranked}
    for r in peru:
        chosen[r["geonameid"]] = r

    out = []
    for r in sorted(chosen.values(), key=lambda r: (-r["population"], r["name"])):
        # Keep alternative names bounded: GeoNames lists many scripts; the
        # contract asks for Spanish and English spellings, which are present
        # in the list but not language-tagged, so we keep a capped subset.
        alt = [n for n in r["alt_names"] if n and n not in (r["name"], r["ascii"])][:8]
        out.append(
            {
                "name": r["name"],
                "ascii": r["ascii"],
                "alt_names": alt,
                "country": r["country"],
                "lat": round(r["lat"], 4),
                "lon": round(r["lon"], 4),
                "population": r["population"],
            }
        )
    return out


def wikidata_coordinates_batch(titles: list[str]) -> dict[str, dict[str, Any]]:
    """Resolve coordinates from Wikidata for many English Wikipedia titles.

    Wikidata returns P625 (coordinate location) reliably where the Wikipedia
    coordinates API does not, and it does not rate-limit a small batch of
    serially issued requests. When a page has P1332/P1333/P1334/P1335 (the
    extremes of a region) those are kept, but a 2-point "extremes" pair is not
    enough to build a box, so `bbox` is only built from a real pair of N/S and
    E/W values. Otherwise the box is null.
    """
    out: dict[str, dict[str, Any]] = {}
    for title in titles:
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbgetentities", "sites": "enwiki", "titles": title,
            "props": "claims|labels", "languages": "en", "format": "json",
        }
        key = "wikidata_" + "".join(c if c.isalnum() else "_" for c in title.lower())[:70]
        try:
            page = fetch(
                _wiki_url(url, params),
                cache_key=key,
                headers={
                    "User-Agent": "EarthTrendDetective/0.2 (NASA Space Apps team project; "
                                  "https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-)"
                },
            )
            data = json.loads(page.text)
        except Exception:
            continue
        for qid, ent in data.get("entities", {}).items():
            if qid == "-1":
                continue
            claims = ent.get("claims", {})

            def coord(pid: str) -> dict[str, Any] | None:
                try:
                    return claims[pid][0]["mainsnak"]["datavalue"]["value"]
                except (KeyError, IndexError, TypeError):
                    return None

            centre = coord("P625")
            if not centre:
                continue
            label = (ent.get("labels", {}).get("en") or {}).get("value") or title
            # Wikidata: P1332 = northernmost point, P1333 = southernmost,
            # P1334 = easternmost, P1335 = westernmost.
            north, south, east, west = coord("P1332"), coord("P1333"), coord("P1334"), coord("P1335")
            bbox = None
            if south and north and west and east:
                bbox = [
                    round(float(west["longitude"]), 4), round(float(south["latitude"]), 4),
                    round(float(east["longitude"]), 4), round(float(north["latitude"]), 4),
                ]
                # Sanity: the box must be non-degenerate and consistent.
                w, s, e, n = bbox
                if not (w < e and s < n) or (e - w) > 300:
                    bbox = None
            out[title] = {
                "lat": round(float(centre["latitude"]), 4),
                "lon": round(float(centre["longitude"]), 4),
                "title": label,
                "qid": qid,
                "url": f"https://www.wikidata.org/wiki/{qid}",
                "bbox": bbox,
                "bbox_source": "wikidata P1332/P1333/P1334/P1335" if bbox else None,
            }
            break
    return out


def _wiki_url(base: str, params: dict[str, Any]) -> str:
    from urllib.parse import urlencode
    return base + "?" + urlencode(params)


def build_regions() -> tuple[list[dict[str, Any]], list[str]]:
    """Region centres from Wikidata; bounding boxes from OSM Nominatim.

    The box is accepted only when Nominatim's centre agrees with Wikidata's
    within 1.5 degrees, so a same-named place elsewhere on Earth is rejected.
    A box that cannot be obtained stays null instead of being guessed.
    """
    regions: list[dict[str, Any]] = []
    problems: list[str] = []

    titles = [r[3] for r in REGIONS]
    coords = wikidata_coordinates_batch(titles)

    for rid, name_es, name_en, wiki_title, biome, osm_query in REGIONS:
        wiki = coords.get(wiki_title)
        if wiki is None:
            problems.append(f"{rid}: no Wikidata coordinates for {wiki_title!r}")
            continue

        bbox = wiki["bbox"]
        bbox_url = wiki["url"] if bbox else None
        bbox_source = wiki["bbox_source"]
        if not bbox:
            try:
                time.sleep(1.5)  # Nominatim usage policy: <= 1 request per second
                osm = nominatim_bbox(osm_query)
            except Exception:  # noqa: BLE001
                osm = None
            if osm and abs(osm["lat"] - wiki["lat"]) <= 1.5 and abs(osm["lon"] - wiki["lon"]) <= 1.5:
                w, s, e, n = osm["bbox"]
                if (e - w) >= 0.05 and (n - s) >= 0.05:
                    bbox = osm["bbox"]
                    bbox_url = f"{NOMINATIM}?q={osm_query}&format=jsonv2"
                    bbox_source = "OpenStreetMap Nominatim boundingbox"
                else:
                    problems.append(f"{rid}: OSM box is a near-point; left null")
            elif osm:
                problems.append(
                    f"{rid}: OSM centre ({osm['lat']},{osm['lon']}) disagrees with Wikidata "
                    f"({wiki['lat']},{wiki['lon']}); bbox left null"
                )
            else:
                problems.append(f"{rid}: no OSM bounding box; left null")

        regions.append(
            {
                "id": rid,
                "names": {"es": name_es, "en": name_en},
                "lat": wiki["lat"],
                "lon": wiki["lon"],
                "bbox": bbox,
                "biome": biome,
                "verified": {
                    "by": "hermes-1",
                    "at": TODAY,
                    "coordinates_url": wiki["url"],
                    "bbox_url": bbox_url,
                    "bbox_source": bbox_source,
                },
            }
        )
    return regions, problems


def nominatim_bbox(query: str) -> dict[str, Any] | None:
    """OSM bounding box for a place, fetched with a descriptive UA."""
    key = "nominatim_" + "".join(c if c.isalnum() else "_" for c in query.lower())[:60]
    url = f"{NOMINATIM}?q={query}&format=jsonv2&limit=1&addressdetails=0"
    page = fetch(
        url,
        cache_key=key,
        headers={
            "User-Agent": "EarthTrendDetective/0.2 (NASA Space Apps team project; "
                          "https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-)"
        },
    )
    data = json.loads(page.text)
    if not data:
        return None
    item = data[0]
    if "boundingbox" not in item:
        return None
    south, north, west, east = (float(x) for x in item["boundingbox"])
    return {
        "bbox": [round(west, 4), round(south, 4), round(east, 4), round(north, 4)],
        "lat": round(float(item["lat"]), 4),
        "lon": round(float(item["lon"]), 4),
        "display_name": item.get("display_name"),
    }


def main() -> int:
    license_page = fetch(GEONAMES_LICENSE, cache_key="geonames_export")
    rows = download_geonames()
    cities = select_cities(rows)

    gazetteer = {
        "schema": "gazetteer/1",
        "generated_at": TODAY,
        "source": {
            "name": "GeoNames cities15000",
            "url": GEONAMES_ZIP,
            "license": "CC BY 4.0",
            "license_url": license_page.final_url,
            "peru_included_in_full": True,
            "note": "~8000 most populated cities plus every Peruvian city in cities15000.",
        },
        "cities": cities,
    }

    regions, problems = build_regions()
    regions_doc = {
        "schema": "regions/1",
        "generated_at": TODAY,
        "note": "Coordinates from Wikipedia (prop=coordinates); boxes from OpenStreetMap Nominatim when consistent with the centre point.",
        "regions": regions,
    }

    out_cities = os.path.join(ROOT, "data", "catalog", "gazetteer.json")
    out_regions = os.path.join(ROOT, "data", "catalog", "regions.json")
    with open(out_cities, "w", encoding="utf-8") as fh:
        json.dump(gazetteer, fh, ensure_ascii=False)
    with open(out_regions, "w", encoding="utf-8") as fh:
        json.dump(regions_doc, fh, ensure_ascii=False, indent=1)

    peru = sum(1 for c in cities if c["country"] == "PE")
    with_bbox = sum(1 for r in regions if r["bbox"])
    print(f"cities={len(cities)} (Peru={peru}) -> {out_cities}")
    print(f"regions={len(regions)} with_bbox={with_bbox} -> {out_regions}")
    for p in problems:
        print("  !", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
