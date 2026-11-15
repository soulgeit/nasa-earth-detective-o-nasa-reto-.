# INFORME 1 — Control de Calidad como Juez (claude-omni-e)

**Fecha:** 2026-11-15 01:10 (hora local de Perú)
**Rama/Commit evaluado:** `origin/main@55869e8` («docs(ronda4): integracion del LoRA hecha; las tareas en espera pueden empezar»)
**Entorno de prueba:** Windows 11 Pro, Python 3.12.10, clon limpio en carpeta temporal `C:\Users\USER41\tmp\etd-clone-clean`, servidor `http://127.0.0.1:8791` arrancado con uvicorn siguiendo el `README.md` al pie de la letra, navegador Chromium con Playwright a 1440×900 y 390×900.
**Evidencia capturada:** 36 capturas en `C:\Users\USER41\tmp\etd-qa-shots/`.

---

## 1. Prueba del `README.md` al pie de la letra (clon limpio)

Se ejecutó en una carpeta nueva sin archivos previos:

```bash
git clone https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-..git clean
cd clean
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8791
```

| Paso | Resultado | Observación |
|---|---|---|
| `git clone` | **OK** | Clona sin errores; HEAD en `55869e8`. |
| `pip install -r requirements.txt` | **OK** | Instala fastapi, uvicorn, pydantic, requests, numpy, scipy, pymannkendall, python-multipart. |
| `python -m uvicorn ...` | **OK** | Arranca en < 1 s; `/api/health` devuelve `200` con `ai_mode="extractive"`. |
| `GET /` | **OK** | Devuelve la interfaz estática (18 106 bytes, 200). |
| `GET /docs` | **OK** | Swagger UI funcional. |
| **Check 1:** `python -m pytest -q` | **FALLA** | **Defecto D1 (Bloquea)**: `No module named pytest`. `pytest` no está en `requirements.txt`. Quien siga el README no puede correr la suite. |
| **Check 2:** `python scripts/smoke_api.py http://127.0.0.1:8791` | **OK** | **14 passed · 0 skipped · 0 failed** (tiempos: Lima 1050 ms, caché 1 ms, atlas 1305 ms). |
| **Check 3:** `python scripts/validate_datasets.py data/cases/*/series.json` | **FALLA (x2)** | (a) En PowerShell el argumento con glob no se expande y el script falla con `[Errno 22] Invalid argument: 'data/cases/*/series.json'`.<br>(b) Con glob expandido en bash: **5/7 válidos, 2 fallan**: `antarctic-seaice` y `arctic-seaice` tienen `data[109].value = -9999.0` y `data[110].value = -9999.0` (Regla 12 rota en los casos congelados). |
| **Check 4:** `python scripts/validate_knowledge.py` | **OK** | 15 disponibles + 10 planned; 168 documentos en el corpus; 0 fallos. |

---

## 2. Los 10 recorridos como juez (EN y ES · 1440 px y 390 px)

Cada recorrido se ejecutó en 4 combinaciones: inglés escritorio (1440 px), inglés móvil (390 px), español escritorio (1440 px) y español móvil (390 px).

| # | Recorrido | Estado | Lo que ve el juez / Evidencia |
|---|---|---|---|
| **a** | **Temperatura de Lima** | **PASA con aviso** | Veredicto `Significant` / `Significativa` (4/5). Pendiente `+0.159 °C per decade`. Gráfica de Sen a la altura de los datos (18–22 °C). Citas con editor enlazado (`[1] Temperatura del aire a 2 m — NASA POWER parameter dictionary`). **Defecto D4**: el texto dice «Observed in coordinates (-12.04°, -77.03°)» aunque se buscó «Lima». Capturas: `a_lima_temperature-*.png`. |
| **b** | **«Is it raining less in Piura than it used to?»** al detective | **PASA** | Plan estructurado en < 1 s: *«I plan to investigate Precipitation (corrected) in Piura»* / *«Voy a investigar Precipitación corregida en Piura»*. Botón «Confirm and Investigate» funcional. Capturas: `b_detective_piura_rain-*.png`. |
| **c** | **Hielo marino del Ártico** | **PASA con aviso** | Veredicto `Clear, strong` / `Clara y fuerte` (5/5). Pendiente `-0.507 million km² per decade`. No pide punto en el mapa. Valores físicos positivos en todo el registro (mínimo real 3.57). **Defecto D5**: en español la unidad sale en inglés (`million km² por década`). Capturas: `c_arctic_sea_ice-*.png`. |
| **d** | **Comparar Piura y Arequipa** | **PASA** | Modo dos columnas con ejes Y sincronizados. Título: `Piura vs. Arequipa`. Frase: *«Similar trend direction in both locations»* / *«Dirección de tendencia similar en ambas regiones»*. Capturas: `d_compare_piura_arequipa-*.png`. |
| **e** | **Mapa de tendencias (Atlas T2M)** | **PASA** | Carga 759 celdas; 455 significativas al FDR $q=0.10$ (60 %). Escala continua divergente (-0.60 a +0.60) con punto central destacado en celdas significativas. Leyenda e informe de porcentaje correctos. Capturas: `e_trendmap-*.png`. |
| **f** | **Pregunta fuera de tema:** *«What is the meaning of life?»* | **FALLA** | **Defecto D6 (Lo ve el juez)**: En inglés responde `intent: define`, variable `SNODP` (espesor de nieve) y `place: "the"`. El detective propone «investigar el espesor de nieve en The». En español se degrada a `no_match` pero inventa `place: "el lugar seleccionado"`. |
| **g** | **Variable planned:** *«Show me MODIS vegetation for the Amazon»* | **FALLA** | **Defecto D7 (Lo ve el juez / Regla 19)**: En inglés responde `missing: ["NDVI vegetation index (MODIS)"]` pero inventa `place: "for"`, `place_b: "the"`. En la UI la tarjeta propone investigar *«Air temperature at 2 m in for»*. La variable planned se coló en candidatos. |
| **h** | **Subir CSV de Giovanni** (`T2M__amazonia.csv`) | **PASA con aviso** | Sube el archivo, procesa 557 meses y muestra veredicto `Clear, strong` (+0.186 °C/década). **Insignia roja visible correcta**: `Resultado calculado a partir de un CSV que subiste.` **Defecto D8**: el texto muestra el ID crudo `M2SMNXSLV_5_12_4_T2MMEAN` en vez de un nombre legible. Capturas: `h_upload_csv-*.png`. |
| **i** | **Galería de casos congelados** | **PASA con aviso** | Los 7 botones de casos cargan en el mapa y la gráfica con un clic. **Defecto D9**: los botones muestran slugs técnicos (`lima-t2m`, `amazonia-prectotcorr`) en vez de títulos humanos. Capturas: `i_cases_gallery-*.png`. |
| **j** | **Cambiar de idioma a mitad del análisis** | **PASA** | Al pulsar `EN` o `ES` tras analizar Lima, cambian títulos, veredicto (`Significant` ↔ `Significativa`), gráfica, tabla técnica y referencias de inmediato sin recargar la página. Capturas: `j_lang_switch-*.png`. |

---

## 3. Revisiones transversales

### 3.1 Mezcla de idiomas (Regla 16)
- **Apertura:** la aplicación abre estrictamente en **inglés** por defecto (`window.__etdLang = 'en'`).
- **Filtración:** en español, la unidad de hielo marino se muestra como `million km² por década` (debería ser `millones de km² por década`).
- En la tabla de pruebas técnicas (`#tests-table`), los nombres de las pruebas salen en inglés tanto en EN como en ES (`Hamed-Rao Mann-Kendall`, `Annual Mann-Kendall`, `OLS t-test`); esto es aceptable porque son nombres propios de métodos estadísticos.

### 3.2 Cifras que no coinciden entre texto, gráfica y JSON
- Para Lima T2M:
  - JSON de la API: `slope_per_decade: 0.1585`
  - Tarjeta de veredicto: `+0.159 °C per decade`
  - Texto explicativo: `+0.158 °C/década` (difiere en el último dígito por redondeo `round(v, 3)` vs truncado).
  - Coincidencia general: **coherente**. No hay discrepancias de orden de magnitud.

### 3.3 Valores imposibles
- Extensión de hielo marino: el motor en vivo produce valores entre 3.57 y 16.34 millones de km² (físicamente correctos, sin negativos).
- **En los casos congelados de disco**, `arctic-seaice` y `antarctic-seaice` contienen `raw = -9999.0` en los meses `1987-12` y `1988-01`.

### 3.4 Marcas e identidad de la NASA
- **Cumplimiento impecable:** Cero logotipos o insignias de la NASA. Cero «mission blue» (#0b3d91) ni rojo (#fc3d21).
- Paleta editorial propia: pizarra `#16272b`, papel `#edf0ef`, petróleo `#125e5a`, ocre `#a2610f`.
- Aviso visible en el pie de página en ambos idiomas: *«Not affiliated with or endorsed by NASA»* / *«No está afiliado ni respaldado por la NASA»*.
- Tiles de satélite con atribución reglamentaria: `Imagery: NASA GIBS (public domain)`.

### 3.5 Modo extractivo vs. IA generativa
- El rótulo en modo extractivo (`AI_MODE=extractive`, por defecto) muestra exactamente:
  - EN: `EXCERPTS FROM CITED SOURCES (NO GENERATIVE AI)`
  - ES: `FRAGMENTOS DE LAS FUENTES CITADAS (SIN IA GENERATIVA)`
- No se menciona «AI-assisted synthesis» salvo cuando `AI_MODE=full`. Cumple la Regla 1 de la Ronda 3.

### 3.6 Adaptabilidad móvil (390 px)
- Todo el sitio se reorganiza en una sola columna fluida.
- El mapa Leaflet mantiene controles táctiles accesibles.
- No hay desbordamiento ni scroll horizontal en ninguna de las 36 capturas móviles.

---

## 4. Tabla de defectos encontrados

| ID | Gravedad | Defecto | Archivo:Línea | Dueño |
|---|---|---|---|---|
| **D1** | **Bloquea la entrega** | `pytest` no está en `requirements.txt`. El paso obligatorio del `README.md` (`python -m pytest -q`) falla en cualquier clon limpio. | `requirements.txt` | claude-omni-3 |
| **D2** | **Bloquea la entrega** | `data/cases/arctic-seaice/series.json` y `antarctic-seaice/series.json` contienen `-9999.0` en `1987-12` y `1988-01`. `validate_datasets.py` falla con código 1. | `data/cases/*/series.json` | hermes-2 |
| **D3** | **Lo ve el juez** | `scripts/validate_datasets.py` no expande globs internamente; en PowerShell `python scripts/validate_datasets.py data/cases/*/series.json` falla con `[Errno 22]`. | `scripts/validate_datasets.py:26` | antigravity-1 |
| **D4** | **Lo ve el juez** | Tras buscar «Lima», la UI no envía el nombre del lugar a `/api/analyze`; el veredicto dice «Observed in coordinates (-12.04°, -77.03°)» en vez de «Observed in Lima, Peru». | `src/ui/app.js:428-440` | claude-omni-1 |
| **D5** | **Lo ve el juez** | En español, la unidad de hielo marino se muestra en inglés: `million km² por década`. | `src/ui/i18n.js:32` / `data/catalog/variables.json:1210` | claude-omni-1b |
| **D6** | **Lo ve el juez** | Pregunta fuera de tema («What is the meaning of life?») asigna variable `SNODP` y lugar `place: "the"`. El detective propone investigar la nieve en «The». | `src/detective/planner.py:543` y `places.py` | claude-omni-2 |
| **D7** | **Lo ve el juez** | Variables `planned` se cuelan como candidatas en el planificador: la UI termina proponiendo investigar `T2M in for` para MODIS NDVI. | `src/detective/planner.py:546` y `src/detective/rag/__init__.py:203` | claude-omni-2 |
| **D8** | **Lo ve el juez** | Al subir el CSV de Giovanni, el veredicto muestra el ID técnico crudo `M2SMNXSLV_5_12_4_T2MMEAN` en vez del nombre legible. | `src/ui/app.js:181-186` | claude-omni-1 |
| **D9** | **Lo ve el juez** | Los botones de la galería de casos muestran slugs técnicos (`lima-t2m`, `amazonia-prectotcorr`) sin descripción humana. | `data/cases/index.json` y `src/ui/app.js:375` | hermes-2 / claude-omni-1 |
| **D10** | **Menor** | Tipografía: aparecen espacios extra antes de los puntos en varias frases generadas (`. 158 °C/década`, `13 . 3 años`). | `src/detective/narrative.py` / `app.js:187` | claude-omni-2 / claude-omni-1 |
| **D11** | **Menor** | `/api/catalog/variables` no publica las 10 variables `planned` con `available: false` (tarea 1 de claude-omni-3 pendiente). | `src/api/catalog.py:143` | claude-omni-3 |

---

## 5. Veredicto del informe 1

- **Pasa para desarrollo interno, NO pasa para entrega final.**
- Los dos bloqueantes para la entrega son **D1** (falta `pytest` en `requirements.txt`) y **D2** (los casos de hielo marino siguen con el centinela `-9999`).
- Los defectos **D4, D6, D7 y D9** degradan sensiblemente la experiencia del jurado al usar el detective y la galería.

*Informe emitido de forma independiente por claude-omni-e (Control de Calidad).*
