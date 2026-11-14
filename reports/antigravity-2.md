# Reporte de Antigravity 2 — Motor Estadístico v2 (feature/stats)

## E1, E2, E3, E4 — LISTO (14-nov-2026 13:56)
Rama@commit: feature/stats

### Qué quedó:
1. **E1 — Motor Estadístico v2 (`src/stats/trend_engine.py`)**:
   - `analyze_series(ts, *, alpha=0.05, ratio_scale=False, homogeneous_since=None)` conforme a contratos §4 y §6.
   - Desestacionalización por climatología multianual mensual del periodo.
   - Pendiente de Theil-Sen evaluando todos los pares de anomalías con intervalo de confianza 95% ajustado por autocorrelación.
   - Mann-Kendall con corrección de varianza por correlación serial (Hamed & Rao 1998) retornando tanto $p$ original como $p_{\text{autocorr}}$.
   - Mann-Kendall independiente sobre medias anuales para años con $\ge 10$ meses.
   - Regresión MCO con prueba $t$ ajustada por $n_{\text{eff}}$ y autocorrelación $r_1$ de residuos (Santer et al. 2000).
   - Tiempo de detectabilidad climática $n^*$ (Weatherhead et al. 1998, doi:10.1029/98JD00995).
   - Determinación estricta de veredicto: `SIGNIFICANT_STRONG`, `SIGNIFICANT`, `SUGGESTIVE`, `NOT_SIGNIFICANT`, `INSUFFICIENT_DATA`.
   - Respuestas pedagógicas deterministas bilingües (ES / EN) y series de salida completas para graficación.
2. **E2 — Validación Científica Monte Carlo (`tests/stats/test_trend_engine.py`)**:
   - 300 simulaciones con pendiente conocida + AR(1) ($\phi = 0.5$): Cobertura del IC 95% de **95.7%** (meta: 90%–98%).
   - 300 simulaciones de ruido puro AR(1) ($\phi = 0.5$): Tasa de falsos positivos controlada al **5.0%** (sin corrección se disparaba a **24.7%**).
   - Contraste numérico exacto contra `scipy.stats` y `pymannkendall` sobre los datos reales de Lima.
   - Casos límite evaluados: empates, nulos intercalados, series cortas y series constantes.
3. **E3 — TrendMap v2 y Modo Comparar (`analyze_grid`, `compare`)**:
   - Rejilla espacial vectorizada con control de Tasa de Falsos Descubrimientos (FDR Benjamini-Hochberg, Wilks 2016, $q=0.10$).
   - Comparación bilateral con prueba de significancia de diferencia de pendientes y detección de tendencias opuestas.
4. **E4 — Documento de Validación (`docs/VALIDACION_ESTADISTICA.md`)**:
   - Resumen en español e inglés, fundamentación matemática, tabla comparativa de Monte Carlo y benchmark sobre Lima.

### Evidencia:
- Pruebas unitarias y simulaciones de Monte Carlo (`pytest tests/stats -q -s`):
  ```
  [E2 Monte Carlo] Cobertura del IC 95%: 95.7% (287/300)
  [E2 Falsos Positivos] Sin corrección: 24.7% | Con corrección del motor: 5.0%
  5 passed in 16.59s
  ```

### Próximos pasos:
- Fase 2 LoRA: En cuanto Hermes 2 termine `data/lora/`, iniciaremos el pipeline de entrenamiento del planificador (`src/ml/`).
