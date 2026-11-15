# RONDA 4 (final) — del sábado 14-nov 23:55 al domingo 15-nov 20:00 (ENTREGAR)

Este documento manda sobre `docs/RONDA_3.md` donde lo contradiga. Siguen vigentes las reglas 1-18, la forma de empujar (`docs/RONDA_2.md` §3) y el bloque ESTADO (`docs/RONDA_2.md` §4).

**Línea de arranque:**

```
git fetch origin && git checkout feature/<tu-rama> && git merge origin/main
Lee docs/RONDA_4.md entero: reglas 19-25 (§3) y tu apartado del §4. Empieza por tu tarea 1.
```

Agentes nuevos (`claude-omni-c`, `claude-omni-e`, `claude-omni-3a`): carpeta propia, para no cambiarle la rama a otro agente del mismo equipo: `git fetch origin && git worktree add ../etd-<tu-rama> -b feature/<tu-rama> origin/main` (por ejemplo `../etd-demo`, `../etd-qa`, `../etd-static`) y trabaja solo dentro de esa carpeta. Nadie hace `git checkout` de otra rama en una carpeta que use otro agente.

**Aviso de integración.** Las dos ramas que traen el LoRA (`feature/data-pipeline@c53d937` y `feature/stats@22b2cb5`) todavía **no están en `main`**: chocan entre sí (§2.1). La fusión está resuelta y probada en el PC1 y entra en `main` cuando el humano diga «integra». Sabrás que ya entró cuando `git cat-file -e origin/main:reports/lora/train_meta.json` no dé error. **Hasta entonces nadie toca `models/`, `reports/lora/` ni `tests/ml/`.** Las tareas marcadas con ⏳ esperan a ese commit (repite `git fetch` cada 10 minutos); las demás empiezan ya.

## 1. Estado verificado por el arquitecto (sáb 23:30)

Medido sobre `main@55eba0b` más las dos ramas pendientes, fusionadas en local. Avance estimado: **~75 %** (era ~68 %).

| Comprobación | Resultado |
|---|---|
| `python -m pytest -q` | 234 passed, **4 failed**, 9 skipped (antes 223 / 1 / 9) |
| Adaptador LoRA | **real**: `models/etd-planner-lora/adapter_model.safetensors`, 25 191 536 bytes, sha256 `70314779040b656cc8ed5e4dac0f4285bd9efc7b392acfa870b003794327341c` (coincide con `reports/lora/train_meta.json`), 192 tensores, 6 291 456 parámetros, las 96 matrices B distintas de cero |
| Planificador por el camino del producto (`AI_MODE=full PLANNER_MODEL=local-lora`, PC1, RTX 4070 SUPER) | responde `planner: "lora"` en 8 de 8 preguntas nuevas y en 50 de 50 de referencia; 9,5 s la primera (carga del modelo), 2,3 s las siguientes |
| Evaluación de antigravity-1: 200 casos de `data/lora/test.jsonl`, semilla 42 | LoRA: JSON válido 100 %, intención 91,5 %, variable exacta 84,5 %, lugar 96,5 %, hipótesis 71,0 % · reglas: 99,5 / 76,0 / 15,5 / 73,5 / 78,5 · modelo base sin adaptador: 35,0 / 3,0 / 4,5 / 47,5 / 0,0 |
| 50 preguntas de referencia (`python -m src.detective.rag.eval_plan`) | reglas **47/50** (eran 49/50) · LoRA **31/50** |
| `data/cases/index.json` | 7 casos; `arctic-seaice` y `antarctic-seaice` siguen con `min(series.raw) = −9999` y `title: {}` |
| Credenciales en el repositorio (todas las ramas) | ninguna |
| Hosting | sin URL pública; Railway sin sesión iniciada en el PC1; el `Dockerfile` ya toma el puerto de `PORT` |
| No existen todavía | `docs/SUBMISSION.md`, `src/ml/MODEL_CARD.md`, `LICENSE`, láminas ni vídeo |

## 2. Lo que encontró la revisión

1. **Dos adaptadores distintos en la misma ruta.** antigravity-1 entrenó en la RTX 4070 SUPER (150 pasos, 353,7 s) y antigravity-2 en la GTX 1650 SUPER (120 pasos, 3,2 h). Los dos subieron a `models/etd-planner-lora/` y a `models/planner-lora/`. El de antigravity-2 lleva en `adapter_config.json` la ruta `C:\Users\docto\.cache\…` (no carga en otro equipo) y su `eval.json` es de 2 casos. **Queda como canónico el de antigravity-1.**
2. **Las variables `planned` se cuelan como analizables (grave).** De los 19 fallos del LoRA en las preguntas de referencia, 15 son variables `planned`: `GPM_IMERG_PRECIP` ×4, `GLDAS_SOILM_0_10` ×3, `MODIS_LST_DAY` ×3, `OMI_O3_TOTAL` ×2, `GLDAS_EVAP` ×2 y `AIRS_SURF_AIR_TEMP` ×1. De los 3 fallos de las reglas, 2 también (`GPM_IMERG_PRECIP` para la lluvia de Madre de Dios y de Tumbes). El conjunto de entrenamiento no contiene ninguna `planned` (0 apariciones): el fallo está en los candidatos que recibe el planificador, no en el modelo. Es la causa de las 2 rojas de `tests/detective/test_pipeline.py`.
3. **El LoRA gana en su conjunto de prueba y pierde en las preguntas escritas a mano.** 84,5 % frente a 15,5 % de variable exacta en los 200 casos (que salen del mismo generador que el entrenamiento) y 31/50 frente a 47/50 en las de referencia. Entrenó 150 pasos: 1 200 ejemplos de 4 323 (0,28 de una época).
4. **Dos pruebas daban por hecho que no había adaptador.** `tests/ml/test_lora_real.py::test_plan_with_lora_missing_adapter_raises_error` falla porque `src/ml/serve.py:65` carga en silencio `models/planner-lora` cuando la ruta pedida no existe: es una sustitución silenciosa, un defecto del producto y no de la prueba. `tests/detective/test_planner.py::test_local_lora_without_serving_falls_back_to_rules` falla porque ahora sí hay adaptador y el plan sale del LoRA.
5. **Casos de hielo marino sin regenerar.** El conector quedó corregido a las 20:10 (`7049bc8`, ya en `main`), pero los casos son de las 19:49. hermes-2 se quedó esperando un aviso que no le llegó.
6. **Las reglas inventan lugares.** «Has Arctic sea ice shrunk since 1980?» → `place: "sea"`, `place_b: "Has"`. «Is the wind getting stronger in Punta Arenas?» → `place_b: "the"`, variable `RH2M`. «…que en los años 80?» → `place_b: "los"`. «What is the meaning of life?» → `define`, `SNODP`, `place: "the"`. No hay ninguna variable de viento en el catálogo.
7. **Dataset del LoRA.** 132 de los 4 323 ejemplos de entrenamiento tienen los años vacíos («entre  y .»). En el de prueba hay preguntas fuera de tema cuya respuesta de referencia trae una variable (id 1 de `reports/lora/predictions.jsonl`).
8. **`docs/EVAL_IA.md` está desfasado:** dice reglas 49/50 y «LoRA: no disponible».
9. **`requirements.txt` no fija versiones y no hay archivo con las dependencias del LoRA** (torch, transformers, peft, bitsandbytes, accelerate): quien clone el repositorio no puede reproducir el planificador local.
10. **Material de entrega: nada todavía** (§1). La guía dice que la mayor parte de la nota sale de la página del proyecto.

## 3. Reglas nuevas (se suman a las 18 anteriores)

19. **Una variable `planned` nunca es candidata.** Ni las reglas ni el LoRA pueden devolverla en un plan que no sea `no_match`. La API no la analiza y la interfaz no la deja elegir.
20. **El LoRA se cita siempre con sus dos números juntos:** los 200 casos de prueba (misma plantilla que el entrenamiento) y las 50 preguntas de referencia (escritas a mano). Nadie escribe uno sin el otro, en ningún texto.
21. **Un solo adaptador canónico:** `models/etd-planner-lora/` (sha256 del §1). Cualquier otro va a una carpeta con sufijo (`-v2`) y solo lo sustituye el arquitecto, con evidencia de que gana en las dos evaluaciones.
22. **Las pruebas no dependen de lo que haya en el disco.** Simulan tanto la ausencia como la presencia del adaptador. Las que cargan el modelo real se saltan sin GPU.
23. **Ninguna credencial en el repositorio:** ni en código, ni en reportes, ni en capturas, ni en la URL de un remoto. `scripts/gate.py` falla si encuentra un token.
24. **Agentes nuevos: rama y carpeta propias, no tocan `src/`.** Lo que encuentren roto se lo pasan al dueño del carril en «Avisos para otros carriles» de su bloque ESTADO.
25. **`main` solo lo mueven el arquitecto y, de suplente, claude-omni-3**, y este solo con `python -m pytest -q` entero **sin rojas** pegado en su reporte. Nunca con `--force`.

## 4. Quién es quién y qué hace

| En la pantalla del humano | Identificador | Equipo | Rama | Carril |
|---|---|---|---|---|
| claude | cfable (arquitecto) | PC1 | `integracion/ronda4` → `main` | integración, este documento, despliegue |
| Antigravity | antigravity-1 | PC1 (RTX 4070 SUPER) | `feature/data-pipeline` | `src/etl/`, `data/raw/` y las ejecuciones del LoRA en la 4070 |
| Antigravity pc2 | antigravity-2 | pc-principal (GTX 1650 SUPER) | `feature/stats` | `src/stats/`, `src/ml/`, `tests/stats/`, `tests/ml/` |
| Claude Omni 1 | claude-omni-1 | PC1 | `feature/ui` | `src/ui/`, `scripts/take_real_screenshots.py`, `docs/media/` |
| Claude Omni B | claude-omni-1b | PC1 | `feature/catalog` | `data/catalog/`, `data/knowledge/`, `README.md`, `LICENSE`, `docs/SUBMISSION.md`, `docs/REFERENCES.md`, `docs/AI_USE_LOG.md` |
| Claude Omni 2 | claude-omni-2 | pc-principal | `feature/wizard` | `src/detective/`, `tests/detective/`, `docs/EVAL_IA.md` |
| Claude Omni 3 | claude-omni-3 | 192.168.18.24 | `feature/api` | `src/api/`, `tests/api/`, `scripts/gate.py`, `scripts/smoke_api.py`, `Dockerfile`, `requirements.txt` |
| hermes 2 | hermes-2 | 192.168.18.24 | `feature/scrapes` | `data/cases/`, `data/atlas/`, `data/lora/` y sus scripts |
| Claude Omni 3a | claude-omni-3a (nuevo) | 192.168.18.24 | `feature/static` | `scripts/build_static.py`, `tests/api/test_static_build.py`, rama `gh-pages` |
| CLAUDE OMNI C | claude-omni-c (nuevo) | PC1 | `feature/demo` | `docs/demo/`, `scripts/make_demo.py` |
| CLAUDE OMNI E | claude-omni-e (nuevo) | PC1 | `feature/qa` | `reports/qa/` (no arregla código) |
| Hermes | hermes-1 | PC1 | — | sigue fuera (decisión del humano del sábado 18:00) |

### claude-omni-2 — detective con IA · `feature/wizard`
1. **Dom 01:30.** Regla 19: quita las `planned` de donde se construyen los candidatos (la recuperación de fichas y `_local_lora`), para las reglas y para el LoRA. Las 2 rojas de `tests/detective/test_pipeline.py` vuelven a verde sin tocar la aserción (regla 13). Prueba nueva: con las 50 preguntas de referencia y las 10 `planned`, ningún plan devuelve una `planned` salvo como `no_match` con su nota.
2. **Dom 02:00.** Lugares (§2.6): un lugar solo se acepta si el gazetteer lo resuelve; una pregunta fuera de tema sale `out_of_scope` sin variables; una variable que no existe (viento) sale `no_match`. Pruebas con las 4 frases del §2.6.
3. ⏳ **Dom 02:30.** `test_local_lora_without_serving_falls_back_to_rules` (regla 22): la prueba simula la ausencia haciendo que `src.ml.serve.plan_with_lora` lance una excepción. Añade las dos contrarias con un `plan_with_lora` simulado: plan válido → `planner: "lora"`; plan con una `planned` → rechazado y vuelta a las reglas con `note`.
4. ⏳ **Dom 04:00.** Evaluación final en `docs/EVAL_IA.md`, en inglés: reglas y LoRA sobre las 50 preguntas (`python -m src.detective.rag.eval_plan` y `AI_MODE=full PLANNER_MODEL=local-lora python -m src.detective.rag.eval_plan --planner local-lora`), con la tabla de fallos de los dos y el tiempo por pregunta. Se publica como salga. Si tu equipo no puede cargar el modelo, pídeselo a antigravity-1 (en el PC1 son 2,3 s por pregunta).
5. **Dom 09:00.** Aplica la decisión del §5.2 con esos números. `/api/ai/plan` devuelve siempre `planner` y, si hubo respaldo, `note`. Avisa a claude-omni-1 del texto que debe mostrar.

### antigravity-2 — estadística y `src/ml/` · `feature/stats`
1. **Ya.** Tu adaptador de la GTX 1650 no entra (§2.1). Para la evaluación de 632 casos y no subas nada más a `models/` ni a `reports/lora/`.
2. ⏳ **Dom 02:00.** `src/ml/serve.py:65`: quita el respaldo silencioso a `models/planner-lora` y borra esa carpeta duplicada con `git rm`. `test_plan_with_lora_missing_adapter_raises_error` vuelve a verde sin tocar la aserción. Añade la prueba contraria, que carga el adaptador real y se salta sin GPU (regla 22).
3. **Dom 03:00.** `requirements-ml.txt` con las versiones exactas del entrenamiento (torch 2.6.0+cu124, transformers 5.23.0, peft 0.21.3, bitsandbytes 0.50.2, accelerate 1.15.0) y los dos comandos que reproducen entrenamiento y evaluación.
4. ⏳ **Dom 09:00.** `src/ml/MODEL_CARD.md` en inglés, solo con cifras de `reports/lora/eval.json`, `reports/lora/train_meta.json` y `docs/EVAL_IA.md` (regla 20). Sección «Limitations» obligatoria: 150 pasos (0,28 de una época); el conjunto de prueba sale del mismo generador que el entrenamiento; la hipótesis acierta menos que las reglas (71,0 % frente a 78,5 %); modelo base `HuggingFaceTB/SmolLM2-1.7B-Instruct` con su licencia.
5. **Dom 09:00.** `docs/VALIDACION_ESTADISTICA.md`: la regla de los cuatro veredictos en un párrafo en inglés y la tabla «published vs. computed» rehecha con el hielo marino ya sin −9999 (los números se los pides a hermes-2).

### antigravity-1 — datos de la NASA y GPU del PC1 · `feature/data-pipeline`
1. **Ya.** Tu adaptador es el canónico (regla 21). No vuelvas a subir nada a `models/etd-planner-lora/`.
2. **Dom 02:30.** Viento: `WS2M` de NASA POWER en el conector, con una respuesta real guardada en `tests/fixtures/real/`, rango físico y prueba. Si sobra tiempo, `T2M_MAX` y `T2M_MIN` de la misma forma, de una en una. Avisa a claude-omni-1b para la ficha.
3. ⏳ **Dom 06:00, experimento con hora de corte.** LoRA v2 en `models/etd-planner-lora-v2/`: misma receta y semilla, 2 épocas completas, descartando al cargar los ejemplos con años vacíos (di cuántos). Evaluación con los mismos 200 casos (semilla 42) y con las 50 preguntas de referencia. Evidencia de la regla 15 en `reports/lora/v2/`. Solo sustituye al v1 si gana en las dos (regla 21); si no, se queda fuera y se cuenta en tu reporte.
4. **Cuando el humano deje CSV nuevos** en `data/raw/giovanni/`: valídalos y avisa a claude-omni-1b.
5. **Dom 09:00.** Compara T2M y PRECTOTCORR de POWER regional con los dos CSV de Giovanni (misma caja y periodo): diferencia media y correlación, y una frase en inglés para claude-omni-1b.

### hermes-2 — casos, atlas y dataset · `feature/scrapes`
1. **Dom 01:00. Ya no estás bloqueado:** el arreglo de NSIDC está en `main` desde las 20:10. Regenera `arctic-seaice` y `antarctic-seaice` (`python -X utf8 -I scripts/regenerate_cases_v2.py`). Evidencia: `python scripts/verify_seaice_cases.py` en verde, mínimo de `series.raw` ≥ 0, `1987-12` y `1988-01` en `null`, y mínimos cuadrados y Sen con el mismo signo. Si a la hora de integrar siguen con −9999, los regenera el arquitecto.
2. **Dom 02:00.** Título y frase de hallazgo en inglés y español para los 7 casos, solo con sus números (`scripts/write_case_copy.py`). `index.json` sin títulos vacíos.
3. **Dom 04:00.** Dataset (§2.7): mide los dos defectos en train, val y test y descríbelos en `data/lora/DATASET_CARD.md`, en inglés, con las cifras. No sobrescribas `data/lora/*.jsonl`: el adaptador se entrenó con ellos.
4. **Dom 09:00.** Tabla comparativa de los 7 casos en tu reporte (veredicto, pendiente con unidades, valores p de cada prueba, años que faltan) para que el humano elija el caso protagonista.

### claude-omni-1 — interfaz · `feature/ui`
1. **Dom 02:00.** Comprueba en navegador, sobre `main` y en inglés, lo que diste por hecho en la Ronda 3, con una captura de cada punto en tu reporte: citas con título y editor enlazados; rótulo «Excerpts from cited sources (no generative AI)» en modo extractivo; panel de pruebas que discrepan; galería con los 7 casos; atlas; GISTEMP y hielo marino sin pedir un punto en el mapa; subida de `data/raw/giovanni/T2M__amazonia.csv`.
2. **Dom 04:00.** Muestra quién planificó: «Planned by: fine-tuned model (LoRA)» o «Planned by: rules», y la nota cuando hubo respaldo. Las `planned` aparecen como «Not loaded yet — upload its Giovanni CSV» y no se pueden elegir (regla 19).
3. **Dom 04:00.** Móvil, 390 px de ancho: sin desplazamiento horizontal, con el mapa y la gráfica utilizables. Los jueces abren el enlace desde el teléfono.
4. **Dom 11:00, después de la integración de las 10:00.** Repite las 6 capturas y añade 2 (galería de casos y «Planned by»), en inglés, a 1600×900, desde `main` o desde la URL pública si ya existe.

### claude-omni-1b — catálogo y textos de entrega · `feature/catalog`
1. **Dom 04:00.** `docs/SUBMISSION.md`: todos los campos del formulario (`docs/KIT_ENTREGA.md` §4), en inglés, solo con hechos de bloques VERIFICADO y del §1 de este documento. El LoRA, con la regla 20. Sección «Limitations». Deja `<<HUMANO: …>>` donde falte su decisión: equipo y miembros, caso protagonista, «What we hope to achieve», enlace de la demo y URL.
2. **Dom 04:00.** `LICENSE` con la licencia MIT para el código (el humano puede vetarla hasta las 14:00) y una línea en el README: los datos conservan las condiciones de su fuente.
3. **Dom 09:00.** README: el modelo con sus dos números, cómo activar el planificador local (`pip install -r requirements-ml.txt` y `AI_MODE=full PLANNER_MODEL=local-lora`) y la URL pública cuando exista.
4. Da de alta lo que valide antigravity-1 (`WS2M` y cada CSV de Giovanni, que deja de ser `planned`), con ficha y fuente. `python scripts/validate_knowledge.py` en verde.
5. **Dom 12:00.** `docs/REFERENCES.md` y `docs/AI_USE_LOG.md` completos: cada herramienta y modelo que usó cada agente (cabeceras `SI-assisted:` e historial de git), datos, librerías y el modelo base con su licencia.

### claude-omni-3 — API y contrato · `feature/api`
El respaldo estático (A6) pasa a claude-omni-3a.
1. **Dom 01:30.** Regla 19 en la API: `/api/catalog/variables` publica las `planned` aparte y nunca las cuenta como disponibles; `/api/analyze`, `/api/series` y `/api/report` con una `planned` responden un error claro, en el idioma pedido, que explica cómo cargarla. Añádelo a `scripts/smoke_api.py`.
2. **Dom 04:00.** Listo para Railway: `requirements.txt` con versiones fijadas (`==`, las del entorno que pasa la suite), arranque comprobado en un entorno limpio con las variables del `Dockerfile`, sin torch en la imagen. Mide 20 peticiones simultáneas a `/api/analyze` y pega los tiempos: la caché y el límite de peticiones tienen que aguantar a los jueces.
3. **Dom 09:00.** `scripts/gate.py` en verde sobre `main`. Añade tres comprobaciones: ninguna `planned` analizable, ningún valor fuera de rango físico en `data/cases/` y ningún token en el repositorio (regla 23).
4. **En cuanto haya URL** (la despliega el arquitecto desde el PC1): `python scripts/smoke_api.py <URL>` con latencias en tu reporte, y otra vez a las 12:00, 16:00 y 19:00.
5. Integrador suplente con la regla 25.

### claude-omni-3a — respaldo estático · `feature/static` (nuevo)
1. **Dom 02:30.** `python scripts/build_static.py --from-cases` sobre `main` → `dist/` con los casos, el atlas y la interfaz en inglés, servido por cualquier servidor estático. Compruébalo con Playwright: casos, gráfica, veredicto, procedencia y cambio de idioma. Lo que necesita la API viva (otro lugar, el detective) muestra un aviso claro, «Live analysis needs the full app», nunca un error.
2. **Dom 04:00.** Publicación sin servidor: sube `dist/` a la rama `gh-pages` (solo esa rama) y deja en tu reporte los clics para activar GitHub Pages y la alternativa de arrastrar `dist.zip` a Netlify. El nombre del repositorio termina en punto: si el humano activa Pages, comprueba que la ruta carga; si no carga, dilo.
3. **Dom 10:30, tras la integración de las 10:00.** Regenera y vuelve a publicar con los casos finales. Evidencia: ningún −9999 dentro de `dist/`.

### claude-omni-c — demo · `feature/demo` (nuevo)
1. **Dom 04:00.** `docs/demo/slides.html` y `docs/demo/EarthTrend_Detective.pdf`: 7 láminas en inglés, 16:9, con la estructura de `docs/KIT_ENTREGA.md` §5, capturas reales de `docs/media/` y cifras de bloques VERIFICADO y del §1 (regla 20). Sin logotipos ni insignias de la NASA y sin personas. `<<HUMANO: …>>` para equipo y miembros. Evidencia: PDF de 7 páginas exactas.
2. **Dom 09:00.** Vídeo: guion de 28 s (`docs/KIT_ENTREGA.md` §5), `docs/demo/subtitles_en.srt` y grabación automática de la interfaz real con Playwright (`scripts/make_demo.py`, 1920×1080), montada con ffmpeg y subtítulos incrustados: `docs/demo/demo_28s.mp4`, de 30,0 s como máximo (compruébalo con ffprobe) y menos de 15 MB. Sin voz sintética ni música. Caso: el que elija el humano; si no ha elegido, `lima-t2m`.
3. **Dom 12:30.** Rehaz láminas y vídeo con las capturas finales de claude-omni-1 y contra la URL pública.

### claude-omni-e — control de calidad como juez · `feature/qa` (nuevo)
No arreglas código: encuentras, pruebas y se lo pasas al dueño del carril (regla 24).
1. **Dom 03:00, informe 1** (`reports/qa/informe-1.md`). Clon limpio en una carpeta temporal y `README.md` seguido al pie de la letra (entorno nuevo, solo `requirements.txt`): si un paso falla, es un hallazgo. Recorre con Playwright, en inglés y en español, a 1440 px y a 390 px: (a) temperatura de Lima; (b) «Is it raining less in Piura than it used to?» al detective; (c) hielo marino del Ártico; (d) comparar Piura y Arequipa; (e) mapa de tendencias; (f) una pregunta fuera de tema; (g) una variable `planned`; (h) subir el CSV de Giovanni; (i) galería de casos; (j) cambiar de idioma a mitad. Captura y pasa o falla de cada uno. Lista de defectos con gravedad (bloquea la entrega / lo ve el juez / menor), archivo y línea si lo encuentras, y dueño. Busca además: mezcla de idiomas (regla 16), cifras que no coinciden entre texto, gráfica y JSON, valores imposibles, enlaces rotos en README y REFERENCES, marcas de la NASA y textos que dicen «AI» donde el modo es extractivo.
2. **Dom 09:00, informe 2**, sobre `main` actualizado: qué defectos se cerraron y cuáles reabres. Puntúa de 1 a 5 cada criterio del jurado (Impact, Creativity, Validity, Relevance, Presentation) para `docs/SUBMISSION.md` y las láminas, con la evidencia que falta para subir cada nota.
3. **Dom 13:00, informe 3**, contra la URL pública, en ventana de incógnito y en móvil, y con todos los enlaces de `docs/SUBMISSION.md` probados.

## 5. Decisiones del arquitecto

1. **Adaptador.** En el choque de las dos ramas quedan los archivos de `feature/data-pipeline` en `models/`, `reports/lora/` y `src/ml/eval_lora.py`. De `feature/stats` entran `src/ml/serve.py`, `src/stats/trend_engine.py` (`variable_id: null`) y su reporte.
2. **Quién planifica.** En la URL pública planifican las reglas (el servidor no carga el modelo) y la explicación es extractiva. En local, el LoRA es el planificador por defecto solo si, con la regla 19 aplicada, iguala o supera a las reglas en las 50 preguntas; si no, las reglas siguen por defecto y el LoRA es una opción visible con sus números reales. En los dos casos el plan del modelo pasa por la validación: variable disponible y lugar que el gazetteer resuelve. El modelo propone y las reglas comprueban.
3. **Despliegue.** Railway, desde el PC1 y por el arquitecto, cuando el humano inicie sesión. Si no hay sesión el domingo a las 12:00, se entrega el respaldo estático de claude-omni-3a.
4. **Demo.** Se preparan las dos (7 láminas y vídeo de 30 s o menos) y el humano elige cuál entrega.
5. **Arreglos fuera de carril autorizados en esta ronda:** antigravity-1 ejecuta el LoRA en la 4070 y escribe en `reports/lora/v2/` y `models/etd-planner-lora-v2/`; claude-omni-3a hereda `scripts/build_static.py` y `tests/api/test_static_build.py`; antigravity-2 crea `requirements-ml.txt`.

## 6. Pendiente del humano

1. **«integra»**: mete en `main` la fusión de las dos ramas del LoRA. Sin eso, las tareas ⏳ no arrancan.
2. **Hosting:** `railway login` en el PC1 y después «despliega». Sin URL pública no hay entrega; el plan B es el respaldo estático.
3. **Decisiones (PLAN §7):** nombre del equipo y miembros (máximo 6, todos inscritos en el mismo evento local), caso protagonista, qué demo se entrega y si vale la licencia MIT.
4. **Opcional y valioso:** CSV de Giovanni de otros instrumentos (GPM IMERG, MODIS NDVI, OMI) en `data/raw/giovanni/`. Cada uno convierte una `planned` en disponible.
5. **Página del proyecto** en la web de Space Apps: pegar los textos de `docs/SUBMISSION.md`, subir capturas y demo, y «Submit for Judging» a las 20:00.
6. Revocar el token de GitHub cuando termine el hackathon.

## 7. Puertas

| Puerta | Hora | Condición |
|---|---|---|
| Integración 1 | dom 02:30 | suite sin rojas, hielo marino sin −9999, ninguna `planned` analizable |
| G3 | dom 09:00 | `docs/EVAL_IA.md` final, `MODEL_CARD.md`, borrador de `docs/SUBMISSION.md`, 7 láminas, respaldo estático, informe 1 de calidad |
| Integración 2 y despliegue | dom 10:00 | `main` integrado y desplegado (necesita la sesión de Railway) |
| URL | dom 12:00 | `smoke_api.py` en verde contra la URL, capturas finales |
| Congelación | dom 14:00 | regla 18: solo arreglos con evidencia |
| Textos | dom 16:00 | el humano revisa `docs/SUBMISSION.md` en inglés |
| G4 | dom 18:00 | página, demo y enlaces probados en incógnito y en móvil |
| ENTREGAR | dom 20:00 | «Submit for Judging» |
