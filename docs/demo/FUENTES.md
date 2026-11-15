# FUENTES — Cifras citadas en las 7 láminas de demostración

Documentación de procedencia de cada cifra y métrica que figura en `docs/demo/slides.html` y `docs/demo/EarthTrend_Detective_slides.pdf`.
Cumple con `docs/RONDA_5.md` §4 (claude-omni-1, tarea 4): *«Cada cifra de una lámina sale de un caso congelado o de docs/EVAL_IA.md y se anota de dónde en docs/demo/FUENTES.md»*.

---

### Lámina 1 — Título y Presentación
- **Lema del proyecto**: «Investigate a place on Earth with real NASA Earth science data». Fuente: `src/ui/index.html` (tagline oficial).
- **Caso protagonista**: Hielo marino del Ártico frente al Antártico (contraste científico honesto de «no hay tendencia»). Fuente: `docs/RONDA_5.md` §6.4.

---

### Lámina 2 — El Problema y las 4 Preguntas
- **Preguntas del desafío**: «What is changing? Where? How much? Is it statistically significant?». Fuente: `docs/KIT_ENTREGA.md` §4, NASA Space Apps Challenge 2026.
- **Variables científicas en catálogo**: 15 variables reales de la NASA implementadas + 10 variables planificadas de Giovanni GES DISC. Fuente: `data/catalog/variables.json`.

---

### Lámina 3 — La Solución en una Pantalla
- **Captura real**: `docs/media/verdict_view.png` (resolución 1600×900, generada contra el backend en vivo con datos reales).
- **Caso Lima T2M**:
  * Tasa de cambio: `+0.159 °C/década` (`+0.1585 °C/década` sin redondear; la UI redondea el valor publicado a 3 decimales). Fuente: `data/cases/lima-t2m/analysis.json`.
  * Cambio acumulado: `+0.713 °C` a lo largo de 45 años (540 meses, 1981–2025). Fuente: `data/cases/lima-t2m/analysis.json`.
  * Escalera de evidencia: 4 de 5 (`Significant trend`). Fuente: `data/cases/lima-t2m/case.json`.
  * Detectabilidad: `13.3 años adicionales` estimados para certeza estadística definitiva (Weatherhead et al. 1998). Fuente: `data/cases/lima-t2m/analysis.json` (`detectability.more_years_needed`).

---

### Lámina 4 — Datos Reales de la NASA: Fuentes y Procedencia
- **NASA POWER v2.10.0**: 540 meses continuos (1981-01 a 2025-12), resolución nativa 0.5° × 0.625° (MERRA-2). Fuente: `data/cases/lima-t2m/analysis.json` (`provenance`).
- **NSIDC Sea Ice Index v4**: 574 meses (1978-11 a 2026-10), resolución hemisférica mensual, 2 meses faltantes (1987-12 y 1988-01) enmascarados como `null`. Fuente: `data/cases/arctic-seaice/analysis.json` (`provenance`).
- **NASA GISTEMP v4**: 1.762 meses de anomalías globales de temperatura superficial (1880 a 2026). Fuente: `src/etl/gistemp.py`.
- **NASA GES DISC Giovanni**: 557 meses en exportaciones CSV reales de la cuenca amazónica (1980 a 2026). Fuente: `data/cases/amazonia-t2m/analysis.json`.

---

### Lámina 5 — Estadística Honesta: Escalera de 5 Niveles y «Años que Faltan»
- **Caso Ártico (`arctic-seaice`)**:
  * Pendiente Theil-Sen: `−0.495 millones de km²/década` (`-4.4 %/década`). Fuente: `data/cases/arctic-seaice/analysis.json`.
  * Cambio acumulado: `−2.378 millones de km²` en 48 años. Fuente: `data/cases/arctic-seaice/analysis.json`.
  * Veredicto: `Clear, strong trend` (5/5). Todas las pruebas estadísticas coinciden (`tests_agree: true`, $p < 0.001$). Fuente: `data/cases/arctic-seaice/analysis.json`.
- **Caso Antártico (`antarctic-seaice`) — Contraste Científico Honesto**:
  * Pendiente Theil-Sen: `−0.048 millones de km²/década` (`-0.4 %/década`). Fuente: `data/cases/antarctic-seaice/analysis.json`.
  * Veredicto: `No trend detectable so far` (2/5). El cambio observado corresponde a variabilidad natural ($p = 0.528$). Fuente: `data/cases/antarctic-seaice/analysis.json`.
  * Años faltantes: `84.8 años adicionales` necesarios para confirmar una tendencia real (Weatherhead et al. 1998). Fuente: `data/cases/antarctic-seaice/analysis.json` (`detectability.more_years_needed`).

---

### Lámina 6 — Análisis Espacial y Asistente con IA Fundamentada
- **Atlas Espacial de Tendencias (TrendMap)**: 759 celdas regionales analizadas con control de tasa de falsos descubrimientos (*False Discovery Rate*, FDR Benjamini-Hochberg $q = 0.10$). Fuente: `data/atlas/T2M.json` y `docs/media/trendmap_spatial.png`.
- **Modo Comparación**: Lima, Perú (`+0.159 °C/década`) vs. Ártico Svalbard (`+0.699 °C/década`, amplificación polar 4×). Fuente: `data/cases/svalbard-t2m/analysis.json` y `docs/media/compare_mode.png`.
- **Evaluación del Asistente Detective**:
  * Planificador por reglas: `50/50` preguntas de referencia acertadas (`100 %`). Fuente: `docs/EVAL_IA.md` y `docs/RONDA_5.md` §1.
  * Planificador LoRA afinado (`SmolLM2-1.7B` en 4 bits, RTX 4070 SUPER): `40/50` preguntas acertadas (`80.0 %`), latencia mediana de `2.2 s/pregunta`. Fuente: `docs/EVAL_IA.md` y `reports/_arquitecto.md`.
  * Corpus de conocimiento: `168 documentos` y fichas de la NASA verificadas con citas estrictamente extractivas. Fuente: `data/knowledge/docs.jsonl`.

---

### Lámina 7 — Impacto, Acceso Público y Próximos Pasos
- **Despliegue público en vivo**: `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` (100 % funcional sin servidores ni instalaciones). Fuente: `docs/RONDA_5.md` §1.
- **Responsive en móvil**: Medido en viewport 390×844 px, `0 px` de desplazamiento horizontal, mapa y gráfica interactivos. Fuente: `docs/media/mobile_390_overview.png` y `reports/claude-omni-1.md`.
- **Licencia y código abierto**: Código bajo licencia MIT; datos y metadatos con atribución a NASA POWER, GISS, NSIDC y GES DISC. Fuente: `LICENSE`.
