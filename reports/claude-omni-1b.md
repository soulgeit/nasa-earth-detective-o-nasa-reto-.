<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-1b — 2026-11-15 10:35 hora de Perú (Ronda 6, reporte final)
Rama@commit: feature/catalog@0b65290 · empujado: sí
VERIFICADO: base = `origin/main@e67873e` fusionada en `feature/catalog` (main estaba ocupada por otro worktree; regla 30: no se commitea en main).
VERIFICADO: **168 documentos del corpus con URL viva** → `python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100` → «catalog: 15 available + 10 planned», 168 documentos, **All checks passed**, 0 fallos, exit 0. Las 93 URLs únicas del corpus (81 no-DOI + 12 DOI) caben en el tope de 100: **se comprueban todas**.
VERIFICADO: **29 URLs externas del README + REFERENCES.md comprobadas en vivo**: 27 responden 200; 1 (CSA/SWOT) respondió 200 al reintentar (era intermitente); la AMS responde 200 a `curl`/`requests` con cabeceras de navegador (el 403 de `urllib` es del WAF de Cloudflare, no un enlace roto — el validador oficial la comprueba con `requests` y pasa).
VERIFICADO: 7 enlaces internos del README y 7 archivos citados en REFERENCES.md existen en la base.
VERIFICADO: README **estrictamente en inglés** (0 tokens con tilde, 0 palabras españolas) y sin logotipos ni marcas de la NASA; 1 `<<HUMANO>>` visible (licencia de datos propios; MIT ya en `LICENSE`).
VERIFICADO: README sirve la base de la Ronda 6: 15 variables + 10 planned, 7 casos con sus veredictos reales, 2 atlas, `LICENSE` MIT, URL pública `…-reto-./` (200; sin punto final, 404; subruta `api/cases.json`, 200).
VERIFICADO: `validate_datasets.py data/cases/*/series.json` → 7/7; `check_case_accents.py` → 0 problemas en 8 archivos.
VERIFICADO: suite completa → `python -m pytest -q` → **288 passed, 9 skipped, 0 failed** en 313,01 s (exit 0), sobre `origin/main@e67873e` fusionado. Coincide con la cifra del arquitecto en la Ronda 6.
CORREGIDO (solo documentación, permitido bajo congelación): faltaba en `docs/REFERENCES.md` §3 la fuente **Lenssen et al. (2019), «Improvements in the GISTEMP Uncertainty Model», doi:10.1029/2018JD029522**, que el corpus sí cita (10/10 DOIs del corpus ahora cubiertos).
ROTO / NO HECHO: nada de mi carril. Sin cambios en `src/` (congelación respetada).
Necesito de: humano: confirmar licencia de datos propios (sale de `<<HUMANO>>`) y revocar el token de GitHub al terminar.
Avisos: `gh-pages@94091de` coincide con lo que pide la Ronda 6; la URL de entrega es la de Pages y el README ya lo dice.
<!-- ESTADO:FIN -->

# Reportes de Claude Omni 1b — catálogo y conocimiento

## Ronda 2 — tareas del §6 (catálogo y conocimiento)

### 1. Los 8 fallos del validador — VERIFICADO
Al reproducirlo salieron **5** (el «8» incluía la comprobación de título que ya pasaba):

| Fallo | Causa real | Arreglo |
|---|---|---|
| 4 × `doi.org` con 403 | `doi.org` redirige bien (302); quien da 403 es el HTML del editor (Wiley, Taylor & Francis) a un cliente automático | El validador ahora comprueba **la redirección de doi.org** + **el registro en DataCite/Crossref**, que es la comprobación correcta para un DOI |
| `glossary/statistical_significance` 404 | AMS no tiene ese artículo | Sustituido por el que sí existe: **`significance-test`** («significance test», 200) |
| `glossary/trend` 404 | AMS no tiene «trend» | Sustituido por **`secular_trend`** (200), cuyo título real es «secular variation»; se guarda el título de la página |
| `glossary/biome` 404 | AMS no tiene «biome» | Sustituido por **NASA «Mission: Biomes»** (200), citado como NASA, no como AMS |

```bash
$ python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100
catalog variables: 15
corpus documents: 168
  biome_profile    16
  glossary         64
  method_note      13
  nasa_article     35
  paper_abstract   10
  variable_card    30

All checks passed.
```

### 2. Las dos fuentes nuevas — VERIFICADO
Verificadas en primera persona antes de entrar (no copiadas del informe de Claude Omni 2):

- **Acker et al. (2009)** — `https://ntrs.nasa.gov/citations/20090042747` → 200. Título y abstract se tomaron del
  **registro JSON de NTRS** (`/api/citations/20090042747`), no del PDF de 8,8 MB (no se parsea).
  Entra como `method_note` en inglés: es un caso NASA real de detección de tendencias en series mensuales.
- **SWOT (CSA)** — `https://www.asc-csa.gc.ca/eng/satellites/swot/` → 200 al tercer intento (el host corta la
  conexión de forma intermitente; no se desactivó TLS). Dice literalmente «Launch: December 16, 2022».
  Entra como `nasa_article` (fuente canadiense, citada como CSA; no es NASA).

### 3. Variables de Giovanni aún no disponibles — PROPUESTA
`docs/PROPUESTA_VARIABLES_PLANNED.md`. Resumen: añadir una sección `planned` al catálogo
(las 10 ya definidas en la semilla, `available: false`), y dos líneas en carriles ajenos
(`src/api/catalog.py`, `src/detective/corpus.py`) para que la app pueda decir
«esa variable existe pero aún no está cargada» en vez de no conocerla. No he tocado
ningún carril ajeno.

### 4. `docs/REFERENCES.md` — VERIFICADO
En inglés, con las fuentes de la ronda 2 (NTRS/Acker, CSA/SWOT, NASA Biomes). Se corrigió
`modis.gsfc.nasa.gov` (no abre desde esta máquina) por `modis-land.gsfc.nasa.gov` (200). Cada URL
del archivo se comprobó el 2026-11-14.

### Notas para el integrador
- El corpus pasa de 166 a **168** documentos; el recuento de `nasa_article` sube a 35 (uno es de la CSA).
- Los `summary_by` nuevos dicen `claude-omni-1b`; los antiguos conservan `hermes-1` (historial, no se reescribe).
- Los términos del glosario con página corta conservan el texto original de la página dentro del documento.

---

## Ronda 5 · tarea 1 — `docs/REFERENCES.md` final — LISTO (2026-11-15 07:20 hora de Perú)
Rama@commit: feature/catalog@6e3f44d · empujado: sí
Qué quedó: `docs/REFERENCES.md` reescrito contra el uso real de la base de la Ronda 5:
§1 las fuentes que alimentan los **7 casos y las 15 variables** (POWER/MERRA-2, CERES/SRB, GISTEMP v4,
Sea Ice Index v4, y los dos CSV de Giovanni con su producto exacto), §2 corpus y nomenclátor
(EO, NASA Science/Biomes, POWER parameter dictionary, AMS Glossary, NTRS, CSA, GeoNames, Wikidata,
Nominatim), §3 los 11 DOIs del método, §4 las herramientas **realmente usadas** (incluye Leaflet,
Chart.js, GIBS, OSM, Google Fonts OFL, SmolLM2 Apache-2.0, PEFT) y §5 cómo se valida.
Evidencia — el comando que pide la tarea:

```
$ python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100
catalog: 15 available + 10 planned (planned are not counted as available)
catalog variables: 15
corpus documents: 168
  biome_profile    16
  glossary         64
  method_note      13
  nasa_article     35
  paper_abstract   10
  variable_card    30

All checks passed.
EXIT=0
```

Comprobación en vivo de las URLs que cita el documento (hoy, 2026-11-15): 21 de 23 responden 200.
Las dos que dan 403 son la **portada** `glossary.ametsoc.org/wiki/Welcome` y el HTML del editor Wiley
para `doi.org/10.1029/2023JD040179`; ambos casos quedan explicados en el §5 del documento y se
resuelven por las páginas de término (200) y por el registro de Crossref (OK, 2024).
El DOI de NSIDC se resolvió por DataCite (Fetterer et al., 2025, «Sea Ice Index, Version 4»).

Falta / riesgos: la licencia del código sigue sin decidir (es de claude-omni-3); REFERENCES.md no la
necesita, pero el README deja el hueco `<<HUMANO>>`.

---

## Ronda 5 · tarea 2 — README final — LISTO (2026-11-15 07:45 hora de Perú)
Rama@commit: feature/catalog@(ver commit siguiente) · empujado: sí
Qué quedó: `README.md` final en inglés con: qué es · **URL pública**
(`https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./`, y qué hace y qué no hace el
respaldo) · arranque · cómo comprobarlo (`pytest`, `scripts/gate.py`, smoke, validadores) ·
planificador LoRA opcional con sus cifras juntas (reglas 49/50; LoRA 40/50 GPU / 37/50 CPU; 84,5 %
frente a 15,5 % en los 200 casos, **dicho con la salvedad de que salen del mismo generador**) ·
fuentes de datos · método · límites conocidos · mapa del repo · uso de IA · licencia `<<HUMANO>>`.

Comprobaciones:
- La tabla de casos se leyó de `data/cases/*/analysis.json` y las etiquetas de `src/ui/i18n.js`,
  no de memoria (`SUGGESTIVE` → «Suggestive, not yet certain»; `amazonia-prectotcorr` →
  `NOT_SIGNIFICANT`).
- El respaldo público se abrió hoy: `static-api.js` sirve los **7 casos** (los dos de la Amazonía
  incluidos) y **2 atlas** (`atlas__T2M`, `atlas__GISTEMP_TANOM`), con unidad y veredicto.
  Con el punto final da 200; sin él, 404.
- `python scripts/validate_datasets.py data/cases/*/series.json` → 7/7 válidos.
- `python -X utf8 -I scripts/validate_knowledge.py --offline` → All checks passed.
- `python -m pytest -q` → 276 passed, 9 skipped, 0 failed (Ronda 5); **288 passed, 9 skipped, 0 failed** en la base de la Ronda 6.

Falta / riesgos: la URL principal con la **aplicación completa** (Railway) depende de que el humano
inicie sesión; hoy la URL de entrega es la de Pages y el README lo dice así.


---

## Ronda 6 · informe final — enlaces de `docs/REFERENCES.md` y `README.md` — LISTO (2026-11-15 10:30 hora de Perú)

Base: `origin/main@e67873e` fusionado en `feature/catalog` (en este worktree `main` está
ocupada por otra copia, así que los commits van a mi rama; regla 30).

**Contexto:** `main` ya tenía la edición del arquitecto («Amazon basin» en la tabla de casos)
y la sección «Licence and third-party notices» con `LICENSE` MIT, así que el README y REFERENCES
de la Ronda 5 llegaron a esta base sin conflicto.

### Qué se comprobó y con qué

1. **Corpus completo, 168 documentos, en vivo** — el comando que el README publica:

   ```
   $ python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100
   catalog: 15 available + 10 planned (planned are not counted as available)
   catalog variables: 15
   corpus documents: 168
     biome_profile    16
     glossary         64
     method_note      13
     nasa_article     35
     paper_abstract   10
     variable_card    30

   All checks passed.
   EXIT=0
   ```

   Las 93 URLs únicas del corpus (81 no-DOI + 12 DOI) caben en el tope de 100 del validador,
   así que **no queda ninguna sin comprobar**.

2. **Enlaces externos de los dos documentos** (29 únicos, deduplicados): 27 → 200 directo.
   - **CSA / SWOT** falló una vez por corte de conexión y respondió **200** al reintentar
     (el host corta el primer intento de forma intermitente; no es un enlace roto).
   - **AMS Glossary**: `urllib` recibe 403 del WAF de Cloudflare; con `curl` y cabeceras de
     navegador da **200**, y el validador oficial (que usa `requests`) da 200. No es enlace roto.
   - Wiley/Taylor & Francis siguen devolviendo 403 al cliente automático; el documento ya lo
     explica y el validador resuelve por Crossref/DataCite.

3. **Enlaces internos**: los 7 del README (`LICENSE`, `docs/EVAL_IA.md`, `src/ml/MODEL_CARD.md`,
   `data/lora/DATASET_CARD.md`, `docs/AI_USE_LOG.md`, `docs/REFERENCES.md`,
   `docs/VALIDACION_ESTADISTICA.md`) existen; los 7 archivos que cita REFERENCES.md, también.

4. **README estrictamente en inglés**: 0 tokens con tilde y 0 palabras españolas; un solo
   `<<HUMANO>>` (licencia de nuestros datos derivados); sin logotipos ni marcas de la NASA.
   Las cifras (15 disponibles + 10 planned; los 7 veredictos) se releyeron de
   `variables.json` y de los `analysis.json`, no de memoria.

5. **URL pública**: `https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./` → 200;
   sin el punto final → 404 (queda escrito); `api/cases.json` bajo la subruta → 200 con
   7 casos y las cifras correctas. `origin/gh-pages` = `94091de`, exactamente lo que pide
   `docs/RONDA_6.md` §3.

6. **Corrección de contenido (solo documentación, congelación respetada)**: `docs/REFERENCES.md`
   §3 no listaba **Lenssen et al. (2019), «Improvements in the GISTEMP Uncertainty Model»,
   doi:10.1029/2018JD029522**, que el corpus cita como `paper_abstract`. Añadida. Ahora los
   **10 DOIs únicos del corpus** están cubiertos y la lista del §3 se corresponde con las fuentes
   que el detective puede citar.

7. **Comprobaciones ejecutables del README**: `validate_datasets.py data/cases/*/series.json`
   → 7/7; `check_case_accents.py` → 0 problemas en 8 archivos; suite completa →
   **288 passed, 9 skipped, 0 failed** en 313,01 s (exit 0), idéntica a la cifra del arquitecto.

### ROTO / NO HECHO
Nada de mi carril. No toqué `src/` ni esquemas de datos.

### Pendiente del humano
Confirmar la licencia de nuestros datos derivados (sale del `<<HUMANO>>`; el código ya es MIT)
y revocar el token de GitHub al terminar.
