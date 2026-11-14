# Antigravity 1 — Datos NASA reales

Rama `feature/data-pipeline` · Carpetas `src/etl/`, `tests/etl/`, `scripts/validate_datasets.py`

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
