<!-- ESTADO:INICIO -->
## ESTADO — rag-qa — 2026-11-15 14:15 hora de Perú
Rama@commit: rag/qa · empujado: sí
VERIFICADO: Arranque de Ronda 7 completado; data/knowledge/golden_cities.jsonl creado con 60 preguntas reales de referencia (12 por ciudad en Lima, Huancayo, Andahuaylas, Ica y Ayacucho; 30 en español y 30 en inglés; cubriendo exactamente los 12 temas climáticos de §4); scripts/eval_cities.py implementado y probado midiendo Hit@1, Hit@3 y Precision@3 por ciudad; suite tests/detective/test_golden_cities.py (7 passed en 0.33s) y tests/detective/test_fragments.py (6 passed en 0.23s) al 100% en verde; scripts/validate_fragments.py verificado; línea base inicial de recuperación documentada en reports/qa/ronda7-baseline.md (Hit@3 inicial de 11.7% confirmando la necesidad de nutrición regional).
ESCRITO (sin ejecutar de punta a punta): Ninguno.
ROTO / NO HECHO: Ninguno. Marco de evaluación y muestreo de veracidad listo para recibir las tandas de fragmentos.
Siguiente paso: Esperar la Tanda 1 (15:15) en integracion/ronda7 para medir progreso de recuperación, ejecutar muestreo de veracidad (10 docs por carril) y emitir notas handoff si hay inconsistencias.
Necesito de: Los carriles regionales (rag-lima, rag-huancayo, rag-andahuaylas, rag-ica, rag-ayacucho), rag-datos y rag-recursos: empujar sus primeras tandas (≥15 docs/ciudad) a integracion/ronda7.
Avisos para otros carriles: El benchmark oficial de las cinco ciudades está activo en data/knowledge/golden_cities.jsonl. Pueden ejecutar python scripts/eval_cities.py localmente para comprobar si sus fragmentos son recuperados para su ciudad y temas.
<!-- ESTADO:FIN -->

# Reporte de QA y Calidad RAG — Ronda 7 (Huiracocha IA)

**Carril:** `rag-qa`  
**Rama:** `rag/qa` (integrada en `integracion/ronda7`)  
**Archivos bajo gestión exclusiva:**
- `data/knowledge/golden_cities.jsonl`
- `scripts/eval_cities.py`
- `tests/detective/test_golden_cities.py`
- `reports/rag-qa.md`
- `reports/qa/ronda7-*.md`
- `reports/handoff/rag-qa--para--*.md`

---

## 1. Entregables del Arranque (14:15)

1. **Conjunto Golden de 60 Preguntas Reales (`data/knowledge/golden_cities.jsonl`):**
   - 12 preguntas por ciudad en Lima, Huancayo, Andahuaylas, Ica y Ayacucho.
   - Distribución equitativa: 30 preguntas en español (`es`) y 30 en inglés (`en`).
   - Cobertura exhaustiva 1:1 de los 12 temas climáticos definidos en `docs/RONDA_7.md` §4:
     - Tema 1: Ubicación, altitud, relieve y cuenca.
     - Tema 2: Temperatura normal (medias, máximas y mínimas).
     - Tema 3: Lluvia (estacionalidad, totales, garúa).
     - Tema 4: Extremos (heladas, friajes, olas de calor, huaicos, inundaciones, sequías).
     - Tema 5: El Niño y La Niña (impactos locales documentados).
     - Tema 6: Agua (ríos, glaciares, lagunas, acuíferos, embalses).
     - Tema 7: Agricultura (cultivos tradicionales, calendario agrícola, riesgo climático).
     - Tema 8: Aire y radiación (calidad del aire, polvo, UV, nubosidad).
     - Tema 9: Suelo y vegetación (NDVI, lomas, expansión urbana).
     - Tema 10: Tendencias ya publicadas (estudios, SENAMHI, INAIGEM).
     - Tema 11: Estaciones meteorológicas e instrumentos de observación.
     - Tema 12: Población expuesta y sectores vulnerables.

2. **Motor de Evaluación RAG (`scripts/eval_cities.py`):**
   - Evalúa si `retrieve()` retorna en el Top 3 (`Hit@3`) un documento correspondiente a la ciudad esperada y al tema esperado.
   - Modos CLI: `--markdown`, `--json`, `--city <nombre>`, `--quiet`.
   - Soporte programático para integración en pruebas continuas.

3. **Batería de Pruebas Unitarias (`tests/detective/test_golden_cities.py`):**
   - 7 pruebas pasando al 100% en verde: estructura, cobertura de ciudades y temas, unicidad de IDs, correspondencia con el catálogo de variables, lógica de emparejamiento de ciudad/tema y ejecución del motor de evaluación.

---

## 2. Medición de Línea Base (Tanda 0 — Previa a Fragmentos)

```
| Ciudad | Preguntas | Hit@1 | Hit@1 % | Hit@3 | Hit@3 % | Precision@3 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lima** | 12 | 1 | 8.3% | 4 | 33.3% | 0.111 |
| **Huancayo** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **Andahuaylas** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **Ica** | 12 | 1 | 8.3% | 3 | 25.0% | 0.083 |
| **Ayacucho** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **TOTAL** | **60** | **2** | **3.3%** | **7** | **11.7%** | **0.039** |
```

Informe detallado disponible en [reports/qa/ronda7-baseline.md](file:///C:/Users/docto/etd-rag-qa/reports/qa/ronda7-baseline.md).
