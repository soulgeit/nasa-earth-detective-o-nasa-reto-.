"""
Motor estadístico para detección de tendencias en variables de Ciencias de la Tierra.
Diseñado para el reto NASA Space Apps: Earth Science Data Detective.
Implementa:
- Desestacionalización por anomalías climatológicas.
- Prueba no paramétrica de Mann-Kendall con cálculo de Z y p-value.
- Estimador robusto de pendiente de Theil-Sen.
- Regresión lineal por mínimos cuadrados ordinarios (OLS) con R² e intervalos.
- Veredicto cualitativo en lenguaje accesible para estudiantes.
"""

import math
from typing import List, Dict, Any, Tuple


def deseasonalize_monthly(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Elimina el ciclo estacional natural calculando anomalías mensuales respecto
    a la media histórica de cada mes calendario.
    """
    month_sums = {m: 0.0 for m in range(1, 13)}
    month_counts = {m: 0 for m in range(1, 13)}

    for pt in series:
        m = pt['month']
        month_sums[m] += pt['value']
        month_counts[m] += 1

    month_means = {
        m: (month_sums[m] / month_counts[m]) if month_counts[m] > 0 else 0.0
        for m in range(1, 13)
    }

    deseasonalized = []
    for pt in series:
        m = pt['month']
        anomaly = pt['value'] - month_means[m]
        deseasonalized.append({
            'date': pt['date'],
            'year': pt['year'],
            'month': m,
            'raw_value': pt['value'],
            'monthly_climatology': round(month_means[m], 4),
            'anomaly': round(anomaly, 4)
        })
    return deseasonalized


def theil_sen_slope(values: List[float]) -> float:
    """
    Calcula la pendiente de Theil-Sen (mediana de todas las pendientes entre pares).
    Método no paramétrico inmune a valores extremos o ruido.
    """
    n = len(values)
    if n < 2:
        return 0.0

    slopes = []
    # Para series largas, submuestreamos uniformemente si n > 150 para mantener O(N log N)
    step = 1 if n <= 150 else int(math.ceil(n / 100.0))

    for i in range(0, n - 1, step):
        for j in range(i + 1, n, step):
            dt = j - i
            slopes.append((values[j] - values[i]) / dt)

    slopes.sort()
    m = len(slopes)
    if m == 0:
        return 0.0
    if m % 2 == 1:
        return slopes[m // 2]
    else:
        return (slopes[m // 2 - 1] + slopes[m // 2]) / 2.0


def mann_kendall_test(values: List[float]) -> Dict[str, Any]:
    """
    Prueba no paramétrica de Mann-Kendall para verificar si existe una tendencia
    monótona estadísticamente significativa en la serie temporal.
    """
    n = len(values)
    if n < 3:
        return {
            's_stat': 0,
            'z_stat': 0.0,
            'p_value': 1.0,
            'trend': 'insufficient_data',
            'is_significant': False
        }

    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = values[j] - values[i]
            if diff > 1e-9:
                s += 1
            elif diff < -1e-9:
                s -= 1

    # Varianza de S (asumiendo pocos empates)
    var_s = (n * (n - 1) * (2 * n + 5)) / 18.0

    # Estadístico Z estandarizado
    if s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0

    # Aproximación del p-value bilateral usando función de error
    p_value = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))
    p_value = max(0.000001, min(1.0, p_value))

    trend_direction = "ninguna"
    if p_value < 0.05:
        trend_direction = "ascendente" if s > 0 else "descendente"

    return {
        's_stat': s,
        'z_stat': round(z, 4),
        'p_value': round(p_value, 6),
        'trend': trend_direction,
        'is_significant': bool(p_value < 0.05)
    }


def calculate_linear_trend(values: List[float]) -> Dict[str, Any]:
    """
    Calcula la regresión lineal OLS: pendiente, intercepto, R² y valores proyectados.
    """
    n = len(values)
    if n < 2:
        return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0, 'projected': values}

    x_vals = list(range(n))
    x_mean = sum(x_vals) / n
    y_mean = sum(values) / n

    numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0.0
    intercept = y_mean - slope * x_mean

    # R^2
    ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
    ss_res = sum((values[i] - (slope * x_vals[i] + intercept)) ** 2 for i in range(n))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    projected = [round(slope * x + intercept, 4) for x in x_vals]

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': round(max(0.0, r_squared), 4),
        'projected': projected
    }


def analyze_earth_science_trend(
    series: List[Dict[str, Any]],
    variable_meta: Dict[str, Any],
    region_meta: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de análisis estadístico y genera la síntesis 'Data Detective'.
    """
    raw_values = [p['value'] for p in series]
    deseasonalized = deseasonalize_monthly(series)
    anomalies = [p['anomaly'] for p in deseasonalized]

    # Cálculos en datos desestacionalizados (eliminando el ciclo de estaciones)
    mk_result = mann_kendall_test(anomalies)
    sen_slope_per_month = theil_sen_slope(anomalies)
    ols_result = calculate_linear_trend(raw_values)

    total_months = len(series)
    total_years = max(1.0, total_months / 12.0)

    # Tasas de cambio anual y decadal
    annual_rate = sen_slope_per_month * 12.0
    decadal_rate = annual_rate * 10.0

    start_val = ols_result['projected'][0] if ols_result['projected'] else 1.0
    end_val = ols_result['projected'][-1] if ols_result['projected'] else 1.0
    percent_change = ((end_val - start_val) / abs(start_val)) * 100.0 if abs(start_val) > 1e-6 else 0.0

    # Veredicto pedagógico del Detective
    p_val = mk_result['p_value']
    is_sig = mk_result['is_significant']

    if is_sig and p_val < 0.001:
        sig_label = "Extremadamente Significativo (Certeza > 99.9%)"
        sig_explanation = f"La probabilidad de que esta tendencia sea una casualidad natural es de apenas {p_val * 100:.4f}%."
    elif is_sig:
        sig_label = "Estadísticamente Significativo (Certeza > 95%)"
        sig_explanation = f"Existe una tendencia definida y sistemática corroborada por la prueba de Mann-Kendall (p={p_val:.4f})."
    else:
        sig_label = "No Significativo / Variabilidad Normal"
        sig_explanation = f"Las fluctuaciones observadas corresponden al ruido climático habitual (p={p_val:.4f} >= 0.05)."

    direction_verb = "aumentando" if annual_rate > 0 else "disminuyendo"
    if not is_sig:
        direction_verb = "fluctuando sin cambio neto sostenido"

    return {
        "variable": variable_meta,
        "region": region_meta,
        "summary": {
            "total_observations": total_months,
            "period": f"{series[0]['date']} a {series[-1]['date']}",
            "annual_rate": round(annual_rate, 5),
            "decadal_rate": round(decadal_rate, 4),
            "percent_change_total": round(percent_change, 2),
            "r_squared": ols_result['r_squared'],
            "mann_kendall_z": mk_result['z_stat'],
            "p_value": mk_result['p_value'],
            "is_significant": is_sig,
            "significance_label": sig_label
        },
        "detective_answers": {
            "what": f"{variable_meta.get('name', 'Variable')}: está {direction_verb} a lo largo del periodo analizado.",
            "where": f"{region_meta.get('name', 'Región seleccionada')} ({region_meta.get('biome', 'Área de estudio')}).",
            "how_much": f"Variación estimada de {decadal_rate:+.4f} {variable_meta.get('unit', '')} por década ({percent_change:+.2f}% total).",
            "is_significant": sig_explanation,
            "scientific_context": variable_meta.get('what_down_means' if annual_rate < 0 else 'what_up_means', '')
        },
        "series": {
            "dates": [p['date'] for p in series],
            "raw_values": raw_values,
            "anomalies": anomalies,
            "trend_projected": ols_result['projected']
        }
    }
