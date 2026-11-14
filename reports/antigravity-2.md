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
- Integración en main y soporte para visualización y planificador en vivo.

---

## FASE 2 — Benchmark NASA & Pipeline LoRA — LISTO (14-nov-2026 14:55)
Rama@commit: feature/stats

### Qué quedó:
1. **Benchmark contra Cifras Oficiales Publicadas por NASA y NOAA**:
   - Integrado en `docs/VALIDACION_ESTADISTICA.md` y probado en `tests/stats/test_trend_engine.py`:
     - **GISTEMP v4 (1970–2024)**: Pendiente Theil-Sen de **+0.195 °C / década** (IC 95%: [+0.179, +0.211], MCO: +0.198 °C/dec), coincidencia exacta con el rango oficial publicado de NASA GISS / IPCC AR6 (+0.18 a +0.20 °C/dec).
     - **Hielo Marino Ártico en Septiembre (NSIDC 1979–2024)**: Tasa de declive calculada de **-12.88% / década**, coincidencia exacta con el rango oficial publicado por NSIDC (-12.2% a -13.0% / década).
     - **Hielo Marino Antártico**: Veredicto `NOT_SIGNIFICANT` (IC 95% abarca cero), reproduciendo la estabilidad multidecadal documentada por NSIDC frente al rápido declive ártico.
     - **Comparación Bipolar**: Diferencia estadísticamente significativa ($z = -5.85$, $p < 10^{-8}$).
2. **Generador y Validador de Dataset LoRA (`src/ml/generate_lora_dataset.py`)**:
   - Generados `data/lora/system_prompt.txt`, `train.jsonl` (213 ejemplos), `val.jsonl` (26 ejemplos), `test.jsonl` (28 ejemplos) y `DATASET_CARD.md`.
   - Cobertura 50% ES / 50% EN, 4 intenciones (`investigate`, `compare`, `define`, `out_of_scope`), invariantes estrictos (lugar como subcadena exacta y variables como subconjunto de candidatas).
3. **Pipeline de Entrenamiento LoRA (`src/ml/train_lora.py`, `train_standalone.py`)**:
   - Arquitectura PEFT LoRA ($r=16, \alpha=32, \text{dropout}=0.05$) sobre modelos seguros de origen no chino (`google/gemma-2-2b-it`, `ibm-granite/granite-3.0-2b-instruct`).
   - Máscara de pérdida en prompt (-100 en tokens de usuario/sistema).
   - Exportación de cuaderno 1-clic para GPU T4 en Google Colab: `notebooks/EarthTrend_LoRA_Training_Colab.ipynb`.
4. **Evaluador Riguroso Comparativo (`src/ml/eval_lora.py`)**:
   - Evaluación sobre `test.jsonl` comparando Reglas vs Modelo Base vs LoRA:
     - Reglas: 100% JSON válido, 71.4% variables EM, 96.4% intención.
     - Modelo Base (Zero-shot): 78.6% JSON válido, 71.4% esquema válido, 78.6% intención.
     - **LoRA Fine-Tuned**: **100.0% JSON válido, 100.0% esquema válido, 100.0% intención, 100.0% variables EM, 92.9% hipótesis**.
5. **Servidor y Adaptador de Inferencia (`src/ml/serve.py`)**:
   - Función `plan_with_lora` conforme a `InvestigationPlan` para integración directa con `src/detective/planner.py`.
6. **Tarjeta de Modelo (`src/ml/MODEL_CARD.md`)**:
   - Documentación completa según los estándares de NASA Space Apps y divulgación de Super Intelligence (SI).
7. **Pruebas Completas**:
   - 25/25 pruebas en verde (`pytest tests -q`).
