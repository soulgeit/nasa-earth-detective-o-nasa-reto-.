# Reporte de Antigravity 1 — Datos NASA Reales (feature/data-pipeline)

## D1, D2, D3, D6 — LISTO (14-nov-2026 13:48)
Rama@commit: feature/data-pipeline

### Qué quedó:
1. **D1 — Conector NASA POWER (`src/etl/power.py`)**:
   - Conexión oficial a NASA POWER Monthly Point y Regional con `User-Agent: EarthTrendDetective/0.2`, timeout (10s/60s), reintentos con backoff exponencial.
   - Descarte estricto de claves anuales `YYYY13` y mapeo de valores de relleno (`-999.0`) a `null`.
   - Consulta regional con media ponderada por `cos(latitud)` (`aggregation: "area_mean_coslat"`).
   - Generación de rejillas 3D para mapas de tendencias (`TrendMap v2`).
   - Caché en disco en `DATA_CACHE_DIR` con TTL de 30 días y preservación de respuesta cruda.
   - Procedencia completa (`provenance`) conforme a Contratos §3: URL, hash SHA-256, versión de la API de NASA, cita oficial y timestamp UTC.
2. **D2 — Eliminación de series sintéticas**:
   - Eliminados definitivamente los 4 archivos simulados en `data/processed/`.
   - Eliminada la función `generate_synthetic_timeseries` y `random.gauss` de `src/etl/`.
3. **D3 — Registro central (`src/etl/registry.py`)**:
   - Funciones `get_series`, `get_grid`, `parse_giovanni_csv` y clase de excepción `DataUnavailable` con códigos del contrato §6.
   - Despacho automático basado en el catálogo (`variables.json` / `variables.seed.json`).
4. **D5 — Parser Giovanni (`src/etl/giovanni.py`)**:
   - Parser para exportaciones de Giovanni con metadatos, detección de unidades, y agregación diaria a mensual con umbral del >= 70% de cobertura.
5. **D6 — Validador de datasets (`scripts/validate_datasets.py`)**:
   - Validación de esquema `timeseries/2`, `provenance.kind`, SHA-256, orden temporal estricto sin duplicados, ausencia de -999 y mínimo de 120 meses.

### Evidencia:
- Comando de aceptación D1:
  ```powershell
  python -c "from src.etl.registry import get_series as g; s=g('T2M',lat=-12.05,lon=-77.03); d=s['data']; print(len(d), d[0], d[-1], s['provenance']['kind'])"
  ```
  Salida:
  ```
  540 {'date': '1981-01', 'value': 18.41} {'date': '2025-12', 'value': 18.58} nasa_api
  ```
- Pruebas unitarias de ETL (`pytest tests/etl -q`):
  ```
  .......                                                                  [100%]
  7 passed in 15.29s
  ```
- Auditoría de código sintético:
  ```powershell
  git grep -nE "random\.gauss|generate_synthetic" -- src
  # Resultado: limpio (0 coincidencias)
  ```
- Validación de datasets (`scripts/validate_datasets.py`):
  ```
  ✓ APROBADO good.json: Cumple timeseries/2, procedencia verificada, orden temporal y sin nulos corruptos.
  ❌ FALLÓ broken.json: Detectó esquema inválido, procedencia corrupta, fechas desordenadas y -999 sin limpiar.
  ```

### Límites de NASA POWER API documentados:
- Parámetros por petición: hasta 10 parámetros recomendados por petición GET.
- Cobertura espacial: Resolución de 0.5° x 0.625° en MERRA-2.
- Límites de caja regional: cajas mayores a 10°x10° se rechazan con código `BBOX_TOO_LARGE`.
- Frecuencia de peticiones: respetando límite de ~30 req/min con reintentos y caché local de 30 días.

---

## D4 — GISTEMP v4 & NSIDC Sea Ice Index v4 — LISTO (14-nov-2026 14:40)
Rama@commit: feature/data-pipeline

### Qué quedó:
1. **Conector NASA GISTEMP v4 (`src/etl/gistemp.py`)**:
   - Descarga directa de la tabla de medias mensuales globales de temperatura (Land-Ocean Temperature Index, 1880 a 2026) desde `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv`.
   - Caché persistente con SHA-256 en `data/cache/gistemp/` y fallback automático a fixture real offline (`tests/fixtures/real/gistemp_glb_monthly.csv`).
   - Normalización bajo contrato `timeseries/2` con `unit: "°C"`, `variable_id: "GISTEMP_TANOM"`, y agregación `area_mean_coslat`.
2. **Conector NSIDC Sea Ice Index v4 (`src/etl/nsidc_seaice.py`)**:
   - Descarga y compilación de series de extensión mensual de hielo marino satelital (DMSP SSM/I-SSMIS / Nimbus-7 SMMR) desde NOAA/NSIDC (`https://noaadata.apps.nsidc.org/NOAA/G02135/`).
   - Soporte para Ártico (`SEAICE_EXTENT_N`) y Antártico (`SEAICE_EXTENT_S`) con `unit: "10^6 km²"`, 1979 a 2026 (564 meses).
   - Fixtures reales preservados en `tests/fixtures/real/` para pruebas unitarias sin conexión.
3. **Integración en Registro (`src/etl/registry.py`)**:
   - `get_series("GISTEMP_TANOM")` y `get_series("SEAICE_EXTENT_{N,S}")` integrados y enrutados.
4. **Validador de Datasets (`scripts/validate_datasets.py`)**:
   - Función `validate_dataset(dict)` expuesta para validación programática en memoria y CLI.
5. **Pruebas (`tests/etl/test_additional_sources.py`)**:
   - 10/10 pruebas pasando en verde (`pytest tests/etl -q`).

### Evidencia:
- Validación directa:
  ```powershell
  python -c "from src.etl.registry import get_series; from scripts.validate_datasets import validate_dataset; print([(v, len(validate_dataset(get_series(v)))==0) for v in ['GISTEMP_TANOM', 'SEAICE_EXTENT_N', 'SEAICE_EXTENT_S']])"
  # [('GISTEMP_TANOM', True), ('SEAICE_EXTENT_N', True), ('SEAICE_EXTENT_S', True)]
  ```
- Test suite:
  ```
  tests/etl/test_additional_sources.py ...
  tests/etl/test_power.py .......
  10 passed in 15.39s
  ```
