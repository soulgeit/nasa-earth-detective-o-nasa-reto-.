# Registro de uso de IA (SI) — requisito del reto

La guía de entrega 2026 exige indicar dónde y cómo se usó IA. Código y datos generados con IA se reconocen en el texto descriptivo y en los metadatos;
imágenes y vídeos generados llevan marca de agua visible. Este archivo es la base de la respuesta al campo «Use of Super Intelligence (SI)».

**Cómo se marca cada cosa**
- Código: primera línea de cada archivo generado → `SI-assisted: <agente> (<modelo>)` como comentario.
- Datos generados (p. ej. preguntas de entrenamiento): campo `meta.source` en cada registro y ficha `DATASET_CARD.md`.
- Datos de la NASA: **no** son generados; llevan `provenance` con la consulta exacta.
- Imágenes, vídeo y audio: no se genera ninguno con IA salvo que se anote aquí, y entonces con marca de agua.

**Cada agente añade una fila al entregar** (no borres ni reordenes las de otros).

| Fecha | Agente | Herramienta y modelo | Archivos | Qué se hizo con IA | Revisado por (persona) |
|---|---|---|---|---|---|
| 2026-11-14 | Arquitecto | Claude Code (Claude Fable 5.2) | `docs/PLAN_GANADOR.md`, `docs/CONTRATOS.md`, `docs/KIT_ENTREGA.md`, `prompts/*.md`, `TASKS.md`, `README.md`, `data/catalog/variables.seed.json`, `data/raw/giovanni/README.md` | Auditoría del prototipo, verificación de las fuentes de datos con llamadas reales, redacción del plan, de los contratos y de los prompts de los agentes | pendiente |
| 2026-11-14 | Claude Omni 2 | Claude Code (Claude Opus 5.5) | `src/detective/*`, `src/detective/rag/*`, `tests/detective/*`, `docs/EVAL_IA.md`, `reports/claude-omni-2.md` | Implementación del detective: recuperación BM25 + vectores + RRF, planificador con validación dura y respaldo por reglas, geocodificador, clasificación de Köppen (reglas de Peel et al. 2007 leídas de la fuente), explicación con guardián determinista y 98 pruebas. Los 10 textos trampa del guardián y las 15 preguntas de oro provisionales fueron redactados con IA y se revisan a mano | pendiente |
