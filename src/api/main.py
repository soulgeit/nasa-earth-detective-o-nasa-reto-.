# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
EarthTrend Detective API v2 — implementación del contrato §7.

Principios:
- O devuelve el dato real pedido, o un error con código. Nunca otro dato «parecido».
- La ciencia vive en `src/stats`; los datos, en `src/etl`. Aquí solo se orquesta.
- Procedencia visible en cada respuesta.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import catalog, modules, service, validation
from .cache import analysis_cache
from .config import (
    AI_MODE,
    API_TITLE,
    API_VERSION,
    MAX_UPLOAD_BYTES,
    UI_DIR,
)
from .errors import ApiError, api_error_handler, http_exception_handler
from .logging_mw import StructuredAccessLog
from .ratelimit import limiter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("etd.api")

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "Honest trend analysis for real NASA Earth science data. "
        "Every answer either carries its real data and provenance, or an explicit error code."
    ),
    docs_url="/docs",
    redoc_url=None,
)

# CORS abierto solo a lo necesario: GET/POST, sin credenciales (A4).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_middleware(StructuredAccessLog)


@app.exception_handler(RequestValidationError)
async def _validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI devuelve `{"detail": [...]}`; el contrato §7 pide `{"error": ...}`."""
    first = (exc.errors() or [{}])[0]
    loc = ".".join(str(p) for p in first.get("loc", ()) if p != "query")
    err = ApiError(
        "INVALID_REQUEST",
        hint=f"{loc}: {first.get('msg', 'invalid value')}".strip(),
    )
    return JSONResponse(status_code=400, content=err.payload())


@app.on_event("startup")
def _startup() -> None:
    log.info("EarthTrend Detective API %s starting (ai_mode=%s)", API_VERSION, AI_MODE)


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------


def _client_key(request: Request) -> str:
    """IP del cliente para el límite de peticiones. Sin datos personales.

    Detrás del proxy de la nube (Fly, Render, Koyeb) `request.client.host` es la
    IP del proxy, así que todos los visitantes compartirían el mismo cupo de 120
    peticiones por minuto y la demo se bloquearía sola. Se prefiere la primera
    entrada de `X-Forwarded-For`, que el proxy antepone.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    first = forwarded.split(",")[0].strip()
    if first:
        return first
    return request.client.host if request.client else "unknown"


def _limit(request: Request) -> None:
    limiter.check(_client_key(request))


def _data_headers(extra: dict[str, Any] | None = None) -> dict[str, str]:
    headers = {"Cache-Control": "no-store"}
    if extra:
        headers.update({k: str(v) for k, v in extra.items()})
    return headers


# --------------------------------------------------------------------------
# /health
# --------------------------------------------------------------------------


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, Any]:
    status = modules.modules().status()
    sources_up = {
        "etl": status["etl"].available,
        "stats": status["stats"].available,
        "detective": status["detective"].available,
    }
    overall = "ok" if sources_up["etl"] and sources_up["stats"] else "degraded"
    return {
        "status": overall,
        "version": API_VERSION,
        "ai_mode": AI_MODE,
        "sources_up": sources_up,
        "modules": {k: {"name": v.name, "available": v.available, "detail": v.detail} for k, v in status.items()},
        "cache": analysis_cache.stats(),
    }


@app.get("/api/health/live", tags=["meta"])
def health_live() -> dict[str, str]:
    return {"status": "ok"}


# --------------------------------------------------------------------------
# Catálogo, regiones y casos congelados
# --------------------------------------------------------------------------


@app.get("/api/catalog/variables", tags=["catalog"])
def list_variables(lang: str = Query("es", pattern="^(es|en)$")) -> dict[str, Any]:
    cards = catalog.all_variables()
    meta = catalog.catalog_meta()
    out = []
    for card in cards:
        item = dict(card)
        for field in ("names", "simple_definition"):
            value = item.get(field)
            if isinstance(value, dict) and lang in value:
                item[f"{field}_lang"] = value[lang]
        out.append(item)
    return {"catalog": meta, "variables": out}


@app.get("/api/catalog/regions", tags=["catalog"])
def list_regions() -> dict[str, Any]:
    """Regiones con nombre. Con la semilla aún no hay gazetteer; se informa."""
    from .config import DATA_DIR

    path = DATA_DIR / "catalog" / "gazetteer.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            regions = data.get("regions", data) if isinstance(data, dict) else data
            return {"source": "gazetteer", "regions": regions}
        except json.JSONDecodeError as exc:
            raise ApiError("INTERNAL_ERROR", hint=f"Invalid gazetteer.json: {exc}") from exc
    return {
        "source": "none",
        "regions": [],
        "hint": "Geocoding (Hermes 1 gazetteer) is not available on this branch yet; click on the map instead.",
    }


def _frozen(kind: str) -> list[dict[str, Any]]:
    from .config import CASES_DIR, ATLAS_DIR

    base = CASES_DIR if kind == "cases" else ATLAS_DIR
    index = base / "index.json"
    if not index.exists():
        raise ApiError(
            "DATA_UNAVAILABLE",
            message={
                "es": f"Los {kind} congelados todavía no existen en esta rama.",
                "en": f"Frozen {kind} are not available on this branch yet.",
            },
            hint=f"Expected {index.relative_to(index.parents[2])} (Hermes 2 lane).",
        )
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError("INTERNAL_ERROR", hint=f"Invalid frozen index: {exc}") from exc
    items = data.get(kind, data) if isinstance(data, dict) else data
    _check_provenance(items, kind)
    return items


def _check_provenance(items: Any, kind: str) -> None:
    if not isinstance(items, list):
        raise ApiError("INTERNAL_ERROR", hint=f"Frozen {kind} index is not a list.")
    for item in items:
        provenance = (item or {}).get("provenance") or {}
        if provenance.get("kind") not in {"nasa_api", "nasa_file", "user_upload"}:
            raise ApiError(
                "INTERNAL_ERROR",
                hint=f"Frozen {kind} item without a valid NASA provenance: {provenance.get('kind')!r}",
            )


@app.get("/api/cases", tags=["catalog"])
def list_cases() -> dict[str, Any]:
    return {"cases": _frozen("cases")}


@app.get("/api/atlas/{variable_id}", tags=["catalog"])
def get_atlas(variable_id: str) -> dict[str, Any]:
    catalog.get_variable(variable_id)
    from .config import ATLAS_DIR

    path = ATLAS_DIR / f"{variable_id}.json"
    if not path.exists():
        raise ApiError(
            "DATA_UNAVAILABLE",
            message={
                "es": f"El atlas para '{variable_id}' no está precalculado.",
                "en": f"The atlas for '{variable_id}' is not precomputed.",
            },
            hint="Frozen atlas files are produced by the Hermes 2 lane.",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError("INTERNAL_ERROR", hint=f"Invalid atlas file: {exc}") from exc
    if data.get("schema") != "trendmap/2":
        raise ApiError("INTERNAL_ERROR", hint="Frozen atlas file is not a trendmap/2.")
    _check_provenance([data], "atlas")
    return data


@app.get("/api/geocode", tags=["catalog"])
def geocode(q: str = Query(..., min_length=1, max_length=120)) -> dict[str, Any]:
    from .config import DATA_DIR

    path = DATA_DIR / "catalog" / "gazetteer.json"
    if not path.exists():
        raise ApiError(
            "DATA_UNAVAILABLE",
            message={"es": "El gazetteer todavía no está disponible.", "en": "The gazetteer is not available yet."},
            hint="Click on the map instead; Hermes 1 publishes data/catalog/gazetteer.json.",
        )
    # El buscador real lo implementa el detective (contrato §6, geocode).
    geo = modules.modules().detective_fn("geocode")
    if geo is None:
        raise ApiError("AI_UNAVAILABLE", hint="src.detective.geocode is not importable yet.")
    return {"places": geo(q)}


# --------------------------------------------------------------------------
# Datos: /series, /analyze, /trendmap, /compare, /analyze/upload
# --------------------------------------------------------------------------


def _series_params(
    variable_id: str,
    lat: float | None,
    lon: float | None,
    bbox: str | None,
    start: str | None,
    end: str | None,
) -> dict[str, Any]:
    catalog.get_variable(variable_id)
    position, mode = validation.point_or_bbox(lat, lon, bbox)
    start, end = validation.check_period(start, end)
    return {"variable_id": variable_id, **position, "start": start, "end": end, "_mode": mode}


@app.get("/api/series", tags=["data"])
def get_series_endpoint(
    request: Request,
    variable_id: str = Query(..., min_length=1, max_length=40),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    bbox: str | None = Query(None, description="oeste,sur,este,norte"),
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
) -> JSONResponse:
    _limit(request)
    params = _series_params(variable_id, lat, lon, bbox, start, end)
    params.pop("_mode")
    ts = service.get_series(**params)
    return JSONResponse(ts, headers=_data_headers())


@app.get("/api/analyze", tags=["data"])
def analyze_endpoint(
    request: Request,
    variable_id: str = Query(..., min_length=1, max_length=40),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    bbox: str | None = Query(None, description="oeste,sur,este,norte"),
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
) -> JSONResponse:
    _limit(request)
    params = _series_params(variable_id, lat, lon, bbox, start, end)
    params.pop("_mode")
    result = service.analyze(**params)
    return JSONResponse(result, headers=_data_headers())


@app.get("/api/trendmap", tags=["data"])
def trendmap_endpoint(
    request: Request,
    variable_id: str = Query(..., min_length=1, max_length=40),
    bbox: str = Query(..., description="oeste,sur,este,norte"),
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
) -> JSONResponse:
    _limit(request)
    catalog.get_variable(variable_id)
    box = validation.check_bbox(bbox)
    assert box is not None
    start, end = validation.check_period(start, end)
    result = service.trendmap(variable_id, box, start=start, end=end)
    return JSONResponse(result, headers=_data_headers())


@app.get("/api/compare", tags=["data"])
def compare_endpoint(
    request: Request,
    variable_id: str = Query(..., min_length=1, max_length=40),
    a: str = Query(..., description="lat,lon del primer punto"),
    b: str = Query(..., description="lat,lon del segundo punto"),
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
) -> JSONResponse:
    _limit(request)

    def parse_point(raw: str, label: str) -> tuple[float, float]:
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) != 2:
            raise ApiError(
                "INVALID_REQUEST",
                message={"es": f"'{label}' debe ser lat,lon.", "en": f"'{label}' must be lat,lon."},
                hint=raw,
            )
        try:
            return validation.check_point(float(parts[0]), float(parts[1]))
        except ValueError as exc:
            raise ApiError("INVALID_REQUEST", hint=f"{label}: {raw}") from exc

    pa = parse_point(a, "a")
    pb = parse_point(b, "b")
    start, end = validation.check_period(start, end)
    result = service.compare(variable_id, pa, pb, start=start, end=end)
    return JSONResponse(result, headers=_data_headers())


@app.post("/api/analyze/upload", tags=["data"])
async def analyze_upload_endpoint(
    request: Request,
    file: UploadFile = File(...),
    variable_id: str | None = Query(None, max_length=40),
) -> JSONResponse:
    _limit(request)
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ApiError(
            "TOO_LARGE",
            hint=f"Max upload is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ApiError(
            "INVALID_REQUEST",
            message={"es": "El archivo debe ser texto UTF-8.", "en": "The file must be UTF-8 text."},
            hint=str(exc),
        ) from exc
    result = service.analyze_upload(text, variable_id)
    return JSONResponse(result, headers=_data_headers())


# --------------------------------------------------------------------------
# Endpoints de IA — delegan en src.detective; si falla, el resto sigue.
# --------------------------------------------------------------------------


def _detective_call(attr: str, producer) -> Any:
    fn = modules.modules().detective_fn(attr)
    if fn is None:
        raise ApiError(
            "AI_UNAVAILABLE",
            message={
                "es": "El detective con IA no está disponible; el resto de la app sigue funcionando.",
                "en": "The AI detective is unavailable; the rest of the app keeps working.",
            },
            hint=f"src.detective.{attr} is not importable on this branch.",
        )
    try:
        return producer(fn)
    except Exception as exc:
        raise ApiError("AI_UNAVAILABLE", hint=f"{attr}: {type(exc).__name__}: {exc}"[:300]) from exc


@app.post("/api/ai/plan", tags=["ai"])
def ai_plan(request: Request, question: str = Query(..., min_length=3, max_length=500), lang: str = Query("es")) -> JSONResponse:
    _limit(request)
    lang = validation.check_lang(lang)
    result = _detective_call("plan", lambda fn: fn(question, lang=lang))
    return JSONResponse(result, headers=_data_headers())


@app.post("/api/ai/explain", tags=["ai"])
async def ai_explain(request: Request) -> JSONResponse:
    _limit(request)
    body = await request.json()
    analysis = body.get("analysis")
    level = body.get("level", "school")
    lang = validation.check_lang(body.get("lang"))
    if not isinstance(analysis, dict) or analysis.get("schema") != "analysis/2":
        raise ApiError(
            "INVALID_REQUEST",
            message={"es": "Falta un 'analysis' con esquema analysis/2.", "en": "Missing an 'analysis' with schema analysis/2."},
        )
    result = _detective_call("explain", lambda fn: fn(analysis, level=level, lang=lang))
    return JSONResponse(result, headers=_data_headers())


@app.post("/api/ai/scout", tags=["ai"])
def ai_scout(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    lang: str = Query("es"),
) -> JSONResponse:
    _limit(request)
    lang = validation.check_lang(lang)
    result = _detective_call("scout", lambda fn: fn(lat, lon, lang=lang))
    return JSONResponse(result, headers=_data_headers())


# --------------------------------------------------------------------------
# Informe imprimible
# --------------------------------------------------------------------------


@app.get("/api/report", tags=["data"], response_class=HTMLResponse)
def report_endpoint(
    request: Request,
    variable_id: str = Query(..., min_length=1, max_length=40),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    bbox: str | None = Query(None),
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    lang: str = Query("en"),
) -> HTMLResponse:
    _limit(request)
    from .report import render_report

    lang = validation.check_lang(lang)
    params = _series_params(variable_id, lat, lon, bbox, start, end)
    params.pop("_mode")
    result = service.analyze(**params)
    return HTMLResponse(render_report(result, lang=lang))


# --------------------------------------------------------------------------
# UI estática servida por el mismo servicio (A5)
# --------------------------------------------------------------------------
#
# La UI referencia `app.js`, `styles.css` e `i18n.js` de forma relativa, así que
# tiene que vivir en la raíz, no bajo `/ui`. Los assets se sirven con caché; el
# HTML, siempre revalidado, para que un despliegue nuevo se vea al recargar.

_CACHE_HEADERS = {"Cache-Control": "public, max-age=3600"}
_HTML_HEADERS = {"Cache-Control": "no-cache"}


def _ui_asset(path: str):
    candidate = (UI_DIR / path).resolve()
    try:
        candidate.relative_to(UI_DIR.resolve())
    except ValueError:
        return None  # fuera del directorio de la UI: no se sirve
    if candidate.is_file() and candidate.suffix in {".js", ".css", ".map", ".svg", ".png", ".ico", ".woff2"}:
        media = {
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".woff2": "font/woff2",
        }.get(candidate.suffix, "application/octet-stream")
        return Response(content=candidate.read_bytes(), media_type=media, headers=_CACHE_HEADERS)
    return None


@app.get("/", include_in_schema=False)
def root() -> Any:
    index = UI_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"), headers=_HTML_HEADERS)
    return JSONResponse({"service": API_TITLE, "version": API_VERSION, "docs": "/docs", "api": "/api"})


_ASSET_SUFFIXES = {".js", ".css", ".map", ".svg", ".png", ".ico", ".woff2", ".jpg", ".webp"}


@app.get("/{asset_path:path}", include_in_schema=False)
def static_ui(asset_path: str) -> Any:
    """Assets de la UI en la raíz. Las rutas /api/* las gana el router de la API."""
    if asset_path.startswith("api/") or asset_path.startswith(("docs", "openapi.json", "redoc")):
        raise ApiError("NOT_FOUND", hint=asset_path)
    served = _ui_asset(asset_path)
    if served is not None:
        return served
    if Path(asset_path).suffix.lower() in _ASSET_SUFFIXES:
        # Un asset que falta NO puede caer en el fallback HTML: el navegador
        # recibiría HTML donde espera JavaScript y fallaría sin decir por qué.
        raise ApiError(
            "NOT_FOUND",
            message={"es": "Ese archivo de la interfaz no existe.", "en": "That interface asset does not exist."},
            hint=asset_path,
        )
    index = UI_DIR / "index.html"
    if index.exists():
        # SPA fallback: cualquier ruta desconocida devuelve la página, no un 404 seco.
        return HTMLResponse(index.read_text(encoding="utf-8"), headers=_HTML_HEADERS)
    raise ApiError("NOT_FOUND", hint=asset_path)


@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Response-Time-ms"] = f"{(time.perf_counter() - started) * 1000:.0f}"
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
