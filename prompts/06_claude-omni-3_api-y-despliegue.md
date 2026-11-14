# 06 · Claude Omni 3 — API v2 y despliegue público

**Rama:** `feature/api` · **Carpetas:** `src/api/`, `tests/api/`, `Dockerfile`, `scripts/smoke_api.py`
**Antes:** lee `prompts/00_LEER_PRIMERO.md` y `docs/CONTRATOS.md` (§6, §7, §11).

## Tu misión
Unes datos, estadística e IA en una API honesta: o devuelve el dato real pedido, o un error claro. Y la dejas en internet para que un juez la abra dentro de tres semanas y funcione.

## Tareas, en orden

### A1 — Esqueleto por contrato (P0, primera hora)
Reescribe `src/api/main.py` con los endpoints del contrato §7 y modelos Pydantic para TimeSeries, AnalysisResult y TrendMap v2.
- **Elimina la sustitución silenciosa** (`main.py:103-108`): si no hay dato → `404`/`502` con `{"error": {"code", "message": {"es","en"}, "hint"}}`.
- Mientras llegan los módulos reales, programa contra sus firmas (§6) con dobles de prueba que leen las muestras reales de `tests/fixtures/real/`, activos solo con `ALLOW_FIXTURES=1`.
  Con `ALLOW_FIXTURES` apagado y sin módulo real → `503`, nunca datos de muestra.
- Validación de entrada: latitud, longitud, caja (oeste < este, sur < norte, tamaño máximo), `variable_id` existente, fechas.
- Título de la API: «EarthTrend Detective API» (sin «NASA» en el nombre).

### A2 — Integración real (P0, en cuanto Antigravity 1 y 2 empujen)
- `/series` → `get_series`; `/analyze` → `get_series` + `analyze_series(ratio_scale, homogeneous_since desde la tarjeta)` + añade `variable`.
- `/trendmap` → `get_grid` + `analyze_grid`. `/compare` → dos análisis + `compare`. `/analyze/upload` → `parse_giovanni_csv` + análisis (límite 5 MB, solo texto).
- `/cases` y `/atlas/{id}` sirven los archivos congelados de `data/cases/` y `data/atlas/` (Hermes 2), validando su `provenance`.
- `/report` → HTML imprimible bilingüe con resultado, método, procedencia y cita.
- Caché de respuestas de análisis en memoria con caducidad; cabeceras `Cache-Control` en lo estático.
- **Prueba de la puerta G1**: `GET /api/analyze?variable_id=T2M&lat=-12.05&lon=-77.03` → `schema: analysis/2`, `provenance.kind: nasa_api`, 540 observaciones.

### A3 — Endpoints de IA (P1)
`/ai/plan`, `/ai/scout`, `/ai/explain`, `/geocode` delegan en `src/detective` (Claude Omni 2). Tiempo máximo 20 s; si el módulo falla → `AI_UNAVAILABLE` y el resto de la app sigue.
`/health` informa `ai_mode` y qué fuentes responden.

### A4 — Robustez (P0)
- Límite de peticiones por IP en los endpoints que llaman a la NASA (para no agotar el cupo de POWER) y exclusión mutua por clave de caché para no duplicar descargas.
- Registro estructurado sin datos personales. CORS abierto solo a `GET`/`POST` necesarios.
- `scripts/smoke_api.py <url_base>`: recorre todos los endpoints con casos reales y un par de errores esperados; imprime una tabla y sale ≠ 0 si algo falla. Lo usa el arquitecto en cada puerta.
- `pytest tests/api -q` en verde (cliente de pruebas de FastAPI; red simulada con las muestras reales).

### A5 — Un solo servicio y despliegue (P0, sábado por la noche; repetir tras cada puerta)
- FastAPI sirve también `src/ui/` en `/`. `Dockerfile` ligero (sin `torch`; la IA en producción va en `AI_MODE=extractive` salvo que el humano configure un `LLM_BASE_URL`).
- Despliega en el hosting que confirme el humano (tiene Railway; el inicio de sesión lo hace él: **no intentes autenticarte tú**). Variables por entorno, nunca en el repo.
- Arranque con caché precalentada para los casos de demostración, de modo que la primera visita del juez sea instantánea.
- Tras desplegar: `python scripts/smoke_api.py https://<url>` y pega la tabla en tu reporte. Prueba la URL en una ventana de incógnito y desde el móvil.

### A6 — Respaldo estático (P1)
`scripts/build_static.py`: genera en `dist/` una copia de la UI que lee solo `data/cases/` y `data/atlas/` (sin API), lista para GitHub Pages.
Es el seguro por si el servidor cae durante las semanas de evaluación.

## Aceptación
- Tabla de `smoke_api.py` en verde en local y en la URL pública.
- `curl` a un punto sin datos o a una variable inexistente → error con código, no un 200 con datos ajenos.
- Latencia: `/analyze` en frío < 6 s, en caché < 300 ms; `/trendmap` de 4°×4° < 6 s.

## Plan B
Si el hosting se atasca más de 45 min: publica el respaldo estático (A6) y deja la API en local para el vídeo. Avisa al arquitecto.

Reporta en `reports/claude-omni-3.md`.
