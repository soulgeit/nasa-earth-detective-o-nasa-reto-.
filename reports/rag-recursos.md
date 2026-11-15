<!-- ESTADO:INICIO -->
## ESTADO — rag-recursos — 2026-11-15 14:52 hora de Perú
Rama@commit: rag/recursos@9692ef1 · empujado: si
VERIFICADO: python scripts/validate_fragments.py → OK: 42 document(s) valid in 2 fragment file(s) (21 es, 21 en, 21 urls)
VERIFICADO: pytest tests/detective/test_fragments.py → 6 passed
VERIFICADO: python -c "from src.detective import corpus; docs = corpus.load_corpus(); print(len(docs))" → 268 documentos, 0 fragment errors
ESCRITO: 42 documentos (26 en platforms.jsonl cubriendo los 13 recursos oficiales de §8 en es/en; 16 en methods.jsonl con notas de método para estudiantes con fuentes primarias)
ROTO / NO HECHO: ninguno; Hito de las 16:30 (§7 y §8) cumplido anticipadamente al 100%
Siguiente paso: Monitorización de integracion/ronda7 y soporte a otros carriles si requieren referencias
Necesito de: arquitecto: nada
Avisos para otros carriles: data/knowledge/resources/platforms.jsonl y methods.jsonl disponibles en integracion/ronda7; ntrs-20090042747 y csa-swot-mission superados con supersedes limpios
<!-- ESTADO:FIN -->

# Reporte Carril RAG Recursos (Ronda 7 — Huiracocha IA)

## Resumen Ejecutivo

El carril **rag-recursos** ha completado la cobertura íntegra exigida en los apartados §5 y §8 de `docs/RONDA_7.md`:
1. **13 Recursos Oficiales del Reto (§8)** convertidos en 26 documentos bilingües (13 en español, 13 en inglés) en `data/knowledge/resources/platforms.jsonl`, detallando qué ofrece cada portal, qué variables y resolución espacial/temporal maneja, cómo se extrae una serie temporal y qué requisitos de acceso exige (cuenta Earthdata, token API o acceso libre).
2. **8 Notas de Método Estadístico para Estudiantes** convertidas en 16 documentos bilingües (8 en español, 8 en inglés) en `data/knowledge/resources/methods.jsonl`, con definiciones claras para estudiantes de secundaria y universidad, cada una respaldada por fuentes primarias abiertas de primer nivel (USGS, NOAA, WMO/OMM, IPCC, ASA).
3. **Mapeo de Supersedes**:
   - `ntrs-20090042747`: superado por `res-platforms-ntrs-acker2009-es` con análisis metodológico completo del PDF de Acker et al. (2009) y variables hidrológicas (`PRECTOTCORR`, `GLDAS_RUNOFF`).
   - `csa-swot-mission`: superado por `res-platforms-csa-swot-es` con documentación técnica de la misión SWOT, radar KaRIn y variables (`GLDAS_RUNOFF`, `EVLAND`, `GWETTOP`).
4. **Cumplimiento de Derechos de Autor**: Los artículos de terceros con copyright (Medium por Kriss y Statsig) fueron sintetizados con resúmenes propios originales (`is_quotation: false`, `summary_by: "rag-recursos"`).
5. **Validación Estricta**: 100% superado en `python scripts/validate_fragments.py` y `pytest tests/detective/test_fragments.py` (0 fragment errors en `corpus.load_corpus()`).

---

## 1. Inventario de Documentos de Recursos Oficiales (`platforms.jsonl`)

Total: 26 documentos (13 español, 13 inglés).

| Recurso Oficial (§8) | ID Español / Inglés | Tipo | Variables Catálogo | Acceso / Requisitos |
|---|---|---|---|---|
| 1. NASA Giovanni | `res-platforms-giovanni-es`<br>`res-platforms-giovanni-en` | `nasa_article` | `T2M`, `PRECTOTCORR`, `AOD_55`, `CLOUD_AMT` | Abierto en web; Earthdata Login para descargas completas |
| 2. NASA GES DISC Hydrology Time Series | `res-platforms-hydrology-time-series-es`<br>`res-platforms-hydrology-time-series-en` | `nasa_article` | `GLDAS_SOILM_0_10`, `GLDAS_EVAP`, `GLDAS_RUNOFF`, `GWETTOP`, `EVLAND` | Libre consulta; Earthdata Login para API/subsetting |
| 3. NASA AppEEARS | `res-platforms-appeears-es`<br>`res-platforms-appeears-en` | `nasa_article` | `MODIS_NDVI`, `MODIS_LST_DAY`, `TS`, `GWETTOP` | Requiere cuenta gratuita Earthdata Login |
| 4. NOAA Climate Data Online (CDO) | `res-platforms-noaa-cdo-es`<br>`res-platforms-noaa-cdo-en` | `nasa_article` | `T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `SNODP` | Libre en web; Token gratuito por email para API REST |
| 5. NASA NTRS Acker et al. 2009 PDF | `res-platforms-ntrs-acker2009-es`<br>`res-platforms-ntrs-acker2009-en` | `paper_abstract` | `PRECTOTCORR`, `GLDAS_RUNOFF` | Dominio público NASA (PDF descargable sin login) |
| 6. KNMI Climate Explorer | `res-platforms-climexp-knmi-es`<br>`res-platforms-climexp-knmi-en` | `method_note` | `T2M`, `PRECTOTCORR`, `GISTEMP_TANOM`, `PS` | Acceso científico libre sin registro |
| 7. Medium: Statistical test methods (Kriss) | `res-platforms-snpkriss-trend-methods-es`<br>`res-platforms-snpkriss-trend-methods-en` | `method_note` | `[]` | Resumen propio (`summary_by: "rag-recursos"`) |
| 8. Statsig: Guide to Statistical Significance | `res-platforms-statsig-significance-guide-es`<br>`res-platforms-statsig-significance-guide-en` | `method_note` | `[]` | Resumen propio (`summary_by: "rag-recursos"`) |
| 9. CSA RADARSAT Constellation (RCM) | `res-platforms-csa-rcm-es`<br>`res-platforms-csa-rcm-en` | `nasa_article` | `GWETTOP`, `SEAICE_EXTENT_N`, `SNODP` | Licencia de Gobierno Abierto Canadá; EODMS libre |
| 10. Geo.ca Plataforma Geoespacial | `res-platforms-geoca-es`<br>`res-platforms-geoca-en` | `method_note` | `GWETTOP`, `MODIS_NDVI`, `GLDAS_RUNOFF` | Licencia de Gobierno Abierto Canadá; libre sin login |
| 11. CSA Misión SWOT | `res-platforms-csa-swot-es`<br>`res-platforms-csa-swot-en` | `nasa_article` | `GLDAS_RUNOFF`, `EVLAND`, `GWETTOP` | Acceso abierto vía NASA PO.DAAC y CNES AVISO+ |
| 12. CSA Monitoreo de Ecosistemas | `res-platforms-csa-ecosystems-space-es`<br>`res-platforms-csa-ecosystems-space-en` | `nasa_article` | `MODIS_NDVI`, `GWETTOP`, `T2M` | Abierto con atribución informativa |
| 13. CSA Tutorial SAR en Python | `res-platforms-csa-sar-tutorial-es`<br>`res-platforms-csa-sar-tutorial-en` | `method_note` | `GWETTOP`, `GLDAS_RUNOFF` | Código abierto (Licencia MIT en GitHub) |

---

## 2. Inventario de Notas de Método Estadístico para Estudiantes (`methods.jsonl`)

Total: 16 documentos (8 español, 8 inglés).

| Concepto de Método | ID Español / Inglés | Concepto Explicado | Fuente Primaria Abierta |
|---|---|---|---|
| 1. Tendencia secular | `res-methods-tendencia-secular-es`<br>`res-methods-secular-trend-en` | Cambio sostenido a largo plazo vs variabilidad interanual (El Niño/La Niña); normales de 30 años | NOAA NCEI / WMO Climate Guidelines (WMO-No. 1203) |
| 2. Test de Mann-Kendall | `res-methods-test-mann-kendall-es`<br>`res-methods-mann-kendall-test-en` | Test no paramétrico basado en rangos para tendencias monótonas; robustez ante outliers | USGS Techniques and Methods / Helsel et al. (2020) |
| 3. Pendiente de Theil-Sen | `res-methods-pendiente-theil-sen-es`<br>`res-methods-theil-sen-slope-en` | Mediana de todas las pendientes entre pares de puntos; punto de ruptura del 29% | USGS TWRI Book 4, Chap A3 / Helsel & Hirsch (2002) |
| 4. Valor p y significancia | `res-methods-valor-p-significancia-es`<br>`res-methods-p-value-significance-en` | Probabilidad bajo la hipótesis nula ($H_0$); regla $p < 0.05$; significancia vs tamaño de efecto | American Statistical Association (ASA) / NOAA Climate.gov |
| 5. Intervalo de confianza | `res-methods-intervalo-confianza-es`<br>`res-methods-confidence-interval-en` | Rango de incertidumbre al 95%; regla visual de no cruzar el cero para confirmar tendencia | IPCC AR5/AR6 Uncertainty Guidance / WMO Guidelines |
| 6. Autocorrelación temporal | `res-methods-autocorrelacion-persistencia-es`<br>`res-methods-autocorrelation-persistence-en` | Persistencia y memoria climática (lag-1); falsos positivos en Mann-Kendall y preblanqueamiento | WMO Guide to Climatological Practices (WMO-No. 100) / USGS |
| 7. Estacionalidad | `res-methods-estacionalidad-desestacionalizacion-es`<br>`res-methods-seasonality-deseasonalization-en` | Ciclo anual regular vs tendencia secular; cálculo de anomalías mensuales respecto a normales | NOAA NCEI / WMO Guidelines on Climatological Normals |
| 8. No significativo $\neq$ no cambia | `res-methods-no-significativo-no-es-sin-cambio-es`<br>`res-methods-not-significant-not-no-change-en` | Ausencia de evidencia no es evidencia de ausencia; tamaño de muestra, ruido y variabilidad | American Statistical Association (ASA) / USGS Guidelines |

---

## 3. Verificación Técnica de Fragmentos y Suite de Pruebas

### Ejecución de `scripts/validate_fragments.py`:
```
fragment                            docs   es   en  urls quotes
resources/methods.jsonl               16    8    8     8      0
resources/platforms.jsonl             26   13   13    13      0

OK: 42 document(s) valid in 2 fragment file(s).
```

### Ejecución de `tests/detective/test_fragments.py`:
```
etd-rag-recursos\tests\detective\test_fragments.py ......                [100%]
6 passed
```

### Carga del corpus en memoria (`src.detective.corpus.load_corpus()`):
```
Total docs loaded: 268
Fragment errors: []
Resources docs loaded: 42
ntrs-20090042747 in docs: False (superseded by res-platforms-ntrs-acker2009-es)
csa-swot-mission in docs: False (superseded by res-platforms-csa-swot-es)
```

---

## 4. Estado de Cumplimiento de Metas

- **Hito 16:30 (§7 y §8)**: Superado al 100% con las 13 fuentes del reto cubiertas en español e inglés, más las 8 notas metodológicas completas.
- **Sin colisiones**: Únicamente se crearon archivos en `data/knowledge/resources/` y el reporte propio `reports/rag-recursos.md`.
- **Integridad del repositorio**: Cero modificaciones a archivos de otros carriles ni a `docs.jsonl`.
