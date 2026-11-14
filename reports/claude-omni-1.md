# Reportes de Claude Omni 1 (Interfaz)

## U1 — LISTO  (2026-11-14 13:26 UTC-5)
Rama@commit: feature/ui@b5ac5e8
Qué quedó:
- Eliminado completamente el generador sintético `calculateStatsClientSide` de `src/ui/app.js`.
- Eliminado el catálogo embebido de variables inventadas y los valores por defecto inventados (`0.82`, `0.00001`, `Valor Observado (Satélite)`).
- Eliminada la paleta con los colores de marca de la NASA (`#0b3d91`, `#fc3d21`); sustituida por una paleta editorial propia accesible (petróleo `#125e5a`, tinta pizarra `#16272b`, ocre `#a2610f`, fondo papel `#edf0ef`).
- Agregado estado de error explícito y digno con código upstream + enlace a casos congelados cuando la API no responde.
Evidencia:
```bash
$ git grep -nE "Math\.sin|Math\.random|0\.82|0\.00001" -- src/ui
(sin resultados — código de salida 1)
```
Falta / riesgos: Ninguno para U1.
Necesito de otros: Antigravity 1 y Claude Omni 3 para que `/api/analyze` y `/api/catalog/variables` devuelvan datos reales en vivo.

## U2 — LISTO  (2026-11-14 13:28 UTC-5)
Rama@commit: feature/ui@b5ac5e8
Qué quedó:
- Pantalla principal implementada en una sola página con tres zonas (mapa interactivo Leaflet con mosaico base NASA GIBS Blue Marble y fallback a OSM; panel de investigación con selector de variable, periodo y buscador de lugares; zona de resultados).
- Gráfica temporal con Chart.js conmutador triple: valores mensuales, anomalías y medias anuales; banda de confianza y recta de Sen; línea punteada de empalme de productos (`homogeneous_since`).
- Cuatro hallazgos con la escalera de veredicto en 5 estados (`INSUFFICIENT_DATA`, `NOT_SIGNIFICANT`, `SUGGESTIVE`, `SIGNIFICANT`, `SIGNIFICANT_STRONG`).
- Tarjeta de detectabilidad con barra comparativa visual de años disponibles vs. años necesarios (Weatherhead et al. 1998).
- Desplegable técnico «Cómo lo sabemos» con tabla de pruebas (Mann-Kendall mensual y anual, t-test OLS), autocorrelación, tamaño efectivo de muestra y advertencias.
- Procedencia visible completa: fuente, resolución nativa, fecha, URL exacta con enlace y cita oficial.
- Aviso rojo visible automático cuando `provenance.kind === 'fixture'` o `'user_upload'`.
- Módulo de internacionalización completo `src/ui/i18n.js` con soporte nativo EN / ES.
- Responsive verificado en Playwright a 1440x900 (2 columnas) y a 360x800 (móvil 1 columna sin scroll horizontal).
Evidencia:
- Capturas verificadas en Playwright con fixture real de NASA POWER en Lima (`power_monthly_point_lima.json`).
- Archivos generados: `src/ui/app.js`, `src/ui/index.html`, `src/ui/styles.css`, `src/ui/i18n.js`.
Falta / riesgos:
- Integrar con los endpoints reales de FastAPI cuando Claude Omni 3 los despliegue.
- Tareas U3 (mapa de tendencias /api/trendmap y modo comparar) y U4 (detective RAG/plan) para la siguiente fase.
Necesito de otros:
- Claude Omni 3 (`feature/api`): desplegar endpoints `/api/health`, `/api/catalog/variables`, `/api/cases`, `/api/analyze`.
