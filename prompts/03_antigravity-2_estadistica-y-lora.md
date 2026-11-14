# 03 · Antigravity 2 — Motor estadístico v2 (ruta crítica nº 2) y, después, LoRA

**Rama:** `feature/stats` (fase 2: `feature/lora`) · **Carpetas:** `src/stats/`, `tests/stats/`, `src/ml/`, `docs/VALIDACION_ESTADISTICA.md`
**Antes:** lee `prompts/00_LEER_PRIMERO.md` y `docs/CONTRATOS.md` (§4, §5, §6, §10).

## Tu misión
Los jueces son científicos de la Tierra. El motor actual declararía «significativo» casi cualquier cosa porque ignora la autocorrelación de los datos mensuales.
Tú entregas una estadística que un climatólogo firmaría, y la prueba de que es correcta. Después entrenas el planificador LoRA.

## FASE 1 — Estadística (objetivo: listo a las 17:00 del sábado)

### E1 — `analyze_series(ts, *, alpha=0.05, ratio_scale=False, homogeneous_since=None)` (P0)
Entrada: TimeSeries v2. Salida: AnalysisResult v2 (todo salvo `variable`). Usa `numpy`, `scipy` y `pymannkendall`; **comprueba sus firmas reales** antes de usarlas.

1. Recorta a `homogeneous_since` si viene (y añade el aviso `SOURCE_SPLICE` si se pidió un periodo que lo cruza). Tiempo en año decimal.
2. `INSUFFICIENT_DATA` si hay menos de 10 años o cobertura < 80 %. Los nulos se saltan con su fecha real; nunca se rellenan.
3. Climatología mensual del periodo analizado → anomalías.
4. **Pendiente de Sen** sobre las anomalías frente al tiempo, con todos los pares (sin submuestrear), e IC 95 %.
5. **Mann-Kendall** con corrección de empates, y versión corregida por autocorrelación (Hamed y Rao 1998). Devuelve ambos valores p.
6. **Mann-Kendall sobre medias anuales** (años con ≥ 10 meses) como comprobación independiente.
7. **MCO + prueba t ajustada** (Santer et al. 2000): r1 de los residuos, `n_eff = n(1−r1)/(1+r1)` (r1 acotado a [0, 0,95]), error estándar y grados de libertad con `n_eff`, IC 95 % y valor p.
8. **Detectabilidad** (Weatherhead et al. 1998, doi:10.1029/98JD00995): `n* = [(3,3·σ_N/|ω|)·√((1+φ)/(1−φ))]^(2/3)` años, con σ_N y φ de los residuos mensuales y ω la pendiente anual. Lee el artículo y confirma la fórmula y sus unidades antes de implementarla. `more_years_needed = max(0, n* − años)`.
9. **Veredicto**: `SIGNIFICANT_STRONG` (p corregido < 0,01, anual < 0,05 y el IC excluye 0) · `SIGNIFICANT` (p corregido < 0,05 y lo confirma el anual o la prueba t) · `SUGGESTIVE` (solo una prueba < 0,05, o 0,05 ≤ p < 0,10; aviso `TESTS_DISAGREE` si procede) · `NOT_SIGNIFICANT`.
10. `total_change = pendiente anual × años`. `percent_per_decade` solo si `ratio_scale` (pendiente por década / |media del periodo| × 100).
11. `answers` en ES y EN con plantillas por veredicto y dirección. Lenguaje honesto: «compatible con», «los datos aún no permiten afirmarlo». Nunca atribuyas causas.
12. Series de salida para la gráfica, incluida la banda de confianza de la recta y las medias anuales.

### E2 — Pruebas que demuestran que es correcto (P0)
`tests/stats/` (los datos simulados **solo** viven aquí):
- Cobertura: 300 simulaciones de recta conocida + ruido AR(1) (φ = 0,5) → el IC 95 % contiene la pendiente verdadera en 90–98 % de los casos.
- Falsos positivos: 300 simulaciones AR(1) **sin** tendencia → con corrección, la tasa de «significativo» queda ≤ 10 %; sin corrección, mide cuánto sube. Guarda ambas cifras: van a la presentación.
- Contraste con `pymannkendall` y `scipy.stats` sobre la muestra real de Lima (`tests/fixtures/real/`), igualdad con tolerancia.
- Empates, nulos, serie corta, serie constante, pendiente negativa.
- `pytest tests/stats -q` en verde. Pega la salida.

### E3 — `analyze_grid` y `compare` (P1)
- Rejilla: por celda, medias anuales → Sen por década + Mann-Kendall, vectorizado. Significancia con **Benjamini-Hochberg, q = 0,10** (Wilks 2016, doi:10.1175/BAMS-D-15-00267.1). Salida TrendMap v2.
  Rendimiento: 400 celdas × 45 años en menos de 2 s.
- `compare(a, b)`: `opposite` si los signos difieren y ambas son significativas; diferencia de pendientes con z = (b1−b2)/√(SE1²+SE2²); frase en ES y EN.

### E4 — Validación contra valores publicados (P1, es oro para el criterio Validez)
Cuando Antigravity 1 entregue GISTEMP y hielo marino: calcula (a) la tendencia de la temperatura media global y (b) la del hielo marino ártico de septiembre,
y compáralas con las cifras que **publican** NASA GISS y NSIDC. Busca esas cifras en sus páginas oficiales hoy y cita la URL; no uses números de memoria.
Escribe `docs/VALIDACION_ESTADISTICA.md` (inglés, con resumen en español): método, tabla «publicado vs. calculado», resultados de E2, limitaciones.

## FASE 2 — LoRA (empieza al cerrar E1–E3; el dataset lo produce Hermes 2 en `data/lora/`)

Objetivo medible: que un modelo pequeño y abierto convierta la pregunta de un estudiante en un `InvestigationPlan` (contrato §10) mejor que el modelo base y que las reglas.

- **L1 — Pipeline** en `src/ml/` con entorno aparte (`.venv-ml`): `train_lora.py`, `eval_lora.py`, `README.md`.
  Antes de escribir código, lee la documentación **vigente** de `transformers`, `peft` y `trl` (formato de mensajes, pérdida solo sobre la respuesta del asistente, selección de módulos). No programes de memoria.
- **Modelo base**: pequeño (≤ 4 B de parámetros), licencia permisiva, descargable sin trámite, buen español, convertible para Ollama, y de **origen no chino**
  (la guía revisa vínculos con entidades chinas; evitamos el riesgo). Pistas a verificar en huggingface.co: Phi-4-mini (MIT), IBM Granite pequeño (Apache-2.0), Gemma pequeño (pide aceptar términos).
  Elige con datos: prueba de carga + 50 ejemplos sin afinar. Si el tiempo da, entrena dos tamaños y quédate con el menor que cumpla.
- **Valores de partida** (ajusta con la validación): r = 16, alfa = 32, dropout 0,05, todas las capas lineales, lr 2e-4 con coseno, 3 épocas, secuencia ≤ 512, semilla 42, guardar el mejor por pérdida de validación.
- **L2 — Prueba de humo**: una pasada con 20 ejemplos y un modelo diminuto para comprobar que el pipeline corre de principio a fin sin GPU grande.
- **L3 — Entrenamiento real**: ejecuta `nvidia-smi` y reporta la VRAM libre. **Si hay menos de 8 GB libres, no toques nada**: pide al humano una ventana de GPU
  (la RTX 4070 SUPER de la PC1 está casi llena por un modelo cargado en Ollama) o usa Kaggle/Colab con el mismo script. Deja el entrenamiento en **un solo comando** documentado.
- **L4 — Evaluación** sobre `data/lora/test.jsonl` (nunca visto): JSON válido %, intención, variable correcta en 1.ª posición, variable entre las 3 primeras, lugar exacto, detección de fuera de tema, latencia.
  Tres columnas: reglas · modelo base · LoRA. Escríbelo en `docs/EVAL_IA.md`. **Si el LoRA no gana, se reporta tal cual y se usa lo mejor.** Nada de maquillar.
- **L5 — Servir**: fusiona el adaptador, conviértelo y regístralo en Ollama como `etd-planner` siguiendo la documentación vigente de importación de Ollama. Límite 45 min;
  plan B: servidor mínimo compatible con la API de chat de OpenAI en `src/ml/serve.py`. Entrega a Claude Omni 2 el nombre del modelo y el esquema JSON para salida restringida.
- **L6 — Ficha del modelo** (`src/ml/MODEL_CARD.md`): base, licencia, datos, cómo se generaron (con qué IA), métricas, límites. Si el humano lo aprueba, publica el adaptador en Hugging Face.

## Plan B
- `pymannkendall` no instala → implementa Hamed-Rao tú y contrástalo con un caso publicado.
- Sin GPU el domingo a las 08:00 → se cierra L4 con reglas vs. modelo base y se declara el LoRA como experimento pendiente.

Reporta en `reports/antigravity-2.md`.
