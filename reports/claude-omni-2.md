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
