# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Registro central de conectores ETL para EarthTrend Detective.
Despacha consultas de series y rejillas hacia el conector adecuado (POWER, GISTEMP, NSIDC, Giovanni)
según el catálogo de variables oficial (data/catalog/variables.json o variables.seed.json).
Cumple con el contrato §6.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.etl.power import (
    DataUnavailable,
    get_power_point_series,
    get_power_regional_series,
    get_power_grid,
)
from src.etl.giovanni import parse_giovanni_csv
from src.etl.gistemp import get_gistemp_series
from src.etl.nsidc_seaice import get_nsidc_series


def _load_catalog() -> Dict[str, dict]:
    """Carga data/catalog/variables.json o su semilla variables.seed.json."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    cat_path = root_dir / "data" / "catalog" / "variables.json"
    if not cat_path.exists():
        cat_path = root_dir / "data" / "catalog" / "variables.seed.json"

    if not cat_path.exists():
        return {}

    try:
        with open(cat_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    catalog_dict = {}
    # Soportar formato de variables.json (lista en "variables" o "live")
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "variables" in data:
            items = data["variables"]
        elif "live" in data:
            items = data["live"]
        else:
            items = list(data.values())

    for item in items:
        if isinstance(item, dict) and "id" in item:
            catalog_dict[item["id"]] = item

    return catalog_dict


def get_series(
    variable_id: str,
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    bbox: Optional[List[float]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None
) -> dict:
    """
    Obtiene la serie temporal mensual normalizada (TimeSeries v2).
    """
    catalog = _load_catalog()
    var_meta = catalog.get(variable_id)
    if not var_meta:
        # Si no está en el catálogo, pero es un parámetro conocido de POWER, permitirlo como fallback
        connector = "power"
        connector_param = variable_id
    else:
        connector = var_meta.get("connector", "power")
        connector_param = var_meta.get("connector_param", variable_id)

    # Años de inicio y fin
    if variable_id in ("GISTEMP_TANOM", "GISTEMP", "GLOBAL_TEMP_ANOMALY"):
        start_year = int(start.split("-")[0]) if (start and len(start) >= 4) else 1880
    elif "SEAICE" in variable_id:
        start_year = int(start.split("-")[0]) if (start and len(start) >= 4) else 1979
    else:
        start_year = int(start.split("-")[0]) if (start and len(start) >= 4) else 1981
    end_year = int(end.split("-")[0]) if (end and len(end) >= 4) else 2025

    if connector == "gistemp" or variable_id in ("GISTEMP_TANOM", "GISTEMP", "GLOBAL_TEMP_ANOMALY"):
        return get_gistemp_series(variable_id, start_year=start_year, end_year=end_year)

    elif connector == "nsidc" or "SEAICE" in variable_id:
        return get_nsidc_series(variable_id, start_year=start_year, end_year=end_year)

    elif connector == "power":
        if bbox is not None:
            return get_power_regional_series(
                connector_param, bbox, start_year=start_year, end_year=end_year
            )
        elif lat is not None and lon is not None:
            return get_power_point_series(
                connector_param, lat, lon, start_year=start_year, end_year=end_year
            )
        else:
            raise DataUnavailable(
                "OUT_OF_COVERAGE",
                "Se requiere especificar (lat, lon) o bbox para consultar NASA POWER"
            )

    elif connector == "giovanni_csv":
        raise DataUnavailable(
            "OUT_OF_COVERAGE",
            f"La variable {variable_id} requiere subir un CSV de Giovanni via parse_giovanni_csv"
        )
    else:
        raise DataUnavailable(
            "VARIABLE_UNKNOWN",
            f"Conector '{connector}' no implementado para variable {variable_id}"
        )


def get_grid(
    variable_id: str,
    bbox: List[float],
    *,
    start: Optional[str] = None,
    end: Optional[str] = None
) -> dict:
    """
    Obtiene la rejilla temporal mensual normalizada para mapas de tendencias (TrendMap v2).
    """
    catalog = _load_catalog()
    var_meta = catalog.get(variable_id)
    if not var_meta:
        connector = "power"
        connector_param = variable_id
    else:
        connector = var_meta.get("connector", "power")
        connector_param = var_meta.get("connector_param", variable_id)

    start_year = int(start.split("-")[0]) if (start and len(start) >= 4) else 1981
    end_year = int(end.split("-")[0]) if (end and len(end) >= 4) else 2025

    if connector == "power":
        return get_power_grid(connector_param, bbox, start_year=start_year, end_year=end_year)
    else:
        raise DataUnavailable(
            "VARIABLE_UNKNOWN",
            f"get_grid no disponible para conector {connector} de la variable {variable_id}"
        )


# Exportaciones públicas requeridas por contrato §6
__all__ = [
    "get_series",
    "get_grid",
    "parse_giovanni_csv",
    "get_gistemp_series",
    "get_nsidc_series",
    "DataUnavailable"
]
