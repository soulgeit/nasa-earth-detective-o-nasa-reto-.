# SI-assisted: Antigravity 1 (Claude Opus 5.5 / Gemini 3.8 Flash)
"""
Parser de CSV exportado de Giovanni (GES DISC) -> TimeSeries v2 (`user_upload`).

Soporta:
- Exportaciones oficiales de Giovanni GES DISC (con metadatos Title:, User Start Date:,
  User Bounding Box:, URL to Reproduce Results:, Fill Value:, cabecera `time, <VAR>` y datos).
- Exportaciones con cabeceras de comentarios `#` (formato estándar de tutoriales y API).
- Detección automática de columnas de fecha y variable.
- Detección de unidad y valor de relleno desde la cabecera / URL de reproducción.
- Extracción de bounding box de la región en `region.bbox` y centroide `lat, lon`.
- Agregación diaria -> mensual con umbral de representatividad >= 70% de días válidos.
- Preservación de procedencia completa con `provenance.kind = "user_upload"`.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from .errors import DataUnavailable

_DATE_PATTERNS = (
    re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?"),
    re.compile(r"^\d{4}-\d{2}$"),
    re.compile(r"^\d{2}/\d{2}/\d{4}([ T]\d{2}:\d{2}(:\d{2})?)?"),
    re.compile(r"^\d{4}/\d{2}/\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?"),
    re.compile(r"^\d{4}/\d{2}$"),
    re.compile(r"^\d{8}$"),
)
_DATE_HEADER_HINTS = ("time", "date", "fecha", "year", "month", "day")

# Rellenos conocidos cuando la cabecera no lo declara.
DEFAULT_FILLS = (-999.0, -999, -9999.0, -9999)


def _is_date(text: str) -> bool:
    text = text.strip().strip('"')
    return any(p.match(text) for p in _DATE_PATTERNS)


def _to_iso(text: str) -> str | None:
    text = text.strip().strip('"')
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m",
        "%Y/%m",
        "%Y%m%d",
    ):
        try:
            dt = datetime.strptime(text[: len("2026-11-14 00:00:00")], fmt)
            return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
        except ValueError:
            continue
    return None


def _clean(line: str) -> str:
    return line.strip().strip(",")


def _split_metadata(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Separa (metadatos, cabecera de la tabla, filas de datos).

    Identifica la primera fila de datos reales donde la primera celda es una fecha
    y la fila inmediatamente anterior no comentada ni de metadatos como cabecera.
    """
    for idx, line in enumerate(lines):
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        try:
            cells = [_clean(c) for c in next(csv.reader([line]))]
        except Exception:
            continue

        if not cells:
            continue

        # Líneas de metadatos tipo "User Start Date:," o "Title:,"
        if cells[0].endswith(":"):
            continue

        # Si la primera celda es una fecha, encontramos la primera fila de datos
        if _is_date(cells[0]):
            header_idx = idx - 1
            while header_idx >= 0 and not lines[header_idx].strip():
                header_idx -= 1
            if header_idx < 0:
                raise DataUnavailable(
                    "UPSTREAM_ERROR", "CSV de Giovanni sin cabecera de columnas antes de los datos"
                )
            return lines[:header_idx], [lines[header_idx]], lines[idx:]

    raise DataUnavailable(
        "UPSTREAM_ERROR",
        "CSV de Giovanni sin fila de fechas reconocible; no se interpreta a ciegas",
    )


def _pick_columns(header: list[str], variable_id: str | None) -> tuple[int, int]:
    lowered = [h.strip().lower() for h in header]
    date_idx = next(
        (i for i, h in enumerate(lowered) if any(h.startswith(p) for p in _DATE_HEADER_HINTS)),
        0,
    )
    value_idx = None
    if variable_id:
        token = variable_id.lower()
        value_idx = next((i for i, h in enumerate(lowered) if token in h), None)
    if value_idx is None:
        value_idx = next(
            (i for i in range(len(header)) if i != date_idx and lowered[i] not in ("", "time", "date")),
            None,
        )
    if value_idx is None or value_idx == date_idx:
        raise DataUnavailable("UPSTREAM_ERROR", "no se identifica la columna de la variable")
    return date_idx, value_idx


def _fill_from_header(meta: list[str]) -> float | None:
    for line in meta:
        match = re.search(r"(fill|missing|nodata)[^0-9\-]*([0-9eE\.\+\-]+)", line, re.I)
        if match:
            try:
                return float(match.group(2))
            except ValueError:
                pass
    return None


def _unit_from_header(meta: list[str]) -> str | None:
    for line in meta:
        unquoted = urllib.parse.unquote(line)
        match = re.search(r"units?\s*[:=]\s*([A-Za-z0-9%°/\.\^\-\+\*\s]+)", unquoted, re.I)
        if match:
            u = match.group(1).split("&")[0].split(")")[0].strip()
            if u.lower() in ("c", "celsius"):
                return "°C"
            return u
    return None


def _bbox_from_header(meta: list[str]) -> tuple[list[float] | None, float | None, float | None]:
    for line in meta:
        match = re.search(r"bounding\s*box[^0-9\-]*([0-9\.\,\-\s]+)", line, re.I)
        if match:
            clean_str = match.group(1).strip().strip('"').strip("'")
            parts = [p.strip() for p in clean_str.split(",")]
            if len(parts) >= 4:
                try:
                    w, s, e, n = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
                    lat = round((s + n) / 2.0, 4)
                    lon = round((w + e) / 2.0, 4)
                    return [w, s, e, n], lat, lon
                except ValueError:
                    pass
    return None, None, None


def parse_csv(text: str, variable_id: str | None = None) -> dict:
    """CSV de Giovanni -> TimeSeries v2 con provenance.kind = user_upload."""
    if not text or not text.strip():
        raise DataUnavailable("UPSTREAM_ERROR", "CSV vacio")
    lines = text.splitlines()
    meta_lines, header_lines, table_lines = _split_metadata(lines)
    reader = csv.reader(io.StringIO("\n".join(table_lines)))
    header = next(csv.reader([header_lines[0]]))
    date_idx, value_idx = _pick_columns(header, variable_id)
    fill = _fill_from_header(meta_lines)
    unit = _unit_from_header(meta_lines)
    bbox, center_lat, center_lon = _bbox_from_header(meta_lines)

    points: list[tuple[str, float | None]] = []
    for row in reader:
        if len(row) <= max(date_idx, value_idx):
            continue
        iso = _to_iso(row[date_idx])
        if iso is None:
            continue
        raw = row[value_idx].strip()
        if raw == "" or raw.lower() in ("nan", "na", "null", "none"):
            points.append((iso, None))
            continue
        try:
            val = float(raw)
        except ValueError:
            points.append((iso, None))
            continue

        if val is not None and (val == fill if fill is not None else False):
            val = None
        elif val is not None and (val in DEFAULT_FILLS or val >= 1e14 or val < -1e20):
            # En Giovanni, valores >= 1e14 (ej. 1e15) o centinelas son relleno.
            val = None
        points.append((iso, val))
    if not points:
        raise DataUnavailable("UPSTREAM_ERROR", "CSV sin filas de datos utiles")

    is_daily = any(len(iso) == 10 for iso, _ in points)
    if is_daily:
        data = _to_monthly(points)
    else:
        data = _to_monthly_keep(points)
    if not data:
        raise DataUnavailable("OUT_OF_COVERAGE", "sin meses con cobertura suficiente (>=70%)")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "schema": "timeseries/2",
        "variable_id": variable_id or _guess_variable(header, value_idx),
        "unit": unit or "",
        "cadence": "monthly",
        "region": {
            "kind": "bbox" if bbox else "named",
            "name": _guess_region_name(meta_lines),
            "lat": center_lat,
            "lon": center_lon,
            "bbox": bbox,
        },
        "aggregation": "area_mean_coslat",
        "data": data,
        "provenance": {
            "kind": "user_upload",
            "source": "Giovanni (GES DISC) CSV export",
            "underlying": _guess_product(meta_lines),
            "request_url": _extract_reproduce_url(meta_lines),
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sha256": sha,
            "native_resolution": None,
            "citation": "NASA Giovanni, GES DISC; https://giovanni.gsfc.nasa.gov/",
            "header_metadata": [line.strip() for line in meta_lines if line.strip()],
        },
    }


def _to_monthly(points: list[tuple[str, float | None]]) -> list[dict]:
    """Agrega a mensual: media de dias validos; mes valido si >=70 % de dias."""
    buckets: dict[str, list[float]] = {}
    seen: dict[str, int] = {}
    for iso, val in points:
        month = iso[:7]
        seen[month] = seen.get(month, 0) + 1
        if val is not None:
            buckets.setdefault(month, []).append(val)
    out = []
    for month in sorted(seen):
        vals = buckets.get(month, [])
        if not vals or len(vals) / seen[month] < 0.70:
            out.append({"date": month, "value": None})
            continue
        out.append({"date": month, "value": round(sum(vals) / len(vals), 6)})
    return out


def _to_monthly_keep(points: list[tuple[str, float | None]]) -> list[dict]:
    """Serie ya mensual: se conserva tal cual, con nulos."""
    out = []
    for iso, val in points:
        month = iso[:7]
        if out and out[-1]["date"] == month:
            if out[-1]["value"] is None:
                out[-1]["value"] = val
            continue
        out.append({"date": month, "value": val})
    return out


def _guess_variable(header: list[str], value_idx: int) -> str:
    raw = header[value_idx].strip() if value_idx < len(header) else "UPLOADED"
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()
    return cleaned or "UPLOADED"


def _guess_product(meta: list[str]) -> str | None:
    for line in meta:
        match = re.search(r"(product|dataset|title|data field)\s*[:=]\s*(.+)", line, re.I)
        if match:
            return match.group(2).strip().strip('"').strip(",")[:200]
    return None


def _guess_region_name(meta: list[str]) -> str | None:
    for line in meta:
        match = re.search(r"region\s*[:=]\s*(.+)", line, re.I)
        if match:
            return match.group(1).strip().strip('"').strip(",")
    return None


def _extract_reproduce_url(meta: list[str]) -> str | None:
    for line in meta:
        match = re.search(r"https?://[^\",\s\r\n]+", line, re.I)
        if match:
            return match.group(0).strip().strip('"').strip("'")
    return None
