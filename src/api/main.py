"""
Servidor API REST con FastAPI para EarthTrend Detective.
Provee endpoints para consultar variables satelitales, regiones y ejecutar
el análisis estadístico en tiempo real.
"""

import os
import json
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import local del motor estadístico
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
from src.stats.trend_engine import analyze_earth_science_trend

app = FastAPI(
    title="NASA EarthTrend Detective API",
    description="API de análisis de tendencias y significancia estadística para datos de Ciencias de la Tierra.",
    version="1.0.0"
)

# Habilitar CORS para permitir llamadas desde el frontend local o la red de Herdr
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATALOG_PATH = os.path.join(BASE_DIR, "data", "variables_catalog.json")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")


def load_catalog() -> Dict[str, Any]:
    if not os.path.exists(CATALOG_PATH):
        raise HTTPException(status_code=500, detail="Catálogo de variables no encontrado")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "NASA EarthTrend Detective API",
        "endpoints": ["/api/variables", "/api/regions", "/api/cases", "/api/analyze"]
    }


@app.get("/api/variables")
def get_variables():
    catalog = load_catalog()
    return {"variables": catalog.get("variables", [])}


@app.get("/api/regions")
def get_regions():
    catalog = load_catalog()
    return {"regions": catalog.get("predefined_regions", [])}


@app.get("/api/cases")
def get_cases():
    """Retorna los casos emblemáticos listos para análisis instantáneo."""
    catalog = load_catalog()
    cases = []
    for reg in catalog.get("predefined_regions", []):
        cases.append({
            "region_id": reg["id"],
            "region_name": reg["name"],
            "variable_id": reg["primary_variable"],
            "description": reg["description"]
        })
    return {"cases": cases}


@app.get("/api/analyze")
def analyze(
    region_id: str = Query(..., description="ID de la región (ej: amazon_deforestation_arc)"),
    variable_id: str = Query(..., description="ID de la variable (ej: MODIS_NDVI)")
):
    catalog = load_catalog()

    # Buscar variable
    var_meta = next((v for v in catalog.get("variables", []) if v["id"] == variable_id), None)
    if not var_meta:
        raise HTTPException(status_code=404, detail=f"Variable '{variable_id}' no encontrada en el catálogo.")

    # Buscar región
    reg_meta = next((r for r in catalog.get("predefined_regions", []) if r["id"] == region_id), None)
    if not reg_meta:
        reg_meta = {"id": region_id, "name": region_id, "biome": "Región personalizada"}

    # Cargar archivo procesado correspondiente
    filename = f"{region_id}_{variable_id}.json"
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)

    if not os.path.exists(filepath):
        # Fallback inteligente: buscar cualquier archivo de esa región o usar el primero disponible
        available = [f for f in os.listdir(PROCESSED_DATA_DIR) if f.endswith(".json")]
        if not available:
            raise HTTPException(status_code=404, detail="No hay series temporales cargadas en data/processed/")
        filepath = os.path.join(PROCESSED_DATA_DIR, available[0])

    with open(filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)

    series_data = payload.get("data", [])
    if not series_data:
        raise HTTPException(status_code=400, detail="La serie temporal no contiene observaciones.")

    result = analyze_earth_science_trend(series_data, var_meta, reg_meta)
    return result


class CustomAnalysisRequest(BaseModel):
    variable_id: str
    region_name: str
    series: List[Dict[str, Any]]


@app.post("/api/analyze_custom")
def analyze_custom(req: CustomAnalysisRequest):
    catalog = load_catalog()
    var_meta = next((v for v in catalog.get("variables", []) if v["id"] == req.variable_id), {
        "id": req.variable_id,
        "name": req.variable_id,
        "unit": "unidades"
    })
    reg_meta = {"id": "custom", "name": req.region_name, "biome": "Área de estudio definida por usuario"}

    result = analyze_earth_science_trend(req.series, var_meta, reg_meta)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
