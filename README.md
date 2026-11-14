# EarthTrend Detective - NASA Space Apps Challenge

Herramienta de Ciencia de Datos y Visualización para detectar, caracterizar y verificar la significancia estadística de cambios en el sistema terrestre utilizando datos satelitales y modelos asimilados de la NASA.

---

## 🚀 Inicio Rápido (Demo sin instalación)

1. Abre directamente `src/ui/index.html` en cualquier navegador web moderno (Edge, Chrome, Firefox).
2. Haz clic en cualquiera de los **Casos de Estudio Emblemáticos**:
   - 🌲 **Deforestación Amazonía** (MODIS NDVI): caída drástica y significativa de cobertura vegetal.
   - ❄️ **Calentamiento Ártico** (MERRA-2 Temp): tendencia al alza a +0.75°C/década (p < 0.001).
   - 🌊 **Desecación Mar de Aral** (SWOT Nivel de Agua): pérdida sostenida de nivel freático y lacustre.
   - 🌾 **Sequía California** (GLDAS Humedad del suelo): agotamiento de agua superficial en zona agrícola.
3. Observa cómo la aplicación responde a las 4 preguntas planteadas por la NASA:
   - **¿Qué está cambiando?**
   - **¿Dónde está cambiando?**
   - **¿Cuánto está cambiando?**
   - **¿Es estadísticamente significativo?** (Prueba Mann-Kendall y desestacionalización).

---

## 🛠️ Ejecución con Backend FastAPI (Opcional)

Si deseas levantar el servidor REST en Python:

```bash
pip install -r requirements.txt
python src/api/main.py
```
El servidor estará disponible en `http://localhost:8000` con documentación interactiva en `/docs`.

---

## 🤖 Organización del Enjambre de Agentes en Herdr

Este repositorio está estructurado para que 8 agentes trabajen en paralelo sin colisiones:

| Agente | Rol | Rama Git | Módulo |
| :--- | :--- | :--- | :--- |
| **Claude Fable 5.2** | Arquitecto / Reviewer | `main` | `ARCHITECTURE.md`, `TASKS.md` |
| **Antigravity 1** | Motor Estadístico | `feature/stats` | `src/stats/` |
| **Antigravity 2** | Backend API | `feature/api` | `src/api/` |
| **Claude Omni 1** | Frontend Dashboard | `feature/ui` | `src/ui/` |
| **Claude Omni 2** | Detective Wizard | `feature/wizard` | `src/detective/` |
| **Claude Omni 3** | Adaptadores ETL | `feature/etl` | `src/etl/` |
| **Hermes 1** | Catálogo Científico | `feature/catalog` | `data/variables_catalog.json` |
| **Hermes 2** | Ingesta de Datos | `feature/scrapes` | `data/raw/`, `data/processed/` |
