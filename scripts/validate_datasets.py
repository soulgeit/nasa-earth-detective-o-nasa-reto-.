# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Validador de datasets del ETL (contrato v2 §3, regla 12).

Uso:
    python scripts/validate_datasets.py <ruta.json> [<ruta.json> ...]

Comprueba: esquema `timeseries/2`, `provenance.kind` permitido, `sha256`
presente, fechas YYYY-MM crecientes sin duplicados, ningún centinela de relleno
(-999, -9999, etc.), rangos físicos por variable (Regla 12), >= 120 meses.
Sale con codigo != 0 si algun archivo falla.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.etl.validate import validate_file  # noqa: E402


def expand_paths(args: list[str]) -> list[str]:
    """Expande comodines aqui: PowerShell y cmd pasan `data/cases/*/series.json` tal cual.

    Un patron sin coincidencias se devuelve intacto para que cuente como fallo
    visible en vez de desaparecer de la cuenta.
    """
    import glob

    out: list[str] = []
    for arg in args:
        if any(ch in arg for ch in "*?["):
            matches = sorted(glob.glob(arg, recursive=True))
            out.extend(matches if matches else [arg])
        else:
            out.append(arg)
    return out


def main(argv: list[str]) -> int:
    paths = expand_paths(argv[1:])
    if not paths:
        print("uso: python scripts/validate_datasets.py <archivo.json> [...]")
        return 2
    failed = 0
    for path in paths:
        if any(ch in path for ch in "*?["):
            failed += 1
            print(f"[FAIL] {path}")
            print("   - ningun archivo coincide con el patron")
            continue
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
