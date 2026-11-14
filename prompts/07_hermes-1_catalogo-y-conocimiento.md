# 07 · Hermes 1 — Catálogo v2, gazetteer y corpus de conocimiento

**Rama:** `feature/catalog` · **Carpetas:** `data/catalog/`, `data/knowledge/`, `scripts/validate_knowledge.py`, `docs/REFERENCES.md`
**Antes:** lee `prompts/00_LEER_PRIMERO.md` y `docs/CONTRATOS.md` (§8, §9).

## Tu misión
Eres la memoria verificada del detective. Lo que escribas lo leerán estudiantes y lo citará la IA delante de jueces de la NASA.
**Una sola fuente inventada nos descalifica.** Por eso tu regla es mecánica:

> Solo escribes un dato (URL, DOI, resolución, fecha, definición técnica) si abriste la página y lo leíste ahí. Si no lo pudiste comprobar, el campo va `null`. Nunca escribas de memoria.

Descarga con Python (`requests` o `httpx`, con `certifi`); no uses `curl` de Windows ni desactives la verificación de certificados.

## Tareas, en orden

### C1 — Catálogo v2 (P0, objetivo: 3 horas)
Convierte `data/catalog/variables.seed.json` en `data/catalog/variables.json` con el esquema del contrato §8. **No cambies ningún `id`.**
Para cada una de las 15 variables de `live`:
- `names` y `simple_definition` en español e inglés. Definición de ≤ 30 palabras que entienda alguien de 15 años, sin jerga.
- `what_up_means` / `what_down_means`: qué puede indicar subir o bajar, en condicional («puede indicar…»).
- `typical_drivers` (3–5) y `caveats` (2–4), en ambos idiomas.
- `keywords`: ≥ 8 por idioma, incluyendo palabras coloquiales («calor», «bochorno», «sequía», «garúa», «smog»).
- `source`: confirma en la documentación de POWER (https://power.larc.nasa.gov/docs/ y su página de parámetros) de qué modelo o instrumento viene cada parámetro,
  su resolución, su fecha de inicio y **si empalma fuentes distintas** (→ `homogeneous_since`). La semilla trae hipótesis marcadas en `_verify`: confírmalas o corrígelas.
- `verified`: tu nombre, la fecha y la URL donde lo comprobaste.
Aviso obligatorio en las variables de reanálisis: las tendencias pueden verse afectadas por cambios en el sistema de observación.

### C2 — Lugares (P0, en paralelo con C1)
- `data/catalog/gazetteer.json` a partir de GeoNames `cities15000` (comprueba la URL de descarga y la licencia en geonames.org y cítala en `docs/REFERENCES.md`).
  Campos: `name`, `ascii`, `alt_names` (español e inglés), `country`, `lat`, `lon`, `population`. Conserva las ~8 000 ciudades más pobladas **y todas las de Perú**.
- `data/catalog/regions.json`: ~60 regiones naturales con nombre en ambos idiomas, punto central, caja y bioma: Amazonía, Sahel, Mar de Aral, Ártico, Antártida, Groenlandia, Himalaya, Gran Barrera de Coral…
  y de Perú: Cordillera Blanca, Lago Titicaca, Madre de Dios, desierto de Sechura, valle de Ica, Loreto. Cada coordenada, comprobada en una fuente que anotas.

### C3 — Corpus para el RAG (P1, hasta la puerta G2 y seguir ampliando de noche)
`data/knowledge/docs.jsonl`, esquema del contrato §9. Para **cada** documento: descargas la página, compruebas el 200, extraes el texto principal,
guardas 300–1 200 caracteres relevantes, el título tal como aparece, la URL final, la fecha si figura, `fetched_at` y el `sha256` del HTML.

| Tipo | Mínimo | De dónde |
|---|---|---|
| `variable_card` | 1 por variable e idioma | Generadas desde tu catálogo |
| `biome_profile` | 8 | Desierto, selva tropical, estuario o costa, aire sobre una gran ciudad, zona polar, alta montaña y glaciares, sabana, valle agrícola. Qué variables suelen cambiar ahí y por qué, **según las páginas que citas** |
| `nasa_article` | 30 | Artículos de la NASA sobre cambios observados: Earth Observatory («World of Change»), science.nasa.gov, Earthdata, GISS, NSIDC. Incluye al menos 6 sobre Perú o Sudamérica |
| `paper_abstract` | 10 | Artículos de método y de hallazgos. Solo el resumen si la página lo ofrece en abierto; si no, 2 frases tuyas marcadas `"summary_by": "hermes-1"` + el DOI |
| `method_note` | 6 | Qué es una tendencia, una anomalía, el valor p, Mann-Kendall, la pendiente de Sen, la autocorrelación: redactadas a partir de las fuentes citadas |
| `glossary` | 25 términos | Español e inglés |

Pistas para empezar (son pistas: **comprueba cada una antes de usarla**, las direcciones cambian):
`giovanni.gsfc.nasa.gov` · `disc.gsfc.nasa.gov` · `power.larc.nasa.gov/docs` · `data.giss.nasa.gov/gistemp` · `nsidc.org/data/seaice_index` · `gpm.nasa.gov` · `ldas.gsfc.nasa.gov/gldas` · `airs.jpl.nasa.gov` · `modis.gsfc.nasa.gov` · `earthdata.nasa.gov`.
DOIs a comprobar en `https://doi.org/<doi>`: 10.1029/98JD00995 (Weatherhead 1998) · 10.1029/1999JD901105 (Santer 2000) · 10.1016/S0022-1694(97)00125-X (Hamed y Rao 1998) · 10.1080/01621459.1968.10480934 (Sen 1968) · 10.2307/1907187 (Mann 1945) · 10.1175/BAMS-D-15-00267.1 (Wilks 2016) · 10.1175/JCLI-D-16-0758.1 (MERRA-2) · 10.1175/BAMS-85-3-381 (GLDAS) · 10.1029/2018JD029522 (GISTEMP) · 10.21105/joss.01556 (pyMannKendall).
Solo texto, sin imágenes. El contenido de la NASA suele ser de dominio público; el de revistas no: de ahí la regla del resumen.

### C4 — Validador (P0 para la puerta)
`scripts/validate_knowledge.py`:
- Catálogo: están todos los `id` de la semilla; ambos idiomas completos; ninguna definición vacía; cada `doi` y `url` no nulos responden.
- Corpus: campos obligatorios; cada URL responde 200; el título guardado aparece en la página; longitud del texto; sin duplicados; `sha256` presente.
- Sale con código ≠ 0 si algo falla e imprime qué. Pruébalo también con un documento roto a propósito. Pega ambas salidas en tu reporte.

### C5 — Preguntas de oro (P1)
`data/knowledge/golden_questions.jsonl`: 50 preguntas (25 en español, 25 en inglés) como las haría un estudiante, cada una con las 1–2 variables correctas:
`{"question": "...", "lang": "es", "expected_variable_ids": ["PRECTOTCORR"]}`. Escríbelas **antes** de ver qué devuelve el buscador. Las usa Claude Omni 2.

### C6 — Variables de Giovanni (P1, cuando el humano deje los CSV en `data/raw/giovanni/`)
Completa las tarjetas de `planned_giovanni` con el producto y la versión que figuran en la cabecera del CSV y el DOI de la página del producto en GES DISC, comprobado.

### C7 — Referencias para la entrega (P0, domingo 12:00)
`docs/REFERENCES.md` en inglés: todas las fuentes de datos, herramientas, librerías y sus licencias y citas, tal como las pide el formulario
(«Space Agency Partner Data and Other References»). Pide por el canal a cada agente que te diga qué usó.

## Aceptación
- `python scripts/validate_knowledge.py` termina en 0. Salida en el reporte.
- Recuento por tipo de documento y por idioma.
- 5 documentos elegidos al azar por el arquitecto abren y coinciden con lo guardado.

## Plan B
Si un sitio bloquea la descarga, pasa al siguiente: mejor 25 documentos impecables que 60 dudosos. Anota lo que no pudiste comprobar.

Reporta en `reports/hermes-1.md`.
