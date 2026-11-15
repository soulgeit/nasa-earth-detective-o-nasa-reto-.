<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-2 — 2026-11-15 08:20 (hora de Perú)
Rama@commit: feature/wizard@e701385 · empujado: sí · base: integracion/ronda5
VERIFICADO: suite completa → `python -m pytest -q` → 284 passed, 0 failed, 10 skipped
VERIFICADO: §4.1 docs/SUBMISSION.md → un apartado por campo de KIT_ENTREGA §4; todas las cifras con su comando; enlaces comprobados (200)
VERIFICADO: §4.2 uso de IA → párrafo del formulario + dos filas nuevas en docs/AI_USE_LOG.md
VERIFICADO: §4.3 fuentes de la explicación → `grep -c "Hermes 1" data/knowledge/docs.jsonl` → 0; validate_knowledge 168 documentos sin fallos; texto sin URLs y con el editor real
VERIFICADO: §4.4 docs/EVAL_IA.md → LoRA 40/50 en GPU (2,2 s) + 37/50 en CPU (13,7 s) + reglas 50/50; decisión escrita: el producto planifica con reglas
VERIFICADO: §4.5 reglas 50/50 = 1.000 y recuperación P@1 1.000 (era 49/50 y 0.980)
VERIFICADO: tests/detective → 155 passed
ESCRITO (sin ejecutar de punta a punta): nada pendiente en mi carril
ROTO / NO HECHO: el LoRA no se re-evaluó en GPU desde este equipo (no hay RTX 4070 aquí); la cifra 40/50 y 2,2 s es la del arquitecto, citada como suya
Siguiente paso: si el humano escribe «integra», nada más por mi parte; la Ronda 5 cierra mi carril
Necesito de: humano: decidir equipo/miembros, URL de la app completa y caso de la demo (los tres están como <<HUMANO>> en docs/SUBMISSION.md)
Avisos para otros carriles: el léxico del detective ahora trata las frases multi-palabra como frases; si alguien añade alias, que use la frase completa ("turning into desert") y no la palabra suelta
Avisos: los textos de SUBMISSION citan 50/50 y 40/50 juntos; si antigravity-1 entrega el LoRA v2, hay que rehacer las dos cifras
<!-- ESTADO:FIN -->

# claude-omni-2 — detective con IA (RAG, planificador, explicación con guardián)

Rama de trabajo: `feature/wizard` · Carpetas: `src/detective/`, `tests/detective/`, sección RAG de `docs/EVAL_IA.md`

## Entorno (14-nov-2026, PC1)

- Python 3.12 no estaba en PATH; se creó `.venv` con `uv` sobre **CPython 3.11.15**.
  Instalado: `numpy 2.4.6`, `scipy 1.17.1`, `requests 2.34.2`, `pytest 9.2.0`, `pypdf 7.1.0` (solo para leer el PDF de Peel 2007).
- **Ollama no estaba en marcha** durante toda la sesión (`curl localhost:11434` → conexión rechazada y
  `ollama` no está en PATH). Por eso todo se construyó y se verificó en `AI_MODE=extractive`.
  No se detuvo, descargó ni arrancó ningún modelo (regla 13).

## R1 — Recuperación — LISTO (14-nov-2026)

Rama@commit: `feature/wizard@9e7bdc5` (commit local; push pendiente)

**Qué quedó**
- `src/detective/rag/`: BM25 Okapi propio, vectores por embeddings con caché `.npz`, fusión RRF,
  `retrieve(query, lang, k, types)` con `score/title/url/type`.
- `src/detective/corpus.py`: carga `data/knowledge/docs.jsonl` si existe; si no, deriva tarjetas de
  `data/catalog/variables.json` o de la semilla. Nunca inventa documentos.
- `src/detective/lexicon.py`: ampliación de consulta coloquial es/en → `variable_id` (dato lingüístico,
  sin definiciones ni cifras del catálogo).
- `python -m src.detective.rag.build_index` reconstruye el `.npz`; se invalida si cambia el corpus.

**Evidencia**
- `python -m src.detective.rag.eval` → BM25 P@1 1.000, P@3 1.000, MRR 1.000 sobre 15 preguntas
  provisionales. `vectors` vacío: no hay servicio de embeddings (declarado en `docs/EVAL_IA.md`).

**Riesgos**
- El corpus actual son 50 tarjetas derivadas de la semilla: los textos son cortos (nombre + unidad).
  Cuando Hermes 1 entregue `docs.jsonl` (artículos NASA, perfiles de bioma) la recuperación mejora sola.
- `EMBED_MODEL` vacío ⇒ columna `vectors` sin medir. **No se maquilla**: la tabla lo dice.

## R2 — Evaluación de la recuperación — LISTO (14-nov-2026)

**Qué quedó**: `src/detective/rag/eval.py` (P@1, P@3, MRR por backend; `--json`), tabla en `docs/EVAL_IA.md`.
15 preguntas provisionales escritas antes de mirar resultados (`tests/detective/golden_questions.provisional.jsonl`,
marcadas `"provisional": true`). Se sustituyen por las 50 de Hermes 1 sin tocar código.

**Evidencia**: ver bloque `TABLA_R2` de `docs/EVAL_IA.md`.

## R3 — `plan()` — LISTO (14-nov-2026)

**Qué quedó**: `src/detective/planner.py` con validación dura (JSON, `variable_ids ⊆ candidatas`,
`place` subcadena literal, años válidos), un reintento, y respaldo por reglas. `"mode"` siempre presente.
El mensaje al modelo es el mismo formato del dataset LoRA y el `system` se lee de `data/lora/system_prompt.txt`;
si no existe, no se llama al modelo (se informa en `note`) para no romper el contrato entrenamiento==uso.

**Evidencia**
```
plan("¿está lloviendo menos en Piura?") →
{'intent': 'investigate', 'variable_ids': ['PRECTOTCORR'], 'place': 'Piura',
 'hypothesis': 'down', 'lang': 'es', 'mode': 'rules'}
```

**Necesito de otros**: Hermes 2 debe publicar `data/lora/system_prompt.txt` para que el camino LoRA
sea idéntico al entrenamiento. Antigravity 2, confirmar el formato exacto de `CANDIDATES:`.

## R4 — `geocode()` — PARCIAL (14-nov-2026)

**Qué quedó**: `src/detective/gazetteer.py` con coincidencia exacta, sin tildes, por prefijo y difusa
(≥0.86), desempate por población. Sin resultado → `[]` (la UI pide clic en el mapa). Nunca se piden
coordenadas a un modelo. `AI_GEOCODE_ONLINE=1` habilita Nominatim (ODbL) como respaldo explícito, apagado por defecto.

**Bloqueado por**: `data/catalog/gazetteer.json` no existe todavía (es de Hermes 1, tarea C2).
Hoy `geocode("Piura")` devuelve `[]`, que es el comportamiento correcto pero no útil.
La lógica está probada con un gazetteer temporal en `tests/detective/test_geocode.py` (8 pruebas).

## R5 — `scout()` — PARCIAL (14-nov-2026)

**Qué quedó**: `src/detective/scouting.py` + `src/detective/koppen.py`.
Clasificación de Köppen-Geiger completa con las reglas de **Peel et al. (2007), Tabla 1**
(leído el PDF: `https://hess.copernicus.org/articles/11/1633/2007/hess-11-1633-2007.pdf`,
HTTP 200, 1 712 278 bytes). Incluye la desviación documentada del propio artículo:
la frontera C/D usa `Tcold > 0 °C` (Russell 1931), no `−3 °C`, y **el grupo B se identifica primero**
(cita textual del artículo: *"the B climates must be identified first"*).

**Evidencia** — con la muestra real `tests/fixtures/real/power_monthly_point_lima.json`
(T2M + PRECTOTCORR, 1981–2025, sin relleno), Lima clasifica:

```
KÖPPEN: BWh | árido o semiárido, desierto, caliente
DIAG: {'t_cold': 16.72, 't_hot': 19.93, 'map_mm': 30.1, 'mat_c': 18.19}
CRIT: {'p_threshold': 64.38, 'season_summer_share': 0.762}
```

**Bloqueado por**: `src/etl/registry.py::get_series` aún no existe (carril de Antigravity 1).
`scout()` lo detecta, lo dice en `place.etl.reason` y sigue devolviendo candidatas documentales.
También falta `gazetteer.json` para la regla de «gran ciudad a menos de 50 km».

## R6 — `explain()` con guardián — LISTO (14-nov-2026)

**Qué quedó**: `src/detective/narrative.py` + `src/detective/guard.py`.
Dos párrafos; párrafo 1 con las cifras de los hechos, párrafo 2 con hipótesis citadas `[n]`.
Guardián determinista: cifras (redondeo por precisión del token), citas existentes, idioma pedido,
y rechazo de exceso causal en **ambos** idiomas cuando el veredicto no es significativo.
Un reintento y luego respaldo extractivo (plantilla de `answers` + fragmentos tal cual).

**Evidencia**
```
pytest tests/detective/test_guard.py -q  →  15 passed
10 textos trampa (cifras/años inventados + «demuestra»/«proves») → 10/10 rechazados
```

**Riesgos**: el prompt del explicador y el guardián están afinados con el corpus de la semilla.
Con artículos largos de Hermes 1, revisar que el guardián no rechace citas legítimas.

## R7 — Pruebas — LISTO (14-nov-2026)

**Evidencia**
```
$ .venv/Scripts/python.exe -m pytest tests/detective -q
98 passed in 0.37s
```
Cubre: guardián (10 trampas + tolerancias), validación del plan, geocodificador,
Köppen (incluidos los casos límite `B` antes de `A`, `Dfd`, `Csa`, `ET`, `EF`) y
20 preguntas de punta a punta que **bloquean sockets**: si algo intentara salir a la red, el test fallaría.

## Notas de integración (para Claude Omni 3 y Claude Omni 1)

- API pública tal cual el contrato §6: `from src.detective import retrieve, plan, scout, explain, geocode`.
- ⚠️ **Colisión de nombres resuelta**: los módulos se llaman `narrative.py`, `scouting.py` y `gazetteer.py`
  precisamente para que `from src.detective import explain` devuelva la **función** y no el módulo.
- `scout()` devuelve `{"place": {...}, "candidates": [...], "query_used", "method"}`; si el ETL falta,
  `place.etl.available = false` con el motivo. La UI debería mostrarlo, no ocultarlo.
- `explain()` siempre trae `guard` con `numbers_ok/citations_ok/language_ok/no_overclaim/retries/reasons`.
- `plan()` puede traer `note` cuando el camino LoRA no se pudo usar; la UI puede ignorarlo.
- El antiguo `wizard.py` (diccionario de 4 opciones con regiones inventadas) ya no se importa desde
  `src/detective/__init__.py`. **Sugerencia al arquitecto**: borrarlo cuando la UI deje de nombrarlo.

## Registro de IA

Fila añadida en `docs/AI_USE_LOG.md`. Todos los archivos nuevos llevan `SI-assisted: claude-omni-2 (Claude Opus 5.5)`
como primera línea.

## S0 — Verificación de las 13 fuentes aportadas por el humano — LISTO (14-nov-2026)

Recibidas de un mensaje del humano el 14-nov-2026. **Ninguna se citó sin abrirla.**
Comando: `requests.get(url, timeout=30)` con `certifi 2026.10.23` (regla 14: sin `verify=False`).

| # | URL | HTTP | Qué es, comprobado en la propia página | ¿Sirve al producto? |
|---|---|---|---|---|
| 1 | `giovanni.gsfc.nasa.gov/giovanni/` | 200 | GES DISC Giovanni | **Sí** — vía para los CSV de GPM/GLDAS/AIRS/OMI/MODIS (ya prevista en `data/raw/giovanni/README.md`) |
| 2 | `disc.gsfc.nasa.gov/...Hydrology Time Series` | 200 | Página de GES DISC (2 828 B de shell; herramienta **descontinuada**, como ya consta en `prompts/00_LEER_PRIMERO.md`) | No — no meter como conector |
| 3 | `appeears.earthdatacloud.nasa.gov` | 200 | AppEEARS (extracción por punto/área, requiere Earthdata) | Complementaria, no para el MVP |
| 4 | `ncei.noaa.gov/cdo-web/` | 200 | NOAA CDO (observaciones in situ de EE. UU.) | No prioritario: cobertura global limitada |
| 5 | `ntrs.nasa.gov/.../20090042747.pdf` | 200, PDF 8,8 MB, 27 p | **Acker et al. (2009)**, *Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions*, EARSeL eProceedings 8(2). Verificado también por `ntrs.nasa.gov/api/citations/20090042747` (título, autores, publicación) | **Sí, como `method_note`**: es un caso NASA real de detección de tendencias en series mensuales |
| 6 | `climexp.knmi.nl` | 200 | KNMI Climate Explorer | No para el producto; herramienta de referencia |
| 7 | `medium.com/...statistical-test-methods...` | 200 | Blog divulgativo (OLS, Mann-Kendall, Seasonal Kendall, raíz unitaria) | Solo como lectura. **No citable**: no es fuente primaria |
| 8 | `statsig.com/.../statistical-significance` | 200 | Blog de *experimentación de producto* (A/B testing) | **No sirve**: mide experimentos aleatorizados, no tendencias en series temporales |
| 9 | `donnees-data.asc-csa.gc.ca/en/dataset/rcm` | **TLS falla** | `SSLCertVerificationError: unable to get local issuer certificate` — el host sirve la **cadena de certificado incompleta**. Certificado no emitido a tiempo, no es un fallo de `certifi` (probado con el paquete actualizado) | **No verificable**. No se cita; no se desactiva TLS (regla 14) |
| 10 | `geo.ca/` | 200 | Portal GEO.ca (Gobierno de Canadá) | No prioritario |
| 11 | `asc-csa.gc.ca/eng/satellites/swot/` | 200 | CSA: **«Launch: December 16, 2022»**, misión NASA+CNES con CSA y UKSA | **Sí**, como cita de la fecha de lanzamiento de SWOT |
| 12 | `asc-csa.gc.ca/.../monitoring-and-protecting-our-ecosystems-from-space.asp` | 200 | CSA, observación de ecosistemas | Contexto |
| 13 | `github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial` | 200 | Tutorial de SAR de la CSA | No aplica (no usamos SAR) |

### Dos cosas que salieron de aquí y que **no son mías**

1. **La fecha de lanzamiento de SWOT, ahora con fuente primaria.** La página de la CSA
   (#11) dice literalmente *"Launch: December 16, 2022"*. La auditoría del arquitecto
   (`docs/PLAN_GANADOR.md` §1) ya señalaba que la serie «SWOT 2000–2024» es imposible;
   ahora hay cita verificable para respaldarlo.
   **Sigue en el repo**: `data/processed/aral_sea_SWOT_WATER_ELEV.json` y
   `data/variables_catalog.json:67`. La v2 ordena borrarlos (`docs/CONTRATOS.md` §1) y todavía están.
   Carril del arquitecto / Antigravity 1 — no los toco desde aquí.

2. **Material para el corpus (Hermes 1).** #5 (Acker et al. 2009) y #11 son documentos
   verificados y con URL viva que encajan en `data/knowledge/docs.jsonl` como
   `method_note` y `nasa_article`. `data/knowledge/` y `docs/REFERENCES.md` son su carril;
   le paso la tabla tal cual.

### Lo que descarto y por qué

- **#8 (Statsig)**: su marco es inferencia sobre experimentos controlados. Aplicarlo a una
  serie temporal observacional es justo el error que el reto castiga.
- **#7 (Medium)**: útil para que el equipo repase Seasonal Kendall, pero no es citable
  ante un juez. Sería `type: method_note` con `"summary_by"` si Hermes 1 lo quisiera.
- **#9**: no verificable sin desactivar TLS. Queda fuera.
- **#2**: la herramienta de Hydrology Time Series está descontinuada (ya documentado en el
  repo); la URL responde porque es la ficha de la herramienta, no un servicio vivo.

### Impacto en mi carril

Ninguno negativo: `src/detective/` no usa SWOT ni ninguno de estos conectores directamente.
La #5 refuerza el enfoque del guardián (cifras solo desde el motor estadístico) y confirma
que la detección de tendencias en series **mensuales** con pocos años es un problema real
que incluso un equipo de la NASA trata con cuidado.

---

# Ronda 2 — detalle de las tareas

## T1 — Citaciones por variable analizada · VERIFICADO

**Problema visto por el arquitecto:** al explicar T2M de Lima se citaban cinco fichas
de aerosoles y GISTEMP, con ids internos (`[var-aod_55-es]`) y todas rotuladas
«NASA Earth Observatory».

**Causa raíz (reproducida):** `_passages_for` construía una sola bolsa de palabras
(`"Temperatura del aire a 2 m T2M Lima, Peru"`), la ampliación léxica metía AOD_55 y
GISTEMP por el alias «aire»/«temperatura», y la recuperación devolvía 4 fichas de AOD
antes de cualquier T2M. Además el corpus tenía **30 fichas duplicadas** (las de
`docs.jsonl` más otra copia derivada del catálogo).

**Arreglos:**
1. `_passages_for` recupera por `variable_id` y solo acepta documentos que lleven esa
   variable; después, como mucho un artículo de la región y un `method_note`.
2. Deduplicación por URL normalizada: la misma página en dos idiomas es una cita.
3. `load_corpus` ya no deriva tarjetas del catálogo si `docs.jsonl` las trae: 196 → 166
   documentos, cero duplicados.
4. Las citas exponen `title`, `url` y `publisher` reales; el id interno pasa a
   `source_id` y no aparece en el texto.
5. El texto cita **una frase** y debajo la fuente con su enlace, en vez de volcar el
   fragmento entero.
6. Léxico: «aire»/«air» ya no arrastran AOD_55; «humo» y «garúa» sí apuntan a AOD_55 y
   CLOUD_AMT. Se añadió coincidencia por frase («humedad del aire» → RH2M).

**Evidencia (datos reales, extremo a extremo):**
```
GET /api/analyze?variable_id=T2M&lat=-12.05&lon=-77.03   → 200, 540 meses
POST /api/ai/explain {analysis, level:school, lang:es}   → 200
  mode: extractive · numbers_ok: true · 2 citas
  [1] Temperatura del aire a 2 m — NASA POWER parameter dictionary
  [2] What the Mann-Kendall test is — Hermes 1 summary of cited sources
```

**Pendiente en otro carril:** el rótulo «Síntesis asistida por IA» cuando `mode` es
`extractive` está en `src/ui/i18n.js` (Claude Omni 1). No lo toqué (regla 2). Anotado
en el bloque ESTADO.

## T2 — `no_match` honesto · VERIFICADO

Las 2 pruebas rojas esperaban `MODIS_NDVI`, que no está en el catálogo, y el
planificador respondía `EVLAND` (lo más parecido). Ahora `MISSING_TOPICS` +
`_coverage()` devuelven `intent: "no_match"`, `variable_ids: []`, el nombre de lo que
falta y hasta 3 alternativas **que sí existen** y son afines físicamente.

```
plan("¿la selva de Madre de Dios pierde vegetación?")
→ intent no_match · missing ["NDVI / vegetación (MODIS)"] · alternatives [GWETTOP, EVLAND]
```

Cubre NDVI (MODIS), GPM, GLDAS, AIRS, OMI NO₂ y OMI O₃.

## T3 — Gazetteer real y scout · VERIFICADO

- `alt_names` y `ascii` en uso: "Cuzco"→Cusco, "Lima, Peru"→Lima, "Moscow"→Moscow.
- Falsos positivos cerrados: "Peru" → `[]` (un gazetteer de ciudades no tiene países);
  "Perth" ya no se lleva "Peru" por el alt_name «Per».
- **Rendimiento:** de 1 300 ms a **4 ms** por consulta (antes: 55 331 llamadas a
  `SequenceMatcher` por consulta; ahora índice de prefijos cacheado).
- `find_in_text` conserva el texto tal como se escribió («Cuzco» no se normaliza).
- `scout` con el ETL real: Köppen BWh para Lima, ciudad grande a 0,8 km, costero desde
  `regions.json` (aproximado y declarado), 3 candidatas con su cita.
- `src/detective/wizard.py` **borrado**.

**Límite de la fuente, medido y declarado:** la celda de POWER para Cusco tiene
elevación 3 739,76 m y 9,1 °C en el mes más cálido → clasifica **ET**, mientras la
ciudad está a ~3 350 m y no es tundra. El código es correcto para la celda; `scout`
añade ahora `CELL_RESOLUTION` y `POLAR_CODE_AT_LOW_LATITUDE` para no presentarlo como
un hecho sobre la ciudad.

## T4 — `PLANNER_MODEL=local-lora` · ESCRITO

- `local-lora` llama a `src/ml/serve.py::generate(messages)` si existe; si no, responde
  por reglas con `note: "local_lora_unavailable"`. Nunca simula.
- El mensaje se reconstruye con el formato exacto del dataset
  (`- T2M: nombre (unidad) - definición`) desde `data/catalog/variables.json`.
- Una prueba comprueba que el `system_prompt` es **idéntico** al de `data/lora/train.jsonl`.

**Estado:** el camino de respaldo está verificado; el camino real no puede probarse
hasta que Antigravity 2 entregue el adaptador y `serve.py`.

## Evaluación de recuperación (actualizada)

Sobre las **50 preguntas oficiales** de Hermes 1 (`data/knowledge/golden_questions.jsonl`),
no las provisionales:

| Backend | P@1 | P@3 | MRR |
|---|---|---|---|
| bm25 | 0.960 | 1.000 | 0.977 |
| vectors | — | — | — |

Subió de 0.880 a 0.960 P@1 tras añadir humo, garúa y la coincidencia por frase.
Tabla completa y comando en `docs/EVAL_IA.md`.
