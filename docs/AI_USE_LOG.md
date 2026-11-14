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
| 2026-11-14 | Claude Omni 1 | Claude Code (Claude Sonnet 5.5) | `src/ui/app.js`, `src/ui/index.html`, `src/ui/styles.css`, `src/ui/i18n.js` | Tareas U1, U2 y U3: limpieza de datos falsos, pantalla principal, Leaflet (NASA GIBS), Chart.js (banda de Sen, anomalías, medias anuales), escalera de veredicto en 5 niveles, barra de detectabilidad, internacionalización ES/EN, mapa de tendencias regional (TrendMap v2 con control FDR de celdas y escala divergente simétrica) y modo Comparar dos lugares con ejes Y sincronizados | pendiente |
