# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Pruebas científicas del motor estadístico v2 (E2).
Verifica:
1. Cobertura del IC 95% en 300 simulaciones con ruido AR(1) (phi = 0.5).
2. Tasa de falsos positivos en 300 simulaciones de ruido puro AR(1) (controlada <= 10% con corrección).
3. Contraste numérico frente a scipy y pymannkendall sobre la muestra real de Lima.
4. Casos límite: empates, nulos intercalados, serie corta, serie constante, pendiente negativa.
5. Grid con FDR y función compare.
"""

import json
import math
import numpy as np
import pytest
from pathlib import Path
import scipy.stats as stats
import pymannkendall as pmk

from src.stats.trend_engine import (
    analyze_series,
    analyze_grid,
    compare,
    _sen_slope_all_pairs,
    _ols_santer_2000
)


def _generate_ar1_series(n_years: int = 20, true_slope: float = 0.5, phi: float = 0.5, sigma: float = 1.0, seed: int = 42):
    """Genera serie mensual sintética con ruido AR(1) para validación en tests."""
    np.random.seed(seed)
    n_months = n_years * 12
    e = np.zeros(n_months)
    e[0] = np.random.normal(0, sigma)
    for t in range(1, n_months):
        e[t] = phi * e[t-1] + np.random.normal(0, sigma * math.sqrt(1 - phi**2))

    t_years = np.arange(n_months) / 12.0
    y = 10.0 + true_slope * t_years + e

    pts = []
    base_year = 2000
    for idx, val in enumerate(y):
        yr = base_year + idx // 12
        mo = (idx % 12) + 1
        pts.append({"date": f"{yr:04d}-{mo:02d}", "value": float(val)})

    return {
        "schema": "timeseries/2",
        "variable_id": "TEST_VAR",
        "unit": "units",
        "cadence": "monthly",
        "region": {"kind": "point", "name": "Synthetic Site", "lat": 0.0, "lon": 0.0, "bbox": None},
        "aggregation": "point",
        "data": pts,
        "provenance": {"kind": "fixture", "sha256": "mock"}
    }


def test_confidence_interval_coverage_monte_carlo():
    """300 simulaciones con pendiente conocida + AR(1) (phi=0.5) -> cobertura en 90%-98%."""
    true_slope_decade = 0.40  # 0.04 por año
    true_slope_annual = 0.04
    n_sims = 300
    contained_count = 0

    for i in range(n_sims):
        ts = _generate_ar1_series(n_years=25, true_slope=true_slope_annual, phi=0.5, sigma=1.2, seed=1000 + i)
        res = analyze_series(ts, alpha=0.05)
        ci = res["trend"]["sen_ci95_per_decade"]
        if ci[0] <= true_slope_decade <= ci[1]:
            contained_count += 1

    coverage_pct = (contained_count / n_sims) * 100.0
    print(f"\n[E2 Monte Carlo] Cobertura del IC 95%: {coverage_pct:.1f}% ({contained_count}/{n_sims})")
    assert 90.0 <= coverage_pct <= 98.0, f"Cobertura {coverage_pct}% fuera del rango esperado [90%, 98%]"


def test_false_positive_rate_monte_carlo():
    """300 simulaciones de ruido AR(1) puro sin tendencia -> falsos positivos <= 10% con corrección del motor."""
    n_sims = 300
    sig_with_correction = 0
    sig_without_correction = 0

    for i in range(n_sims):
        # true_slope = 0.0
        ts = _generate_ar1_series(n_years=25, true_slope=0.0, phi=0.5, sigma=1.0, seed=5000 + i)
        res = analyze_series(ts, alpha=0.05)

        # Con corrección integral del motor (is_significant)
        if res["significance"]["is_significant"]:
            sig_with_correction += 1

        # Sin corrección: prueba no paramétrica univariada sin ajuste por autocorrelación
        p_orig = res["tests"]["mann_kendall"]["p_value"]
        if p_orig < 0.05:
            sig_without_correction += 1

    rate_with = (sig_with_correction / n_sims) * 100.0
    rate_without = (sig_without_correction / n_sims) * 100.0
    print(f"\n[E2 Falsos Positivos] Sin corrección: {rate_without:.1f}% | Con corrección del motor: {rate_with:.1f}%")

    # Sin corrección, la tasa de falsos positivos se dispara por el ruido correlacionado
    # Con la corrección del motor, se mantiene estrictamente <= 10% (nominal 5%)
    assert rate_with <= 10.0, f"Falsos positivos con corrección ({rate_with}%) supera el 10%"
    assert rate_without > rate_with, "La corrección debe reducir significativamente la tasa de falsos positivos"


def test_contrast_against_real_lima_fixture():
    """Contrasta los cálculos contra scipy y pymannkendall usando la muestra real de Lima."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    lima_file = root_dir / "tests" / "fixtures" / "real" / "power_monthly_point_lima.json"
    assert lima_file.exists(), "Falta fixture real de Lima"

    with open(lima_file, "r", encoding="utf-8") as f:
        raw_json = json.load(f)

    p_dict = raw_json["properties"]["parameter"]["T2M"]
    pts = []
    for k in sorted(p_dict.keys()):
        if not k.endswith("13"):
            pts.append({"date": f"{k[:4]}-{k[4:]}", "value": float(p_dict[k])})

    ts = {
        "schema": "timeseries/2",
        "variable_id": "T2M",
        "unit": "°C",
        "cadence": "monthly",
        "region": {"kind": "point", "name": "Lima, Peru", "lat": -12.05, "lon": -77.03, "bbox": None},
        "aggregation": "point",
        "data": pts,
        "provenance": {"kind": "nasa_api", "source": "NASA POWER v2.10.0", "sha256": "mock"}
    }

    res = analyze_series(ts)

    # 1. Verificar veredicto
    assert res["significance"]["verdict_code"] == "SIGNIFICANT_STRONG"
    assert res["significance"]["is_significant"] is True
    assert res["trend"]["direction"] == "up"
    assert res["trend"]["sen_slope_per_decade"] > 0.0

    # 2. Contraste directo de Mann-Kendall con pymannkendall
    anoms = [a for a in res["series"]["anomalies"] if a is not None]
    direct_pmk = pmk.hamed_rao_modification_test(anoms)
    assert abs(res["tests"]["mann_kendall"]["p_value_autocorr"] - float(direct_pmk.p)) < 1e-5

    # 3. Contraste de Theil-Sen con scipy
    x_dec = np.array([float(d[:4]) + (float(d[5:7]) - 0.5) / 12.0 for d in res["series"]["dates"]])
    scipy_res = stats.theilslopes(anoms, x_dec)
    calc_annual = res["trend"]["sen_slope_per_decade"] / 10.0
    assert abs(calc_annual - scipy_res.slope) < 1e-4


def test_edge_cases():
    """Prueba empates, valores nulos, serie corta (<10 años) y serie constante."""
    # 1. Serie corta (<10 años) -> INSUFFICIENT_DATA
    short_ts = _generate_ar1_series(n_years=5, true_slope=0.2, seed=99)
    res_short = analyze_series(short_ts)
    assert res_short["significance"]["verdict_code"] == "INSUFFICIENT_DATA"
    assert "SHORT_RECORD" in res_short["warnings"]

    # 2. Serie constante -> slope = 0
    const_pts = [{"date": f"{y:04d}-{m:02d}", "value": 15.0} for y in range(2000, 2015) for m in range(1, 13)]
    const_ts = {
        "schema": "timeseries/2",
        "variable_id": "CONST",
        "unit": "m",
        "data": const_pts,
        "region": {"kind": "point"}
    }
    res_const = analyze_series(const_ts)
    assert res_const["trend"]["sen_slope_per_decade"] == 0.0
    assert res_const["significance"]["verdict_code"] == "NOT_SIGNIFICANT"

    # 3. Serie con empates y nulos intercalados
    pts_with_nulls = []
    for idx, p in enumerate(const_pts):
        v = p["value"] + (0.5 if idx % 2 == 0 else 0.0)
        # 10% de nulos
        if idx % 10 == 0:
            v = None
        pts_with_nulls.append({"date": p["date"], "value": v})
    nulls_ts = {
        "schema": "timeseries/2",
        "variable_id": "TIES_NULLS",
        "unit": "m",
        "data": pts_with_nulls,
        "region": {"kind": "point"}
    }
    res_nulls = analyze_series(nulls_ts)
    assert res_nulls["period"]["n_missing"] > 0
    assert res_nulls["period"]["coverage"] >= 0.80

    # 4. Pendiente negativa
    neg_ts = _generate_ar1_series(n_years=20, true_slope=-0.5, seed=123)
    res_neg = analyze_series(neg_ts)
    assert res_neg["trend"]["direction"] == "down"
    assert res_neg["trend"]["sen_slope_per_decade"] < 0.0


def test_grid_fdr_and_compare():
    """Prueba analyze_grid con Benjamini-Hochberg FDR y función compare."""
    # Rejilla sintética 3D
    n_years = 15
    dates = [f"{y:04d}-{m:02d}" for y in range(2000, 2000 + n_years) for m in range(1, 13)]
    lats = [-10.0, -9.5, -9.0]
    lons = [-75.0, -74.5, -74.0]
    
    # Celda (0,0) con fuerte tendencia al alza, celda (2,2) con tendencia a la baja, el resto ruido
    values_3d = []
    for t_idx, dt in enumerate(dates):
        t_yr = t_idx / 12.0
        mat = []
        for i in range(len(lats)):
            row = []
            for j in range(len(lons)):
                if i == 0 and j == 0:
                    val = 10.0 + 1.0 * t_yr
                elif i == 2 and j == 2:
                    val = 20.0 - 1.0 * t_yr
                else:
                    val = 15.0 + math.sin(t_yr) * 0.1
                row.append(val)
            mat.append(row)
        values_3d.append(mat)

    grid = {
        "variable_id": "T2M",
        "lats": lats,
        "lons": lons,
        "dates": dates,
        "values": values_3d,
        "unit": "°C",
        "provenance": {"kind": "fixture"}
    }

    tmap = analyze_grid(grid, fdr_q=0.10)
    assert tmap["schema"] == "trendmap/2"
    assert tmap["n_cells"] == 9
    assert tmap["n_significant"] >= 2
    # Celda (0,0) significativa FDR
    assert tmap["significant_fdr"][0][0] is True
    # Celda (2,2) significativa FDR
    assert tmap["significant_fdr"][2][2] is True

    # Test compare
    ts_up = _generate_ar1_series(n_years=25, true_slope=0.5, seed=1)
    ts_down = _generate_ar1_series(n_years=25, true_slope=-0.5, seed=2)
    a1 = analyze_series(ts_up)
    a2 = analyze_series(ts_down)
    comp = compare(a1, a2)

    assert comp["opposite"] is True
    assert comp["difference_significant"] is True
    assert "opuestas" in comp["statement"]["es"]
    assert "opposing" in comp["statement"]["en"]
