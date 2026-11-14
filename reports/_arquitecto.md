<!-- ESTADO:INICIO -->
## ESTADO — cfable (arquitecto) — 2026-11-14 17:45 hora de Perú
Rama@commit: integracion/ronda2 → main · empujado: sí
VERIFICADO: integración de las 6 ramas → `python -m pytest -q` → 196 passed, 2 failed, 9 skipped
VERIFICADO: API integrada → `python scripts/smoke_api.py http://127.0.0.1:8791` → 10 passed · 0 failed
VERIFICADO: G1 → `GET /api/analyze?variable_id=T2M&lat=-12.05&lon=-77.03` → analysis/2, 540 meses, provenance nasa_api con sha256
VERIFICADO: interfaz v2 contra la API real en navegador → buscar «Lima» → Investigar → veredicto, cifra, IC y procedencia en pantalla
ROTO / NO HECHO: 2 pruebas del detective (MODIS_NDVI ya no está en el catálogo); `validate_knowledge.py` da 8 fallos de URL; `/api/cases` 503
ROTO / NO HECHO: no hay LoRA entrenado; no hay URL pública; no hay CSV de Giovanni; `scripts/gate.py` sin escribir
Siguiente paso: revisar los bloques ESTADO de todos con `bash scripts/estado.sh` en la puerta G2 (sáb 23:30)
Necesito de: humano: repartir la línea de arranque de `docs/RONDA_2.md`, GPU o Colab para el LoRA, CSV de Giovanni, inicio de sesión del hosting
Avisos para otros carriles: toqué una línea en `src/detective/gazetteer.py`, una en `src/ui/app.js`, `requirements.txt` y 2 pruebas de `tests/test_system.py` (detalle en `docs/RONDA_2.md` §5)
<!-- ESTADO:FIN -->

# Reporte — arquitecto (cfable)

## Integración Ronda 2 — VERIFICADO (2026-11-14 17:45)
Rama@commit: integracion/ronda2 (fusionada en main)
Qué quedó: `main` contiene `feature/api`, `feature/stats`, `feature/wizard`, `feature/catalog`, `feature/scrapes` y `feature/ui`,
con cada choque resuelto por carril (`docs/RONDA_2.md` §5). Estado anterior de `main`: etiqueta `antes-integracion-ronda2`.
No se integró la evaluación simulada del LoRA (`docs/RONDA_2.md` §1, hallazgo 2).

Evidencia:

```
$ python -m pytest -q -p no:cacheprovider
FAILED tests/detective/test_pipeline.py::test_pipeline_offline[¿la selva de Madre de Dios pierde vegetación?-es-MODIS_NDVI]
FAILED tests/detective/test_pipeline.py::test_pipeline_offline[is Amazon vegetation declining?-en-MODIS_NDVI]
2 failed, 196 passed, 9 skipped, 54 warnings in 26.83s

$ python scripts/smoke_api.py http://127.0.0.1:8791
health                           PASS  HTTP 200 ai_mode=extractive
catalog/variables                PASS  HTTP 200 variables=15
analyze unknown variable -> 404  PASS  HTTP 404 code=VARIABLE_UNKNOWN
analyze no coords -> 400         PASS  HTTP 400
analyze Lima (G1)                PASS  HTTP 200 schema=analysis/2 provenance=nasa_api n_obs=540 870ms
analyze Lima (cache < 300ms)     PASS  HTTP 200 1ms
trendmap                         PASS  HTTP 200 cells=63
cases                            PASS  HTTP 503
report                           PASS  HTTP 200 bytes=4304
UI /                             PASS  HTTP 200 bytes=17307
10 passed · 0 skipped · 0 failed

$ python scripts/validate_datasets.py data/cases/*/series.json     →  5/5 archivos validos
$ python scripts/validate_knowledge.py                             →  8 failure(s)  (URL del corpus que no responden 200)
```

Recorrido en navegador (Chrome sin interfaz, perfil propio) contra `http://127.0.0.1:8791/`: 15 variables en el selector;
«Lima» → -12.04, -77.03; Investigar → «Tendencia clara y fuerte», +0.159 °C por década, IC 95 % +0.031 … +0.281,
fuente NASA POWER v2.10.0 con la consulta exacta. Defectos vistos en ese recorrido: `docs/RONDA_2.md` §6.

Falta / riesgos: el veredicto «fuerte» de Lima contradice su propia t de MCO (p = 0,072) y la detectabilidad (faltan 13,3 años).
La gráfica dibuja la banda de confianza fuera de escala. Sin despliegue público todavía.
Necesito de otros: ver «Necesito de» en el bloque ESTADO.
