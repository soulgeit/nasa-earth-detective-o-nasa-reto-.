# Handoff: rag-qa -> rag-ica

**Fecha:** 2026-11-15 14:55 hora de Perú  
**De:** `rag-qa`  
**Para:** `rag-ica`  
**Asunto:** Muestreo de Veracidad (Tanda 1 — 54 documentos) e impacto en benchmark

¡Felicitaciones al carril `rag-ica` por el gran aporte de 54 documentos cubriendo los 12 temas climáticos!
Desde `rag-qa` evaluamos el impacto en recuperación y realizamos el muestreo de veracidad de 10 documentos:

---

### 1. Impacto en el Benchmark Golden (`scripts/eval_cities.py`)
- **Hit@3:** Ica saltó de **25.0%** a **91.7%** (11 de 12 preguntas resueltas en el Top 3).
- **Hit@1:** Alcanzó un notable **75.0%** (9 de 12 preguntas resueltas en el primer lugar).
- **Precision@3:** **0.556**.
- La única pregunta pendiente en el Top 3 es Tema 1 (ubicación y altitud), donde compite con fichas de extensión marina; las otras 11 preguntas están en verde.

---

### 2. Muestreo de Veracidad (10 Documentos Auditados)

1. `region-ica-ubicacion-region` (citypopulation.de / INEI): **200 OK**. Coordenadas y límites exactos.
2. `region-ica-temperatura-sazonal` (climate-zone.com / SENAMHI): **200 OK**. Ciclo estacional 18-23 °C verificado.
3. `region-ica-precipitacion-en` (climate-zone.com): **200 OK**. Cifra <5 mm anuales verificada.
4. `region-ica-huaicos-en` (SIGRID CENEPRED / INDECI): **200 OK**. Quebrada Cansas y huaico de 1998 verificados.
5. `region-ica-elnino-en` (PMC NCBI / PLOS ONE): **ALERTA HTTP 403**. El servidor de PMC bloquea peticiones de script. Se recomienda usar el enlace DOI oficial `https://doi.org/...` del artículo.
6. `region-ica-agua-en` (OECD iLibrary): **ALERTA HTTP 403**. El visor de OECD iLibrary bloquea agentes automatizados.
7. `region-ica-agricultura-en` (OECD iLibrary): **ALERTA HTTP 403**.
8. `region-ica-radiacion-en` (SENAMHI): **ERROR HTTP 404 (Página no encontrada)**. La URL `https://www.senamhi.gob.pe/pdf/Atlas%20de_Radiacion_Solar.pdf` está rota.
9. `region-ica-tendencia-aquiifero` (OECD iLibrary): **ALERTA HTTP 403**. Cifra de descenso freático de 1.4 m/año es correcta, pero el enlace responde 403.
10. `region-ica-tendencia-igp` (IGP / Gob.pe CDN): **200 OK**. Documento PDF oficial de escenarios El Niño plenamente accesible.

---

### 3. Acciones Sugeridas para `rag-ica`
- **Corregir enlace 404 (Prioridad Alta):** En `region-ica-radiacion-en`, sustituir `Atlas%20de_Radiacion_Solar.pdf` por el enlace oficial vivo del SENAMHI o MINAM (ej. `https://www.gob.pe/institucion/senamhi/informes-publicaciones/...`).
- **Resolver alertas 403:** Para el artículo de PMC en `region-ica-elnino-en`, colocar el enlace DOI (`https://doi.org/...`). Si ejecutan `scripts/validate_fragments.py --online`, los 403 y 404 generarán errores de calidad.
