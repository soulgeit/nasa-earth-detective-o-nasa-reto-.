# SI-assisted: hermes-2 (Claude Opus 5.5)
"""Comprueba que los casos de hielo marino salieron limpios (Ronda 3, tarea 2).

Criterios de aceptacion:
- min(series.data.value) >= 0  (no queda relleno)
- 1987-12 y 1988-01 son null  (el hueco del satelite, regla 12)
- la pendiente OLS y la de Sen tienen el mismo signo y orden de magnitud

Uso: python -X utf8 -I scripts/verify_seaice_cases.py
Sale con codigo 1 si algun criterio falla.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "data", "cases")
HOLE = ("1987-12", "1988-01")


def check(case_id: str) -> list[str]:
    problems: list[str] = []
    base = os.path.join(CASES, case_id)
    with open(os.path.join(base, "series.json"), encoding="utf-8") as fh:
        series = json.load(fh)
    with open(os.path.join(base, "analysis.json"), encoding="utf-8") as fh:
        analysis = json.load(fh)

    values = {p["date"]: p["value"] for p in series["data"]}
    present = [v for v in values.values() if v is not None]
    lowest = min(present) if present else None
    if lowest is None or lowest < 0:
        problems.append(f"min(series) = {lowest} (deberia ser >= 0)")

    for month in HOLE:
        if values.get(month) is not None:
            problems.append(f"{month} no es null ({values.get(month)})")

    trend = analysis["trend"]
    sen = trend["sen_slope_per_decade"]
    ols = trend["ols_slope_per_decade"]
    if sen is None or ols is None:
        problems.append("falta alguna pendiente")
    elif sen * ols <= 0:
        problems.append(f"signos opuestos: Sen {sen} vs OLS {ols}")
    elif abs(ols) > 10 * max(abs(sen), 1e-9):
        problems.append(f"OLS {ols} desproporcionada frente a Sen {sen}")

    print(f"{case_id}: min={lowest} | {HOLE[0]}={values.get(HOLE[0])} "
          f"{HOLE[1]}={values.get(HOLE[1])} | Sen={sen} OLS={ols} "
          f"-> {'OK' if not problems else 'FALLA'}")
    return problems


def main() -> int:
    failed = 0
    for case_id in ("arctic-seaice", "antarctic-seaice"):
        failed += len(check(case_id))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
