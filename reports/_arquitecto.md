<!-- ESTADO:INICIO -->
## ESTADO — cfable (arquitecto) — 2026-11-14 19:55 hora de Perú
Rama@commit: integracion/ronda3 → main · empujado: sí
VERIFICADO: fusión de las 7 ramas feature/* → sin conflictos → `python -m pytest -q` → 223 passed, 1 failed, 9 skipped
VERIFICADO: API integrada → `python scripts/smoke_api.py http://127.0.0.1:8791` → 10 passed · 0 skipped · 0 failed
VERIFICADO: `/api/analyze` T2M Lima → `SIGNIFICANT`, `tests_agree: false`; `/api/cases` 200 con 5 casos; `/api/atlas/T2M` 759 celdas; explicación extractiva con 2 citas de temperatura
VERIFICADO: los 2 CSV de `data/raw/giovanni/` son exportaciones auténticas de Giovanni (MERRA-2), 557 meses cada una
ROTO / NO HECHO: `test_published_nasa_benchmarks` en rojo: el hielo marino lleva −9999 en 1987-12 y 1988-01 (sale así de `get_series`); mínimos cuadrados del Ártico +25,7 por década
ROTO / NO HECHO: LoRA sin evidencia (no existe `reports/lora/`; en el PC1 no hay proceso de entrenamiento); sin URL pública; casos congelados con el veredicto anterior
ROTO / NO HECHO: `validate_knowledge.py` no reejecutado por mí; `/api/analyze` pide coordenadas a GISTEMP y hielo marino; `/api/trendmap` devuelve `variable_id: "VAR"`
Siguiente paso: ventana de integración del sábado 22:00 con `bash scripts/estado.sh`
Necesito de: humano: inicio de sesión del hosting, decidir en qué PC se entrena el LoRA, más CSV de Giovanni de otros instrumentos, decisiones de PLAN §7
Avisos para otros carriles: reglas 12-18 y tareas con hora límite en `docs/RONDA_3.md`; propuesta de variables `planned` aprobada con condiciones
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
