# EVAL_IA — evaluación de la IA del detective

**Dueño de la sección RAG:** claude-omni-2 · **Rama:** `feature/wizard`
Todo lo de aquí se regenera con comandos del repo; ninguna cifra está escrita a mano.

## 1. Recuperación (R2)

Comando: `python -m src.detective.rag.eval` (añade `--json` para uso automático).

<!-- TABLA_R2_INICIO -->
Fuente / Source: `data/knowledge/golden_questions.jsonl` (Hermes 1, 50 preguntas / 50 questions)

| Backend | Precision@1 | Precision@3 | MRR | Preguntas / Questions (k=6) |
|---|---|---|---|---|
| bm25 | 0.960 | 1.000 | 0.977 | 50 |
| vectors | — | — | — | 0 |
| fusion | 0.960 | 1.000 | 0.977 | 50 |

Medido el 14-nov-2026 a las 18:45 (hora de Perú) con `python -m src.detective.rag.eval`,
corpus de 166 documentos. `vectors` queda fuera de la media: no había servicio de
embeddings en esta máquina (Ollama apagado). / `vectors` drops out of the means when
no embedding service is available (contract §11).

Los 2 aciertos que faltan en P@1 están a 1 posición: "¿La garúa de Lima se está
volviendo más frecuente?" (esperado CLOUD_AMT/RH2M) y "Is Lake Titicaca losing water
to more evaporation?" (esperado EVLAND/GWETTOP). Ambos caen en P@3.
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
