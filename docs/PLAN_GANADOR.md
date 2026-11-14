# PLAN GANADOR — EarthTrend Detective (NASA Space Apps 2026)

Escrito el sábado 14-nov-2026, 12:45 (hora de Perú). **Cierre oficial: domingo 15-nov, 23:59 hora local del evento. Entregamos a las 20:00.**
Reglas y contratos: `prompts/00_LEER_PRIMERO.md`, `docs/CONTRATOS.md`. Entrega: `docs/KIT_ENTREGA.md`.

## 1. Diagnóstico del repo (por qué el plan anterior no gana)

El tablero marca casi todo como hecho, pero lo que hay es una maqueta. Con evidencia:

| Hallazgo | Dónde | Por qué importa |
|---|---|---|
| **Los 4 datasets son inventados** (seno + recta + ruido) y están etiquetados como MODIS, SWOT, MERRA-2 y GLDAS | `src/etl/nasa_adapters.py:75-97`, `data/processed/*.json` | Hay una serie «SWOT» de 2000 a 2024 y SWOT se lanzó en dic-2022. Un juez de la NASA lo ve en 10 segundos. Hunde Validez y Relevancia |
| La UI **fabrica la significancia**: `isSig = |pendiente| > 0.001`, `p = 0.00001` fijo, R² «0.82» por defecto | `src/ui/app.js:85`, `:95`, `:149` | Muestra un valor p que nadie calculó, bajo el rótulo «Valor Observado (Satélite)» (`:162`) |
| La API **sustituye en silencio**: si no existe el archivo pedido, analiza «el primero disponible» | `src/api/main.py:103-108` | Cualquier combinación devuelve datos de otra región sin avisar |
| No hay una sola descarga real de la NASA | todo `src/etl/` | El objetivo 2 del reto es «adquirir los datos para una región» |
| Mann-Kendall sin corrección de empates ni de autocorrelación; Theil-Sen submuestreado; OLS sin IC ni prueba t (el documento dice que sí) | `src/stats/trend_engine.py:101`, `:59`, `:129-159` | Con datos mensuales la autocorrelación infla la significancia: casi todo saldría «significativo» |
| «% de cambio» calculado sobre °C | `src/stats/trend_engine.py:188` | Un porcentaje de −7 °C no significa nada |
| Sin mapa, sin regiones libres, sin IA; el «wizard» es un diccionario de 4 opciones | `src/detective/wizard.py` | El reto pide «dónde» y sugiere IA para proponer variables |
| Solo en español; colores y textos «de la NASA» | `src/ui/` | La entrega se juzga en inglés y la regla prohíbe usar la marca NASA en contenido generado |
| `tests/test_stats.py` figura como hecho y no existe | `TASKS.md` | El tablero no es fiable: desde ahora, «hecho» exige evidencia |

Lo que sí sirve: la estructura por módulos, FastAPI + UI estática, las ramas por agente, las tarjetas de variables con definiciones sencillas y la idea de las «4 preguntas».

## 2. El producto que sí gana

**Una herramienta donde un estudiante hace de detective de datos: elige un lugar, la herramienta trae los datos reales de la NASA, mide la tendencia y le dice con honestidad si es real o todavía no se puede saber.**

### P0 — imprescindible (sin esto no se entrega)
1. **Datos NASA reales para cualquier punto o caja del planeta**, en vivo, vía NASA POWER (MERRA-2 y CERES; 1981–2025, sin cuenta). Verificado: 2 s por consulta.
2. **Serie temporal** con ciclo estacional, anomalías, medias anuales y recta de tendencia con banda de confianza.
3. **Veredicto con las 4 preguntas**: qué, dónde, cuánto (por década, con IC 95 %) y si es significativo, usando las tres vías que nombra el reto:
   prueba t, Mann-Kendall e intervalos de confianza, corregidas por autocorrelación.
4. **Procedencia visible** en cada resultado: fuente, URL de la consulta, fecha, cita.
5. **Inglés y español**, sin instalación, con 3–4 casos de demostración «para mirar».

### P1 — lo que nos separa del resto
6. **Mapa de tendencias**: pendiente por celda y punteado donde es significativa (con control de falsos descubrimientos).
   Es la respuesta directa al «dónde» y a la frase clave del reto: *la misma variable sube en una región y baja en otra*.
7. **Modo comparar**: dos regiones, misma variable, lado a lado, con la frase «tendencias opuestas» cuando lo sean.
8. **«¿Cuántos años faltan para estar seguros?»** (Weatherhead et al. 1998). El reto lo dice textual: a veces a una tendencia solo le falta más tiempo de datos.
9. **Detective con IA (RAG)**: el estudiante escribe «¿llueve menos en Piura?» o hace clic en el mapa y la IA propone qué variables investigar, **con fuentes citadas**. Es lo que el reto sugiere al hablar de usar artículos y características de la región (desierto, selva, estuario, aire sobre una gran ciudad).
10. **Planificador afinado con LoRA**: un modelo pequeño y abierto convierte la pregunta en un plan estructurado. Medimos base vs. LoRA vs. reglas y publicamos la tabla.
11. **Sube tu CSV de Giovanni**: con eso la herramienta sirve para cualquier variable que Giovanni exporte (GPM, GLDAS, AIRS, OMI, MODIS…).
12. **Validación contra valores publicados**: el motor reproduce tendencias que la NASA y NSIDC ya publican (temperatura global, hielo marino ártico de septiembre).

### P2 — si sobra tiempo
13. Atlas global precalculado (4–6 variables). 14. Segunda opinión con otra fuente (p. ej. GPM frente a MERRA-2). 15. Explicación afinada con LoRA. 16. Dato de una agencia socia (GPM es NASA/JAXA; ESA CCI).

### Cómo se usa la IA sin perder validez
- **La IA nunca escribe cifras ni coordenadas.** Las cifras salen del motor; un guardián rechaza cualquier número que no esté en los datos.
- **RAG** sobre un corpus pequeño y verificado (tarjetas de variables, perfiles de bioma, artículos de la NASA, resúmenes de artículos científicos), cada documento con URL comprobada.
- **LoRA** entrenado con las candidatas recuperadas dentro del prompt (afinado aumentado con recuperación), así el catálogo puede crecer sin reentrenar.
- **Todo degrada con elegancia**: sin modelo, la app sigue funcionando con reglas + fragmentos citados (`AI_MODE=extractive`).

## 3. Arquitectura

```
 Estudiante ── UI estática (Leaflet + Chart.js, ES/EN) ──────────────┐
                                                                     ▼
                         FastAPI  /api/series /analyze /trendmap /compare /ai/*
              ┌──────────────┬───────────────┬──────────────────────────┐
              ▼              ▼               ▼                          ▼
        src/etl          src/stats      src/detective              data/
   POWER · Giovanni CSV  Sen · MK · t   RAG (BM25 + embeddings)    catalog/ knowledge/
   GISTEMP · NSIDC       FDR · detect.  plan (LoRA→reglas)         cases/ (reales congelados)
   caché + procedencia                  explain (+ guardián)       atlas/ · lora/
                                              │
                                    Ollama local (modelo LoRA + explicador)
```

Despliegue: un solo servicio (FastAPI sirve también la UI). Respaldo: sitio estático con los casos reales congelados, por si la API cae durante las semanas de evaluación.

## 4. Fuentes de datos (todas verificadas hoy)

| Nivel | Fuente | Qué da | Cuenta |
|---|---|---|---|
| 0 | NASA POWER punto y regional | Temperatura, lluvia, humedad de suelo, evaporación, nieve, humedad, vapor de agua, ozono, aerosoles, nubosidad, radiación solar | No |
| 0 | NASA GISTEMP (un archivo) | Anomalía de temperatura global en rejilla desde 1880 | No |
| 0 | NSIDC Sea Ice Index v4 | Hielo marino ártico y antártico mensual (tendencias opuestas, caso de libro) | No |
| 1 | Giovanni → CSV (lo exporta el humano) | GPM IMERG, GLDAS, AIRS, OMI, MODIS: las fuentes que el reto nombra | Earthdata (gratis) |
| 2 | ORNL MODIS, AppEEARS, earthaccess | Automatizar el nivel 1 | Caído hoy / cuenta |

Cuidado científico que debe estar en el catálogo: la cabecera de POWER declara dos fuentes de radiación (SRB y CERES SYN1deg), así que la radiación y la nubosidad
combinan productos distintos. Analizar a través de un empalme crea tendencias falsas → campo `homogeneous_since`. La fecha del empalme (hipótesis: 2001) la confirma Hermes 1 en la documentación.
Comprobado en la muestra real: `AOD_55` empieza en 2001-01; `CLOUD_AMT` y `ALLSKY_SFC_SW_DWN`, en 1984-01; el resto, en 1981-01.

## 5. Calendario y puertas (hora local)

| Cuándo | Puerta | Se cumple si |
|---|---|---|
| Sáb 13:30 | **G0 Arranque** | Plan en `main`, 8 agentes con su prompt, cuenta Earthdata creada |
| Sáb 17:30 | **G1 Datos reales** | `/api/analyze?variable_id=T2M&lat=-12.05&lon=-77.03` devuelve análisis v2 con datos de POWER; sintéticos borrados; pruebas del motor en verde |
| Sáb 23:30 | **G2 Detective completo** | Mapa con clic, mapa de tendencias, comparar, catálogo ≥ 18 variables, RAG con fuentes, dataset LoRA v1, primer CSV de Giovanni analizado |
| Noche | Trabajos largos | Entrenamiento LoRA (ventana de GPU), atlas, ampliar corpus |
| Dom 10:00 | **G3 IA integrada** | Planificador LoRA servido y evaluado (o plan B por reglas), explicación con guardián, UI bilingüe, 4 casos en modo demo |
| Dom 14:00 | **Congelación** | Solo correcciones. Despliegue público funcionando |
| Dom 18:00 | **G4 Entrega lista** | Página del proyecto en inglés, demo (30 s o 7 láminas), enlaces públicos probados en incógnito |
| Dom 20:00 | **ENTREGAR** | «Submit for Judging» pulsado. Margen de 4 h |

Regla de recorte: si una puerta no se cumple a su hora, se corta P2, luego lo último de P1. **P0 no se negocia.**

## 6. Lo que solo puedes hacer tú (humano)

1. Publicar este plan en `main` y pegar a cada agente su línea de arranque (ver `TASKS.md`).
2. Crear cuenta en https://urs.earthdata.nasa.gov (gratis, 2 min).
3. En Giovanni (https://giovanni.gsfc.nasa.gov), exportar series «Time Series, Area-Averaged» en CSV y dejarlas en `data/raw/giovanni/`.
   Mínimo 5: lluvia GPM IMERG, humedad de suelo GLDAS, temperatura AIRS, NO₂ u ozono OMI, NDVI MODIS, para las regiones de los casos. **El primero cuanto antes**: Antigravity 1 lo necesita como muestra.
4. Decidir la ventana de GPU para entrenar el LoRA (hoy la RTX 4070 SUPER está casi llena por un modelo de 35B cargado en Ollama de forma permanente) o usar Kaggle/Colab.
5. Elegir los casos y la historia (sección 7). Es tu decisión, no de la IA.
6. `railway login` (o el hosting que elijas) y, con el sitio arriba, pedir la clasificación de FortiGuard que recomienda la guía.
7. Equipo: todos inscritos en el mismo evento local, máximo 6, ninguno en lista de espera.
8. Grabar o armar la demo y pulsar «Submit for Judging».

## 7. Decisiones que te tocan (márcalas hoy)

La guía dice que la IA puede acelerar el trabajo pero **no debe ser quien idee cómo resolver el reto**. La idea base (detective + 4 preguntas) ya era tuya; estas decisiones también deben serlo:

- [ ] **Caso estrella local.** Opciones: lluvias y El Niño en Piura · calentamiento en la Cordillera Blanca · humedad de suelo en Ica · aire sobre Lima · selva de Madre de Dios. ¿Cuál cuenta tu equipo con conocimiento propio?
- [ ] **Caso «no significativo»**: uno donde la respuesta honesta sea «todavía no se puede saber». Enseña más que tres casos obvios.
- [ ] **Caso de tendencias opuestas**: hielo marino ártico vs. antártico, o NO₂ en dos ciudades.
- [ ] Nombre y lema definitivos (sin «NASA» en el nombre).
- [ ] Demo oficial: vídeo ≤ 30 s **o** 7 láminas (solo uno cuenta).
- [ ] Qué premio buscamos: propongo Best Use of Science o Best Use of Data, con Local Impact como segunda vía.

## 8. Riesgos y plan B

| Riesgo | Plan B |
|---|---|
| POWER lento o caído durante la evaluación | Caché en disco + casos reales congelados en `data/cases/` + sitio estático |
| El LoRA no supera al modelo base o no hay GPU | Se entrega planificador por reglas + RAG y se publica la tabla tal cual salga. No se maquilla |
| No llega ningún CSV de Giovanni | Se entrega con POWER + GISTEMP + NSIDC; se declara en la página qué fuentes del reto quedaron fuera |
| Un agente entrega sin evidencia o con datos inventados | La puerta `scripts/gate.py` lo rechaza; no se fusiona |
| Modelos de origen chino en el producto (Qwen, DeepSeek, BGE) | La guía somete a revisión los vínculos con entidades chinas. No afirmo que usarlos esté prohibido, pero es un riesgo barato de evitar: en el producto usar Gemma, Phi, Granite o Llama. Si dudas, pregunta a tu Local Lead |
| Se acaba el tiempo | Regla de recorte de la sección 5 |
