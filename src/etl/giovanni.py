# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Parser de exportaciones CSV de NASA Giovanni (GES DISC).
Parsea metadatos de cabecera, extrae series temporales, convierte valores de relleno a null,
y agrega series diarias a mensuales con el criterio del >= 70 % de días válidos.
Cumple con el esquema TimeSeries v2 (provenance.kind = "user_upload").
"""

import csv
import io
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict

from src.etl.power import DataUnavailable


def parse_giovanni_csv(text: str, variable_id: Optional[str] = None) -> dict:
    """
    Parsea el contenido de texto de un archivo CSV exportado desde Giovanni.
    Devuelve un diccionario con formato TimeSeries v2.
    """
    if not text or not text.strip():
        raise DataUnavailable("UPSTREAM_ERROR", "El contenido CSV de Giovanni está vacío")

    lines = [line.strip() for line in text.splitlines()]
    header_meta: Dict[str, str] = {}
    data_rows: List[List[str]] = []
    in_data = False
    data_header: List[str] = []

    for line in lines:
        if not line:
            continue
        # Metadatos comentados o clave-valor en la cabecera
        if line.startswith("#") or (not in_data and ":" in line and not line.lower().startswith("time")):
            clean_meta = line.lstrip("#").strip()
            if ":" in clean_meta:
                k, v = clean_meta.split(":", 1)
                header_meta[k.strip()] = v.strip()
            continue

        # Detección del inicio de la tabla de datos
        parts = [p.strip() for p in next(csv.reader([line]))]
        if not in_data:
            lower_parts = [p.lower() for p in parts]
            if any("time" in p or "date" in p for p in lower_parts):
                data_header = parts
                in_data = True
                continue
            else:
                continue

        # Fila de datos
        if in_data and len(parts) >= 2:
            data_rows.append(parts)

    if not data_rows:
        raise DataUnavailable("UPSTREAM_ERROR", "No se encontraron filas de datos en el CSV de Giovanni")

    # Identificar variable y unidad
    extracted_var = variable_id or header_meta.get("Variable") or header_meta.get("Parameter") or "GIOVANNI_VAR"
    extracted_unit = header_meta.get("Units") or header_meta.get("Unit") or ""
    if len(data_header) >= 2 and not extracted_unit:
        col_title = data_header[1]
        if "(" in col_title and ")" in col_title:
            extracted_unit = col_title.split("(")[-1].split(")")[0].strip()

    fill_val = float(header_meta.get("FillValue", -999.0)) if "FillValue" in header_meta else -999.0

    # Parsear puntos fecha -> valor
    raw_points = []
    is_daily = False

    for row in data_rows:
        date_str = row[0].strip()
        val_str = row[1].strip()
        
        # Parsear fecha: YYYY-MM o YYYY-MM-DD
        date_clean = date_str.split("T")[0].split(" ")[0]
        date_parts = date_clean.split("-")
        if len(date_parts) == 3:
            is_daily = True
            
        try:
            val_num = float(val_str)
            if abs(val_num - fill_val) < 1e-4:
                val = None
            else:
                val = round(val_num, 4)
        except ValueError:
            val = None

        raw_points.append((date_clean, val))

    clean_series = []
    if is_daily:
        # Agregar a mensual con regla de >= 70% de cobertura
        months_data = defaultdict(list)
        for dt_str, val in raw_points:
            parts = dt_str.split("-")
            if len(parts) >= 2:
                ym = f"{parts[0]}-{parts[1]}"
                months_data[ym].append(val)

        for ym in sorted(months_data.keys()):
            vals = months_data[ym]
            total_days = len(vals)
            valid_vals = [v for v in vals if v is not None]
            if total_days > 0 and (len(valid_vals) / total_days) >= 0.70:
                monthly_mean = round(sum(valid_vals) / len(valid_vals), 4)
            else:
                monthly_mean = None
            clean_series.append({"date": ym, "value": monthly_mean})
    else:
        # Ya es mensual
        for dt_str, val in raw_points:
            parts = dt_str.split("-")
            ym = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else dt_str
            clean_series.append({"date": ym, "value": val})

    sha256_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    provenance = {
        "kind": "user_upload",
        "source": "NASA Giovanni (GES DISC)",
        "underlying": header_meta.get("Product", "NASA Earth Science Data"),
        "request_url": header_meta.get("URL", "https://giovanni.gsfc.nasa.gov/giovanni/"),
        "retrieved_at": now_iso,
        "sha256": sha256_hash,
        "native_resolution": header_meta.get("Resolution", "Area-Averaged"),
        "citation": "Goddard Earth Sciences Data and Information Services Center (GES DISC) / NASA Giovanni"
    }

    region_name = header_meta.get("Region", "Uploaded Giovanni Region")

    return {
        "schema": "timeseries/2",
        "variable_id": extracted_var,
        "unit": extracted_unit,
        "cadence": "monthly",
        "region": {
            "kind": "named",
            "name": region_name,
            "lat": None,
            "lon": None,
            "bbox": None
        },
        "aggregation": "area_mean_coslat" if "area" in region_name.lower() else "point",
        "data": clean_series,
        "provenance": provenance
    }
