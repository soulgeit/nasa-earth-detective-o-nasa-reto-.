# Comparación Cuantitativa: NASA POWER vs. NASA Giovanni (MERRA-2)

**Autor:** Antigravity 1  
**Fecha:** Domingo 15-nov-2026 07:05 hora de Perú (Ronda 5)  
**Comando reproducible:**
```bash
python scripts/compare_power_giovanni.py
```

---

## 1. Objetivo y Región de Estudio

Validar la coherencia física y estadística entre dos vías de acceso a los datos de reanálisis atmosférico **MERRA-2** de la NASA:
1. **NASA POWER API** (acceso programático mensual de `src/etl/power.py`).
2. **NASA Giovanni (GES DISC)** (exportación oficial CSV de `data/raw/giovanni/`).

La comparación se realiza sobre la misma región de la **Amazonía**:
- **Bounding Box:** `[-71.0, 0.85, -69.84, 1.7]` (Oeste, Sur, Este, Norte)
- **Periodo Común Completo:** 1981-01 a 2025-12 (**45 años = 540 meses continuos**)
- **Variables comparadas:**
  - `T2M`: Temperatura del aire a 2 m (°C)
  - `PRECTOTCORR`: Precipitación total corregida en superficie (mm/día)

---

## 2. Resultados Cuantitativos

### 2.1. Temperatura del aire a 2 m (`T2M`)

| Métrica | NASA Giovanni | NASA POWER | Diferencia (POWER − Giovanni) |
|---|---|---|---|
| **Media mensual** | 24.9185 °C | 24.9345 °C | **+0.0159 °C** |
| **Desviación estándar** | 0.8710 °C | 0.8679 °C | −0.0031 °C |
| **Error Absoluto Medio (MAE)** | — | — | **0.0483 °C** |
| **Error Cuadrático Medio (RMSE)** | — | — | **0.0752 °C** |
| **Correlación de Pearson ($r$)** | — | — | **0.9927** ($p < 10^{-15}$) |
| **Pendiente de Sen** | **+0.1964 °C/década** | **+0.1887 °C/década** | **−0.0077 °C/década** |
| **Intervalo Confianza 95% (Sen)** | [+0.1302, +0.2638] | [+0.1227, +0.2563] | Solape casi idéntico |
| **Pendiente MCO** | +0.1982 °C/década | +0.1889 °C/década | −0.0093 °C/década |
| **Veredicto Mann-Kendall** | `SIGNIFICANT_STRONG` ($p < 10^{-4}$) | `SIGNIFICANT_STRONG` ($p < 10^{-4}$) | **Coinciden al 100%** |

### 2.2. Precipitación (`PRECTOTCORR`)

| Métrica | NASA Giovanni | NASA POWER | Diferencia (POWER − Giovanni) |
|---|---|---|---|
| **Media mensual** | 7.8445 mm/día | 7.7944 mm/día | **−0.0501 mm/día** |
| **Desviación estándar** | 3.3278 mm/día | 3.2982 mm/día | −0.0296 mm/día |
| **Error Absoluto Medio (MAE)** | — | — | **0.2748 mm/día** |
| **Error Cuadrático Medio (RMSE)** | — | — | **0.3705 mm/día** |
| **Correlación de Pearson ($r$)** | — | — | **0.9938** ($p < 10^{-15}$) |
| **Pendiente de Sen** | **−0.0867 mm/día/década** | **−0.0122 mm/día/década** | **+0.0745 mm/día/década** |
| **Intervalo Confianza 95% (Sen)** | [−0.3229, +0.1561] | [−0.2542, +0.2250] | Ambos cruzan el cero |
| **Pendiente MCO** | −0.1018 mm/día/década | −0.0341 mm/día/década | +0.0677 mm/día/década |
| **Veredicto Mann-Kendall** | `NOT_SIGNIFICANT` ($p = 0.357$) | `NOT_SIGNIFICANT` ($p = 0.899$) | **Coinciden al 100%** |

---

## 3. Conclusiones Físicas y Metodológicas

1. **Altísima correlación y coincidencia de tendencias:**
   - Para temperatura ($T2M$), ambas fuentes exhiben una correlación de $r = 0.9927$ y una pendiente de calentamiento robusta y estadísticamente significativa de ~+0.19 °C por década, resultando en un veredicto idéntico `SIGNIFICANT_STRONG`.
   - Para precipitación ($PRECTOTCORR$), ambas fuentes muestran correlación de $r = 0.9938$ y confirman la ausencia de tendencia monótona significativa en 45 años, con un veredicto idéntico `NOT_SIGNIFICANT`.
2. **Origen de las diferencias menores:**
   - La caja de la Amazonía elegida tiene una extensión de $0.85^\circ \times 1.16^\circ$. Como la API regional de NASA POWER exige cajas de al menos $2^\circ \times 2^\circ$, para cajas sub-regionales el conector de POWER consulta el centroide ponderado $(-70.42^\circ, 1.27^\circ)$, mientras que Giovanni calcula la media exacta de área sobre las celdas nativas comprendidas. Aun con esta diferencia técnica de muestreo, la discrepancia media es de apenas **0.016 °C** y **0.05 mm/día**, lo cual valida la consistencia total del producto.

---

## 4. Frase de Síntesis en Inglés (para `claude-omni-1b` y `README.md`)

> *"Across the 1981–2025 period (540 months) over the Amazon bbox [-71.0, 0.85, -69.84, 1.7], NASA POWER and Giovanni agree closely on underlying MERRA-2 trends: for T2M, both identify a statistically significant warming trend (Giovanni +0.196 vs POWER +0.189 °C/decade; r=0.993, MAE=0.05 °C) with identical verdict (SIGNIFICANT_STRONG); for precipitation, both show no detectable trend (Giovanni -0.087 vs POWER -0.012 mm/day/decade; r=0.994) with matching verdict (NOT_SIGNIFICANT)."*
