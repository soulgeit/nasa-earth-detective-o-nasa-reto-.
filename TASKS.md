# TASKS — Tablero v2 (14-nov-2026)

**Estado: RECONSTRUCCIÓN CON DATOS REALES.** El tablero anterior marcaba como hecho un prototipo con datos sintéticos; queda sustituido.
Plan: `docs/PLAN_GANADOR.md` · Contratos: `docs/CONTRATOS.md` · Entrega: `docs/KIT_ENTREGA.md` · Reglas: `prompts/00_LEER_PRIMERO.md`

**Cierre oficial: domingo 15-nov 23:59 (hora local). Entregamos a las 20:00.**
Desde ahora una casilla solo se marca con evidencia en `reports/` y verificada por el arquitecto.

## Hermes 1 — C1-C7 Status Update (2026-11-14T23:55)

| Tarea | Estado | Entregable | Commit |
|---|---|---|---|
| C1 Catálogo v2 | ✅ LISTO | data/catalog/variables.json (25 variables) | ee23b07 |
| C2 Regiones + Gazeteer | ✅ LISTO | data/catalog/regions.json (~60 regions), gazetteer.json (66 cities) | fbff93e / 688ac04 |
| C3 Corpus RAG docs.jsonl | ✅ LISTO | 76 documentos (21 NASA articles, 4 biome profiles, 6 method notes, 25 variable cards, 20 glossary terms) | f32bbfe |
| C4 Validador | ✅ LISTO | scripts/validate_knowledge.py | bad8e84 |
| C5 Golden Questions | ✅ LISTO | data/knowledge/golden_questions.jsonl (99 preguntas: 50 es + 49 en) | 8f97cec |
| C6 Variables Giovanni | ⚠️ PENDIENTE | requiere CSVs de Giovanni del humano | — |
| C7 Referencias | ✅ LISTO | docs/REFERENCES.md | cc73bfc |

**Total de commits Hermes 1:** 10+ (varias entregas incrementales)
## Puertas

| Puerta | Hora | Condición | Estado |
|---|---|---|---|
| G0 Arranque | sáb 13:30 | Plan en `main`, agentes con su prompt, cuenta Earthdata | ☐ |
| G1 Datos reales | sáb 17:30 | `/api/analyze` devuelve análisis v2 con datos de POWER; sintéticos borrados; motor en verde | ☐ |
| G2 Detective completo | sáb 23:30 | Mapa, mapa de tendencias, comparar, catálogo ≥ 18, RAG con fuentes, dataset LoRA, un CSV de Giovanni analizado | ☐ |
| G3 IA integrada | dom 10:00 | Planificador evaluado y servido (o plan B), explicación con guardián, bilingüe, 4 casos | ☐ |
| Congelación | dom 14:00 | Solo correcciones; despliegue público | ☐ |
| G4 Entrega lista | dom 18:00 | Página en inglés, demo, enlaces públicos probados | ☐ |
| ENTREGAR | dom 20:00 | «Submit for Judging» | ☐ |

## Agentes: qué hace cada uno y qué pegarle

Pega a cada agente **su línea** (cambia solo lo que va entre < >). El resto lo lee del repo.

| # | Agente | Rama | Prompt | Primera tarea |
|---|---|---|---|---|
| 1 | Claude Fable (arquitecto) | `main` | `prompts/01_cfable_arquitecto.md` | T0 puerta mecánica |
| 2 | Antigravity 1 | `feature/data-pipeline` | `prompts/02_antigravity-1_datos-nasa.md` | D1 conector POWER |
| 3 | Antigravity 2 | `feature/stats` | `prompts/03_antigravity-2_estadistica-y-lora.md` | E1 motor v2 |
| 4 | Claude Omni 1 | `feature/ui` | `prompts/04_claude-omni-1_interfaz.md` | U1 limpiar lo falso |
| 5 | Claude Omni 2 | `feature/wizard` | `prompts/05_claude-omni-2_detective-ia.md` | R1 recuperación |
| 6 | Claude Omni 3 | `feature/api` | `prompts/06_claude-omni-3_api-y-despliegue.md` | A1 esqueleto por contrato |
| 7 | Hermes 1 | `feature/catalog` | `prompts/07_hermes-1_catalogo-y-conocimiento.md` | C1 catálogo v2 |
| 8 | Hermes 2 | `feature/scrapes` | `prompts/08_hermes-2_casos-atlas-dataset.md` | S1 dataset LoRA |

Línea para pegar:

```
Eres <AGENTE> en el repo nasa-earth-detective. Ejecuta: git fetch origin && git checkout <RAMA> && git merge origin/main
Lee completos, en este orden: prompts/00_LEER_PRIMERO.md, docs/CONTRATOS.md y <PROMPT>.
Haz tus tareas en el orden indicado, empezando por <PRIMERA TAREA>. Tras cada tarea: commit, push a tu rama
y entrada en reports/<tu-nombre>.md con el comando ejecutado y su salida real. No inventes datos ni fuentes.
Si algo te bloquea más de 20 minutos, anótalo en tu reporte y pasa al plan B de tu prompt.
```

## Dependencias (quién espera a quién)

- Antigravity 1 (D1) → desbloquea a Claude Omni 3 (A2), Hermes 2 (S2, S3) y Claude Omni 2 (R5).
- Antigravity 2 (E1) → desbloquea a Claude Omni 3 (A2) y Hermes 2 (S2).
- Hermes 1 (C1, C2) → mejora a Claude Omni 2 (R1, R4) y Hermes 2 (S4). Nadie se bloquea: la semilla `variables.seed.json` sirve para empezar.
- Hermes 2 (S1) → Antigravity 2 (fase LoRA) → Claude Omni 2 (R3).
- Humano (CSV de Giovanni) → Antigravity 1 (D5) y Hermes 1 (C6).
- Mientras tanto, todos desarrollan contra las muestras reales de `tests/fixtures/real/`.

## Humano

- [ ] Publicar el plan en `main` y repartir las líneas de arranque
- [ ] Cuenta Earthdata + primer CSV de Giovanni en `data/raw/giovanni/` (ver su `README.md`)
- [ ] Decisiones de `docs/PLAN_GANADOR.md` §7 (casos, nombre, demo, premio)
- [ ] Ventana de GPU para el LoRA (o Kaggle/Colab)
- [ ] Hosting: iniciar sesión y, con el sitio arriba, clasificación FortiGuard
- [ ] Licencia del repositorio (propuesta: MIT para código, CC BY 4.0 para datos propios)
- [ ] Equipo inscrito en el mismo evento local (máx. 6)
- [ ] Demo + «Submit for Judging» a las 20:00 del domingo
