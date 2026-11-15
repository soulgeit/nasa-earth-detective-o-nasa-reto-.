<!-- ESTADO:INICIO -->
## ESTADO — rag-ayacucho — 2026-11-15 14:35 hora de Perú
Rama@commit: rag/ayacucho@adf9de4 · empujado: si
VERIFICADO: validate_fragments.py regions/ayacucho → OK: 16 document(s) valid in 1 fragment file(s)
ESCRITO (sin ejecutar de punta a punta): ninguno
ROTO / NO HECHO: ninguno
Siguiente paso: Tanda 2 (alcanzar >= 35 documentos cubriendo temas 5, 7, 8, 9 y reforzando 10)
Necesito de: arquitecto: nada por ahora
Avisos para otros carriles: carril rag-ayacucho arrancó tanda 1 con 16 docs oficiales (SENAMHI, ANA, INAIGEM, CENEPRED, INEI).
<!-- ESTADO:FIN -->

# Reporte de avance — carril rag-ayacucho

## Tanda 1 — VERIFICADO (2026-11-15 14:35)
Rama@commit: rag/ayacucho@adf9de4
Qué quedó: 16 documentos iniciales válidos para Ayacucho en data/knowledge/regions/ayacucho.jsonl (8 en español, 8 en inglés, 8 URLs de 5 instituciones oficiales: SENAMHI, ANA, INAIGEM, CENEPRED, INEI). Cubre temas 1, 2, 3, 4, 6, 10, 11, 12.
Evidencia:
  - python scripts/validate_fragments.py regions/ayacucho → OK: 16 document(s) valid in 1 fragment file(s).
  - python -m pytest tests/detective/test_fragments.py -q → 6 passed in 0.21s
Falta / riesgos: Expandir hacia Tanda 2 (35 documentos a las 16:30) y Tanda 3 (50 documentos a las 17:30) cubriendo los 12 temas de §4.
Necesito de otros: ninguno.
