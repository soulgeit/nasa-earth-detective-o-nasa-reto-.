# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""Logica de validacion reutilizable por `scripts/validate_datasets.py`."""

from __future__ import annotations

import hashlib
import json
import os

ALLOWED_PROVENANCE = ("nasa_api", "nasa_file", "user_upload", "fixture")
ALLOWED_AGGREGATION = ("point", "area_mean_coslat")
ALLOWED_REGION_KIND = ("point", "bbox", "named")
MIN_MONTHS = 120


def _month_ok(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 7 or value[4] != "-":
        return False
    try:
        year, month = int(value[:4]), int(value[5:])
    except ValueError:
        return False
    return 1 <= month <= 12 and 1800 <= year <= 2200


def validate_document(doc, *, min_months: int = MIN_MONTHS, expect_kind: str | None = None) -> list[str]:
    """Devuelve la lista de errores; vacia = valido."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["el documento no es un objeto JSON"]

    if doc.get("schema") != "timeseries/2":
        errors.append(f"schema distinto de 'timeseries/2': {doc.get('schema')!r}")
    if not doc.get("variable_id"):
        errors.append("falta variable_id")
    if not doc.get("unit"):
        errors.append("falta unit")
    if doc.get("cadence") != "monthly":
        errors.append(f"cadence distinto de 'monthly': {doc.get('cadence')!r}")

    agg = doc.get("aggregation")
    if agg not in ALLOWED_AGGREGATION:
        errors.append(f"aggregation no permitido: {agg!r}")

    region = doc.get("region") or {}
    if region.get("kind") not in ALLOWED_REGION_KIND:
        errors.append(f"region.kind no permitido: {region.get('kind')!r}")

    prov = doc.get("provenance") or {}
    kind = prov.get("kind")
    if kind not in ALLOWED_PROVENANCE:
        errors.append(f"provenance.kind no permitido: {kind!r}")
    if expect_kind and kind != expect_kind:
        errors.append(f"provenance.kind esperado {expect_kind!r}, es {kind!r}")
    if kind == "fixture" and os.environ.get("ALLOW_FIXTURES") != "1":
        errors.append("provenance.kind = fixture fuera de tests (ALLOW_FIXTURES != 1)")
    sha = prov.get("sha256")
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha.lower()):
        errors.append("provenance.sha256 ausente o no es un sha256 hex")
    if not prov.get("retrieved_at"):
        errors.append("provenance.retrieved_at ausente")
    if not (prov.get("source") or "").strip():
        errors.append("provenance.source ausente")
    if kind in ("nasa_api", "nasa_file") and not prov.get("request_url"):
        errors.append("provenance.request_url ausente para fuente NASA")

    data = doc.get("data")
    if not isinstance(data, list) or not data:
        errors.append("data vacia o no es lista")
        return errors
    previous = None
    for idx, point in enumerate(data):
        if not isinstance(point, dict):
            errors.append(f"data[{idx}] no es objeto")
            continue
        date = point.get("date")
        if not _month_ok(date):
            errors.append(f"data[{idx}].date no es YYYY-MM: {date!r}")
        elif previous is not None and date <= previous:
            errors.append(f"data[{idx}] fecha no creciente o duplicada: {previous} -> {date}")
        else:
            previous = date
        val = point.get("value")
        if val is not None:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                errors.append(f"data[{idx}].value no numerico: {val!r}")
            elif val == -999 or val == -999.0:
                errors.append(f"data[{idx}].value es el relleno -999 (debe ser null)")

    if len(data) < min_months:
        errors.append(f"solo {len(data)} meses (minimo {min_months})")
    return errors


def validate_file(path: str, **kwargs) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return [f"no se puede leer JSON: {exc}"]
    return validate_document(doc, **kwargs)


def digest(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()
