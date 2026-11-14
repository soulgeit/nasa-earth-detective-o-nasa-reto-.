# Claude Omni 3 — API v2 y despliegue

Carril: `feature/api` · Carpetas: `src/api/`, `tests/api/`, `Dockerfile`, `scripts/smoke_api.py`

---

## A1 — LISTO (14-nov-2026, 13:30 hora de Perú)

Rama@commit: feature/api@<pendiente de commit>

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
