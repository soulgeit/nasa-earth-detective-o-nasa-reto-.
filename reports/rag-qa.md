<!-- ESTADO:INICIO -->
## ESTADO — rag-qa — 2026-11-15 15:45 hora de Perú
Rama@commit: rag/qa · empujado: sí
VERIFICADO: Integración completa de las 5 ciudades y recursos evaluada sobre integracion/ronda7; corpus validado con scripts/validate_fragments.py --stats suma 712 documentos válidos en 13 archivos (Lima 130, Ica 137, Huancayo 123, Andahuaylas 118, Ayacucho 162, Recursos 42); evaluación RAG global (scripts/eval_cities.py) subió a 66.7% Hit@3 (40/60) y 35.0% Hit@1 (21/60), destacando Ayacucho (100.0% Hit@3), Huancayo (66.7%), Andahuaylas (66.7%), Lima (58.3%) e Ica (41.7%); muestreo de veracidad cruzado (10 docs por carril) completado: Huancayo impecable (10/10 en 200 OK), Andahuaylas 9/10 en 200 OK, Recursos 8/10 en 200 OK; detectada alerta crítica en Ayacucho (7/10 URLs con HTTP 404 por rutas no existentes en gob.pe) y enlace roto 404 en Ica (Atlas radiación); handoffs emitidos para rag-ayacucho, rag-ica, rag-lima y rag-recursos; suite tests/detective/ al 100% en verde (13 passed).
ESCRITO (sin ejecutar de punta a punta): Ninguno.
ROTO / NO HECHO: Ninguno en carril rag-qa. URLs 404 reportadas en Ayacucho e Ica notificadas a los dueños para corrección antes de las 18:30 (momento en que rag-qa asume corrección exclusiva).
Siguiente paso: Monitorear subsanación de enlaces rotos por los carriles y preparar informe final consolidado a las 18:45.
Necesito de: rag-ayacucho: corregir los 7 enlaces rotos (404) de gob.pe reportados en handoff; rag-ica: corregir URL 404 de radiación.
Avisos para otros carriles: Handoff crítico emitido en reports/handoff/rag-qa--para--rag-ayacucho.md; informes detallados en reports/qa/ronda7-tanda1.md y reports/qa/ronda7-tanda2.md.
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

---

## 3. Auditoría Preventiva de Recursos del Reto (§8)
- **13 enlaces del reto (§8)** auditados por conectividad, SSL y presencia previa en `docs.jsonl`.
- **10 enlaces respondiendo HTTP 200** directamente (Giovanni, GES DISC, AppEEARS, NOAA NCEI, NTRS PDF, KNMI, Statsig, Geo.ca, ASC Ecosystems, CSA SAR Tutorial).
- **1 duplicado identificado:** `https://www.asc-csa.gc.ca/eng/satellites/swot/` ya existe en `docs.jsonl` bajo `res-csa-swot`. `rag-recursos` debe usar `"supersedes": ["res-csa-swot"]` si lo actualiza para evitar duplicación.
- **2 alertas transmitidas:** `SSLError` en `donnees-data.asc-csa.gc.ca` (cadena de certificados) y `403` en Medium (bloqueo a bots que exige resumen propio `is_quotation: false`).
- Nota oficial de coordinación emitida en [reports/handoff/rag-qa--para--rag-recursos.md](file:///C:/Users/docto/etd-rag-qa/reports/handoff/rag-qa--para--rag-recursos.md).

