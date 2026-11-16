# Script: EarthTrend Detective (30s Video)
**Goal:** NASA Space Apps Challenge 2026 Project Video Demo
**Target Duration:** Exactly 28.0 - 29.5 seconds (Constraint: <= 30.0s)
**Resolution:** 1920x1080 (16:9 full HD)
**Audio/Voice:** No synthetic voice / AI speech (per project rules). Clean visual pacing with cinematic intro & overlay lower-thirds subtitles.
**Case Source:** Arctic sea ice (strong negative trend) vs. Antarctic sea ice (honest not significant verdict) and Lima, Peru temperature.

---

### Timeline Breakdown

| Time Window | Duration | Scene / Action on Screen | Caption / Overlay Card (English) | Data Source & Case |
|---|---|---|---|---|
| **00:00 - 00:03** | 3.0s | **Title Card & Mission Scope**<br>Dark slate background, editorial palette, clean typography.<br>EarthTrend Detective title, NASA Space Apps Challenge 2026 subtitle.<br>Core question: *"Is a climate trend in a place you care about real?"* | **EarthTrend Detective**<br>*Real NASA Earth science data for any point or region on Earth.* | `docs/KIT_ENTREGA.md` §5 |
| **00:03 - 00:09** | 6.0s | **Investigation 1: Arctic Sea Ice Extent (1978–2026)**<br>Load Arctic sea ice case in web app UI.<br>Display time-series chart with Theil-Sen slope & 95% confidence fan.<br>Verdict ladder: **SIGNIFICANT_STRONG (5/5)**.<br>Highlighted stat: **-0.50 million km² / decade (-4.4%)**. | **1. Arctic Sea Ice (1978–2026)**<br>*Verdict: Clear, strong trend (-0.50 million km²/decade). Mann-Kendall & OLS agree.* | `data/cases/arctic-seaice/analysis.json`<br>NSIDC Sea Ice Index v4 |
| **00:09 - 00:15** | 6.0s | **Investigation 2: Honest Science & Detectability**<br>Switch to Antarctic sea ice case.<br>Verdict: **NOT_SIGNIFICANT (2/5)**.<br>Display Weatherhead detectability calculation bar: **"133 more years needed"** for certainty.<br>No false alarms: honest uncertainty bounds. | **2. Antarctic Sea Ice: Honest Verdicts**<br>*No trend detectable so far (p = 0.63). Detectability model: ~133 more years needed.* | `data/cases/antarctic-seaice/analysis.json`<br>Weatherhead et al. (1998) |
| **00:15 - 00:21** | 6.0s | **Investigation 3: Global Spatial TrendMap**<br>Open Spatial TrendMap mode with Benjamini-Hochberg FDR control ($q=0.10$).<br>Display 759 grid cells for air temperature; 455 cells (60%) marked with significant center dot.<br>Prevents false positive stippling. | **3. Spatial TrendMap (FDR Control)**<br>*Air temperature at 2 m: 60% of cells show significant trends (Wilks 2016).* | `data/atlas/T2M.json`<br>NASA POWER / MERRA-2 |
| **00:21 - 00:26** | 5.0s | **Investigation 4: Two-Location Comparison & AI Detective**<br>Compare Mode: Piura vs. Arequipa with synchronized Y-axes.<br>Ask the Detective box with cited NASA sources & verified provenance URLs. | **4. Compare Mode & AI Detective**<br>*Synchronized scales, citations from NASA Earth Observatory, and full cryptographic provenance.* | `data/cases/piura-prectotcorr/`<br>`src/ui/app.js` |
| **00:26 - 00:29** | 3.0s | **Closing Outro & Live Public App Link**<br>Full link to open GitHub Pages live deployment.<br>Available in English & Spanish. No installation required. | **EarthTrend Detective**<br>*Explore live: soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./*<br>Open source & free for all students. | `docs/KIT_ENTREGA.md` §1 |

Total Planned Duration: **29.0 seconds** (Strictly within the 30.0s cap).

---

## Versión 2 — vídeo de presentador con las láminas al costado (15-nov, 19:05)

**Archivo:** `docs/demo/Huiracocha_AI_pitch_30s.mp4` — 1920×1080, 30 fps, **29,97 s** (≤ 30,0 s), H.264 + AAC.
Se construye con `python scripts/build_pitch_video.py <presentador.mp4> <narración.mp3>`.

- **Izquierda:** el presentador (vídeo propio del equipo, vertical, un adulto). Su vídeo original dura 36 s y dice el
  mismo guion que la narración, empezando en el segundo 3,12; se recortó desde su primera palabra y se **re-temporizó
  tramo a tramo** (8 tramos; siete necesitan ±6 % o menos, solo la primera frase pide 22 %) para que sus labios sigan la
  narración. Los tiempos por palabra se midieron con faster-whisper (large-v3).
- **Derecha:** las 7 láminas de `slides.html` dentro de una ventana de aplicación (barra con la dirección en vivo y el
  distintivo LIVE), que cambian con la frase que se dice.
- **Subtítulos en inglés** grabados en pantalla, indicador de lámina y la etiqueta
  «Narration: AI-generated voice (ElevenLabs)».
- **Voz:** la narración es una voz generada con IA (ElevenLabs). El guion de la primera versión decía «sin voz sintética»;
  la regla real del proyecto (`docs/KIT_ENTREGA.md` §1) es **declarar y marcar** lo generado, y eso es lo que se hace:
  etiqueta visible, `docs/AI_USE_LOG.md` y `docs/SUBMISSION.md`.

| Tiempo | Frase (narración) | Lámina |
|---|---|---|
| 0:00–0:02,7 | Our planet is changing faster than ever. | 1 · título, Huiracocha AI, RAG y LoRA |
| 0:02,7–0:07,2 | Yet the communities facing the storm are left blind to what is coming. | 2 · el problema |
| 0:07,2–0:10,9 | We created Huiracocha to change that forever. | 3 · la aplicación (veredicto real de Lima) |
| 0:10,9–0:16,5 | We bring the boundless vision of space straight into the hands of those who walk the earth. | 4 · datos reales de la NASA |
| 0:16,5–0:19,9 | Now, any community can see threats rising, | 5 · estadística honesta |
| 0:19,9–0:24,4 | protect their water and land, and act before disaster strikes. | 6 · RAG + LoRA y el escaneo |
| 0:24,4–0:26,0 | The truth is here. | 7 · impacto y enlaces |
| 0:26,0–0:30,0 | The power to defend your home is finally yours. | 7 |
