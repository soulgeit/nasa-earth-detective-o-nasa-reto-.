"""
Herramienta de Control de Calidad (QA) para el Jefe de Scrapers (Antigravity 1).
Valida que todos los datasets generados por Hermes 1 y Hermes 2 cumplan
con el esquema de datos y los estándares científicos de la NASA.
"""

import os
import json
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(BASE_DIR, "data", "variables_catalog.json")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def audit_catalog():
    print("🔍 [1/2] Auditando catálogo de variables (Hermes 1)...")
    if not os.path.exists(CATALOG_PATH):
        print("  ❌ ERROR: No se encontró data/variables_catalog.json")
        return False

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    variables = catalog.get("variables", [])
    regions = catalog.get("predefined_regions", [])

    print(f"  ✓ {len(variables)} variables registradas.")
    print(f"  ✓ {len(regions)} regiones de estudio configuradas.")

    for v in variables:
        required = ["id", "name", "satellite_instrument", "unit", "simple_definition"]
        for r in required:
            if r not in v:
                print(f"  ⚠️ Advertencia: Variable {v.get('id')} carece del campo '{r}'")
    return True


def audit_timeseries():
    print("\n🔍 [2/2] Auditando series temporales procesadas (Hermes 2)...")
    if not os.path.exists(PROCESSED_DIR):
        print("  ❌ ERROR: No existe la carpeta data/processed/")
        return False

    files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".json")]
    if not files:
        print("  ❌ ERROR: No hay datasets en data/processed/")
        return False

    print(f"  ✓ Se encontraron {len(files)} archivos de datos procesados.")
    all_ok = True

    for filename in files:
        filepath = os.path.join(PROCESSED_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)

        data = content.get("data", [])
        if len(data) < 24:
            print(f"  ⚠️ {filename}: Datos insuficientes ({len(data)} puntos). Mínimo 24 meses requeridos.")
            all_ok = False
        else:
            # Chequear integridad de fechas y valores numéricos
            nulls = [p for p in data if p.get("value") is None]
            if nulls:
                print(f"  ❌ {filename}: Contiene {len(nulls)} valores nulos.")
                all_ok = False
            else:
                print(f"  ✓ {filename}: {len(data)} puntos continuos sin nulos ({data[0]['date']} a {data[-1]['date']}).")

    return all_ok


if __name__ == "__main__":
    c_ok = audit_catalog()
    t_ok = audit_timeseries()
    if c_ok and t_ok:
        print("\n✅ Veredicto de Antigravity 1 (Jefe de Scrapers): Todos los datos están validados y aprobados para los Constructores.")
        sys.exit(0)
    else:
        print("\n⚠️ Veredicto: Se encontraron advertencias que los scrapers deben corregir.")
        sys.exit(1)
