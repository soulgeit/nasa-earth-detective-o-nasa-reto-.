# TASKS.md - Tablero de Control de Agentes (NASA RETO)

Estado general: **FASE 1 - CONSTRUCCIÓN MODULAR EN PARALELO**  
Arquitecto Supervisor: **Claude Fable 5.2 (`cfable`)**

---

## 🏛️ Estructura de Mando del Enjambre

1. **Arquitecto Supremo:** Claude Fable 5.2 (`cfable`) -> Coordina la arquitectura global y el merge final.
2. **Líder del Equipo de Scrapers (Head of Data & Ingestion):** **Antigravity 1** -> Dirige a Hermes 1 y Hermes 2, define schemas y valida la calidad científica de los datos.
3. **Equipo Scrapers (Recolectores):** Hermes 1 (PC1) y Hermes 2 (PC2).
4. **Equipo Constructores (Desarrollo Core & UI):**
   - **Antigravity 2 (PC2):** Motor Estadístico & Computación Científica.
   - **Claude Omni 1 (PC1):** Frontend & Visualización de Series.
   - **Claude Omni 2 (PC1):** Asistente Detective & Casos de Estudio.
   - **Claude Omni 3 (PC2):** Backend API & ETL Pipeline.

---

## 🛰️ DIVISIÓN 1: EQUIPO DATA & SCRAPERS

### 👑 Antigravity 1 (PC1 - Local) - JEFE DE SCRAPERS
- **Rama:** `feature/data-pipeline`
- **Carpeta:** `data/` y supervisión de pipelines
- **Responsabilidades:**
  - Definir y exigir los formatos estándar a Hermes 1 y Hermes 2.
  - Verificar que ningún dataset contenga valores nulos o corrupción de fechas.
  - Coordinar la integración entre los metadatos científicos y las series temporales procesadas.
  - Tareas asignadas:
    - [x] S0.1: Definir la especificación de datos normalizada para variables de la Tierra.
    - [ ] S0.2: Auditar el catálogo de `data/variables_catalog.json` generado por Hermes 1.
    - [ ] S0.3: Validar las series temporales en `data/processed/` generadas por Hermes 2.
    - [ ] S0.4: Crear script de control de calidad (`scripts/validate_datasets.py`).

### Hermes 1 (PC1 - Local) - Especialista en Catálogos & APIs
- **Supervisor directo:** Antigravity 1
- **Rama:** `feature/catalog`
- **Carpeta:** `data/`
- **Tareas:**
  - [x] T1.1: Generar diccionario de variables NASA en `data/variables_catalog.json` con explicaciones didácticas.
  - [ ] T1.2: Documentar endpoints y fuentes públicas (Giovanni, CDO NOAA, AppEEARS, SWOT, RCM) en `data/SOURCES.md`.
  - [ ] T1.3: Documentar casos de estudio científicos (SeaWiFS, tendencias significativas) para el contexto educativo.

### Hermes 2 (PC2 - 192.168.18.24 Remoto) - Extractor de Series & Datasets
- **Supervisor directo:** Antigravity 1
- **Rama:** `feature/scrapes`
- **Carpeta:** `data/raw/` y `data/processed/`
- **Tareas:**
  - [x] T2.1: Generar datasets mensuales limpios (2000-2024) para el caso Mar de Aral (retroceso de agua).
  - [x] T2.2: Generar datasets mensuales limpios para el caso Calentamiento del Ártico (temperatura MERRA-2).
  - [x] T2.3: Generar datasets mensuales limpios para el caso Deforestación de la Amazonía (NDVI MODIS).
  - [x] T2.4: Generar datasets mensuales limpios para Sequía de California (GPM precipitación y GLDAS humedad).
  - [ ] T2.5: Automatizar descarga y almacenamiento en caché para peticiones de coordenadas arbitrarias.

---

## 🛠️ DIVISIÓN 2: EQUIPO CONSTRUCTORES (Core, API & UI)

### Antigravity 2 (PC2 - 192.168.18.24 Remoto) - Motor Estadístico
- **Rama:** `feature/stats`
- **Carpeta:** `src/stats/`
- **Tareas:**
  - [x] T3.1: Algoritmo de desestacionalización mensual (anomalías climáticas).
  - [x] T3.2: Prueba no paramétrica de Mann-Kendall con cálculo de Z y p-value.
  - [x] T3.3: Estimador de pendiente de Sen (Theil-Sen slope robusta).
  - [x] T3.4: Regresión lineal OLS con intervalo de confianza del 95% y R².
  - [x] T3.5: Generar diagnósticos legibles ("Altamente significativo", "Tendencia moderada", etc.).
  - [x] T3.6: Pruebas unitarias de validación matemática en `tests/test_stats.py`.

### Claude Omni 1 (PC1 - Local) - Frontend & Visualización
- **Rama:** `feature/ui`
- **Carpeta:** `src/ui/`
- **Tareas:**
  - [x] T5.1: Diseñar interfaz interactiva y moderna (HTML5, CSS moderno, JS puro o Chart.js).
  - [x] T5.2: Gráfica principal interactiva: serie temporal, línea de tendencia y anomalías desestacionalizadas.
  - [x] T5.3: Tarjetas de resultados con las 4 preguntas de la NASA (Qué, Dónde, Cuánto, Significancia).
  - [x] T5.4: Sello visual de "Significancia Científica" (p < 0.05 verificado vs. No significativo).
  - [x] T5.5: Selector de regiones y variables con buscador interactivo.

### Claude Omni 2 (PC1 - Local) - Asistente Detective (Wizard)
- **Rama:** `feature/wizard`
- **Carpeta:** `src/detective/`
- **Tareas:**
  - [x] T6.1: Crear asistente guiado ("Data Detective Wizard") con preguntas sencillas para estudiantes.
  - [x] T6.2: Mapear preguntas intuitivas a variables satelitales formales.
  - [x] T6.3: Integrar casos de estudio prediseñados (Aral Sea, Ártico, Amazonía, California).
  - [x] T6.4: Generador de informe de investigación escolar en formato descargable o imprimible.

### Claude Omni 3 (PC2 - 192.168.18.24 Remoto) - Backend API & ETL Pipeline
- **Rama:** `feature/api-etl`
- **Carpeta:** `src/api/` y `src/etl/`
- **Tareas:**
  - [x] T7.1: Servidor FastAPI con endpoints `/api/variables`, `/api/regions`, `/api/analyze`.
  - [x] T7.2: Adaptadores para Giovanni (CSV) y NOAA CDO.
  - [x] T7.3: Conversor de unidades espaciales a unidades comunes (°C, mm, %).
  - [x] T7.4: Conectar la API con los datos procesados validados por Antigravity 1.

---

## 👑 SUPERVISIÓN Y MERGE (Claude Fable 5.2)
- **Rama:** `main`
- **Tareas:**
  - [x] T8.1: Validar diseño de arquitectura y contratos.
  - [ ] T8.2: Auditar PRs / ramas de cada módulo.
  - [ ] T8.3: Integrar ramas (`feature/*`) a `main`.
  - [ ] T8.4: Verificar prueba integral de extremo a extremo.
