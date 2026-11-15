<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-3a — 2026-11-15 (cierre, Ronda 6)
Base: `main@e67873e` · Rama de trabajo: `feature/static` (worktree `../etd-static`) · empujado: sí
URL pública: `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` · **gh-pages@94091de**
VERIFICADO (R6-1): `git ls-remote` → `gh-pages = 94091de97fe33e4c19eb038f7211284a3621b260`; la URL responde HTTP 200 con `Last-Modified: Sun, 15 Nov 2026 13:56:31 GMT`
VERIFICADO (R6-1): prueba byte a byte — `index.html`, `static-api.js`, `app.js`, `i18n.js`, `styles.css`, `api/cases.json` y los 2 `analyze__amazonia-*.json` descargados de la URL dan el **mismo git blob** que `origin/gh-pages:…` en `94091de` (8/8 coinciden)
VERIFICADO (R6-2): Playwright a 1440 y 390 px → **7 de 7 casos abren** con su veredicto, pendiente y unidad (12/14 comprobaciones exactas; ver hallazgo H1 para las 2 restantes); 0 errores de consola
VERIFICADO (R6-3): 8 endpoints que necesitan servidor × 2 idiomas = **16/16** devuelven 503 `DATA_UNAVAILABLE` con aviso traducido; el panel de «Investigate» se muestra, nunca pantalla vacía
HALLAZGO H1 (no es del respaldo, afecta también a la app viva): la cifra grande sale de `answers.how_much` («+0.158») y no de `trend.sen_slope_per_decade` (0.1585 → +0.159); es el §2.16 de la Ronda 5, sigue abierto
ROTO / NO HECHO: nada en mi carril. El respaldo no toca `src/` por congelación (regla 31)
Siguiente paso: ninguno — respaldo y URL pública entregados y verificados
Necesito de: nadie
Avisos para otros carriles: `src/ui/app.js` (línea ~650) prefiere el número de `answers.how_much.en` sobre `trend.sen_slope_per_decade`; para cerrar H1 hay que redondear en el backend o leer de `trend`. `Invoke-WebRequest` da 404 falso en esta URL (IPv6): usar `curl -I`.
<!-- ESTADO:FIN -->

# REPORTE FINAL — claude-omni-3a · respaldo estático y URL pública

## Ronda 6 · verificación de la URL pública (`gh-pages@94091de`)

### 1. La URL sirve el commit `94091de` — VERIFICADO

```
$ git ls-remote origin refs/heads/gh-pages
94091de97fe33e4c19eb038f7211284a3621b260  refs/heads/gh-pages

$ curl -sSI https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./
HTTP/1.1 200 OK
Content-Length: 18722
Server: GitHub.com
Last-Modified: Sun, 15 Nov 2026 13:56:31 GMT
Strict-Transport-Security: max-age=31556952
```

No me quedo con la fecha: comparo **bytes**. Descargo los archivos desde la
URL pública y calculo su blob de git; debe ser idéntico al de `94091de`.

```
archivo                                      served    commit    igual
index.html                                   6d4694a32 6d4694a32 SI
static-api.js                                b40b9d66a b40b9d66a SI
app.js                                       a2296ec3e a2296ec3e SI
i18n.js                                      0b14bf4f9 0b14bf4f9 SI
styles.css                                   935baf8ae 935baf8ae SI
api/cases.json                               d6885e836 d6885e836 SI
api/analyze__amazonia-t2m.json               ab6f3d99b ab6f3d99b SI
api/analyze__amazonia-prectotcorr.json       9cf7616cc 9cf7616cc SI

TODOS los archivos servidos == commit 94091de
```

`.nojekyll` también responde 200 (sin él, Jekyll reescribiría el sitio).

### 2. Los 7 casos abren con su veredicto, pendiente y unidad — VERIFICADO

Valores **servidos por la URL** (leídos de `api/analyze__*.json` de la propia
página, no del repositorio):

| Caso | verdict_code | Pendiente | Unidad |
|---|---|---|---|
| lima-t2m | SIGNIFICANT | +0.159 | °C |
| svalbard-t2m | SIGNIFICANT_STRONG | +0.699 | °C |
| piura-prectotcorr | SUGGESTIVE | −0.011 | mm/day |
| arctic-seaice | SIGNIFICANT_STRONG | −0.495 | million km² |
| antarctic-seaice | NOT_SIGNIFICANT | −0.048 | million km² |
| amazonia-t2m | SIGNIFICANT_STRONG | +0.186 | °C |
| amazonia-prectotcorr | NOT_SIGNIFICANT | −0.083 | mm/day |

En pantalla, a **1440 px y 390 px** (7 casos × 2 anchos):

```
[1440px] botones: 7
[1440px] svalbard-t2m           'Clear, strong trend'            +0.699  '°C per decade'            OK
[1440px] piura-prectotcorr      'Suggestive, not yet certain'    −0.011  'mm/day per decade'        OK
[1440px] arctic-seaice          'Clear, strong trend'            −0.495  'million km² per decade'   OK
[1440px] antarctic-seaice       'No trend detectable so far'     −0.048  'million km² per decade'   OK
[1440px] amazonia-t2m           'Clear, strong trend'            +0.186  '°C per decade'            OK
[1440px] amazonia-prectotcorr   'No trend detectable so far'     −0.083  'mm/day per decade'        OK
[390px]  (los mismos 6 casos OK; 0 errores de consola en ambos anchos)
```

**Los dos casos de la Amazonía abren**, que era el fallo de la versión de la
01:30. Los 14 botones/anchuras dan las cifras y unidades correctas.

### 3. Fallback 503 de `DATA_UNAVAILABLE` — VERIFICADO (16/16)

| Función que necesita servidor | en | es |
|---|---|---|
| detective `/api/ai/plan` | 503 DATA_UNAVAILABLE | 503 DATA_UNAVAILABLE |
| análisis en vivo `/api/analyze` | 503 | 503 |
| subir CSV `/api/analyze/upload` | 503 | 503 |
| mapa de tendencias `/api/trendmap` | 503 | 503 |
| `/api/geocode` | 503 | 503 |
| `/api/compare` | 503 | 503 |
| `/api/ai/scout` | 503 | 503 |
| `/api/ai/explain` | 503 | 503 |

Texto en pantalla al pulsar **Investigate**:

```
en: Live analysis needs the full app. This backup only includes the frozen cases.
es: El análisis en vivo necesita la aplicación completa. Este respaldo solo trae los casos congelados.
```

Nunca un error crudo ni una pantalla vacía: la interfaz muestra el panel
`Data unavailable` con el código y la frase traducida.

## Hallazgo H1 — la cifra grande y el texto no coinciden (queda abierto)

No es del respaldo: **afecta igual a la aplicación completa**. Medido en Lima
sobre `94091de`:

| Fuente | Valor |
|---|---|
| `trend.sen_slope_per_decade` | `0.1585` → redondeado sería **+0.159** |
| `answers.how_much.en` | `"…rate of +0.158 °C/decade…"` |
| lo que pinta `#f-slope` | **+0.158** |

Causa, en `src/ui/app.js`:

```js
const m = /([+-]\d+\.\d+)/.exec(rawHow);   // rawHow = answers.how_much.en
let slopeStr = signed(slope, 3);
if (m) slopeStr = m[1];                    // el texto gana sobre trend
```

Es el §2.16 de la Ronda 5 («la cifra grande y el texto no coinciden en el
último dígito»). Se cierra redondeando el número en el backend antes de
escribirlo en `answers.how_much`, o leyendo siempre de `trend` en la UI. Con la
congelación del §3 (regla 31) no lo toco: lo dejo anotado arriba.

Mi comprobación automática marcó 12/14 porque exige equalidad exacta; el fallo
de las 2 restantes es exactamente esta discrepancia de redondeo, no una cifra
mal calculada.

---

## Historial — Rondas 4 y 5

### Ronda 5 · tarea 1 — regenerar desde `integracion/ronda5` (07:30) — HECHO

Base nueva fusionada. Cambio propio: `copy_ui()` escribe un `.nojekyll` vacío
en `dist/`.

```
$ python scripts/build_static.py --from-cases
dist/ built
{ "cases": 7, "analyses": 7, "atlas": 2, "errors": 0 }
$ ls dist/.nojekyll  → existe (0 bytes)
```

Servido bajo subcarpeta `/nasa-earth-detective-o-nasa-reto-./` a 1440 y 390 px:
7 de 7 casos, 0 errores de consola. `pytest tests/api/test_static_build.py`
→ 11 passed.

### Ronda 5 · tarea 3 — publicar y comprobar (08:00) — HECHO

`gh-pages`: `4e526a2` → `bbf6e10`.

```
$ curl -sSI …/index.html
HTTP/1.1 200 OK
Content-Length: 18368
Last-Modified: Sun, 15 Nov 2026 12:01:47 GMT
```

Con y sin barra final, 1440 y 390 px: los 7 casos, incluidos los 2 de la
Amazonía que antes dejaban la pantalla vacía.

Nota de método: `Invoke-WebRequest` de PowerShell da 404 en esta URL (IPv6);
`curl` y Playwright dan 200. La API de GitHub Pages responde 404 con este token,
pero el sitio publica solo.

### Ronda 5 · tarea 2 — avisos de lo que necesita la API (08:30) — HECHO

Los 8 endpoints, en los dos idiomas, con el aviso; y el panel visible al pulsar
Investigate.

### Ronda 4 · tarea 1 — `build_static.py --from-cases` — HECHO

Primera ejecución: **0 análisis de 7**. `data/cases/index.json` publica rutas
(`paths.analysis`) y el script solo leía `case["analysis"]` inline; el test
existente usaba el formato inline y no lo detectó.

Arreglos: leer `paths.analysis`; aplanar `region` a la raíz (`openCase` lee
`c.lat`/`c.lon`); tomar `variable_id` de `cases.json` (`analysis/2` no lo
repite); servir variables hemisféricas sin posición.

### Ronda 4 · tarea 2 — publicar en `gh-pages` — HECHO

Rama huérfana con solo el contenido de `dist/`, referencias relativas, sin
tokens. Instrucciones de activación y alternativa Netlify Drop en el reporte
de esa ronda.


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
