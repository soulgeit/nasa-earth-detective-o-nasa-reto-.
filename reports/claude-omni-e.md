<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-e — 2026-11-15 12:20 hora de Perú (Ronda 6, cierre — redactado por el arquitecto)
Rama@commit: `main@5361f79` · empujado: sí (carril claude-omni-e verificado por el arquitecto en su nombre)
VERIFICADO: Informe 3 de QA final completo en `reports/qa/informe-3.md`: 7/7 casos en la URL pública con veredicto y pendiente correctos (incl. +0.159 tras H1), 0 errores de consola, cero scroll horizontal a 390 px, idioma ES traducido sin colar inglés.
VERIFICADO: Producción completa en Railway en vivo: `/api/health` 200 `status ok`; smoke_api 17/17 passed, 0 failed; análisis de Lima renderizado con periodo 1981/2025; sin «None and None» (D12); D13 cerrado.
VERIFICADO: D1–D16 todos cerrados (tabla en informe-3 §3): D14 (masie_web→0), D15 (Hermes 1→0), D16 (tildes→0), D1 (suite 289 passed), D2 (−9999 eliminado), D5/D8 (ES y Giovanni limpios).
ROTO / NO HECHO: ninguno. La puerta de calidad está abierta y la entrega es apta.
Siguiente paso: humano envía el formulario a las 20:00.
Necesito de: humano: «Submit for Judging».
Avisos para otros carriles: nada pendiente en QA; informe-3 re-verifica D1–D16 sobre `main` final y ambas URLs públicas.
<!-- ESTADO:FIN -->
Rama@commit: feature/qa@5b61009 · empujado: sí (commit 5b61009 en origin/feature/qa)
VERIFICADO: Informe 2 de QA completo antes de la hora límite (09:00). 10 recorridos repetidos en EN/ES a 1440 y 390 px con Playwright sobre integracion/ronda5 + 68 capturas examinadas individualmente (regla 29). De los 11 defectos del informe 1: 9 cerrados (D1, D2, D3, D4, D6, D7, D9, D10, D11) y 2 abiertos (D5: unidades en español; D8: ID crudo Giovanni; ambos asignados a claude-omni-1 a las 08:30). Se añaden 5 defectos nuevos: D12 («between None and None» en modo comparar), D13 (inputs Desde/Hasta no reflejan periodo del caso congelado), D14 (3 URLs con error DNS masie_web, 1 URL 404, 1 URL 403 en VALIDACION_ESTADISTICA.md §5), D15 (12 fichas de docs.jsonl con publisher «Hermes 1») y D16 (tildes en casos). Respaldo estático probado bajo subcarpeta (http://127.0.0.1:8799/nasa-earth-detective-o-nasa-reto-./): 7 de 7 casos abren con su veredicto, pendiente y unidad, con 0 errores de consola.
ESCRITO (sin ejecutar de punta a punta): ninguno
ROTO / NO HECHO: ninguno en el carril de QA. El producto pasa las comprobaciones técnicas y queda condicionado al cierre de D5, D8, D12, D14 y D15 en la puerta de las 08:30 y la integración G3 de las 10:00.
Siguiente paso: esperar a que claude-omni-3a confirme la publicación del respaldo en GitHub Pages para iniciar el Informe 3 (13:00) en ventana de incógnito y móvil real.
Necesito de: claude-omni-1 (D5 unidades en ES y D8 nombre variable Giovanni a las 08:30); antigravity-2 (D12 None and None y D14 URLs/cifras de la tabla estadística a las 08:30); claude-omni-2 (D15 editor Hermes 1 en docs.jsonl a las 08:30); hermes-2 (D16 tildes en casos a las 08:00); claude-omni-3a (confirmar gh-pages actualizada).
Avisos para otros carriles:
- Para @claude-omni-1: D5 y D8 siguen abiertos. En español, el veredicto de hielo dice `million km²/década` (shots/i_case_arctic-seaice-es-1440.png); al subir CSV de Giovanni se lee `M2SMNXSLV_5_12_4_T2MMEAN`. Además, al abrir un caso congelado los campos Desde/Hasta no se actualizan (D13).
- Para @antigravity-2: D12 NUEVO. En el modo comparar, el enunciado dice «between None and None (z = -2.19)» porque `region.name` viene `null` de la API y el fallback no sustituye `None`. D14 NUEVO: 3 URLs de NSIDC usan el host inexistente `masie_web.apps.nsidc.org` (falla DNS; cambiar a `noaadata.apps.nsidc.org`); la FAQ antártica da 404; el IPCC da 403; y las páginas citadas no contienen la frase literal declarada.
- Para @claude-omni-2: D15 NUEVO. `data/knowledge/docs.jsonl` tiene 12 fichas con `publisher: "Hermes 1 summary of cited sources"`, lo que se cita entre comillas en la UI como si fuera la fuente oficial.
- Para @hermes-2: D16 NUEVO. Faltan tildes en los textos en español de `index.json` y de los botones de la galería («Extension», «Artico», «Antartico», «amazonica», «precipitacion»).
- Para @claude-omni-3a: el respaldo estático local bajo subcarpeta pasa 7/7 casos y 0 errores de consola. Listo para desplegar en `gh-pages`.
<!-- ESTADO:FIN -->

# Reportes de Claude Omni E (Control de Calidad como Juez)

## INFORME 2 — 2026-11-15 07:35 UTC-5 (Ronda 5, cierre)

Entregable completo: [`reports/qa/informe-2.md`](qa/informe-2.md).

### Resumen ejecutivo
- **Base evaluada:** `feature/qa` fusionada con `origin/integracion/ronda5@9104694`.
- **Suite de pruebas:** **276 passed, 0 failed, 9 skipped** (antes 234 passed / 4 failed en R3).
- **Validación de datasets:** **7 de 7 válidos** con `python scripts/validate_datasets.py data/cases/*/series.json` (centinelas `-9999` eliminados; D2 y D3 cerrados).
- **Comprobación de los 11 defectos del Informe 1:**
  - **9 CERRADOS:** D1 (pytest en dev), D2 (-9999 eliminados), D3 (glob PowerShell), D4 (nombre de Lima visible), D6 (pregunta off-topic out_of_scope), D7 (variables planned con 409 y aviso), D9 (botones humanos en galería), D10 (espacios tipográficos eliminados al retirar tabular-nums), D11 (10 planned publicadas en API).
  - **2 ABIERTOS:** D5 (unidades en español: `million km²/década`) y D8 (identificador técnico crudo en CSV de Giovanni). Ambos a cargo de claude-omni-1 a las 08:30.
- **5 defectos nuevos registrados en Informe 2:**
  - **D12 (Lo ve el juez):** Modo comparar dice *«between None and None (z = -2.19)»*.
  - **D13 (Menor):** Inputs Desde/Hasta en UI no se actualizan con el periodo del caso congelado.
  - **D14 (Lo ve el juez / Auditoría de datos):** En `docs/VALIDACION_ESTADISTICA.md` §5, 3 enlaces fallan por DNS (`masie_web.apps.nsidc.org`), 1 da 404 y 1 da 403; páginas no contienen la cifra literal citada.
  - **D15 (Lo ve el juez):** 12 fichas de `data/knowledge/docs.jsonl` citan como editor a `Hermes 1 summary of cited sources`.
  - **D16 (Menor):** Faltan tildes en textos en español de los casos y botones de la galería.
- **Galería de casos congelados:** Los 7 casos despliegan exactamente la pendiente y veredicto de su `analysis.json` congelado (concordancia 100 %).
- **Respaldo estático servido bajo subcarpeta:** 7 de 7 casos abren con su veredicto, pendiente y unidad, y **0 errores de consola** (`static_subpath_test.json`).
- **68 capturas examinadas individualmente** (Regla 29).

---

## INFORME 1 — 2026-11-15 01:25 UTC-5 (Ronda 4)

Entregable completo: [`reports/qa/informe-1.md`](qa/informe-1.md).

### Resumen ejecutivo
- **Clon limpio siguiendo el README al pie de la letra:** el servidor arranca perfecto, `/api/health` 200, `/` 200, `smoke_api.py` pasa 14/14, `validate_knowledge.py` pasa 168/168. Falla `pytest` por no estar instalado en el entorno nuevo (D1) y `validate_datasets.py` por los centinelas `-9999` en los casos de hielo marino (D2).
- **10 recorridos con Playwright (40 combinaciones: EN/ES × 1440/390 px):**
  - **Pasan limpios:** detective con Piura (b), comparar Piura-Arequipa (d), atlas global de tendencias (e), cambio de idioma en vivo (j).
  - **Pasan con advertencia menor:** Lima T2M (a, no muestra «Lima»), Ártico (c, unidad en inglés en UI española), CSV subido (h, muestra ID técnico crudo de Giovanni), casos congelados (i, muestra slugs técnicos).
  - **Fallan:** pregunta fuera de tema (f, asigna nieve y lugar «the»), variable planned (g, propone T2M en «for»).
- **Revisión transversal:**
  - Apertura en inglés por defecto: **CUMPLE** (Regla 16).
  - Marcas NASA: **CUMPLE IMPECABLE** (paleta propia, cero logos, disclaimers visibles).
  - Rótulo extractivo: **CUMPLE** («Excerpts from cited sources (no generative AI)»).
  - Responsivo móvil: **CUMPLE** (390 px sin scroll horizontal).
- **Tabla de defectos completa:** 11 defectos registrados con gravedad, archivo:línea y agente responsable en `reports/qa/informe-1.md`.
