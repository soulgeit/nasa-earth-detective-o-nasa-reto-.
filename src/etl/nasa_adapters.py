"""
Parsers y adaptadores de datos para fuentes públicas de la NASA y agencias espaciales:
- Giovanni (CSV exportado de series temporales)
- NOAA Climate Data Online (CDO)
- Conversiones de unidades estándar
- Generador sintético de respaldo (Fallback offline para demos)
"""

import csv
import io
import math
import random
from typing import List, Dict, Any


def kelvin_to_celsius(val_k: float) -> float:
    return round(val_k - 273.15, 2)


def parse_giovanni_csv(raw_csv_text: str) -> List[Dict[str, Any]]:
    """
    Parsea las exportaciones típicas de Giovanni (cabeceras con metadatos seguidas
    de líneas de tiempo y valor).
    """
    points = []
    lines = raw_csv_text.strip().splitlines()
    data_lines = [l for l in lines if l and not l.startswith("#") and not l.startswith("title")]

    reader = csv.reader(data_lines)
    header = None
    for row in reader:
        if not header:
            header = [col.strip().lower() for col in row]
            continue
        if len(row) < 2:
            continue
        # Intentar extraer fecha y valor numérico
        date_str = row[0].strip()
        try:
            val = float(row[1].strip())
            # Derivar año y mes
            parts = date_str.split("-")
            y = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 1
            points.append({
                "date": date_str,
                "year": y,
                "month": m,
                "value": round(val, 4)
            })
        except ValueError:
            continue
    return points


def parse_noaa_cdo(raw_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parsea respuestas de la API de NOAA CDO v2."""
    points = []
    for item in raw_json:
        date_str = item.get("date", "").split("T")[0]
        val = item.get("value")
        if date_str and val is not None:
            parts = date_str.split("-")
            y = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 1
            points.append({
                "date": date_str,
                "year": y,
                "month": m,
                "value": float(val)
            })
    return points


def generate_synthetic_timeseries(
    start_year: int = 2000,
    end_year: int = 2024,
    base_val: float = 10.0,
    annual_trend: float = 0.05,
    seasonal_amp: float = 2.0,
    noise_std: float = 0.5
) -> List[Dict[str, Any]]:
    """Genera series temporales climáticamente consistentes para demostraciones."""
    pts = []
    for y in range(start_year, end_year + 1):
        for m in range(1, 13):
            t = (y - start_year) + (m - 1) / 12.0
            seasonal = seasonal_amp * math.sin(2 * math.pi * (m - 1) / 12.0)
            noise = random.gauss(0, noise_std)
            val = base_val + (annual_trend * t) + seasonal + noise
            pts.append({
                "date": f"{y:04d}-{m:02d}-01",
                "year": y,
                "month": m,
                "value": round(val, 4)
            })
    return pts
