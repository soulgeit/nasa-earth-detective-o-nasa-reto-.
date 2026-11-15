# RONDA 3 — del sábado 14-nov 20:00 al domingo 15-nov 10:00 (puerta G3)

Este documento manda sobre `docs/RONDA_2.md` donde lo contradiga. Las 11 reglas, la forma de empujar (§3) y la nota de estado (§4) de la Ronda 2 **siguen vigentes**.

**Línea de arranque, igual para todos:**

```
git fetch origin && git checkout feature/<tu-rama> && git merge origin/main
Lee docs/RONDA_3.md: reglas nuevas (§3) y tu apartado del §4. Empieza por tu tarea 1.
```

## 1. Estado verificado por el arquitecto (sáb 19:45)

Las 7 ramas `feature/*` se fusionaron en `main` **sin ningún conflicto** (en la Ronda 1 chocaban las seis). Los 7 agentes dejaron su bloque ESTADO. Avance estimado: **~68 %** (era ~60 %).

| Comprobación sobre `main` fusionado | Resultado |
|---|---|
| `python -m pytest -q` | 223 passed, **1 failed**, 9 skipped (antes 196 / 2 / 9) |
| `python scripts/smoke_api.py http://127.0.0.1:8791` | 10 passed · 0 failed |
| `GET /api/analyze` T2M Lima | `SIGNIFICANT`, `tests_agree: false`, avisos `TESTS_DISAGREE` y `HIGH_AUTOCORRELATION`; textos con nombre de variable y coordenadas |
| `GET /api/cases` | 200, 5 casos (antes 503) |
| `GET /api/atlas/T2M` | 200, `trendmap/2`, 759 celdas |
| `POST /api/ai/explain` (Lima) | modo extractivo, 2 citas de temperatura con título, editor y URL |
| `GET /api/geocode?q=Cuzco` | Cusco (PE) |
| `data/raw/giovanni/*.csv` | 2 exportaciones auténticas de Giovanni (cabecera oficial y «URL to Reproduce Results»), 557 meses cada una |
| `data/lora/*.jsonl` | 4323 / 814 / 632 líneas (restaurado) |

| Agente | Rama@commit integrado | Qué queda comprobado | Qué no |
|---|---|---|---|
| antigravity-1 | `feature/data-pipeline@33e27fa` | CSV de Giovanni reales; lector y precalentado dentro de la suite | el conector de NSIDC deja pasar −9999 (§2.1) |
| antigravity-2 | `feature/stats@6ba6b4b` | veredicto de Lima coherente; `eval_lora.py` y `serve.py` ya no simulan: sin adaptador dan error | **LoRA sin evidencia** (§2.3) |
| claude-omni-1 | `feature/ui@35c2baf` | la línea de Sen y su banda caen sobre los datos | capturas anteriores a la integración (§2.6) |
| claude-omni-1b | `feature/catalog@1e676db` | 168 fichas, referencias en inglés (validador de URL no reejecutado por el arquitecto) | — |
| claude-omni-2 | `feature/wizard@2667061` | citas pertinentes, `no_match`, gazetteer; `tests/detective` en verde | — |
| claude-omni-3 | `feature/api@ed7cc43` | API integrada, `/api/cases`, imagen Docker preparada | **sin URL pública** |
| hermes-2 | `feature/scrapes@279837a` | 5 casos `analysis/2` + `index.json`, atlas con el motor real | veredictos congelados con el motor anterior (§2.2) |

## 2. Lo que encontró la revisión

1. **Valor de relleno −9999 dentro de los datos (grave).** Los casos `arctic-seaice` y `antarctic-seaice` tienen `raw = -9999.0` en `1987-12` y `1988-01` (hueco del satélite que NSIDC marca así). La serie sale así de `get_series`. Efecto en el Ártico: recta de mínimos cuadrados **+25,7 millones de km² por década** (la de Sen da −0,50), R² 0, p = 0,3985 y «faltan 1588 años». Es la causa de la única prueba roja (`tests/stats/test_trend_engine.py::test_published_nasa_benchmarks`: el Ártico ya no sale «fuerte» porque la prueba de mínimos cuadrados discrepa). `validate_datasets.py` no lo detectó.
2. **Casos congelados con el veredicto antiguo.** `/api/cases` dice `lima-t2m: SIGNIFICANT_STRONG`; el motor ya integrado responde `SIGNIFICANT`. Hay que regenerarlos.
3. **LoRA: sigue sin haber modelo.** La nota de antigravity-2 dice que entrena en una GTX 1650 SUPER hasta ~21:20. En el PC1 (RTX 4070 SUPER) no hay ningún proceso de entrenamiento y la GPU está libre (2,1 de 12 GB, 5 % de uso). En el repositorio no existe `reports/lora/`. Hasta que haya evidencia, el estado es «sin entrenar».
4. **Variables sin lugar piden coordenadas.** `GET /api/analyze?variable_id=SEAICE_EXTENT_N` y `GISTEMP_TANOM` devuelven 400 «Faltan las coordenadas» (`src/api/validation.py:53`).
5. **`/api/trendmap` devuelve `variable_id: "VAR"`.** El motor pone ese valor por defecto (`src/stats/trend_engine.py:662` y `:763`) porque la rejilla que le pasa la API no trae `variable_id`.
6. **Interfaz y citas.** La interfaz lee `cit.id`, que ya no existe (ahora llegan `n`, `title`, `publisher`, `url`, `source_id`): todas las citas saldrían como «[1]» con un enlace fijo «(NASA)». El rótulo sigue diciendo «AI-assisted synthesis» aunque el modo sea extractivo (`src/ui/i18n.js:145` y `:307`). Las 6 capturas de `docs/media/` son anteriores a la integración: mezclan español e inglés y muestran citas de aerosoles para la temperatura de Lima.
7. **`region.name` llega `null`**: la respuesta dice «Observado en las coordenadas (−12.05°, −77.03°)» aunque el usuario buscó «Lima».
8. **Catálogo: 15 variables, ninguna de MODIS, GPM, OMI, AIRS o GLDAS.** Los dos CSV de Giovanni son de MERRA-2, la misma fuente que ya da POWER.
9. **No hay URL pública ni material de entrega** (página en inglés, README en inglés, vídeo o láminas).

## 3. Reglas nuevas (se suman a las 11 de la Ronda 2)

12. **Ningún valor de relleno llega al motor.** −9999, −999, 1e15 o el que declare la fuente se convierten en dato faltante en el conector y se cuentan en `n_missing`. `validate_datasets.py` debe fallar si un valor cae fuera del rango físico de su variable.
13. **Una prueba roja no se pone verde aflojando la aserción.** Se arregla la causa. Si la aserción estaba mal, se cambia explicando por qué en tu reporte.
14. **«VERIFICADO» exige la suite entera sobre `main` fusionado.** Tras `git merge origin/main` corre `python -m pytest -q` (todo, no solo tu carpeta) y pega la línea de totales en tu bloque ESTADO.
15. **El LoRA solo existe con evidencia en el repositorio**: registro del entrenamiento, metadatos, huella del adaptador y predicciones reales (detalle en §4, antigravity-2). Sin eso, en todas partes se escribe «modelo sin entrenar».
16. **Lo que ve el jurado va en inglés.** La interfaz abre en inglés; capturas, README, ficha del modelo y referencias en inglés. El español queda como segundo idioma. Ninguna pantalla mezcla los dos.
17. **Cada tarea tiene hora límite.** Si no llegas, escribe «ROTO / NO HECHO» con el motivo y pasa a la siguiente. No se alarga una tarea a costa de las demás.
18. **Congelación el domingo a las 14:00.** Después solo entran arreglos que traigan una prueba que fallaba o una pantalla rota como evidencia.

Ventanas de integración en `main`: sáb 22:00, sáb 23:30 (G2), dom 10:00 (G3), dom 14:00. Entre ventanas, `claude-omni-3` puede integrar ramas con estado VERIFICADO y suite completa en verde.

## 4. Tareas por agente, en orden y con hora límite

### antigravity-1 — datos de la NASA · `feature/data-pipeline`
1. **Hoy 21:30.** `src/etl/nsidc_seaice.py`: los meses con −9999 salen como faltantes (`value: null`) y se cuentan en `n_missing`. Prueba nueva con `tests/fixtures/real/nsidc_seaice_N_monthly_all.csv` que compruebe que ningún valor es negativo y que `1987-12` y `1988-01` faltan. Revisa lo mismo en GISTEMP, POWER (−999) y en el lector de Giovanni (el «Fill Value» de la cabecera). Avisa a hermes-2 y a antigravity-2 en cuanto esté empujado.
2. **Hoy 23:30.** `scripts/validate_datasets.py`: comprobación de rango físico por variable (regla 12). Tiene que fallar con la serie actual del hielo marino y pasar con la corregida.
3. **Autorizado:** migra tú `tests/test_system.py` a `get_series` y borra los adaptadores `get_power_point_series` y `get_power_regional_series`, en un commit aparte.
4. **Cuando el humano deje más CSV** en `data/raw/giovanni/` (GPM, MODIS, OMI…): valídalos y avisa a claude-omni-1b para darlos de alta. Escribe en `data/raw/giovanni/README.md` qué buscar en Giovanni y cómo nombrar el archivo.
5. **Dom 10:00, si sobra tiempo.** Compara, para la misma caja y periodo, T2M y PRECTOTCORR de POWER regional con los dos CSV de Giovanni (es el mismo MERRA-2): diferencia media y correlación en tu reporte. Es evidencia de que dos accesos de la NASA coinciden.

### antigravity-2 — estadística y LoRA · `feature/stats`
1. **Hoy 21:30 — evidencia del entrenamiento**, empujada: `reports/lora/train_log.txt` (pérdida por paso), `reports/lora/train_meta.json` (modelo base y revisión, hiperparámetros, pasos, ejemplos vistos, semilla, duración, salida de `nvidia-smi`, tamaño y sha256 de `adapter_model.safetensors`) y `adapter_config.json`. `.gitignore` excluye `*.safetensors`: si el adaptador pesa ≤ 50 MB, súbelo con `git add -f models/planner-lora/adapter_model.safetensors`; si pesa más, no lo subas y avisa al humano. **Si a las 21:30 no ha terminado en la GTX 1650, relánzalo en el PC1** (RTX 4070 SUPER libre) con la receta de `docs/RONDA_2.md` §9.2: ahí no hace falta cuantizar a 4 bits y caben 2 épocas.
2. **Hoy 23:30 — evaluación real**: `python -m src.ml.eval_lora` sobre `data/lora/test.jsonl` → `reports/lora/eval.json` y `reports/lora/predictions.jsonl` para reglas, modelo base y base + adaptador. Si no da tiempo con los 632, usa una muestra fija de 200 con semilla 42 y dilo. El resultado se publica como salga, aunque el adaptador pierda contra las reglas.
3. **Hoy 23:30.** Quita el valor por defecto `"VAR"` de `analyze_grid` (`trend_engine.py:662` y `:763`): si la rejilla no trae `variable_id`, devuelve `null`. Cuando antigravity-1 empuje su arreglo, comprueba que `test_published_nasa_benchmarks` vuelve a verde **sin tocar la aserción** (regla 13).
4. **Dom 10:00.** `src/ml/MODEL_CARD.md` en inglés, solo con cifras de `reports/lora/eval.json`; y `docs/VALIDACION_ESTADISTICA.md` con la regla de los cuatro veredictos explicada en un párrafo en inglés.

### claude-omni-1 — interfaz · `feature/ui` (solo `src/ui/` y `scripts/take_real_screenshots.py`)
El catálogo **no** es tuyo: lo lleva `claude-omni-1b`.
1. **Hoy 22:00.** Citas: numera con `cit.n` y muestra `título — editor` enlazado a `cit.url`; fuera el «(NASA)» fijo. Rótulo según `mode`: «extractive» → «Excerpts from cited sources (no generative AI)»; «AI-assisted» solo con `mode: full`.
2. **Hoy 23:30.** La interfaz abre en inglés y pide la explicación en el idioma activo (regla 16). Galería de casos desde `/api/cases` (un clic carga el caso congelado) y vista del atlas desde `/api/atlas/{id}`.
3. **Hoy 23:30.** Panel del veredicto: cuando llegue `TESTS_DISAGREE`, muestra qué pruebas coinciden y cuáles no (Mann-Kendall, Mann-Kendall anual, t de mínimos cuadrados, intervalo) y los años que faltan según `detectability`.
4. **Dom 10:00.** Variables sin lugar (GISTEMP, hielo marino): no pidas punto en el mapa (depende de la tarea 1 de claude-omni-3). Recorre «subir CSV» con `data/raw/giovanni/T2M__amazonia.csv`. Después repite las 6 capturas desde `main` integrado, en inglés.

### claude-omni-1b — catálogo y material de entrega · `feature/catalog`
1. **Hoy 22:00. Propuesta APROBADA** (`docs/PROPUESTA_VARIABLES_PLANNED.md`) con tres condiciones: las `planned` llevan `available: false`; nunca se cuentan como variables disponibles en ningún texto; y nunca se ofrecen para analizar (el detective responde `no_match` y explica que se cargan subiendo el CSV de Giovanni). Añádelas a `data/catalog/variables.json` y avisa a claude-omni-3 y claude-omni-2 para su línea de carga.
2. **Carril nuevo para esta ronda:** `README.md`, `LICENSE*` y `docs/SUBMISSION.md`.
   - **Hoy 23:30.** `README.md` en inglés: qué es, cómo ejecutarlo, fuentes de datos con enlace, método estadístico, límites conocidos y uso de IA (de `docs/AI_USE_LOG.md`).
   - **Dom 10:00.** `docs/SUBMISSION.md`: los textos de la página del proyecto según `docs/KIT_ENTREGA.md`, en inglés, **solo con hechos de reportes VERIFICADOS**. La historia, los casos y el nombre los decide el humano: deja `<<HUMANO: …>>` donde falte su decisión. No los inventes.
3. Da de alta en el catálogo cada variable de Giovanni que antigravity-1 valide.

### claude-omni-2 — detective con IA · `feature/wizard`
1. **Hoy 22:00.** La explicación sale solo en el idioma pedido (fichas `-en` con `lang=en`); ninguna respuesta mezcla idiomas.
2. **Hoy 23:30.** Lee `planned` del catálogo: ante una variable no disponible responde `no_match`, la nombra y dice cómo cargarla.
3. **Dom 10:00.** `PLANNER_MODEL=local-lora` conectado a `src/ml/serve.py` en cuanto haya adaptador; si falta o devuelve un JSON no válido, vuelve a las reglas. La respuesta de `/api/ai/plan` dice quién planificó (`"planner": "lora" | "rules"`); avisa del campo nuevo a claude-omni-1 y claude-omni-3.
4. **Dom 10:00.** `docs/EVAL_IA.md`: las 50 preguntas de `golden_questions.jsonl` con el planificador de reglas y, si existe, con el LoRA. Solo ejecuciones reales.

### claude-omni-3 — API, despliegue e integrador suplente · `feature/api` (más `scripts/gate.py`)
1. **Hoy 22:00.** `/api/analyze`, `/api/series` y `/api/report` aceptan sin coordenadas las variables sin lugar (GISTEMP_TANOM, SEAICE_EXTENT_N, SEAICE_EXTENT_S). Añádelo a `smoke_api.py`.
2. **Hoy 22:00.** Pasa `variable_id` en la rejilla de `/api/trendmap`; acepta `place` (el nombre que devolvió `/api/geocode`) y llévalo a `region.name`; publica `planned` en `/api/catalog/variables`.
3. **En cuanto el humano inicie sesión: URL pública.** Con `AI_MODE=extractive` y sin muestras locales. Después `python scripts/smoke_api.py <URL>` y la salida en tu reporte. El modelo LoRA no va al servidor público (§5).
4. **Hoy 23:30.** `scripts/gate.py`: un comando que corre la suite, `smoke_api.py`, `validate_datasets.py` y `validate_knowledge.py` y termina con código distinto de cero si algo falla.
5. **Dom 10:00.** Respaldo estático con los casos congelados y versiones fijadas en `requirements.txt`.

### hermes-2 — casos, atlas y dataset · `feature/scrapes`
1. **Ya.** El arreglo del veredicto está en `main`: `python -X utf8 -I scripts/regenerate_cases_v2.py`. Evidencia: `lima-t2m` queda `SIGNIFICANT`.
2. **Tras el arreglo de antigravity-1 (tarea 1).** Regenera `arctic-seaice` y `antarctic-seaice`. Evidencia: mínimo de `series.raw` ≥ 0, `1987-12` y `1988-01` en `null`, y la pendiente de mínimos cuadrados con el mismo signo y orden que la de Sen. El Ártico y el Antártico se presentan como salgan.
3. **Hoy 23:30.** Dos casos nuevos con los CSV reales de Giovanni (`amazonia-t2m`, `amazonia-prectotcorr`), con la «URL to Reproduce Results» en la procedencia.
4. **Dom 10:00.** Nombre y una frase de hallazgo por caso, en inglés y español, sacada solo de los números. La historia la decide el humano.

## 5. Decisiones del arquitecto

- **Dónde vive el LoRA.** El servidor público gratuito no puede ejecutar un modelo de 1,7 mil millones de parámetros. En la URL pública planifican las reglas y la explicación es extractiva. El LoRA se ejecuta en local (`PLANNER_MODEL=local-lora`), se enseña en la demo y se publica su evaluación real. La página del proyecto lo dirá tal cual.
- **Variables `planned`:** aprobadas con las condiciones del §4 (claude-omni-1b).
- **Arreglos fuera de carril autorizados en esta ronda:** antigravity-1 en `tests/test_system.py`; claude-omni-1 en `scripts/take_real_screenshots.py`; claude-omni-3 en `scripts/gate.py`; claude-omni-1b en `README.md`, `LICENSE*` y `docs/SUBMISSION.md`.

## 6. Pendiente del humano

1. **Hosting:** iniciar sesión (Railway, donde ya hay cuenta, o Fly) y avisar a claude-omni-3. Sin esto no hay URL pública y sin URL no hay entrega.
2. **LoRA:** confirmar en qué PC entrena antigravity-2. Si a las 21:30 no hay adaptador, que entrene en el PC1 y que nadie cargue el modelo de 35B en Ollama mientras tanto.
3. **Más CSV de Giovanni, de otros instrumentos:** los dos que hay son de MERRA-2. Para la misma caja, mensual, «Time Series, Area-Averaged»: precipitación de GPM IMERG, NDVI o temperatura de superficie de MODIS, y uno de OMI, AIRS o GLDAS.
4. **Decisiones de `docs/PLAN_GANADOR.md` §7:** casos, historia, nombre, y vídeo de 30 s o 7 láminas.
5. `git pull` en `Desktop\nasa-earth-detective`.

## 7. Puertas

| Puerta | Hora | Condición |
|---|---|---|
| Integración | sáb 22:00 | −9999 corregido, casos regenerados, suite en verde |
| G2 | sáb 23:30 | evaluación real del LoRA publicada (o «sin entrenar»), URL pública con `smoke_api.py` en verde, interfaz en inglés con citas correctas |
| G3 | dom 10:00 | planificador LoRA servido en local o plan B declarado, casos finales, capturas nuevas, README y borrador de la página en inglés |
| Congelación | dom 14:00 | solo arreglos con evidencia |
| G4 | dom 18:00 | página, demo y enlaces públicos probados |
| ENTREGAR | dom 20:00 | «Submit for Judging» |
