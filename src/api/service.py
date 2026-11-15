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
    place: str | None = None,
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
    _apply_place(ts, place)
    return ts


def _apply_place(ts: dict[str, Any], place: str | None) -> None:
    """Escribe un nombre en `region.name` si el ETL no lo trajo.

    Dos casos (RONDA_3 §2.7):
    - punto o caja: el nombre lo aporta `/api/geocode` como `place`;
    - variable sin lugar (hielo marino): el ETL devuelve `region_fixed = None`
      del catálogo, así que se usa el nombre de la propia variable.

    Nunca se inventa una ubicación: solo se rellena lo que el catálogo o el
    usuario ya dijeron.
    """
    if not isinstance(ts, dict):
        return
    region = ts.get("region")
    if not isinstance(region, dict) or region.get("name"):
        return
    if place:
        region["name"] = place
        return
    if region.get("kind") == "named":
        try:
            card = catalog.get_variable(ts.get("variable_id", ""))
        except ApiError:
            return
        names = card.get("names") or {}
        label = names.get("en") or names.get("es")
        if label:
            region["name"] = label


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
    place: str | None = None,
) -> dict[str, Any]:
    """`/series` -> `analyze_series` + tarjeta del catálogo (contrato A2)."""
    card = catalog.get_variable(variable_id)
    key = _normalize_key("analyze", variable_id, lat, lon, bbox, start, end, place, card.get("source", {}))

    def produce() -> dict[str, Any]:
        ts = get_series(
            variable_id, lat=lat, lon=lon, bbox=bbox, start=start, end=end, place=place
        )
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
        _apply_place(result, place)
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
        # La rejilla del ETL no trae `variable_id`; sin esto el motor pone "VAR"
        # de relleno (RONDA_3 §2.5). La API es quien conoce el id pedido.
        if isinstance(grid, dict):
            grid.setdefault("variable_id", variable_id)
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


# --------------------------------------------------------------------------
# RONDA_7 — escaneo: todas las variables de un punto, ordenadas por evidencia
# --------------------------------------------------------------------------

SCAN_WORKERS = 6
SCAN_FDR_Q = 0.05
POINT_CONNECTORS = ("power",)


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Valores q de Benjamini y Hochberg (1995), en el orden de entrada.

    Con 33 pruebas a alfa = 0,05 se esperan una o dos «significativas» por puro
    azar. El valor q controla la proporción de falsos hallazgos del conjunto.
    """
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    q = [1.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        idx = order[rank - 1]
        running = min(running, p_values[idx] * m / rank)
        q[idx] = running
    return q


def _scan_row(card: dict[str, Any], lat: float, lon: float, place: str | None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "variable_id": card["id"],
        "names": card.get("names"),
        "unit": card.get("unit"),
        "sphere": card.get("sphere"),
        "status": "ok",
    }
    try:
        result = analyze(card["id"], lat=lat, lon=lon, place=place)
    except ApiError as exc:
        row.update(status="error", code=exc.code)
        return row
    except Exception as exc:  # un fallo de una variable no tumba el escaneo
        row.update(status="error", code="UPSTREAM_ERROR", hint=f"{type(exc).__name__}"[:80])
        return row

    trend = result.get("trend") or {}
    tests = (result.get("tests") or {}).get("mann_kendall") or {}
    significance = result.get("significance") or {}
    period = result.get("period") or {}
    p_value = tests.get("p_value_autocorr")
    if p_value is None:
        p_value = tests.get("p_value")
    if trend.get("sen_slope_per_decade") is None or p_value is None or not period.get("years"):
        row.update(status="insufficient", period=period)
        return row
    row.update(
        direction=trend.get("direction"),
        slope_per_decade=trend.get("sen_slope_per_decade"),
        ci95_per_decade=trend.get("sen_ci95_per_decade"),
        percent_per_decade=trend.get("percent_per_decade"),
        total_change=trend.get("total_change"),
        p_value=float(p_value),
        is_significant=bool(significance.get("is_significant")),
        verdict_code=significance.get("verdict_code"),
        tests_agree=significance.get("tests_agree"),
        period={k: period.get(k) for k in ("start", "end", "years", "n_obs")},
        source=(result.get("provenance") or {}).get("underlying") or (result.get("provenance") or {}).get("source"),
    )
    return row


def scan(*, lat: float, lon: float, place: str | None = None) -> dict[str, Any]:
    """Analiza todas las variables de punto del catálogo en un lugar.

    Cada fila sale de `analyze()` (mismo motor, mismas cifras, misma caché) y el
    conjunto añade la corrección por comparaciones múltiples: una variable solo
    se destaca si su valor q (Benjamini-Hochberg) queda por debajo de 0,05.
    """
    lat, lon = validation.check_point(lat, lon)
    cards = [
        c for c in catalog.all_variables()
        if not catalog.is_planned(c) and str(c.get("connector") or "") in POINT_CONNECTORS
    ]
    key = _normalize_key("scan", round(lat, 2), round(lon, 2), place, sorted(c["id"] for c in cards))
    return analysis_cache.get_or_compute(key, lambda: _scan(cards, lat, lon, place))


def _scan(cards: list[dict[str, Any]], lat: float, lon: float, place: str | None) -> dict[str, Any]:
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=SCAN_WORKERS) as pool:
        rows = list(pool.map(lambda card: _scan_row(card, lat, lon, place), cards))

    tested = [r for r in rows if r["status"] == "ok"]
    for row, q_value in zip(tested, _benjamini_hochberg([r["p_value"] for r in tested])):
        row["q_value"] = q_value
        # Confirmada = el veredicto del motor ya era «significativa» (sus pruebas
        # coinciden) Y además sobrevive a la corrección por pruebas múltiples.
        row["confirmed"] = bool(row["is_significant"] and q_value < SCAN_FDR_Q)
    tested.sort(key=lambda r: (not r["confirmed"], r["p_value"], r["variable_id"]))
    others = [r for r in rows if r["status"] != "ok"]
    return {
        "schema": "scan/1",
        "region": {"kind": "point", "name": place, "lat": lat, "lon": lon},
        "n_variables": len(rows),
        "n_tested": len(tested),
        "n_significant": sum(1 for r in tested if r["is_significant"]),
        "n_confirmed": sum(1 for r in tested if r["confirmed"]),
        "multiple_testing": {"method": "Benjamini-Hochberg", "q": SCAN_FDR_Q, "reference": "Benjamini & Hochberg 1995"},
        "rows": tested + others,
    }
