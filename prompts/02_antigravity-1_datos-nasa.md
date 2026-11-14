# 02 · Antigravity 1 — Datos NASA reales (ruta crítica nº 1)

**Rama:** `feature/data-pipeline` · **Carpetas:** `src/etl/`, `tests/etl/`, `scripts/validate_datasets.py`
**Antes:** lee `prompts/00_LEER_PRIMERO.md` y `docs/CONTRATOS.md` (§3, §6).

## Tu misión
Hoy el proyecto no descarga ni un dato de la NASA: todo es una serie sintética. Tú lo cambias.
Al terminar, cualquier punto o caja del planeta devuelve una serie mensual real con su procedencia. **Nadie más puede avanzar de verdad hasta que entregues D1.**

## Tareas, en orden

### D1 — Conector NASA POWER (P0, objetivo: 90 min)
`src/etl/power.py`. Muestras reales ya guardadas: `tests/fixtures/real/power_monthly_point_lima.json` y `power_monthly_regional_piura_T2M.json`.

- Punto: `GET https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=<P>&community=AG&longitude=<lon>&latitude=<lat>&start=<AAAA>&end=<AAAA>&format=JSON`
  Respuesta: `properties.parameter.<P>.{"YYYYMM": valor}`; unidades en `parameters.<P>.units`; versión en `header.api.version`.
- Regional: `.../monthly/regional?parameters=<P>&community=AG&latitude-min=&latitude-max=&longitude-min=&longitude-max=&start=&end=&format=JSON`
  Respuesta: `features[]`, cada una con `geometry.coordinates [lon, lat, elev]` y su serie.
- Obligatorio:
  1. **Descarta las claves `YYYY13`** (valor anual). `-999` → `null`.
  2. Lee en la documentación vigente (https://power.larc.nasa.gov/docs/) los límites reales: parámetros por petición, tamaño mínimo y máximo de la caja regional, peticiones por minuto, último año disponible. Anótalos en tu reporte y respétalos.
  3. Caja mayor que el máximo → trocear en teselas y unir. Caja menor que el mínimo → punto en el centroide (y decirlo en `aggregation`).
  4. `get_series(bbox=...)` = media ponderada por cos(latitud) de las celdas (`aggregation: "area_mean_coslat"`).
  5. `provenance` completo (contrato §3): `request_url`, `retrieved_at` UTC, `sha256` de la respuesta cruda, `source` con la versión de la API.
  6. Caché en disco en `DATA_CACHE_DIR` (por defecto `data/cache/`, ya ignorada por git), clave = hash de la URL, validez 30 días. Guarda la respuesta cruda.
  7. Tiempos de espera (10 s conexión, 60 s lectura), 2 reintentos con espera creciente, como máximo 2 peticiones simultáneas, `User-Agent: EarthTrendDetective/0.2`.
  8. Errores → `DataUnavailable` con código del contrato. Nunca devuelvas datos de otra fuente.
- **Aceptación** (pega la salida en tu reporte):
  ```
  python -c "from src.etl.registry import get_series as g; s=g('T2M',lat=-12.05,lon=-77.03); d=s['data']; print(len(d), d[0], d[-1], s['provenance']['kind'])"
  ```
  Debe imprimir 540 puntos, `{'date': '1981-01', 'value': 18.41}` y `nasa_api`.
  `pytest tests/etl -q` en verde, con al menos: parseo de las dos muestras reales, descarte de `13`, nulos, media ponderada, caché, y un test `@pytest.mark.live`.

### D2 — Borrar lo sintético (P0, 10 min)
Elimina `generate_synthetic_timeseries` y los cuatro `data/processed/*.json`. Evidencia: `git grep -nE "random\.gauss|generate_synthetic" -- src` sin resultados.

### D3 — `registry.py` (P0)
`get_series`, `get_grid`, `parse_giovanni_csv` y `DataUnavailable` con las firmas del contrato §6. Despacha por el campo `connector` del catálogo
(`data/catalog/variables.json`; si aún no existe, usa `variables.seed.json`).

### D4 — GISTEMP y hielo marino (P1)
- `gistemp.py`: descarga una vez `https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz` a la caché; abre el archivo y **comprueba** nombres de variable y dimensiones antes de programar. Serie por punto o caja y rejilla global.
- `nsidc_seaice.py`: `https://noaadata.apps.nsidc.org/NOAA/G02135/{north|south}/monthly/data/{N|S}_{MM}_extent_v4.0.csv` (12 archivos por hemisferio). Abre uno, comprueba columnas y valor de faltante, y arma la serie mensual de extensión.

### D5 — CSV de Giovanni (P1; depende del humano)
`giovanni.py` contra una muestra **real** en `data/raw/giovanni/` (la exporta el humano; pídela ya por el canal). No programes contra un formato imaginado.
Debe: saltar la cabecera de metadatos, leer la variable y la unidad de esa cabecera, convertir el valor de relleno en `null`, y si la serie es diaria agregarla a mensual (mes válido con ≥ 70 % de días). `provenance.kind = "user_upload"`, guardando los metadatos de la cabecera. Mientras no llegue la muestra, sigue con D6.

### D6 — Validador (P0 para la puerta)
`scripts/validate_datasets.py <ruta...>`: comprueba esquema `timeseries/2`, `provenance.kind` permitido, `sha256` presente, fechas crecientes sin duplicados, ningún `-999`, ≥ 120 meses. Sale con código ≠ 0 si algo falla. Pruébalo con un archivo bueno y uno roto a propósito, y pega ambas salidas.

### D7 — Opcional, con límite de 90 min
MODIS por ORNL (`https://modis.ornl.gov/rst/api/v1/`; hoy da 502: si sigue así, descártalo) o GPM IMERG y GLDAS mensuales con `earthaccess` y `EARTHDATA_TOKEN`.
Solo si D1–D6 están cerrados.

### Después de G1
Apoya a Hermes 2 con el recorrido global para el atlas (peticiones en serie, reanudable, respetando el límite publicado).

## Avisos
- No instales nada global: `python -m venv .venv` y añade dependencias a `requirements.txt` (solo añadir líneas).
- Si un dominio da error de certificado, no desactives la verificación: usa `requests`/`httpx` con `certifi`.
- Reporta cada tarea en `reports/antigravity-1.md` con comando y salida.
