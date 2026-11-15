<!-- ESTADO:INICIO -->
## ESTADO — rag-ayacucho — 2026-11-15 15:40 hora de Perú
Rama@commit: rag/ayacucho@2e5c527 · empujado: si
VERIFICADO: validate_fragments.py regions/ayacucho → OK: 57 document(s) valid in 1 fragment file(s) (37 es, 20 en, 29 urls)
VERIFICADO: eval_cities.py --city ayacucho → 12/12 preguntas Hit@3 (100.0%), Hit@1: 58.3%
VERIFICADO: pytest tests/detective/test_fragments.py → 6 passed in 0.27s
ESCRITO (sin ejecutar de punta a punta): ninguno
ROTO / NO HECHO: ninguno; MISIÓN COMPLETADA con antelación a las metas de 16:30 y 17:30
Siguiente paso: Congelación y soporte QA
Necesito de: arquitecto: nada por ahora
Avisos para otros carriles: carril rag-ayacucho completa su misión con 57 docs oficiales (37 ES, 20 EN, 29 URLs) cubriendo al 100% los 12 temas de §4.
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

## Tanda 3 (Misión Completa) — VERIFICADO (2026-11-15 15:40)
Rama@commit: rag/ayacucho@2e5c527
Qué quedó: 57 documentos válidos en data/knowledge/regions/ayacucho.jsonl (37 español, 20 inglés, 29 URLs oficiales y científicas de más de 12 instituciones: SENAMHI, ANA, INAIGEM, CENEPRED, INEI, MIDAGRI, MINAM, ENFEN, NASA POWER, NASA Earth Observatory, IPCC, MDPI Water con DOI, FAO, SUNASS).
- Cobertura exhaustiva de los 12 temas de docs/RONDA_7.md §4 (mínimo 3 docs por tema; tema 10 con 11 documentos).
- Rendimiento en evaluación RAG (scripts/eval_cities.py --city ayacucho): **Hit@3 = 100.0% (12/12 preguntas)**, Hit@1 = 58.3%, Precision@3 = 0.583.
Evidencia:
  - python scripts/validate_fragments.py regions/ayacucho → OK: 57 document(s) valid in 1 fragment file(s).
  - python scripts/eval_cities.py --city ayacucho → Hit@3: 12 (100.0%)
  - python -m pytest tests/detective/test_fragments.py -q → 6 passed in 0.27s
Falta / riesgos: Ninguno. Corpus completo listo para congelación.
