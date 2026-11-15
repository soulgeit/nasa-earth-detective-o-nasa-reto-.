# Ronda 7 — QA Informe Inicial (Línea Base)

**Fecha y hora:** 2026-11-15 14:15 hora de Perú  
**Carril:** `rag-qa`  
**Rama:** `rag/qa` sobre `integracion/ronda7`  
**Objetivo:** Establecer la línea base de evaluación del RAG sobre las cinco ciudades antes del ingreso de las tandas de fragmentos.

---

## 1. Conjunto de Evaluación: `data/knowledge/golden_cities.jsonl`

Se formalizaron **60 preguntas reales de referencia**, distribuidas equitativamente:
- **5 ciudades:** Lima, Huancayo, Andahuaylas, Ica, Ayacucho (12 preguntas por ciudad).
- **12 temas por ciudad (§4 de `docs/RONDA_7.md`):**
  1. Ubicación, altitud, relieve, cuenca.
  2. Temperatura normal: medias, máximas y mínimas estacionales.
  3. Lluvia: estacionalidad, totales, garúa, años secos y húmedos.
  4. Extremos: heladas, friajes, olas de calor, huaicos, inundaciones, granizo, sequías.
  5. El Niño y La Niña: impactos locales históricos.
  6. Agua: ríos, glaciares y nevados, lagunas, acuíferos, embalses.
  7. Agricultura: cultivos representativos, calendario agrícola, riesgo climático.
  8. Aire y radiación: calidad del aire, polvo, radiación UV, nubosidad.
  9. Suelo y vegetación: uso del suelo, deforestación, expansión urbana, NDVI.
  10. Tendencias ya publicadas (estudios, SENAMHI, INAIGEM, IPCC): cifra, unidad y periodo.
  11. Estaciones y datos: estaciones SENAMHI, observatorios, límites de celdas satelitales.
  12. Población expuesta y sectores vulnerables.
- **Idiomas:** 30 preguntas en español (`es`) y 30 en inglés (`en`) (6 de cada una por ciudad).

---

## 2. Línea Base Inicial (Tanda 0 — Previa a Fragmentos)

Ejecución reproducible:
```powershell
python scripts/eval_cities.py --markdown
```

### Resultados de la Línea Base:
| Ciudad | Preguntas | Hit@1 | Hit@1 % | Hit@3 | Hit@3 % | Precision@3 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lima** | 12 | 1 | 8.3% | 4 | 33.3% | 0.111 |
| **Huancayo** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **Andahuaylas** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **Ica** | 12 | 1 | 8.3% | 3 | 25.0% | 0.083 |
| **Ayacucho** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **TOTAL** | **60** | **2** | **3.3%** | **7** | **11.7%** | **0.039** |

### Diagnóstico de la Línea Base:
- El corpus heredado de `docs.jsonl` solo tenía presencia marginal de Lima (1 doc) e Ica (1 doc) y fichas generales de biomas/variables.
- Huancayo, Andahuaylas y Ayacucho tienen **0% de aciertos** en el Top 3, confirmando la necesidad imperiosa de las tandas de nutrición regional (§1).
- Esta medición servirá como punto de referencia contra el cual se evaluará el progreso en las Tandas 1 (15:15), 2 (16:30) y 3 (17:30).

---

## 3. Protocolo de QA para las Tandas de Nutrición
1. **Medición de Recuperación:** Ejecutar `scripts/eval_cities.py` tras cada tanda integrada en `integracion/ronda7`.
2. **Muestreo de Veracidad (Regla 8):** Inspección aleatoria de 10 documentos por carril y tanda. Acceso a la URL primaria para verificar que la cifra, unidad y periodo existen textualmente.
3. **Detección de Inconsistencias y Duplicados:** Comparación entre fragmentos de distintos carriles para prevenir contradicciones numéricas. Notificación vía `reports/handoff/rag-qa--para--<carril>.md`.
4. **Ventana de Corrección Exclusiva (18:30):** A partir de las 18:30, `rag-qa` será el único autor autorizado para corregir fragmentos de cualquier carril previo al cierre.
