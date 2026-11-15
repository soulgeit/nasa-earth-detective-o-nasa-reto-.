# RAG de Ica — Carril rag-ica (Ronda 7)

## Estado actual (16:35)

| Métrica | Valor |
|---|---|
| Documentos válidos | 64 |
| Español | 53 |
| Inglés | 11 |
| URLs únicas | 33 |
| Editores únicos | 52 |
| Temas cubiertos | 12/12 |
| Validación | ✅ Verde (0 errores) |
| Artículos con DOI | 2 |

## Temas cubiertos (≥3 docs cada uno)

| # | Tema | Docs |
|---|---|---|
| 1 | Ubicación, altitud, relieve, cuenca | 3 |
| 2 | Temperatura: medias, máx, mín por estación | 5 |
| 3 | Lluvia: estacionalidad, totales, garúa, años secos | 5 |
| 4 | Extremos: huaicos, inundaciones | 6 |
| 5 | El Niño y La Niña: 2017, 2023-24 | 5 |
| 6 | Agua: acuífero, río Ica, Choclococha | 7 |
| 7 | Agricultura: agroexportación, vid, aceituna | 9 |
| 8 | Aire y radiación: Paracas, UV, polvo | 5 |
| 9 | Suelo y vegetación: NDVI MODIS, uso suelo | 6 |
| 10 | Tendencias ya publicadas | 6 |
| 11 | Estaciones SENAMHI: San Camilo, La Achirana | 3 |
| 12 | Población expuesta y sectores afectados | 4 |

## Fuentes principales

- **NASA POWER** — Temperatura T2M, precipitación PRECTOTCORR, radiación solar, GWETTOP, NDVI MODIS
- **SENAMHI DZ 5 Ica** — Normales térmicas 1991-2020, precipitación decadal MIDAS, pronósticos caudales
- **ANA / PETACC** — Caudal río Ica La Achirana 1922-2013, acuífero sobreexplotación 1.4m/año
- **MIDAGRI** — Perfil productivo 2024: uva 534kt (53% nacional), espárrago 171kt (48%), palta 105kt
- **MINCETUR Ica** — Exportaciones 2023: US$2,038M NT, destinos EE.UU.46%/UE31%/China8%
- **OECD** — Macro-agroexportación Ica 3% PBI / 7% exportaciones, acuífero déficit 52.17 hm³/año
- **INDECI** — 69 puntos críticos huaicos/Ica, 2017: 1149 afectados/23783 damnificados
- **PUCP** — Tesis huaicos Cansas 1998, 80000 personas expuestas
- **INEI** — Censo 2017: 893292 hab
- **IMARPE** — Vientos Paracas 10-15 m/s, tormentas polvo
- **ENFEN / IGP** — Escenarios El Niño 2023-24, prob 77%
- **CENEPRED / INDECOPI** — Riesgo inundación fluvial nivel 0.289 MUY ALTO
- **Springer** — Cambio uso suelo Ica 1990-2030 (DOI: 10.1186/s12302-025-01181-y)
- **IADB / Springer** — Acuífero Ica: 563.35 hm³ explotación (35% nacional), pozos durarán 5-11 años
- **MDPI Remote Sensing** — Desertificación Sudamérica 27-43% superficie
- **PLOS ONE** — Impacto El Niño 2017: 1.9M afectados, 169 muertos, US$4016M

## Commit

- `366595d` → `rag/ica` (pushed)
- `366595d` → `integracion/ronda7` (pushed)
