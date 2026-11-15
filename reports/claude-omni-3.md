<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-3 — 2026-11-14 17:57 (hora de Perú)
Rama@commit: feature/api@024a24e (fast-forward de origin/main) · empujado: sí
VERIFICADO: fusión `origin/main` en `feature/api` → avance limpio, sin conflicto → `pytest -q` 196 passed, 2 failed, 9 skipped
VERIFICADO: smoke integrado → `smoke_api.py http://127.0.0.1:8765` → 10 passed · 0 skipped · 0 failed (analyze Lima 838 ms, trendmap 63 celdas, UI 17 307 B)
VERIFICADO: honestidad de la procedencia y motor v2 → `pytest tests/test_system.py -q` → 7 passed in 1.62s
ESCRITO (sin ejecutar de punta a punta): nada pendiente en mi carril
ROTO / NO HECHO: A5 sin desplegar (falta tu login en Fly; `Dockerfile`/`fly.toml` listos y verificados por pruebas, no por `docker build`); A6 sin regenerar; `/api/cases` en 503
Siguiente paso: `fly launch --no-deploy` + `fly deploy` (comandos en §A5), después `smoke_api.py` contra la URL
Necesito de: humano → iniciar sesión en el hosting (Railway/GitHub Pages) y pasarme la URL; Hermes 2 → `data/cases/index.json`
Avisos para otros carriles: las 2 pruebas rojas son de `tests/detective/test_pipeline.py` (`MODIS_NDVI`, Claude Omni 2), no de la API; `answers.where` dice «None» y `region.name` viene `null` del ETL (carril de Antigravity 1)
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
