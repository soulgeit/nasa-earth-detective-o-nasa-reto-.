# Ronda 7 — QA Informe de Tanda 2 (15:45)

**Fecha y hora:** 2026-11-15 15:45 hora de Perú  
**Carril:** `rag-qa`  
**Rama:** `rag/qa` sobre `integracion/ronda7`  

---

## 1. Estado Global de Fragmentos en el Repositorio
Resultado de `python scripts/validate_fragments.py --stats`:
```
fragment                            docs   es   en  urls quotes
facts/andahuaylas.jsonl               68   34   34    34      0
facts/ayacucho.jsonl                  68   34   34    34      0
facts/huancayo.jsonl                  68   34   34    34      0
facts/ica.jsonl                       68   34   34    34      0
facts/lima.jsonl                      68   34   34    34      0
regions/andahuaylas.jsonl             50   38   12    19      0
regions/ayacucho-por-rag-ayacucho-2.jsonl    58   29   29    20      0
regions/ayacucho.jsonl                36   24   12    20      0
regions/huancayo.jsonl                55   34   21    24      0
regions/ica.jsonl                     69   58   11    35      0
regions/lima.jsonl                    62   42   20    41      0
resources/methods.jsonl               16    8    8     8      0
resources/platforms.jsonl             26   13   13    13      0

OK: 712 document(s) valid in 13 fragment file(s).
```

### Hitos de Volumen Alcanzados:
- **Las 5 ciudades superaron ampliamente el mínimo de 50 documentos:**
  - Lima: 62 regionales + 68 facts = 130 docs.
  - Ica: 69 regionales + 68 facts = 137 docs.
  - Huancayo: 55 regionales + 68 facts = 123 docs.
  - Andahuaylas: 50 regionales + 68 facts = 118 docs.
  - Ayacucho: 94 regionales (36 + 58) + 68 facts = 162 docs.
- **Recursos del reto (§8):** 42 documentos en `resources/` (métodos estadísticos y plataformas).
- **Total acumulado:** **712 documentos válidos**.

---

## 2. Medición de Recuperación RAG Oficial (`scripts/eval_cities.py`)

```
| Ciudad | Preguntas | Hit@1 | Hit@1 % | Hit@3 | Hit@3 % | Precision@3 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lima** | 12 | 3 | 25.0% | 7 | 58.3% | 0.361 |
| **Huancayo** | 12 | 4 | 33.3% | 8 | 66.7% | 0.306 |
| **Andahuaylas** | 12 | 5 | 41.7% | 8 | 66.7% | 0.333 |
| **Ica** | 12 | 4 | 33.3% | 5 | 41.7% | 0.278 |
| **Ayacucho** | 12 | 5 | 41.7% | 12 | 100.0% | 0.500 |
| **TOTAL** | **60** | **21** | **35.0%** | **40** | **66.7%** | **0.356** |
```

### Análisis de Desempeño:
- **Hit@3 Global:** Subió de **11.7%** (línea base) a **66.7%** (40 de 60 preguntas acertadas en el Top 3).
- **Ayacucho:** Rendimiento perfecto en Top 3 (**100.0% Hit@3**, 12/12) gracias al aporte dual de `rag-ayacucho` y `rag-ayacucho-2`.
- **Huancayo y Andahuaylas:** **66.7% Hit@3** cada una, con alta consistencia temática.
- **Hit@1 Global:** 35.0% (21 preguntas devuelven el documento exacto en primer lugar).

---

## 3. Muestreo de Veracidad por Carril (10 Documentos por Carril)

1. **`rag-huancayo` (10 docs):** **10 / 10 OK (HTTP 200)**. CENEPRED, SENAMHI, INAIGEM, MIDAGRI, MINAM, INEI y Elsevier totalmente verificados. Cero enlaces rotos.
2. **`rag-andahuaylas` (10 docs):** **9 / 10 OK (HTTP 200)**. Gob.pe, NASA POWER, CENEPRED, ANA, MINAM, SENAMHI y UNAJMA 200 OK. 1 ReadTimeout en revista mexicana TyCA.
3. **`rag-recursos` (10 docs):** **8 / 10 OK (HTTP 200)**. Portales oficiales de NASA (Giovanni, GES DISC, AppEEARS, NTRS), NOAA NCEI, KNMI, Statsig y Geo.ca plenamente accesibles. Alertas conocidas: Medium (403 anti-bot) y RCM Canadá (SSLError de certificado intermedio).
4. **`rag-ayacucho` (10 docs):** **ALERTA CRÍTICA: 3 OK, 7 HTTP 404**. Enlaces con IDs numéricos presuntamente alucinados en `gob.pe` y SIGRID CENEPRED. Handoff de corrección urgente emitido en `reports/handoff/rag-qa--para--rag-ayacucho.md`.
5. **`rag-ica` (10 docs):** **5 OK, 1 HTTP 404** (Atlas de Radiación Solar de SENAMHI), 4 con 403 (OECD/PMC). Handoff emitido en `reports/handoff/rag-qa--para--rag-ica.md`.
6. **`rag-lima` (10 docs):** **9 OK, 1 alerta HTTP 468** (WAF San Marcos). Handoff emitido en `reports/handoff/rag-qa--para--rag-lima.md`.

---

## 4. Próximos Pasos (Hacia la Congelación de las 18:30)
- Monitorear si `rag-ayacucho` y `rag-ica` subsanan las URLs rotas señaladas en los handoffs.
- A partir de las 18:30, `rag-qa` asumirá la corrección directa o sustitución mediante `supersedes` de todo documento con URL 404 para garantizar la entrega impecable a las 18:45.
