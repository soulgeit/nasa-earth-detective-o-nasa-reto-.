# RONDA 7 — Huiracocha IA: RAG de las cinco ciudades (domingo 15 nov, 14:15 → 19:00)

> Manda sobre `RONDA_6.md` solo en lo que dice aquí: la congelación de código sigue
> para todo el mundo **menos** para los carriles de esta ronda, y cada carril solo
> puede escribir en sus propios archivos. Entrega («Submit») a las 20:00.

## 1. Qué pidió el dueño del proyecto

1. La IA se llama **Huiracocha IA** y tiene que conversar (hoy «hola» no recibe respuesta).
2. La caja de entrada es pobre y hay pocas variables: se amplían las dos.
3. El RAG tiene que estar **bien nutrido para cinco ciudades**: Lima, Huancayo,
   Andahuaylas, Ica y Ayacucho. Hoy el corpus casi no las conoce (medido sobre
   `data/knowledge/docs.jsonl`: Lima 1 documento, Ica 1, las otras tres 0).

Los puntos 1 y 2 son del arquitecto (`src/`, `data/catalog/`). El punto 3 es de los
ocho carriles de abajo, que trabajan **a la vez**.

## 2. Por qué esta vez nadie se pisa

El corpus ya no es un único archivo. La app lee, además de `docs.jsonl`:

```
data/knowledge/regions/<ciudad>.jsonl      lo que dicen las fuentes oficiales de esa ciudad
data/knowledge/facts/<ciudad>.jsonl        tendencias calculadas por nuestro propio motor
data/knowledge/resources/<tema>.jsonl      portales de datos, métodos y tutoriales
```

**Un archivo = un único carril que escribe.** Como nadie comparte archivo, un
`rebase` sobre `main` nunca puede dar conflicto. Si te da conflicto, tocaste algo
que no es tuyo: `git rebase --abort` y deshaz ese cambio.

La app carga estos archivos a la defensiva (una fila mala se salta y no tumba la
IA), así que la puerta estricta es `python scripts/validate_fragments.py`: sin
verde ahí no se empuja.

### Carriles

| Carril | Rama | Archivos propios (nadie más escribe aquí) |
|---|---|---|
| `rag-lima` | `rag/lima` | `data/knowledge/regions/lima.jsonl`, `reports/rag-lima.md` |
| `rag-huancayo` | `rag/huancayo` | `data/knowledge/regions/huancayo.jsonl`, `reports/rag-huancayo.md` |
| `rag-andahuaylas` | `rag/andahuaylas` | `data/knowledge/regions/andahuaylas.jsonl`, `reports/rag-andahuaylas.md` |
| `rag-ica` | `rag/ica` | `data/knowledge/regions/ica.jsonl`, `reports/rag-ica.md` |
| `rag-ayacucho` | `rag/ayacucho` | `data/knowledge/regions/ayacucho.jsonl`, `reports/rag-ayacucho.md` |
| `rag-datos` | `rag/datos` | `data/knowledge/facts/*.jsonl`, `data/cities/**`, `scripts/build_city_facts.py`, `tests/detective/test_city_facts.py`, `reports/rag-datos.md` |
| `rag-recursos` | `rag/recursos` | `data/knowledge/resources/*.jsonl`, `reports/rag-recursos.md` |
| `rag-qa` | `rag/qa` | `data/knowledge/golden_cities.jsonl`, `scripts/eval_cities.py`, `tests/detective/test_golden_cities.py`, `reports/rag-qa.md`, `reports/qa/ronda7-*.md` |
| arquitecto | `integracion/ronda7` | `src/**`, `data/catalog/**`, `data/knowledge/docs.jsonl`, `docs/**`, el resto de `tests/**` y `scripts/**` |

Nadie salvo el arquitecto toca `src/`, `data/catalog/`, `docs.jsonl` ni las pruebas
que ya existen. Si necesitas un cambio ahí, escríbelo en tu reporte bajo
`Necesito de: arquitecto`.

### Mejorar el trabajo de otro sin pisarlo

- **Nunca edites el archivo de otro carril**, ni para corregir una tilde.
- ¿Tienes algo mejor para una ciudad que no es la tuya? Créalo en un archivo
  **tuyo**: `data/knowledge/regions/<ciudad>-por-<tu-carril>.jsonl` (ids
  `region-<ciudad>-por-<tu-carril>-…`). La app lo carga igual.
- ¿Tu documento reemplaza a uno peor (fuente secundaria, cifra vieja, enlace
  roto)? Añade `"supersedes": ["<id del otro>"]` y `"supersedes_reason": "…"`.
  La app retira el antiguo sin que nadie haya editado el archivo ajeno. El
  validador rechaza un `supersedes` sin motivo o hacia un id que no existe.
- ¿Viste un error en el archivo de otro y no tienes reemplazo? Déjalo en
  `reports/handoff/<tu-carril>--para--<su-carril>.md` (archivo nuevo, tuyo) y
  avisa en `#general`. El dueño lo corrige.
- A partir de las **18:30** (congelación de datos) el único que corrige
  cualquier fragmento es `rag-qa`; los demás solo le pasan notas.

## 3. Contrato de un documento (una línea JSON por documento)

```json
{"id": "region-huancayo-heladas-01", "type": "region_note",
 "title": "Heladas en Huancayo y el valle del Mantaro",
 "url": "https://…página exacta de donde sale el dato…",
 "publisher": "SENAMHI", "date": "2023-06", "lang": "es",
 "text": "200 a 1500 caracteres. Nombra la ciudad. Cifras con unidad y periodo.",
 "variables": ["T2M"], "places": ["huancayo"],
 "license": "Gobierno del Perú — información pública",
 "fetched_at": "2026-11-15T19:30:00Z",
 "sha256": "<sha256 del texto en UTF-8>",
 "is_quotation": false, "summary_by": "rag-huancayo"}
```

Reglas que el validador comprueba (y por tanto no se discuten):

1. `id` empieza por `region-<archivo>-`, `fact-<archivo>-` o `res-<archivo>-` y no
   se repite en todo el corpus.
2. `type`: en `regions/` → `region_note`, `nasa_article` o `paper_abstract`; en
   `facts/` → `region_note`; en `resources/` → `method_note`, `nasa_article`,
   `glossary` o `paper_abstract`.
3. En `regions/` y `facts/` el **título y el texto nombran la ciudad** y `places`
   la incluye: así la explicación de la app encuentra el documento del lugar.
4. `variables` solo lleva ids que existan en `data/catalog/variables.json` en el
   momento de empujar (el catálogo crece durante la ronda: `git fetch` antes de
   validar). Lista vacía si el documento no trata de una variable.
5. `sha256` es el del texto; `fetched_at` en UTC con `Z`; `url` absoluta.
6. `is_quotation: true` **solo** si el texto es copia literal de la página. Un
   resumen con tus palabras lleva `false` y `summary_by` con tu carril.
7. Ningún texto se repite entre archivos.

Reglas que el validador no puede comprobar y que `rag-qa` revisa por muestreo:

8. **Nada inventado.** Cada cifra, fecha y nombre está en la página de `url`.
   Si no encuentras la fuente primaria, el documento no existe.
9. Fuentes admitidas, por orden: NASA (Earth Observatory, Earthdata, GES DISC,
   POWER, SERVIR), NOAA, SENAMHI, ANA, INAIGEM, IGP, ENFEN, MINAM, MIDAGRI, INEI,
   CENEPRED, INDECI, gobiernos regionales, ONU (OMM, FAO, Banco Mundial CCKP) y
   artículos con DOI. Fuera: blogs, foros, prensa sin fuente primaria,
   enciclopedias colaborativas y cualquier página generada por IA.
10. Derechos: de NASA, NOAA y documentos públicos del Estado peruano se puede
    citar literal. De revistas, prensa y webs con copyright, **resumen propio**
    y breve con el enlace (o el DOI) como fuente.
11. Raspado con educación: respeta `robots.txt`, una petición por segundo por
    servidor, sin saltar inicios de sesión ni captchas. Las descargas crudas
    (HTML, PDF) se quedan **fuera del repo**.
12. Español primero (lo usa el público de la demo) y, de lo más importante,
    también una versión en inglés como documento aparte (`lang: "en"`).

## 4. Qué significa «ciudad bien nutrida»

Mínimo por ciudad al cierre: **50 documentos válidos** (≥ 35 en español, ≥ 10 en
inglés), **≥ 12 páginas fuente distintas** de **≥ 6 instituciones**, y los doce
temas cubiertos con al menos tres documentos cada uno:

| # | Tema | Variables del catálogo que suele llevar |
|---|---|---|
| 1 | Ubicación, altitud, relieve, cuenca | — |
| 2 | Temperatura normal: medias, máximas y mínimas por estación del año | `T2M`, `TS` |
| 3 | Lluvia: estacionalidad, totales, garúa, años secos y húmedos | `PRECTOTCORR`, `GPM_IMERG_PRECIP` |
| 4 | Extremos: heladas, friajes, olas de calor, huaicos, inundaciones, granizo, sequías (con fecha) | `T2M`, `PRECTOTCORR` |
| 5 | El Niño y La Niña: efectos locales documentados (1982-83, 1997-98, 2017, 2023-24) | `PRECTOTCORR`, `T2M` |
| 6 | Agua: ríos, glaciares y nevados, lagunas, acuíferos, embalses | `SNODP`, `GWETTOP`, `EVLAND`, `GLDAS_RUNOFF` |
| 7 | Agricultura: cultivos, calendario agrícola, riesgo climático | `GWETTOP`, `PRECTOTCORR`, `T2M` |
| 8 | Aire y radiación: calidad del aire, polvo, radiación UV, nubosidad | `AOD_55`, `TO3`, `CLOUD_AMT`, `ALLSKY_SFC_SW_DWN`, `OMI_NO2_TROP` |
| 9 | Suelo y vegetación: uso del suelo, deforestación, expansión urbana | `MODIS_NDVI`, `GWETTOP`, `TS` |
| 10 | **Tendencias ya publicadas** (estudios, SENAMHI, INAIGEM, IPCC): cifra, unidad y periodo exactos | la que corresponda |
| 11 | Estaciones y datos: estaciones SENAMHI de la zona, altitud, qué miden; límites de una celda satelital de ~50 km | — |
| 12 | Población expuesta y sectores afectados | — |

El tema 10 vale doble: es lo que permite a Huiracocha IA comparar «lo que
calculamos» con «lo que ya se publicó». Al menos ocho documentos por ciudad.

`python scripts/validate_fragments.py --stats` imprime la tabla de avance.

## 5. Tareas por carril

### `rag-lima`, `rag-huancayo`, `rag-andahuaylas`, `rag-ica`, `rag-ayacucho`
Nutrir su ciudad según §3 y §4. Pistas de por dónde empezar (comprobar siempre
en la fuente): Lima — garúa e inversión térmica, ríos Rímac, Chillón y Lurín,
calidad del aire, El Niño Costero 2017; Huancayo — valle del Mantaro, nevado
Huaytapallana, heladas, observatorio de Huayao (IGP); Andahuaylas — valle del
Chumbao, laguna de Pacucha, heladas y sequías en Apurímac; Ica — acuífero y
agroexportación, río Ica y huaicos, vientos Paracas, radiación solar;
Ayacucho (Huamanga) — sistema Cachi, sequías, heladas, nevado Razuhuillca.
Al terminar los mínimos, reforzar otra ciudad con un archivo
`<ciudad>-por-<carril>.jsonl` (§2).

### `rag-datos`
Tendencias calculadas, no leídas: para cada una de las cinco ciudades (punto del
gazetteer) y **cada variable disponible del catálogo en el momento de ejecutar**,
llamar en proceso a `src.api.service.analyze(variable_id, lat=…, lon=…, place=…)`
— el mismo camino que `/api/analyze` — y:
1. guardar el resultado íntegro en `data/cities/<ciudad>/<VARIABLE>.analysis.json`;
2. escribir en `data/knowledge/facts/<ciudad>.jsonl` un documento por variable y
   por idioma con pendiente y unidad por década, valor p de Mann-Kendall,
   intervalo de confianza, periodo, número de observaciones y el veredicto **con
   las mismas cifras y el mismo redondeo que publica la app** (cópialas del JSON,
   no las recalcules), más un documento resumen «Qué está cambiando en <Ciudad>»
   que ordena las variables por significancia;
3. `url` = el enlace público reproducible de ese análisis
   (`https://huiracochaia.soulgeit.com/api/analyze?variable_id=…&lat=…&lon=…`),
   `generated_from: "scripts/build_city_facts.py"`, `is_quotation: false`;
4. una prueba que falle si un número del texto no está en el JSON congelado.
El script se vuelve a ejecutar cada vez que el catálogo gane variables. Una
variable que el proveedor no entrega para ese punto se anota en el reporte, no
se rellena.

### `rag-recursos`
Convertir en documentos los recursos del reto (lista en §8) y los métodos que la
app usa: qué ofrece cada portal, qué variables y resolución, cómo se saca una
serie temporal, qué exige (cuenta, token). Primero `grep` de cada URL en
`docs.jsonl`: lo que ya exista y esté bien no se repite; lo que esté pobre se
mejora con `supersedes`. Además, notas de método para público escolar en español
e inglés (tendencia, Mann-Kendall, pendiente de Theil-Sen, valor p, intervalo de
confianza, autocorrelación, estacionalidad, «no significativo no es lo mismo que
no cambia»), cada una con fuente primaria abierta (NASA, NOAA, USGS, OMM).

### `rag-qa`
1. `data/knowledge/golden_cities.jsonl`: ≥ 12 preguntas reales por ciudad (60 en
   total, español e inglés) con la ciudad, la variable y el tema esperados.
2. `scripts/eval_cities.py`: mide por ciudad si `retrieve()` devuelve entre los
   tres primeros un documento de esa ciudad y de ese tema; tabla en el reporte
   después de cada tanda de `main`.
3. Muestreo de veracidad: 10 documentos por carril y tanda; abrir la `url` y
   comprobar que la cifra está ahí. Lo que falle va al dueño por `handoff`.
4. Duplicados y contradicciones entre carriles (dos cifras distintas para lo
   mismo): decide cuál queda, con motivo.
5. Desde las 18:30, único carril que corrige fragmentos. 18:45, informe final
   con la tabla de cobertura y la lista de lo que NO se pudo verificar.

## 6. Cómo trabajar y cómo empujar

Cada carril en **su propia carpeta de trabajo** (nunca dos agentes en la misma):

```
git fetch origin
git worktree add ../etd-<carril> -b rag/<carril> origin/main    # p. ej. ../etd-rag-ica
```

Tandas pequeñas y frecuentes, no una entrega al final:

```
python scripts/validate_fragments.py <carpeta>/<archivo>     # p. ej. regions/ica
python -m pytest tests/detective/test_fragments.py -q
git add <solo tus archivos, con su ruta>        # nunca "git add ." ni "-A"
git commit -m "rag(<carril>): <qué añade> (<n> documentos)"
git fetch origin && git rebase origin/main
git push origin HEAD:refs/heads/rag/<carril>
git push origin HEAD:main                       # si lo rechaza: fetch, rebase, validar, push
```

Prohibido `--force`, prohibido mezclar con commits de fusión, prohibido tocar
`main` con el validador en rojo.

Después de cada push: bloque `ESTADO` en `reports/<carril>.md` (formato de
`RONDA_2.md` §4) y una línea en `#general`:
`[rag-ica] 15:12 tanda 1: 18 documentos, 7 fuentes — main@<commit>`.

## 7. Horario

| Hora | Hito |
|---|---|
| 14:15 | Arranque: worktree, primer documento válido en el archivo propio |
| 15:15 | Tanda 1 en `main`: ≥ 15 documentos por ciudad; `rag-datos` con las 5 ciudades calculadas |
| 16:30 | Tanda 2: ≥ 35 por ciudad; `rag-recursos` con todos los recursos de §8 |
| 17:30 | Tanda 3: ≥ 50 por ciudad y los doce temas cubiertos; refuerzos cruzados |
| 18:30 | **Congelación de datos**: solo correcciones, solo `rag-qa` |
| 18:45 | Informe final de `rag-qa`; `rag-datos` regenera los hechos con el catálogo final |
| 19:00 | Despliegue a producción (lo hace quien el dueño autorice) y recorrido de comprobación |
| 20:00 | Submit |

## 8. Recursos del reto que hay que cubrir (`rag-recursos`)

- https://giovanni.gsfc.nasa.gov/giovanni/
- https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series
- https://appeears.earthdatacloud.nasa.gov/
- https://www.ncei.noaa.gov/cdo-web/
- https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf
- https://climexp.knmi.nl/
- https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b
- https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance
- https://donnees-data.asc-csa.gc.ca/en/dataset/rcm
- https://geo.ca/
- https://www.asc-csa.gc.ca/eng/satellites/swot/
- https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp
- https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial

Los dos artículos de terceros (Medium y Statsig) tienen copyright: resumen propio.

## 9. Lo que el reto pide y esta ronda refuerza

El reto pide elegir variables, sacar la serie de una región, verla en el tiempo
y decir **qué** cambia, **dónde**, **cuánto** y si es **significativo**, para
estudiantes de secundaria y universidad, con definiciones sencillas. Los hechos
calculados (`rag-datos`) responden qué, dónde, cuánto y si es significativo en
cinco lugares concretos; las notas regionales explican el porqué con fuentes; las
notas de método explican la palabra «significativo». Ninguna de las tres cosas
vale si una cifra no se puede seguir hasta su origen.
