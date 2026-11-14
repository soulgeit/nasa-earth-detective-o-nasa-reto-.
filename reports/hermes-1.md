# Reportes de Hermes 1

## C1 — LISTO  (2026-11-14 16:20 UTC-5)
Rama@commit: feature/catalog (pendiente de commit)
Qué quedó:
- `data/catalog/variables.json`: 15 variables live (12 POWER + GISTEMP + 2 NSIDC), esquema contrato §8, sin cambiar ningún id de la semilla.
  - Nombres, definición simple (≤30 palabras), qué significa subir/bajar, conductores típicos y avisos, en ES y EN.
  - `source` verificado contra el **diccionario oficial de parámetros de POWER** y sus páginas de metodología:
    - MERRA-2 y resolución nativa ½°×⅝° para las meteorológicas.
    - Empalme de radiación confirmado: GEWEX SRB 1984–2000 → CERES SYN1deg 2001+ → `homogeneous_since: "2001-01"` en CLOUD_AMT y ALLSKY_SFC_SW_DWN.
    - AOD_55: CERES SYN1deg, empieza en 2001-01.
    - GISTEMP: doi 10.1029/2023JD040179 (Lenssen et al. 2024). NSIDC: doi 10.7265/a98x-0f50 (Sea Ice Index v4).
  - Los 15 DOI/URL no nulos responden (comprobado en `validate_knowledge.py`).
- `scripts/hermes1/build_catalog.py` reconstruye el catálogo desde cero con las fuentes reales.

## C2 — LISTO  (2026-11-14 16:20 UTC-5)
Rama@commit: feature/catalog
Qué quedó:
- `data/catalog/gazetteer.json`: **8 109 ciudades** (8 000 más pobladas + **140 de Perú**), campos del contrato. Fuente GeoNames cities15000, licencia CC BY 4.0 citada.
- `data/catalog/regions.json`: **67 regiones naturales** con nombre ES/EN, centro, bioma y caja.
  - 67 centros verificados en Wikidata (P625); 19 cajas desde los extremos N/S/E/W de Wikidata o desde Nominatim cuando coincide con el centro.
  - Las regiones sin caja verificable quedan con `bbox: null` y se listan en el log; no se inventó ninguna.

## C3 — LISTO  (2026-11-14 16:20 UTC-5)
Rama@commit: feature/catalog
Qué quedó: `data/knowledge/docs.jsonl` con **166 documentos**, esquema §9, cada uno con URL final, título, fecha si figura, `fetched_at` y `sha256` del HTML descargado.
- `variable_card`: 30 (15 variables × 2 idiomas), generadas desde el catálogo.
- `biome_profile`: 16 (8 biomas × 2 idiomas), redactados a partir de las páginas de NASA Earth Observatory que se citan.
- `nasa_article`: 34, **28 sobre Perú/LatAm** (mínimo 6), texto extraído del artículo real.
- `paper_abstract`: 10; resumen de Crossref cuando existe; si no, 2+ frases propias marcadas `summary_by: "hermes-1"` + DOI.
- `method_note`: 12 (6 temas × 2 idiomas) con sus URLs.
- `glossary`: 64 (32 términos × 2 idiomas) desde el Glossary of Meteorology de la AMS.
- Caché de HTML crudo en `data/cache/knowledge/raw/` (ignorada por git) para reauditar cualquier documento.

## C4 — LISTO  (2026-11-14 16:20 UTC-5)
Rama@commit: feature/catalog
Qué quedó: `scripts/validate_knowledge.py`.
- Catálogo: todos los ids de la semilla; ambos idiomas; definiciones no vacías; keywords ≥ 8; DOI y URL comprobados.
- Corpus: campos obligatorios; URL 200; título presente en la página (artículos y papers); longitud 300–1200; sin duplicados; sha256 presente; cuotas mínimas por tipo.
- Sale con código ≠ 0 si algo falla.
Evidencia:
```bash
$ python scripts/validate_knowledge.py
catalog variables: 15
corpus documents: 166
  biome_profile    16
  glossary         64
  method_note      12
  nasa_article     34
  paper_abstract   10
  variable_card    30

All checks passed.
```
Prueba con documento roto a propósito (URL 404, sha vacío, texto corto):
```bash
  - doc var-t2m-es: text length 5 outside 300-1200
  - doc var-t2m-es: sha256 missing or malformed
  - corpus: URL not 200 (404) https://science.nasa.gov/this-page-does-not-exist-404-test/
3 failure(s)
```
Falta / riesgos:
- 122 documentos no tienen fecha porque la página no la publica (no se inventó).
- 3 artículos de NASA no tienen bioma asignado (menciones genéricas).
Necesito de otros: nada bloqueante.

## C5 — LISTO  (2026-11-14 16:20 UTC-5)
`data/knowledge/golden_questions.jsonl`: 50 preguntas (25 ES, 25 EN) con 1–2 variables correctas, escritas antes de ver lo que devuelve el buscador.

## C6 — PENDIENTE (bloqueado por el humano)
No hay CSV en `data/raw/giovanni/`; las tarjetas `planned_giovanni` se completarán cuando el humano deje la primera exportación.

## C7 — LISTO  (2026-11-14 16:20 UTC-5)
`docs/REFERENCES.md` en inglés: fuentes NASA, GeoNames, Wikidata, OpenStreetMap, AMS, referencias metodológicas con DOI y licencias de las herramientas.
