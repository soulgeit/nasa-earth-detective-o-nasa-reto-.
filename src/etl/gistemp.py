# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Conector oficial para NASA GISTEMP v4 (Goddard Institute for Space Studies Surface Temperature Analysis).
Obtiene series temporales mensuales globales de anomalías de temperatura superficial (1880-presente).
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

GISTEMP_GLB_URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 días


def _get_cache_dir() -> Path:
    """Retorna directorio de caché persistente."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    cache_dir = root_dir / "data" / "cache" / "gistemp"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_fixtures_dir() -> Path:
    """Retorna directorio de fixtures reales."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    return root_dir / "tests" / "fixtures" / "real"


def fetch_gistemp_csv(*, force_refresh: bool = False) -> tuple[str, str, str]:
    """
    Obtiene el CSV de medias mensuales globales de GISTEMP v4.
    Retorna tupla: (contenido_csv, sha256_hash, kind_provenance).
    """
    cache_dir = _get_cache_dir()
    cache_file = cache_dir / "GLB.Ts+dSST.csv"

    # 1. Intentar caché vigente
    if not force_refresh and cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            try:
                content = cache_file.read_text(encoding="utf-8")
                h = hashlib.sha256(content.encode("utf-8")).hexdigest()
                return content, h, "nasa_api"
            except Exception:
                pass

    # 2. Intentar descarga en vivo
    try:
        req = urllib.request.Request(
            GISTEMP_GLB_URL,
            headers={"User-Agent": "EarthTrend-Detective/2.0 (NASA Space Apps Challenge 2026)"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw_bytes = resp.read()
            content = raw_bytes.decode("utf-8")
            h = hashlib.sha256(raw_bytes).hexdigest()
            cache_file.write_text(content, encoding="utf-8")
            return content, h, "nasa_api"
    except Exception:
        # 3. Fallback a caché expirado si existe
        if cache_file.exists():
            content = cache_file.read_text(encoding="utf-8")
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return content, h, "nasa_api"

        # 4. Fallback a fixture real si está offline / sandbox
        fixture_file = _get_fixtures_dir() / "gistemp_glb_monthly.csv"
        if fixture_file.exists():
            content = fixture_file.read_text(encoding="utf-8")
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return content, h, "nasa_file"

        raise DataUnavailable(
            "SOURCE_DOWN",
            f"No fue posible contactar NASA GISS ({GISTEMP_GLB_URL}) ni encontrar fixture local."
        )


def parse_gistemp_glb_csv(csv_text: str) -> List[Dict[str, Any]]:
    """
    Parsea el CSV de medias globales de GISTEMP.
    Estructura:
    Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,J-D,D-N,DJF,MAM,JJA,SON
    Valores como '-.19', '1.25', '***' (faltante).
    """
    records = []
    lines = csv_text.strip().splitlines()
    header_found = False

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        parts = [p.strip() for p in line_clean.split(",")]
        if len(parts) >= 13 and parts[0] == "Year" and parts[1] == "Jan":
            header_found = True
            continue

        if not header_found:
            continue

        # Línea de datos
        try:
            year_val = int(parts[0])
        except ValueError:
            continue

        for month_idx in range(1, 13):
            val_str = parts[month_idx]
            if val_str in ("***", "", "NA", "null"):
                parsed_val = None
            else:
                try:
                    parsed_val = float(val_str)
                except ValueError:
                    parsed_val = None

            date_str = f"{year_val:04d}-{month_idx:02d}"
            records.append({
                "date": date_str,
                "value": parsed_val
            })

    # Ordenar estrictamente por fecha ascendente
    records.sort(key=lambda x: x["date"])
    return records


def get_gistemp_series(
    variable_id: str = "GISTEMP_TANOM",
    *,
    start_year: int = 1880,
    end_year: int = 2025,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Obtiene la serie temporal mensual de anomalías de temperatura GISTEMP v4 (schema: timeseries/2).
    """
    if variable_id not in ("GISTEMP_TANOM", "GISTEMP", "GLOBAL_TEMP_ANOMALY"):
        raise DataUnavailable("VARIABLE_UNKNOWN", f"Variable {variable_id} no soportada por conector GISTEMP")

    csv_text, sha256_hash, provenance_kind = fetch_gistemp_csv(force_refresh=force_refresh)
    all_data = parse_gistemp_glb_csv(csv_text)

    # Filtrar por rango
    start_ym = f"{start_year:04d}-01"
    end_ym = f"{end_year:04d}-12"
    filtered_data = [d for d in all_data if start_ym <= d["date"] <= end_ym]

    if not filtered_data:
        raise DataUnavailable("OUT_OF_COVERAGE", f"No hay datos para GISTEMP entre {start_ym} y {end_ym}")

    # Retornar objeto bajo contrato §3
    return {
        "schema": "timeseries/2",
        "variable_id": "GISTEMP_TANOM",
        "unit": "°C",
        "cadence": "monthly",
        "region": {
            "kind": "named",
            "name": "Global Surface (Land-Ocean)",
            "lat": 0.0,
            "lon": 0.0,
            "bbox": [-180.0, -90.0, 180.0, 90.0]
        },
        "aggregation": "area_mean_coslat",
        "data": filtered_data,
        "provenance": {
            "kind": provenance_kind,
            "source": "NASA GISS Surface Temperature Analysis (GISTEMP v4)",
            "underlying": "GHCNv4 / ERSSTv5 (1200 km smoothing)",
            "request_url": GISTEMP_GLB_URL,
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sha256": sha256_hash,
            "native_resolution": "Global Mean",
            "citation": "GISTEMP Team, 2026: GISS Surface Temperature Analysis (GISTEMP), version 4. NASA Goddard Institute for Space Studies. Lenssen et al. (2019), JGR Atmospheres."
        }
    }
