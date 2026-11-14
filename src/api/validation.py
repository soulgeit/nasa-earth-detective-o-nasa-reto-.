# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""Validación de entrada del contrato §7 y §10.

Toda petición inválida lanza `ApiError("INVALID_REQUEST")` con pista bilingüe.
Nada de corregir valores en silencio: si la petición no tiene sentido se dice.
"""

from __future__ import annotations

import re
from typing import Any

from . import catalog
from .config import MAX_BBOX_SPAN_DEG
from .errors import ApiError

DATE_RE = re.compile(r"^(\d{4})-(\d{2})$")


def _bad(es: str, en: str, hint: str = "") -> ApiError:
    return ApiError("INVALID_REQUEST", message={"es": es, "en": en}, hint=hint)


def parse_month(value: str, *, field: str) -> str:
    m = DATE_RE.match(value or "")
    if not m:
        raise _bad(
            f"'{field}' debe tener formato YYYY-MM.",
            f"'{field}' must be formatted YYYY-MM.",
            f"Received: {value!r}",
        )
    year, month = int(m.group(1)), int(m.group(2))
    if not (1 <= month <= 12):
        raise _bad(f"Mes fuera de rango en '{field}'.", f"Month out of range in '{field}'.", value)
    if not (1800 <= year <= 2200):
        raise _bad(f"Año fuera de rango en '{field}'.", f"Year out of range in '{field}'.", value)
    return f"{year:04d}-{month:02d}"


def check_period(start: str | None, end: str | None) -> tuple[str | None, str | None]:
    if start is not None:
        start = parse_month(start, field="start")
    if end is not None:
        end = parse_month(end, field="end")
    if start and end and start > end:
        raise _bad("'start' debe ser anterior a 'end'.", "'start' must be before 'end'.", f"{start} > {end}")
    return start, end


def check_point(lat: float | None, lon: float | None) -> tuple[float, float]:
    if lat is None or lon is None:
        raise _bad(
            "Faltan las coordenadas: pasa lat y lon, o una caja (bbox).",
            "Missing coordinates: pass lat and lon, or a bbox.",
        )
    if not (-90.0 <= lat <= 90.0):
        raise _bad("La latitud debe estar entre -90 y 90.", "Latitude must be between -90 and 90.", str(lat))
    if not (-180.0 <= lon <= 180.0):
        raise _bad("La longitud debe estar entre -180 y 180.", "Longitude must be between -180 and 180.", str(lon))
    return float(lat), float(lon)


def check_bbox(raw: str | list[float] | None) -> list[float] | None:
    """Acepta 'oeste,sur,este,norte' (texto) o una lista ya separada."""
    if raw is None:
        return None
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
        try:
            values = [float(p) for p in parts]
        except ValueError:
            raise _bad(
                "bbox debe ser 'oeste,sur,este,norte' en grados.",
                "bbox must be 'west,south,east,north' in degrees.",
                raw,
            )
    else:
        values = [float(v) for v in raw]

    if len(values) != 4:
        raise _bad("bbox necesita cuatro valores.", "bbox needs four values.", str(raw))
    west, south, east, north = values
    if not (-180.0 <= west <= 180.0 and -180.0 <= east <= 180.0):
        raise _bad("Longitudes de bbox fuera de rango.", "bbox longitudes out of range.", str(values))
    if not (-90.0 <= south <= 90.0 and -90.0 <= north <= 90.0):
        raise _bad("Latitudes de bbox fuera de rango.", "bbox latitudes out of range.", str(values))
    if west >= east:
        raise _bad("bbox exige oeste < este.", "bbox requires west < east.", str(values))
    if south >= north:
        raise _bad("bbox exige sur < norte.", "bbox requires south < north.", str(values))
    if (east - west) > MAX_BBOX_SPAN_DEG or (north - south) > MAX_BBOX_SPAN_DEG:
        raise ApiError(
            "BBOX_TOO_LARGE",
            hint=f"Max span is {MAX_BBOX_SPAN_DEG}° per side; split the area.",
        )
    return [float(v) for v in values]


def check_variable(variable_id: str) -> dict[str, Any]:
    if not variable_id:
        raise _bad("Falta variable_id.", "Missing variable_id.")
    return catalog.get_variable(variable_id)


def point_or_bbox(
    lat: float | None, lon: float | None, bbox: str | list[float] | None
) -> tuple[dict[str, Any], str]:
    """Devuelve (kwargs para el ETL, etiqueta del modo) exigiendo uno de los dos."""
    box = check_bbox(bbox)
    if box is not None:
        return {"bbox": box}, "bbox"
    plat, plon = check_point(lat, lon)
    return {"lat": plat, "lon": plon}, "point"


def check_lang(lang: str | None) -> str:
    if lang is None:
        return "es"
    value = lang.strip().lower()
    if value not in {"es", "en"}:
        raise _bad("Idioma no soportado.", "Unsupported language.", "Allowed: es | en")
    return value
