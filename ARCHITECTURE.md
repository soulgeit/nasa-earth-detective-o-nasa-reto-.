# ARCHITECTURE.md - EarthTrend Detective (NASA Space Apps Challenge)

Sistema multi-agente distribuido para la detección, visualización y análisis de significancia estadística de tendencias en variables de Ciencias de la Tierra de la NASA.

---

## 1. Misión del Sistema
Responder a las cuatro preguntas científicas fundamentales planteadas por la NASA:
1. **¿Qué está cambiando?** Identificación de la variable de Ciencias de la Tierra y definición en lenguaje accesible para estudiantes y público general.
2. **¿Dónde está cambiando?** Localización geográfica precisa (regiones climáticas, biomas, cuencas o coordenadas).
3. **¿Cuánto está cambiando?** Tasa de cambio cuantificada (tasa anual o decadal, porcentaje de variación, pendiente de cambio).
4. **¿Es estadísticamente significativo?** Aplicación rigurosa de métodos estadísticos:
   - Prueba no paramétrica de **Mann-Kendall** para detección de tendencia monótona.
   - Estimador de pendiente de **Sen (Theil-Sen)**.
   - Desestacionalización de series temporales (cálculo de anomalías restando la media del mes calendario).
   - Regresión lineal ordinaria (OLS) con intervalo de confianza al 95% y cálculo de valor *p* ($p < 0.05$).

---

## 2. Mapa de Módulos e Islas de Trabajo

Cada agente tiene propiedad exclusiva sobre su directorio asignado para garantizar cero colisiones de Git:

```
nasa-earth-detective/
├── ARCHITECTURE.md          <- Contratos, interfaces y diseño (Claude Fable 5.2)
├── TASKS.md                 <- Tablero de control de tareas (Claude Fable 5.2)
├── README.md                <- Documentación general y guía de ejecución
├── requirements.txt         <- Dependencias Python del sistema
├── data/                    <- ISLA DE LOS SCRAPERS (Hermes 1 y Hermes 2)
│   ├── variables_catalog.json
│   ├── raw/                 <- Datos brutos descargados
│   └── processed/           <- Series temporales normalizadas en CSV/JSON
├── src/
│   ├── stats/               <- ISLA DE ANTIGRAVITY 1 (Motor Estadístico)
│   │   ├── __init__.py
│   │   └── trend_engine.py  <- Mann-Kendall, Sen's slope, deseasonalize, OLS
│   ├── api/                 <- ISLA DE ANTIGRAVITY 2 (Backend REST - Nodo Remoto)
│   │   ├── __init__.py
│   │   └── main.py          <- Endpoints FastAPI (/variables, /regions, /analyze)
│   ├── ui/                  <- ISLA DE CLAUDE OMNI 1 (Dashboard & Visualización)
│   │   ├── index.html       <- UI interactiva con visualización de tendencias
│   │   ├── app.js           <- Lógica de consumo de API y renderizado gráfico
│   │   └── styles.css       <- Estilos limpios y accesibles
│   ├── detective/           <- ISLA DE CLAUDE OMNI 2 (Asistente Guiado y Presets)
│   │   ├── __init__.py
│   │   ├── wizard.py        <- Flujo de preguntas guiadas para estudiantes
│   │   └── case_studies.json<- Casos demostrativos (Aral Sea, Ártico, Amazonía)
│   └── etl/                 <- ISLA DE CLAUDE OMNI 3 (Parsers y Adaptadores NASA - Nodo Remoto)
│       ├── __init__.py
│       └── nasa_adapters.py <- Parsers Giovanni, NOAA CDO, AppEEARS y conversiones
├── scripts/                 <- Scripts de automatización Git y ejecución de Herdr
│   ├── setup_worktrees.sh   <- Creación de islas Git automáticas
│   └── run_fleet.sh         <- Lanzador de servicios
└── tests/                   <- Pruebas automatizadas de integración y regresión
    └── test_system.py
```

---

## 3. Contratos de Datos (Data Schemas)

### 3.1. Formato de Serie Temporal Normalizada (`TimeSeriesPoint`)
Todos los scrapers y módulos ETL deben entregar las series temporales con esta estructura en JSON:

```json
{
  "variable_id": "MODIS_NDVI",
  "region_id": "amazon_deforestation_arc",
  "unit": "Índice (0 a 1)",
  "period": "monthly",
  "data": [
    {"date": "2000-01-01", "value": 0.82},
    {"date": "2000-02-01", "value": 0.81},
    {"date": "2024-12-01", "value": 0.69}
  ]
}
```

### 3.2. Formato del Reporte Estadístico (`TrendAnalysisResult`)
El motor de `/src/stats/trend_engine.py` y el endpoint `POST /api/analyze` deben responder con esta estructura unificada:

```json
{
  "variable": {
    "id": "MODIS_NDVI",
    "name": "Índice de Vegetación de Diferencia Normalizada",
    "unit": "Índice",
    "sensor": "MODIS (Terra/Aqua)"
  },
  "region": {
    "id": "amazon_deforestation_arc",
    "name": "Arco de Deforestación Amazónico",
    "coordinates": [-10.5, -55.0]
  },
  "time_range": {
    "start": "2000-01-01",
    "end": "2024-12-01",
    "total_observations": 300
  },
  "metrics": {
    "annual_rate_of_change": -0.0052,
    "decadal_rate_of_change": -0.052,
    "percent_change_total": -15.85,
    "sen_slope": -0.00043,
    "r_squared": 0.78,
    "p_value": 0.000012,
    "is_significant": true,
    "confidence_level": "99.9% (p < 0.001)"
  },
  "detective_verdict": {
    "what": "Disminución continua de la cubierta vegetal y biomasa foliar.",
    "where": "Arco de Deforestación Amazónico (frontera agrícola y ganadera).",
    "how_much": "Caída del 15.85% (-0.052 unidades de índice por década).",
    "significance": "Altamente significativo según la prueba de Mann-Kendall (p = 0.000012). No es atribuible a variaciones climáticas aleatorias.",
    "climate_process": "Procesos antropogénicos de desbroce de bosque primario combinados con prolongación de la estación seca."
  },
  "series": {
    "raw": [...],
    "deseasonalized": [...],
    "trend_line": [...]
  }
}
```

---

## 4. Algoritmos Matemáticos Obligatorios

1. **Desestacionalización por Climatología Mensual:**
   $$\text{Anomalía}(año, mes) = X(año, mes) - \mu(mes)$$
   Donde $\mu(mes)$ es el promedio multianual del mes respectivo.

2. **Estadístico $S$ de Mann-Kendall:**
   $$S = \sum_{k=1}^{n-1} \sum_{j=k+1}^n \text{sgn}(X_j - X_k)$$
   Evalúa si existe una tendencia monotónica al alza ($S > 0$) o a la baja ($S < 0$).

3. **Pendiente de Sen (Median of Slopes):**
   $$Q_{med} = \text{mediana}\left( \frac{X_j - X_k}{j - k} \right) \quad \forall \ 1 \le k < j \le n$$
   Inmune a datos atípicos (outliers) causados por eventos climáticos extremos.

---

## 5. Reglas de Git para el Enjambre

1. Ningún agente hace commit directo a `main`.
2. Cada agente trabaja en su rama: `feature/{modulo}`.
3. El Arquitecto (`cfable`) realiza la integración en `main` tras auditar los cambios.
