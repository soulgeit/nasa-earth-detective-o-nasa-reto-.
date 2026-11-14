# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Resolvedor de los módulos del contrato §6.

La API nunca implementa ciencia: consume `src/etl` y `src/stats` cuando existen
con las firmas del contrato. Mientras esos carriles no han empujado, este módulo
ofrece **dobles de prueba** que leen las muestras reales de `tests/fixtures/real/`
y solo se activan con `ALLOW_FIXTURES=1`.

Regla: con `ALLOW_FIXTURES` apagado y sin módulo real → `503 DATA_UNAVAILABLE`.
Nunca se devuelven datos de muestra como si fueran reales.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable

from .config import FIXTURES_DIR, allow_fixtures
from .errors import ApiError

#: Nombres de módulo según el contrato §6.
ETL_MODULE = "src.etl.registry"
STATS_MODULE = "src.stats.trend_engine"
DETECTIVE_MODULE = "src.detective"


@dataclass
class ModuleStatus:
    name: str
    available: bool
    detail: str


def _try_import(name: str) -> tuple[Any | None, str]:
    try:
        return importlib.import_module(name), ""
    except Exception as exc:  # ImportError o cualquier error de importación
        return None, f"{type(exc).__name__}: {exc}"


def _expect_callable(mod: Any, attr: str) -> Callable[..., Any] | None:
    fn = getattr(mod, attr, None)
    return fn if callable(fn) else None


class _Resolver:
    """Estado de los módulos, resuelto una vez por proceso."""

    def __init__(self) -> None:
        self.etl, self.etl_err = _try_import(ETL_MODULE)
        self.stats, self.stats_err = _try_import(STATS_MODULE)
        self.detective, self.detective_err = _try_import(DETECTIVE_MODULE)
        self.fixtures = None
        if self.etl is None and allow_fixtures():
            self.fixtures = _FixtureBackedModules()

    # --- ETL -----------------------------------------------------------
    def get_series(self) -> Callable[..., dict] | None:
        if self.etl is not None:
            fn = _expect_callable(self.etl, "get_series")
            if fn is not None:
                return fn
        if self.fixtures is not None:
            return self.fixtures.get_series
        return None

    def get_grid(self) -> Callable[..., dict] | None:
        if self.etl is not None:
            fn = _expect_callable(self.etl, "get_grid")
            if fn is not None:
                return fn
        if self.fixtures is not None:
            return self.fixtures.get_grid
        return None

    def parse_giovanni_csv(self) -> Callable[..., dict] | None:
        if self.etl is not None:
            fn = _expect_callable(self.etl, "parse_giovanni_csv")
            if fn is not None:
                return fn
        return None

    def data_unavailable_exc(self) -> type[Exception]:
        if self.etl is not None:
            exc = getattr(self.etl, "DataUnavailable", None)
            if isinstance(exc, type) and issubclass(exc, Exception):
                return exc
        return _StubDataUnavailable

    # --- Stats ---------------------------------------------------------
    def analyze_series(self) -> Callable[..., dict] | None:
        if self.stats is not None:
            fn = _expect_callable(self.stats, "analyze_series")
            if fn is not None:
                return fn
        return None

    def analyze_grid(self) -> Callable[..., dict] | None:
        if self.stats is not None:
            fn = _expect_callable(self.stats, "analyze_grid")
            if fn is not None:
                return fn
        return None

    def compare(self) -> Callable[..., dict] | None:
        if self.stats is not None:
            fn = _expect_callable(self.stats, "compare")
            if fn is not None:
                return fn
        return None

    # --- Detective ------------------------------------------------------
    def detective_fn(self, attr: str) -> Callable[..., Any] | None:
        if self.detective is None:
            return None
        return _expect_callable(self.detective, attr)

    # --- Diagnóstico ----------------------------------------------------
    def status(self) -> dict[str, ModuleStatus]:
        def detail(mod: Any, err: str, missing: list[str]) -> str:
            if err:
                return err
            if missing:
                return "missing contract functions: " + ", ".join(missing)
            return "ok"

        etl_missing = [
            f
            for f in ("get_series", "get_grid", "parse_giovanni_csv", "DataUnavailable")
            if getattr(self.etl, f, None) is None
        ]
        stats_missing = [
            f
            for f in ("analyze_series", "analyze_grid", "compare")
            if getattr(self.stats, f, None) is None
        ]
        detective_missing = [
            f
            for f in ("retrieve", "plan", "scout", "explain", "geocode")
            if getattr(self.detective, f, None) is None
        ]
        return {
            "etl": ModuleStatus(
                ETL_MODULE,
                self.etl is not None and not etl_missing,
                detail(self.etl, self.etl_err, etl_missing)
                if self.fixtures is None
                else "fixtures mode (ALLOW_FIXTURES=1)",
            ),
            "stats": ModuleStatus(
                STATS_MODULE,
                self.stats is not None and not stats_missing,
                detail(self.stats, self.stats_err, stats_missing),
            ),
            "detective": ModuleStatus(
                DETECTIVE_MODULE,
                self.detective is not None and not detective_missing,
                detail(self.detective, self.detective_err, detective_missing),
            ),
        }


class _StubDataUnavailable(Exception):
    """Usado solo cuando no hay ETL real; mantiene el contrato de errores."""

    code: str = "UPSTREAM_ERROR"


class _FixtureBackedModules:
    """Dobles de prueba que leen `tests/fixtures/real/`.

    Sirven para que la API y los tests funcionen antes de que exista
    `src/etl/registry.py`. Jamás se activan sin `ALLOW_FIXTURES=1` y todas sus
    respuestas llevan `provenance.kind = "fixture"`.
    """

    _SEED_IDS = {
        # Variable del catálogo semilla -> parámetro presente en la muestra real.
        "T2M": "T2M",
        "PRECTOTCORR": "PRECTOTCORR",
        "GWETTOP": "GWETTOP",
        "EVLAND": "EVLAND",
        "SNODP": "SNODP",
        "RH2M": "RH2M",
        "TQV": "TQV",
        "TO3": "TO3",
        "AOD_55": "AOD_55",
        "CLOUD_AMT": "CLOUD_AMT",
        "ALLSKY_SFC_SW_DWN": "ALLSKY_SFC_SW_DWN",
        "TS": "TS",
    }

    def __init__(self) -> None:
        self._point_path = FIXTURES_DIR / "power_monthly_point_lima.json"
        self._regional_path = FIXTURES_DIR / "power_monthly_regional_piura_T2M.json"

    def _seed(self) -> dict[str, Any]:
        path = FIXTURES_DIR.parents[2] / "data" / "catalog" / "variables.seed.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _seed_entry(self, variable_id: str) -> dict[str, Any]:
        for entry in self._seed().get("live", []):
            if entry.get("id") == variable_id:
                return entry
        return {}

    def _power_series(self, param: str) -> tuple[dict[str, float], dict[str, Any]]:
        raw = json.loads(self._point_path.read_text(encoding="utf-8"))
        series = raw["properties"]["parameter"].get(param)
        if series is None:
            raise _StubDataUnavailable(f"parameter {param} not in fixture")
        return series, raw.get("header", {})

    def get_series(
        self,
        variable_id: str,
        *,
        lat: float | None = None,
        lon: float | None = None,
        bbox: list[float] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        param = self._SEED_IDS.get(variable_id)
        if param is None:
            raise ApiError(
                "DATA_UNAVAILABLE",
                hint=f"Fixture mode cannot serve {variable_id!r}; it is not in tests/fixtures/real/.",
            )

        entry = self._seed_entry(variable_id)
        series, header = self._power_series(param)
        fill = float(header.get("fill_value", -999.0))

        data: list[dict[str, Any]] = []
        for key in sorted(series):
            if key.endswith("13"):
                continue  # valor anual: se descarta (contrato §3)
            month_key = key[:4] + "-" + key[4:6]
            if start and month_key < start:
                continue
            if end and month_key > end:
                continue
            value = series[key]
            data.append({"date": month_key, "value": None if value == fill else float(value)})

        if not data:
            raise _StubDataUnavailable("OUT_OF_COVERAGE:no data in range")

        if bbox is not None:
            region = {"kind": "bbox", "name": "Piura bbox (fixture)", "lat": None, "lon": None, "bbox": bbox}
            aggregation = "area_mean_coslat"
        else:
            region = {
                "kind": "point",
                "name": "Lima, Peru (fixture)",
                "lat": -12.05 if lat is None else lat,
                "lon": -77.03 if lon is None else lon,
                "bbox": None,
            }
            aggregation = "point"

        return {
            "schema": "timeseries/2",
            "variable_id": variable_id,
            "unit": entry.get("unit", ""),
            "cadence": "monthly",
            "region": region,
            "aggregation": aggregation,
            "data": data,
            "provenance": {
                "kind": "fixture",
                "source": f"NASA POWER {header.get('api', {}).get('version', '')} (fixture copy)",
                "underlying": entry.get("challenge_named_source"),
                "request_url": "https://power.larc.nasa.gov/api/temporal/monthly/point?...",
                "retrieved_at": "2026-11-14T17:22:00Z",
                "sha256": "fixture-" + param.lower(),
                "native_resolution": "0.5° x 0.625°",
                "citation": "Data: NASA POWER (fixture for development).",
            },
        }

    def get_grid(
        self,
        variable_id: str,
        bbox: list[float],
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        if variable_id != "T2M":
            raise ApiError(
                "DATA_UNAVAILABLE",
                hint=f"Fixture mode cannot serve {variable_id!r}; it is not in tests/fixtures/real/.",
            )
        raw = json.loads(self._regional_path.read_text(encoding="utf-8"))
        feats = raw.get("features", [])
        if not feats:
            raise _StubDataUnavailable("OUT_OF_COVERAGE:empty fixture")
        coords = [f["geometry"]["coordinates"] for f in feats]
        lons = sorted({round(c[0], 4) for c in coords})
        lats = sorted({round(c[1], 4) for c in coords})
        dates = sorted(
            {d[:4] + "-" + d[4:6] for d in feats[0]["properties"]["parameter"]["T2M"] if not d.endswith("13")}
        )
        values = [[None for _ in lons] for _ in lats]
        for feat in feats:
            lon, lat, _elev = feat["geometry"]["coordinates"]
            series = feat["properties"]["parameter"]["T2M"]
            for key, val in series.items():
                if key.endswith("13"):
                    continue
                date = key[:4] + "-" + key[4:6]
                if start and date < start:
                    continue
                if end and date > end:
                    continue
                i = lats.index(round(lat, 4))
                j = lons.index(round(lon, 4))
                if values[i][j] is None:
                    values[i][j] = {}
                values[i][j][date] = None if val == -999.0 else float(val)
        # Reordenar a [t][lat][lon]
        grid_values: list[list[list[float | None]]] = []
        for date in dates:
            layer = []
            for i in range(len(lats)):
                row = []
                for j in range(len(lons)):
                    cell = values[i][j]
                    row.append(None if cell is None else cell.get(date))
                layer.append(row)
            grid_values.append(layer)
        return {
            "lats": lats,
            "lons": lons,
            "dates": dates,
            "values": grid_values,
            "unit": "°C",
            "provenance": {
                "kind": "fixture",
                "source": "NASA POWER regional (fixture copy)",
                "request_url": "https://power.larc.nasa.gov/api/temporal/monthly/regional?...",
                "retrieved_at": "2026-11-14T17:25:00Z",
                "sha256": "fixture-regional-t2m",
            },
        }


@lru_cache(maxsize=1)
def modules() -> _Resolver:
    return _Resolver()


def clear_cache() -> None:
    modules.cache_clear()


def require(fn: Callable[..., Any] | None, *, what: str) -> Callable[..., Any]:
    """Devuelve la función o lanza `503` con pista clara (nunca datos falsos)."""
    if fn is None:
        raise ApiError(
            "DATA_UNAVAILABLE",
            message={
                "es": f"El módulo de {what} todavía no está disponible en esta rama.",
                "en": f"The {what} module is not available on this branch yet.",
            },
            hint="The ETL/stats lanes must be merged; see docs/CONTRATOS.md §6.",
        )
    return fn
