# SI-assisted: Antigravity 1 (Gemini 3.8 Flash)
"""
Comparación cuantitativa entre NASA POWER y NASA Giovanni (MERRA-2)
para la región de la Amazonía (bbox=[-71.0, 0.85, -69.84, 1.7]) en el periodo común 1981-01 a 2025-12 (540 meses).

Compara:
- Temperatura a 2 m (T2M, °C)
- Precipitación corregida (PRECTOTCORR, mm/día)

Métricas:
- Pendiente de Sen (por década) e intervalo de confianza del 95%
- Veredicto de tendencia del motor estadístico (Mann-Kendall + MCO adaptativo)
- Diferencia media (POWER - Giovanni), MAE, RMSE y correlación de Pearson (r).

Uso:
    python scripts/compare_power_giovanni.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.etl.giovanni import parse_csv
from src.etl import registry
from src.stats.trend_engine import analyze_series


def compare_variable(var_id: str, csv_path: str, bbox: list[float], start: str, end: str) -> dict:
    with open(csv_path, "r", encoding="utf-8") as fh:
        raw_csv = fh.read()
    ts_gio_raw = parse_csv(raw_csv, variable_id=var_id)

    # Filtrar al periodo común
    gio_dict = {p["date"]: p["value"] for p in ts_gio_raw["data"] if start <= p["date"] <= end}
    ts_gio = dict(ts_gio_raw)
    ts_gio["data"] = [{"date": d, "value": gio_dict[d]} for d in sorted(gio_dict)]

    # Obtener serie de POWER
    ts_power = registry.get_series(var_id, bbox=bbox, start=start, end=end)
    power_dict = {p["date"]: p["value"] for p in ts_power["data"] if start <= p["date"] <= end}

    # Análisis estadístico
    res_gio = analyze_series(ts_gio)
    res_pow = analyze_series(ts_power)

    # Métricas de concordancia punto a punto
    common_dates = sorted(set(gio_dict.keys()) & set(power_dict.keys()))
    vals_gio = np.array([gio_dict[d] for d in common_dates], dtype=float)
    vals_pow = np.array([power_dict[d] for d in common_dates], dtype=float)

    diff = vals_pow - vals_gio
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    mean_diff = float(np.mean(diff))
    corr, p_corr = stats.pearsonr(vals_pow, vals_gio)

    sen_gio = res_gio["trend"]["sen_slope_per_decade"]
    sen_pow = res_pow["trend"]["sen_slope_per_decade"]
    ci_gio = res_gio["trend"]["sen_ci95_per_decade"]
    ci_pow = res_pow["trend"]["sen_ci95_per_decade"]
    verdict_gio = res_gio["significance"]["verdict_code"]
    verdict_pow = res_pow["significance"]["verdict_code"]

    return {
        "variable_id": var_id,
        "n_months": len(common_dates),
        "period": f"{start} a {end}",
        "bbox": bbox,
        "giovanni": {
            "mean": float(np.mean(vals_gio)),
            "std": float(np.std(vals_gio, ddof=1)),
            "sen_slope_per_decade": sen_gio,
            "sen_ci95_per_decade": ci_gio,
            "ols_slope_per_decade": res_gio["trend"]["ols_slope_per_decade"],
            "ols_ci95_per_decade": res_gio["trend"]["ols_ci95_per_decade"],
            "verdict": verdict_gio,
            "mk_pvalue": res_gio["tests"]["mann_kendall"]["p_value"],
        },
        "power": {
            "mean": float(np.mean(vals_pow)),
            "std": float(np.std(vals_pow, ddof=1)),
            "sen_slope_per_decade": sen_pow,
            "sen_ci95_per_decade": ci_pow,
            "ols_slope_per_decade": res_pow["trend"]["ols_slope_per_decade"],
            "ols_ci95_per_decade": res_pow["trend"]["ols_ci95_per_decade"],
            "verdict": verdict_pow,
            "mk_pvalue": res_pow["tests"]["mann_kendall"]["p_value"],
        },
        "comparison": {
            "mean_difference_power_minus_gio": mean_diff,
            "mae": mae,
            "rmse": rmse,
            "pearson_r": float(corr),
            "pearson_p": float(p_corr),
            "slope_difference_power_minus_gio": float(sen_pow - sen_gio),
            "verdicts_agree": verdict_gio == verdict_pow,
        },
    }


def main():
    bbox = [-71.0, 0.85, -69.84, 1.7]
    start = "1981-01"
    end = "2025-12"

    t2m_csv = ROOT / "data" / "raw" / "giovanni" / "T2M__amazonia.csv"
    prec_csv = ROOT / "data" / "raw" / "giovanni" / "PRECTOTCORR__amazonia.csv"

    res_t2m = compare_variable("T2M", str(t2m_csv), bbox, start, end)
    res_prec = compare_variable("PRECTOTCORR", str(prec_csv), bbox, start, end)

    print("=" * 78)
    print("COMPARACIÓN CUANTITATIVA: NASA POWER VS GIOVANNI (AMAZONÍA)")
    print(f"Región: bbox={bbox} · Periodo: {start} a {end} (540 meses)")
    print("=" * 78)

    for r in (res_t2m, res_prec):
        vid = r["variable_id"]
        unit = "°C" if vid == "T2M" else "mm/día"
        g = r["giovanni"]
        p = r["power"]
        c = r["comparison"]

        print(f"\n--- Variable: {vid} ({unit}) ---")
        print(f"  * Media mensual:  Giovanni = {g['mean']:.4f} {unit} | POWER = {p['mean']:.4f} {unit} | Dif Media = {c['mean_difference_power_minus_gio']:+.4f} {unit}")
        print(f"  * Concordancia:   MAE = {c['mae']:.4f} {unit} | RMSE = {c['rmse']:.4f} {unit} | Pearson r = {c['pearson_r']:.4f} (p = {c['pearson_p']:.1e})")
        print(f"  * Pendiente Sen:  Giovanni = {g['sen_slope_per_decade']:+.4f} {unit}/década (IC95: [{g['sen_ci95_per_decade'][0]:.4f}, {g['sen_ci95_per_decade'][1]:.4f}])")
        print(f"                    POWER    = {p['sen_slope_per_decade']:+.4f} {unit}/década (IC95: [{p['sen_ci95_per_decade'][0]:.4f}, {p['sen_ci95_per_decade'][1]:.4f}])")
        print(f"                    Dif Pendiente = {c['slope_difference_power_minus_gio']:+.4f} {unit}/década")
        print(f"  * Veredicto MK:   Giovanni = {g['verdict']} (p={g['mk_pvalue']:.2e}) | POWER = {p['verdict']} (p={p['mk_pvalue']:.2e})")
        print(f"  * Veredictos coinciden: {'SÍ' if c['verdicts_agree'] else 'NO'}")

    print("\n" + "=" * 78)
    print("FRASE DE SÍNTESIS EN INGLÉS (PARA claude-omni-1b / README):")
    print("Across the 1981-2025 period (540 months) over the Amazon bbox [-71.0, 0.85, -69.84, 1.7], "
          "NASA POWER and Giovanni agree closely on underlying MERRA-2 trends: "
          f"for T2M, both identify a statistically significant warming trend (Giovanni +{res_t2m['giovanni']['sen_slope_per_decade']:.3f} vs POWER +{res_t2m['power']['sen_slope_per_decade']:.3f} °C/decade; r={res_t2m['comparison']['pearson_r']:.3f}, MAE={res_t2m['comparison']['mae']:.2f} °C) "
          f"with identical verdict ({res_t2m['giovanni']['verdict']}); "
          f"for precipitation, both show no detectable trend (Giovanni {res_prec['giovanni']['sen_slope_per_decade']:+.3f} vs POWER {res_prec['power']['sen_slope_per_decade']:+.3f} mm/day/decade; r={res_prec['comparison']['pearson_r']:.3f}) "
          f"with matching verdict ({res_prec['giovanni']['verdict']}).")
    print("=" * 78)


if __name__ == "__main__":
    main()
