<!-- ESTADO:INICIO -->
## ESTADO — rag-datos — 2026-11-15 15:15 hora de Perú
Rama@commit: rag/datos@170314d · empujado: sí (tanda 1)
VERIFICADO: Cálculo de tendencias climáticas y ambientales en proceso mediante `src.api.service.analyze` para las cinco ciudades oficiales de la Ronda 7 (Lima, Huancayo, Andahuaylas, Ica, Ayacucho) a partir de coordenadas exactas del gazetteer.
VERIFICADO: 165 análisis JSON íntegros congelados en `data/cities/<ciudad>/<VARIABLE>.analysis.json` (33 variables disponibles por ciudad, 100% datos reales de NASA POWER y GISTEMP, nada simulado).
VERIFICADO: 340 documentos de hechos generados en `data/knowledge/facts/<ciudad>.jsonl` (68 documentos por ciudad: 33 variables × 2 idiomas [ES/EN] + 2 documentos de resumen «Qué está cambiando en <Ciudad>» ordenados por significancia estadística).
VERIFICADO: Exactitud y trazabilidad de cifras: cada documento incorpora pendiente Theil-Sen, IC al 95%, tau/z/p-value de Mann-Kendall con corrección de autocorrelación serial mensual, periodo, número de observaciones y veredicto con el mismo redondeo publicado por la app.
VERIFICADO: Calidad y pruebas: `scripts/validate_fragments.py` pasa 100% en verde (340/340 documentos válidos). `tests/detective/test_city_facts.py` y `tests/detective/test_fragments.py` ejecutan 9 passed, 0 failed, demostrando que cualquier cifra no presente en el JSON congelado es rechazada.
ROTO / NO HECHO: Variables no entregadas por el proveedor: `SEAICE_EXTENT_N` y `SEAICE_EXTENT_S` (NSIDC responde `ApiError: OUT_OF_COVERAGE` al tratarse de cobertura polar no aplicable a coordenadas peruanas; según §5 se documenta la exclusión y no se inventan datos).
Siguiente paso: Atentos a nuevos `git fetch` por ampliación de variables en el catálogo para re-ejecutar; re-ejecución final a las 18:45 con el catálogo definitivo.
Necesito de: arquitecto: Ninguno. Todo el motor ETL y de análisis estadístico responde de manera determinista y reproducible.
Avisos para otros carriles: `data/knowledge/facts/*.jsonl` listo con 340 documentos de hechos y resúmenes para Lima, Huancayo, Andahuaylas, Ica y Ayacucho.
<!-- ESTADO:FIN -->

# Reporte Carril rag-datos — Ronda 7 (Huiracocha IA)

**Fecha:** 15 de noviembre de 2026 — Tanda 1 (15:15)  
**Carril:** `rag-datos`  
**Rama:** `rag/datos`  
**Archivos propios:**
- `scripts/build_city_facts.py`
- `data/cities/**` (165 archivos `.analysis.json`)
- `data/knowledge/facts/*.jsonl` (5 archivos `.jsonl`, 340 documentos)
- `tests/detective/test_city_facts.py`
- `reports/rag-datos.md`

---

## 1. Misión y Metodología

Conforme a la especificación de la Ronda 7 (§5 «rag-datos»):
- Se calcularon las tendencias climáticas y ambientales mediante llamada directa en proceso a `src.api.service.analyze(variable_id, lat=..., lon=..., place=...)`.
- Se utilizaron datos satelitales reales de NASA POWER (MERRA-2) y NASA GISTEMP v4; **nada simulado ni inventado**.
- Se congeló el resultado íntegro de cada análisis en `data/cities/<ciudad>/<VARIABLE>.analysis.json`.
- Se generaron los documentos de hechos en formato JSON Lines en `data/knowledge/facts/<ciudad>.jsonl` tanto en español (`lang: "es"`) como en inglés (`lang: "en"`), junto con un resumen estructurado «Qué está cambiando en <Ciudad>» que clasifica las variables según su significancia estadística.

---

## 2. Coordenadas Oficiales (Gazetteer)

Las coordenadas empleadas corresponden con precisión matemática al catálogo oficial `data/catalog/gazetteer.json`:

| Ciudad | Latitud | Longitud | Población | Variables Disponibles | Variables Congeladas | Hechos Generados |
|---|---|---|---|---|---|---|
| **Lima** | -12.0432 | -77.0282 | 7,737,002 | 33 | 33 | 68 (34 ES / 34 EN) |
| **Huancayo** | -12.0687 | -75.2103 | 456,250 | 33 | 33 | 68 (34 ES / 34 EN) |
| **Andahuaylas** | -13.6556 | -73.3872 | 17,444 | 33 | 33 | 68 (34 ES / 34 EN) |
| **Ica** | -14.0754 | -75.7342 | 282,407 | 33 | 33 | 68 (34 ES / 34 EN) |
| **Ayacucho** | -13.1638 | -74.2234 | 140,033 | 33 | 33 | 68 (34 ES / 34 EN) |
| **TOTAL** | — | — | — | — | **165** | **340** |

---

## 3. Variables no Entregadas por el Proveedor

De las 35 variables presentes en el catálogo:
- 33 variables fueron consultadas y congeladas exitosamente.
- 2 variables no son entregadas para estos puntos geográficos por limitaciones físicas de cobertura del sensor:
  1. `SEAICE_EXTENT_N`: Extensión de hielo marino ártico (NSIDC). Cobertura restringida al hemisferio norte polar. Error devuelto: `ApiError: OUT_OF_COVERAGE`.
  2. `SEAICE_EXTENT_S`: Extensión de hielo marino antártico (NSIDC). Cobertura restringida a la Antártida. Error devuelto: `ApiError: OUT_OF_COVERAGE`.

Siguiendo el mandato de §5 (*«Una variable que el proveedor no entrega para ese punto se anota en el reporte, no se rellena»*), estas dos variables no se inventaron ni se aproximaron artificialmente.

---

## 4. Estructura de los Documentos de Hechos

Cada documento generado en `data/knowledge/facts/<ciudad>.jsonl` cumple con el contrato estricto de fragmentos (§3):
- **ID unívoco:** `fact-<ciudad>-<variable>-<lang>` y `fact-<ciudad>-summary-<lang>`.
- **Tipo:** `region_note`.
- **Campos obligatorios:** `id`, `type`, `title`, `url`, `publisher`, `lang`, `text`, `variables`, `places`, `license`, `fetched_at`, `sha256`, `is_quotation: false`, `summary_by: "rag-datos"`, `generated_from: "scripts/build_city_facts.py"`.
- **Cifras publicadas:** Pendiente Theil-Sen con unidad por década, intervalo de confianza al 95%, tau y z de Mann-Kendall, valor p con corrección Hamed-Rao por autocorrelación serial mensual, periodo temporal (1981-01 a 2025-12), total de observaciones (540 meses) y veredicto estadístico (`SIGNIFICANT`, `SUGGESTIVE`, `NOT_SIGNIFICANT`).
- **Resumen:** «Qué está cambiando en <Ciudad>» ordena las variables por significancia (significativas primero, luego sugestivas, luego no significativas).

---

## 5. Verificación de Calidad y Tests

1. **Validador de Fragmentos:**
   ```bash
   python scripts/validate_fragments.py --stats
   ```
   **Resultado:**
   ```
   fragment                            docs   es   en  urls quotes
   facts/andahuaylas.jsonl               68   34   34    34      0
   facts/ayacucho.jsonl                  68   34   34    34      0
   facts/huancayo.jsonl                  68   34   34    34      0
   facts/ica.jsonl                       68   34   34    34      0
   facts/lima.jsonl                      68   34   34    34      0

   OK: 340 document(s) valid in 5 fragment file(s).
   ```

2. **Suite de Pruebas Automatizadas:**
   ```bash
   pytest tests/detective/test_city_facts.py tests/detective/test_fragments.py -v
   ```
   **Resultado:**
   `9 passed, 0 failed`
   - `test_every_city_has_frozen_data_and_facts_files`: PASSED
   - `test_fact_numbers_strictly_match_frozen_analysis_json`: PASSED
   - `test_verification_fails_if_number_is_invented`: PASSED
   - `test_fragments_are_loaded_and_a_bad_row_never_breaks_the_corpus`: PASSED
   - `test_a_fragment_can_supersede_an_older_document_without_editing_its_file`: PASSED
   - `test_files_outside_the_three_lanes_are_not_loaded`: PASSED
   - `test_the_gate_rejects_what_the_contract_forbids`: PASSED
   - `test_the_fragments_in_the_repo_pass_the_gate`: PASSED
   - `test_a_short_place_name_is_matched_as_a_word_not_as_a_substring`: PASSED
