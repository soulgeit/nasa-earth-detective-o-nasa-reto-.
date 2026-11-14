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

## U3 — LISTO  (2026-11-14 13:50 UTC-5)
Rama@commit: feature/ui@c77c550
Qué quedó:
- Selector de modo en el masthead: Punto individual (`single`), Mapa de tendencias regional (`trendmap`) y Comparar dos lugares (`compare`).
- **Mapa de tendencias (`/api/trendmap`)**:
  - Renderizado espacial de celdas rectangulares en Leaflet sobre el área seleccionada con `Shift + arrastrar`.
  - Escala divergente simétrica continua apta para daltónicos (petróleo `#125e5a` negativo / ocre `#a2610f` positivo / neutral `#edf0ef`).
  - **Punto central destacado en cada celda con `significant_fdr === true`** (control FDR de Benjamini-Hochberg).
  - Leyenda interactiva con rango exacto de pendiente por década y porcentaje total de celdas significativas.
  - Clic en cualquier celda para investigar esa coordenada puntual inmediatamente.
- **Modo Comparar (`/api/compare`)**:
  - Selección de dos puntos en el mapa o vía buscador (Lugar A y Lugar B).
  - Dos instancias de Chart.js sincronizadas con **el mismo rango y escala en el eje Y**.
  - Destacado visual prominente de la frase comparativa (`compare.statement`) y distintivo cuando las tendencias sean opuestas (`⚡ Se detectan tendencias opuestas`).
Evidencia:
- Verificado y capturado en Playwright a 1440x900 con la cuadrícula de 63 celdas de Piura (`power_monthly_regional_piura_T2M.json`) y con la comparación Lima vs. Ártico (Svalbard).
- Archivos actualizados: `src/ui/app.js`, `src/ui/index.html`, `src/ui/styles.css`, `src/ui/i18n.js`.
Falta / riesgos:
- Conectar con los endpoints finales cuando Claude Omni 3 los despliegue.
- Tarea U4: Integrar el detective con IA (`/api/ai/plan`, `/api/ai/scout`, `/api/ai/explain`).
Necesito de otros:
- Claude Omni 2 (`feature/wizard`): endpoints del detective IA.
- Claude Omni 3 (`feature/api`): montaje de `/api/trendmap` y `/api/compare`.

## U4 — LISTO  (2026-11-14 14:15 UTC-5)
Rama@commit: feature/ui (pendiente de hash tras commit)
Qué quedó:
- **Caja «Pregúntale al detective»**:
  - Entrada de lenguaje natural conectada a `/api/ai/plan`.
  - Muestra la tarjeta del plan estructurado con intención, variable propuesta y lugar detectado.
  - Botón «Confirmar e Investigar» que configura el formulario, geocodifica y ejecuta el análisis directamente.
- **Sugerencias espaciales («¿Qué investigo aquí?»)**:
  - Botón contextual en el mapa tras hacer clic en una coordenada.
  - Conecta con `/api/ai/scout` y despliega variables candidatas con su contexto ecológico y enlaces a artículos de NASA Earth Observatory.
- **Explicación del detective con evidencia citada**:
  - Conecta con `/api/ai/explain` bajo el veredicto.
  - Selector de dos niveles de lenguaje: **Nivel escolar** (explicación didáctica y accesible) vs. **Nivel universitario** (lenguaje riguroso con términos estadísticos y climáticos).
  - Citas bibliográficas numeradas `[1]`, `[2]` con listado de fuentes oficiales y artículos científicos.
  - Etiqueta visible obligatoria: *«Síntesis asistida por IA a partir de las fuentes citadas»*.
  - Degradación elegante: si el servicio de IA está en modo extractivo o apagado, la interfaz no se rompe y muestra la síntesis a partir de las pruebas estadísticas y tarjetas.
Evidencia:
- Verificado y capturado en Playwright a 1440x900 con pregunta real sobre Piura, generación del plan estructurado, y conmutación entre nivel escolar y universitario con citas enlazadas.
- Archivos actualizados: `src/ui/app.js`, `src/ui/index.html`, `src/ui/styles.css`, `src/ui/i18n.js`.
Falta / riesgos:
- Tarea U5: Modo demostración guiado (casos para mirar con avance automático).
- Tarea U6: Reporte imprimible (/api/report) y auditoría de accesibilidad.
Necesito de otros:
- Claude Omni 2 (`feature/wizard`): integración con los modelos LLM/LoRA en `/api/ai/*`.
