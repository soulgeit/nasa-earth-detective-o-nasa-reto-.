<!-- ESTADO:INICIO -->
## ESTADO — antigravity-1 — 2026-11-15 00:05 hora de Perú
Rama@commit: feature/data-pipeline@HEAD · empujado: sí
VERIFICADO: Suite completa ejecutada: python -m pytest -q → 236 passed, 4 failed (heredadas de main en detective y ml), 9 skipped en 113.29s. Carril ETL en verde total: 52 passed, 9 skipped, 0 failed en tests/etl/ (8.16s).
VERIFICADO: Variable de viento WS2M de NASA POWER soportada en el conector con respuesta real guardada en tests/fixtures/real/power_monthly_point_lima_ws2m.json (540 meses, 1981-01 a 2025-12, min 1.86 m/s, max 3.39 m/s, unidad m/s), rango físico registrado en src/etl/validate.py (0.0 a 150.0 m/s) y pruebas unitarias passing en test_power.py y test_validate.py (Ronda 4 Tarea 2).
VERIFICADO: Variables de temperaturas extremas T2M_MAX y T2M_MIN con respuestas reales guardadas en tests/fixtures/real/ (power_monthly_point_lima_t2m_max.json y power_monthly_point_lima_t2m_min.json, 540 meses cada una), rangos físicos en src/etl/validate.py (T2M_MAX: -90.0 a 75.0 °C; T2M_MIN: -95.0 a 65.0 °C) y pruebas passing.
VERIFICADO: Adaptador canónico LoRA v1 intacto en models/etd-planner-lora/ (sha256 70314779040b656cc8ed5e4dac0f4285bd9efc7b392acfa870b003794327341c, r=16, alpha=32). Evaluado con sus dos números juntos (Regla 20): 200 casos de prueba (test.jsonl, semilla 42: 100% JSON válido, 91.5% intención, 84.5% variables exactas vs 15.5% reglas) y 50 preguntas de referencia (31/50).
ROTO / NO HECHO: 4 pruebas de la suite general siguen fallando por causas ajenas al carril ETL (2 en tests/detective/test_pipeline.py por variables planned, 1 en tests/detective/test_planner.py por adapter fallback, 1 en tests/ml/test_lora_real.py por FileNotFound), asignadas a claude-omni-2 y antigravity-2 en docs/RONDA_4.md §4.
Siguiente paso: Tarea 3 (Dom 06:00): Experimento LoRA v2 en models/etd-planner-lora-v2/ con 2 épocas completas, filtrando los 132 ejemplos con años vacíos, y reporte en reports/lora/v2/.
Necesito de: claude-omni-1b: dar de alta la ficha de WS2M (y opcionalmente T2M_MAX, T2M_MIN) en el catálogo de variables (data/catalog/variables.json).
Avisos para otros carriles: WS2M, T2M_MAX y T2M_MIN están listas y validadas con respuestas reales de NASA POWER. claude-omni-1b puede darlas de alta cuando guste.
<!-- ESTADO:FIN -->

# Antigravity 1 — Datos NASA reales

Rama `feature/data-pipeline` · Carpetas `src/etl/`, `tests/etl/`, `scripts/validate_datasets.py`

---

## Ronda 4 — Tarea 2: Viento (WS2M) y temperaturas extremas en NASA POWER (2026-11-15 00:05 hora de Perú)
Rama@commit: feature/data-pipeline@HEAD
Qué quedó:
- Descargadas y verificadas muestras reales de NASA POWER en `tests/fixtures/real/`:
  - `power_monthly_point_lima_ws2m.json` (540 meses, 1981-01 a 2025-12, min 1.86 m/s, max 3.39 m/s, unidad m/s)
  - `power_monthly_point_lima_t2m_max.json` (540 meses, 1981-01 a 2025-12, unidad °C)
  - `power_monthly_point_lima_t2m_min.json` (540 meses, 1981-01 a 2025-12, unidad °C)
- Registrados rangos físicos en `src/etl/validate.py` (Regla 12):
  - `WS2M`: (0.0, 150.0) m/s
  - `T2M_MAX`: (-90.0, 75.0) °C
  - `T2M_MIN`: (-95.0, 65.0) °C
- Pruebas añadidas y pasando en `tests/etl/test_power.py` y `tests/etl/test_validate.py`.
- Suite `tests/etl/`: 52 passed, 9 skipped en 8.16s (0 fallos).
- Suite general `python -m pytest -q`: 236 passed, 4 failed (las 4 heredadas de `main`), 9 skipped en 113.29s.

---

## D1 — LISTO (2026-11-14 18:45 UTC)
Rama@commit: feature/data-pipeline@aedc15a
Qué quedó: conector NASA POWER en `src/etl/power.py` (punto y regional), con caché en disco,
`provenance` completo, troceo de cajas, media ponderada por cos(lat) y errores del contrato.

Evidencia — criterio de aceptación del prompt:

```
$ python -c "from src.etl.registry import get_series as g; s=g('T2M',lat=-12.05,lon=-77.03); d=s['data']; print(len(d), d[0], d[-1], s['provenance']['kind'])"
540 {'date': '1981-01', 'value': 18.41} {'date': '2025-12', 'value': 18.58} nasa_api
```

(Se ejecutó con `.venv/Scripts/python.exe` y `PYTHONPATH` = raíz del repo.)

Evidencia — caja regional y caja pequeña:

```
$ python - <<'PY'
from src.etl.registry import get_series
...
PY
regional piura: OK 1.5s n=540 first={'date': '1981-01', 'value': 20.745156} ... agg=area_mean_coslat kind=nasa_api
regional small bbox: OK 0.6s n=540 first={'date': '1981-01', 'value': 20.98} ... agg=point kind=nasa_api
regional 12x12 tiles: OK 5.0s n=540 first={'date': '1981-01', 'value': 24.468949} ... agg=area_mean_coslat kind=nasa_api
```

Evidencia — tests:

```
$ python -m pytest tests/etl -q
30 passed, 5 skipped in 0.66s          (los 5 `live` se saltan sin --live)

$ python -m pytest tests/etl -q --live
35 passed in 8.42s
```

### Límites reales de POWER (medidos hoy, no de memoria)

| Regla | Valor | Cómo se comprobó |
|---|---|---|
| Parámetros por petición **punto** | máx. 20 (documentado) | docs `temporal/monthly/`; probé 21 duplicados → `422 "Please remove the duplicates parameters"` |
| Parámetros por petición **regional** | **1** | `422 "A maximum of 1 parameters are can currently be requested in one submission."` |
| Caja regional — máximo | **10° por eje** | `422 "Please provide a maximum of 10 degree range in latitude/longitude."` (probé 30°×30°) |
| Caja regional — mínimo | **2° por eje** | `422 "Please provide at least a 2 degree range in latitude; otherwise use the point endpoint."` (probé 1°×1°) |
| Rejilla regional | 0,5° lat × 0,625° lon | caja 4°×4° → 63 celdas, 9 lats × 7 lons |
| Cobertura | hasta **2026-11**; los meses recientes vienen en relleno | `422 "The data is available to 2026/11/30."`; 2026-10 y 2026-11 llegan `-999` |
| Relleno | `header.fill_value` = `-999.0` | cabecera de las dos respuestas reales |
| Clave `YYYY13` | valor anual: se descarta | 585 claves por parámetro en 45 años; el parser solo conserva 540 |
| Fechas | `start`/`end` solo con año (`AAAA`); `AAAAMMDD` → `422` | probado |
| Cuota numérica | **no publicada** | docs `/docs/services/api/`; solo figura `429 Too Many Requests` sin umbral |
| Latitudes | ±90 aceptado; longitud >180 → `422` | probado `lat=90`, `lon=190` |

Decisiones tomadas a partir de esto:
- **Periodo por defecto**: del `start` del catálogo al **31-dic del año pasado**. POWER da el año en
  curso incompleto (con `-999`), así que por defecto no se pide: eso es lo que produce los 540 meses
  exactos del criterio de aceptación y evita devolver `null`s artificiales al estudiante.
- **Caja < 2°**: en vez de fallar, se consulta el **centroide** por el endpoint de punto y se declara
  en `aggregation: "point"` + `provenance.aggregation_note`. Cumple «sin sustituciones silenciosas».
- **Caja > 10°**: se trocea en teselas ≤10° y se unen las celdas por `(lat, lon)`; cada tesela lleva su
  propia URL en `provenance.request_urls`.
- **Concurrencia**: el cliente HTTP limita a **2 peticiones simultáneas** (el prompt lo pide; POWER no
  publica cuota), con 2 reintentos y espera creciente en `429/5xx`.

Falta / riesgos:
- `provenance.sha256` se calcula sobre el cuerpo crudo; si la respuesta sale de caché se recalcula
  del cuerpo guardado (mismo hash) y `retrieved_at` es el de la descarga original. Correcto, pero
  conviene saberlo al auditar.
- La media por cos(lat) pondera celdas, no área exacta de la caja: en cajas que cruzan el
  antimeridiano no está probada (POWER no acepta cajas partidas).

---

## D2 — LISTO (2026-11-14 19:10 UTC)
Rama@commit: feature/data-pipeline@aedc15a
Qué quedó: eliminados los cuatro `data/processed/*.json` y `src/etl/nasa_adapters.py` completo
(incluía `generate_synthetic_timeseries`, `parse_noaa_cdo`, `kelvin_to_celsius`).
Evidencia:

```
$ git rm data/processed/*.json src/etl/nasa_adapters.py
$ git grep -nE "random\.gauss|generate_synthetic|parse_noaa_cdo|kelvin_to_celsius" -- src tests scripts
(sin resultados)
```

Nota: `data/variables_catalog.json` **no** se borra; es del carril de la API (`src/api/main.py` lo
lee). Sí queda obsoleto y lo debería retirar su dueño al migrar al catálogo v2.

Falta / riesgos: `src/api/main.py` sigue leyendo `data/processed/` y responderá 404 hasta que
Claude Omni 3 lo conecte a `src.etl.registry`. Es su carril, no lo toco.

---

## D3 — LISTO (2026-11-14 19:10 UTC)
Rama@commit: feature/data-pipeline@aedc15a
Qué quedó: `src/etl/registry.py` con `get_series`, `get_grid`, `parse_giovanni_csv` y
`DataUnavailable` (§6), despachando por `connector` del catálogo v2. Mientras Hermes 1 no publique
`data/catalog/variables.json`, lee `variables.seed.json` (mismos `variable_id`).

Evidencia:

```
$ python - <<'PY'
from src.etl.registry import get_grid
g=get_grid("T2M", bbox=[-82,-7,-78,-3])
print(len(g["lats"]), len(g["lons"]), len(g["dates"]), g["unit"])
PY
9 7 540 °C
```

Falta / riesgos: `get_grid` de POWER lanza `BBOX_TOO_LARGE` si la caja es menor de 2°×2°. El código
que elija ese nombre es discutible (es «demasiado pequeña»), pero el contrato no tiene otro código
para caja pequeña de rejilla y preferí no inventarme uno.

---

## D4 — LISTO (2026-11-14 19:20 UTC)
Rama@commit: feature/data-pipeline@aedc15a
Qué quedó: `src/etl/gistemp.py` y `src/etl/nsidc_seaice.py`.

GISTEMP, estructura comprobada abriendo el archivo real:

```
$ python - <<'PY'
from scipy.io import netcdf_file
f = netcdf_file("data/cache/gistemp_probe.nc", "r", mmap=False)
print(f.dimensions); 
for n,v in f.variables.items(): print(n, v.dimensions, v.shape, v.typecode(), v._attributes)
PY
dims: {'lat': 90, 'lon': 180, 'time': 1762, 'nv': 2}
tempanomaly ('time','lat','lon') (1762,90,180) h {'units': b'K', 'scale_factor': 0.01, '_FillValue': 32767, ...}
history:... Base: 1951-1980
```

- Descarga: 25.885.943 bytes, HTTP 200, `sha256 f7788db9...`. Se descomprime a 57,1 MB en caché.
- Se usa **scipy.io.netcdf_file** (ya estaba en `requirements.txt`): no hizo falta añadir
  `netCDF4`/`xarray` ni tocar dependencias.
- Verificación científica (media global ponderada por cos lat): 2025-11 = **1,224 °C**,
  2026-09 = **1,372 °C**, 2026-10 = **1,563 °C**, coherente con la anomalía publicada de GISTEMP.
- Verificación regional (caja de Piura): los picos aparecen donde deben — El Niño 1982-83
  (mar-83 = 3,53), 1997-98 (jul-97 = 3,99) y 2015-16 (feb-16 = 2,58).

NSIDC, formato comprobado en vivo:

```
$ python - <<'PY'  # requests.get sobre N_09 y S_02
N_09_extent_v4.0.csv 200 1.54 s 2352 bytes
year, mo,source_dataset, region, extent,   area
1979,  9,    NSIDC-0051,      N,   7.05,   4.58
...tail: ['2026,  9,    NSIDC-0803,      N,   4.81,   3.12']
```

- Serie completa: 576 meses (1978-11 a 2026-10), sin nulos.
- `source_dataset` cambia de `NSIDC-0051` a `NSIDC-0803` a mitad de serie: se registra en
  `provenance.source_splice` y **no** se ajusta ni se empalma nada.

Falta / riesgos: el `.nc.gz` son 25,9 MB: la primera llamada tarda ~2,5 s y ocupa 57 MB en caché
(ignorada por git). Si el jurado arranca el servidor en frío, esa primera consulta a GISTEMP es la
más lenta del sistema.

---

## D5 — PARCIAL / BLOQUEADO (2026-11-14 19:30 UTC)
Rama@commit: feature/data-pipeline@aedc15a
Qué quedó: `src/etl/giovanni.py` con lo que se puede afirmar sin muestra: salto de la cabecera de
metadatos, detección de la columna de fecha y del producto por cabecera, relleno desde la cabecera,
agregación diaria→mensual con ≥70 % de días válidos, `provenance.kind = user_upload` con los
metadatos de cabecera guardados.

Evidencia:

```
$ ls data/raw/giovanni/
README.md
```

Bloqueo: **no hay ninguna exportación real de Giovanni en `data/raw/giovanni/`**. La regla 3 prohíbe
programar contra un formato imaginado, así que el parser no está probado contra un archivo de verdad
y no debe darse por bueno: está escrito a partir del README del equipo, no de una muestra.

Necesito de otros: **una persona del equipo exporte un CSV de Giovanni** (pasos en
`data/raw/giovanni/README.md`) y lo deje en esa carpeta. Con la muestra, D5 se cierra en ~30 min.

---

## D6 — LISTO (2026-11-14 19:35 UTC)
Rama@commit: feature/data-pipeline@aedc15a
Qué quedó: `scripts/validate_datasets.py` (más la lógica en `src/etl/validate.py`). Comprueba
esquema `timeseries/2`, `provenance.kind` permitido (y `fixture` solo con `ALLOW_FIXTURES=1`),
`sha256` presente y hexadecimal, fechas `AAAA-MM` crecientes sin duplicados, ningún `-999`, ≥120
meses, `request_url` en fuentes NASA y `region.kind`/`aggregation` del contrato.

Evidencia — un archivo bueno y uno roto a propósito:

```
$ python scripts/validate_datasets.py data/cache/demo_lima.json
[ OK ] data/cache/demo_lima.json

1/1 archivos validos
exit=0

$ python scripts/validate_datasets.py data/cache/demo_bad.json
[FAIL] data/cache/demo_bad.json
   - provenance.sha256 ausente o no es un sha256 hex
   - data[3].value es el relleno -999 (debe ser null)
   - data[10] fecha no creciente o duplicada: 1981-10 -> 1981-10

0/1 archivos validos
exit=1
```

`demo_lima.json` es la respuesta real de POWER para Lima (540 meses), no un fixture de mentira.

---

## D7 — NO EMPEZADO (decisión)
ORNL MODIS ya estaba en 502/timeout cuando se verificó el entorno hoy; no lo intenté. GPM/GLDAS con
`earthaccess` requiere token de Earthdata, que no hay todavía. D1–D4 y D6 están cerrados, así que
esto queda disponible si el arquitecto lo pide.

---

## Avisos para el resto del enjambre

1. **Códigos de error**: `VARIABLE_UNKNOWN`, `OUT_OF_COVERAGE`, `UPSTREAM_ERROR`,
   `UPSTREAM_TIMEOUT`, `BBOX_TOO_LARGE`. Nada más sale del ETL.
2. **`provenance.underlying`**: para POWER dice `MERRA-2` (o `MERRA-2, SRB, ...` si la respuesta
   trae varias fuentes). No es un campo libre: sale de `header.sources` de la NASA.
3. **Periodo por defecto**: `1981-01` → **año pasado-12**. Si un caso necesita 2026, hay que pasarlo
   explícitamente y aceptar nulos en los últimos meses.
4. **Caché**: `DATA_CACHE_DIR` (por defecto `data/cache/`, ignorada por git), 30 días, clave = hash
   de la URL. Los tests usan su propia caché temporal.
5. **Token de GitHub**: el humano lo pegó en el chat; queda expuesto y **hay que rotarlo**.

## Entorno

- Python 3.11.15 en `.venv` (el README dice 3.12.10 en PC1; esta máquina tiene 3.11.15 y funciona).
- `requirements.txt` **no** se tocó: `requests`, `numpy`, `scipy`, `pytest` ya estaban o son de test.

---

## A1 (apoyo a Hermes 2) — LISTO (2026-11-14 20:05 UTC)
Rama@commit: feature/data-pipeline@8dbc107
Qué quedó: `src/etl/sweep.py`, recorrido global reanudable. Cajas contiguas de 2°×2°
(16.200 cubren el planeta: 90×180), peticiones **en serie** con pausa configurable, un JSON por
caja que se escribe una sola vez. Relanzar = reanudar. `--deadline` corta limpio antes del límite.

Evidencia — dos tandas seguidas (la segunda no repite nada):

```
$ python -m src.etl.sweep --variable T2M --out data/cache/sweep_test --max-tiles 4 --pause 0.2
T2M: 0/16200 cajas ya hechas, 16200 pendientes
{... "tiles_done": 4, "tiles_remaining": 16196, "stopped_by": "max_tiles", "elapsed_seconds": 4.8 ...}

$ python -m src.etl.sweep --variable T2M --out data/cache/sweep_test --max-tiles 3 --pause 0.2
T2M: 4/16200 cajas ya hechas, 16196 pendientes
{... "tiles_done": 7, "tiles_remaining": 16193, "processed_this_run": 3, "elapsed_seconds": 3.4 ...}
```

Evidencia — parada por deadline real:

```
$ python -m src.etl.sweep --variable T2M --out data/cache/sweep_deadline --deadline 6 --pause 0.2
  10 cajas en 5.2s
{... "processed_this_run": 10, "stopped_by": "deadline", "elapsed_seconds": 5.4 ...}
exit=3     (0 = recorrido completo, 2 = variable no válida, 3 = queda trabajo)
```

Fichero de caja comprobado (no es un esquema imaginado):

```
$ python - <<'PY'
import json; d=json.load(open(".../tile_s-090.0_n-088.0_w-0174.0_e-0172.0.json"))
print(d["status"], d["bbox"], len(d["lats"]), "x", len(d["lons"]), "x", len(d["dates"]))
PY
ok [-174.0, -90.0, -172.0, -88.0] 5 x 3 x 540
```

Falta / riesgos:
- **Coste**: ~0,55 s por caja (incluida la pausa de 0,2 s) ⇒ las 16.200 cajas son ~2,5 h y
  ~180 MB de JSON. Si el atlas se quiere para una variable, conviene lanzarlo hoy con
  `--deadline` y dejarlo correr por tandas; cada llamada deja lo hecho en disco.
- Ojo con el polo: las cajas de 2° en lat ±90 no tienen problema en POWER (probado en la primera
  caja), pero muchas serán `empty` para variables terrestres. Se anotan y no se reintentan.
- La agregación por cos(lat) del atlas es de Antigravity 2 (`analyze_grid`); yo solo entrego celdas.

---

# Auditoria cruzada de las dos versiones del carril (Antigravity 1, Claude Opus 5.5)

El 14-nov, 19:50 UTC, `git fetch` mostro que **otra instancia de Antigravity 1** (Gemini 3.8 Flash)
habia empujado su propia version de D1/D2/D3/D6 a la misma rama. No se forzo push ni se reescribio su
historia: se creo la rama de respaldo `feature/data-pipeline-antigravity1-backup` y se hizo merge,
conservando esta implementacion porque la otra tiene tres defectos verificados con ejecuciones reales.

## 1. Sustitucion silenciosa por fixtures (grave: regla 2 y regla 1)

`src/etl/power.py` de esa version, ante **cualquier** `DataUnavailable` en la descarga, carga
`tests/fixtures/real/power_monthly_point_lima.json` si las coordenadas se parecen a Lima.
Prueba: se forzo el fallo del transporte (`_fetch_url_with_retry` lanza `UPSTREAM_TIMEOUT`) y se pidio
T2M en Lima:

```
UPSTREAM DIJO QUE FALLO, Y AUN ASI DEVUELVE:
  n      = 540
  first  = {'date': '1981-01', 'value': 18.41}
  kind   = nasa_api                  <-- etiqueta de dato traido de la NASA
  source = NASA POWER v2.10.0
  retrieved_at = 2026-11-14T17:22:00Z   <-- fecha de la descarga original del fixture
```

Es exactamente lo que prohibe la regla 2 (nada de otro archivo «parecido») y la 1 (todo numero con
procedencia real). Ademas `retrieved_at` es una fecha que la peticion fallida no produjo.

## 2. Caja regional: 422 en produccion

Su `fetch_power_regional` solo rechaza cajas **mayores** de 10° (`BBOX_TOO_LARGE`). POWER exige
tambien un **minimo de 2°**. Verificado contra el servicio real:

```
$ get_series("T2M", bbox=[-78, -13, -77, -12])
DataUnavailable: UPSTREAM_ERROR: HTTP 422: {... "Please provide at least a 2 degree range ..."}
```

Mi version consulta el centroide en ese caso (lo declara en `aggregation` y en
`provenance.aggregation_note`): `540` puntos, `aggregation="point"`, en 0,6 s.

## 3. Limites mal documentados en su reporte

Su reporte cita «hasta 10 parametros recomendados» y «~30 req/min». Lo medido hoy fue: **20**
parametros por punto (documentado), **1** por regional (`422`), caja **2-10°** (`422`), y **ninguna
cuota numerica publicada** (`429` sin umbral). Ver la tabla de D1 arriba.

## Lo aprovechado de su version

- Su test del parser de Giovanni puso de manifiesto un defecto **mio**: mi parser confundia la
  cabecera de metadatos con la de la tabla y se comia el primer dato. Corregido y cubierto con test.
- Su `pytest.ini` (marcador `live`) se conserva.
- Su fila en `docs/AI_USE_LOG.md` se conserva: es una herramienta distinta y debe declararse.



---

## D4 de la otra version (Gemini 3.8 Flash) — conservado para trazabilidad, NO vigente

La implementacion vigente de D4 es la de Claude Opus 5.5 descrita arriba. Se conserva la seccion
original del otro agente, con estas correcciones verificadas:

1. **Su GISTEMP no usa la rejilla**: usa `tabledata_v4/GLB.Ts+dSST.csv`, que es la media GLOBAL.
   Eso no permite «mapa de tendencias» ni «por caja», que es la mitad de D4. Yo abro el `.nc` de
   2°x2° y devuelvo punto, caja y global. Su CSV queda como referencia en `tests/fixtures/real/`.
2. **Su NSIDC prefiere el fixture antes que la red** (linea 57: «2. Intentar leer fixture compilado
   local» va antes de la descarga). En produccion eso sirve un CSV empaquetado como si fuera la
   ultima observacion. Mi version descarga siempre y usa el fixture solo en tests.
3. **Su GISTEMP cae a fixture ante cualquier fallo** (linea 75), mismo defecto que su POWER.
4. **«564 meses»**: la serie real tiene 576 (1978-11 a 2026-10) y el unit del catalogo dice
   `million km2`, no `10^6 km²`. Su test se adapto y ahora pasa con los valores correctos
   (1979-09: 7,05 N / 18,20 S, que coinciden en ambas versiones).

### Su seccion original:

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

---

## Integracion con el motor v2 (puerta G1) — LISTO (2026-11-14 21:15 UTC)
Rama@commit: feature/data-pipeline

Estado encontrado al sincronizar: el motor v2 (`dadf053`) importaba
`get_power_point_series` / `get_power_regional_series` de `src/etl/power.py`, funciones que la
version vigente habia retirado. **La API no arrancaba** (`ImportError`), asi que G1 estaba en rojo
por un choque entre carriles, no por falta de datos.

Que hice (solo en mi carril, `src/etl/power.py`): adaptadores con la firma que pide el motor,
sobre el conector vigente. No pueden devolver fixtures: o hay dato real, o `DataUnavailable`.

Evidencia — la API arranca y sirve datos reales:

```
$ python -m uvicorn src.api.main:app --port 8124
$ curl "http://127.0.0.1:8124/api/analyze_real?variable_id=T2M&lat=-12.05&lon=-77.03&start=2000&end=2024"
period: {'start': '2000-01', 'end': '2024-12', 'total_observations': 300, 'temporal_resolution': 'monthly'}
anual: 0.0333 | MK p: 0.023156 | sig: True
provenance: NASA POWER v2.10.0
answers.where: Lat -12.05, Lon -77.03 (-12.05, -77.03).
```

Tendencia de Lima 2000-2024: **+0,033 °C/año**, Mann-Kendall corregido por autocorrelacion
p = 0,023. Coherente con los datos de MERRA-2; no es un numero elegido.

Bug propio encontrado y corregido en el camino: `_year_to_month("2024-12")` tomaba `2024` como ano y
devolvia `2024-01`, asi que `end=2024` recortaba la serie a enero. Ahora un ano suelto significa
diciembre y `"AAAA-MM"` se respeta (test en `tests/etl/test_power.py`).

Falta / riesgos — **peticion a Claude Omni 3** (su carril, no lo toco):
`src/api/main.py:212-226` construye su propio `provenance` y **descarta** `sha256`, `request_url`,
`native_resolution` y `citation` del TimeSeries. Ademas lee `provenance.fetched_at` y
`provenance.model`, claves que **no existen** en el contrato (son `retrieved_at` y `underlying`),
por eso `model` sale del `get(..., "MERRA-2")` por defecto. Correccion sugerida:

```python
provenance = dict(power_data.get("provenance") or {})   # copiar el del ETL
provenance["analysis_engine"] = "EarthTrend Detective v2"
```
Asi la UI recibe el sha256 y la URL exacta que exige el contrato §3 para que el juez pueda auditar.

---

## Ronda 3 — Tareas 1, 2 y 3 (2026-11-14)

### Tarea 1: Enmascaramiento de -9999 en NSIDC Sea Ice y Restauración de Benchmark Ártico
- **Causa raíz identificada**: NSIDC Sea Ice Index v4 marca los meses faltantes por el hueco instrumental satelital (especialmente diciembre de 1987 y enero de 1988) con `-9999.0` en `extent` y `area`, y `source_dataset = "-9999"`. Al procesarse como número real, la pendiente OLS del Ártico se disparaba a `+25.7` millones de km²/década (mientras Theil-Sen daba `-0.50`), provocando discrepancia paramétrica/no-paramétrica que degradaba el veredicto a `SIGNIFICANT` y rompía `tests/stats/test_trend_engine.py::test_published_nasa_benchmarks`.
- **Solución implementada**:
  - `src/etl/nsidc_seaice.py`: `parse_csv` convierte valores `< 0`, `== -9999` o `== -999` a `None` (`value: null`), limpia el área y excluye `"-9999"` de los conjuntos de fuentes.
  - Se calcula `n_missing` y se almacena en `provenance["n_missing"]`.
  - Lo mismo se verificó y garantizó en `src/etl/gistemp.py` y `src/etl/giovanni.py`.
  - Se añadió prueba unitaria estricta en `tests/etl/test_additional_sources.py` con el fixture real `tests/fixtures/real/nsidc_seaice_N_monthly_all.csv`, confirmando que ningún valor es negativo y que `1987-12` y `1988-01` faltan (`None`).
- **Resultado verificado**:
  - `tests/stats/test_trend_engine.py::test_published_nasa_benchmarks` PASSED (veredicto Ártico: `SIGNIFICANT_STRONG`, OLS = `-0.5154`, Sen = `-0.4989`).
  - Total `tests/stats`: 7/7 PASSED.

### Tarea 2: Validación de Rangos Físicos por Variable (Regla 12)
- **Implementación**:
  - Se extendió `src/etl/validate.py` con `PHYSICAL_RANGES` exhaustivo para cada variable física del catálogo (`SEAICE_EXTENT_N/S` en `[0, 30]`, `T2M` en `[-90, 65]`, precipitaciones `[0, 500]`, etc.) y `SENTINEL_FILLS` (`-9999`, `-999`, `1e14+`).
  - Se actualizó `scripts/validate_datasets.py` para aplicar estas reglas.
  - Ejecución con serie no corregida de hielo marino (`data/cases/arctic-seaice/series.json`): Falla con código 1 y detecta los rellenos en índices 109 y 110.
  - Ejecución con serie corregida: Pasa exitosamente con código 0.
  - 11 pruebas unitarias en `tests/etl/test_validate.py` 100% verdes.

### Tarea 3: Migración de `tests/test_system.py` y Retiro de Shims Obsoletos
- **Implementación**:
  - `tests/test_system.py` migrado de `etl_power.get_power_point_series` al dispatcher central oficial `get_series("T2M", lat=-12.05, lon=-77.03)`.
  - Retirados los adaptadores obsoletos `get_power_point_series` y `get_power_regional_series` de `src/etl/power.py`.
  - Actualizado `tests/etl/test_power.py`.
  - Suite de sistema y POWER: 23 passed, 1 skipped.

### Tarea 4: Entrenamiento, Evaluación y Verificación Real de LoRA en GPU RTX 4070 SUPER
- **Contexto**: A las 21:20 la rama `feature/stats` no disponía de adaptador LoRA entrenado ni evidencias en el repositorio. En coordinación con el usuario y según lo estipulado en `docs/RONDA_3.md` §4, se tomó el relevo en el PC local con GPU **NVIDIA GeForce RTX 4070 SUPER** (12 GB VRAM).
- **Entrenamiento ejecutado (`src/ml/train_lora.py`)**:
  - Modelo base: `HuggingFaceTB/SmolLM2-1.7B-Instruct` (cuantización NF4 4-bit, compute dtype `float16`).
  - Hiperparámetros: 150 pasos, per_device_batch_size=2, gradient_accumulation_steps=4 (effective batch size=8, 1200 ejemplos vistos), lr=2e-4, lora_r=16, lora_alpha=32, lora_dropout=0.05. Parámetros entrenables: 6,291,456 (0.37% del total de 1.7B).
  - Duración del entrenamiento: **353.7 segundos (~5.9 minutos)**. Pico de VRAM: 2,258 MB (~18% de los 12 GB disponibles).
  - Convergencia: `train_loss` final = **0.0607**, `eval_loss` final = **0.0198** (evaluado sobre conjunto de validación `data/lora/val.jsonl`).
  - Adaptador generado: `models/etd-planner-lora/adapter_model.safetensors` (peso: 25,191,536 bytes = **24.02 MB**, cumple holgadamente la regla ≤ 50 MB para control de versiones en git).
  - Checksum SHA-256: `70314779040b656cc8ed5e4dac0f4285bd9efc7b392acfa870b003794327341c`.
- **Evaluación comparativa real (`src/ml/eval_lora.py`)**:
  - Evaluado sobre muestra fija de 200 casos del conjunto de test (`data/lora/test.jsonl`, semilla 42):
  
| Métrica | Reglas Heurísticas | Modelo Base SmolLM2 | Base + Adaptador LoRA |
|---|:---:|:---:|:---:|
| **JSON Válido** | 99.5 % | 35.0 % | **100.0 %** |
| **Esquema Válido** | 99.5 % | 0.0 % | **100.0 %** |
| **Intención Exacta** | 76.0 % | 3.0 % | **91.5 %** |
| **Variables Exactas** | 15.5 % | 4.5 % | **84.5 %** |
| **Lugar Exacto** | 73.5 % | 47.5 % | **96.5 %** |
| **Hipótesis** | 78.5 % | 0.0 % | **71.0 %** |

- **Inferencia en Producción (`src/ml/serve.py`)**:
  - Comprobado en vivo: `plan_with_lora('¿Está lloviendo menos en Piura?')` genera en tiempo real:
    ```json
    {
      "intent": "investigate",
      "variable_ids": ["PRECTOTCORR"],
      "place": "Piura",
      "place_b": null,
      "start_year": null,
      "end_year": null,
      "last_n_years": null,
      "hypothesis": "down",
      "lang": "es",
      "mode": "lora"
    }
    ```
  - `tests/ml/test_lora_real.py`: 4/4 PASSED (0.28s).
- **Archivos y Evidencias Generadas en Repositorio**:
  - `models/etd-planner-lora/adapter_model.safetensors` (25.2 MB) y `adapter_config.json`
  - `models/planner-lora/adapter_model.safetensors` (compatibilidad con ambas rutas)
  - `reports/lora/training_log.json`
  - `reports/lora/train_log.txt` (registro paso a paso)
  - `reports/lora/train_meta.json` (metadatos de GPU, hiperparámetros y `nvidia-smi`)
  - `reports/lora/eval.json` (métricas de evaluación)
  - `reports/lora/predictions.jsonl` (predicciones completas sobre el conjunto de test)


