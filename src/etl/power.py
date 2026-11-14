# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Conector NASA POWER (MERRA-2 / CERES) - mensual, punto y regional.

Reglas comprobadas en vivo el 2026-11-14 (ver reports/antigravity-1.md):
- Punto: `parameters` acepta hasta 20; la respuesta es `Feature` con la serie en
  `properties.parameter.<P>`, unidades en `parameters.<P>.units` y version en
  `header.api.version` (v2.10.0).
- Regional: **un solo parametro** por peticion; caja de **2 a 10 grados por eje**
  (`422` fuera de ese rango). La respuesta es `features[]`, cada una con
  `geometry.coordinates = [lon, lat, elev]` y su propia serie.
- Claves `YYYYMM`; la clave `YYYY13` es el valor anual: **se descarta**.
- Relleno `header.fill_value` (-999.0) -> `null`.
- Cobertura verificada hoy: hasta 2026-11, con los ultimos meses en relleno.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

from . import cache, catalog
from .errors import DataUnavailable
from .http import UpstreamError, UpstreamTimeout, get as http_get

BASE = "https://power.larc.nasa.gov/api/temporal/monthly"
COMMUNITY = "AG"
POINT_MAX_PARAMS = 20          # documentado: "A maximum of 20 parameters"
REGIONAL_MAX_DEGREES = 10.0    # verificado: "Please provide a maximum of 10 degree range"
REGIONAL_MIN_DEGREES = 2.0     # verificado: "Please provide at least a 2 degree range"
NATIVE_RESOLUTION = "0.5° x 0.625°"
CACHE_TTL_DAYS = 30.0


# --------------------------------------------------------------------------- #
# utilidades de fechas
# --------------------------------------------------------------------------- #
def _parse_ym(value: str) -> tuple[int, int]:
    value = value.strip()
    if len(value) == 10:  # AAAA-MM-DD
        return int(value[0:4]), int(value[5:7])
    if len(value) == 8:   # AAAAMMDD
        return int(value[0:4]), int(value[4:6])
    if len(value) == 7:   # AAAA-MM
        return int(value[0:4]), int(value[5:7])
    if len(value) == 4:   # AAAA
        return int(value[0:4]), 1
    raise ValueError(f"fecha no reconocida: {value!r}")


def _as_year(value: str) -> int:
    return _parse_ym(value)[0]


def default_period(card: dict) -> tuple[str, str]:
    """Periodo por defecto: desde el inicio del catalogo hasta el ultimo ano completo.

    POWER publica datos meteorologicos del ano en curso solo hasta el mes anterior;
    por eso el fin por defecto es el 31-dic del ano pasado (hoy 2026 -> 2025-12),
    que es exactamente lo que exige el criterio de aceptacion D1 (540 puntos).
    """
    start = str(card.get("start") or "1981-01")
    last_full_year = datetime.now(timezone.utc).year - 1
    return start, f"{last_full_year}-12"


def _month_keys(series: dict) -> list[str]:
    """Claves YYYYMM ordenadas, sin la clave anual YYYY13."""
    # `YYYY13` es el agregado anual de POWER: no es un mes y se descarta.
    keys = [k for k in series if len(k) == 6 and not k.endswith("13")]
    return sorted(keys)


def _iso_month(key: str) -> str:
    return f"{key[0:4]}-{key[4:6]}"


def _value(raw, fill: float) -> float | None:
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if val == fill or not math.isfinite(val):
        return None
    return val


# --------------------------------------------------------------------------- #
# peticiones
# --------------------------------------------------------------------------- #
def point_url(variable_id: str, lat: float, lon: float, start: str, end: str) -> str:
    query = urlencode(
        {
            "parameters": variable_id,
            "community": COMMUNITY,
            "longitude": f"{lon:.2f}",
            "latitude": f"{lat:.2f}",
            "start": _as_year(start),
            "end": _as_year(end),
            "format": "JSON",
        }
    )
    return f"{BASE}/point?{query}"


def regional_url(variable_id: str, bbox, start: str, end: str) -> str:
    west, south, east, north = bbox
    query = urlencode(
        {
            "parameters": variable_id,
            "community": COMMUNITY,
            "latitude-min": f"{south:.2f}",
            "latitude-max": f"{north:.2f}",
            "longitude-min": f"{west:.2f}",
            "longitude-max": f"{east:.2f}",
            "start": _as_year(start),
            "end": _as_year(end),
            "format": "JSON",
        }
    )
    return f"{BASE}/regional?{query}"


def _fetch(url: str) -> tuple[dict, dict, str]:
    """Descarga (o lee cache): devuelve (json, provenance, sha256)."""
    cached = cache.load(url, ttl_days=CACHE_TTL_DAYS)
    if cached is not None:
        body, meta = cached["body"], cached["meta"]
    else:
        try:
            resp = http_get(url)
        except UpstreamTimeout as exc:
            raise DataUnavailable("UPSTREAM_TIMEOUT", f"{url}: {exc}") from exc
        except UpstreamError as exc:
            raise DataUnavailable("UPSTREAM_ERROR", f"{url}: {exc}") from exc
        if resp.status_code != 200:
            raise DataUnavailable("UPSTREAM_ERROR", f"HTTP {resp.status_code} {url}: {resp.text[:300]}")
        body = resp.content
        meta = cache.store(url, body, status=resp.status_code)
    try:
        doc = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DataUnavailable("UPSTREAM_ERROR", f"respuesta no JSON de {url}: {exc}") from exc
    if doc.get("messages"):
        raise DataUnavailable("UPSTREAM_ERROR", f"{url}: {doc['messages']}")
    header = doc.get("header") or {}
    api = header.get("api") or {}
    sources = header.get("sources") or []
    version = api.get("version")
    provenance = {
        "kind": "nasa_api",
        "source": f"NASA POWER {version}" if version else "NASA POWER",
        "underlying": _underlying(sources),
        "request_url": url,
        "retrieved_at": meta.get("fetched_at"),
        "sha256": hashlib.sha256(body).hexdigest(),
        "native_resolution": NATIVE_RESOLUTION,
        "citation": "NASA Prediction Of Worldwide Energy Resources (POWER) project; "
                    "https://power.larc.nasa.gov/",
    }
    return doc, provenance, provenance["sha256"]


def _underlying(sources: list[str]) -> str | None:
    if not sources:
        return None
    names = ["MERRA-2" if s.upper() == "MERRA2" else s for s in sources]
    return ", ".join(names)


def fetch_point_raw(variable_id: str, lat: float, lon: float, start: str, end: str) -> dict:
    doc, _, _ = _fetch(point_url(variable_id, lat, lon, start, end))
    return doc


def fetch_regional_raw(variable_id: str, bbox, start: str, end: str) -> dict:
    doc, _, _ = _fetch(regional_url(variable_id, bbox, start, end))
    return doc


# --------------------------------------------------------------------------- #
# parseo de respuestas reales
# --------------------------------------------------------------------------- #
def parse_point_response(doc: dict, variable_id: str) -> dict:
    """Convierte una respuesta `point` en {dates, values, unit, fill, header}."""
    props = doc.get("properties") or {}
    params = props.get("parameter") or {}
    if variable_id not in params:
        raise DataUnavailable("VARIABLE_UNKNOWN", f"{variable_id} no viene en la respuesta de POWER")
    root_header = doc.get("header") or {}
    fill = float(root_header.get("fill_value", -999.0))
    units = ((doc.get("parameters") or {}).get(variable_id) or {}).get("units")
    series = params[variable_id]
    keys = _month_keys(series)
    if not keys:
        raise DataUnavailable("UPSTREAM_ERROR", "respuesta de POWER sin claves mensuales")
    return {
        "dates": [_iso_month(k) for k in keys],
        "values": [_value(series[k], fill) for k in keys],
        "unit": units,
        "fill": fill,
        "header": root_header,
        "geometry": doc.get("geometry") or {},
    }


def parse_regional_response(doc: dict, variable_id: str) -> dict:
    """Convierte una respuesta `regional` en celdas con su serie."""
    features = doc.get("features") or []
    root_header = doc.get("header") or {}
    fill = float(root_header.get("fill_value", -999.0))
    units = ((doc.get("parameters") or {}).get(variable_id) or {}).get("units")
    cells = []
    for feat in features:
        coords = (feat.get("geometry") or {}).get("coordinates") or []
        params = (feat.get("properties") or {}).get("parameter") or {}
        if len(coords) < 2 or variable_id not in params:
            continue
        series = params[variable_id]
        keys = _month_keys(series)
        if not keys:
            continue
        cells.append(
            {
                "lon": float(coords[0]),
                "lat": float(coords[1]),
                "elev": float(coords[2]) if len(coords) > 2 else None,
                "dates": [_iso_month(k) for k in keys],
                "values": [_value(series[k], fill) for k in keys],
            }
        )
    if not cells:
        raise DataUnavailable("OUT_OF_COVERAGE", "la caja no contiene celdas con datos")
    return {"cells": cells, "unit": units, "fill": fill, "header": root_header}


# --------------------------------------------------------------------------- #
# troceo de cajas (POWER: maximo 10 grados por eje)
# --------------------------------------------------------------------------- #
def _tiles(bbox) -> list[tuple[float, float, float, float]]:
    west, south, east, north = (float(v) for v in bbox)
    dlat = north - south
    dlon = east - west
    if dlat <= 0 or dlon <= 0:
        raise DataUnavailable("OUT_OF_COVERAGE", f"bbox invalida: {bbox}")
    n_lat = max(1, math.ceil(dlat / REGIONAL_MAX_DEGREES))
    n_lon = max(1, math.ceil(dlon / REGIONAL_MAX_DEGREES))
    step_lat = dlat / n_lat
    step_lon = dlon / n_lon
    tiles = []
    for i in range(n_lat):
        for j in range(n_lon):
            tiles.append(
                (
                    round(west + j * step_lon, 6),
                    round(south + i * step_lat, 6),
                    round(west + (j + 1) * step_lon, 6),
                    round(south + (i + 1) * step_lat, 6),
                )
            )
    return tiles


def _bbox_span(bbox) -> tuple[float, float]:
    west, south, east, north = (float(v) for v in bbox)
    return north - south, east - west


# --------------------------------------------------------------------------- #
# API publica del conector
# --------------------------------------------------------------------------- #
def series(variable_id: str, *, lat=None, lon=None, bbox=None, start=None, end=None) -> dict:
    """TimeSeries v2 (contrato §3) desde POWER."""
    card = catalog.get_variable(variable_id)
    if card.get("connector") != "power":
        raise DataUnavailable("VARIABLE_UNKNOWN", f"{variable_id} no es del conector power")
    start_def, end_def = default_period(card)
    start = str(start or start_def)
    end = str(end or end_def)
    if _as_year(start) > _as_year(end):
        raise DataUnavailable("OUT_OF_COVERAGE", f"start {start} posterior a end {end}")

    if bbox is not None:
        return _series_bbox(variable_id, card, bbox, start, end)
    if lat is None or lon is None:
        raise DataUnavailable("OUT_OF_COVERAGE", "se necesita lat/lon o bbox")
    lat_f, lon_f = float(lat), float(lon)
    _check_coords(lat_f, lon_f)
    return _series_point(variable_id, card, lat_f, lon_f, start, end)


def _check_coords(lat: float, lon: float) -> None:
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise DataUnavailable("OUT_OF_COVERAGE", f"coordenadas fuera de rango: {lat}, {lon}")


def _unit(card: dict, api_unit: str | None, power_name: str | None) -> str:
    return card.get("unit") or api_unit or power_name or ""


def _cover(dates: list[str], start: str, end: str) -> list[int]:
    s, e = _iso_month(f"{_as_year(start):04d}{_parse_ym(start)[1]:02d}"), _iso_month(
        f"{_as_year(end):04d}{_parse_ym(end)[1]:02d}"
    )
    return [i for i, d in enumerate(dates) if s <= d <= e]


def _tp(name: str, kind: str, lat=None, lon=None, bbox=None) -> dict:
    return {"kind": kind, "name": name, "lat": lat, "lon": lon, "bbox": list(bbox) if bbox else None}


def _series_point(variable_id: str, card: dict, lat: float, lon: float, start: str, end: str) -> dict:
    url = point_url(variable_id, lat, lon, start, end)
    doc, provenance, _ = _fetch(url)
    parsed = parse_point_response(doc, variable_id)
    keep = _cover(parsed["dates"], start, end)
    if not keep:
        raise DataUnavailable("OUT_OF_COVERAGE", f"sin meses entre {start} y {end}")
    data = [{"date": parsed["dates"][i], "value": parsed["values"][i]} for i in keep]
    if all(pt["value"] is None for pt in data):
        raise DataUnavailable("OUT_OF_COVERAGE", f"POWER no tiene datos para {variable_id} en {lat},{lon}")
    return {
        "schema": "timeseries/2",
        "variable_id": variable_id,
        "unit": _unit(card, parsed["unit"], card.get("power_longname")),
        "cadence": "monthly",
        "region": _tp(None, "point", lat=lat, lon=lon),
        "aggregation": "point",
        "data": data,
        "provenance": provenance,
    }


def _series_bbox(variable_id: str, card: dict, bbox, start: str, end: str) -> dict:
    west, south, east, north = (float(v) for v in bbox)
    dlat, dlon = _bbox_span(bbox)
    if dlat <= 0 or dlon <= 0:
        raise DataUnavailable("OUT_OF_COVERAGE", f"bbox invalida: {bbox}")
    if south < -90 or north > 90 or west < -180 or east > 180:
        raise DataUnavailable("OUT_OF_COVERAGE", f"bbox fuera de rango: {bbox}")

    # Caja pequena: POWER exige >= 2 grados; se consulta el centroide y se declara.
    if dlat < REGIONAL_MIN_DEGREES or dlon < REGIONAL_MIN_DEGREES:
        lat_c = (south + north) / 2.0
        lon_c = (west + east) / 2.0
        ts = _series_point(variable_id, card, round(lat_c, 2), round(lon_c, 2), start, end)
        ts["region"] = _tp(None, "bbox", bbox=bbox)
        ts["aggregation"] = "point"
        ts["provenance"]["aggregation_note"] = (
            "bbox smaller than POWER's 2 degree minimum; point requested at the centroid "
            "(see aggregation)"
        )
        return ts

    grid = _regional_grid(variable_id, card, bbox, start, end)
    dates = grid["dates"]
    area_mean, cover = _coslat_mean(grid)
    data = [{"date": d, "value": v} for d, v in zip(dates, area_mean)]
    if not data:
        raise DataUnavailable("OUT_OF_COVERAGE", f"sin meses entre {start} y {end} en {bbox}")
    provenance = grid["provenance"]
    provenance["cells"] = len(grid["cells"])
    provenance["n_missing_cells"] = int(sum(1 for c in cover if c == 0))
    provenance["request_urls_count"] = len(grid["request_urls"])
    if len(grid["request_urls"]) > 1:
        provenance["request_urls"] = grid["request_urls"]
    return {
        "schema": "timeseries/2",
        "variable_id": variable_id,
        "unit": _unit(card, grid["unit"], card.get("power_longname")),
        "cadence": "monthly",
        "region": _tp(None, "bbox", bbox=bbox),
        "aggregation": "area_mean_coslat",
        "data": data,
        "provenance": provenance,
    }


def _regional_grid(variable_id: str, card: dict, bbox, start: str, end: str) -> dict:
    """Consulta una o varias teselas (<=10 grados) y une las celdas por (lat, lon)."""
    tiles = _tiles(bbox)
    cells_by_key: dict[tuple[float, float], dict] = {}
    request_urls: list[str] = []
    date_sets: set[tuple[str, ...]] = set()
    units = None
    provenance = None
    for tile in tiles:
        url = regional_url(variable_id, tile, start, end)
        request_urls.append(url)
        try:
            doc, prov, _ = _fetch(url)
        except DataUnavailable as exc:
            if len(tiles) == 1:
                raise
            # Una tesela sin datos no invalida el resto; se anota.
            request_urls.append(f"# {tile}: {exc.code}")
            continue
        parsed = parse_regional_response(doc, variable_id)
        units = units or parsed["unit"]
        provenance = provenance or prov
        date_sets.add(tuple(parsed["cells"][0]["dates"]))
        for cell in parsed["cells"]:
            key = (cell["lat"], cell["lon"])
            if key in cells_by_key:
                # Celdas repetidas en el borde de dos teselas: nos quedamos con la primera.
                continue
            cells_by_key[key] = cell
    if not cells_by_key or provenance is None:
        raise DataUnavailable("OUT_OF_COVERAGE", f"ninguna tesela de {bbox} devolvio datos")
    if len(date_sets) > 1:
        raise DataUnavailable("UPSTREAM_ERROR", "teselas con rejillas temporales distintas")
    dates = list(cells_by_key[sorted(cells_by_key)[0]]["dates"])
    keep = _cover(dates, start, end)
    if not keep:
        raise DataUnavailable("OUT_OF_COVERAGE", f"sin meses entre {start} y {end}")
    cells = []
    for key in sorted(cells_by_key, key=lambda k: (-k[0], k[1])):
        cell = cells_by_key[key]
        cells.append({"lat": key[0], "lon": key[1], "values": [cell["values"][i] for i in keep]})
    return {
        "dates": [dates[i] for i in keep],
        "cells": cells,
        "unit": units,
        "provenance": provenance,
        "request_urls": request_urls,
    }


def _coslat_mean(grid: dict) -> tuple[list[float | None], list[int]]:
    """Media ponderada por cos(lat) por fecha. None si ninguna celda tiene dato."""
    n_dates = len(grid["dates"])
    sums = [0.0] * n_dates
    weights = [0.0] * n_dates
    counts = [0] * n_dates
    for cell in grid["cells"]:
        w = math.cos(math.radians(cell["lat"]))
        for i, val in enumerate(cell["values"]):
            if val is None:
                continue
            sums[i] += val * w
            weights[i] += w
            counts[i] += 1
    means = [round(sums[i] / weights[i], 6) if weights[i] > 0 else None for i in range(n_dates)]
    return means, counts


def grid(variable_id: str, bbox, *, start=None, end=None) -> dict:
    """Rejilla de celdas para el mapa de tendencias (contrato §6).

    -> {"lats", "lons", "dates", "values"[t][lat][lon], "unit", "provenance"}
    """
    card = catalog.get_variable(variable_id)
    if card.get("connector") != "power":
        raise DataUnavailable("VARIABLE_UNKNOWN", f"{variable_id} no es del conector power")
    start_def, end_def = default_period(card)
    start = str(start or start_def)
    end = str(end or end_def)
    dlat, dlon = _bbox_span(bbox)
    if dlat < REGIONAL_MIN_DEGREES or dlon < REGIONAL_MIN_DEGREES:
        raise DataUnavailable(
            "BBOX_TOO_LARGE",
            "get_grid necesita una caja de al menos 2x2 grados (limite de POWER para regional)",
        )
    data = _regional_grid(variable_id, card, bbox, start, end)
    lats = sorted({c["lat"] for c in data["cells"]}, reverse=True)
    lons = sorted({c["lon"] for c in data["cells"]})
    lat_idx = {v: i for i, v in enumerate(lats)}
    lon_idx = {v: i for i, v in enumerate(lons)}
    values: list[list[list[float | None]]] = [
        [[None for _ in lons] for _ in lats] for _ in data["dates"]
    ]
    for cell in data["cells"]:
        i, j = lat_idx[cell["lat"]], lon_idx[cell["lon"]]
        for t, val in enumerate(cell["values"]):
            values[t][i][j] = val
    return {
        "lats": lats,
        "lons": lons,
        "dates": data["dates"],
        "values": values,
        "unit": _unit(card, data["unit"], card.get("power_longname")),
        "provenance": data["provenance"],
    }


# --------------------------------------------------------------------------- #
# Adaptadores de compatibilidad para el motor v2 (`src/api/main.py`)
# --------------------------------------------------------------------------- #
def _year_to_month(value) -> str | None:
    """Acepta 2000, "2000", 202001, "2020-01" o "20240131" -> "AAAA-MM". None pasa None."""
    if value is None:
        return None
    text = str(value).strip()
    if len(text) >= 7 and text[4] == "-":          # ya viene como AAAA-MM
        return text[:7]
    if len(text) >= 6 and text[:4].isdigit() and text[4:6].isdigit():
        return f"{text[:4]}-{text[4:6]}"
    return f"{text[:4]}-01"


def _period(start_year, end_year) -> tuple[str | None, str | None]:
    start = _year_to_month(start_year)
    if end_year is None:
        return start, None
    text = str(end_year)
    # Un ano suelto (2000 o "2000") significa "hasta diciembre de ese ano".
    # Ojo: "2024-12" ya mide 7 caracteres; comprobar la longitud seria un bug.
    if len(text) == 4:
        text = f"{text}-12"
    return start, _year_to_month(text)


def get_power_point_series(param, lat, lon, start_year=None, end_year=None, name=None) -> dict:
    """Firma del conector anterior, sobre el conector vigente (datos reales)."""
    start, end = _period(start_year, end_year)
    ts = series(param, lat=lat, lon=lon, start=start, end=end)
    if name:
        ts["region"]["name"] = name
    return ts


def get_power_regional_series(param, bbox, start_year=None, end_year=None, name=None) -> dict:
    start, end = _period(start_year, end_year)
    ts = series(param, bbox=bbox, start=start, end=end)
    if name:
        ts["region"]["name"] = name
    return ts


def get_power_grid(param, bbox, start_year=None, end_year=None) -> dict:
    start, end = _period(start_year, end_year)
    return grid(param, bbox, start=start, end=end)
