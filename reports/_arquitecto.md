<!-- ESTADO:INICIO -->
## ESTADO — cfable (arquitecto) — 2026-11-15 06:35 hora de Perú
Rama@commit: `integracion/ronda5` · empujado: sí, como rama; **todavía no está en `main`** (pasa cuando el humano diga «integra»)
VERIFICADO: `main@d51fd9d` + las 8 ramas de la Ronda 4 + 4 commits de arreglos → `python -m pytest -q` → 276 passed, 0 failed, 9 skipped; en un clon nuevo con un venv nuevo y sin `torch` → 275 passed, 0 failed, 10 skipped
VERIFICADO: `python scripts/smoke_api.py http://127.0.0.1:8795` → 15 passed · 0 failed; `python scripts/gate.py --base … --skip-suite --offline` → PUERTA ABIERTA
VERIFICADO: recorrido en Chrome (Playwright) → 27 de 28 en la app y 19 de 19 en el respaldo estático bajo una subruta; los 7 casos abren su análisis congelado
VERIFICADO: 50 preguntas de referencia → reglas 49/50; LoRA 40/50 (RTX 4070 SUPER, 4 bits, mediana 2,2 s, `planner: "lora"` en 50 de 50)
VERIFICADO: rescatado el trabajo sin subir de claude-omni-1 (`feature/ui@9ef14d6`) y de claude-omni-e (`feature/qa@10f4b46`)
ROTO / NO HECHO: la URL pública (GitHub Pages, ya activa) sirve `gh-pages@4e526a2`, de la 01:30: los 2 casos de la Amazonía no abren, cifras sin unidad y con huecos; el respaldo corregido está generado y probado pero sin subir (espera «despliega» o a claude-omni-3a)
ROTO / NO HECHO: no existen `docs/SUBMISSION.md`, `LICENSE` ni `docs/demo/`; Railway sin sesión en el PC1; en español la unidad sale en inglés; no probé `docker build` ni un clon limpio en Linux
Siguiente paso: pasar `integracion/ronda5` a `main` cuando el humano diga «integra»; integración 2 a las 10:00; desplegar en Railway cuando inicie sesión
Necesito de: humano: «integra», «despliega», `railway login` en el PC1 y las decisiones de `docs/RONDA_5.md` §6
Avisos para otros carriles: manda `docs/RONDA_5.md` (reglas 26-31); la base es `origin/integracion/ronda5`, no `main`; toqué archivos de cinco carriles (lista en su §5)
<!-- ESTADO:FIN -->

# Reporte — arquitecto (cfable)

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
