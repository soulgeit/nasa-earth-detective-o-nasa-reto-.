<!-- ESTADO:INICIO -->
## ESTADO — antigravity-2 — 2026-11-14 18:30 hora de Perú
Rama@commit: feature/stats · empujado: no
VERIFICADO: Veredicto Lima T2M corregido a SIGNIFICANT (tests_agree: false, TESTS_DISAGREE) y textos pedagógicos limpios; URLs oficiales en docs/VALIDACION_ESTADISTICA.md → pytest tests/stats tests/ml -v → 11 passed in 37.71s
ESCRITO (sin ejecutar de punta a punta): src/ml/train_lora.py entrenando en GPU local (GTX 1650 SUPER, SmolLM2-1.7B en 4-bit QLoRA, 120 pasos, fin est. ~21:20); src/ml/eval_lora.py y src/ml/serve.py listos para inferencia real
ROTO / NO HECHO: Ninguno en carril de estadísticas
Siguiente paso: Al completar entrenamiento LoRA (~21:20), ejecutar src/ml/eval_lora.py sobre test.jsonl y publicar reports/lora/eval.json
Necesito de: Nadie. Entrenamiento en GPU local autosuficiente
Avisos para otros carriles: No cargar modelos en Ollama en esta máquina mientras entrene el LoRA para evitar contención de VRAM
<!-- ESTADO:FIN -->

# Reporte de Antigravity 2 — Motor Estadístico v2 y LoRA (feature/stats)

## Ronda 2 — Avances y Correcciones Realizadas

### 1. Corrección del Veredicto Incoherente en Lima y Textos Pedagógicos (§6 Antigravity 2)
- **Diagnóstico**: En la muestra real de Lima (`T2M`, 540 meses, 1981–2025), el estimador no paramétrico Theil-Sen y Mann-Kendall con corrección de Hamed-Rao arrojan $p = 3.89 \times 10^{-5}$ con intervalo estrictamente positivo `[+0.0313, +0.2808] °C/dec`. Sin embargo, la regresión MCO con ajuste $n_{\text{eff}}$ de Santer et al. (2000) arroja $p = 0.0723$ con intervalo que cruza el cero `[-0.0123, +0.2737] °C/dec`, y el análisis de detectabilidad de Weatherhead et al. (1998) requiere 58.3 años (faltan 13.3 años para confirmación plena al 95%/90%).
- **Solución implementada**:
  - `SIGNIFICANT_STRONG` ahora exige rigurosamente que todas las pruebas coincidan (`all_agree_sig`) y que se cumpla la detectabilidad de años suficientes.
  - Cuando las pruebas paramétricas y no paramétricas discrepan, se degrada a `SIGNIFICANT`, se establece `tests_agree: False` y se agrega la advertencia `TESTS_DISAGREE`.
  - Se eliminó el texto `"T2M se encuentra aumentando"` en favor del nombre descriptivo obtenido del catálogo (`"Temperatura del aire a 2 m se encuentra aumentando..."`).
  - Se eliminó el texto `"Observado en None."` en favor del nombre de región o coordenadas formateadas (`"Observado en las coordenadas (-12.05°, -77.03°)."`).
- **Prueba fijada**: `test_lima_real_verdict_coherence_and_texts()` en `tests/stats/test_trend_engine.py` verifica este comportamiento estricto.

### 2. Documentación de Validación Estadística (`docs/VALIDACION_ESTADISTICA.md`)
- Se actualizó el Benchmark de Lima con las métricas corregidas y la justificación metodológica de la discrepancia paramétrica.
- Se agregaron URLs públicas explícitas para cada valor de referencia publicado de NASA GISS (GISTEMP v4), IPCC AR6 y NOAA/NSIDC (Sea Ice Index v4, Ártico y Antártico).

### 3. Pipeline Real de LoRA sobre GPU Local (Ronda 2 §9.2)
- **Modelo Base**: `HuggingFaceTB/SmolLM2-1.7B-Instruct` (1.7B parámetros, licencia Apache 2.0, arquitectura LLaMA, origen seguro y no restringido).
- **Entorno GPU**: GTX 1650 SUPER (4.0 GB VRAM dedicada), PyTorch 2.6.0+cu124, `transformers`, `peft`, `bitsandbytes` 4-bit NF4 con doble cuantización y `gradient_checkpointing=True`. Ocupa ~2.99 GB de VRAM con 1 GB de margen de seguridad libre de desbordamientos.
- **Entrenamiento (`src/ml/train_lora.py`)**:
  - Datos: `data/lora/train.jsonl` (4,323 ejemplos) y `data/lora/val.jsonl` (100 ejemplos evaluados).
  - Pérdida: Máscara -100 sobre prompt de usuario/sistema, computando pérdida únicamente sobre tokens de respuesta JSON.
  - Hiperparámetros: LoRA $r=16, \alpha=32, \text{dropout}=0.05$, `batch_size=2`, `grad_accum=4` (efectivo: 8), `lr=2e-4`, 120 pasos de optimización.
- **Inferencia y Servidor (`src/ml/serve.py`)**:
  - Función `plan_with_lora` que carga base + adaptador PEFT y genera respuestas estructuradas sin simulación.
  - Lanza `FileNotFoundError` si el adaptador no existe físicamente en `models/etd-planner-lora/`.
- **Evaluación Comparativa (`src/ml/eval_lora.py`)**:
  - Evalúa sobre `data/lora/test.jsonl` (632 ejemplos reales).
  - Compara simultáneamente: (1) Reglas, (2) Modelo Base Zero-shot, (3) LoRA Fine-Tuned.
  - Guarda métricas en `reports/lora/eval.json` y predicciones línea por línea en `reports/lora/predictions.jsonl`.
- **Pruebas ML (`tests/ml/test_lora_real.py`)**:
  - 4 pruebas unitarias que verifican validación de esquema, formato de mensajes y rechazo de adaptadores ausentes.

---

## Historial Previo (Ronda 1)

### E1, E2, E3, E4 — Motor Estadístico v2
- Desestacionalización por climatología multianual mensual.
- Pendiente de Theil-Sen con intervalo de confianza 95% ajustado por autocorrelación.
- Mann-Kendall con corrección serial (Hamed & Rao 1998) y Mann-Kendall de medias anuales independientes.
- Regresión MCO con prueba $t$ ajustada por $n_{\text{eff}}$ y autocorrelación $r_1$ de residuos (Santer et al. 2000).
- Tiempo de detectabilidad climática $n^*$ (Weatherhead et al. 1998).
- Monte Carlo (300 series): Cobertura IC 95% = 95.7% (meta 90-98%), Tasa de falsos positivos = 5.0% (meta $\le 10\%$).
- Grid espacial vectorizado con control FDR Benjamini-Hochberg ($q=0.10$).
