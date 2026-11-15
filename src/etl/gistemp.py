# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Conector GISTEMP v4 (rejilla 2°x2°, anomalia de temperatura desde 1880).

Archivo y estructura comprobados en vivo el 2026-11-14:
`https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz` (25,9 MB, HTTP 200)

    dims: lat=90, lon=180, time=1762, nv=2
    variables: lat, lon, time (days since 1800-01-01), time_bnds,
               tempanomaly(time, lat, lon) int16, scale_factor=0.01, _FillValue=32767, units K
    history: "... Base: 1951-1980"

- Anomalia en K (delta de temperatura: numericamente igual en °C).
- `_FillValue` -> `null`.
- Solo se usa el paquete estandar (gzip + scipy.io.netcdf_file): no se anade
  `netCDF4` ni `xarray` a `requirements.txt` para una dependencia opcional.
"""

from __future__ import annotations

import gzip
import hashlib
import math
import os
from datetime import datetime, timedelta, timezone

from . import cache, catalog
from .errors import DataUnavailable
from .http import UpstreamError, UpstreamTimeout, get as http_get

URL = "https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz"
CACHE_TTL_DAYS = 30.0
CITATION = (
    "GISTEMP Team, 2026: GISS Surface Temperature Analysis (GISTEMP), version 4. "
    "NASA Goddard Institute for Space Studies. Lenssen et al. 2019, JGR Atmospheres."
)
NATIVE_RESOLUTION = "2° x 2°"


# --------------------------------------------------------------------------- #
# descarga y cache del archivo
# --------------------------------------------------------------------------- #
def _download() -> tuple[str, dict]:
    """Descarga (o reutiliza) el .nc y lo deja descomprimido en la cache.

    Devuelve (ruta_nc, provenance_base).
    """
    cached = cache.load(URL, ttl_days=CACHE_TTL_DAYS)
    if cached is not None:
        body, meta = cached["body"], cached["meta"]
    else:
        try:
            resp = http_get(URL)
        except UpstreamTimeout as exc:
            raise DataUnavailable("UPSTREAM_TIMEOUT", f"{URL}: {exc}") from exc
        except UpstreamError as exc:
            raise DataUnavailable("UPSTREAM_ERROR", f"{URL}: {exc}") from exc
        if resp.status_code != 200:
            raise DataUnavailable("UPSTREAM_ERROR", f"HTTP {resp.status_code} {URL}")
        body = resp.content
        meta = cache.store(URL, body, status=resp.status_code)

    directory = os.environ.get("DATA_CACHE_DIR") or os.path.join("data", "cache")
    nc_path = os.path.join(directory, "gistemp1200_GHCNv4_ERSSTv5.nc")
    sha = hashlib.sha256(body).hexdigest()
    if not (os.path.exists(nc_path) and os.path.getsize(nc_path) > 0):
        try:
            data = gzip.decompress(body)
        except OSError as exc:
            raise DataUnavailable("UPSTREAM_ERROR", f"gzip corrupto: {exc}") from exc
        os.makedirs(directory, exist_ok=True)
        tmp = nc_path + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, nc_path)
    provenance = {
        "kind": "nasa_file",
        "source": "NASA GISTEMP v4",
        "underlying": "GHCNv4 + ERSSTv5 (base 1951-1980)",
        "request_url": URL,
        "retrieved_at": meta.get("fetched_at"),
        "sha256": sha,
        "native_resolution": NATIVE_RESOLUTION,
        "citation": CITATION,
    }
    return nc_path, provenance


class _Open:
    """Wrapper minimo sobre scipy.io.netcdf_file que cierra el mmap."""

    def __init__(self, path: str):
        from scipy.io import netcdf_file

        self._f = netcdf_file(path, "r", mmap=False)

    def __enter__(self):
        return self._f

    def __exit__(self, *exc):
        self._f.close()
        return False


def _times(ds) -> list[tuple[int, int]]:
    var = ds.variables["time"]
    units = (var._attributes.get("units") or b"days since 1800-01-01").decode()
    base_str = units.split("since", 1)[1].strip()
    base = datetime.strptime(base_str[:10], "%Y-%m-%d")
    out = []
    for raw in var[:]:
        d = base + timedelta(days=int(raw))
        out.append((d.year, d.month))
    return out


def _lat_lon(ds):
    lats = [float(v) for v in ds.variables["lat"][:]]
    lons = [float(v) for v in ds.variables["lon"][:]]
    return lats, lons


def _anomaly(ds) -> tuple["object", float]:
    var = ds.variables["tempanomaly"]
    attrs = var._attributes
    scale = float(attrs.get("scale_factor", 1.0))
    fill = attrs.get("_FillValue")
    fill = int(fill) if fill is not None else None
    return var, (scale, fill)


def _cell_indices(lats: list[float], lons: list[float], west: float, south: float, east: float, north: float):
    """Indices de celdas cuya area cae dentro de la caja (rejilla de centros)."""
    lat_idx = [i for i, la in enumerate(lats) if south <= la <= north]
    lon_idx = [j for j, lo in enumerate(lons) if _lon_in(lo, west, east)]
    return lat_idx, lon_idx


def _lon_in(lon: float, west: float, east: float) -> bool:
    if west <= east:
        return west <= lon <= east
    # Caja que cruza el antimeridiano.
    return lon >= west or lon <= east


def _values_for(ds, lat_idx, lon_idx, var_info, n_times: int):
    var, (scale, fill) = var_info
    out = []
    for t in range(n_times):
        slab = var[t]
        vals = []
        weights = []
        for i in lat_idx:
            w = math.cos(math.radians(float(ds.variables["lat"][i])))
            for j in lon_idx:
                raw = int(slab[i][j])
                if fill is not None and raw == fill:
                    continue
                vals.append(raw * scale)
                weights.append(w)
        if not vals:
            out.append((None, 0))
        else:
            out.append((sum(v * w for v, w in zip(vals, weights)) / sum(weights), len(vals)))
    return out


def series(variable_id: str, *, lat=None, lon=None, bbox=None, start=None, end=None) -> dict:
    card = catalog.get_variable(variable_id)
    if card.get("connector") != "gistemp":
        raise DataUnavailable("VARIABLE_UNKNOWN", f"{variable_id} no es de GISTEMP")
    nc_path, provenance = _download()
    with _Open(nc_path) as ds:
        times = _times(ds)
        lats, lons = _lat_lon(ds)
        var_info = _anomaly(ds)
        if bbox is not None:
            west, south, east, north = (float(v) for v in bbox)
            if south < -90 or north > 90:
                raise DataUnavailable("OUT_OF_COVERAGE", f"bbox fuera de rango: {bbox}")
            region = {"kind": "bbox", "name": None, "lat": None, "lon": None, "bbox": list(bbox)}
            aggregation = "area_mean_coslat"
            lat_idx, lon_idx = _cell_indices(lats, lons, west, south, east, north)
            if not lat_idx or not lon_idx:
                raise DataUnavailable("OUT_OF_COVERAGE", f"la caja {bbox} no cubre celdas GISTEMP")
        else:
            if lat is None or lon is None:
                # Sin coordenadas: la serie GLOBAL del planeta (la referencia del
                # calentamiento global). Se declara en `region` y `aggregation`.
                region = {
                    "kind": "named",
                    "name": "Global (all GISTEMP land+ocean cells)",
                    "lat": None,
                    "lon": None,
                    "bbox": None,
                }
                aggregation = "area_mean_coslat"
                lat_idx, lon_idx = list(range(len(lats))), list(range(len(lons)))
            else:
                lat_f, lon_f = float(lat), float(lon)
                if not (-90 <= lat_f <= 90) or not (-180 <= lon_f <= 180):
                    raise DataUnavailable("OUT_OF_COVERAGE", f"coordenadas fuera de rango: {lat},{lon}")
                # La rejilla son centros de celda de 2 grados: se toma la mas cercana.
                i = min(range(len(lats)), key=lambda k: abs(lats[k] - lat_f))
                j = min(range(len(lons)), key=lambda k: abs(((lons[k] - lon_f + 180) % 360) - 180))
                region = {"kind": "point", "name": None, "lat": lat_f, "lon": lon_f, "bbox": None}
                aggregation = "point"
                lat_idx, lon_idx = [i], [j]
                provenance = dict(provenance)
                provenance["grid_cell"] = {"lat": lats[i], "lon": lons[j]}

        values = _values_for(ds, lat_idx, lon_idx, var_info, len(times))

    lo = str(start)[:7] if start else None
    hi = str(end)[:7] if end else None
    data = []
    for (year, month), (val, _n) in zip(times, values):
        date = f"{year:04d}-{month:02d}"
        if lo and date < lo:
            continue
        if hi and date > hi:
            continue
        data.append({"date": date, "value": round(val, 4) if val is not None else None})
    if not data:
        raise DataUnavailable("OUT_OF_COVERAGE", f"sin meses entre {start} y {end}")
    if all(pt["value"] is None for pt in data):
        raise DataUnavailable("OUT_OF_COVERAGE", f"sin datos GISTEMP en {bbox or (lat, lon)}")
    provenance = dict(provenance)
    provenance["n_missing"] = sum(1 for pt in data if pt["value"] is None)
    return {
        "schema": "timeseries/2",
        "variable_id": variable_id,
        "unit": card.get("unit") or "°C (anomaly vs 1951-1980)",
        "cadence": "monthly",
        "region": region,
        "aggregation": aggregation,
        "data": data,
        "provenance": provenance,
    }


def grid(variable_id: str, bbox, *, start=None, end=None) -> dict:
    """Rejilla global o por caja: {"lats","lons","dates","values"[t][lat][lon],...}."""
    card = catalog.get_variable(variable_id)
    if card.get("connector") != "gistemp":
        raise DataUnavailable("VARIABLE_UNKNOWN", f"{variable_id} no es de GISTEMP")
    nc_path, provenance = _download()
    with _Open(nc_path) as ds:
        times = _times(ds)
        lats, lons = _lat_lon(ds)
        if bbox is not None:
            west, south, east, north = (float(v) for v in bbox)
            lat_idx, lon_idx = _cell_indices(lats, lons, west, south, east, north)
        else:
            lat_idx, lon_idx = list(range(len(lats))), list(range(len(lons)))
        if not lat_idx or not lon_idx:
            raise DataUnavailable("OUT_OF_COVERAGE", f"bbox sin celdas: {bbox}")
        var, (scale, fill) = _anomaly(ds)
        lo = str(start)[:7] if start else None
        hi = str(end)[:7] if end else None
        sel = [
            t
            for t, (y, m) in enumerate(times)
            if (not lo or f"{y:04d}-{m:02d}" >= lo) and (not hi or f"{y:04d}-{m:02d}" <= hi)
        ]
        dates = [f"{times[t][0]:04d}-{times[t][1]:02d}" for t in sel]
        values = []
        for t in sel:
            slab = var[t]
            rows = []
            for i in lat_idx:
                row = []
                for j in lon_idx:
                    raw = int(slab[i][j])
                    row.append(None if (fill is not None and raw == fill) else raw * scale)
                rows.append(row)
            values.append(rows)
    return {
        "lats": [lats[i] for i in lat_idx],
        "lons": [lons[j] for j in lon_idx],
        "dates": dates,
        "values": values,
        "unit": card.get("unit"),
        "provenance": provenance,
    }
