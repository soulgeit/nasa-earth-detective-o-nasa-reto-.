<!-- ESTADO:INICIO -->
## ESTADO — cfable (arquitecto) — 2026-11-14 23:40 hora de Perú
Rama@commit: `integracion/ronda4` → `main` · empujado: sí (sábado 23:40, cuando el humano dijo «integra»)
VERIFICADO: `main@55eba0b` + `feature/data-pipeline@c53d937` + `feature/stats@22b2cb5` fusionadas y ya en `main` → `python -m pytest -q` → 234 passed, 4 failed, 9 skipped
VERIFICADO: adaptador LoRA real → sha256 `70314779…341c` coincide con `reports/lora/train_meta.json`; 192 tensores, las 96 matrices B distintas de cero; por `AI_MODE=full PLANNER_MODEL=local-lora` responde `planner: "lora"` en 2,3 s (PC1, RTX 4070 SUPER)
VERIFICADO: 50 preguntas de referencia → `python -m src.detective.rag.eval_plan` → reglas 47/50; con `--planner local-lora` → LoRA 31/50 (15 de sus 19 fallos son variables `planned`)
ROTO / NO HECHO: 4 rojas (2 del detective por las `planned`, 2 que daban por hecho que no había adaptador); casos de hielo marino con −9999; sin URL pública; sin `docs/SUBMISSION.md`, `src/ml/MODEL_CARD.md`, `LICENSE` ni demo
Siguiente paso: integración 1 del domingo 02:30 (suite sin rojas); desplegar en Railway cuando el humano inicie sesión en el PC1
Necesito de: humano: `railway login` en el PC1 y las decisiones de `docs/RONDA_4.md` §6
Avisos para otros carriles: manda `docs/RONDA_4.md` (reglas 19-25, tareas con hora límite, tres agentes nuevos); la fusión del LoRA ya está en `main`: las tareas ⏳ empiezan tras `git merge origin/main`
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
