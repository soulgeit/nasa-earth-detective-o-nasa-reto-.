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
