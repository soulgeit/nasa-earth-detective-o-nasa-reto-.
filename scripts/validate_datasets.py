# SI-assisted: Antigravity 1 (Claude Opus 5.5)
"""
Validador de datasets del ETL (contrato v2 §3).

Uso:
    python scripts/validate_datasets.py <ruta.json> [<ruta.json> ...]

Comprueba: esquema `timeseries/2`, `provenance.kind` permitido, `sha256`
presente, fechas YYYY-MM crecientes sin duplicados, ningun -999, >= 120 meses.
Sale con codigo != 0 si algun archivo falla. Sin argumentos, valida todos los
JSON de `data/catalog/` que declaren `timeseries/2` (hoy: ninguno).
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.etl.validate import validate_file  # noqa: E402


def main(argv: list[str]) -> int:
    paths = argv[1:]
    if not paths:
        print("uso: python scripts/validate_datasets.py <archivo.json> [...]")
        return 2
    failed = 0
    for path in paths:
        errors = validate_file(path)
        if errors:
            failed += 1
            print(f"[FAIL] {path}")
            for err in errors:
                print(f"   - {err}")
        else:
            print(f"[ OK ] {path}")
    print(f"\n{len(paths) - failed}/{len(paths)} archivos validos")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
