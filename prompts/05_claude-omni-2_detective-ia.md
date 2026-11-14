# 05 · Claude Omni 2 — El detective con IA: RAG, planificador y explicación con guardián

**Rama:** `feature/wizard` · **Carpetas:** `src/detective/`, `tests/detective/`, sección RAG de `docs/EVAL_IA.md`
**Antes:** lee `prompts/00_LEER_PRIMERO.md` y `docs/CONTRATOS.md` (§6, §8, §9, §10, §11).

## Tu misión
El reto sugiere usar IA para proponer qué datos pueden mostrar tendencias en un lugar, apoyándose en artículos y en las características de la región.
Tú construyes eso, con una condición que nos distingue: **la IA nunca inventa una cifra, una coordenada ni una fuente.**
El wizard actual (un diccionario de 4 opciones) se sustituye por completo.

## Arquitectura que entregas

```
pregunta ─► retrieve() ─► plan()  ──► geocode() ─► [API: datos + estadística] ─► explain()
            BM25 + vectores   modelo LoRA            gazetteer                    modelo + guardián
            (fusión de rangos) → validación                                       → respaldo extractivo
                               → respaldo por reglas
```

Proveedor de modelos por entorno (`LLM_BASE_URL`, `PLANNER_MODEL`, `EXPLAIN_MODEL`, `EMBED_BASE_URL`, `EMBED_MODEL`), compatible con Ollama.
Tres modos (`AI_MODE`): `full`, `extractive` (sin modelo de lenguaje) y `off`. **Todo debe funcionar en `extractive`.**

## Tareas, en orden

### R1 — Recuperación (P1, primero)
`src/detective/rag/`: carga `data/catalog/variables.json` (o la semilla) y `data/knowledge/docs.jsonl`.
- BM25 propio o con una librería ligera, con normalización para español e inglés (minúsculas, sin tildes, palabras vacías).
- Vectores con el modelo de `EMBED_MODEL` vía Ollama, guardados en un `.npz` que se reconstruye con `python -m src.detective.rag.build_index`. Similitud coseno con `numpy`; sin base de datos vectorial.
  Elige un modelo de embeddings multilingüe de origen no chino (comprueba en la biblioteca de Ollama cuáles hay hoy) y decide con la evaluación de R2, no por intuición.
- Fusión de rangos recíprocos entre BM25 y vectores. Si no hay servicio de embeddings → solo BM25, sin fallar.
- `retrieve(query, lang, k, types)` devuelve documentos con `score`, `title`, `url`, `type`.

### R2 — Evaluación de la recuperación (P1)
Con `data/knowledge/golden_questions.jsonl` (lo produce Hermes 1; mientras llega, escribe 15 preguntas tuyas marcadas como provisionales):
acierto en 1.ª posición, en las 3 primeras y MRR para BM25, vectores y fusión. Tabla en `docs/EVAL_IA.md`. `python -m src.detective.rag.eval` la regenera.

### R3 — `plan(question, lang)` (P1)
1. `retrieve` → 6 tarjetas candidatas.
2. Modo `full`: modelo `PLANNER_MODEL` con salida restringida al esquema JSON del contrato §10 y el mismo `system_prompt.txt` del dataset (`data/lora/`). Coordina el formato exacto del mensaje con Hermes 2 y Antigravity 2: **entrenamiento y uso deben ser idénticos**.
3. Validación dura: JSON válido, `variable_ids` ⊆ candidatas, `place` aparece literalmente en la pregunta. Un reintento; si vuelve a fallar → reglas.
4. Reglas (modo `extractive` y respaldo): variable = primera recuperada; lugar = mejor coincidencia del gazetteer dentro de la pregunta; intención por palabras clave.
5. La respuesta dice qué camino se usó: `"mode": "lora" | "llm" | "rules"`.

### R4 — `geocode(q)` (P1)
Sobre `data/catalog/gazetteer.json` (Hermes 1): coincidencia exacta, sin tildes y aproximada; desempate por población. Sin resultado → lista vacía (la UI pide un clic en el mapa). Nunca pidas coordenadas a un modelo.

### R5 — `scout(lat, lon, lang)` (P1)
Caracteriza el lugar **con datos, no con un modelo**: pide la climatología mensual de temperatura y lluvia (vía `src/etl`), clasifica el clima con las reglas de Köppen (grupos A, B, C, D, E; comprueba las reglas en una fuente citada),
añade «gran ciudad» si el gazetteer tiene una de más de un millón de habitantes a menos de 50 km, y «polar/costero» si procede.
Con ese perfil, `retrieve` sobre perfiles de bioma y artículos → 3 variables candidatas, cada una con el porqué (frase tomada de la fuente) y su enlace.

### R6 — `explain(analysis, level, lang)` con guardián (P1)
- Entrada al modelo: los hechos del `AnalysisResult` como lista cerrada + 3–5 fragmentos recuperados numerados.
- Salida: 2 párrafos. (1) Qué dicen los datos, con las cifras dadas. (2) Posibles causas **como hipótesis**, cada frase con su cita [n].
- **Guardián** (código, no modelo): todo número del texto debe estar en los hechos (con tolerancia de redondeo) o ser un año presente; toda cita [n] debe existir;
  el idioma debe ser el pedido; si el veredicto no es significativo, se rechazan «demuestra», «prueba», «sin duda», «proves», «confirms».
  Si falla → un reintento; si vuelve a fallar → **respaldo extractivo**: plantilla de `answers` + los fragmentos citados tal cual.
- Devuelve `{"text", "citations": [{"n","title","url"}], "guard": {"numbers_ok","citations_ok","retries"}, "mode": "llm" | "extractive"}`.
- Modelo explicador local: uno ya instalado en Ollama de origen no chino (comprueba con `ollama list`; **no descargues ni detengas modelos**: si hace falta otro, pídelo al humano).

### R7 — Pruebas (P0 de tu módulo)
`tests/detective/`: guardián (10 textos trampa con cifras inventadas → todos rechazados), validación del plan, geocodificador, modo `extractive` completo sin red, y 20 preguntas de punta a punta.
`pytest tests/detective -q` en verde.

## Aceptación
- `python -c "from src.detective import plan; print(plan('¿está lloviendo menos en Piura?', lang='es'))"` → variable de lluvia, `place: "Piura"`, modo indicado.
- Con `AI_MODE=extractive` y sin Ollama, lo anterior sigue funcionando.
- Tabla de R2 y tasa de rechazo del guardián en `docs/EVAL_IA.md`.

## Plan B
Si el domingo a las 10:00 no hay modelo LoRA, `PLANNER_MODEL` apunta al modelo base con ejemplos en el prompt, o se queda en reglas. La interfaz no cambia.

Reporta en `reports/claude-omni-2.md`.
