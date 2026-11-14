# Modulo estadístico para detección de tendencias en series temporales
from .trend_engine import (
    deseasonalize_monthly,
    calculate_linear_trend,
    mann_kendall_test,
    theil_sen_slope,
    analyze_earth_science_trend
)
