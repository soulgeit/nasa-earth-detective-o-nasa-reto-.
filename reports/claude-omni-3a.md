<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-3a — 2026-11-15 07:05 hora de Perú
Rama@commit: feature/static@8eebe38 · empujado: sí · **gh-pages@bbf6e10** (antes 4e526a2)
VERIFICADO (R5 · tarea 1): `python scripts/build_static.py --from-cases` → 7 casos, 7 análisis, 2 atlas, 0 errores; `.nojekyll` presente en dist/
VERIFICADO (R5 · tarea 1): Playwright sirviendo dist/ bajo subcarpeta `/nasa-earth-detective-o-nasa-reto-./` a 1440 y 390 px → **los 7 casos abren** con su verdict_code y su pendiente, con unidad, **0 errores de consola**
VERIFICADO (R5 · tarea 1): cifras de la UI = `analysis.json` en los 7: lima +0.159 SIGNIFICANT · svalbard +0.699 SIGNIFICANT_STRONG · piura −0.011 SUGGESTIVE · arctic −0.495 SIGNIFICANT_STRONG · antarctic −0.048 NOT_SIGNIFICANT · amazonia-t2m +0.186 SIGNIFICANT_STRONG · amazonia-prectotcorr −0.083 NOT_SIGNIFICANT
VERIFICADO (R5 · tarea 1): `pytest tests/api/test_static_build.py` → 11 passed (2 pruebas nuevas: `.nojekyll` y `GET /api/cases/<id>` en el shim)
VERIFICADO (R5 · tarea 3): URL pública `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` → HTTP 200, `Last-Modified: Sun, 15 Nov 2026 12:01:47 GMT` (sello nuevo); con y sin barra final, a 1440 y 390 px: **7 de 7 casos abren con veredicto, pendiente y unidad, 0 errores de consola**; los 2 de la Amazonía ya abren (+0.186 °C/década y −0.083 mm/día)
VERIFICADO (R5 · tarea 2): los 8 endpoints que necesitan la API (plan, analyze, upload, trendmap, geocode, compare, scout, explain) → 503 `DATA_UNAVAILABLE` con el aviso en **es y en**; al pulsar «Investigate» sale el panel con `<Code: DATA_UNAVAILABLE>` + mensaje traducido, nunca pantalla vacía
ROTO / NO HECHO: tarea 4 (regenerar tras las integraciones de 10:00 y 15:00) — no hay integración nueva todavía a las 07:45
Siguiente paso: esperar la integración de las 10:00, repetir la tarea 1 y volver a empujar `gh-pages`
Necesito de: nadie
Avisos para otros carriles: GitHub rechaza la API de Pages para este token (404 en `/pages`), pero el sitio publica solo; la comprobación fiable es `curl -I` + Playwright, no `Invoke-WebRequest` (falla por IPv6). `analysis.json` no lleva `variable.unit`: la pone el catálogo (`_decorate_analysis`).
<!-- ESTADO:FIN -->

## Estado anterior (Ronda 4, 01:15)

**Antes:** 7 casos, veredicto «Significant trend», pendiente +0.159 °C/década, procedencia NASA POWER v2.10.0, gráfica dibujada, cambio de idioma EN↔ES, hielo marino 200 SIGNIFICANT_STRONG, ningún −9999, 7 passed.

# Reporte — claude-omni-3a (respaldo estático)

## RONDA 5 — la URL pública (GitHub Pages)

### Tarea 1 — regenerar desde `integracion/ronda5` (07:30) — HECHO

Base nueva: `feature/static` fusionado con `origin/integracion/ronda5`.
Cambio propio: `copy_ui()` escribe un `.nojekyll` vacío en `dist/` (sin él,
GitHub Pages pasa el sitio por Jekyll).

```
$ python scripts/build_static.py --from-cases
dist/ built
{ "cases": 7, "analyses": 7, "atlas": 2, "errors": 0 }
$ ls dist/.nojekyll        →  existe (0 bytes)
```

Servido **bajo subcarpeta** `/nasa-earth-detective-o-nasa-reto-./` (como lo
publica GitHub Pages), Playwright a 1440 y 390 px, un caso por carga:

| Caso | Veredicto en pantalla | Pendiente | Unidad | `analysis.json` |
|---|---|---|---|---|
| lima-t2m | Significant trend | +0.159 | °C per decade | 0.1585 SIGNIFICANT |
| svalbard-t2m | Clear, strong trend | +0.699 | °C per decade | 0.6986 SIGNIFICANT_STRONG |
| piura-prectotcorr | Suggestive, not yet certain | −0.011 | mm/day per decade | −0.011 SUGGESTIVE |
| arctic-seaice | Clear, strong trend | −0.495 | million km² per decade | −0.4953 SIGNIFICANT_STRONG |
| antarctic-seaice | No trend detectable so far | −0.048 | million km² per decade | −0.0481 NOT_SIGNIFICANT |
| amazonia-t2m | Clear, strong trend | +0.186 | °C per decade | 0.1864 SIGNIFICANT_STRONG |
| amazonia-prectotcorr | No trend detectable so far | −0.083 | mm/day per decade | −0.0829 NOT_SIGNIFICANT |

**7 de 7 abren, 0 errores de consola.** `pytest tests/api/test_static_build.py`
→ **11 passed**.

### Tarea 3 — comprobar la URL pública (08:00) — HECHO

`gh-pages`: `4e526a2` → **`bbf6e10`**.

```
$ curl -sSI https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./index.html
HTTP/1.1 200 OK
Content-Length: 18368
Last-Modified: Sun, 15 Nov 2026 12:01:47 GMT
```

Con barra final y sin ella, a 1440 y 390 px: **7 de 7 casos** con su veredicto,
su pendiente y su unidad; los dos de la Amazonía, que en `4e526a2` dejaban la
pantalla vacía, ya abren. **0 errores de consola.**

Nota de método: `Invoke-WebRequest` de PowerShell da 404 en esta URL (resuelve
por IPv6); `curl` y Playwright dan 200. La API de GitHub Pages responde 404 con
este token, pero el sitio publica solo.

### Tarea 2 — avisos de lo que necesita la API (08:30) — HECHO

Los 8 endpoints que dependen del servidor (`/api/ai/plan`, `/api/analyze`,
`/api/analyze/upload`, `/api/trendmap` fuera de los 2 atlas, `/api/geocode`,
`/api/compare`, `/api/ai/scout`, `/api/ai/explain`) devuelven **503
`DATA_UNAVAILABLE`** con el aviso en los dos idiomas:

```
en: Live analysis needs the full app. This backup only includes the frozen cases.
es: El análisis en vivo necesita la aplicación completa. Este respaldo solo trae los casos congelados.
```

Y al pulsar **Investigate** en la interfaz sale el panel de error, no una
pantalla vacía:

```
[en] panel visible=True  resultado_oculto=True
     Code: DATA_UNAVAILABLE
     Live analysis needs the full app. This backup only includes the frozen cases.
     The interface never invents data. When the analysis service is down you can still open a frozen, real case.
[es] panel visible=True  resultado_oculto=True
     Código: DATA_UNAVAILABLE
     El análisis en vivo necesita la aplicación completa. Este respaldo solo trae los casos congelados.
     La interfaz nunca inventa datos. Si el servicio de análisis está caído, aún puedes abrir un caso real congelado.
```

### Tarea 4 — repetir tras cada integración (10:00 y 15:00) — PENDIENTE

A las 07:45 no hay commits nuevos en `integracion/ronda5` ni en `main`.

---

# Historial — Ronda 4

## Tarea 1 — `build_static.py --from-cases` (Dom 02:30) — HECHO

Primera ejecución: **0 análisis de 7**. `data/cases/index.json` publica rutas
(`paths.analysis`) y el script solo leía `case["analysis"]` inline; el único
test existente usaba el formato inline, así que nunca lo detectó.

Arreglos en `scripts/build_static.py`:

1. `build_from_cases()` lee `paths.analysis` (acepta también el inline viejo).
2. `_normalize_case()` aplana `region` a la raíz: `openCase()` de la UI lee
   `c.lat`/`c.lon`, no `c.region.lat`. Sin esto la galería se veía pero el clic
   no abría nada.
3. `_bake_index()` toma `variable_id` de `cases.json` porque `analysis/2` no
   repite `variable.id`; sin él el shim no podía emparejar la petición.
4. Variables hemisféricas/globales (hielo marino, GISTEMP) sin posición se
   sirven por variable (antes `position` salía `"None,None"` y caían en 503).
5. Aviso explícito, en los dos idiomas: «Live analysis needs the full app».

Evidencia:

```
$ python scripts/build_static.py --from-cases
dist/ built
{ "cases": 7, "analyses": 7, "atlas": 2, "errors": 0 }

$ pytest -q tests/api/test_static_build.py
7 passed
```

### Verificación en navegador (Playwright, Chromium headless, 1440×900)

Servidor estático local sobre `dist/`:

```
TITLE: EarthTrend Detective
CASES rendered: 7
VERDICT: Significant trend
SLOPE: +0.159
PROVENANCE: NASA POWER v2.10.0
CHART canvas: 1
EN 'Frozen cases': 1  →  ES cases h2: Casos congelados
PROBE status: 503  code: DATA_UNAVAILABLE
  en: Live analysis needs the full app. This backup only includes the frozen cases.
  es: El análisis en vivo necesita la aplicación completa. Este respaldo solo trae los casos congelados.
HEALTH: {"status":"static","version":"static-1","ai_mode":"off",...}
ICE status: 200  verdict: SIGNIFICANT_STRONG
JS ERRORS: none
FAILED REQUESTS: none
```

Ningún `-9999` dentro de `dist/` (`Select-String` sobre `dist/api/*.json` y
`dist/static-api.js`: sin coincidencias).

## Tarea 2 — publicar en `gh-pages` (Dom 04:00) — HECHO

Rama `gh-pages` creada huérfana (sin historia del código) con **solo** el
contenido de `dist/`. Commit `4e526a2`. Empujada al remoto.

```
$ git ls-remote --heads <origin> | grep gh-pages
4e526a2375c3a18f09f65dc6a54d44241d0b1039  refs/heads/gh-pages
```

Contenido publicado: `index.html`, `app.js`, `i18n.js`, `styles.css`,
`static-api.js` y `api/` (12 archivos JSON: health, casos, catálogo y 2 atlas).
Todas las referencias del HTML son **relativas**, así que funciona aunque
GitHub Pages lo sirva bajo una subruta. Sin tokens dentro de la rama.

### Clics para activar GitHub Pages

1. Abre `https://github.com/soulgeit/nasa-earth-detective-o-nasa-reto-/settings/pages`
2. En **Source** elige **Deploy from a branch**.
3. **Branch**: `gh-pages` · **Folder**: `/ (root)` → **Save**.
4. Espera 1–2 minutos; la URL aparece en esa misma página:
   `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-/`

⚠️ **El nombre del repositorio termina en punto** (`…-reto-.`). GitHub puede
generar una URL con el punto final, que algunos navegadores y servidores
normalizan o recortan. Si al abrirla no carga, la alternativa inmediata:

### Alternativa sin servidor: Netlify Drop

1. Comprime `dist/` en `dist.zip` (o arrastra la carpeta entera).
2. Entra en `https://app.netlify.com/drop` y arrastra `dist.zip`.
3. Te da una URL pública al instante, sin cuenta obligatoria.

El respaldo se comporta igual: casos congelados sí, análisis en vivo no
(«Live analysis needs the full app»).

## Tarea 3 — regenerar tras la integración de las 10:00 (Dom 10:30) — PENDIENTE

Al cerrar esta ronda faltaba la integración de las 10:00. Cuando `main` esté
integrado: `git -C ../etd-static merge origin/main`, volver a correr
`python scripts/build_static.py --from-cases` y repetir el push a `gh-pages`
con el mismo procedimiento (worktree `../etd-pages`, copiar `dist/`, commit).
Evidencia exigida: `Select-String -Pattern '-9999'` sobre `dist/api/*.json`
sin coincidencias.

## Pruebas añadidas (`tests/api/test_static_build.py`)

| Prueba | Qué fija |
|---|---|
| `test_build_creates_complete_dist` | hornea el análisis global además del puntual (regresión del bug de `paths`) |
| `test_shim_contains_baked_index_with_position` | `variable_id` y `position` correctos; el global va con `position: None` |
| `test_global_case_matches_without_position` | el shim sirve variables sin lat/lon |
| `test_cases_are_flattened_for_the_ui` | `c.lat`/`c.lon`/`region_name` en la raíz |
