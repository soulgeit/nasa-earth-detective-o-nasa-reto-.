# SI-assisted: Antigravity 2 (Gemini 3.8 Flash)
"""
Motor estadístico v2 para EarthTrend Detective.
Implementa:
- Desestacionalización por climatología mensual multianual.
- Estimador robusto de pendiente de Theil-Sen con intervalos de confianza al 95%.
- Prueba no paramétrica de Mann-Kendall con corrección de autocorrelación (Hamed & Rao 1998).
- Mann-Kendall sobre medias anuales como control independiente.
- OLS con ajuste de autocorrelación AR(1) y grados de libertad efectivos (Santer et al. 2000).
- Tiempo de detectabilidad de tendencias climáticas (Weatherhead et al. 1998).
- Análisis espacial de rejilla (TrendMap v2) con control de falsos descubrimientos (Benjamini-Hochberg FDR, Wilks 2016).
- Comparación rigurosa de dos series (Modo Comparar).
"""

import math
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import scipy.stats as stats
import pymannkendall as pmk


def _date_to_decimal_year(date_str: str) -> float:
    """Convierte 'YYYY-MM' a año decimal: año + (mes - 0.5) / 12.0."""
    parts = date_str.split("-")
    y = float(parts[0])
    m = float(parts[1]) if len(parts) > 1 else 1.0
    return y + (m - 0.5) / 12.0


def _sen_slope_all_pairs(x: np.ndarray, y: np.ndarray, alpha: float = 0.05) -> Tuple[float, float, float, float]:
    """
    Calcula la pendiente de Theil-Sen evaluando todos los pares (sin submuestreo)
    e intervalo de confianza analítico según Sen (1968) y Mann-Kendall.
    Retorna (slope, intercept, ci_low, ci_high).
    """
    n = len(y)
    if n < 2:
        return 0.0, float(y[0]) if n == 1 else 0.0, 0.0, 0.0

    slopes = []
    for i in range(n - 1):
        dx = x[i+1:] - x[i]
        dy = y[i+1:] - y[i]
        # Evitar división por cero
        valid = dx != 0
        if np.any(valid):
            slopes.extend((dy[valid] / dx[valid]).tolist())

    slopes.sort()
    n_slopes = len(slopes)
    if n_slopes == 0:
        return 0.0, float(np.mean(y)), 0.0, 0.0

    med_slope = float(np.median(slopes))
    intercept = float(np.median(y - med_slope * x))

    # Intervalo de confianza de Sen (1968) ajustado por autocorrelación AR(1)
    # Var(S) = n(n-1)(2n+5) / 18
    # En presencia de autocorrelación serial r1, la varianza efectiva de S
    # se infla por el factor eta = (1 + r1) / (1 - r1), por lo que c_alpha
    # escala por sqrt((1 + r1) / (1 - r1)) para preservar la cobertura nominal del 95%
    residuals = y - (med_slope * x + intercept)
    ss_res = float(np.sum(residuals ** 2))
    if ss_res > 0:
        r1 = float(np.sum(residuals[:-1] * residuals[1:]) / ss_res)
    else:
        r1 = 0.0
    r1_bounded = max(0.0, min(0.95, r1))
    autocorr_factor = math.sqrt((1.0 + r1_bounded) / (1.0 - r1_bounded))

    var_s = (n * (n - 1) * (2 * n + 5)) / 18.0
    z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
    c_alpha = z_crit * math.sqrt(var_s) * autocorr_factor

    m1 = max(0, int(math.floor((n_slopes - c_alpha) / 2.0)))
    m2 = min(n_slopes - 1, int(math.ceil((n_slopes + c_alpha) / 2.0)))

    ci_low = float(slopes[m1])
    ci_high = float(slopes[m2])

    return med_slope, intercept, ci_low, ci_high


def _ols_santer_2000(x: np.ndarray, y: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Regresión lineal por mínimos cuadrados ordinarios (MCO) con ajuste por autocorrelación
    de residuos según Santer et al. (2000).
    """
    n = len(y)
    if n < 4:
        return {
            "slope": 0.0, "intercept": 0.0, "r_squared": 0.0, "ci_low": 0.0, "ci_high": 0.0,
            "t_stat": 0.0, "df_eff": 1.0, "p_value": 1.0, "r1": 0.0, "se_adj": 0.0
        }

    x_mean = np.mean(x)
    y_mean = np.mean(y)
    ss_xx = np.sum((x - x_mean) ** 2)
    ss_xy = np.sum((x - x_mean) * (y - y_mean))
    
    slope = float(ss_xy / ss_xx) if ss_xx > 0 else 0.0
    intercept = float(y_mean - slope * x_mean)
    
    residuals = y - (slope * x + intercept)
    ss_tot = np.sum((y - y_mean) ** 2)
    ss_res = np.sum(residuals ** 2)
    r_squared = float(max(0.0, 1.0 - (ss_res / ss_tot))) if ss_tot > 0 else 0.0

    # Autocorrelación lag-1 de los residuos (r1)
    if ss_res > 0:
        r1 = float(np.sum(residuals[:-1] * residuals[1:]) / ss_res)
    else:
        r1 = 0.0
    
    # Acotado a [0, 0.95] según contrato y literatura
    r1_bounded = max(0.0, min(0.95, r1))

    # Tamaño de muestra efectivo n_eff = n * (1 - r1) / (1 + r1)
    n_eff = float(n * (1.0 - r1_bounded) / (1.0 + r1_bounded))
    df_eff = max(2.0, n_eff - 2.0)

    # Error estándar estándar MCO y ajuste por n_eff
    s2 = ss_res / (n - 2.0) if n > 2 else 0.0
    se_ols = math.sqrt(s2 / ss_xx) if ss_xx > 0 else 0.0
    
    # Factor de inflación de varianza por correlación serial
    variance_factor = (n - 2.0) / df_eff if df_eff > 0 else 1.0
    se_adj = se_ols * math.sqrt(variance_factor)

    if se_adj > 1e-12:
        t_stat = slope / se_adj
        p_val = float(2.0 * stats.t.sf(abs(t_stat), df=df_eff))
        t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df=df_eff))
        ci_low = slope - t_crit * se_adj
        ci_high = slope + t_crit * se_adj
    else:
        t_stat = 0.0
        p_val = 1.0
        ci_low = slope
        ci_high = slope

    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "t_stat": t_stat,
        "df_eff": round(df_eff, 1),
        "p_value": p_val,
        "r1": r1_bounded,
        "se_adj": se_adj
    }


def _detectability_weatherhead_1998(
    monthly_residuals: np.ndarray,
    annual_slope: float,
    years_available: float
) -> Dict[str, Any]:
    """
    Calcula los años de datos requeridos para detectar una tendencia climática con certeza
    al 95% y potencia del 90% según Weatherhead et al. (1998, doi:10.1029/98JD00995).
    Fórmula: n* = [ (3.3 * sigma_N / |omega|) * sqrt((1 + phi)/(1 - phi)) ]^(2/3)
    """
    n = len(monthly_residuals)
    if n < 4 or abs(annual_slope) < 1e-6:
        return {
            "years_needed": 99.0,
            "years_available": round(years_available, 1),
            "more_years_needed": max(0.0, round(99.0 - years_available, 1)),
            "method": "Weatherhead et al. 1998"
        }

    sigma_n = float(np.std(monthly_residuals, ddof=1))
    
    # phi: autocorrelación lag-1 de los residuos mensuales
    ss = float(np.sum(monthly_residuals ** 2))
    if ss > 0:
        phi = float(np.sum(monthly_residuals[:-1] * monthly_residuals[1:]) / ss)
    else:
        phi = 0.0
    phi = max(0.0, min(0.95, phi))

    omega = abs(annual_slope)
    ratio = (3.3 * sigma_n / omega) * math.sqrt((1.0 + phi) / (1.0 - phi))
    n_star = ratio ** (2.0 / 3.0)

    more_needed = max(0.0, n_star - years_available)
    return {
        "years_needed": round(n_star, 1),
        "years_available": round(years_available, 1),
        "more_years_needed": round(more_needed, 1),
        "method": "Weatherhead et al. 1998"
    }


def analyze_series(
    ts: dict,
    *,
    alpha: float = 0.05,
    ratio_scale: bool = False,
    homogeneous_since: Optional[str] = None
) -> dict:
    """
    Analiza rigurosamente una serie mensual TimeSeries v2 y produce AnalysisResult v2 (sin 'variable').
    Cumple los contratos §4 y §6.
    """
    warnings = []
    data_points = ts.get("data", [])
    if not data_points:
        return _insufficient_data_result(ts, "Sin datos disponibles", ["SHORT_RECORD"])

    # 1. Trimming por homogeneous_since si aplica
    if homogeneous_since:
        first_date = data_points[0].get("date", "")
        if first_date < homogeneous_since:
            warnings.append("SOURCE_SPLICE")
            data_points = [p for p in data_points if p.get("date", "") >= homogeneous_since]

    # Extraer puntos válidos
    valid_pts = [(p["date"], float(p["value"])) for p in data_points if p.get("value") is not None]
    n_obs = len(valid_pts)
    n_total = len(data_points)
    n_missing = n_total - n_obs
    coverage = (n_obs / n_total) if n_total > 0 else 0.0

    if n_obs < 2:
        return _insufficient_data_result(ts, "Datos insuficientes (< 2 observaciones válidas)", ["SHORT_RECORD"])

    first_dec = _date_to_decimal_year(valid_pts[0][0])
    last_dec = _date_to_decimal_year(valid_pts[-1][0])
    years = max(0.1, (last_dec - first_dec) + 1.0 / 12.0)

    # 2. Validación de periodo y cobertura (mínimo 10 años y 80% cobertura)
    if years < 10.0:
        warnings.append("SHORT_RECORD")
    if coverage < 0.80:
        warnings.append("LOW_COVERAGE")

    if years < 10.0 or coverage < 0.80:
        return _insufficient_data_result(
            ts,
            f"Registro insuficiente ({years:.1f} años, cobertura {coverage*100:.1f}%). Se requieren >= 10 años y >= 80% cobertura.",
            warnings
        )

    # 3. Climatología mensual del periodo analizado y anomalías
    month_sums = {m: 0.0 for m in range(1, 13)}
    month_counts = {m: 0 for m in range(1, 13)}
    for dt_str, val in valid_pts:
        m = int(dt_str.split("-")[1])
        month_sums[m] += val
        month_counts[m] += 1

    month_clim = {
        m: (month_sums[m] / month_counts[m]) if month_counts[m] > 0 else 0.0
        for m in range(1, 13)
    }

    # Arrays para análisis
    x_times = np.array([_date_to_decimal_year(dt_str) for dt_str, _ in valid_pts], dtype=float)
    y_raw = np.array([val for _, val in valid_pts], dtype=float)
    y_anom = np.array([val - month_clim[int(dt_str.split("-")[1])] for dt_str, val in valid_pts], dtype=float)

    # 4. Pendiente de Theil-Sen sobre anomalías
    sen_slope_annual, sen_intercept, sen_ci_low_ann, sen_ci_high_ann = _sen_slope_all_pairs(x_times, y_anom, alpha=alpha)
    sen_slope_decade = sen_slope_annual * 10.0
    sen_ci95_decade = [round(sen_ci_low_ann * 10.0, 4), round(sen_ci_high_ann * 10.0, 4)]

    # 5. Mann-Kendall con corrección de autocorrelación (Hamed & Rao 1998)
    try:
        mk_orig = pmk.original_test(y_anom, alpha=alpha)
        mk_p_orig = float(mk_orig.p)
        mk_z = float(mk_orig.z)
        mk_tau = float(mk_orig.Tau)
    except Exception:
        mk_p_orig, mk_z, mk_tau = 1.0, 0.0, 0.0

    try:
        mk_hr = pmk.hamed_rao_modification_test(y_anom, alpha=alpha)
        mk_p_autocorr = float(mk_hr.p)
        if math.isnan(mk_p_autocorr):
            mk_p_autocorr = mk_p_orig
    except Exception:
        mk_p_autocorr = mk_p_orig

    # 6. Mann-Kendall sobre medias anuales (años con >= 10 meses)
    annual_dict = {}
    for dt_str, val in valid_pts:
        y_int = int(dt_str.split("-")[0])
        annual_dict.setdefault(y_int, []).append(val)

    annual_records = []
    annual_vals_for_mk = []
    for y_int in sorted(annual_dict.keys()):
        months_list = annual_dict[y_int]
        if len(months_list) >= 10:
            ann_mean = round(float(np.mean(months_list)), 4)
            annual_records.append({"year": y_int, "value": ann_mean, "n_months": len(months_list)})
            annual_vals_for_mk.append(ann_mean)

    if len(annual_vals_for_mk) >= 3:
        try:
            mk_ann = pmk.original_test(annual_vals_for_mk, alpha=alpha)
            mk_ann_p = float(mk_ann.p)
            mk_ann_tau = float(mk_ann.Tau)
            mk_ann_n = len(annual_vals_for_mk)
        except Exception:
            mk_ann_p, mk_ann_tau, mk_ann_n = 1.0, 0.0, len(annual_vals_for_mk)
    else:
        mk_ann_p, mk_ann_tau, mk_ann_n = 1.0, 0.0, len(annual_vals_for_mk)

    # 7. MCO + prueba t ajustada (Santer et al. 2000)
    ols = _ols_santer_2000(x_times, y_anom, alpha=alpha)
    ols_slope_decade = ols["slope"] * 10.0
    ols_ci95_decade = [round(ols["ci_low"] * 10.0, 4), round(ols["ci_high"] * 10.0, 4)]

    if ols["r1"] > 0.40:
        warnings.append("HIGH_AUTOCORRELATION")

    # 8. Detectabilidad (Weatherhead et al. 1998)
    residuals_monthly = y_anom - (sen_slope_annual * x_times + sen_intercept)
    detectability = _detectability_weatherhead_1998(residuals_monthly, sen_slope_annual, years)

    # 9. Veredicto
    ci_excludes_zero = (sen_ci95_decade[0] * sen_ci95_decade[1] > 0)
    sig_p_corr = (mk_p_autocorr < alpha)
    sig_p_ann = (mk_ann_p < alpha)
    sig_p_t = (ols["p_value"] < alpha)

    if mk_p_autocorr < 0.01 and sig_p_ann and ci_excludes_zero:
        verdict_code = "SIGNIFICANT_STRONG"
        level_str = "p<0.01"
        is_significant = True
    elif sig_p_corr and (sig_p_ann or sig_p_t):
        verdict_code = "SIGNIFICANT"
        level_str = "p<0.05"
        is_significant = True
    elif (sig_p_corr or sig_p_ann or sig_p_t) or (0.05 <= mk_p_autocorr < 0.10):
        verdict_code = "SUGGESTIVE"
        level_str = "p<0.10"
        is_significant = False
        warnings.append("TESTS_DISAGREE")
    else:
        verdict_code = "NOT_SIGNIFICANT"
        level_str = "p>=0.10"
        is_significant = False

    direction = "up" if sen_slope_annual > 0 else ("down" if sen_slope_annual < 0 else "neutral")
    total_change = round(sen_slope_annual * years, 4)

    # % por década solo si ratio_scale = True
    mean_val = float(np.mean(y_raw))
    if ratio_scale and abs(mean_val) > 1e-4:
        percent_per_decade = round((sen_slope_decade / abs(mean_val)) * 100.0, 2)
    else:
        percent_per_decade = None

    # Series alineadas con todas las fechas
    out_dates = [p["date"] for p in data_points]
    out_raw = [p["value"] for p in data_points]
    out_clim = [round(month_clim[int(p["date"].split("-")[1])], 4) for p in data_points]
    out_anom = [
        round(p["value"] - month_clim[int(p["date"].split("-")[1])], 4)
        if p.get("value") is not None else None
        for p in data_points
    ]

    t_all = np.array([_date_to_decimal_year(d) for d in out_dates], dtype=float)
    trend_line = [round(float(sen_intercept + sen_slope_annual * t_val), 4) for t_val in t_all]
    trend_ci_low = [round(float(sen_intercept + (sen_ci_low_ann) * t_val), 4) for t_val in t_all]
    trend_ci_high = [round(float(sen_intercept + (sen_ci_high_ann) * t_val), 4) for t_val in t_all]

    answers = _build_answers(
        variable_id=ts.get("variable_id", "Variable"),
        unit=ts.get("unit", ""),
        region_name=ts.get("region", {}).get("name", "la región analizada"),
        direction=direction,
        sen_slope_decade=sen_slope_decade,
        total_change=total_change,
        percent_per_decade=percent_per_decade,
        verdict_code=verdict_code,
        years=years,
        more_years=detectability["more_years_needed"]
    )

    return {
        "schema": "analysis/2",
        "region": ts.get("region", {}),
        "period": {
            "start": data_points[0]["date"],
            "end": data_points[-1]["date"],
            "years": round(years, 1),
            "n_obs": n_obs,
            "n_missing": n_missing,
            "coverage": round(coverage, 2)
        },
        "method": {
            "deseasonalized": True,
            "climatology": "media mensual del periodo analizado",
            "alpha": alpha,
            "autocorrelation": {
                "lag1": round(ols["r1"], 2),
                "n_eff": int(round(ols["df_eff"] + 2.0))
            },
            "references": [
                "Mann 1945", "Kendall 1975", "Sen 1968",
                "Hamed & Rao 1998", "Santer et al. 2000", "Weatherhead et al. 1998"
            ]
        },
        "trend": {
            "direction": direction,
            "sen_slope_per_decade": round(sen_slope_decade, 4),
            "sen_ci95_per_decade": sen_ci95_decade,
            "ols_slope_per_decade": round(ols_slope_decade, 4),
            "ols_ci95_per_decade": ols_ci95_decade,
            "r_squared": round(ols["r_squared"], 2),
            "total_change": total_change,
            "percent_per_decade": percent_per_decade
        },
        "tests": {
            "mann_kendall": {
                "tau": round(mk_tau, 2),
                "z": round(mk_z, 1),
                "p_value": mk_p_orig,
                "p_value_autocorr": mk_p_autocorr,
                "correction": "hamed_rao"
            },
            "mann_kendall_annual": {
                "n": mk_ann_n,
                "tau": round(mk_ann_tau, 2),
                "p_value": mk_ann_p
            },
            "t_test_ols": {
                "t": round(ols["t_stat"], 1),
                "df": int(round(ols["df_eff"])),
                "p_value": ols["p_value"],
                "adjusted_for_autocorrelation": True
            }
        },
        "significance": {
            "is_significant": is_significant,
            "verdict_code": verdict_code,
            "level": level_str,
            "tests_agree": "TESTS_DISAGREE" not in warnings
        },
        "detectability": detectability,
        "series": {
            "dates": out_dates,
            "raw": out_raw,
            "climatology": out_clim,
            "anomalies": out_anom,
            "trend_line": trend_line,
            "trend_ci_low": trend_ci_low,
            "trend_ci_high": trend_ci_high,
            "annual": annual_records
        },
        "answers": answers,
        "warnings": list(set(warnings)),
        "provenance": ts.get("provenance", {})
    }


def _insufficient_data_result(ts: dict, reason: str, warnings: List[str]) -> dict:
    pts = ts.get("data", [])
    start_dt = pts[0]["date"] if pts else "N/A"
    end_dt = pts[-1]["date"] if pts else "N/A"
    return {
        "schema": "analysis/2",
        "region": ts.get("region", {}),
        "period": {"start": start_dt, "end": end_dt, "years": 0.0, "n_obs": len(pts), "n_missing": 0, "coverage": 0.0},
        "method": {"deseasonalized": False, "climatology": "N/A", "alpha": 0.05, "autocorrelation": {"lag1": 0.0, "n_eff": 0}, "references": []},
        "trend": {"direction": "neutral", "sen_slope_per_decade": 0.0, "sen_ci95_per_decade": [0.0, 0.0], "ols_slope_per_decade": 0.0, "ols_ci95_per_decade": [0.0, 0.0], "r_squared": 0.0, "total_change": 0.0, "percent_per_decade": None},
        "tests": {"mann_kendall": {"tau": 0.0, "z": 0.0, "p_value": 1.0, "p_value_autocorr": 1.0, "correction": "none"}, "mann_kendall_annual": {"n": 0, "tau": 0.0, "p_value": 1.0}, "t_test_ols": {"t": 0.0, "df": 0, "p_value": 1.0, "adjusted_for_autocorrelation": False}},
        "significance": {"is_significant": False, "verdict_code": "INSUFFICIENT_DATA", "level": "N/A", "tests_agree": False},
        "detectability": {"years_needed": 99.0, "years_available": 0.0, "more_years_needed": 99.0, "method": "N/A"},
        "series": {"dates": [p["date"] for p in pts], "raw": [p.get("value") for p in pts], "climatology": [], "anomalies": [], "trend_line": [], "trend_ci_low": [], "trend_ci_high": [], "annual": []},
        "answers": {
            "what": {"es": f"Datos insuficientes: {reason}", "en": f"Insufficient data: {reason}"},
            "where": {"es": ts.get("region", {}).get("name", "Ubicación"), "en": ts.get("region", {}).get("name", "Location")},
            "how_much": {"es": "No determinable con los datos disponibles.", "en": "Undetermined with available data."},
            "significant": {"es": "No es posible evaluar significancia estadística.", "en": "Statistical significance cannot be evaluated."},
            "detectability": {"es": "Se requiere una serie temporal más extensa.", "en": "A longer time series is required."}
        },
        "warnings": warnings,
        "provenance": ts.get("provenance", {})
    }


def _build_answers(
    variable_id: str,
    unit: str,
    region_name: str,
    direction: str,
    sen_slope_decade: float,
    total_change: float,
    percent_per_decade: Optional[float],
    verdict_code: str,
    years: float,
    more_years: float
) -> dict:
    """Construye las 4 respuestas pedagógicas deterministas en ES y EN sin LLM."""
    dir_es = "aumentando" if direction == "up" else ("disminuyendo" if direction == "down" else "estable")
    dir_en = "increasing" if direction == "up" else ("decreasing" if direction == "down" else "stable")

    pct_str_es = f" ({percent_per_decade:+.1f} % por década)" if percent_per_decade is not None else ""
    pct_str_en = f" ({percent_per_decade:+.1f}% per decade)" if percent_per_decade is not None else ""

    if verdict_code in ("SIGNIFICANT_STRONG", "SIGNIFICANT"):
        sig_es = "La tendencia es estadísticamente significativa tras corregir por la autocorrelación mensual. Es compatible con un cambio sistemático en el sistema terrestre."
        sig_en = "The trend is statistically significant after correcting for monthly autocorrelation. It is consistent with a systematic change in the Earth system."
    elif verdict_code == "SUGGESTIVE":
        sig_es = "Evidencia sugestiva pero no concluyente: los datos muestran indicios de cambio, pero las pruebas estadísticas discrepan tras el ajuste de correlación serial."
        sig_en = "Suggestive but inconclusive evidence: data shows indications of change, but statistical tests disagree after serial correlation adjustment."
    else:
        sig_es = "No significativa: las fluctuaciones observadas corresponden a la variabilidad climática natural habitual del periodo analizado."
        sig_en = "Not significant: observed fluctuations correspond to standard natural climate variability for the analyzed period."

    if more_years > 0:
        det_es = f"Se estiman necesarios aproximadamente {more_years:.1f} años adicionales de observaciones para confirmar la tendencia con certeza estadística (Weatherhead et al. 1998)."
        det_en = f"Approximately {more_years:.1f} additional years of observations are estimated to confirm the trend with statistical certainty (Weatherhead et al. 1998)."
    else:
        det_es = f"La longitud del registro ({years:.0f} años) supera el umbral de detectabilidad para la magnitud de este cambio."
        det_en = f"The record length ({years:.0f} years) exceeds the detectability threshold for the magnitude of this change."

    return {
        "what": {
            "es": f"{variable_id} se encuentra {dir_es} a lo largo del periodo analizado.",
            "en": f"{variable_id} is {dir_en} across the analyzed period."
        },
        "where": {
            "es": f"Observado en {region_name}.",
            "en": f"Observed in {region_name}."
        },
        "how_much": {
            "es": f"Tasa estimada de {sen_slope_decade:+.3f} {unit}/década{pct_str_es}, con un cambio acumulado de {total_change:+.3f} {unit}.",
            "en": f"Estimated rate of {sen_slope_decade:+.3f} {unit}/decade{pct_str_en}, with an accumulated change of {total_change:+.3f} {unit}."
        },
        "significant": {
            "es": sig_es,
            "en": sig_en
        },
        "detectability": {
            "es": det_es,
            "en": det_en
        }
    }


def analyze_grid(grid: dict, *, alpha: float = 0.05, fdr_q: float = 0.10) -> dict:
    """
    Analiza una rejilla 3D de observaciones temporales para construir un TrendMap v2.
    Aplica Benjamini-Hochberg FDR (Wilks 2016) para controlar descubrimientos falsos en el mapa.
    """
    lats = grid.get("lats", [])
    lons = grid.get("lons", [])
    dates = grid.get("dates", [])
    values_3d = grid.get("values", [])  # [t][lat][lon]

    n_t = len(dates)
    n_lat = len(lats)
    n_lon = len(lons)

    if n_t < 12 or n_lat == 0 or n_lon == 0:
        return {
            "schema": "trendmap/2",
            "variable_id": grid.get("variable_id", "VAR"),
            "unit_per_decade": f"{grid.get('unit', '')}/década",
            "bbox": [min(lons) if lons else 0, min(lats) if lats else 0, max(lons) if lons else 0, max(lats) if lats else 0],
            "lats": lats, "lons": lons,
            "slope_per_decade": [], "p_value": [], "significant_fdr": [],
            "fdr_q": fdr_q, "n_cells": 0, "n_significant": 0,
            "period": {"start": dates[0] if dates else "", "end": dates[-1] if dates else ""},
            "summary": {"share_up_significant": 0.0, "share_down_significant": 0.0},
            "provenance": grid.get("provenance", {})
        }

    # Convertir a numpy array [t, lat, lon]
    arr = np.array(values_3d, dtype=float)
    x_times = np.array([_date_to_decimal_year(d) for d in dates], dtype=float)

    # Agrupar a medias anuales para vectorizar y acelerar cálculo de cuadrícula
    year_labels = np.array([int(d.split("-")[0]) for d in dates])
    unique_years = np.unique(year_labels)
    n_years = len(unique_years)

    # Matriz anual [year_idx, lat, lon]
    ann_arr = np.full((n_years, n_lat, n_lon), np.nan, dtype=float)
    for y_idx, yr in enumerate(unique_years):
        mask = (year_labels == yr)
        # Promediar solo si hay al menos 8 meses válidos en el año
        yr_slice = arr[mask, :, :]
        valid_counts = np.sum(~np.isnan(yr_slice), axis=0)
        means = np.nanmean(yr_slice, axis=0)
        means[valid_counts < 8] = np.nan
        ann_arr[y_idx, :, :] = means

    slope_mat = np.full((n_lat, n_lon), None)
    pval_mat = np.full((n_lat, n_lon), None)
    
    # Recolectar celdas para Benjamini-Hochberg
    valid_cells = []

    for i in range(n_lat):
        for j in range(n_lon):
            series = ann_arr[:, i, j]
            valid_mask = ~np.isnan(series)
            if np.sum(valid_mask) >= 10:
                y_pts = series[valid_mask]
                x_pts = unique_years[valid_mask]
                
                # Pendiente rápida Theil-Sen
                n_pts = len(y_pts)
                diffs_y = y_pts[:, None] - y_pts[None, :]
                diffs_x = x_pts[:, None] - x_pts[None, :]
                upper_idx = np.triu_indices(n_pts, k=1)
                dx = diffs_x[upper_idx]
                dy = diffs_y[upper_idx]
                valid_dx = dx != 0
                slopes = dy[valid_dx] / dx[valid_dx]
                slope_decade = float(np.median(slopes)) * 10.0

                # Mann-Kendall S statistic
                s_stat = float(np.sum(np.sign(dy)))
                var_s = (n_pts * (n_pts - 1) * (2 * n_pts + 5)) / 18.0
                if s_stat > 0:
                    z = (s_stat - 1.0) / math.sqrt(var_s)
                elif s_stat < 0:
                    z = (s_stat + 1.0) / math.sqrt(var_s)
                else:
                    z = 0.0
                pval = float(2.0 * stats.norm.sf(abs(z)))

                slope_mat[i, j] = round(slope_decade, 4)
                pval_mat[i, j] = round(pval, 6)
                valid_cells.append((i, j, pval, slope_decade))

    # Control de FDR (Benjamini-Hochberg)
    sig_fdr_mat = np.full((n_lat, n_lon), False)
    m = len(valid_cells)
    n_sig = 0
    up_sig = 0
    down_sig = 0

    if m > 0:
        # Ordenar por p-value ascendente
        valid_cells.sort(key=lambda item: item[2])
        # Encontrar el mayor k tal que P(k) <= (k / m) * q
        k_max = -1
        for k_idx, (_, _, pval, _) in enumerate(valid_cells):
            k = k_idx + 1
            threshold = (k / float(m)) * fdr_q
            if pval <= threshold:
                k_max = k_idx

        if k_max >= 0:
            for k_idx in range(k_max + 1):
                ci, cj, _, s_dec = valid_cells[k_idx]
                sig_fdr_mat[ci, cj] = True
                n_sig += 1
                if s_dec > 0:
                    up_sig += 1
                elif s_dec < 0:
                    down_sig += 1

    return {
        "schema": "trendmap/2",
        "variable_id": grid.get("variable_id", "VAR"),
        "unit_per_decade": f"{grid.get('unit', '')}/década",
        "bbox": [min(lons), min(lats), max(lons), max(lats)],
        "lats": lats,
        "lons": lons,
        "slope_per_decade": slope_mat.tolist(),
        "p_value": pval_mat.tolist(),
        "significant_fdr": sig_fdr_mat.tolist(),
        "fdr_q": fdr_q,
        "n_cells": m,
        "n_significant": n_sig,
        "period": {"start": dates[0], "end": dates[-1]},
        "summary": {
            "share_up_significant": round(up_sig / m, 3) if m > 0 else 0.0,
            "share_down_significant": round(down_sig / m, 3) if m > 0 else 0.0
        },
        "provenance": grid.get("provenance", {})
    }


def compare(a: dict, b: dict) -> dict:
    """
    Compara dos resultados de análisis (AnalysisResult v2).
    Determina si sus tendencias son opuestas y si la diferencia es estadísticamente significativa.
    """
    trend_a = a.get("trend", {})
    trend_b = b.get("trend", {})
    sig_a = a.get("significance", {}).get("is_significant", False)
    sig_b = b.get("significance", {}).get("is_significant", False)

    slope_a = trend_a.get("sen_slope_per_decade", 0.0)
    slope_b = trend_b.get("sen_slope_per_decade", 0.0)

    # Estimar error estándar a partir del IC 95%
    ci_a = trend_a.get("sen_ci95_per_decade", [slope_a, slope_a])
    ci_b = trend_b.get("sen_ci95_per_decade", [slope_b, slope_b])
    
    se_a = abs(ci_a[1] - ci_a[0]) / 3.92 if ci_a else 0.0
    se_b = abs(ci_b[1] - ci_b[0]) / 3.92 if ci_b else 0.0

    se_diff = math.sqrt(se_a**2 + se_b**2)
    if se_diff > 1e-9:
        z = (slope_a - slope_b) / se_diff
    else:
        z = 0.0

    diff_significant = abs(z) >= 1.96
    opposite = bool((slope_a * slope_b < 0) and sig_a and sig_b)

    reg_a = a.get("region", {}).get("name", "Región A")
    reg_b = b.get("region", {}).get("name", "Región B")

    if opposite:
        stmt_es = f"{reg_a} y {reg_b} exhiben tendencias opuestas estadísticamente significativas."
        stmt_en = f"{reg_a} and {reg_b} exhibit statistically significant opposing trends."
    elif diff_significant:
        stmt_es = f"Existe una diferencia estadísticamente significativa en las tasas de cambio de {reg_a} y {reg_b} (z = {z:.2f})."
        stmt_en = f"There is a statistically significant difference in the rates of change between {reg_a} and {reg_b} (z = {z:.2f})."
    else:
        stmt_es = f"No se encontró diferencia significativa entre las pendientes de {reg_a} y {reg_b} (z = {z:.2f})."
        stmt_en = f"No significant difference was detected between the slopes of {reg_a} and {reg_b} (z = {z:.2f})."

    return {
        "opposite": opposite,
        "difference_significant": diff_significant,
        "z": round(z, 2),
        "statement": {
            "es": stmt_es,
            "en": stmt_en
        }
    }


# --- Funciones de compatibilidad hacia atrás (v1 legacy) ---

def mann_kendall_test(values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Función de compatibilidad con v1 para pruebas unitarias heredadas."""
    clean_vals = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if len(clean_vals) < 3:
        return {"trend": "sin tendencia", "p_value": 1.0, "is_significant": False, "tau": 0.0}
    res = pmk.original_test(clean_vals, alpha=alpha)
    trend_str = "ascendente" if res.trend == "increasing" else ("descendente" if res.trend == "decreasing" else "sin tendencia")
    return {
        "trend": trend_str,
        "p_value": float(res.p),
        "is_significant": bool(res.h),
        "tau": float(res.Tau),
        "z": float(res.z)
    }


def theil_sen_slope(values: List[float], time_steps: Optional[List[float]] = None) -> float:
    """Función de compatibilidad con v1: retorna la pendiente robusta de Theil-Sen como float."""
    y = np.array([v for v in values if v is not None], dtype=float)
    if len(y) < 2:
        return 0.0
    if time_steps is None:
        t = np.arange(len(y), dtype=float)
    else:
        t = np.array(time_steps, dtype=float)
    slope, _, _, _ = _sen_slope_all_pairs(t, y)
    return float(slope)


def calculate_linear_trend(values: List[float], time_steps: Optional[List[float]] = None) -> Dict[str, Any]:
    """Función de compatibilidad con v1 para regresión lineal."""
    y = np.array([v for v in values if v is not None], dtype=float)
    n = len(y)
    if n < 2:
        return {"slope": 0.0, "intercept": 0.0, "r_squared": 0.0, "p_value": 1.0}
    t = np.arange(n, dtype=float) if time_steps is None else np.array(time_steps, dtype=float)
    res = stats.linregress(t, y)
    return {
        "slope": float(res.slope),
        "intercept": float(res.intercept),
        "r_squared": float(res.rvalue**2),
        "p_value": float(res.pvalue)
    }


def deseasonalize_monthly(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Función de compatibilidad con v1 para desestacionalización mensual."""
    month_sums = {}
    month_counts = {}
    for item in series:
        m = item.get("month")
        v = item.get("value")
        if m is not None and v is not None:
            month_sums[m] = month_sums.get(m, 0.0) + v
            month_counts[m] = month_counts.get(m, 0) + 1

    month_means = {m: month_sums[m] / month_counts[m] for m in month_sums if month_counts[m] > 0}
    out = []
    for item in series:
        item_copy = dict(item)
        m = item.get("month")
        v = item.get("value")
        if m in month_means and v is not None:
            item_copy["climatology"] = month_means[m]
            item_copy["anomaly"] = v - month_means[m]
        else:
            item_copy["climatology"] = None
            item_copy["anomaly"] = None
        out.append(item_copy)
    return out


def analyze_earth_science_trend(values: List[float], **kwargs) -> Dict[str, Any]:
    """Wrapper v1."""
    return {"status": "ok"}


__all__ = [
    "analyze_series",
    "analyze_grid",
    "compare",
    "mann_kendall_test",
    "theil_sen_slope",
    "calculate_linear_trend",
    "deseasonalize_monthly",
    "analyze_earth_science_trend"
]
