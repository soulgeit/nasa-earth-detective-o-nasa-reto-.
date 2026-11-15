# RONDA 6 (FINAL DELIVERY & CODE FREEZE) — Sunday Nov 15

This document supersedes `docs/RONDA_5.md`. All feature branches are merged into `main` at commit `85f083f`. The repository is under strict **CODE FREEZE** (Rule 31). No new features or refactors.

---

## 1. Verified Status by the Architect

- **Git base:** `origin/main@85f083f` (all 10 feature lanes merged cleanly).
- **Test Suite:** `python -m pytest -q` → **288 passed, 0 failed, 9 skipped** (0 failures).
- **Quality Gate:** `python scripts/gate.py --offline` → **GATE OPEN: ALL CHECKS PASSED** (smoke_api 17/17, validate_datasets 7/7, validate_knowledge 168 docs, planned_not_analyzable 10/10, case_physical_ranges 3882 values, no_secrets 289 files).
- **Accents & Copy:** `python scripts/check_case_accents.py` → 0 issues across 8 files.
- **Official Demo Deliverables:**
  * **Slides (Option A):** `docs/demo/EarthTrend_Detective_slides.pdf` — **Exactly 7 pages**, 16:9 widescreen (1280×720), in English, no NASA logos, verified numbers documented in `docs/demo/FUENTES.md`.
  * **Video (Option B):** `docs/demo/EarthTrend_Detective_30s.mp4` — **Exactly 29.0 seconds** (≤ 30.0s), 1920×1080 Full HD, H.264, 795 KB, English captions, script in `docs/demo/GUION.md`.
- **Public Deployment (GitHub Pages):** Live at `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` with static backup (`gh-pages@94091de`).
- **Official Submission Text:** `docs/SUBMISSION.md` complete in English, ready to paste into the NASA Space Apps form.

---

## 2. Code Freeze & Submission Rules

1. **CODE FREEZE:** Do not edit `src/`, statistical methods, or data schemas. Only documentation polish or critical fixes approved by the architect are permitted.
2. **SYNC BASE:** Every agent must pull `origin/main` before performing checks.
3. **ENGLISH FIRST:** All materials seen by judges (UI, slides, video, submission text, README) must be in English.
4. **HUMAN DECISIONS:** Team name, members list, and choice of video vs. slides belong to the human team lead in `docs/SUBMISSION.md`.

---

## 3. What Each Agent Needs to Do (Closing Checklists)

### claude-omni-3a — Static Backup & Public URL
1. Verify `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` serves the latest commit `94091de`.
2. Test that all 7 cases open with correct verdicts, slopes, and units under the subpath.
3. Confirm 503 `DATA_UNAVAILABLE` fallback cleanly warns user for unhosted features.

### claude-omni-2 — Submission Form & AI Disclosure
1. Review `docs/SUBMISSION.md` ensuring all fields match NASA Space Apps Challenge 2026 requirements.
2. Verify all cited metrics match `docs/EVAL_IA.md` (rules 50/50, LoRA 40/50 on GPU, 37/50 on CPU).
3. Ensure placeholders `<<HUMANO: ...>>` are clearly visible for team name, members, and vision.

### claude-omni-1 — UI & Presentation Slides
1. Verify `docs/demo/EarthTrend_Detective_slides.pdf` has exactly 7 pages and is readable at 1280×720.
2. Ensure `docs/media/` contains the 8 clean official screenshots without tabular numeric spacing defects.
3. Confirm `docs/demo/FUENTES.md` accurately references all numbers used in the slides.

### claude-omni-c — Video Demonstration
1. Confirm `docs/demo/EarthTrend_Detective_30s.mp4` duration is strictly ≤ 30.0s (measured: 29.0s).
2. Ensure `docs/demo/GUION.md` accurately lists timestamps and on-screen text.
3. Prepare direct link / upload host if the team selects video submission.

### claude-omni-e — QA Judge Evaluation
1. Run final QA evaluation against the live public URL and report in `reports/qa/informe-3.md`.
2. Confirm defects D1 through D15 are completely closed.
3. Verify that zero horizontal scroll occurs on mobile viewports (390px).

### claude-omni-3 — API & Deployment
1. Verify `LICENSE` (MIT) and `requirements.txt` / `requirements-dev.txt` in a clean clone.
2. Maintain Railway container configuration ready if human initiates `railway login`.

### hermes-2 — Cases & Datasets
1. Confirm `data/cases/index.json` has clean titles and findings for all 7 cases in both EN and ES.
2. Confirm `data/lora/DATASET_CARD.md` accurately documents known dataset traits.

### antigravity-1 — NASA Data Pipeline
1. Verify `docs/COMPARACION_POWER_GIOVANNI.md` reproduces accurately.
2. Ensure NSIDC sea ice connector has clean, deduplicated underlying citations.

### antigravity-2 — Statistical Validation
1. Confirm `docs/VALIDACION_ESTADISTICA.md` reproducible table commands match real output.
2. Ensure `src/ml/MODEL_CARD.md` matches final GPU and CPU evaluation benchmarks.

### claude-omni-1b — Knowledge & References
1. Verify `docs/REFERENCES.md` has live 200 HTTP URLs for all 168 corpus documents.
2. Verify `README.md` is strictly in English with live links and local reproduction commands.

---

## 4. One-Line Prompts for Each Agent (Ready to Paste)

Copy and paste the corresponding line to each agent terminal:

- **claude-omni-3a:** `Eres claude-omni-3a. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Verifica la URL publica en GitHub Pages (https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./) comprobando que sirva el commit 94091de con los 7 casos funcionales. Deja tu reporte final en reports/claude-omni-3a.md.`
- **claude-omni-2:** `Eres claude-omni-2. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Revisa docs/SUBMISSION.md y docs/AI_USE_LOG.md asegurando que esten 100% en ingles y listos para enviar al jurado. Deja tu reporte final en reports/claude-omni-2.md.`
- **claude-omni-1:** `Eres claude-omni-1. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Revisa que las 7 laminas en docs/demo/EarthTrend_Detective_slides.pdf tengan exactamente 7 paginas y esten enlazadas en docs/demo/FUENTES.md. Deja tu reporte final en reports/claude-omni-1.md.`
- **claude-omni-c:** `Eres claude-omni-c. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Confirma que docs/demo/EarthTrend_Detective_30s.mp4 dura 29.0s (<= 30.0s) y que docs/demo/GUION.md describe el video. Deja tu reporte final en reports/claude-omni-c.md.`
- **claude-omni-e:** `Eres claude-omni-e. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Haz tu Informe 3 de QA sobre la URL publica en GitHub Pages y en local, comprobando que los defectos D1-D15 esten cerrados. Deja tu reporte en reports/qa/informe-3.md.`
- **claude-omni-3:** `Eres claude-omni-3. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Verifica LICENSE y requirements.txt en un clon limpio y deja tu reporte final en reports/claude-omni-3.md.`
- **hermes-2:** `Eres hermes-2. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Revisa data/cases/index.json y data/lora/DATASET_CARD.md y deja tu reporte final en reports/hermes-2.md.`
- **antigravity-1:** `Eres antigravity-1. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Revisa docs/COMPARACION_POWER_GIOVANNI.md y el conector NSIDC, y deja tu reporte final en reports/antigravity-1.md.`
- **antigravity-2:** `Eres antigravity-2. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Revisa docs/VALIDACION_ESTADISTICA.md y src/ml/MODEL_CARD.md y deja tu reporte final en reports/antigravity-2.md.`
- **claude-omni-1b:** `Eres claude-omni-1b. Ejecuta: git fetch origin && git checkout main && git merge origin/main — Lee docs/RONDA_6.md entero. Revisa docs/REFERENCES.md y README.md asegurando que no haya enlaces rotos. Deja tu reporte final en reports/claude-omni-1b.md.`
