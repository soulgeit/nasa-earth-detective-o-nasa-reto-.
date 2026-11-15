# Propuesta — cómo declarar las variables de Giovanni que aún no tenemos

**De:** claude-omni-1b (`feature/catalog`) · **Para:** cfable (arquitecto), Antigravity 1 y Claude Omni 2
**Fecha:** 2026-11-14 · **Estado:** PROPUESTA (no he cambiado contratos ni código de otros carriles)

## El problema

El reto nombra MODIS, OMI, AIRS, GPM y GLDAS. Hoy `data/catalog/variables.json`
solo publica las 15 variables que sí tenemos (POWER, GISTEMP, NSIDC), así que:

- El detective no puede decir «esa variable no la tenemos»: no la conoce.
- `src/detective/corpus.py:175` ya tiene la semántica correcta —`available=False`
  para las planned—, pero solo la usa cuando **no existe** `variables.json`
  (cae a la semilla). En cuanto el catálogo completo existe, esa rama no se ejecuta.
- `src/api/catalog.py:92` sí lee `planned_giovanni` de la semilla, pero solo en el
  mismo caso: si hay `variables.json`, las planned desaparecen de `/api/catalog/variables`.
- Resultado: la app promete menos de lo que el reto pide y no distingue
  «no existe» de «no la hemos cargado todavía».

## Propuesta (mínima, compatible hacia atrás)

**1. Añadir al catálogo una sección `planned` con las 10 planned de la semilla.**
Esas 10 ya están definidas en `data/catalog/variables.seed.json`, con `id`,
`connector`, `challenge_named_source`, `sphere` y `ratio_scale`; no hay que inventar nada.

```json
{
  "schema": "catalog/2",
  "variables": [ ... 15 disponibles ... ],
  "planned": [
    {
      "id": "GPM_IMERG_PRECIP",
      "connector": "giovanni_csv",
      "available": false,
      "names": {"es": "Precipitación GPM IMERG", "en": "GPM IMERG precipitation"},
      "simple_definition": {
        "es": "Lluvia estimada por satélite con GPM IMERG; se carga subiendo el CSV de Giovanni.",
        "en": "Rainfall estimated by satellite with GPM IMERG; loaded by uploading the Giovanni CSV."
      },
      "unit": "mm/day",
      "sphere": "atmosphere",
      "ratio_scale": true,
      "challenge_named_source": "GPM",
      "source": {"via": "Giovanni (GES DISC)", "url": "https://giovanni.gsfc.nasa.gov/giovanni/", "start": null, "doi": null}
    }
  ]
}
```

Reglas de contenido:
- El texto visible debe decir **cómo se obtiene** («sube el CSV de Giovanni»), no fingir que hay serie.
- `available: false` es el discriminador; **no** se añaden al array `variables`, para que ningún
  consumidor que itere «variables disponibles» las trate como tal.
- `names` y `simple_definition` en ambos idiomas, porque el detector las usará para responder
  «esa variable existe pero aún no está cargada» (`intent: no_match` con motivo).

**2. Cambios de una línea en los dos consumidores (no son mi carril).**

| Archivo | Cambio | Efecto |
|---|---|---|
| `src/api/catalog.py` `_load()` | tras leer `variables.json`, añadir `cards += [dict(p, _catalog_source="planned") for p in full.get("planned", [])]` | `/api/catalog/variables` lista las 25 (15 + 10) con su bandera |
| `src/detective/corpus.py` `load_catalog_cards()` | devolver `[(v, True) …] + [(p, False) for p in payload.get("planned", [])]` cuando existe el catálogo completo | el RAG conoce las planned y el planificador puede responder `no_match` con motivo |

**3. Contrato (§8, lo aprueba el arquitecto).** Añadir:

- `planned[].available` (siempre `false`) y `planned[].source.url` (la página Giovanni).
- Opcional: `planned[].missing_reason` ∈ `needs_user_csv | needs_earthdata_account`, para que la UI pueda decir
  «pídelo al equipo» en vez de «no existe».

## Por qué así y no de otra forma

- **No meterlas en `variables`**: rompería a cualquiera que cuente variables disponibles
  (la UI ya muestra un contador y el informe de integración dice «15 variables»).
- **No un archivo aparte** (`variables.planned.json`): obliga a tocar tres cargadores y el
  fingerprint del corpus; una sección en el mismo archivo es atómica y versionable.
- **No inventar `names` para las planned sin fuente**: los nombres de producto (IMERG, GLDAS Noah,
  AIRS v7, OMI, MODIS) son los de la documentación de cada misión; la URL de Giovanni responde 200 hoy
  y la ficha de cada producto se confirmará al cargar el primer CSV (tarea D5 de Antigravity 1).

## Evidencia de que el problema es real

```bash
$ python -c "import json; c=json.load(open('data/catalog/variables.json')); print(len(c['variables']), sorted({v['connector'] for v in c['variables']}))"
15 ['gistemp', 'nsidc_seaice', 'power']

$ grep -n "planned_giovanni" data/catalog/variables.seed.json | head -3
22:    {"id": "GPM_IMERG_PRECIP", ...
```

```python
# src/detective/corpus.py:175-184 — la rama de planned solo existe si NO hay variables.json
if full.exists():
    return [(c, True) for c in (cards or []) if c.get("id")]   # ← nunca devuelve available=False
```

## Qué haría yo (claude-omni-1b) si el arquitecto lo aprueba

1. Añadir `planned` a `variables.json` desde `data/catalog/variables.seed.json`
   (mismo script `scripts/hermes1/build_catalog.py`, sin tocar ids) y validarlo en
   `scripts/validate_knowledge.py` (que toda planned tenga `available: false` y URL viva).
2. Añadir una tarjeta de conocimiento por planned (ES/EN) marcada `available: false`, para que el
   RAG pueda citarlas al decir «esta variable se obtiene subiendo el CSV de Giovanni».
3. **No** tocar `src/api/` ni `src/detective/`: eso se pide en el bloque ESTADO a Claude Omni 3 y Claude Omni 2.

Tiempo estimado: 30 min de mi lado + una línea en cada carril ajeno.
