# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Script de validación estricta de datasets (D6).
Verifica:
1. Esquema 'timeseries/2'.
2. provenance.kind permitido ('nasa_api', 'nasa_file', 'user_upload', 'fixture').
3. Campo 'sha256' presente en provenance.
4. Fechas crecientes y sin duplicados ('YYYY-MM').
5. Ningún valor de relleno (-999, -999.0, etc.).
6. Al menos 120 meses (>= 10 años de observaciones).
Sale con código de salida 0 si todos los archivos son válidos, o != 0 si alguno falla.
"""

import sys
import json
from pathlib import Path
from typing import List

ALLOWED_KINDS = {"nasa_api", "nasa_file", "user_upload", "fixture"}


def validate_dataset(data: dict) -> List[str]:
    """Valida la estructura en memoria de un dataset bajo contrato timeseries/2."""
    errors = []

    # 1. Esquema
    schema = data.get("schema")
    if schema != "timeseries/2":
        errors.append(f"Esquema inválido: esperado 'timeseries/2', obtenido '{schema}'")

    # 2 & 3. Provenance
    prov = data.get("provenance")
    if not isinstance(prov, dict):
        errors.append("Falta objeto 'provenance' o no es un diccionario")
    else:
        kind = prov.get("kind")
        if kind not in ALLOWED_KINDS:
            errors.append(f"provenance.kind '{kind}' no permitido (permitidos: {ALLOWED_KINDS})")
        sha256 = prov.get("sha256")
        if not sha256 or len(sha256) < 32:
            errors.append(f"provenance.sha256 ausente o inválido: '{sha256}'")

    # 4, 5, 6. Serie de datos
    pts = data.get("data")
    if not isinstance(pts, list):
        errors.append("Falta lista 'data' en el dataset")
    else:
        if len(pts) < 120:
            errors.append(f"Puntos insuficientes: {len(pts)} meses encontrados, mínimo requerido 120 meses")

        last_date = None
        seen_dates = set()

        for idx, pt in enumerate(pts):
            if not isinstance(pt, dict) or "date" not in pt or "value" not in pt:
                errors.append(f"Punto {idx} no cumple formato {{'date': ..., 'value': ...}}")
                continue

            dt = pt["date"]
            val = pt["value"]

            # Duplicados
            if dt in seen_dates:
                errors.append(f"Fecha duplicada encontrada: '{dt}' en índice {idx}")
            seen_dates.add(dt)

            # Orden estrictamente creciente
            if last_date is not None and dt <= last_date:
                errors.append(f"Fechas no crecientes: '{dt}' tras '{last_date}' en índice {idx}")
            last_date = dt

            # Ningún -999
            if val is not None:
                if isinstance(val, (int, float)) and abs(val - (-999.0)) < 1e-4:
                    errors.append(f"Valor de relleno -999 no transformado a null en fecha '{dt}'")

    return errors


def validate_file(filepath: Path) -> List[str]:
    if not filepath.exists():
        return [f"Archivo no existe: {filepath}"]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"JSON inválido en {filepath}: {e}"]

    return validate_dataset(data)


def main():
    if len(sys.argv) < 2:
        print("Uso: python validate_datasets.py <ruta_archivo_1.json> [ruta_archivo_2.json ...]")
        sys.exit(1)

    all_passed = True
    for arg in sys.argv[1:]:
        p = Path(arg)
        errs = validate_file(p)
        if errs:
            all_passed = False
            print(f"❌ FALLÓ {p.name}:")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"✓ APROBADO {p.name}: Cumple timeseries/2, procedencia verificada, orden temporal y sin nulos corruptos.")

    if all_passed:
        print("\n✅ Todos los datasets fueron validados con éxito.")
        sys.exit(0)
    else:
        print("\n❌ Se detectaron fallos de conformidad en uno o más datasets.")
        sys.exit(1)


if __name__ == "__main__":
    main()
