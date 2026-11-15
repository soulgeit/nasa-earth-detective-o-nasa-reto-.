# RAG de Ica — Carril rag-ica (Ronda 7)

## Estado actual (15:30)

| Métrica | Valor |
|---|---|
| Documentos válidos | 54 |
| Español | 43 |
| Inglés | 11 |
| URLs únicas | 26 |
| Instituciones | 10+ (NASA, ANA, OECD, INDECI, SENAMHI, PUCP, INEI, IMARPE, ENFEN, CENEPRED, UP, UNALM, atmospheric-chemistry) |
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
| 6 | Agua: acuífero, río Ica, Choclococha | 5 (4 es, 1 en) |
| 7 | Agricultura: agroexportación, vid, aceituna | 5 (5 es) |
| 8 | Aire y radiación: Paracas, UV, polvo | 5 (4 es, 1 en) |
| 9 | Suelo y vegetación: NDVI MODIS, uso suelo | 4 (3 es, 1 en) |
| 10 | Tendencias ya publicadas | 6 (5 es, 1 en) |
| 11 | Estaciones SENAMHI: San Camilo, La Achirana | 3 (3 es) |
| 12 | Población expuesta y sectores afectados | 4 (3 es, 1 en) |

## Fuentes principales

- **NASA POWER** — Temperatura T2M, precipitación PRECTOTCORR, radiación solar, GWETTOP, NDVI MODIS (3 docs)
- **SENAMHI DZ 5 Ica** — Normales térmicas 1991-2020, precipitación decadal MIDAS, pronósticos caudales, clima (4 docs)
- **ANA / PETACC** — Caudal río Ica La Achirana 1922-2013, acuífero sobreexplotación 1.4m/año (3 docs)
- **OECD** — Macro-agroexportación Ica 3% PBI / 7% exportaciones, Choclococha, acuífero déficit 52.17 hm³/año (2 docs)
- **INDECI** — 69 puntos críticos huaicos/Ica, 2017: 1149 afectados/23783 damnificados/3 muertos (3 docs)
- **PUCP** — Tesis huaicos Cansas 1998, 80000 personas expuestas, gestión agua Ica-Pampas (3 docs)
- **INEI** — Censo 2017: 893292 hab, provincias, etnicidad (1 doc)
- **IMARPE / Atmospheric Chemistry and Physics** — Vientos Paracas 10-15 m/s, tormentas polvo, fuentes MODIS (2 docs)
- **ENFEN / IGP / SENAMHI** — Escenarios El Niño 2023-24, prob 77% persistencia, magnitud fuerte-moderada (2 docs)
- **CENEPRED / SIGRID** — Puntos críticos inundación/flujo detritos Ica 2021 (1 doc)
- **UP / UPC** — Balance hídrico 79.89 MMC déficit mensual, índices confiabilidad 89.45%/75.31% (2 docs)
- **PLOS ONE** — Impacto El Niño 2017: 1.9M afectados, 169 muertos, US$4016M daños (2 docs)

## Documentos clave por tema

- **Acuífero**: descenso 1.4m/ano (Ica), 1.5m (Villacurí), 1.85m (Lanchas); déficit 52.17 hm³/ano (ANA)
- **Caudal**: estación La Achirana, 92 años (1922-2013), media 9.86 m³/s, extremo húmedo 17.43 (1933), extremo seco 0.15 (1992)
- **El Niño 2017**: 3er más intenso siglo XXI; TSM Puerto Chicama 17→26.9°C; 169 muertos, 194000 desplazados
- **El Niño 2023-24**: Alerta 77%; prob 82% verano 2024; 37 distritos emergencia Ica; 69 puntos críticos
- **Vientos Paracas**: 4-5/año, >10-15 m/s, tormentas polvo 60-100 µm desde Pampa Villacurí
- **Huaicos Cansas**: 1998: 600 m³/s; 80000 personas en conos aluviales; rocas 40 toneladas

## Commit

- `73b3ad3` → `rag/ica` (pushed)
- `73b3ad3` → `integracion/ronda7` (pushed)

## Próximos pasos

- 16:30: reforzar temas 9, 11, 12 con documentos adicionales si es necesario
- Revisar handoff de otros carriles si aplica
- Preparar refuerzos cruzados `<ciudad>-por-<carril>.jsonl`
