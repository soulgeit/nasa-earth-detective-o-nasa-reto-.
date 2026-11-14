# TASKS.md - Tablero de Control de Agentes (NASA RETO)

Estado general: **FASE 1 - CONSTRUCCIÓN MODULAR EN PARALELO**  
Arquitecto Supervisor: **Claude Fable 5.2 (`cfable`)**

---

## Leyenda de Estados
- `[ ]` Pendiente
- `[/]` En Progreso
- `[x]` Completado

---

## 🛰️ EQUIPO SCRAPERS (Ingesta de Información y Datos)

### Hermes 1 (PC1 - Local)
- **Rama:** `feature/catalog`
- **Carpeta:** `data/`
- **Tareas:**
  - [x] T1.1: Generar diccionario estructurado de variables NASA en `data/variables_catalog.json` con explicaciones didácticas.
  - [ ] T1.2: Documentar endpoints y fuentes públicas (Giovanni, CDO NOAA, AppEEARS, SWOT, RCM) en `data/SOURCES.md`.
  - [ ] T1.3: Mapear enlaces científicos de referencia (artículo SeaWiFS, guía de significancia) para contexto pedagógico.

### Hermes 2 (PC2 - 192.168.18.24 Remoto)
- **Rama:** `feature/scrapes`
- **Carpeta:** `data/raw/` y `data/processed/`
- **Tareas:**
  - [x] T2.1: Generar datasets mensuales limpios (2000-2024) para el caso Mar de Aral (retroceso de agua).
  - [x] T2.2: Generar datasets mensuales limpios para el caso Calentamiento del Ártico (temperatura MERRA-2).
  - [x] T2.3: Generar datasets mensuales limpios para el caso Deforestación de la Amazonía (NDVI MODIS).
  - [x] T2.4: Generar datasets mensuales limpios para Sequía de California (GPM precipitación y GLDAS humedad).
  - [ ] T2.5: Script de descarga en vivo o caché local para peticiones arbitrarias.

---

## 🛠️ EQUIPO CONSTRUCTORES (Desarrollo de Software)

### Antigravity 1 (PC1 - Local)
- **Rama:** `feature/stats`
- **Carpeta:** `src/stats/`
- **Tareas:**
  - [x] T3.1: Implementar algoritmo de desestacionalización mensual (anomalías climáticas).
  - [x] T3.2: Implementar prueba no paramétrica de Mann-Kendall con cálculo de Z y p-value.
  - [x] T3.3: Implementar estimador de pendiente de Sen (Theil-Sen slope).
  - [x] T3.4: Implementar regresión lineal OLS con intervalo de confianza del 95% y R².
  - [x] T3.5: Generar diagnósticos legibles ("Altamente significativo", "Tendencia moderada", etc.).
  - [x] T3.6: Pruebas unitarias de validación matemática en `tests/test_stats.py`.

### Antigravity 2 (PC2 - 192.168.18.24 Remoto)
- **Rama:** `feature/api`
- **Carpeta:** `src/api/`
- **Tareas:**
  - [x] T4.1: Crear servidor FastAPI con soporte CORS multiplataforma.
  - [x] T4.2: Endpoint `GET /api/variables`: Listar variables y metadatos.
  - [x] T4.3: Endpoint `GET /api/regions`: Listar regiones y bounding boxes.
  - [x] T4.4: Endpoint `GET /api/timeseries`: Retornar series históricas crudas.
  - [x] T4.5: Endpoint `POST /api/analyze`: Conectar con el motor estadístico y devolver el reporte científico completo.
  - [ ] T4.6: Documentación Swagger/OpenAPI interactiva en `/docs`.

### Claude Omni 1 (PC1 - Local)
- **Rama:** `feature/ui`
- **Carpeta:** `src/ui/`
- **Tareas:**
  - [x] T5.1: Diseñar interfaz interactiva y moderna (HTML5, CSS moderno, JS puro o Chart.js).
  - [x] T5.2: Gráfica principal interactiva: serie temporal, línea de tendencia y anomalías desestacionalizadas.
  - [x] T5.3: Tarjetas de resultados con las 4 preguntas de la NASA (Qué, Dónde, Cuánto, Significancia).
  - [x] T5.4: Sello visual de "Significancia Científica" (p < 0.05 verificado vs. No significativo).
  - [x] T5.5: Selector de regiones y variables con buscador interactivo.

### Claude Omni 2 (PC1 - Local)
- **Rama:** `feature/wizard`
- **Carpeta:** `src/detective/`
- **Tareas:**
  - [x] T6.1: Crear asistente guiado ("Data Detective Wizard") con preguntas sencillas para estudiantes.
  - [x] T6.2: Mapear preguntas intuitivas ("¿Hay sequía?", "¿Se está calentando?") a variables satelitales formales.
  - [x] T6.3: Integrar casos de estudio prediseñados (Aral Sea, Ártico, Amazonía, California).
  - [x] T6.4: Generador de informe de investigación escolar en formato descargable o imprimible.

### Claude Omni 3 (PC2 - 192.168.18.24 Remoto)
- **Rama:** `feature/etl`
- **Carpeta:** `src/etl/`
- **Tareas:**
  - [x] T7.1: Adaptador para series temporales de Giovanni (Giovanni CSV Parser).
  - [x] T7.2: Adaptador para NOAA Climate Data Online (CDO).
  - [x] T7.3: Conversor de unidades de ingeniería espacial a unidades comprensibles (°C, mm, %).
  - [x] T7.4: Generador sintético de series temporales de respaldo con ruido climáticamente realista (fallback offline).

---

## 👑 SUPERVISIÓN Y MERGE (Claude Fable 5.2)
- **Rama:** `main`
- **Tareas:**
  - [x] T8.1: Validar diseño de arquitectura y contratos.
  - [ ] T8.2: Auditar PRs / ramas de cada módulo.
  - [ ] T8.3: Integrar ramas (`feature/*`) a `main`.
  - [ ] T8.4: Verificar prueba integral de extremo a extremo.
