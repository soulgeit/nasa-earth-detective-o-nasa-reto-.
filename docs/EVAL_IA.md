# EVAL_IA — evaluación de la IA del detective

**Dueño de la sección RAG:** claude-omni-2 · **Rama:** `feature/wizard`
Todo lo de aquí se regenera con comandos del repo; ninguna cifra está escrita a mano.

## 1. Recuperación (R2)

Comando: `python -m src.detective.rag.eval` (añade `--json` para uso automático).

<!-- TABLA_R2_INICIO -->
Fuente / Source: `data/knowledge/golden_questions.jsonl` (Hermes 1, 50 preguntas / 50 questions)

| Backend | Precision@1 | Precision@3 | MRR | Preguntas / Questions (k=6) |
|---|---|---|---|---|
| bm25 | 0.980 | 1.000 | 0.990 | 50 |
| vectors | — | — | — | 0 |
| fusion | 0.980 | 1.000 | 0.990 | 50 |

Medido el 14-nov-2026 a las 21:40 (hora de Perú) con `python -m src.detective.rag.eval`,
corpus de 166 documentos. `vectors` queda fuera de la media: no había servicio de
embeddings en esta máquina (Ollama apagado). / `vectors` drops out of the means when
no embedding service is available (contract §11).

El único fallo en P@1 lo recupera P@3: "Is dust from the Sechura Desert travelling
farther now?" (esperado AOD_55).
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
- **LoRA**: no se evaluó en esta rama; corresponde a Antigravity 2 / juicio del arquitecto.
  Esta sección no afirma ninguna cifra sobre LoRA.

## 5. Ejecución reproducible

```bash
python -m venv .venv && .venv/Scripts/pip install numpy scipy requests pytest
python -m pytest tests/detective -q          # 98 tests
python -m src.detective.rag.eval             # tabla de recuperación
```


## 4-bis. Planificador sobre las 50 preguntas de oro (RONDA 3)

Comando: `python -m src.detective.rag.eval_plan` (añade `--json` para uso automático).

<!-- TABLA_PLAN_INICIO -->
### Planner over the 50 golden questions (RONDA 3 & 4)

Commands:
`python -m src.detective.rag.eval_plan` (rules) and
`AI_MODE=full PLANNER_MODEL=local-lora python -m src.detective.rag.eval_plan --planner local-lora`.
Measured 2026-11-15, `main` merged, rule 19 applied (a `planned` variable is never a candidate).

| Planner | Variable accuracy | Questions |
|---|---|---|
| rules | 49/50 = 0.980 | 50 |
| LoRA (local, CPU) | 37/50 = 0.740 | 50 |

Both numbers are always reported together (rule 20). Timing on this machine
(GTX 1650 SUPER, CPU inference): ~3.6 s/question for rules; ~13.7 s/question for
LoRA after one ~60 s model load.

Rules failures (1):

| Question | Lang | Intent | Got | Expected |
|---|---|---|---|---|
| Is dust from the Sechura Desert travelling farther now? | en | `investigate` | `GWETTOP` | `AOD_55` |

LoRA failures (13) — none is a `planned` variable, so rule 19 removed 15 of the
previous 19 misses:

| Question | Lang | Intent | Got | Expected |
|---|---|---|---|---|
| ¿Está lloviendo menos en Piura en los últimos años? | es | compare | T2M | PRECTOTCORR |
| ¿El aire de Lima está más sucio que hace años? | es | compare | RH2M | AOD_55 |
| ¿Qué ha pasado con la lluvia en la selva de Madre de Dios? | es | investigate | T2M | PRECTOTCORR |
| Temperatura de la superficie del suelo en la costa | es | investigate | GISTEMP_TANOM | TS |
| ¿El lago Titicaca está perdiendo agua por evaporación? | es | investigate | TQV | EVLAND, GWETTOP |
| ¿La garúa de Lima se está volviendo más frecuente? | es | compare | ALLSKY_SFC_SW_DWN | CLOUD_AMT, RH2M |
| ¿El vapor de agua sobre la costa peruana cambió? | es | investigate | RH2M | TQV |
| ¿Qué variable debo mirar para saber si Piura se desertifica? | es | investigate | T2M | GWETTOP, PRECTOTCORR |
| ¿Las lluvias de El Niño son más intensas en Tumbes? | es | compare | T2M | PRECTOTCORR |
| Ground surface temperature in Puno, trend? | en | investigate | GISTEMP_TANOM | TS |
| Is Lima's drizzle becoming more frequent? | en | investigate | PRECTOTCORR | CLOUD_AMT, RH2M |
| Which variable tells me if Piura is turning into desert? | en | investigate | T2M | GWETTOP, PRECTOTCORR |
| Are El Nino rains stronger in Tumbes? | en | compare | T2M | PRECTOTCORR |

### Who plans by default (RONDA 4 §5.2)

The LoRA **is not the silent default**. The public server runs `AI_MODE=extractive`
(rules plan, no model loaded). Locally, `PLANNER_MODEL=local-lora` opts in to the
adapter explicitly, and every plan the model produces is re-verified by the rules
(variable available, place resolvable). On the 50 reference questions the rules
(49/50) beat the LoRA (37/50), so rules are the default and the LoRA is an explicit
option with its real numbers.
<!-- TABLA_PLAN_FIN -->
