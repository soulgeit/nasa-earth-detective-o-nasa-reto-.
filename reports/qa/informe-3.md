# Informe 3 — QA Final sobre la Entrega (Ronda 6)

**Fecha:** 2026-11-15 12:15 hora de Perú (revisado 12:40)
**Realizado por:** arquitecto (cfable) en nombre del carril claude-omni-e, con verificación independiente del peer user41-73
**Base verificada:** `main@5361f79` (código y reportes; suite 289 passed, 0 failed, 9 skipped medida sobre el árbol equivalente `0c86b8c`, estos dos commits solo añaden documentación) y `gh-pages@10c7e16`

---

## 1. Verificación contra la URL pública (GitHub Pages)

`https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./`

Playwright (Chromium headless, 1440×900 y 390×844):

| Caso | Pendiente esperada | Resultado |
|---|---|---|
| Lima, Peru: air temperature 1981-2025 | +0.159 | ✅ OK |
| Svalbard, Norway: air temperature 1981-2025 | +0.699 | ✅ OK |
| Piura, Peru: precipitation 1981-2025 | −0.011 | ✅ OK |
| Arctic sea ice extent, 1978-2026 | −0.495 | ✅ OK |
| Antarctic sea ice extent, 1978-2026 | −0.048 | ✅ OK |
| Amazon basin: air temperature 1980-2026 | +0.186 | ✅ OK |
| Amazon basin: precipitation 1980-2026 | −0.083 | ✅ OK |

- **7/7 casos** abren con su veredicto, pendiente y unidad correctos.
- **0 errores de consola** en ninguna de las 8 páginas (7 casos + ES).
- **Viewport 390 px:** `scrollWidth = clientWidth = 390` → **cero desplazamiento horizontal** (D7 cerrado).
- **Idioma ES:** la galería traduce «Todavía no se detecta tendencia» (sin colar el inglés); título «Cuenca amazónica: temperatura del aire…» traducido (D5 y D16 cerrados).
- **Copia corregida H1:** el texto «Estimated rate of +0.159 °C/decade» coincide con la cifra grande (+0.1585 → +0.159) (H1 cerrado).

## 2. Verificación contra la producción completa (Railway)

`https://nasa-earth-detective-o-nasa-reto-production.up.railway.app`

- `GET /api/health` → **HTTP 200**, `status ok`, `ai_mode=extractive`, ETL/stats/detective `available: true`.
- `python scripts/smoke_api.py <url>` → **17 passed · 0 skipped · 0 failed**.
- Recorrido en vivo: investigar Lima → análisis renderizado, campos de periodo **1981/2025** correctos (D13 cerrado), sin «None and None» en modo comparación (D12 cerrado), 0 errores de consola.
- `GET /api/cases` → 7 casos; `GET /api/cases/lima-t2m` → `analysis/2`, verdict SIGNIFICANT; `GPM_IMERG_PRECIP` → HTTP 409 `VARIABLE_PLANNED` (regla 19).

## 3. Cierre de defectos D1–D16

| Defecto | Estado | Evidencia |
|---|---|---|
| D1 pytest | ✅ Cerrado | `289 passed, 0 failed` sobre `main@5361f79` |
| D2 −9999 hielo marino | ✅ Cerrado | hermes-2/antigravity-1 R6; `verify_seaice_cases.py` en verde |
| D3–D4, D6, D7, D9–D11 | ✅ Cerrados | `reports/qa/informe-2.md` + re-verificación en esta pasada |
| D5 unidades en ES | ✅ Cerrado | Galería y veredictos en español sin unidades inglesas |
| D8 ID crudo Giovanni | ✅ Cerrado | Upload muestra nombre limpio (claude-omni-1 R6) |
| D12 «between None and None» | ✅ Cerrado | No aparece en Railway; `nameA/nameB` con fallback |
| D13 inputs Desde/Hasta | ✅ Cerrado | 1981/2025 correctos al abrir caso congelado |
| D14 URLs muertas (masie_web) | ✅ Cerrado | `grep masie_web` → 0 en docs/data/src; URLs corregidas |
| D15 editor «Hermes 1» en docs.jsonl | ✅ Cerrado | `grep -c "Hermes 1" data/knowledge/docs.jsonl` → 0 |
| D16 tildes en casos | ✅ Cerrado | `check_case_accents.py` → 0 problemas en 8 archivos |

## 4. Entrega final

- **Subida pública 1 (app completa):** Railway en vivo, smoke 17/17, URL en README y SUBMISSION.
- **Subida pública 2 (respaldo estático):** GitHub Pages `gh-pages@10c7e16`, 7/7 casos, 0 errores, sin scroll horizontal.
- **Demo:** láminas (PDF 7 páginas exactas, 1280×720, cifras alineadas con H1 y EVAL_IA) decididas por el equipo; vídeo 29.0s disponible como opción B.
- **Formulario:** `docs/SUBMISSION.md` completo en inglés, con `<<HUMANO>>` resueltos (miembro: Angel Fernando Reyes Moreno).

**VEREDICTO: ENTREGABLE.** Sin defectos abiertos. Pendiente solo la acción humana de «Submit for Judging» antes de las 20:00.