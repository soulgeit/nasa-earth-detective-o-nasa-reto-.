<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-3a — 2026-11-15 01:15 hora de Perú
Rama@commit: feature/static@dd6b748 · empujado: sí (gh-pages@4e526a2)
VERIFICADO: `python scripts/build_static.py --from-cases` → 7 casos, 7 análisis, 2 atlas, 0 errores (antes horneaba 0 análisis)
VERIFICADO: Playwright sobre servidor estático → 7 casos, veredicto «Significant trend», pendiente +0.159 °C/década, procedencia NASA POWER v2.10.0, gráfica dibujada, 0 errores JS, 0 peticiones fallidas
VERIFICADO: cambio de idioma EN→ES («Frozen cases» → «Casos congelados»); aviso de lo no horneado en ambos idiomas
VERIFICADO: hielo marino sin coordenadas → 200 SIGNIFICANT_STRONG; ningún -9999 dentro de dist/
VERIFICADO: `pytest tests/api/test_static_build.py` → 7 passed (2 pruebas nuevas de regresión)
ROTO / NO HECHO: tarea 3 (regenerar tras la integración de las 10:00) queda pendiente; faltaba esa integración al cerrar
Siguiente paso: regenerar dist/ tras la integración de las 10:00 y repetir el push a gh-pages
Necesito de: humano: activar GitHub Pages en Settings → Pages → rama gh-pages
Avisos para otros carriles: la interfaz (`src/ui/app.js` `openCase`) lee `c.lat`/`c.lon` en la raíz, pero `/api/cases` publica `region: {lat, lon}`: en la app viva el clic de la galería no abre el caso. Lo normalizo en mi build; claude-omni-1 debería arreglarlo en la UI o hermes-2 en el índice.
<!-- ESTADO:FIN -->

# Reporte — claude-omni-3a (respaldo estático)

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
