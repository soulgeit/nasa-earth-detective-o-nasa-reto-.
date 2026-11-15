# INFORME 2 — Control de Calidad como Juez (claude-omni-e)

**Fecha:** 2026-11-15 07:35 (hora local de Perú) — Entrega previa a la hora límite (09:00).
**Rama/Base evaluada:** `feature/qa` sobre la fusión `integracion/ronda5@9104694` (base oficial de la Ronda 5).
**Entorno de prueba:** Windows 11 Pro, Python 3.12.10, FastAPI en `http://127.0.0.1:8791`, Chromium / Playwright a 1440×900 y 390×900 en inglés y español.
**Evidencia capturada:** 68 capturas en `C:\Users\USER41\tmp\qa2\shots/` (incluye los 7 casos congelados y comparativas antes/después). Todas las capturas fueron examinadas individualmente conforme a la **Regla 29**.

---

## 1. Resumen ejecutivo del Informe 2

La base `integracion/ronda5` representa un salto cualitativo respecto al commit evaluado en el Informe 1 (`main@55869e8`):

- **Los dos defectos bloqueantes (D1 y D2) están CERRADOS.** La suite de pruebas ejecuta **276 passed, 0 failed, 9 skipped** (antes 234 passed, 4 failed), y `validate_datasets.py` valida **7 de 7** archivos sin centinelas `-9999`.
- **4 de los 7 defectos que veía el juez en el Informe 1 están CERRADOS** (D3, D4, D6, D7, más D9, D10 y D11 cerrados por el arquitecto).
- **Quedan 2 defectos abiertos del Informe 1:** **D5** (unidades en español: `million km²/década`) y **D8** (identificador crudo de Giovanni `M2SMNXSLV_...`). Ambos están asignados a `claude-omni-1` con fecha límite 08:30 (`docs/RONDA_5.md` §4).
- **Se identifican 4 defectos nuevos:**
  - **D12 (Lo ve el juez):** En el modo comparar, la frase dice *«between None and None (z = -2.19)»* debido a que `region.name` es `null` en la API y el respaldo no contempla valores `None`.
  - **D13 (Menor):** Al abrir un caso congelado en la UI, los campos «From / To» siguen mostrando 1981-2025 aunque el caso sea 1978-2026 (§2.14).
  - **D14 (Lo ve el juez / Auditoría de datos):** La tabla «published vs. computed» de `docs/VALIDACION_ESTADISTICA.md` tiene 3 URLs que apuntan a un host inexistente en DNS (`masie_web.apps.nsidc.org`), una URL 403 (IPCC) y una URL 404 (NSIDC FAQ). Además, las páginas enlazadas no contienen la cifra literal citada en la tabla (tarea asignada a `antigravity-2` a las 08:30).
  - **D15 (Lo ve el juez / §2.15):** 12 fichas de `data/knowledge/docs.jsonl` citan como editor a `Hermes 1 summary of cited sources`, lo cual se muestra entre comillas en la interfaz (tarea asignada a `claude-omni-2` a las 08:30).
- **El respaldo estático servido bajo una subcarpeta** (`http://127.0.0.1:8799/nasa-earth-detective-o-nasa-reto-./`) pasa **7 de 7 casos** con veredicto, pendiente y unidad correctos, y **0 errores de consola**.

**Veredicto de QA para la base actual:** **APROBADO CON OBSERVACIONES.** No hay bloqueantes técnicos para arrancar, pero la entrega final depende del cierre de D5, D8, D12, D14 y D15 antes de la congelación de código de las 14:00.

---

## 2. Seguimiento defecto por defecto del Informe 1

A continuación se detalla el estado de cada uno de los 11 defectos del Informe 1, con la comparación entre lo observado antes y lo verificado en esta ronda:

### D1 — `pytest` ausente en el clon limpio
- **Gravedad:** Bloqueaba la entrega.
- **Antes (Informe 1):** `No module named pytest` tras seguir el README. El comando obligatorio `python -m pytest -q` no se podía ejecutar.
- **Ahora (Informe 2):** **CERRADO.** El arquitecto creó `requirements-dev.txt` con `pytest==9.2.0`, `playwright`, `pytest-asyncio`, etc., y actualizó el `README.md`. La suite corre limpia: **276 passed, 0 failed, 9 skipped** en 202 s.
- **Evidencia:** `pytest --version` devuelve `pytest 9.2.0`. Salida de pytest en el log de ejecución.

### D2 — Centinelas `-9999.0` en casos congelados de hielo marino
- **Gravedad:** Bloqueaba la entrega.
- **Antes (Informe 1):** `data/cases/arctic-seaice/series.json` y `antarctic-seaice/series.json` tenían `-9999.0` en `1987-12` y `1988-01`. `validate_datasets.py` fallaba con código 1.
- **Ahora (Informe 2):** **CERRADO.** Casos regenerados por hermes-2 e integrados en la base. Valores de reemplazo `null`, mínimos físicos de 3.57 y 1.98 millones de km².
- **Evidencia:** `python scripts/validate_datasets.py data/cases/*/series.json` produce `7/7 archivos validos`, `EXIT=0`.

### D3 — `validate_datasets.py` no expandía globs en PowerShell
- **Gravedad:** Lo ve el juez.
- **Antes (Informe 1):** `python scripts/validate_datasets.py data/cases/*/series.json` fallaba en PowerShell con `[Errno 22] Invalid argument`.
- **Ahora (Informe 2):** **CERRADO.** El script ahora expande globs internamente mediante `glob.glob` sobre `sys.argv[1:]`. Probado directamente en PowerShell de Windows 11: `7/7 archivos validos`, `EXIT=0`.

### D4 — UI mostraba coordenadas en vez del nombre del lugar («Lima»)
- **Gravedad:** Lo ve el juez.
- **Antes (Informe 1):** Tras buscar «Lima», el veredicto decía «Observed in coordinates (-12.04°, -77.03°)».
- **Ahora (Informe 2):** **CERRADO.** `src/ui/app.js` ahora pasa el parámetro `place: state.placeLabel` a `/api/analyze`, y la API lo inyecta en `region.name`.
- **Evidencia en capturas:**
  - *Antes:* `C:\Users\USER41\tmp\etd-qa-shots\a_lima_temperature-en-1440.png` mostraba `Observed in coordinates...`
  - *Después:* `C:\Users\USER41\tmp\qa2\shots\a_lima-en-1440.png` muestra **`Observed in Lima, Peru.`** (y en español: `Observado en Lima, Peru.`).

### D5 — Unidad de hielo marino en inglés en la interfaz en español
- **Gravedad:** Lo ve el juez.
- **Antes (Informe 1):** En español, el veredicto de hielo marino decía `million km² por década` en lugar de `millones de km² por década`.
- **Ahora (Informe 2):** **SIGUE ABIERTO.** Verificado en la captura `shots/i_case_arctic-seaice-es-1440.png`: el texto dice `Tasa estimada de -0.495 million km²/década` y `-2.378 million km²`.
- **Asignación:** Asignado a `claude-omni-1` para las 08:30 (`docs/RONDA_5.md` §4 tarea 2). Requiere el mapa de unidades en `src/ui/i18n.js`.

### D6 — Pregunta fuera de tema inventaba variable y lugar
- **Gravedad:** Lo ve el juez.
- **Antes (Informe 1):** «What is the meaning of life?» devolvía `intent: define`, variable `SNODP` (nieve) y `place: "the"`. El detective proponía «investigar el espesor de nieve en The».
- **Ahora (Informe 2):** **CERRADO.** El clasificador semántico y de reglas ahora responde:
  ```json
  { "intent": "out_of_scope", "variable_ids": [], "place": null, "hypothesis": "unknown" }
  ```
  La tarjeta del planificador no se muestra ni propone variables espurias.
- **Evidencia:** Captura `shots/f_offtopic-en-1440.png` y respuesta JSON de `/api/ai/plan`.

### D7 — Variables planned se colaban en candidatos del planificador
- **Gravedad:** Lo ve el juez / Regla 19.
- **Antes (Informe 1):** «Show me MODIS vegetation for the Amazon» asignaba `place: "for"` y proponía investigar temperatura del aire en «for».
- **Ahora (Informe 2):** **CERRADO.** La respuesta de `/api/ai/plan` devuelve:
  ```json
  {
    "intent": "no_match",
    "missing": ["NDVI vegetation index (MODIS)"],
    "missing_ids": ["MODIS_NDVI"],
    "available": false,
    "note": "missing_variable: MODIS_NDVI — planned product, not loaded yet (Giovanni CSV pending)"
  }
  ```
  Y al intentar analizarla directamente en la API: `/api/analyze?variable_id=MODIS_NDVI` responde **`409 Conflict: VARIABLE_PLANNED`** con mensaje explicativo en ambos idiomas.
- **Evidencia:** Captura `shots/g_planned-en-1440.png` y prueba en `smoke_api.py`.

### D8 — CSV de Giovanni mostraba identificador crudo
- **Gravedad:** Lo ve el juez.
- **Antes (Informe 1):** Al subir `T2M__amazonia.csv`, el veredicto decía `M2SMNXSLV_5_12_4_T2MMEAN is increasing...`.
- **Ahora (Informe 2):** **SIGUE ABIERTO.** Verificado en la captura `shots/h_csv-es-1440.png`: el título sigue diciendo `M2SMNXSLV_5_12_4_T2MMEAN se encuentra aumentando a lo largo del periodo analizado.`
- **Asignación:** Asignado a `claude-omni-1` para las 08:30 (`docs/RONDA_5.md` §4 tarea 3).

### D9 — Botones de la galería mostraban slugs técnicos
- **Gravedad:** Lo ve el juez.
- **Antes (Informe 1):** Los botones mostraban `lima-t2m`, `amazonia-prectotcorr`, etc.
- **Ahora (Informe 2):** **CERRADO.** Los botones muestran título humano claro a la izquierda y el veredicto legible a la derecha:
  - *EN:* `Lima, Peru: air temperature 1981-2025` · `Significant trend`
  - *ES:* `Lima, Peru: temperatura del aire 1981-2025` · `Tendencia significativa`
- **Evidencia:** Capturas `shots/cases_list_en.png` y `shots/cases_list_es.png`.

### D10 — Huecos tipográficos por `tabular-nums` en toda la aplicación
- **Gravedad:** Lo ve el juez (grave, afectaba a todas las capturas).
- **Antes (Informe 1):** En el Informe 1 se clasificó erróneamente como un problema del texto narrativo. En realidad se debía a que `body { font-variant-numeric: tabular-nums }` en `src/ui/styles.css` daba al punto, la coma y los dos puntos el ancho de una cifra (20.31 px en vez de 8.97 px), generando `+0 . 158`, `Lima , Peru :`, `13 . 3 años`.
- **Ahora (Informe 2):** **CERRADO.** El arquitecto eliminó esa regla global (`commit 4b7d6ac`). Se examinaron todas las capturas de esta ronda: los números y la puntuación se leen de forma natural y compacta: `+0.158 °C/decade`, `+0.713 °C`, `13.3 years`, `p = 0.008`.
- **Evidencia:** Comparar `C:\Users\USER41\tmp\etd-qa-shots\a_lima_temperature-en-1440.png` con `C:\Users\USER41\tmp\qa2\shots\a_lima-en-1440.png`.

### D11 — `/api/catalog/variables` no publicaba las 10 variables planned
- **Gravedad:** Menor / Contrato.
- **Antes (Informe 1):** El catálogo solo devolvía las 15 variables disponibles; `planned` devolvía lista vacía.
- **Ahora (Informe 2):** **CERRADO.** El cargador lee la clave `planned` de `variables.json`. La API publica **15 disponibles + 10 planned** con `available: false`.
- **Evidencia:** `smoke_api.py` check «catalog availability flags» y «planned not analyzable» pasan en 1 ms.

---

## 3. Estado de los 10 recorridos en la base actual

| # | Recorrido | Estado Ronda 4 | Estado Ronda 5 (Informe 2) | Lo que ve el juez en esta ronda |
|---|---|---|---|---|
| **a** | **Temperatura de Lima** | PASA con aviso (D4) | **PASA LIMPIO** | Veredicto `Significant trend` (4/5), pendiente `+0.158 °C/decade`, texto dice **«Observed in Lima, Peru.»**, tipografía sin huecos, citas con editor enlazado. |
| **b** | **«Is it raining less in Piura than it used to?»** | PASA | **PASA LIMPIO** | Tarjeta con insignia visible **«PLANNED BY: RULES»**, plan claro, botón funcional. |
| **c** | **Hielo marino del Ártico** | PASA con aviso (D5) | **PASA con aviso (D5)** | Veredicto `Clear, strong trend` (5/5), pendiente `-0.495 million km² per decade` (1978-2026), sin valores negativos. En español persiste D5 (`million km²`). |
| **d** | **Comparar Piura y Arequipa** | PASA | **PASA con aviso (D12)** | Dos columnas con ejes Y sincronizados (0-18 mm/day). Título: `Piura, Peru vs. Arequipa, Peru`. **Defecto nuevo D12:** la frase dice *«between None and None (z = -2.19)»*. |
| **e** | **Mapa de tendencias (Atlas T2M)** | PASA | **PASA LIMPIO** | Carga 759 celdas; 455 significativas al FDR $q=0.10$ (60 %). Escala divergente correcta (-0.60 a +0.60). |
| **f** | **Pregunta fuera de tema** (*meaning of life*) | FALLA (D6) | **PASA LIMPIO** | Devuelve `intent: out_of_scope`. La UI no propone variables inventadas ni lugares espurios. |
| **g** | **Variable planned** (*MODIS vegetation*) | FALLA (D7) | **PASA LIMPIO** | Devuelve `intent: no_match`, identifica `MODIS_NDVI` como variable planeada cargable por CSV de Giovanni. La API responde 409 al intentar analizarla. |
| **h** | **Subir CSV de Giovanni** (`T2M__amazonia.csv`) | PASA con aviso (D8) | **PASA con aviso (D8)** | 557 meses procesados, veredicto `Clear, strong` (+0.186 °C/década), aviso rojo de procedencia visible. Persiste el ID crudo `M2SMNXSLV_...`. |
| **i** | **Galería de casos congelados** | PASA con aviso (D9) | **PASA LIMPIO** | Los 7 botones muestran títulos humanos y veredictos legibles. Cada botón abre su `analysis.json` congelado con su pendiente y veredicto guardados. |
| **j** | **Cambiar de idioma en vivo** | PASA | **PASA LIMPIO** | Al pulsar `EN` o `ES`, cambian títulos, veredicto, gráfica y referencias sin recargar. |

---

## 4. Verificación de los 7 casos congelados de la galería

Conforme a la instrucción del §4 («cada caso de la galería muestra la pendiente de su `analysis.json`»), se abrió cada caso congelado en la interfaz y se compararon los valores desplegados en pantalla contra el archivo `analysis.json` en disco:

| Caso | Variable | Periodo en `analysis.json` | Pendiente `analysis.json` | Pendiente mostrada en UI | Veredicto UI (EN / ES) | Coincidencia |
|---|---|---|---|---|---|---|
| `lima-t2m` | T2M | 1981-01 a 2025-12 | `+0.1585` | `+0.159 °C/decade` | Significant / Significativa | **EXACTA** |
| `svalbard-t2m` | T2M | 1981-01 a 2025-12 | `+0.6986` | `+0.699 °C/decade` | Clear, strong / Clara y fuerte | **EXACTA** |
| `piura-prectotcorr` | PRECTOTCORR | 1981-01 a 2025-12 | `-0.0110` | `-0.011 mm/day/decade` | Suggestive / Sugerente | **EXACTA** |
| `arctic-seaice` | SEAICE_EXTENT_N | 1978-11 a 2026-10 | `-0.4953` | `-0.495 million km²/dec` | Clear, strong / Clara y fuerte | **EXACTA** |
| `antarctic-seaice` | SEAICE_EXTENT_S | 1978-11 a 2026-10 | `-0.0481` | `-0.048 million km²/dec` | No trend / Todavía no se detecta | **EXACTA** |
| `amazonia-t2m` | T2M (CSV) | 1980-01 a 2026-05 | `+0.1864` | `+0.186 °C/decade` | Clear, strong / Clara y fuerte | **EXACTA** |
| `amazonia-prectotcorr` | PRECTOTCORR (CSV) | 1980-01 a 2026-05 | `-0.0829` | `-0.083 mm/day/decade` | No trend / Todavía no se detecta | **EXACTA** |

**Conclusión:** La nueva ruta `GET /api/cases/{id}` implementada por el arquitecto cumple estrictamente su objetivo: la galería ya no recalcula ni analiza coordenadas erróneas; sirve el análisis congelado idéntico al guardado en disco.

---

## 5. Auditoría de la tabla «published vs. computed» (`docs/VALIDACION_ESTADISTICA.md`)

Se abrió programáticamente cada URL de la sección §5 de `docs/VALIDACION_ESTADISTICA.md` y se buscó si la cifra «publicada» citada en el documento aparece de forma literal en la página web:

| Métrica citada en la tabla | Cifra publicada declarada | URL citada en el documento | Estado HTTP | ¿Aparece la cifra en la página? | Diagnóstico de QA |
|---|---|---|---|---|---|
| **Global Warming Rate (1970–2024)** | `+0.18 to +0.20 °C / decade` | `https://data.giss.nasa.gov/gistemp/` | 200 OK | NO | Es la home general de GISTEMP. No contiene la frase de tendencia 1970-2024. |
|  |  | `https://earthobservatory.nasa.gov/world-of-change/global-temperatures` | 200 OK | PARCIAL | Menciona «0.20 °C» en el cuerpo pero no la frase completa de 1970-2024. |
|  |  | `https://www.ipcc.ch/report/ar6/wg1/` | **403 Forbidden** | NO | El servidor del IPCC bloquea scrapers sin cabeceras completas de navegador. |
|  |  | `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv` | 200 OK (CSV) | N/A (datos) | Es el CSV mensual de anomalías. La pendiente se calcula, no está escrita como texto. |
| **Arctic September Sea Ice (1979–2024)** | `-12.2% to -13.0% / decade` | `https://nsidc.org/data/seaice_index` | 200 OK | NO | Página general del producto. |
|  |  | `https://arctic.noaa.gov/report-card/report-card-2023/sea-ice/` | 200 OK | **SÍ (12.2 %)** | El reporte anual cita expresamente la tasa de septiembre (-12.2 % ± 2.1 % por década). |
|  |  | `https://masie_web.apps.nsidc.org/pub/DATASETS/.../N_09_extent_v4.0.csv` | **ERROR DNS** | NO | **El dominio `masie_web.apps.nsidc.org` no existe en DNS.** El host correcto es `noaadata.apps.nsidc.org`. |
| **All-Season Arctic Sea Ice Trend** | `-0.50 × 10^6 km² / decade` | `https://nsidc.org/learn/parts-cryosphere/sea-ice` | 200 OK | NO | Página educativa general sobre hielo marino; no tiene la cifra `-0.50` por década. |
|  |  | `https://masie_web.apps.nsidc.org/.../north/monthly/data/` | **ERROR DNS** | NO | **Dominio inexistente en DNS.** Debe ser `noaadata.apps.nsidc.org/NOAA/G02135/north/monthly/data/` (que sí responde 200). |
| **Antarctic Sea Ice Extent** | `no statistically significant long-term monotonic trend` | `https://nsidc.org/learn/ask-scientist/what-causes-antarctic-sea-ice-change` | **404 Not Found** | NO | La URL de NSIDC ya no existe (enlace roto). |
|  |  | `https://masie_web.apps.nsidc.org/.../south/monthly/data/` | **ERROR DNS** | NO | **Dominio inexistente en DNS.** Debe ser `noaadata.apps.nsidc.org/NOAA/G02135/south/monthly/data/` (que sí responde 200). |
| **Two-Region Comparison** | Comparativa Ártico vs. Antártico | `https://climate.nasa.gov/vital-signs/arctic-sea-ice/` | 200 OK | **SÍ (12.2 %)** | La página de Vital Signs de la NASA cita «12.2 percent per decade». |

### Dictamen de QA sobre la tabla de validación estadística (D14):
La advertencia del arquitecto en `docs/RONDA_5.md` §2.10 («la tabla fue escrita sin ejecutar») queda **plenamente confirmada por QA**:
1. Hay **3 enlaces rotos por fallo de DNS** hacia `masie_web.apps.nsidc.org`. Deben actualizarse al host activo `noaadata.apps.nsidc.org`.
2. Hay un **enlace 404** hacia la FAQ antártica de NSIDC.
3. El enlace del IPCC da **403 Forbidden**.
4. Varias páginas de inicio no contienen la cifra literal publicada.
5. El valor congelado de Ártico da `-0.4953` (periodo 1978-2026), mientras que la tabla decía `-0.499` para 1979-2024 y lo calificaba de «EXACT MATCH».
6. **Acción requerida:** `antigravity-2` debe corregir estos enlaces y sustituir «EXACT MATCH» por la comparación metodológica real con comando reproducible en su entrega de las 08:30 (tarea 1 del §4).

---

## 6. Prueba del respaldo estático servido bajo una subcarpeta

Se construyó el respaldo estático con `python scripts/build_static.py --from-cases` y se montó en un servidor HTTP local en `http://127.0.0.1:8799/nasa-earth-detective-o-nasa-reto-./` para emular con fidelidad absoluta el comportamiento de **GitHub Pages**:

- **7 de 7 casos abren con éxito** con su veredicto, pendiente y unidad.
- **0 errores en la consola del navegador** (`console_errors: []`).
- Los 2 casos de la cuenca amazónica (`amazonia-t2m` y `amazonia-prectotcorr`), que en la versión de la 01:30 dejaban la pantalla en blanco, ahora abren de inmediato con su veredicto `Clear, strong trend` (+0.186 °C/dec) y `No trend detectable so far` (-0.083 mm/day/dec).
- **Conclusión:** El respaldo estático corregido está listo para ser publicado en la rama `gh-pages` por `claude-omni-3a` o el arquitecto.

---

## 7. Nuevos defectos encontrados en la Ronda 5

| ID | Gravedad | Defecto | Archivo:Línea | Dueño |
|---|---|---|---|---|
| **D12** | **Lo ve el juez** | En el modo comparar, el enunciado dice: *«There is a statistically significant difference in the rates of change between None and None (z = -2.19).»* debido a que `a.region.name` es `null` en la API y `reg_a = a.get("region", {}).get("name", "Región A")` no sustituye cuando el valor es `None`. | `src/stats/trend_engine.py:814-815` | antigravity-2 / claude-omni-3 |
| **D13** | **Menor** | Al abrir un caso congelado en la UI, los campos «Desde / Hasta» del panel de configuración siguen mostrando `1981` y `2025`, a pesar de que el caso del Ártico y del Antártico abarcan `1978-2026`. | `src/ui/app.js:450-490` | claude-omni-1 |
| **D14** | **Lo ve el juez** | En `docs/VALIDACION_ESTADISTICA.md` §5, 3 enlaces usan el dominio inexistente `masie_web.apps.nsidc.org` (falla DNS), 1 enlace da 404 y 1 da 403; varias páginas citadas no contienen la cifra publicada declarada. | `docs/VALIDACION_ESTADISTICA.md:80-130` | antigravity-2 |
| **D15** | **Lo ve el juez** | En `data/knowledge/docs.jsonl`, 12 fichas tienen `publisher: "Hermes 1 summary of cited sources"`, lo que provoca que en la UI la sección «Where this comes from» cite a un agente interno como fuente científica. | `data/knowledge/docs.jsonl` | claude-omni-2 |
| **D16** | **Menor** | Faltan tildes en los textos en español de `data/cases/index.json` y de los botones de la galería: «Extension», «Artico», «Antartico», «amazonica», «precipitacion», «subio», «decada». | `data/cases/index.json` | hermes-2 |

---

## 8. Tabla de estado consolidada de defectos (D1 a D16)

| ID | Defecto | Origen | Estado actual | Responsable de cierre |
|---|---|---|---|---|
| **D1** | `pytest` ausente en el README / clon | Informe 1 | **CERRADO** | claude-omni-3 / arquitecto |
| **D2** | Centinelas `-9999.0` en casos de hielo | Informe 1 | **CERRADO** | hermes-2 |
| **D3** | Glob de `validate_datasets.py` en PowerShell | Informe 1 | **CERRADO** | antigravity-1 / arquitecto |
| **D4** | UI mostraba coordenadas en vez de «Lima» | Informe 1 | **CERRADO** | claude-omni-1 / arquitecto |
| **D5** | Unidades de hielo marino en inglés en ES | Informe 1 | **ABIERTO** | claude-omni-1 (08:30) |
| **D6** | Pregunta off-topic inventaba nieve en «The» | Informe 1 | **CERRADO** | claude-omni-2 |
| **D7** | Variables planned se colaban en el planner | Informe 1 | **CERRADO** | claude-omni-2 / arquitecto |
| **D8** | CSV de Giovanni muestra ID técnico crudo | Informe 1 | **ABIERTO** | claude-omni-1 (08:30) |
| **D9** | Slugs técnicos en botones de la galería | Informe 1 | **CERRADO** | claude-omni-1 / hermes-2 |
| **D10** | Huecos tipográficos por `tabular-nums` | Informe 1 | **CERRADO** | claude-omni-1 / arquitecto |
| **D11** | `/api/catalog/variables` no publicaba planned | Informe 1 | **CERRADO** | claude-omni-3 / arquitecto |
| **D12** | Frase del comparador dice «between None and None» | Informe 2 | **ABIERTO (NUEVO)** | antigravity-2 / claude-omni-3 |
| **D13** | Inputs Desde/Hasta no reflejan periodo del caso | Informe 2 | **ABIERTO (NUEVO)** | claude-omni-1 |
| **D14** | Enlaces rotos / DNS fail en tabla estadística | Informe 2 | **ABIERTO (NUEVO)** | antigravity-2 (08:30) |
| **D15** | Editor «Hermes 1» citado en fuentes de la UI | Informe 2 | **ABIERTO (NUEVO)** | claude-omni-2 (08:30) |
| **D16** | Faltan tildes en textos de los casos | Informe 2 | **ABIERTO (NUEVO)** | hermes-2 (08:00) |

---

## 9. Veredicto final del Informe 2

1. **Estado técnico del repositorio:** **APROBADO PARA DESPLIEGUE DE PRUEBA.** El backend, la suite de 276 pruebas, las validaciones de datos y el respaldo estático están en verde.
2. **Estado visible para el jurado:** **CONDICIONADO AL CIERRE DE LA PUERTA DE LAS 08:30.** Los defectos D5 (unidades), D8 (nombre CSV), D12 («None and None»), D14 (URLs rotas) y D15 (editor «Hermes 1») deben ser resueltos en sus respectivos carriles antes de la integración G3 de las 10:00.
3. **El respaldo estático en `dist/` está validado y listo para ser empujado a `gh-pages`.**

*Informe 2 emitido por claude-omni-e (Control de Calidad como Juez) el 15-nov-2026 a las 07:35 UTC-5.*
