# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Conector oficial para NSIDC Sea Ice Index v4 (National Snow and Ice Data Center / NOAA).
Obtiene series temporales mensuales de extensión de hielo marino en el Ártico y Antártico (1979-presente).
Cumple con el contrato timeseries/2 y las reglas de cero datos sintéticos.
"""

import os
import csv
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

from src.etl.power import DataUnavailable

NSIDC_BASE_URL = "https://noaadata.apps.nsidc.org/NOAA/G02135"
CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 días


def _get_cache_dir() -> Path:
    """Retorna directorio de caché persistente para NSIDC."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    cache_dir = root_dir / "data" / "cache" / "nsidc"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_fixtures_dir() -> Path:
    """Retorna directorio de fixtures reales."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    return root_dir / "tests" / "fixtures" / "real"


def fetch_nsidc_monthly_series(hemi: str, code: str) -> tuple[List[Dict[str, Any]], str, str]:
    """
    Obtiene la serie temporal completa de extensión mensual para el hemisferio dado ('N' o 'S').
    Retorna tupla: (lista_records, sha256_hash, kind_provenance).
    """
    cache_dir = _get_cache_dir()
    cache_file = cache_dir / f"nsidc_{code}_monthly_all.csv"

    # 1. Intentar caché vigente
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            try:
                content = cache_file.read_text(encoding="utf-8")
                h = hashlib.sha256(content.encode("utf-8")).hexdigest()
                records = _parse_compiled_csv(content)
                return records, h, "nasa_api"
            except Exception:
                pass

    # 2. Intentar leer fixture compilado local (real NASA/NOAA data)
    fixture_file = _get_fixtures_dir() / f"nsidc_seaice_{code}_monthly_all.csv"
    if fixture_file.exists():
        try:
            content = fixture_file.read_text(encoding="utf-8")
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            records = _parse_compiled_csv(content)
            # Guardar en cache para próximas llamadas
            try:
                cache_file.write_text(content, encoding="utf-8")
            except Exception:
                pass
            return records, h, "nasa_file"
        except Exception:
            pass

    # 3. Intentar descarga en vivo de los 12 archivos mensuales si la red está disponible
    all_points = {}
    total_bytes = b""
    try:
        hemi_name = "north" if code == "N" else "south"
        for m in range(1, 13):
            url = f"{NSIDC_BASE_URL}/{hemi_name}/monthly/data/{code}_{m:02d}_extent_v4.0.csv"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "EarthTrend-Detective/2.0 (NASA Space Apps Challenge 2026)"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_chunk = resp.read()
                total_bytes += raw_chunk
                lines = raw_chunk.decode("utf-8").splitlines()
                reader = csv.reader(lines)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 5:
                        try:
                            yr = int(row[0].strip())
                            mo = int(row[1].strip())
                            val_str = row[4].strip()
                            val = float(val_str)
                            if val < -900:
                                val = None
                            ym = f"{yr:04d}-{mo:02d}"
                            all_points[ym] = val
                        except (ValueError, IndexError):
                            continue

        if all_points:
            sorted_ym = sorted(all_points.keys())
            records = [{"date": ym, "value": all_points[ym]} for ym in sorted_ym]
            h = hashlib.sha256(total_bytes).hexdigest()

            # Guardar en caché
            try:
                with open(cache_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["date", "extent_million_sq_km"])
                    for ym in sorted_ym:
                        writer.writerow([ym, all_points[ym]])
            except Exception:
                pass

            return records, h, "nasa_api"
    except Exception:
        pass

    raise DataUnavailable(
        "SOURCE_DOWN",
        f"No fue posible contactar NSIDC ({NSIDC_BASE_URL}) ni cargar fixture local de hielo marino."
    )


def _parse_compiled_csv(csv_text: str) -> List[Dict[str, Any]]:
    """Parsea el archivo compilado date,extent_million_sq_km."""
    records = []
    lines = csv_text.strip().splitlines()
    reader = csv.reader(lines)
    header = next(reader, None)
    for row in reader:
        if len(row) >= 2:
            ym = row[0].strip()
            val_str = row[1].strip()
            if not val_str or val_str.lower() in ("none", "null", "nan"):
                val = None
            else:
                try:
                    val = float(val_str)
                    if val < -900:
                        val = None
                except ValueError:
                    val = None
            records.append({"date": ym, "value": val})
    records.sort(key=lambda x: x["date"])
    return records


def get_nsidc_series(
    variable_id: str = "SEAICE_EXTENT_N",
    *,
    start_year: int = 1979,
    end_year: int = 2025
) -> Dict[str, Any]:
    """
    Obtiene la serie temporal mensual de extensión de hielo marino de NSIDC (schema: timeseries/2).
    Soporta:
      - SEAICE_EXTENT_N: Extensión Ártico (mensual)
      - SEAICE_EXTENT_S: Extensión Antártico (mensual)
    """
    var_upper = variable_id.upper()
    if var_upper.endswith("_S") or "ANTARCTIC" in var_upper or "_SOUTH" in var_upper:
        code = "S"
        hemi_name = "south"
        region_name = "Southern Ocean (Antarctic Sea Ice)"
        lat = -90.0
        bbox = [-180.0, -90.0, 180.0, -50.0]
    else:
        code = "N"
        hemi_name = "north"
        region_name = "Arctic Ocean (Northern Hemisphere Sea Ice)"
        lat = 90.0
        bbox = [-180.0, 60.0, 180.0, 90.0]

    all_records, sha256_hash, provenance_kind = fetch_nsidc_monthly_series(hemi_name, code)

    # Filtrar por rango
    start_ym = f"{start_year:04d}-01"
    end_ym = f"{end_year:04d}-12"
    filtered_data = [d for d in all_records if start_ym <= d["date"] <= end_ym]

    if not filtered_data:
        raise DataUnavailable("OUT_OF_COVERAGE", f"No hay datos para NSIDC entre {start_ym} y {end_ym}")

    return {
        "schema": "timeseries/2",
        "variable_id": f"SEAICE_EXTENT_{code}",
        "unit": "10^6 km²",
        "cadence": "monthly",
        "region": {
            "kind": "named",
            "name": region_name,
            "lat": lat,
            "lon": 0.0,
            "bbox": bbox
        },
        "aggregation": "area_mean_coslat",
        "data": filtered_data,
        "provenance": {
            "kind": provenance_kind,
            "source": "NSIDC Sea Ice Index, Version 4",
            "underlying": "DMSP SSM/I-SSMIS / Nimbus-7 SMMR (Fetterer et al. 2024)",
            "request_url": f"{NSIDC_BASE_URL}/{hemi_name}/monthly/data/",
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sha256": sha256_hash,
            "native_resolution": "25 km grid polar stereographic",
            "citation": "Fetterer, F., et al. 2024. Sea Ice Index, Version 4. Boulder, Colorado USA. NSIDC: National Snow and Ice Data Center."
        }
    }
