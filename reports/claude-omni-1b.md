<!-- ESTADO:INICIO -->
## ESTADO — claude-omni-1b — 2026-11-14 17:55 hora de Perú
Rama@commit: feature/catalog@PENDIENTE · empujado: no
VERIFICADO: 8 fallos del validador cerrados → `python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100` → «All checks passed» (168 docs, 0 fallos).
VERIFICADO: 2 fuentes nuevas → Acker et al. 2009 (NTRS 20090042747, abstract real) y SWOT de la CSA (`Launch: December 16, 2022`), ambas con URL 200 y sha256.
VERIFICADO: `docs/REFERENCES.md` en inglés con las fuentes de la ronda 2 y MODIS corregido a `modis-land.gsfc.nasa.gov`.
ESCRITO (sin ejecutar de punta a punta): propuesta de variables planned en `docs/PROPUESTA_VARIABLES_PLANNED.md`; necesita 1 línea en `src/api/catalog.py` y otra en `src/detective/corpus.py` (carriles ajenos).
ROTO / NO HECHO: nada de mi carril; no aplico la propuesta sin aprobación del arquitecto.
Siguiente paso: esperar aprobación del §8; si se aprueba, añado `planned` al catálogo y lo valido.
Necesito de: cfable (arquitecto): aprobar o corregir la propuesta `docs/PROPUESTA_VARIABLES_PLANNED.md`.
Necesito de: claude-omni-3 y claude-omni-2: aplicar la línea de sus cargadores si el arquitecto aprueba.
Avisos para otros carriles: los DOI de editorial dan 403 al bot aunque resuelven; el validador ahora comprueba la redirección de doi.org + el registro en DataCite/Crossref, no el HTML del editor. `README` del corpus: 31 artículos, uno es de la CSA (canadiense), no de la NASA.
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
