# EVAL_IA — evaluación de la IA del detective

**Dueño de la sección RAG:** claude-omni-2 · **Rama:** `feature/wizard`
Todo lo de aquí se regenera con comandos del repo; ninguna cifra está escrita a mano.

## 1. Recuperación (R2)

Comando: `python -m src.detective.rag.eval` (añade `--json` para uso automático).

<!-- TABLA_R2_INICIO -->
Fuente / Source: `data/knowledge/golden_questions.jsonl` (Hermes 1, 50 preguntas / 50 questions)

| Backend | Precision@1 | Precision@3 | MRR | Preguntas / Questions (k=6) |
|---|---|---|---|---|
| bm25 | 1.000 | 1.000 | 1.000 | 50 |
| vectors | — | — | — | 0 |
| fusion | 1.000 | 1.000 | 1.000 | 50 |

Medido el 15-nov-2026 con `python -m src.detective.rag.eval`, corpus de 168
documentos. `vectors` queda fuera de la media: no había servicio de embeddings en
esta máquina (Ollama apagado). / `vectors` drops out of the means when no embedding
service is available (contract §11).

Sin fallos: 50/50 en primera posición. La última que fallaba (polvo del desierto de
Sechura) era un defecto del léxico, no de la recuperación; ver §4-bis.
<!-- TABLA_R2_FIN -->

### Qué se midió y con qué

- **Corpus**: 50 documentos (25 tarjetas de variable × 2 idiomas) derivados de
  `data/catalog/variables.seed.json`, la semilla que fija los `variable_id`.
  Cuando Hermes 1 publique `data/knowledge/docs.jsonl`, el corpus crece sin tocar código.
- **Conjunto de preguntas**: `tests/detective/golden_questions.provisional.jsonl`,
  15 preguntas (10 es / 5 en) escritas **antes** de ejecutar el buscador.
  Se sustituye por `data/knowledge/golden_questions.jsonl` (Hermes 1, 50 preguntas) en cuanto llegue.
- **Backends**: BM25 Okapi propio (`k1=1.5`, `b=0.75`), vectores por embeddings
  (Ollama, `EMBED_MODEL`) y fusión de rangos recíprocos (RRF, k=60).
- **Ampliación de consulta**: `src/detective/lexicon.py` traduce palabras coloquiales
  ("llueve", "smog", "garúa") a los `variable_id` y nombres largos que ya están en la semilla.
  No añade documentos; solo términos a la consulta.

### Estado de los vectores

El 14-nov-2026 el servicio de Ollama **no estaba en marcha** en esta máquina
(`curl localhost:11434` → conexión rechazada), así que la columna `vectors` está vacía.
No se inventa un valor. Cuando el humano levante Ollama con un modelo de embeddings
multilingüe (`EMBED_MODEL=<modelo>`), basta:

```bash
python -m src.detective.rag.build_index     # crea data/cache/rag/docs-<modelo>.npz
python -m src.detective.rag.eval            # rellena la columna "vectors"
```

El índice se invalida solo si cambia el corpus (huella sha256 del contenido de los documentos).

## 2. Guardián de la explicación (R6)

Comando: `python -m pytest tests/detective/test_guard.py -q`

- **10 textos trampa** con cifras inventadas, años inventados o exceso de causalidad:
  **10/10 rechazados** por `run_guard` (ver `TRAPS` en `tests/detective/test_guard.py`).
- Tolerancias: un número se acepta solo si es un **redondeo del número de un hecho**
  a la precisión con la que se escribió ("0.3" vale para 0.31; "1999" no vale para 1981;
  "0.0001" no vale para 0.01). Los marcadores de cita `[3]` y los identificadores
  (`T2M`, `AOD_55`) no cuentan como cifras.
- Las cifras **dentro de comillas** se validan contra el fragmento citado, no contra los hechos,
  porque son una cita textual de la fuente.
- El exceso causal ("demuestra", "sin duda", "proves", "confirms") se rechaza en **español y en inglés**
  cuando el veredicto no es significativo.
- Si el guardián rechaza dos veces al modelo → respaldo extractivo: plantilla de `answers`
  + fragmentos citados tal cual. Ese camino es el que corre siempre con `AI_MODE=extractive`.

## 3. Modo extractivo (sin modelo, sin red)

Comando: `python -m pytest tests/detective -q` (la suite bloquea sockets en las pruebas
de punta a punta: si algo intenta salir a la red, el test falla).

- 20 preguntas de punta a punta (12 es / 8 en): recuperación → plan → explicación.
  Todas producen plan con `"mode": "rules"` y explicación con `"mode": "extractive"`.
- Con `AI_MODE=extractive` y Ollama apagado, el planificador devuelve la variable correcta
  como primera candidata en 20/20.

## 4. Planificador (R3)

- Contrato: la salida del modelo se valida contra el esquema de §10 y contra las candidatas
  recuperadas; `place` debe ser una **subcadena literal** de la pregunta. Un reintento y luego reglas.
- El mensaje de usuario que se envía al modelo es **el mismo formato** del dataset LoRA
  (`QUESTION: ...` + `CANDIDATES:` con `- ID: nombre`), y el `system` se lee de
  `data/lora/system_prompt.txt`. Si ese archivo no existe (Hermes 2 aún no lo ha publicado),
  el planificador **no llama a ningún modelo**: responde por reglas y lo anota en `note`.
- **LoRA**: evaluado de verdad, en GPU y en CPU. Las cifras, la máquina de cada
  medición, los fallos y los 200 casos de prueba están en la sección
  «Planner over the 50 golden questions» más abajo. El producto planifica con
  reglas; el LoRA es el modo local opcional.

## 5. Ejecución reproducible

```bash
python -m venv .venv && .venv/Scripts/pip install numpy scipy requests pytest
python -m pytest tests/detective -q          # 98 tests
python -m src.detective.rag.eval             # tabla de recuperación
```


## 4-bis. Planificador sobre las 50 preguntas de oro (RONDA 3)

Comando: `python -m src.detective.rag.eval_plan` (añade `--json` para uso automático).

<!-- TABLA_PLAN_INICIO -->
### Planner over the 50 golden questions (RONDA 3, 4 and 5)

Commands:
`python -m src.detective.rag.eval_plan` (rules) and
`AI_MODE=full PLANNER_MODEL=local-lora python -m src.detective.rag.eval_plan --planner local-lora`.
Rule 19 applied: a `planned` variable is never a candidate, for the rules or the model.

| Planner | Variable accuracy | Questions | Machine | Median time |
|---|---|---|---|---|
| rules | 50/50 = 1.000 | 50 | any (no model) | 2.6 s |
| LoRA | 40/50 = 0.800 | 50 | RTX 4070 SUPER, 4-bit | 2.2 s |
| LoRA | 37/50 = 0.740 | 50 | GTX 1650 SUPER, CPU float32 | 13.7 s |

The LoRA result depends on the machine (2.2 s on the RTX 4070 SUPER vs 13.7 s on CPU),
so **both the GPU and the CPU measurement are reported**: 40/50 on GPU, 37/50 on CPU.
The rules, which run anywhere, score 50/50 and are the product default.

Before rule 19 the LoRA scored 31/50; filtering `planned` products out of the
candidates recovered 9 questions on GPU and 6 on CPU. **None of its remaining
misses is a `planned` variable**: it confuses neighbouring variables
(`TS`/`T2M`, rain/temperature).

Both LoRA numbers are always reported together with its 200-case evaluation
(rule 20): on the 200 test cases drawn from the training generator, the adapter
reaches 84.5 % exact-variable accuracy against 15.5 % for the rules; on the 50
hand-written reference questions the order reverses (40/50 vs 50/50). The test set
comes from the same generator as the training data, which is why it is always shown
next to the hand-written set and never on its own.

Rules failures: **none** (50/50). The last one — desert dust attributed to soil
moisture instead of aerosol optical depth — was a lexicon bug: "turning into desert"
was splitting into loose words, so "desert" alone meant soil moisture. Words that are
too generic on their own are now excluded from loose matching
(`_PHRASE_ONLY_WORDS` in `src/detective/lexicon.py`), and multi-word aliases are also
matched as phrases. Retrieval went from P@1 0.980 to **1.000** with the same change.

LoRA failures on GPU (10), from `reports/_arquitecto.md`:

| Question | Got | Expected |
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

LoRA failures on CPU (13) — the same families plus three more that the 4-bit GPU
run gets right; the fuller list is reproducible with the command above.

### Who plans by default

**The rules decide who plans.** By default (`AI_MODE=extractive`) the rules answer, no
model is loaded and no GPU is needed. Since 2026-11-15 the public demo also runs an optional
hosted language model (OpenAI `gpt-4.1-mini`, `AI_MODE=full`) that proposes the plan; the rules
re-verify it and overrule it when they disagree. The LoRA is the optional local mode
(`PLANNER_MODEL=local-lora`); it needs ~7 GB of RAM in float32 or a CUDA GPU in 4-bit, so it is
not deployed to the public server. Every plan any model produces is re-verified by the rules
(variable available, place resolvable), so a model mistake in the place or the variable id
cannot reach the user. The numbers in this file measure the rules and the LoRA; the hosted model
was only checked end to end (`docs/RONDA_7.md` section 12), not scored on the 50 questions.

The numbers above are the reason: 50/50 rules vs 40/50 LoRA on the hand-written
questions. The LoRA is shown as what it is — a working fine-tune with published
results — not as the default planner.
<!-- TABLA_PLAN_FIN -->

## Comprobación en vivo del camino conversacional (Ronda 7, 15-nov-2026)

Medido en la RTX 4070 SUPER del PC1 con `AI_MODE=full PLANNER_MODEL=local-lora`: el adaptador
`etd-planner-lora` se carga en segundo plano (≈8 s) y se hicieron 6 preguntas reales a
`POST /api/ai/chat`. **No es un benchmark**: son 6 preguntas, solo para comprobar cómo se
comporta el producto con el adaptador encendido.

| Pregunta | Latencia | Plan que propuso el LoRA | Resultado |
|---|---|---|---|
| ¿Llueve menos en Ica? | 3,1 s | PRECTOTCORR · Ica | conservado |
| Is Lima getting hotter? | 2,4 s | T2M · Lima | conservado |
| heladas en Huancayo | 2,5 s | T2M | **corregido por las reglas** → FROST_DAYS |
| Compara la lluvia de Andahuaylas y Lima | 2,6 s | PRECSNOLAND (comparar) | **corregido por las reglas** → PRECTOTCORR |
| viento en Ica | 2,4 s | WS2M · Ica | conservado |
| ¿Hay más radiación UV en Ayacucho? | 2,8 s | ALLSKY_SFC_UV_INDEX · Ayacucho | conservado |

Con reglas (el modo del servidor público) las seis se planifican bien y responden en milisegundos.
Conclusión: el LoRA funciona y es más lento (2,4–3,1 s); no es más preciso que las reglas, lo que
coincide con el 40/50 frente al 50/50 de las preguntas de referencia. Por eso el producto exige que las
reglas respalden el plan del adaptador y, si no lo respaldan, deciden ellas (`lora_overruled` en la
nota del plan; ver `conversation._verify_lora_plan`). Además el adaptador nunca puede retener una
petición: una inferencia a la vez, tope de 25 s y precarga en segundo plano
(`planner._guarded_lora_call`; antes, el 15-nov a las 17:50, cargarlo dentro de la petición dejó sin
respuesta al servidor público).
