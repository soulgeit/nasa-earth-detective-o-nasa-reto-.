# CONTRATOS v2 — fuente de verdad entre agentes

Sustituye a la sección 3 de `ARCHITECTURE.md`. Si algo aquí choca con otro documento, manda este.
Cambios: solo el arquitecto, a propuesta escrita en un reporte.

## 1. Carriles (quién toca qué)

| Agente | Rama | Carpetas propias |
|---|---|---|
| cfable (arquitecto) | `main` | `docs/`, `prompts/`, `README.md`, `TASKS.md`, `scripts/gate.py`, `tests/test_contracts.py` |
| Antigravity 1 | `feature/data-pipeline` | `src/etl/`, `scripts/validate_datasets.py`, `tests/etl/` |
| Antigravity 2 | `feature/stats` (fase 2: `feature/lora`) | `src/stats/`, `tests/stats/`, `src/ml/`, `docs/VALIDACION_ESTADISTICA.md` |
| Claude Omni 1 | `feature/ui` | `src/ui/` |
| Claude Omni 2 | `feature/wizard` | `src/detective/`, `tests/detective/`, `docs/EVAL_IA.md` (sección RAG) |
| Claude Omni 3 | `feature/api` | `src/api/`, `tests/api/`, `Dockerfile`, `scripts/smoke_api.py` |
| Hermes 1 | `feature/catalog` | `data/catalog/`, `data/knowledge/`, `scripts/validate_knowledge.py` |
| Hermes 2 | `feature/scrapes` | `data/cases/`, `data/atlas/`, `data/lora/`, `scripts/build_*.py`, `scripts/freeze_case.py` |

Archivos comunes (`requirements.txt`, `.env.example`, `docs/AI_USE_LOG.md`, `reports/<nombre>.md`): se **añaden líneas**, no se reordenan ni se borran las de otros.
Se borran en la v2: `data/processed/*.json` (sintéticos), `generate_synthetic_timeseries` y `calculateStatsClientSide`.

## 2. Identificadores

- `variable_id`: MAYÚSCULAS con guion bajo, estable. Los de POWER son el nombre del parámetro (`T2M`). Semilla en `data/catalog/variables.seed.json`.
- Fechas mensuales: `"YYYY-MM"`. Tiempo para regresiones: año decimal `año + (mes - 0.5) / 12`.
- `bbox`: `[oeste, sur, este, norte]` en grados. Longitud de −180 a 180.
- Idioma: `lang` ∈ `es | en`.

## 3. TimeSeries v2

```json
{
  "schema": "timeseries/2",
  "variable_id": "T2M",
  "unit": "°C",
  "cadence": "monthly",
  "region": {"kind": "point", "name": "Lima, Peru", "lat": -12.05, "lon": -77.03, "bbox": null},
  "aggregation": "point",
  "data": [{"date": "1981-01", "value": 18.41}, {"date": "1981-02", "value": null}],
  "provenance": {
    "kind": "nasa_api",
    "source": "NASA POWER v2.10.0",
    "underlying": "MERRA-2",
    "request_url": "https://power.larc.nasa.gov/api/temporal/monthly/point?...",
    "retrieved_at": "2026-11-14T17:22:00Z",
    "sha256": "<hash de la respuesta cruda>",
    "native_resolution": "0.5° x 0.625°",
    "citation": "texto de cita que pide la fuente"
  }
}
```

- `region.kind` ∈ `point | bbox | named` · `aggregation` ∈ `point | area_mean_coslat`.
- `provenance.kind` ∈ `nasa_api | nasa_file | user_upload | fixture`. `fixture` solo existe en `tests/`.
  La API no sirve `fixture` salvo `ALLOW_FIXTURES=1`; la UI muestra un aviso rojo si `kind` no es `nasa_*` ni `user_upload`.
- Faltantes: `value: null` (nunca −999, nunca 0, nunca interpolado).

## 4. AnalysisResult v2

```json
{
  "schema": "analysis/2",
  "variable": { "...tarjeta del catálogo (la añade la API)..." },
  "region": { "...igual que TimeSeries..." },
  "period": {"start": "1981-01", "end": "2025-12", "years": 45.0, "n_obs": 540, "n_missing": 0, "coverage": 1.0},
  "method": {
    "deseasonalized": true, "climatology": "media mensual del periodo analizado", "alpha": 0.05,
    "autocorrelation": {"lag1": 0.41, "n_eff": 226},
    "references": ["Mann 1945", "Kendall 1975", "Sen 1968", "Hamed & Rao 1998", "Santer et al. 2000", "Weatherhead et al. 1998"]
  },
  "trend": {
    "direction": "up",
    "sen_slope_per_decade": 0.31, "sen_ci95_per_decade": [0.22, 0.40],
    "ols_slope_per_decade": 0.30, "ols_ci95_per_decade": [0.19, 0.41], "r_squared": 0.28,
    "total_change": 1.40, "percent_per_decade": null
  },
  "tests": {
    "mann_kendall": {"tau": 0.25, "z": 6.1, "p_value": 1.1e-9, "p_value_autocorr": 3.0e-4, "correction": "hamed_rao"},
    "mann_kendall_annual": {"n": 45, "tau": 0.52, "p_value": 4.0e-7},
    "t_test_ols": {"t": 4.9, "df": 224, "p_value": 1.8e-6, "adjusted_for_autocorrelation": true}
  },
  "significance": {"is_significant": true, "verdict_code": "SIGNIFICANT_STRONG", "level": "p<0.01", "tests_agree": true},
  "detectability": {"years_needed": 14.2, "years_available": 45.0, "more_years_needed": 0.0, "method": "Weatherhead et al. 1998"},
  "series": {
    "dates": [], "raw": [], "climatology": [], "anomalies": [],
    "trend_line": [], "trend_ci_low": [], "trend_ci_high": [],
    "annual": [{"year": 1981, "value": 18.9, "n_months": 12}]
  },
  "answers": {
    "what": {"es": "...", "en": "..."}, "where": {"es": "...", "en": "..."},
    "how_much": {"es": "...", "en": "..."}, "significant": {"es": "...", "en": "..."},
    "detectability": {"es": "...", "en": "..."}
  },
  "warnings": ["HIGH_AUTOCORRELATION"],
  "provenance": { "...copiado del TimeSeries..." }
}
```

- `verdict_code` ∈ `SIGNIFICANT_STRONG | SIGNIFICANT | SUGGESTIVE | NOT_SIGNIFICANT | INSUFFICIENT_DATA`.
- `percent_per_decade` solo si la tarjeta dice `ratio_scale: true` (nunca para temperaturas en °C).
- `warnings` ∈ `SHORT_RECORD | LOW_COVERAGE | HIGH_AUTOCORRELATION | SOURCE_SPLICE | TESTS_DISAGREE | REANALYSIS_CAVEAT`.
- `answers` son plantillas deterministas (sin modelo de lenguaje). Nunca afirman causa: «compatible con», no «demuestra».

## 5. TrendMap v2

```json
{
  "schema": "trendmap/2", "variable_id": "T2M", "unit_per_decade": "°C/década",
  "bbox": [-82, -7, -78, -3], "lats": [], "lons": [],
  "slope_per_decade": [[]], "p_value": [[]], "significant_fdr": [[]],
  "fdr_q": 0.10, "n_cells": 63, "n_significant": 41,
  "period": {"start": "1981-01", "end": "2025-12"},
  "summary": {"share_up_significant": 0.65, "share_down_significant": 0.0},
  "provenance": {}
}
```

Matrices `[lat][lon]`, `null` donde no hay dato. Significancia por celda con control FDR (Benjamini-Hochberg; Wilks 2016).

## 6. Firmas Python (lo que cada módulo expone)

```python
# src/etl/registry.py  — Antigravity 1
def get_series(variable_id, *, lat=None, lon=None, bbox=None, start=None, end=None) -> dict   # TimeSeries v2
def get_grid(variable_id, bbox, *, start=None, end=None) -> dict   # {"lats","lons","dates","values"[t][lat][lon],"unit","provenance"}
def parse_giovanni_csv(text: str, variable_id: str | None = None) -> dict                      # TimeSeries v2, kind=user_upload
class DataUnavailable(Exception): code: str   # VARIABLE_UNKNOWN | OUT_OF_COVERAGE | UPSTREAM_ERROR | UPSTREAM_TIMEOUT | BBOX_TOO_LARGE

# src/stats/trend_engine.py  — Antigravity 2
def analyze_series(ts: dict, *, alpha=0.05, ratio_scale=False, homogeneous_since=None) -> dict  # AnalysisResult v2 sin "variable"
def analyze_grid(grid: dict, *, alpha=0.05, fdr_q=0.10) -> dict                                  # TrendMap v2
def compare(a: dict, b: dict) -> dict   # {"opposite": bool, "difference_significant": bool, "z": float, "statement": {"es","en"}}

# src/detective/  — Claude Omni 2
def retrieve(query: str, *, lang="es", k=6, types=None) -> list[dict]     # documentos con score y url
def plan(question: str, *, lang="es") -> dict                              # InvestigationPlan
def scout(lat: float, lon: float, *, lang="es") -> dict                    # candidatas para ese lugar, con fuentes
def explain(analysis: dict, *, level="school", lang="es") -> dict          # {"text","citations","guard","mode"}
def geocode(q: str) -> list[dict]                                          # [{"name","country","lat","lon","bbox"}]
```

## 7. API HTTP (Claude Omni 3) — prefijo `/api`

| Método y ruta | Entrada | Salida |
|---|---|---|
| `GET /health` | — | `{status, version, ai_mode, sources_up}` |
| `GET /catalog/variables?lang=` | — | tarjetas |
| `GET /catalog/regions` · `GET /cases` | — | regiones y casos congelados |
| `GET /cases/{id}` | id de `GET /cases` | `{case, analysis}`: la ficha y su `analysis/2` guardado, sin recalcular; `404 NOT_FOUND` si el id no existe |
| `GET /geocode?q=` | texto | `{"places": [{"name","country","lat","lon","bbox","population","match_score"}]}` |
| `GET /series` | `variable_id` + (`lat`,`lon`) o `bbox` + `start`,`end` | TimeSeries v2 |
| `GET /analyze` | igual | AnalysisResult v2 |
| `POST /analyze/upload` | CSV de Giovanni (multipart) | AnalysisResult v2 |
| `GET /trendmap` | `variable_id`, `bbox` | TrendMap v2 |
| `GET /compare` | `variable_id`, `a=lat,lon`, `b=lat,lon` | dos análisis + `compare` |
| `GET /atlas/{variable_id}` | — | TrendMap v2 global precalculado |
| `POST /ai/plan` · `/ai/scout` · `/ai/explain` | ver §6 | ver §6 |
| `GET /report` | igual que `/analyze` + `lang` | HTML imprimible |

Errores: JSON `{"error": {"code": "...", "message": {"es","en"}, "hint": "..."}}` con 400/404/422/502/504. Códigos de §6 más `INSUFFICIENT_DATA`, `AI_UNAVAILABLE`.

## 8. Catálogo (Hermes 1) — `data/catalog/variables.json`

```json
{
  "id": "T2M", "connector": "power", "connector_param": "T2M",
  "names": {"es": "Temperatura del aire a 2 m", "en": "Air temperature at 2 m"},
  "simple_definition": {"es": "...", "en": "..."},
  "unit": "°C", "ratio_scale": false, "sphere": "atmosphere",
  "source": {"model_or_mission": "MERRA-2", "instrument": null, "via": "NASA POWER",
             "challenge_named_source": "MERRA-2", "native_resolution": "0.5° x 0.625°",
             "start": "1981-01", "homogeneous_since": null, "doi": null, "url": "..."},
  "what_up_means": {"es": "...", "en": "..."}, "what_down_means": {"es": "...", "en": "..."},
  "typical_drivers": {"es": ["..."], "en": ["..."]},
  "caveats": {"es": ["..."], "en": ["..."]},
  "keywords": {"es": ["calor", "temperatura"], "en": ["heat", "temperature"]},
  "verified": {"by": "hermes-1", "at": "2026-11-14", "evidence_url": "..."}
}
```

`sphere` ∈ `atmosphere | land | ocean | cryosphere | biosphere`. `challenge_named_source` ∈ `MODIS | OMI | AIRS | GPM | MERRA-2 | GLDAS | other`.
`doi` y `url` solo si se abrieron y comprobaron; si no, `null`.

## 9. Documento de conocimiento (Hermes 1) — `data/knowledge/docs.jsonl`

```json
{"id": "eo-aral-2024", "type": "nasa_article", "title": "...", "url": "https://...", "publisher": "NASA Earth Observatory",
 "date": "2024-08-01", "lang": "en", "text": "<300-1200 caracteres extraídos de la página>",
 "variables": ["PRECTOTCORR"], "biomes": ["desert"], "license": "NASA (dominio público)",
 "fetched_at": "2026-11-14T19:00:00Z", "sha256": "<hash del html>"}
```

`type` ∈ `variable_card | biome_profile | region_note | nasa_article | paper_abstract | method_note | glossary`.

## 10. InvestigationPlan y dataset LoRA

```json
{"intent": "investigate", "variable_ids": ["PRECTOTCORR"], "place": "Piura", "place_b": null,
 "start_year": null, "end_year": null, "last_n_years": null, "hypothesis": "down", "lang": "es"}
```

- `intent` ∈ `investigate | compare | define | out_of_scope | no_match` · `hypothesis` ∈ `up | down | unknown`.
- `variable_ids` ⊆ candidatas dadas. `place` es **texto copiado de la pregunta** (o `null`); las coordenadas las pone `geocode`.
- Dataset (`data/lora/{train,val,test}.jsonl`), una línea por ejemplo:

```json
{"messages": [{"role": "system", "content": "<SYSTEM fijo, en data/lora/system_prompt.txt>"},
              {"role": "user", "content": "QUESTION: ...\nCANDIDATES:\n- T2M: ...\n- PRECTOTCORR: ..."},
              {"role": "assistant", "content": "{\"intent\": ...}"}],
 "meta": {"lang": "es", "intent": "investigate", "gold": ["PRECTOTCORR"], "template_id": "inv-es-017", "source": "template|paraphrase"}}
```

## 11. Variables de entorno (`.env.example`)

`DATA_CACHE_DIR`, `ALLOW_FIXTURES`, `AI_MODE` (`full | extractive | off`), `LLM_BASE_URL`, `PLANNER_MODEL`, `EXPLAIN_MODEL`, `EMBED_BASE_URL`, `EMBED_MODEL`, `EARTHDATA_TOKEN` (opcional).
Con `AI_MODE=extractive` todo funciona sin modelo de lenguaje: recuperación BM25, planificador por reglas y explicación con fragmentos citados.
