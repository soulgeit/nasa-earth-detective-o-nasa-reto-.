<!-- ESTADO:INICIO -->
## ESTADO — cfable (arquitecto) — 2026-11-15 18:35 hora de Perú
Rama@commit: `integracion/ronda7@41dd611` · empujado: sí (NO está en `main`: espera el «integra» del humano)
VERIFICADO: suite completa **361 pasan / 0 fallan / 9 omitidas**; `scripts/gate.py --offline` → **PUERTA ABIERTA** (7/7: pytest, smoke_api, validate_datasets, validate_knowledge, planned_not_analyzable, case_physical_ranges, no_secrets); `validate_fragments.py` → 773 documentos válidos en 13 archivos.
VERIFICADO: corpus de **999 documentos** (antes 168): Lima 140, Huancayo 129, Andahuaylas 124, Ica 143, Ayacucho 195; 172 instituciones, 433 páginas fuente; catálogo de **35 variables** (20 nuevas de NASA POWER, cada una pedida en vivo).
VERIFICADO en navegador (servidor local): «hola» → saludo de Huiracocha IA; «¿Llueve menos en Ica?» → plan + serie real + veredicto + explicación que cita notas SENAMHI de Ica; chip de ciudad → escaneo de 32 variables con corrección de Benjamini–Hochberg (Huancayo 9/32, Ayacucho 16/32 confirmadas); móvil 390 px sin desbordamiento; copia estática con aviso «necesita el servidor en vivo» y 0 errores de consola.
ROTO / RIESGO: producción (despliegue `978ec8e4` de las 17:31, imagen pesada con `ai_mode=full`) se **colgó a las 17:50**: cada mensaje de chat carga SmolLM2 + LoRA en CPU dentro de la petición y el servicio deja de responder (último log: «generation flags»). Hoy responde de nuevo, pero volverá a colgarse con el siguiente chat. La imagen ligera (reglas + RAG) contesta en milisegundos.
Siguiente paso: humano → «integra» (`integracion/ronda7` → `main`) y «despliega» (`bash scripts/deploy_railway.sh --deploy`: comprueba, sube la imagen ligera y verifica la URL).
Necesito de: humano: esas dos órdenes; y decidir si quiere el texto de «Runas de Energía / Machu Picchu» como dedicatoria (no puedo afirmarlo como ubicación técnica: el servidor está en Railway).
Avisos para otros carriles: `feature/ui` quedó fusionada en `integracion/ronda7`; no empujar chat ni UI a `main`; no desplegar `Dockerfile.lora` en la URL pública.
<!-- ESTADO:FIN -->

# Reporte — arquitecto (cfable)

## Cierre de producción (final) — VERIFICADO (2026-11-15 12:05)
Rama@commit: `main@5361f79` (empujado)

```
$ python -m pytest -q -p no:cacheprovider
289 passed, 9 skipped, 74 warnings in 271.13s (0:04:31)

$ python scripts/smoke_api.py https://nasa-earth-detective-o-nasa-reto-production.up.railway.app
17 passed · 0 skipped · 0 failed
  health 200 ai_mode=extractive · catalog 15 · analyze Lima 540 obs sospecha NASA · trendmap 63 celdas
  cases 200 · case detail lima-t2m SIGNIFICANT · GPM_IMERG_PRECIP → 409 VARIABLE_PLANNED · UI 200

$ curl -I https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./
HTTP 200 · Last-Modified: Sun, 15 Nov 2026 16:50:07 GMT (gh-pages@10c7e16, H1 aplicado)
```

Despliegue completo (Railway): la app interactiva con API viva responde en producción y
pasa el smoke completo. El respaldo estático (GitHub Pages) sirve los 7 casos congelados
con las cifras ya corregidas (+0.159 tras H1). Láminas de entrega alineadas con H1 y
regeneradas a PDF (7 páginas exactas). «Live links» de SUBMISSION y README apuntan a
ambas URLs.

## Cierre Ronda 6 (final) — VERIFICADO (2026-11-15 11:30)
Rama@commit: `main@9e386db` (todo lo de la entrega en `main`, en verde, empujado)

Verificación de cierre ejecutada por el arquitecto tras la integración de los reportes R6:

```
$ python -m pytest -q -p no:cacheprovider          (sobre main ampliado, 10:5x)
288 passed, 9 skipped, 74 warnings in 272.47s (0:04:32)

$ python scripts/gate.py --offline --skip-suite
OK smoke_api · OK validate_datasets · OK validate_knowledge
OK planned_not_analyzable · OK case_physical_ranges · OK no_secrets (289 archivos)
PUERTA ABIERTA: todo en verde

$ ffprobe docs/demo/EarthTrend_Detective_30s.mp4 → duration 29.000000 s (≤ 30.0)
$ pypdf docs/demo/EarthTrend_Detective_slides.pdf → /Count 7 (≤ 7 páginas, 2.407.097 bytes)
$ curl 7 casos en GitHub Pages → 7/7 HTTP 200, texto es corregido ya en vivo
```

Despliegue final: `gh-pages@cb84560` generado con `scripts/build_static.py --from-cases`
(7 casos, 7 análisis, 2 atlas, 0 errores) y empujado. URL pública
`https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` HTTP 200 con
`Last-Modified: Sun, 15 Nov 2026 16:30:03 GMT`; la corrección «todavía no se detecta
tendencia» ya se sirve desde la URL.

Lo que entró en `main` tras la integración de las 10 ramas (todo docs/scripts seguro,
sin tocar `src/` ni esquemas):
- `fix/pytest-testpaths@3a61b8e`: pytest solo recoge `tests/` (un clon limpio fallaba porque `scripts/test_ui_r5.py` importa playwright).
- `feature/scrapes` (hermes-2 R6): idioma mezclado en un hallazgo es y cifra de `DATASET_CARD`.
- `feature/catalog` (claude-omni-1b R6): reporte final + fuente Lenssen 2019.
- `feature/static` (claude-omni-3a R6): reporte con verificación byte a byte de la URL pública.
- `integracion/ronda6` (scripts de despliegue `deploy_update.ps1/.sh`).
- `docs(reports)`: reportes R6 de antigravity-1, antigravity-2, claude-omni-c (portado desde `feature/demo@b3eb737`, que también quedó empujada).
- `9e386db` (humano): láminas y SUBMISSION con el miembro del equipo y la visión; demo = láminas.

Quedan: informes R6 de 4 carriles (claude-omni-1, claude-omni-2, claude-omni-3,
claude-omni-e/informe-3) y el «Submit for Judging» humano a las 20:00.

## Integración Ronda 6 (Final pre-entrega) — VERIFICADO (2026-11-15 08:50)
Rama@commit: `integracion/ronda6` (fusión de las 10 ramas sin conflictos)

Qué entró:
- `feature/data-pipeline@016bc52`: Comparación cuantitativa POWER-Giovanni (`docs/COMPARACION_POWER_GIOVANNI.md`), arreglo de «Based on» en conector NSIDC.
- `feature/scrapes@53f07d0`: Casos regenerados con tildes en español, lugar en texto de respuestas, veredictos en lenguaje legible, y defectos del dataset en `data/lora/DATASET_CARD.md`.
- `feature/stats@cc0cf4b`: Tabla de validación con comandos reproducibles en `docs/VALIDACION_ESTADISTICA.md`, `MODEL_CARD.md` actualizado con métricas GPU/CPU.
- `feature/static@5a0ee23`: Respaldo estático con `.nojekyll` y soporte verificado de los 7 casos bajo subcarpeta.
- `feature/api@f8f2915`: `LICENSE` MIT agregada, `GET /api/cases/{id}` en contrato y smoke tests.
- `feature/catalog@ecf888e`: `docs/REFERENCES.md` final revisado en vivo, `README.md` final bilingüe.
- `feature/wizard@a642596`: `docs/SUBMISSION.md` completo en inglés con comandos reproducibles, evaluación LoRA GPU/CPU en `docs/EVAL_IA.md`, citas sin nombres de agentes en `data/knowledge/docs.jsonl`.
- `feature/ui@f4201dd`: 7 láminas oficiales en `docs/demo/EarthTrend_Detective_slides.pdf` y `slides.html` (fuentes en `docs/demo/FUENTES.md`), capturas limpias sin huecos tipográficos en `docs/media/`, unidades traducidas en español, QA D8 resuelto.
- `feature/qa@5ea562d`: `reports/qa/informe-2.md` con defectos cerrados.
- `rescate/demo@9bc5276`: Vídeo de demostración oficial de 29.0s (`docs/demo/EarthTrend_Detective_30s.mp4`) con guion en `docs/demo/GUION.md`.

Evidencia:

```
$ python -m pytest -q
288 passed, 9 skipped, 74 warnings in 275.12s (0:04:35)

$ python scripts/gate.py --offline --skip-suite
=== smoke_api === 17 passed · 0 skipped · 0 failed
=== validate_datasets === 7/7 archivos validos
=== validate_knowledge === 168 docs, All checks passed
=== planned no analizable === planned=10 available=15 solapamiento=False
=== rangos fisicos === 7/7 series validas; 3882 valores dentro de rango
=== credenciales === 289 archivos revisados; 0 hallazgos
PUERTA ABIERTA: todo en verde

$ python scripts/check_case_accents.py
0 problemas en 8 archivos

$ python -c "..." (duración de EarthTrend_Detective_30s.mp4)
Duration in seconds: 29.0 (cumple <= 30.0s)

$ python -c "..." (páginas de EarthTrend_Detective_slides.pdf)
Page count: 7 (cumple <= 7 páginas)
```

Estado para la entrega:
- Todo el código y los entregables están en verde y verificados.
- Lista para merge en `main` cuando el humano confirme «integra».

## Integración Ronda 5 — VERIFICADO (2026-11-15 06:35)
Rama@commit: `integracion/ronda5` (en GitHub como rama; no está en `main`)

Qué entró: `feature/scrapes@2f6e137`, `feature/data-pipeline@e05ea3b`, `feature/stats@446eded`, `feature/wizard@4a9ae56`,
`feature/api@ae406fa`, `feature/static@fbe332b`, `feature/ui@9ef14d6` y `feature/qa@10f4b46` sobre `main@d51fd9d`.
Dos choques: los casos de hielo marino (dos regeneraciones; quedan los de hermes-2) y `src/detective/planner.py`
(quedan las dos mejoras). Encima, cuatro commits míos: `4b7d6ac` (puntuación), `fe4bf13` (galería, lugar y `planned`),
`76ca740` (README y validador) y `9f7a9fd` (etiqueta de la explicación y favicon). Detalle y motivos en `docs/RONDA_5.md` §2 y §5.

Evidencia:

```
$ python -m pytest -q -p no:cacheprovider                       (solo la fusión)
269 passed, 9 skipped, 66 warnings in 218.50s (0:03:38)

$ python -m pytest -q -p no:cacheprovider                       (con los cuatro commits, en 9f7a9fd)
276 passed, 9 skipped, 74 warnings in 196.89s (0:03:16)

$ python scripts/smoke_api.py http://127.0.0.1:8795
15 passed · 0 skipped · 0 failed

$ python scripts/gate.py --base http://127.0.0.1:8795 --skip-suite --offline
OK smoke_api · OK validate_datasets · OK validate_knowledge · OK planned_not_analyzable
OK case_physical_ranges · OK no_secrets (265 archivos, 0 hallazgos)      PUERTA ABIERTA

$ python -m src.detective.rag.eval_plan
| rules | 49/50 = 0.980 | 50 |        única fallida: polvo del desierto de Sechura → GWETTOP (esperado AOD_55)

$ AI_MODE=full PLANNER_MODEL=local-lora python -m src.detective.rag.eval_plan --planner local-lora
| local-lora | 40/50 = 0.800 | 50 |   quién planificó: lora 50 · 112,4 s en total, mediana 2,2 s (RTX 4070 SUPER, 4 bits)

$ curl "http://127.0.0.1:8795/api/catalog/variables?lang=en"
n_available 15 · n_planned 10        (antes de `fe4bf13`: n_planned 0)
$ curl "http://127.0.0.1:8795/api/analyze?variable_id=MODIS_NDVI&lat=-12&lon=-70"
HTTP 409 VARIABLE_PLANNED            (antes: HTTP 404 VARIABLE_UNKNOWN)
```

Los 10 fallos del LoRA en GPU (devuelto → esperado):

| Pregunta | Devuelto | Esperado |
|---|---|---|
| ¿Hace más calor ahora en Lima que cuando era niño? | `TS` | `T2M` |
| ¿Por qué hay más humo en el cielo de la Amazonía en septiembre? | `CLOUD_AMT` | `AOD_55`, `PRECTOTCORR` |
| ¿Qué ha pasado con la lluvia en la selva de Madre de Dios? | `T2M` | `PRECTOTCORR` |
| Temperatura de la superficie del suelo en Puno, tendencia | `GISTEMP_TANOM` | `TS` |
| ¿La garúa de Lima se está volviendo más frecuente? | `ALLSKY_SFC_SW_DWN` | `CLOUD_AMT`, `RH2M` |
| ¿El vapor de agua sobre la costa peruana está cambiando? | `RH2M` | `TQV` |
| ¿Las lluvias de El Niño son más intensas en Tumbes? | `T2M` | `PRECTOTCORR` |
| Ground surface temperature in Puno, trend | `GISTEMP_TANOM` | `TS` |
| Is Lima's drizzle becoming more frequent? | `PRECTOTCORR` | `CLOUD_AMT`, `RH2M` |
| Which variable tells me if Piura is turning into desert? | `T2M` | `GWETTOP`, `PRECTOTCORR` |

Recorrido en Chrome (Playwright, perfil propio) contra `http://127.0.0.1:8795/` (27 de 28): los 7 casos de la galería abren su
análisis congelado y cada uno muestra el `verdict_code` del índice (pendientes de Sen: Lima +0,1585; Svalbard +0,6986;
Piura −0,011; Ártico −0,4953; Antártico −0,0481; Amazonía temperatura +0,1864; Amazonía lluvia −0,0829). Buscar «Lima» e
investigar → «Observed in Lima.». Detective: «What is the meaning of life?» → `out_of_scope` sin variable ni lugar;
«Show me MODIS vegetation for the Amazon» → `no_match`, falta `NDVI vegetation index (MODIS)`, sin lugar inventado.
A 390 px: `scrollWidth` 390 = `clientWidth` 390. Puntuación medida a 32 px: el punto pasa de 20,31 px a 8,97 px al
quitar `tabular-nums`.

Falta / riesgos: lo de ROTO / NO HECHO del bloque ESTADO. La galería ya no depende de los servidores de la NASA,
pero el análisis en vivo sí: si NASA POWER responde lento durante el juicio, el respaldo son los 7 casos.

Clon nuevo, como lo haría un juez (`git clone` de esta rama, venv nuevo, sin `torch`, `peft` ni `transformers`):

```
$ pip install -r requirements.txt && pip install -r requirements-dev.txt
$ python -m pytest -q -p no:cacheprovider
275 passed, 10 skipped, 74 warnings in 211.09s (0:03:31)
```

URL pública (dom 06:32): `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` → HTTP 200,
`Last-Modified: Sun, 15 Nov 2026 06:31:19 GMT` (la 01:31 de Perú): es `gh-pages@4e526a2`. El mismo recorrido sobre ella:
Lima, Svalbard, Piura, Ártico y Antártico abren con su veredicto, pero la cifra sale sin unidad («+0.159 per decade»);
al pulsar «Amazon (lower Amazon basin)» la zona de resultados queda vacía, y el segundo botón de la Amazonía tampoco
abre. El respaldo regenerado desde `9f7a9fd` y servido en local bajo una subruta pasa 19 de 19; no lo subí.


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
