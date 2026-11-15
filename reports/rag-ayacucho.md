<!-- ESTADO:INICIO -->
## ESTADO — rag-ayacucho — 2026-11-15 15:50 hora de Perú
Rama@commit: rag/ayacucho@4129374 · empujado: si
VERIFICADO: validate_fragments.py regions/ayacucho → OK: 63 document(s) valid in 1 fragment file(s) (40 es, 23 en, 35 urls)
VERIFICADO: eval_cities.py --city ayacucho → 12/12 preguntas Hit@3 (100.0%), Hit@1: 58.3%
VERIFICADO: pytest tests/detective/test_fragments.py → 6 passed in 0.29s
ESCRITO (sin ejecutar de punta a punta): ninguno
ROTO / NO HECHO: ninguno; Hitos superados holgadamente (63/50 docs), recursos del reto §8 integrados para Ayacucho
Siguiente paso: Congelación y soporte QA
Necesito de: arquitecto: nada por ahora
Avisos para otros carriles: carril rag-ayacucho incorpora 63 docs oficiales (40 ES, 23 EN, 35 URLs únicas) integrando datos de NASA Giovanni, AppEEARS, GLDAS Hydrology, SWOT, NOAA NCEI y KNMI.
<!-- ESTADO:FIN -->

# Reporte de avance y cierre — carril rag-ayacucho

## Tanda 1 — VERIFICADO (2026-11-15 14:35)
Rama@commit: integracion/ronda7@1883e2b
Qué quedó: 16 documentos iniciales válidos para Ayacucho en data/knowledge/regions/ayacucho.jsonl (8 es, 8 en, 8 URLs de 5 instituciones oficiales: SENAMHI, ANA, INAIGEM, CENEPRED, INEI).
Evidencia:
  - python scripts/validate_fragments.py regions/ayacucho → OK: 16 document(s) valid in 1 fragment file(s).
  - python -m pytest tests/detective/test_fragments.py -q → 6 passed

## Tanda 2 — VERIFICADO (2026-11-15 15:32)
Rama@commit: integracion/ronda7@0d81d5c
Qué quedó: 36 documentos válidos acumulados en data/knowledge/regions/ayacucho.jsonl (24 español, 12 inglés, 20 URLs únicas de 10 instituciones y publicaciones). Hito de 35 documentos superado.
Evidencia:
  - python scripts/validate_fragments.py regions/ayacucho → OK: 36 document(s) valid in 1 fragment file(s).
  - python -m pytest tests/detective/test_fragments.py -q → 6 passed

## Tanda 3 (Misión Completa y Recursos §8) — VERIFICADO (2026-11-15 15:50)
Rama@commit: rag/ayacucho@4129374
Qué quedó: 63 documentos válidos en data/knowledge/regions/ayacucho.jsonl (40 español, 23 inglés, 35 URLs oficiales y científicas de más de 14 instituciones: SENAMHI, ANA, INAIGEM, CENEPRED, INEI, MIDAGRI, MINAM, ENFEN, NASA POWER, NASA GES DISC Giovanni, NASA Earthdata AppEEARS, NASA/CSA SWOT, NOAA NCEI CDO, KNMI Climate Explorer, IPCC, MDPI Water con DOI, FAO, SUNASS).
- Cobertura exhaustiva de los 12 temas de docs/RONDA_7.md §4 (mínimo 3 docs por tema; tema 10 con 11 documentos).
- Integración directa para Ayacucho de los recursos del reto de §8 (NASA Giovanni GPM IMERG, GES DISC Hydrology GLDAS, AppEEARS MODIS NDVI/LST, NOAA NCEI GHCN, SWOT radar altimetry, KNMI ENSO teleconnections).
- Rendimiento en evaluación RAG (scripts/eval_cities.py --city ayacucho): **Hit@3 = 100.0% (12/12 preguntas)**, Hit@1 = 58.3%, Precision@3 = 0.500.
Evidencia:
  - python scripts/validate_fragments.py regions/ayacucho → OK: 63 document(s) valid in 1 fragment file(s).
  - python scripts/eval_cities.py --city ayacucho → Hit@3: 12 (100.0%)
  - python -m pytest tests/detective/test_fragments.py -q → 6 passed in 0.29s
Falta / riesgos: Ninguno. Corpus completo listo para congelación.
