<!-- ESTADO:INICIO -->
## ESTADO — rag-andahuaylas — 2026-11-15 15:01 hora de Perú
Rama@commit: rag/andahuaylas@preparando-tanda3 · empujado: no
VERIFICADO: 50 documentos válidos → python scripts/validate_fragments.py regions/andahuaylas → OK: 50 document(s) valid in 1 fragment file(s)
ESCRITO: data/knowledge/regions/andahuaylas.jsonl (50 docs: 38 es, 12 en, 19 URLs únicas, 16 instituciones, 12 temas cubiertos)
ROTO / NO HECHO: Ninguno. Meta final de §4 de 50 documentos alcanzada antes de las 15:15.
Siguiente paso: Commit de la tanda completa de 50 documentos y sincronización con integracion/ronda7.
Necesito de: arquitecto: nada por ahora.
Avisos para otros carriles: carril rag-andahuaylas ha completado el 100% de los requerimientos de §4 (50 docs, 16 instituciones, 12 temas).
<!-- ESTADO:FIN -->

# Reporte Carril rag-andahuaylas — Ronda 7

## Resumen de Ejecución
- Carpeta de trabajo: `C:\Users\USER41\work\etd-rag-andahuaylas`
- Rama: `rag/andahuaylas`
- Archivo propio de datos: `data/knowledge/regions/andahuaylas.jsonl`
- Archivo de reporte: `reports/rag-andahuaylas.md`

## Cumplimiento de Criterios §4
1. **Mínimo 50 documentos válidos:** ✅ 50 documentos.
2. **Distribución por idioma:** ✅ 38 en español (≥ 35 requerido), 12 en inglés (≥ 10 requerido).
3. **Páginas fuente distintas:** ✅ 19 URLs distintas (≥ 12 requerido).
4. **Instituciones oficiales distintas:** ✅ 16 instituciones (≥ 6 requerido):
   - NASA (NASA POWER / MERRA-2)
   - SENAMHI
   - ANA (Autoridad Nacional del Agua)
   - INAIGEM
   - CENEPRED
   - INEI
   - MIDAGRI
   - SERFOR
   - INDECI
   - INGEMMET
   - MINAM
   - Gobierno Regional de Apurímac
   - Municipalidad Provincial de Andahuaylas
   - IPCC
   - Universidad Nacional José María Arguedas
   - Tecnología y Ciencias del Agua (revista con DOI)
5. **Cobertura de los 12 temas (§4):**
   - Tema 1: Ubicación, altitud, relieve, cuenca (4 docs)
   - Tema 2: Temperatura normal (4 docs)
   - Tema 3: Lluvia y estacionalidad (4 docs)
   - Tema 4: Extremos: heladas, huaicos, granizadas (4 docs)
   - Tema 5: El Niño y sequías locales (4 docs)
   - Tema 6: Agua: Chumbao, Pacucha, manantiales (5 docs)
   - Tema 7: Agricultura: papa nativa, maíz, SAC (4 docs)
   - Tema 8: Aire y radiación UV (4 docs)
   - Tema 9: Suelo, vegetación y expansión urbana (4 docs)
   - Tema 10: Tendencias ya publicadas (SENAMHI, CENEPRED, IPCC, ERCC) (9 docs - requisito ≥ 8 cumplido)
   - Tema 11: Estaciones SENAMHI y celdas satelitales (4 docs)
   - Tema 12: Población expuesta y sectores vulnerables (4 docs)
6. **Pruebas automatizadas:**
   - `python scripts/validate_fragments.py regions/andahuaylas` → VERDE (0 errores)
   - `python -m pytest tests/detective/test_fragments.py -q` → 6 passed (VERDE)

## Necesito de: arquitecto (Feedback del Humano sobre la UI)
1. **Espacio de entrada conversacional:** El cuadro de texto actual para hablar con la IA (#detective-input) en el carril izquierdo es demasiado estrecho y pequeño; el usuario requiere que sea más amplio y con un flujo conversacional más natural (por ejemplo, conectando directamente con el nuevo endpoint /api/ai/chat de la Ronda 7 para responder saludos como «Quetal» o preguntas generales de forma conversacional sin fallar inmediatamente con error de variables).
2. **Nuevo Logo de Huiracocha IA:** El usuario ha facilitado la imagen oficial del sol místico andino/tecnológico con el planeta abajo para colocarla como logo principal de la aplicación. Se ha procesado y guardado en src/ui/huiracocha-logo.png con transparencia (fondo oscuro eliminado) para su integración en el header/masthead.
