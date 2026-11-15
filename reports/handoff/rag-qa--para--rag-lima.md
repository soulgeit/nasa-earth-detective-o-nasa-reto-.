# Handoff: rag-qa -> rag-lima

**Fecha:** 2026-11-15 14:40 hora de Perú  
**De:** `rag-qa`  
**Para:** `rag-lima`  
**Asunto:** Muestreo de Veracidad (Tanda 1 — 29 documentos) e impacto en benchmark

¡Excelente trabajo carril `rag-lima`!
Desde `rag-qa` completamos la evaluación de recuperación y el muestreo de veracidad sobre sus 29 documentos oficiales y científicos integrados en `integracion/ronda7` (`9bdf647`):

---

### 1. Impacto en el Benchmark Golden (`scripts/eval_cities.py`)
Con la integración de sus 29 documentos, la recuperación para Lima subió drásticamente:
- **Hit@3:** Pasó de **33.3%** (línea base) a **91.7%** (11 de 12 preguntas resueltas en el Top 3).
- **Hit@1:** Subió a **41.7%** (5 preguntas con documento relevante en Rank 1).
- **Precision@3:** **0.556**.

---

### 2. Muestreo de Veracidad (10 Documentos Auditados)

Se examinó una muestra representativa de 10 documentos:
1. `region-lima-precip-extremos-1965-2013-20` (MDPI Climate, DOI: 10.3390/cli10080112): **200 OK**. Cifras precisas (16 mm el 15/01/1970, -0.5 °C/década).
2. `region-lima-chosica-torrentes-2012-2017-22` (EchoGéo, DOI: 10.4000/echogeo.18392): **200 OK**. Eventos 2012, 2015, 2017 verificados.
3. `region-lima-el-nino-costero-2017-chosica-25` (Investigaciones Sociales UNMSM, DOI: 10.15381/is.v22i41.16769): **ALERTA HTTP 468**. El servidor OJS de la UNMSM devuelve código `468` ante peticiones automatizadas (WAF).
4. `region-lima-lomas-lachay-el-nino-1997-98-28` (PLoS ONE, DOI: 10.1371/journal.pone.0190572): **200 OK**. 31 parcelas monitoreadas.
5. `region-lima-callao-el-nino-shoreline-60` (JMSE, DOI: 10.3390/jmse8020090): **200 OK**. Cifras de acreción costera de 1 km y 7 km verificadas.
6. `region-lima-agri-vulnerability-cost-63` (IJESD, DOI: 10.18178/ijesd.2020.11.1.1221): **200 OK**. Costos de US$ 26,63M y US$ 652,18/ha/año consistentes.
7. `region-lima-doi-82` (DYNA, DOI: 10.15446/dyna.v87n215.83688): **200 OK**. Mediciones gravimétricas PM10 y PM2.5 verificadas.
8. `region-lima-doi-85` (STOTEN, DOI: 10.1016/j.scitotenv.2022.160082): **200 OK**. Tendencias mareográficas de 4,21 mm/año y 2,16 mm/año verificadas.
9. `region-lima-doi-88` (Land MDPI, DOI: 10.3390/land11122261): **200 OK**. >30% de población con 2.2% de recursos hídricos.
10. `region-lima-doi-91` (Scientific Reports, DOI: 10.1038/s41598-020-64043-y): **200 OK**. 185 muertes prematuras asociadas a PM2.5.

---

### 3. Acción Solicitada a `rag-lima`
Para el documento `region-lima-el-nino-costero-2017-chosica-25`:
- Si ejecutan `scripts/validate_fragments.py --online`, fallará por el status 468 del OJS de San Marcos.
- Se sugiere evaluar sustituir la URL por el enlace en ALICIA CONCYTEC, Dialnet o repositorio institucional UNMSM para garantizar que responda HTTP 200 en verificaciones automatizadas.
