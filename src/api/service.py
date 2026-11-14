# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Orquestación de la API: une ETL + estadística + caché + errores.

Aquí no se calcula nada científico ni se inventa ningún dato. Cada función
llama a la firma real del contrato §6 y traduce sus fallos a `ApiError`.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from . import catalog, modules, validation
from .cache import analysis_cache
from .errors import ApiError


def _normalize_key(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:32]


def _translate_etl_error(exc: Exception) -> ApiError:
    """Convierte `DataUnavailable` (contrato §6) al formato §7."""
    code = getattr(exc, "code", None) or "UPSTREAM_ERROR"
    message = str(exc)
    detail = ""
    if ":" in message:
        head, _, detail = message.partition(":")
        if head.strip() in {
            "VARIABLE_UNKNOWN",
            "OUT_OF_COVERAGE",
            "UPSTREAM_ERROR",
            "UPSTREAM_TIMEOUT",
            "BBOX_TOO_LARGE",
        }:
            code = head.strip()
    if code not in {
        "VARIABLE_UNKNOWN",
        "OUT_OF_COVERAGE",
        "UPSTREAM_ERROR",
        "UPSTREAM_TIMEOUT",
        "BBOX_TOO_LARGE",
        "INSUFFICIENT_DATA",
    }:
        code = "UPSTREAM_ERROR"
    return ApiError(code, hint=detail or message[:300])


def get_series(
    variable_id: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    bbox: list[float] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    fn: Callable[..., dict] = modules.require(modules.modules().get_series(), what="data (ETL)")
    # El catálogo se valida después del módulo: si el ETL no existe en esta rama
    # (503) esa es la causa real, no una variable que el ETL sí conoce.
    catalog.get_variable(variable_id)
    exc_type = modules.modules().data_unavailable_exc()
    kwargs: dict[str, Any] = {}
    if bbox is not None:
        kwargs["bbox"] = bbox
    else:
        kwargs["lat"] = lat
        kwargs["lon"] = lon
    try:
        ts = fn(variable_id, start=start, end=end, **kwargs)
    except exc_type as exc:  # type: ignore[misc]
        raise _translate_etl_error(exc) from exc
    except ApiError:
        raise
    except Exception as exc:  # red, timeout, parser roto
        raise _translate_etl_error(exc) from exc
    validate_series(ts, variable_id)
    return ts


def validate_series(ts: dict[str, Any], variable_id: str) -> None:
    """Comprueba lo mínimo que la API promete de toda serie que sirve."""
    if not isinstance(ts, dict):
        raise ApiError("UPSTREAM_ERROR", hint="ETL returned a non-object series.")
    if ts.get("schema") != "timeseries/2":
        raise ApiError("UPSTREAM_ERROR", hint=f"Unexpected schema: {ts.get('schema')!r}")
    if ts.get("variable_id") != variable_id:
        # Un ETL que devuelve otra variable es exactamente la sustitución silenciosa
        # que el contrato prohíbe: se rechaza, no se corrige.
        raise ApiError(
            "UPSTREAM_ERROR",
            hint=f"ETL returned variable {ts.get('variable_id')!r} for request {variable_id!r}.",
        )
    if not ts.get("data"):
        raise ApiError("OUT_OF_COVERAGE", hint="The series has no observations.")
    provenance = ts.get("provenance") or {}
    if not provenance.get("kind"):
        raise ApiError("UPSTREAM_ERROR", hint="Series without provenance.")


def analyze(
    variable_id: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
    bbox: list[float] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """`/series` -> `analyze_series` + tarjeta del catálogo (contrato A2)."""
    card = catalog.get_variable(variable_id)
    key = _normalize_key("analyze", variable_id, lat, lon, bbox, start, end, card.get("source", {}))

    def produce() -> dict[str, Any]:
        ts = get_series(variable_id, lat=lat, lon=lon, bbox=bbox, start=start, end=end)
        analyze_fn = modules.require(modules.modules().analyze_series(), what="statistics")
        try:
            result = analyze_fn(
                ts,
                ratio_scale=bool(card.get("ratio_scale", False)),
                homogeneous_since=(card.get("source") or {}).get("homogeneous_since"),
            )
        except ApiError:
            raise
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code == "INSUFFICIENT_DATA":
                raise ApiError("INSUFFICIENT_DATA", hint=str(exc)[:300]) from exc
            raise ApiError("UPSTREAM_ERROR", hint=f"stats: {type(exc).__name__}: {exc}"[:300]) from exc
        if not isinstance(result, dict) or result.get("schema") != "analysis/2":
            raise ApiError("UPSTREAM_ERROR", hint="stats returned an unexpected analysis schema.")
        result["variable"] = card
        return result

    return analysis_cache.get_or_compute(key, produce)


def analyze_upload(text: str, variable_id: str | None) -> dict[str, Any]:
    card = catalog.get_variable(variable_id) if variable_id else None
    parse = modules.require(modules.modules().parse_giovanni_csv(), what="Giovanni CSV parser")
    try:
        ts = parse(text, variable_id)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code:
            raise _translate_etl_error(exc) from exc
        raise ApiError(
            "INVALID_REQUEST",
            message={"es": "No se pudo leer el CSV de Giovanni.", "en": "Could not read the Giovanni CSV."},
            hint=str(exc)[:300],
        ) from exc
    validate_series(ts, ts.get("variable_id", variable_id or ""))
    analyze_fn = modules.require(modules.modules().analyze_series(), what="statistics")
    result = analyze_fn(
        ts,
        ratio_scale=bool((card or {}).get("ratio_scale", False)),
        homogeneous_since=((card or {}).get("source") or {}).get("homogeneous_since"),
    )
    if isinstance(result, dict) and result.get("schema") == "analysis/2":
        result["variable"] = card or {
            "id": ts.get("variable_id"),
            "names": {"es": ts.get("variable_id", ""), "en": ts.get("variable_id", "")},
            "unit": ts.get("unit", ""),
            "ratio_scale": False,
            "_catalog_source": "user_upload",
        }
    return result


def trendmap(
    variable_id: str,
    bbox: list[float],
    *,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    catalog.get_variable(variable_id)
    key = _normalize_key("trendmap", variable_id, bbox, start, end)

    def produce() -> dict[str, Any]:
        grid_fn = modules.require(modules.modules().get_grid(), what="grid data (ETL)")
        grid = grid_fn(variable_id, bbox, start=start, end=end)
        analyze_fn = modules.require(modules.modules().analyze_grid(), what="statistics")
        try:
            result = analyze_fn(grid)
        except Exception as exc:
            raise ApiError("UPSTREAM_ERROR", hint=f"stats/grid: {type(exc).__name__}: {exc}"[:300]) from exc
        if not isinstance(result, dict) or result.get("schema") != "trendmap/2":
            raise ApiError("UPSTREAM_ERROR", hint="stats returned an unexpected trendmap schema.")
        return result

    return analysis_cache.get_or_compute(key, produce)


def compare(
    variable_id: str,
    a: tuple[float, float],
    b: tuple[float, float],
    *,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    catalog.get_variable(variable_id)
    res_a = analyze(variable_id, lat=a[0], lon=a[1], start=start, end=end)
    res_b = analyze(variable_id, lat=b[0], lon=b[1], start=start, end=end)
    compare_fn = modules.require(modules.modules().compare(), what="statistics")
    try:
        cmp_result = compare_fn(res_a, res_b)
    except Exception as exc:
        raise ApiError("UPSTREAM_ERROR", hint=f"stats/compare: {type(exc).__name__}: {exc}"[:300]) from exc
    return {"a": res_a, "b": res_b, "compare": cmp_result}
