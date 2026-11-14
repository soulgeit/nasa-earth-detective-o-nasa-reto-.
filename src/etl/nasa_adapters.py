# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Parsers y adaptadores de datos para fuentes públicas de la NASA y agencias espaciales:
- NOAA Climate Data Online (CDO)
- Conversiones de unidades estándar
Nota: Generadores sintéticos eliminados definitivamente para garantizar validez científica (D2).
"""

from typing import List, Dict, Any


def kelvin_to_celsius(val_k: float) -> float:
    return round(val_k - 273.15, 2)


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
