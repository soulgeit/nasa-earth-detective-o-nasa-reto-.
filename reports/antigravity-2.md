<!-- ESTADO:INICIO -->
## ESTADO — antigravity-2 — 2026-11-15 00:25 hora de Perú
Rama@commit: feature/stats@355e834 · empujado: sí
VERIFICADO: Respaldo silencioso de src/ml/serve.py:65 eliminado; carpeta duplicada models/planner-lora/ borrada con git rm; tests/ml/test_lora_real.py verde (4 passed, 1 skipped por GPU) sin tocar la aserción; prueba contraria añadida bajo Regla 22; requirements-ml.txt creado con versiones exactas del entrenamiento (torch 2.6.0+cu124, transformers 5.23.0, peft 0.21.3, bitsandbytes 0.50.2, accelerate 1.15.0) y comandos canónicos de reproducción; src/ml/MODEL_CARD.md publicado en inglés con regla 20 (ambos benchmarks: 200 casos de test 84.5% var match y 50 preguntas de referencia 31/50) y sección obligatoria de Limitations; docs/VALIDACION_ESTADISTICA.md enriquecido con la regla de los cuatro veredictos en inglés (§3.6); suite entera ejecutada (tests/ml y tests/stats en verde; 2 fallas restantes en tests/detective/test_pipeline.py corresponden a planned variables del carril claude-omni-2).
ESCRITO (sin ejecutar de punta a punta): Tabla «published vs. computed» de docs/VALIDACION_ESTADISTICA.md con hielo marino sin −9999 (esperando regeneración de hermes-2).
ROTO / NO HECHO: Rehechura final de la tabla «published vs. computed» de hielo marino en docs/VALIDACION_ESTADISTICA.md pendiente de la regeneración de series por hermes-2 (Dom 01:00; actualmente verify_seaice_cases.py falla con −9999).
Siguiente paso: Cuando hermes-2 publique los casos de hielo marino sin −9999, extraer las cifras finales de Sen/MCO y actualizar la tabla de docs/VALIDACION_ESTADISTICA.md antes de las 09:00.
Necesito de: hermes-2 (regeneración de arctic-seaice y antarctic-seaice sin −9999 con verify_seaice_cases.py en verde).
Avisos para otros carriles: models/planner-lora/ ha sido eliminado definitivamente con git rm; la ruta canónica única del adaptador es models/etd-planner-lora/ (Regla 21). El import de src/ml/serve.py ya no hace respaldo silencioso. requirements-ml.txt listo para reproducción en máquinas con GPU.
<!-- ESTADO:FIN -->

# Reporte de Antigravity 2 — Ronda 4 (Final)

## Tareas Completadas en la Ronda 4 (§4 antigravity-2)

### 1. Parada de evaluación GTX 1650 y no subir a models/ ni reports/lora/ (§4.1)
- Verificado: Ningún proceso en segundo plano de evaluación ni entrenamiento ejecutándose.
- Adaptador canónico único de antigravity-1 respetado en `models/etd-planner-lora/` (Regla 21).

### 2. Eliminación de respaldo silencioso y limpieza de carpeta duplicada (§4.2)
- Se eliminó el respaldo silencioso en `src/ml/serve.py:65` que apuntaba a `models/planner-lora`.
- Se eliminó la carpeta duplicada `models/planner-lora/` mediante `git rm -r`.
- `tests/ml/test_lora_real.py::test_plan_with_lora_missing_adapter_raises_error` volvió a verde inmediatamente sin modificar su aserción.
- Se añadió `tests/ml/test_lora_real.py::test_plan_with_lora_real_adapter_on_gpu`, que valida la inferencia en GPU con el adaptador canónico y se salta limpiamente en entornos sin GPU CUDA cumpliendo la Regla 22.
- Resultado: `tests/ml/` 4 passed, 1 skipped in 0.25s.

### 3. Archivo requirements-ml.txt (§4.3)
- Creado `requirements-ml.txt` con las dependencias y versiones exactas congeladas:
  - `torch==2.6.0+cu124` (con `--extra-index-url https://download.pytorch.org/whl/cu124`)
  - `transformers==5.23.0`
  - `peft==0.21.3`
  - `bitsandbytes==0.50.2`
  - `accelerate==1.15.0`
  - `datasets>=2.14.0`
- Contiene los dos comandos oficiales para reproducir tanto el entrenamiento LoRA como la evaluación formal.

### 4. Tarjeta de Modelo: src/ml/MODEL_CARD.md (§4.4)
- Redactada en inglés siguiendo las mejores prácticas de documentación de modelos (Hugging Face Model Card).
- Cumplimiento estricto de la Regla 20: Cita obligatoria simultánea de ambos números:
  - 200 casos de prueba sintéticos: LoRA 84.5% variable match vs Reglas 15.5%.
  - 50 preguntas de referencia escritas a mano: LoRA 31/50 (62.0%) vs Reglas 47/50 (94.0%).
- Sección «Limitations» obligatoria:
  - 150 pasos de entrenamiento (~0.28 épocas).
  - Test set sintético comparte generador con entrenamiento.
  - Precisión de hipótesis de LoRA (71.0%) inferior a reglas heurísticas (78.5%).
  - Modo de fallo de variables `planned` (15 de 19 fallos en preguntas de referencia).
  - Requisitos de hardware (CUDA GPU >= 4 GB VRAM) y respaldo automático a reglas en CPU.
  - Licencia Apache 2.0 del modelo base `HuggingFaceTB/SmolLM2-1.7B-Instruct`.

### 5. Validación Estadística: docs/VALIDACION_ESTADISTICA.md (§4.5)
- Incorporada la sección 3.6 en inglés con la regla formal de clasificación de los cuatro veredictos (`SIGNIFICANT_STRONG`, `SIGNIFICANT`, `SUGGESTIVE`, `NOT_SIGNIFICANT`).
- Actualización de la tabla con el hielo marino regenerado en espera de hermes-2 (límite 01:00).

### 6. Ejecución de la Suite Completa de Pruebas
- Suite completa `python -m pytest -q`: 236 passed, 2 failed, 10 skipped.
- Las 2 únicas pruebas en rojo corresponden a `tests/detective/test_pipeline.py` (variables `planned` bajo resolución por `claude-omni-2` según §4.1).
- Todos los tests del carril (`tests/ml/` y `tests/stats/`) pasan al 100%.

---

## Historial Previo (Rondas 1 a 3)
- Motor estadístico v2: Theil-Sen, Mann-Kendall con corrección de Hamed-Rao, MCO ajustado por Santer et al. (2000), detectabilidad de Weatherhead et al. (1998) y Monte Carlo (300 series) con cobertura 95.7% y falsos positivos al 5.0%.
- Resolución de incoherencia paramétrica en Lima y adición de advertencia `TESTS_DISAGREE`.
