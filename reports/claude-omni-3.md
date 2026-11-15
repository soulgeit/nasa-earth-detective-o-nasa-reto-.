<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-3 — 2026-11-15 11:10 (hora de Perú) — RONDA 6, cierre
Rama@commit: main@3f066f5 → integrado y empujado; ahora local = 8c07783 (sync) · empujado: sí
VERIFICADO: `fix/pytest-testpaths` fusionado en `main` (regla 30, aprobado por el humano) → `pytest -q` en clon limpio de `main` desde GitHub → **288 passed, 0 failed, 10 skipped**; `gate.py` → PUERTA ABIERTA (6/6)
VERIFICADO: `LICENSE` MIT y `requirements.txt` (10 deps `==`) en clon limpio; `requirements-dev.txt` (`-r` + pytest + httpx)
VERIFICADO: producción en Railway viva (`…-production.up.railway.app`) → smoke **17/17** (lo midió el arquitecto; yo confirmo el estado en su reporte)
CERRADO: el hallazgo bloqueante de la Ronda 6 (scripts/test_ui_r5.py rompía la colección de pytest) está en `main` y no vuelve
ROTO / NO HECHO: Docker no ejecutable aquí (no instalado); clon en Linux no ejecutable (sin WSL)
Necesito de: nada — mi carril cerrado. Queda el envío del formulario (humano, 20:00)
Avisos: `pytest.ini` ahora lleva `testpaths = tests`; quien clone `main` hoy sigue el README sin fricción
<!-- ESTADO:FIN -->

# Claude Omni 3 — API v2 y despliegue

Carril: `feature/api` · Carpetas: `src/api/`, `tests/api/`, `Dockerfile`, `scripts/smoke_api.py`

---

## A1 — LISTO (14-nov-2026, 13:30 hora de Perú)

Rama@commit: feature/api@505fcf8

**Qué quedó**

Esqueleto completo de la API según `docs/CONTRATOS.md` §7, programado contra las
firmas de §6 con un resolvedor que respeta la regla de oro: nunca sustituye datos.

| Archivo | Papel |
|---|---|
| `src/api/main.py` | App FastAPI con los 15 endpoints de §7; errores en formato §7 |
| `src/api/config.py` | Configuración por entorno; sin secretos; rutas del repo |
| `src/api/errors.py` | `ApiError` con `{code, message:{es,en}, hint}` y mapa de estados |
| `src/api/schemas.py` | Pydantic de TimeSeries v2, AnalysisResult v2, TrendMap v2, plan |
| `src/api/modules.py` | Resolvedor de módulos §6 + dobles de fixtures (solo `ALLOW_FIXTURES=1`) |
| `src/api/catalog.py` | Catálogo §8 desde `variables.json` o la semilla, marcando procedencia |
| `src/api/service.py` | Orquestación ETL → estadística, validación de series, caché |
| `src/api/cache.py` | Caché TTL en memoria con exclusión mutua por clave |
| `src/api/ratelimit.py` | Ventana deslizante por IP para los endpoints que llaman a la NASA |
| `src/api/validation.py` | Validación de lat/lon/bbox/fechas/variable/idioma |
| `src/api/report.py` | Informe imprimible HTML bilingüe, sin JS ni recursos externos |
| `Dockerfile` | Un solo servicio, sin torch, usuario no root, healthcheck |
| `scripts/smoke_api.py` | Recorrido de todos los endpoints, tabla y salida ≠ 0 si algo falla |
| `tests/api/test_contract.py` | 19 pruebas de contrato, errores y no-sustitución |

Decisiones que conviene conocer:

1. **Eliminada la sustitución silenciosa** de `main.py:103-108`. Si falta el dato →
   `404`/`502`/`504`/`503` con código. Ningún «analiza el primero disponible».
2. **`ALLOW_FIXTURES` apagado por defecto**: con el módulo real ausente, los
   endpoints de datos devuelven `503 DATA_UNAVAILABLE`. Los dobles de prueba solo
   existen con `ALLOW_FIXTURES=1` y todas sus respuestas llevan
   `provenance.kind = "fixture"` (la UI debe pintar el aviso rojo).
3. **`/api/health` informa qué falta**, no un «ok» genérico: dice qué módulo y qué
   función del contrato §6 no está importable.
4. **Título sin «NASA»**: «EarthTrend Detective API» (regla 10).
5. **CORS** abierto solo a `GET`/`POST`/`OPTIONS`, sin credenciales (A4).
6. **El catálogo sale de la semilla** mientras Hermes 1 no publique
   `data/catalog/variables.json`; la respuesta marca `catalog.source = "seed"` e
   `is_complete: false`, y los campos que la semilla no trae quedan vacíos, no
   inventados.

**Evidencia**

```
$ .venv/Scripts/python.exe -m pytest tests/api -q
19 passed, 41 warnings in 0.45s
```

```
$ PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/smoke_api.py http://127.0.0.1:8765
CHECK                            STATUS  TIME    DETAIL
-------------------------------  ------  ------  --------------------------------------------------
health                           PASS      12ms  HTTP 200 ai_mode=extractive
catalog/variables                PASS       1ms  HTTP 200 variables=25
analyze unknown variable -> 404  PASS       0ms  HTTP 404 code=VARIABLE_UNKNOWN
analyze no coords -> 400         PASS       0ms  HTTP 400
analyze Lima (G1)                SKIP       0ms  HTTP 503 — real data module not merged yet
trendmap                         SKIP       0ms  HTTP 503 — grid module not merged yet
cases                            PASS       0ms  HTTP 503
report                           SKIP       0ms  HTTP 503 — analysis module not merged yet
UI /                             PASS       0ms  HTTP 200 bytes=6023

6 passed · 3 skipped · 0 failed
EXIT=0
```

Prueba de orquestación de punta a punta (con un motor estadístico **descartable**
fuera del repo, solo para comprobar `service`/`cache`/`report`; no forma parte del
árbol de trabajo):

```
analyze 200
 schema analysis/2 prov fixture n_obs 540 card T2M
 trend 0.1184 SIGNIFICANT
cache stats {'entries': 1, 'hits': 1, 'misses': 2, 'ttl': 3600}
report 200 <!doctype html><html lang="en">... len 3569
trendmap 200 63
compare 200 ['a', 'b', 'compare']
```

Los dobles de fixtures reproducen exactamente la aceptación de D1:
540 puntos, primero `{'date': '1981-01', 'value': 18.41}`, `provenance.kind` fixture.

**Falta / riesgos**

- A2 (integración real) depende de `src/etl/registry.py` (Antigravity 1) y
  `analyze_series`/`analyze_grid`/`compare` (Antigravity 2). En cuanto empujen,
  el resolvedor los toma sin tocar `main.py`.
- `/api/cases` y `/api/atlas` esperan `data/cases/index.json` y
  `data/atlas/{variable}.json` de Hermes 2; hoy responden `503` con pista.
- `/api/report` usa los `answers` del AnalysisResult tal cual: si el motor los
  deja vacíos, el informe sale sin texto narrativo (no se inventa nada).
- La UI de `feature/ui` sigue llamando a `/api/analyze?region_id=...` (contrato v1);
  hasta que Claude Omni 1 migre a `lat`/`lon`, `/api/analyze` responde `400`. Es
  esperado y está en su carril (U1/U2).

**Necesito de otros**

- Antigravity 1: `src/etl/registry.py` con `get_series`, `get_grid`,
  `parse_giovanni_csv`, `DataUnavailable` (contrato §6).
- Antigravity 2: `analyze_series`, `analyze_grid`, `compare`.
- Hermes 1: `data/catalog/variables.json` para que las tarjetas dejen de ser semilla.
- Humano: hosting (Railway) para A5; el inicio de sesión lo haces tú.

---

## A6 — LISTO (14-nov-2026, 14:20 hora de Perú)

Rama@commit: feature/api@<pendiente de commit>

**Qué quedó**

`scripts/build_static.py` genera `dist/`: la UI sin API, con las respuestas
reales congeladas y un interceptor de `fetch` (`dist/static-api.js`) que
responde desde `dist/api/*.json`.

- `--base URL` hornea desde una API viva (local o desplegada).
- `--from-cases` hornea desde `data/cases/index.json` y `data/atlas/*.json`
  (carril Hermes 2), sin red.
- Lo que no está horneado → `503 DATA_UNAVAILABLE` con el formato §7. El
  respaldo **nunca inventa** un número.
- La comparación de posición tolera redondeo (`-12.0500` ≡ `-12.05`), que es
  justo lo que envía la UI.
- Si falta un archivo de la UI (`index.html`, `app.js`, `styles.css`,
  `i18n.js`) el script **falla** en vez de publicar una página rota.
- El interceptor se inyecta antes de `app.js` y respeta `window.ETD_API_BASE`.

**Evidencia**

```
$ python scripts/build_static.py --from-cases
dist/ built
{
 "cases": 1,
 "analyses": 1,
 "atlas": 0,
 "errors": 0
}
```

Prueba en Chrome real (headless, `--dump-dom`) contra `http://127.0.0.1:8899`
servido por `http.server` — es decir, sin ninguna API detrás:

```
has static shim: True
has verdict node: True
  DATA_UNAVAILABLE: False
  cases-list: True
  variable-select: True
```

Y pidiendo el shim directamente desde la página:

```
health 200 status,version,ai_mode,sources_up
catalog 200 catalog,variables
cases 200 cases
analyze-float 200 analysis/2      <- la UI envía -12.0500 / -77.0300
n_obs=540 verdict=SIGNIFICANT
analyze-wrong 503 DATA_UNAVAILABLE
atlas-miss 503 DATA_UNAVAILABLE
```

Los casos del índice horneado se pintan en la lista (`Lima, Peru — Lima air
temperature (static build test case)` en el DOM final).

```
$ .venv/Scripts/python.exe -m pytest tests/api -q
24 passed, 41 warnings in 2.26s
```

`tests/api/test_static_build.py` (5 pruebas): dist completo, orden de los
scripts, índice horneado con su posición, el shim no inventa datos y la falta
de un archivo de UI falla explícitamente.

**Falta / riesgos**

- Aún no hay `data/cases/` ni `data/atlas/` reales (Hermes 2). En cuanto
  existan, `--from-cases` produce el respaldo definitivo sin tocar código.
- El respaldo real se publica en GitHub Pages en A5; el login de hosting y el
  alta de la página lo hace el humano.
- Los CDN (Leaflet, Chart.js, fuentes) siguen siendo externos; si la red del
  juez los bloquea, el mapa no carga. Se puede empaquetar en local más tarde.

**Necesito de otros**

- Hermes 2: `data/cases/index.json` con los 3–4 casos elegidos y `data/atlas/*.json`.

---

## Bloqueo de push (14-nov-2026, 14:05)

El primer PAT del chat (fine-grained) autenticaba como `soulgeit` pero daba
`403 Permission ... denied` al empujar: le faltaba `Contents: Read and write`
sobre este repo. Con el PAT clásico del proyecto, el push de A1 quedó en
`031a022..505fcf8  feature/api`. Ningún token se guardó en el repo, en
`.git/config` ni en este reporte.

---

## A2 (parcial) — orquestación blindada con dobles (14-nov-2026, 14:45)

`src/etl` y `src/stats` aún no han empujado, así que la integración real sigue
pendiente. Mientras, se fijó con pruebas lo que **sí** puedo garantizar hoy:
que la orquestación no sustituya, no invente y traduzca bien los fallos.

`tests/api/doubles.py` + `tests/api/test_service.py` (12 pruebas):

- `analysis/2` con la tarjeta del catálogo añadida por la API.
- Caché: la segunda petición idéntica sale de caché (`hits >= 1`).
- `DataUnavailable` → `504 UPSTREAM_TIMEOUT` / `404 OUT_OF_COVERAGE`.
- **Un ETL que devuelve otra variable → `502 UPSTREAM_ERROR`** con el id pedido
  en el `hint`. Igual que la sustitución silenciosa de un archivo, la de una
  variable se corta.
- Serie vacía → `OUT_OF_COVERAGE`; serie corta → `422 INSUFFICIENT_DATA`.
- Esquema de análisis inesperado → `502`.
- `/trendmap` y `/compare` con el motor inyectado.
- `/report` en `en` y `es`, HTML autocontenido (sin una sola URL externa).
- `/analyze/upload` con CSV tipo Giovanni → `provenance.kind = user_upload`.
- Límite por IP → `429 RATE_LIMITED` con el formato §7.

```
$ .venv/Scripts/python.exe -m pytest tests/api -q
36 passed, 41 warnings in 2.06s
```

---

## A4/A5 (parcial) — UI en la raíz y registro estructurado (14-nov-2026, 14:35)

**Qué quedó**

- La UI se sirve **en la raíz** (`/`, `/app.js`, `/styles.css`, `/i18n.js`), que
  es donde los `index.html` de la UI buscan sus assets relativos. Antes solo
  estaba bajo `/ui` y los assets daban 404 en producción.
- Un asset que falta devuelve **404 JSON** con el formato §7, no la página HTML:
  un 200 con HTML donde el navegador espera JavaScript rompería la página sin
  decir por qué (fallo detectado y corregido durante la prueba).
- Rutas normales desconocidas → fallback SPA (la página), sin 404 secos.
- `/api/*` siempre tiene prioridad sobre el fallback.
- HTML con `Cache-Control: no-cache`; assets con `max-age=3600`.
- Registro estructurado por petición en JSON: método, ruta, estado y ms.
  **Sin IP, sin User-Agent, sin cabeceras ni cuerpos** (A4, sin datos personales).

**Evidencia**

```
$ curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/            -> 200
$ curl ... /app.js   -> 200 text/javascript
$ curl ... /nope.js  -> 404
$ grep '"event"' uvicorn.log
{"event": "request", "method": "GET", "path": "/", "status": 200, "ms": 3}
{"event": "request", "method": "GET", "path": "/app.js", "status": 200, "ms": 2}
{"event": "request", "method": "GET", "path": "/nope.js", "status": 404, "ms": 28}
```

```
$ .venv/Scripts/python.exe -m pytest tests/api -q
41 passed, 51 warnings in 2.57s
```

**Riesgo abierto**: los assets son los de `main` (UI v1) hasta que el arquitecto
fusione `feature/ui`. La UI nueva usa `i18n.js`, que no está en esta rama; el
servidor lo devuelve 404 en JSON (fallo explícito) en vez de servir HTML.

---

## A2 (cierre) — G1 verde con ETL y motor reales (14-nov-2026, 15:05)

Rama@commit: feature/api · fusionadas `feature/data-pipeline`, `feature/stats`,
`feature/wizard` y `feature/catalog`. Falta solo `feature/ui`.

**Qué quedó**

- **G1 pasa con datos reales de NASA POWER**, sin dobles: 540 meses de Lima
  (1981-01 → 2025-12), `analysis/2`, `SIGNIFICANT_STRONG`, Theil-Sen
  +0.1585 °C/década, MK corregido Hamed-Rao p = 3.9e-05.
- `pymannkendall>=1.4.3` declarado en `requirements.txt` (lo usa el contraste
  numérico de E2).
- `tests/test_system.py` reescrito: el anterior importaba funciones del prototipo
  (`mann_kendall_test`, `theil_sen_slope`, ...) que ya no existen y **rompía la
  colección de todo `pytest`**. Ahora prueba el motor v2 con series
  deterministas y la honestidad de la procedencia.
- Las 3 pruebas de contrato que esperaban el mundo anterior a la fusión
  (`/api/series` → 503) se actualizan al contrato real: datos de POWER con
  `kind = nasa_api`, y salto explícito si no hay red.

**Fallo de integridad corregido (antecedente: Antigravity 1 / D1)**

`src/etl/power.py` cargaba `tests/fixtures/real/` cuando NASA POWER fallaba y
`_build_provenance` la marcaba como `kind: "nasa_api"` con la URL y la fecha
reales. Eso es exactamente la sustitución silenciosa que `CONTRATOS.md` §3
prohíbe: con la red caída, el jurado habría visto un snapshot local presentado
como dato en vivo de la NASA.

Corrección:

- El respaldo local solo se activa con `ALLOW_FIXTURES=1` y se marca
  `kind = "fixture"`, `source = "... (copia local ...)"`,
  `citation = "... no dato en vivo"`.
- Sin red y con `ALLOW_FIXTURES=0`, el ETL **falla** (`UPSTREAM_TIMEOUT`) en vez
  de degradar en silencio.
- `fetch_power_point`/`fetch_power_regional` devuelven un quinto campo `origin`
  y la procedencia se construye a partir de él.

**Evidencia**

```
$ .venv/Scripts/python.exe -m pytest -q
158 passed, 54 warnings in 24.38s
```

```
$ python scripts/smoke_api.py http://127.0.0.1:8765
CHECK                            STATUS  TIME    DETAIL
-------------------------------  ------  ------  --------------------------------------------------
health                           PASS      12ms  HTTP 200 ai_mode=extractive
catalog/variables                PASS       1ms  HTTP 200 variables=25
analyze unknown variable -> 404  PASS      22ms  HTTP 404 code=VARIABLE_UNKNOWN
analyze no coords -> 400         PASS      15ms  HTTP 400
analyze Lima (G1)                PASS      99ms  HTTP 200 schema=analysis/2 provenance=nasa_api n_obs=540
analyze Lima (cache < 300ms)     PASS      26ms  HTTP 200
trendmap                         PASS      63ms  HTTP 200 cells=63
cases                            PASS      12ms  HTTP 503
report                           PASS      16ms  HTTP 200 bytes=4323
UI /                             PASS       1ms  HTTP 200 bytes=6023

10 passed · 0 skipped · 0 failed
```

**Falta / riesgos**

- `feature/ui` sin fusionar: los assets siguen siendo la UI v1.
- `/api/cases` en 503 hasta que Hermes 2 publique `data/cases/index.json`.
- El catálogo sale de la semilla (`catalog.source = "seed"`) hasta que Hermes 1
  mergee `variables.json` a esta rama.

---

## A5 — preparación del despliegue (14-nov-2026, 18:10 hora de Perú)

**Qué quedó** (A5 sigue sin URL: el login del hosting es del humano)

Dos fallos del `Dockerfile` que habrían roto el despliegue en cualquier nube:

1. **La imagen no llevaba los datos que la app lee en tiempo de ejecución.**
   `src/api/config.py` usa `data/cases/` (`/api/cases`), `data/atlas/`
   (`/api/atlas/{var}`) y `data/knowledge/` (corpus del RAG). Solo se copiaba
   `data/catalog/`. En la nube esos tres endpoints habrían dado 503 aunque en
   local funcionasen.
2. **Puerto fijo en 8000.** Fly, Render y Koyeb inyectan `PORT`; con un puerto
   fijo el health check falla y el despliegue se da por caído. Ahora el `CMD`
   usa `${PORT:-8080}` y el `HEALTHCHECK` lee la misma variable.

Además:

- **`.dockerignore`**: el contexto de construcción pasa de **218 MB a 19 MB**.
  Sin él, cada `fly deploy` subiría el `.venv` (196 MB) y el historial de git.
- **`fly.toml`**: app `earthtrend-detective`, región `iad`, `shared-cpu-1x` con
  512 MB, `auto_stop_machines = false` (un arranque en frío delante de un juez
  es una página rota), health check en `/api/health/live`.
- **Límite por IP detrás del proxy** (`src/api/main.py:_client_key`): usaba
  `request.client.host`, que en la nube es la IP del proxy, de modo que **todos
  los visitantes compartirían el cupo de 120 peticiones/min** y la demo se
  bloquearía sola. Ahora lee la primera entrada de `X-Forwarded-For`.

**Evidencia**

```
$ python -m pytest tests/api tests/test_system.py -q
48 passed, 51 warnings in 5.11s

$ verificación del COPY contra lo que la app lee
COPY en la imagen: ['requirements.txt', 'src/', 'data/catalog/', 'data/cases/', 'data/atlas/', 'data/knowledge/', 'scripts/smoke_api.py']
OK   data/catalog/      catálogo v2 (/api/catalog/variables)
OK   data/cases/        /api/cases (index.json)
OK   data/atlas/        /api/atlas/{var}
OK   data/knowledge/    corpus del RAG (src/detective/corpus.py)

$ IP tras el proxy
varios usuarios -> 1.2.3.4 | 5.6.7.8      (antes: ambos 172.18.0.1)
sin cabecera   -> 127.0.0.1
```

**Falta**

- **No he construido la imagen**: esta máquina no tiene Docker ni flyctl. El
  `Dockerfile` está verificado por lectura y por pruebas, no por `docker build`.
  La primera compilación real será en `fly deploy` (construye en remoto).
- URL pública: pendiente del login del humano.

**Cómo desplegarlo** (para el humano)

```bash
# 1. Instalar flyctl (una vez)
iwr https://fly.io/install.ps1 -useb | iex
#    luego cerrar y reabrir la terminal para que tome el PATH

# 2. Crear la cuenta e iniciar sesión (aquí no se puede automatizar)
fly auth signup        # o: fly auth login

# 3. Crear la app sin desplegar (usa el fly.toml de la raíz)
cd C:\Users\USER37\work\etd
fly launch --no-deploy --copy-config

# 4. Desplegar (construye en remoto; no hace falta Docker local)
fly deploy

# 5. Comprobar
fly status
curl https://earthtrend-detective.fly.dev/api/health/live
```

Coste: `shared-cpu-1x` de 512 MB en `iad` son ~$3,5/mes. Fly condona las
facturas por debajo de $5 en cuentas personales, así que en la práctica queda
en $0 mientras no se pase de esa cifra. Si el nombre `earthtrend-detective`
está cogido, `fly launch` pedirá otro y hay que actualizar `app` en `fly.toml`.

Alternativas si no se quiere dar tarjeta en Fly:

- **Koyeb** — un servicio free por organización, 512 MB / 0,1 vCPU, indefinido,
  pero se apaga a la hora sin tráfico.
- **Render** — 750 h/mes, se duerme a los 15 min y tarda ~1 min en despertar.

---

## Ronda 3 — tareas 1, 2 y 4 (14-nov-2026, 20:05 hora de Perú)

Rama@commit: feature/api · fusionado `origin/main` (32d07e2) sin conflicto.

### Tarea 1 — variables sin lugar (22:00)

`GET /api/analyze?variable_id=SEAICE_EXTENT_N` y `GISTEMP_TANOM` devolvían 400
«Faltan las coordenadas». La causa: `validation.point_or_bbox` exigía siempre
lat/lon, aunque los conectores de GISTEMP y NSIDC ya devuelven series globales o
hemisféricas sin coordenadas.

- `validation.is_placeless(card)` deduce del **conector** (`gistemp`,
  `nsidc_seaice`) si la variable se analiza sin lugar. No se decide por el id,
  para que una variable nueva del mismo conector herede la regla.
- Se responde en modo `global` y las variables locales siguen exigiendo
  coordenadas (`T2M` sin coords sigue siendo 400).
- Añadido a `smoke_api.py`, junto con el resto de comprobaciones nuevas.

### Tarea 2 — `place`, `variable_id` en la rejilla y `planned` (22:00)

1. **`place` → `region.name`.** `/api/analyze`, `/api/series` y `/api/report`
   aceptan `place` (el nombre que devuelve `/api/geocode`) y lo escriben en
   `region.name`, que llega vacío del ETL. Ahora `answers.where` dice
   «Observed in Lima, Peru» y no «Observado en None» (§2.7). Para las variables
   sin lugar se usa el nombre de la propia variable del catálogo
   («Arctic sea ice extent»), nunca una ubicación inventada.
   La clave de caché incluye `place`: dos nombres del mismo punto son respuestas
   distintas.
2. **`/api/trendmap` devolvía `variable_id: "VAR"`.** La rejilla del ETL no
   trae ese campo y el motor ponía un relleno. La API —que sí conoce el id
   pedido— lo inyecta antes de llamar al motor. Arreglado en mi carril, sin
   depender de que antigravity-2 cambie el motor.
3. **`/api/catalog/variables` publica `available` y `planned`.** Se deducen del
   conector: `power`, `gistemp` y `nsidc_seaice` son servibles; `giovanni_csv`
   es `planned` y nunca `available` (regla 16, condiciones de claude-omni-1b).
   Si el catálogo ya los declara, se respeta su valor.

### Tarea 4 — `scripts/gate.py` (23:30, adelantada)

Un comando que corre la suite, el smoke, `validate_datasets.py` y
`validate_knowledge.py`, y sale con código ≠ 0 si algo falla.

- El smoke levanta su propio uvicorn en un puerto libre y lo detiene al acabar:
  no depende de que algo esté corriendo.
- `validate_datasets.py` solo entiende `timeseries/2`, así que el gate filtra
  los congelados por `schema`. Pasarle `analysis.json`, `case.json` o los
  `trendmap/2` del atlas producía 13 fallos de forma que no eran del contenido.
- Los validadores de conocimiento van con `--offline` por defecto: la puerta no
  debe caerse porque GitHub no responda, y las URLs ya se validan aparte.

### Evidencia

```
$ python -m pytest tests/api/test_contract.py -q
30 passed, 63 warnings in 23.50s

$ python -m pytest -q            # regla 14, suite entera
223 passed, 1 failed, 9 skipped in 141.26s
  FAILED tests/stats/test_trend_engine.py::test_published_nasa_benchmarks
  (causa: −9999 del hielo marino, carril de antigravity-1)

$ python scripts/smoke_api.py http://127.0.0.1:8765
CHECK                                   STATUS  TIME    DETAIL
health                                  PASS      11ms  HTTP 200 ai_mode=extractive
catalog/variables                       PASS       1ms  HTTP 200 variables=15
analyze unknown variable -> 404         PASS       1ms  HTTP 404 code=VARIABLE_UNKNOWN
analyze no coords -> 400                PASS       0ms  HTTP 400
analyze Lima (G1)                       PASS      59ms  HTTP 200 schema=analysis/2 provenance=nasa_api n_obs=540
analyze Lima (cache < 300ms)            PASS       1ms  HTTP 200 1ms
trendmap                                PASS      23ms  HTTP 200 cells=63
cases                                   PASS       1ms  HTTP 200
report                                  PASS       1ms  HTTP 200 bytes=4358
analyze placeless variable (no coords)  PASS      90ms  GISTEMP_TANOM:Global (all GISTEMP land+ocean cells) SEAICE_EXTENT_N:Arctic sea ice extent SEAICE_EXTENT_S:Antarctic sea ice extent
analyze place -> region name            PASS      79ms  HTTP 200 where='Observed in Lima, Peru.'
trendmap variable_id echo               PASS       2ms  HTTP 200 variable_id='T2M'
catalog availability flags              PASS       2ms  HTTP 200 n=15 available=15 planned=0
UI /                                    PASS      16ms  HTTP 200 bytes=17598

14 passed · 0 skipped · 0 failed
```

```
$ python scripts/gate.py --skip-suite --offline
OK    smoke_api            exit=0      9.7s
OK    validate_datasets    exit=0      0.1s     (5 series congeladas)
OK    validate_knowledge   exit=0      0.1s     (15 variables, 168 documentos)
PUERTA ABIERTA: todo en verde

$ python scripts/gate.py --offline      # con suite
FALLA  pytest               exit=1    141.4s   (la roja ajena de arriba)
OK    smoke_api / validate_datasets / validate_knowledge
PUERTA CERRADA: fallaron pytest
```

### Falta

- **URL pública**: sigue bloqueada por el login del humano en Fly. La imagen y
  `fly.toml` están listos desde la ronda anterior; no he podido ejecutar
  `fly deploy` porque no hay sesión (`flyctl auth whoami` → no access token).
- 5 pruebas nuevas en `tests/api/test_contract.py`.

---

## Ronda 4 — tareas 1, 2 y 3 (15-nov-2026, 01:30 hora de Perú)

Rama@commit: feature/api · fusionado `origin/main` (55869e8) sin conflicto.

### Tarea 1 — regla 19: una `planned` nunca se analiza (01:30)

- **`VARIABLE_PLANNED` (HTTP 409)**, código nuevo en `src/api/errors.py` con
  mensaje bilingüe. El texto dice qué variable es, que está planificada y cómo
  cargarla («descarga su CSV de Giovanni y súbelo en *Analizar un CSV*»), en el
  idioma pedido.
- **`catalog.is_planned(card)`**: respeta `planned`/`available` si el catálogo
  los declara y, si no, lo deduce del conector (`power`, `gistemp`,
  `nsidc_seaice` son servibles; el resto —Giovanni— no). Así funciona hoy,
  antes de que claude-omni-1b añada las fichas `planned`.
- **`validation.check_analyzable`** se usa en `/api/analyze`, `/api/series`,
  `/api/report` y `/api/trendmap`.
- **`/api/catalog/variables` publica las `planned` aparte**:
  `{catalog, variables, planned}` con `catalog.n_available` y `n_planned`. Nunca
  se cuentan como disponibles (regla 16).
- Añadido a `smoke_api.py` y con 2 pruebas de contrato que inyectan una ficha
  `planned` y comprueban el 409 y el reparto del catálogo.

### Tarea 2 — versiones fijadas, entorno limpio y 20 simultáneas (04:00, adelantada)

**`requirements.txt` con `==`**, las 10 del entorno que pasa la suite:

```
fastapi==0.163.0      starlette==1.10.0        uvicorn==0.54.0
pydantic==2.14.3      python-multipart==0.0.33 requests==2.34.2
certifi==2026.10.23   numpy==2.5.4             scipy==1.18.1
pymannkendall==1.4.3
```

`starlette` y `certifi` se fijan aunque lleguen como dependencias: el código
importa `starlette` directamente, y `requests` usa `certifi` para TLS.

**Arranque en entorno limpio**: venv nuevo (`C:\Users\USER37\cleanenv`, Python
3.12.14, pip 25.0.1), `pip install -r requirements.txt` y arranque con las
variables del `Dockerfile` (`AI_MODE=extractive`, `ALLOW_FIXTURES=0`). El smoke
completo pasa contra ese servidor: **15/15**.

**20 peticiones simultáneas** (`scripts/load_test.py`, IP distinta por petición
para medir concurrencia y no el cupo de 120/min):

```
20 simultáneas, misma clave (caché)
  códigos              : {200: 20}
  total (pared)        : 55 ms
  latencia min/med/max : 7 / 43 / 50 ms
  throughput           : 366,9 req/s

20 simultáneas, 20 claves distintas (motor sin caché)
  códigos              : {200: 20}
  total (pared)        : 6 807 ms
  latencia min/med/max : 20 / 3 703 / 6 803 ms
  throughput           : 2,9 req/s
```

Lectura honesta: **no se pierde ninguna petición** (20/20 HTTP 200 en los dos
casos) y la caché absorbe bien. Pero 20 análisis distintos a la vez tardan
~3,7 s de mediana porque el proceso es de un solo worker y el motor es CPU puro.
Con la caché caliente —el caso normal en una demo, donde los jueces abren los
mismos casos— la respuesta es de decenas de milisegundos. Si el jurado pulsa 20
puntos distintos a la vez, espera unos segundos; no hay error ni caída.

### Tarea 3 — `scripts/gate.py` con las tres comprobaciones nuevas (09:00, adelantada)

1. **`planned_not_analyzable`** — regla 19: comprueba que ninguna `planned` se
   publica como disponible y que la API responde `VARIABLE_PLANNED` a cada una.
   Funciona con `--base URL` o en proceso (offline).
2. **`case_physical_ranges`** — regla 12: recorre los `series.json` de
   `data/cases/` con `src/etl/validate.py` (que es la autoridad de los rangos) y
   además revisa cada valor contra `PHYSICAL_RANGES`. **Hoy falla**, y hace bien:
   `arctic-seaice` y `antarctic-seaice` siguen con −9999 en `data[109]` y
   `data[110]` (1987-12 y 1988-01). Es el carril de hermes-2.
3. **`no_secrets`** — regla 23: busca la forma de un secreto (tokens de GitHub,
   AWS, HF, Google, claves privadas) en el árbol versionado, no la palabra
   «token». Verificado con un positivo de prueba (lo detecta) y con el
   repositorio (0 hallazgos en 294 archivos).

```
$ python scripts/gate.py --skip-suite --offline
OK    smoke_api               exit=0     16.2s
OK    validate_knowledge      exit=0      0.2s
OK    planned_not_analyzable  exit=0      0.2s
OK    no_secrets              exit=0      1.1s
FALLA validate_datasets      exit=1      0.2s   ← −9999 del hielo (hermes-2)
FALLA case_physical_ranges   exit=1      0.1s   ← el mismo −9999, detectado por mi comprobación
PUERTA CERRADA
```

### Suite completa (regla 14)

```
$ python -m pytest -q
237 passed, 3 failed, 9 skipped in 201.99s
  FAILED tests/detective/test_pipeline.py::test_pipeline_offline[what is soil moisture?-en-GWETTOP]
  FAILED tests/detective/test_pipeline.py::test_missing_variable_is_declared_not_substituted[...]
  FAILED tests/ml/test_lora_real.py::test_plan_with_lora_missing_adapter_raises_error
```

Las tres rojas son ajenas: dos de `src/detective` (carril claude-omni-2) y una
de `src/ml/serve.py` (carril antigravity-2). **No integro en `main`** (regla 25:
solo con la suite entera sin rojas).

### Falta

- **URL pública**: la despliega el arquitecto desde el PC1 en Railway. En cuanto
  exista, `smoke_api.py` contra ella a las 12:00, 16:00 y 19:00.
- El respaldo estático (A6) ya no es mío: pasó a claude-omni-3a.

---

## Ronda 5 — clon limpio, LICENSE y contrato (15-nov-2026, 07:35 hora de Perú)

Rama@commit: feature/api · fusionado `origin/integracion/ronda5` (base de la ronda) sin conflicto.

### Revisión de los tres cambios del arquitecto en mi carril (§5)

**No contradicen el contrato.** Los revisé uno por uno:

1. **`GET /api/cases/{id}`** devuelve `{case, analysis}` con el `analysis.json`
   guardado y **no recalcula**. Si el archivo falta o no es `analysis/2`, responde
   con un error del contrato en vez de sustituirlo por otro análisis: eso es
   justo lo que la regla de oro pide. Verificado en vivo: `lima-t2m` → 200 con
   `analysis/2` y `SIGNIFICANT`; `no-such-case` → 404 `NOT_FOUND`.
2. **El cargador lee la clave `planned` del catálogo.** Era un fallo real mío:
   mis pruebas de la regla 19 inyectaban una tarjeta fabricada y pasaban aunque
   la API en vivo publicara 0 `planned` (exactamente lo que la regla 28 prohíbe).
   Ahora publica **15 disponibles + 10 planned** y `MODIS_NDVI` da 409 en vez de
   404. Lo compruebo contra el archivo real en el smoke.
3. **Mensaje en inglés de `VARIABLE_PLANNED`** con el nombre en inglés. Correcto:
   usaba `names.es` primero y en inglés salía el nombre en español.

### Tarea 2 — `LICENSE` (antes de las 08:00)

`LICENSE` con MIT, «Copyright (c) 2026 EarthTrend Detective team».

En el README, apartado **«Licence and third-party notices»** con las fuentes de
datos y su cita (POWER, GISTEMP v4, NSIDC Sea Ice Index v4, Giovanni/GES DISC),
las librerías de la interfaz (Leaflet BSD-2-Clause, Chart.js MIT, Schibsted
Grotesk y Source Serif 4 bajo OFL 1.1), las teselas (NASA GIBS dominio público,
OpenStreetMap ODbL, ambas atribuidas en el mapa) y las de Python.

**Las licencias de los paquetes no las puse de memoria**: leí el `LICENSE` que
trae cada paquete instalado. Resultado: FastAPI MIT; Starlette, Uvicorn, NumPy y
SciPy **BSD-3-Clause** (había puesto BSD-3 solo en NumPy y SciPy); pymannkendall
MIT. Leaflet y Chart.js, verificados en su repositorio.

### Tarea 3 — `GET /api/cases/{id}` en el contrato y en el smoke (antes de las 09:00)

- Documentada en `docs/CONTRATOS.md` §7.
- Dos comprobaciones nuevas en `smoke_api.py`: 200 con `analysis/2` para un caso
  real, 404 `NOT_FOUND` para un id inventado.

**De paso corregí un fallo mío en el smoke**: «catalog availability flags»
calculaba `planned = len(variables) - available`, que da 0 porque las planned ya
no están en esa lista. Ahora lee la lista `planned` real y dice 15 + 10.

### Tarea 1 — clon limpio (08:00)

**Linux o WSL: imposible en este equipo.** `wsl --status` responde «no está
instalado» y no hay distros. Instalarlo pide administrador y reinicio, y la
decisión no es mía. Queda en ROTO / NO HECHO.

Hice el clon limpio **en Windows**, que es lo único que este equipo permite, y
seguí el README al pie de la letra:

```
git clone … && git checkout feature/api        -> 60b293b
python -m venv .venv                           -> Python 3.12.14
pip install -r requirements.txt                -> 6 paquetes, versiones fijadas
python -m uvicorn src.api.main:app --port 8791 -> health 200,
                                                  etl=True stats=True detective=True
pip install -r requirements-dev.txt            -> pytest 9.2.0, httpx 0.28.1
python -m pytest -q                            -> 275 passed, 10 skipped (5:51)
python scripts/smoke_api.py http://127.0.0.1:8791 -> 17 passed · 0 skipped · 0 failed
python scripts/validate_datasets.py data/cases/*/series.json -> 7/7 válidos
python scripts/validate_knowledge.py           -> 15 disponibles + 10 planned,
                                                  168 documentos, sin fallos
python scripts/gate.py --base … --skip-suite --offline -> PUERTA ABIERTA (6/6)
```

Coincide con lo que midió el arquitecto en el PC1 (275 / 0 / 10).

**Hallazgo del entorno, que sí merece constar**: en este PC `python` del `PATH`
es el alias de Microsoft Store y no ejecuta nada. Alguien siguiendo el README en
Windows se para en el primer comando con un mensaje que no explica nada («Python
was not found»). Añadí al README el requisito de Python 3.12 y la nota del alias;
es documentación, no código.

### Tarea 4 — Docker (10:00)

**Imposible en este equipo**: `docker` no está instalado. Queda en ROTO /
NO HECHO. El `Dockerfile` sí copia `data/cases/` (lo verifiqué en la ronda 3), así
que `/api/cases/lima-t2m` debería responder 200 dentro del contenedor, pero no
tengo cómo demostrarlo aquí.

### Suite completa (regla 14)

```
$ python -m pytest -q
275 passed, 10 skipped in 351.14s
```

**Cero rojas.** No integro en `main` porque el arquitecto no me lo ha pedido
(regla 30: el suplente solo actúa si el humano se lo pide).

### Pendiente por hora

- **10:00** — `gate.py` completo en G3.
- **12:00, 16:00, 19:00** — smoke contra la URL pública (la del respaldo ya vive;
  la aplicación completa espera a Railway).
- **18:00** — `gate.py` en G4.
- **Tarea 6** (README final, que era de claude-omni-1b): solo pasa a mí si a las
  10:00 no hay commit suyo. A las 07:31 su rama no tenía nada nuevo desde ayer a
  las 20:26.

---

# Reporte final — Ronda 6 (15-nov-2026, 10:45 hora de Perú)

Base: `origin/main@e67873e`, clonado de cero desde GitHub. No hubo cambios de
código en mi carril esta ronda: `main` está en congelación (regla 31).

## Tarea 1 — `LICENSE` y `requirements.txt` en un clon limpio

### Lo que pide el checklist

**`LICENSE`** — presente en `main@e67873e`, MIT:

```
$ ls LICENSE && head -3 LICENSE
MIT License

Copyright (c) 2026 EarthTrend Detective team
```

**`requirements.txt`** — 10 dependencias, todas con `==`:

```
fastapi==0.163.0      starlette==1.10.0     uvicorn==0.54.0
pydantic==2.14.3      python-multipart==0.0.33   requests==2.34.2
certifi==2026.10.23   numpy==2.5.4          scipy==1.18.1
pymannkendall==1.4.3
```

**`requirements-dev.txt`** — `-r requirements.txt` + `pytest==9.2.0` +
`httpx==0.28.1`. Lo correcto: el despliegue no necesita pytest.

Instaladas en un venv nuevo, las 10 salen exactamente en la versión fijada (lo
comprobé leyendo `importlib.metadata` después de instalar, no el archivo).

### Hallazgo: el README no se podía seguir en un clon limpio

En un clon de `main@e67873e`, con venv nuevo y solo `requirements-dev.txt`:

```
$ python -m pytest -q
ERROR scripts/test_ui_r5.py
!!! Interrupted: 1 error during collection !!!
E   ModuleNotFoundError: No module named 'playwright'
```

**Causa.** `scripts/test_ui_r5.py` es un *script* de verificación con Playwright
(de claude-omni-1; se ejecuta a mano con `python scripts/test_ui_r5.py`, como él
documenta en su reporte), pero se llama `test_*`, así que pytest lo recoge,
intenta importar `playwright` y **aborta toda la colección**. No está en ningún
`requirements`: correcto, porque Playwright con su navegador son ~50 MB que solo
necesita quien hace capturas.

**Efecto en la entrega.** El primer comando de comprobación del README falla en
cualquier máquina limpia, y `gate.py` sin `--skip-suite` cierra la puerta:

```
$ python scripts/gate.py --base … --offline        # clon de main
FALLA  pytest              exit=2      1.4s
OK     smoke_api, validate_datasets, validate_knowledge,
       planned_not_analyzable, case_physical_ranges, no_secrets
PUERTA CERRADA: fallaron pytest
```

El arquitecto no lo vio porque midió el gate con `--skip-suite` (§1 de
`RONDA_6.md` dice `gate.py --offline`, pero el resultado que pegó no incluye la
línea de pytest).

**Arreglo** (`fix/pytest-testpaths@3a61b8e`, una línea en `pytest.ini`):

```ini
testpaths = tests
```

`scripts/` queda fuera de la recolección y el script sigue funcionando a mano.
No toca código, no toca `src/`, no cambia ninguna prueba.

### Verificación del arreglo, en un clon limpio desde cero

```
$ git clone -b fix/pytest-testpaths … && python -m venv .venv
$ pip install -r requirements-dev.txt
$ python -m uvicorn src.api.main:app --port 8802      -> health 200
      ai_mode=extractive etl=True stats=True detective=True
$ python -m pytest -q
287 passed, 10 skipped in 494.73s
$ python scripts/gate.py --base http://127.0.0.1:8802 --offline
OK    pytest                 exit=0    490.9s
OK    smoke_api              exit=0     18.6s
OK    validate_datasets      exit=0      0.2s
OK    validate_knowledge     exit=0      0.2s
OK    planned_not_analyzable exit=0      0.0s
OK    case_physical_ranges   exit=0      0.1s
OK    no_secrets             exit=0      0.8s
PUERTA ABIERTA: todo en verde
```

### Una diferencia con la cifra del arquitecto, dicha tal cual

Él midió **288 passed, 9 skipped**; yo obtengo **287 passed, 10 skipped**. El
total coincide (297), así que **una prueba que en el PC1 pasa, aquí se omite**.
No la he identificado con certeza y no la voy a adivinar: lo más probable es una
que depende de red o de GPU. Ninguna falla en ninguno de los dos equipos.

### Resto de comprobaciones del README (clon limpio de `main`)

```
smoke_api.py http://127.0.0.1:8801     -> 17 passed · 0 skipped · 0 failed
validate_datasets.py data/cases/*/series.json -> 7/7 válidos
validate_knowledge.py                  -> 15 disponibles + 10 planned, 168 docs, OK
```

## Tarea 2 — Railway / Docker

`docker` no está instalado en este equipo, así que `docker build` no es
ejecutable aquí y no lo puedo demostrar. Queda en ROTO / NO HECHO, como pedí en
la ronda anterior.

Lo que sí puedo afirmar, por lectura del `Dockerfile` y por el árbol de `main`:
la imagen copia `src/`, `data/catalog/`, `data/cases/`, `data/atlas/` y
`data/knowledge/`; toma el puerto de `$PORT`; y no incluye `torch` ni Playwright.
La configuración de Railway/Fly sigue lista para el momento en que el humano
inicie sesión.

## Lo que hay que hacer con esto

`main` está congelado y la regla 30 dice que no muevo `main` por mi cuenta. La
rama **`fix/pytest-testpaths@3a61b8e`** está empujada y es de una línea. Si el
arquitecto la fusiona antes de la entrega, el README y el gate funcionan en
cualquier máquina; si no, quien clonе el repositorio se para en el primer
`pytest -q` y `gate.py` completo cierra la puerta.

No he tocado `main`, ningún archivo de `src/`, ni ninguna prueba existente.
