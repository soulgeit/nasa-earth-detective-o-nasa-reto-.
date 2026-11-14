"""
Servidor API REST v2 con FastAPI para EarthTrend Detective.

Endpoints:
  GET  /api/health              — estado del servidor
  GET  /api/variables           — catálogo de variables NASA POWER
  GET  /api/regions             — regiones predefinidas (Lima, Piura, etc.)
  GET  /api/analyze_real        — análisis con datos reales de NASA POWER
  GET  /api/analyze             — análisis legacy (datos cached)
  POST /api/analyze_custom      — análisis sobre serie arbitraria

El motor estadístico (trend_engine v2) incluye:
  - Mann-Kendall con corrección de empates y autocorrelación (Hamed & Rao 2002)
  - Theil-Sen completo
  - OLS con IC 95 %, valor-p de la pendiente y R² ajustado
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys_path = str(BASE_DIR)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from src.stats.trend_engine import analyze as analyze_trend
from src.etl.power import get_power_point_series, get_power_regional_series


# ---------------------------------------------------------------------------
# Instancia
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NASA EarthTrend Detective API v2",
    description=(
        "Análisis de tendencias en variables de Ciencias de la Tierra "
        "con datos reales de NASA POWER y estadística corregida."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caché del cliente POWER (reutiliza sesión)
# ---------------------------------------------------------------------------
# Datos estáticos
# ---------------------------------------------------------------------------

CATALOG_PATH = BASE_DIR / "data" / "variables_catalog.json"

PREDEFINED_REGIONS = [
    {
        "id": "lima_peru",
        "name": "Lima, Perú",
        "lat": -12.05,
        "lon": -77.03,
        "biome": "Desierto costero",
        "description": "Ciudad de Lima, clima desértico con influencia de El Niño",
    },
    {
        "id": "piura_peru",
        "name": "Piura, Perú",
        "lat": -5.19,
        "lon": -80.63,
        "biome": "Sabana costera / El Niño",
        "description": "Región norte afectada fuertemente por El Niño",
    },
    {
        "id": "cusco_peru",
        "name": "Cusco, Perú",
        "lat": -13.53,
        "lon": -71.97,
        "biome": "Altiplano andino",
        "description": "Ciudad del Cusco, 3.400 msnm, clima de montaña",
    },
    {
        "id": "iyaca_peru",
        "name": "Iquitos, Perú",
        "lat": -3.75,
        "lon": -73.25,
        "biome": "Selva amazónica",
        "description": "Puerto principal de la selva amazónica peruana",
    },
    {
        "id": "arctic_sea_ice",
        "name": "Mar Ártico",
        "lat": 75.0,
        "lon": 0.0,
        "biome": "Hielo marino ártico",
        "description": "Región ártica con tendencia de pérdida de hielo documentada",
    },
    {
        "id": "sahel_africa",
        "name": "Sahel, África",
        "lat": 15.0,
        "lon": 0.0,
        "biome": "Sahel semiárido",
        "description": "Zona de transición Sahara-Sahel, alta variabilidad",
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "EarthTrend Detective API v2",
        "version": "2.0.0",
        "endpoints": [
            "/api/variables",
            "/api/regions",
            "/api/analyze_real",
            "/api/analyze",
            "/api/analyze_custom",
            "/docs",
        ],
    }


@app.get("/api/variables")
def get_variables():
    """Devuelve las variables de NASA POWER con nombre y unidades."""
    return {
        "source": "NASA POWER (MERRA-2 / CERES)",
        "variables": [
            {"id": k, "name": v[0], "unit": v[1]}
            for k, v in POWER_PARAMETERS.items()
        ],
    }


@app.get("/api/regions")
def get_regions():
    """Regiones predefinidas con coordenadas."""
    return {"regions": PREDEFINED_REGIONS}


@app.get("/api/analyze_real")
def analyze_real(
    variable_id: str = Query(..., description="Variable POWER (ej: T2M)"),
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    start: int = Query(2000, description="Año o YYYYMM inicio"),
    end: int = Query(2024, description="Año o YYYYMM fin"),
    temporal: str = Query("monthly", regex="daily|monthly"),
    community: str = Query("RE", regex="RE|AG|SB|HY"),
    region_name: Optional[str] = Query(None, description="Nombre de región"),
    biome: Optional[str] = Query(None, description="Bioma"),
):
    """
    Análisis con datos reales de NASA POWER.

    1. Descarga la serie de POWER (o cache local).
    2. Ejecuta el motor estadístico v2 (MK corregido + Theil-Sen + OLS con IC).
    3. Devuelve veredicto con las 4 preguntas.
    """
    # 1. Obtener datos reales de NASA POWER (función del módulo power.py)
    try:
        # POWER usa start/end como años (YYYY) o YYYYMM
        power_data = get_power_point_series(
            param=variable_id,
            lat=lat,
            lon=lon,
            start_year=start,
            end_year=end,
            name=region_name or f"Lat {lat}, Lon {lon}",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"POWER API error: {e}")

    series = power_data["data"]
    if not series:
        raise HTTPException(
            status_code=400,
            detail="POWER devolvió 0 observaciones. Verifica coordenadas y rango."
        )

    # 2. Metadata de variable
    var_meta = {
        "name": power_data.get("variable_id", variable_id),
        "unit": power_data.get("unit", "?"),
    }

    # 3. Metadata de región
    region_meta = {
        "id": f"{region_name or 'custom'}_{lat}_{lon}",
        "name": region_name or f"Lat {lat}, Lon {lon}",
        "lat": lat,
        "lon": lon,
        "biome": biome or "Región personalizada",
    }

    # 4. Proveniencia
    provenance = {
        "source": power_data.get("provenance", {}).get("source", "NASA POWER"),
        "source_url": "https://power.larc.nasa.gov",
        "fetched_at": power_data.get("provenance", {}).get("retrieved_at", ""),
        "model": power_data.get("provenance", {}).get("underlying", "MERRA-2"),
    }

    # 5. Análisis estadístico
    result = analyze_trend(
        series=series,
        variable_id=variable_id,
        variable_name=var_meta.get("name", variable_id),
        unit=var_meta.get("unit", "?"),
        region=region_meta,
        provenance=provenance,
    )

    return result


@app.get("/api/analyze")
def analyze_legacy(
    region_id: str = Query(..., description="ID de región predefinida"),
    variable_id: str = Query("T2M", description="Variable POWER"),
):
    """
    Análisis legacy: carga la región del catálogo y llama a analyze_real.
    Equivalente a analyze_real con las coordenadas de la región.
    """
    region = next((r for r in PREDEFINED_REGIONS if r["id"] == region_id), None)
    if not region:
        # Buscar en catálogo legacy
        if CATALOG_PATH.exists():
            with open(CATALOG_PATH, "r") as f:
                catalog = json.load(f)
            region = next(
                (r for r in catalog.get("predefined_regions", []) if r["id"] == region_id),
                None,
            )
        if not region:
            raise HTTPException(
                status_code=404,
                detail=f"Región '{region_id}' no encontrada"
            )

    # Llamada a analyze_real con los params de la región
    lat = region.get("lat", 0.0)
    lon = region.get("lon", 0.0)

    try:
        power_data = get_power_point_series(
            param=variable_id,
            lat=lat,
            lon=lon,
            start_year=2000,
            end_year=2024,
            name=region.get("name", region_id),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"POWER API error: {e}")

    series = power_data["data"]
    var_meta = {
        "name": power_data.get("variable_id", variable_id),
        "unit": power_data.get("unit", "?"),
    }
    region_meta = {
        "id": region_id,
        "name": region.get("name", region_id),
        "lat": lat,
        "lon": lon,
        "biome": region.get("biome", "Región personalizada"),
    }
    provenance = {
        "source": power_data.get("source", "NASA POWER"),
        "source_url": power_data.get("source_url", ""),
        "fetched_at": power_data.get("provenance", {}).get("fetched_at", ""),
        "model": power_data.get("provenance", {}).get("model", "MERRA-2"),
    }

    return analyze_trend(
        series=series,
        variable_id=variable_id,
        variable_name=var_meta["name"],
        unit=var_meta["unit"],
        region=region_meta,
        provenance=provenance,
    )


class CustomAnalysisRequest(BaseModel):
    variable_id: str
    region_name: str
    series: List[Dict[str, Any]]


@app.post("/api/analyze_custom")
def analyze_custom(req: CustomAnalysisRequest):
    """
    Análisis sobre una serie arbitraria (ej: CSV subido de Giovanni).
    La serie debe tener campos: "date" y <variable_id>.
    """
    region_meta = {
        "id": "custom",
        "name": req.region_name,
        "biome": "Área de estudio definida por usuario",
    }
    provenance = {
        "source": "Datos del usuario (subido)",
        "source_url": "",
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": "Custom upload",
    }

    return analyze_trend(
        series=req.series,
        variable_id=req.variable_id,
        variable_name=req.variable_id,
        unit="?",
        region=region_meta,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
