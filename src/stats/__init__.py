# Modulo estadístico para detección de tendencias en series temporales
# Motor v2: Mann-Kendall (corregido), Theil-Sen, OLS con IC 95%
from .trend_engine import (
    analyze,
    mann_kendall,
    theil_sen_slope,
    ols_with_ci,
    deseasonalize,
    consistent_rates,
)
