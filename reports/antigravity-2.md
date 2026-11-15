<!-- ESTADO:INICIO -->
## ESTADO — antigravity-2 — 2026-11-15 07:20 hora de Perú
Rama@commit: feature/stats@fcbca81 · empujado: sí
VERIFICADO: Fusión de origin/integracion/ronda5 completada; suite completa ejecutada con 275 passed, 0 failed, 10 skipped (tests/stats y tests/ml 100% verde: 11 passed, 1 skipped); tabla «published vs. computed» de docs/VALIDACION_ESTADISTICA.md actualizada con comandos CLI reproducibles al lado para cada fila de hielo marino (septiembre, all-season y antártico), citas textuales de NSIDC/NOAA añadidas y «EXACT MATCH» sustituido por intervalo medido y diferencias numéricas exactas; comando reproducible de Monte Carlo documentado en §2; src/ml/MODEL_CARD.md actualizado con las cifras de Ronda 5 (Regla 20: 200 casos test 84.5%, 50 golden questions: LoRA GPU 40/50, LoRA CPU 37/50, reglas 49/50, histórico 31/50) y limitaciones actualizadas a variables vecinas (0 fallos en planned).
ESCRITO (sin ejecutar de punta a punta): Ninguno.
ROTO / NO HECHO: Ninguno en carril de estadística y ML.
Siguiente paso: Atender revisiones de QA (informe 2) o integración de las 10:00 (G3).
Necesito de: Nadie.
Avisos para otros carriles: Comandos repetibles para hielo marino y Monte Carlo disponibles en docs/VALIDACION_ESTADISTICA.md para que claude-omni-e (QA) los compruebe y claude-omni-2 / claude-omni-1b los citen en SUBMISSION y README.
<!-- ESTADO:FIN -->

# Reporte de Antigravity 2 — Ronda 5 (Cierre)

## Tareas Completadas en la Ronda 5 (§4 antigravity-2)

### 1. Fusión de la base `origin/integracion/ronda5`
- Integrada la rama `origin/integracion/ronda5` (commit `9104694`) sobre `feature/stats`.
- Verificada la regeneración de los casos de hielo marino sin valores residuales de `-9999` (`scripts/verify_seaice_cases.py` en verde con mínimos de 3.57 y 1.98).

### 2. Actualización de la Tabla «published vs. computed» ([docs/VALIDACION_ESTADISTICA.md](file:///C:/Users/docto/etd-stats/docs/VALIDACION_ESTADISTICA.md#L96-L115))
- Recalculadas todas las filas del hielo marino con comandos CLI de una línea directamente ejecutables y reproducibles por cualquier evaluador o script de QA:
  - **Hielo marino del Ártico en septiembre (1979–2024):** Cita literal del *NSIDC Sea Ice Index* ("The linear rate of decline for September sea ice extent is 12.2% per decade relative to the 1981 to 2010 average") y *NOAA Arctic Report Card 2023*. Calculado con el motor ETD v2: `-12.28% / década` (Theil-Sen: `-0.7186` × $10^6$ km²/dec, 95% CI: `[-0.8600, -0.6000]`; OLS: `-0.7412` × $10^6$ km²/dec). Estado: **Dentro del intervalo publicado** (diferencia de solo $+0.08\%$ / década respecto al 12.2% oficial).
  - **Hielo marino del Ártico todas las estaciones (1979–2024 y registro completo 1978–2026):** Cita literal de *NSIDC State of the Cryosphere* ("The linear rate of decline for all months combined from 1979 to 2024 is approximately -40,000 to -50,000 square kilometers per year (-0.40 to -0.50 million square kilometers per decade)."). Calculado con ETD v2: 1979–2024 Sen `-0.4989` × $10^6$ km²/dec (OLS `-0.5154`); registro completo congelado Sen `-0.4953` × $10^6$ km²/dec (95% CI: `[-0.5573, -0.4371]`, OLS `-0.5106`). Veredicto: `SIGNIFICANT_STRONG` ($p < 0.01$). Estado: **Dentro del intervalo publicado** (diferencia $\Delta = +0.0011$ a $+0.0047$ × $10^6$ km²/década respecto a -0.50).
  - **Hielo marino del Antártico (1979–2024 y registro completo 1978–2026):** Cita literal de *NSIDC Antarctic Sea Ice FAQ* ("Antarctic sea ice extent shows high interannual and multidecadal variability, with no statistically significant long-term trend observed over the satellite record (1979–present)."). Calculado con ETD v2: 1979–2024 Sen `-0.0028` × $10^6$ km²/dec (95% CI `[-0.1552, +0.1491]`, cruza el cero); registro completo congelado Sen `-0.0481` × $10^6$ km²/dec (95% CI `[-0.1913, +0.1023]`, cruza el cero). Veredicto: `NOT_SIGNIFICANT` ($p \ge 0.10$, `tests_agree: true`). Estado: **Coincide con el estado publicado** (estadísticamente indistinguible de cero, $\Delta = -0.0028$ × $10^6$ km²/dec).
  - **Comparación bi-regional (Ártico vs Antártico):** Diferencia estadísticamente significativa ($z = -5.85, p = 4.9 \times 10^{-9}$), confirmando dinámicas climáticas opuestas.
- Añadido el comando experimental para verificar Monte Carlo en la sección §2:
  `pytest tests/stats/test_trend_engine.py -k "monte_carlo" -v` (Cobertura 95.7%, Falsos positivos 5.0%).

### 3. Ficha del Modelo ([src/ml/MODEL_CARD.md](file:///C:/Users/docto/etd-stats/src/ml/MODEL_CARD.md))
- Actualizada con las cifras oficiales de la Ronda 5 (§1):
  - **200 casos de prueba sintéticos:** LoRA 84.5% exact variable match, 100% valid JSON, 100% valid schema, 91.5% intent accuracy, 96.5% place match, 71.0% hypothesis accuracy (vs Reglas 15.5%).
  - **50 preguntas de referencia (golden questions):**
    - Reglas deterministas: **49 / 50** (98.0%, único fallo: polvo de Sechura).
    - LoRA en GPU (4-bit NF4, RTX 4070 SUPER): **40 / 50** (80.0%, 50/50 planificadas por LoRA, latencia mediana 2.2 s/query).
    - LoRA en CPU: **37 / 50** (74.0%).
    - Histórico previo a Regla 19: 31 / 50 (62.0%).
- Sección «Limitations» actualizada:
  - 0 fallos en variables `planned` (resuelto por Regla 19).
  - El modo de fallo actual responde a confusión semántica entre variables vecinas (p. ej. temperatura de piel `TS` vs temperatura a 2 metros `T2M`).

### 4. Ejecución y Validación de la Suite
- Suite completa `python -m pytest -q`: **275 passed, 0 failed, 10 skipped**.
- Carril propio (`tests/stats/` y `tests/ml/`): **100% verde** (11 passed, 1 skipped sin GPU).
