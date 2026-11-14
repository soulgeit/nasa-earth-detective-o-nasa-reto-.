# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Parser de CSV exportado de Giovanni (GES DISC) -> TimeSeries v2 (`user_upload`).

ESTADO: PARCIAL (2026-11-14). En `data/raw/giovanni/` todavia no hay ninguna
exportacion real, y la regla 3 del equipo prohibe programar contra un formato
imaginado. Este modulo implementa solo lo que se puede afirmar sin muestra:

- Giovanni antepone lineas de metadatos (`#` o texto) antes de la tabla: se saltan
  hasta la primera linea que contenga comas y una columna de fecha reconocible.
- La primera fila de la tabla se toma como cabecera; se localiza la columna de
  fecha y la primera columna numerica del producto.
- El valor de relleno se detecta por cabecera (`fill`, `missing`, `nodata`) y,
  si no aparece, se tratan como nulos los valores negativos absurdos y los vacios
  NO se inventan: se quedan en `null`.
- Serie diaria -> mensual solo si el mes tiene >= 70 % de dias con dato (contrato §4).

Pendiente de validar contra una exportacion real (tarea D5, bloqueada por el humano).
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime, timezone

from .errors import DataUnavailable

_DATE_PATTERNS = (
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{4}-\d{2}$"),
    re.compile(r"^\d{4}/\d{2}/\d{2}$"),
    re.compile(r"^\d{4}/\d{2}$"),
    re.compile(r"^\d{8}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"),
)
_DATE_HEADER_HINTS = ("time", "date", "fecha", "year", "month", "day")


def _is_date(text: str) -> bool:
    text = text.strip().strip('"')
    return any(p.match(text) for p in _DATE_PATTERNS)


def _to_iso(text: str) -> str | None:
    text = text.strip().strip('"')
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m", "%Y%m%d"):
        try:
            dt = datetime.strptime(text[: len("2026-11-14T00:00:00")], fmt)
            return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
        except ValueError:
            continue
    return None


def _clean(line: str) -> str:
    return line.strip().strip(",")


def _split_metadata(lines: list[str]) -> tuple[list[str], list[str]]:
    """Separa cabecera de metadatos y tabla de datos."""
    for idx, line in enumerate(lines):
        if "," not in line:
            continue
        cells = [_clean(c) for c in next(csv.reader([line]))]
        if any(_is_date(c) for c in cells):
            return lines[:idx], lines[idx:]
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
        match = re.search(r"(fill|missing|nodata)[^0-9\-]*(-?\d+(?:\.\d+)?)", line, re.I)
        if match:
            return float(match.group(2))
    return None


def _unit_from_header(meta: list[str]) -> str | None:
    for line in meta:
        match = re.search(r"unit[s]?\s*[:=]\s*([A-Za-z0-9%°/\.\^\-\+\*\s]+)", line, re.I)
        if match:
            return match.group(1).strip()
    return None


def parse_csv(text: str, variable_id: str | None = None) -> dict:
    """CSV de Giovanni -> TimeSeries v2 con provenance.kind = user_upload."""
    if not text or not text.strip():
        raise DataUnavailable("UPSTREAM_ERROR", "CSV vacio")
    lines = text.splitlines()
    meta_lines, table_lines = _split_metadata(lines)
    reader = csv.reader(io.StringIO("\n".join(table_lines)))
    header = next(reader)
    date_idx, value_idx = _pick_columns(header, variable_id)
    fill = _fill_from_header(meta_lines)
    unit = _unit_from_header(meta_lines)

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
        if fill is not None and val == fill:
            val = None
        elif val < -1e20:
            val = None
        points.append((iso, val))
    if not points:
        raise DataUnavailable("UPSTREAM_ERROR", "CSV sin filas de datos utiles")

    daily = any(len(iso) == 10 for iso, _ in points)
    data = _to_monthly(points) if daily and _looks_daily(points) else _to_monthly_keep(points)
    if not data:
        raise DataUnavailable("OUT_OF_COVERAGE", "sin meses con cobertura suficiente (>=70%)")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "schema": "timeseries/2",
        "variable_id": variable_id or _guess_variable(header, value_idx),
        "unit": unit or "",
        "cadence": "monthly",
        "region": {"kind": "named", "name": None, "lat": None, "lon": None, "bbox": None},
        "aggregation": "area_mean_coslat",
        "data": data,
        "provenance": {
            "kind": "user_upload",
            "source": "Giovanni (GES DISC) CSV export",
            "underlying": _guess_product(meta_lines),
            "request_url": None,
            "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sha256": sha,
            "native_resolution": None,
            "citation": "NASA Giovanni, GES DISC; https://giovanni.gsfc.nasa.gov/",
            "header_metadata": [line.strip() for line in meta_lines if line.strip()],
        },
    }


def _looks_daily(points: list[tuple[str, float | None]]) -> bool:
    days = [iso for iso, _ in points]
    return len(days) > 40 and len(days[:40]) == len(set(days[:40]))


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
        match = re.search(r"(product|dataset|data field)\s*[:=]\s*(.+)", line, re.I)
        if match:
            return match.group(2).strip().strip(",")[:200]
    return None
