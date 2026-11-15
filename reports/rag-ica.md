# RAG de Ica — Carril rag-ica (Ronda 7)

## Estado actual (16:05)

| Métrica | Valor |
|---|---|
| Documentos válidos | 58 |
| Español | 47 |
| Inglés | 11 |
| URLs únicas | 28 |
| Editores únicos | 47 |
| Temas cubiertos | 12/12 |
| Validación | ✅ Verde (0 errores) |

## Temas cubiertos (≥3 docs cada uno)

| # | Tema | Docs |
|---|---|---|
| 1 | Ubicación, altitud, relieve, cuenca | 3 (3 es) |
| 2 | Temperatura: medias, máx, mín por estación | 5 (4 es, 1 en) |
| 3 | Lluvia: estacionalidad, totales, garúa, años secos | 5 (4 es, 1 en) |
| 4 | Extremos: huaicos, inundaciones | 6 (5 es, 1 en) |
| 5 | El Niño y La Niña: 2017, 2023-24 | 5 (4 es, 1 en) |
| 6 | Agua: acuífero, río Ica, Choclococha | 4 (4 es) |
| 7 | Agricultura: agroexportación, vid, aceituna | 9 (9 es) |
| 8 | Aire y radiación: Paracas, UV, polvo | 5 (4 es, 1 en) |
| 9 | Suelo y vegetación: NDVI MODIS, uso suelo | 4 (3 es, 1 en) |
| 10 | Tendencias ya publicadas | 6 (5 es, 1 en) |
| 11 | Estaciones SENAMHI: San Camilo, La Achirana | 3 (3 es) |
| 12 | Población expuesta y sectores afectados | 4 (3 es, 1 en) |

## Fuentes principales

- **NASA POWER** — Temperatura T2M, precipitación PRECTOTCORR, radiación solar, GWETTOP, NDVI MODIS
- **SENAMHI DZ 5 Ica** — Normales térmicas 1991-2020, precipitación decadal MIDAS, pronósticos caudales, clima
- **ANA / PETACC** — Caudal río Ica La Achirana 1922-2013, acuífero sobreexplotación 1.4m/año
- **MIDAGRI** — Perfil productivo 2024: uva 534kt (53% nacional), espárrago 171kt (48%), palta 105kt (4th), arándano +88%
- **MINCETUR Ica** — Exportaciones 2023: US$2,038M NT, destinos EE.UU.46%/UE31%/China8%
- **OECD** — Macro-agroexportación Ica 3% PBI / 7% exportaciones, Choclococha, acuífero déficit 52.17 hm³/año
- **INDECI** — 69 puntos críticos huaicos/Ica, 2017: 1149 afectados/23783 damnificados/3 muertos
- **PUCP** — Tesis huaicos Cansas 1998, 80000 personas expuestas, gestión agua Ica-Pampas
- **INEI** — Censo 2017: 893292 hab, provincias, etnicidad
- **IMARPE / Atmospheric Chemistry and Physics** — Vientos Paracas 10-15 m/s, tormentas polvo, fuentes MODIS
- **ENFEN / IGP / SENAMHI** — Escenarios El Niño 2023-24, prob 77% persistencia, magnitud fuerte-moderada
- **CENEPRED / SIGRID** — Puntos críticos inundación/flujo detritos Ica 2021
- **UP / UPC** — Balance hídrico 79.89 MMC déficit mensual, índices confiabilidad 89.45%/75.31%
- **PLOS ONE** — Impacto El Niño 2017: 1.9M afectados, 169 muertos, US$4016M daños

## Commit

- `b54be15` → `rag/ica` (pushed)
- `b54be15` → `integracion/ronda7` (pushed)

## Próximos pasos

- Reforzar T9 suelo-vegetación con más docs NASA/INDECOPI si necesario
- Reforzar T6 agua con INAIGEM si se encuentran docs de acuífero/sistema Choclococha
- Preparar documento cruzado `<ciudad>-por-<carril>.jsonl` si encuentro datos mejores para Lima o Ayacucho
