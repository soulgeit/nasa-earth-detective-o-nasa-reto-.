# Ronda 7 — QA Informe de Tanda 1 (15:00)

**Fecha y hora:** 2026-11-15 15:00 hora de Perú  
**Carril:** `rag-qa`  
**Rama:** `rag/qa` sobre `integracion/ronda7`  

---

## 1. Estado de Fragmentos en el Repositorio
Resultado de `python scripts/validate_fragments.py --stats`:
```
fragment                            docs   es   en  urls quotes
regions/ica.jsonl                     54   43   11    26      0
regions/lima.jsonl                    29   19   10    25      0

OK: 83 document(s) valid in 2 fragment file(s).
```

---

## 2. Medición de Recuperación RAG (`scripts/eval_cities.py`)

```
| Ciudad | Preguntas | Hit@1 | Hit@1 % | Hit@3 | Hit@3 % | Precision@3 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lima** | 12 | 5 | 41.7% | 8 | 66.7% | 0.361 |
| **Huancayo** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **Andahuaylas** | 12 | 0 | 0.0% | 0 | 0.0% | 0.000 |
| **Ica** | 12 | 9 | 75.0% | 11 | 91.7% | 0.556 |
| **Ayacucho** | 12 | 1 | 8.3% | 1 | 8.3% | 0.028 |
| **TOTAL** | **60** | **15** | **25.0%** | **20** | **33.3%** | **0.189** |
```

### Hallazgos Principales:
- **Ica (`rag-ica`):** Excelente desempeño. Con 54 documentos cubriendo los 12 temas, Ica alcanza un **91.7% Hit@3** (11/12 preguntas) y **75.0% Hit@1** (9/12 preguntas en primera posición).
- **Lima (`rag-lima`):** Se mantiene sólida con 29 documentos oficiales y científicos (8/12 en Top 3 y 5/12 en Rank 1).
- **Huancayo y Andahuaylas:** Pendientes de la llegada de sus primeras tandas para activar el RAG local.

---

## 3. Muestreo de Veracidad (10 Documentos por Carril)

### A. Muestreo `rag-lima` (10 docs):
- **9 / 10 enlaces verificados HTTP 200** (MDPI Climate, EchoGéo, PLoS ONE, JMSE, IJESD, DYNA, STOTEN, Land, Scientific Reports).
- **1 / 10 enlace con alerta:** `region-lima-el-nino-costero-2017-chosica-25` devuelve HTTP 468 por WAF en OJS San Marcos.
- Trazabilidad numérica: 100% de coherencia en fechas, precipitaciones y temperaturas. Handoff enviado en `reports/handoff/rag-qa--para--rag-lima.md`.

### B. Muestreo `rag-ica` (10 docs):
- **5 / 10 enlaces verificados HTTP 200** (citypopulation.de, climate-zone.com, SIGRID CENEPRED, Gob.pe CDN).
- **1 / 10 enlace ROTO (HTTP 404):** `region-ica-radiacion-en` apunta a `https://www.senamhi.gob.pe/pdf/Atlas%20de_Radiacion_Solar.pdf` (página no existe).
- **4 / 10 enlaces con bloqueo de bot (HTTP 403):** 3 enlaces de OECD iLibrary y 1 de PMC NCBI.
- Trazabilidad numérica: Datos de descenso de napa freática (1.4 m/año), lluvias (<5 mm/año) e impacto económico corroborados.
- Handoff crítico enviado en `reports/handoff/rag-qa--para--rag-ica.md` para corregir el 404 antes de validaciones `--online`.
