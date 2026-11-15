<!-- ESTADO:INICIO -->
## ESTADO — hermes-2 — 2026-11-15 07:40 hora de Perú (Ronda 5)
Rama@commit: feature/scrapes@589566f · empujado: sí
SUITE COMPLETA sobre integracion/ronda5 fusionado: `python -m pytest -q` → **276 passed, 10 skipped, 0 failed**.
VERIFICADO: tildes → `python -X utf8 -I scripts/check_case_accents.py` → 0 problemas en 8 archivos. Arregladas en la fuente (`write_case_copy.py`), no con sed sobre el JSON; los títulos en inglés siguen «Lima, Peru».
VERIFICADO: el lugar en el texto → `answers.where` nombra Lima / Svalbard / Piura / Hielo marino del Ártico / Hielo marino del Antártico / el área de Amazonía; ya no dice «coordenadas» ni «la región seleccionada».
VERIFICADO: **las cifras no cambiaron** en los 7 casos (trend, tests, significance, period, detectability contra origin/integracion/ronda5): 0 diferencias.
VERIFICADO: el hallazgo usa «Tendencia clara y fuerte», «Tendencia significativa», «Sugerente, aun sin certeza» y «Todavía no se detecta tendencia»; 0 códigos en mayúsculas en los 14 textos.
VERIFICADO: `data/lora/DATASET_CARD.md` lleva una sección de un párrafo citable por claude-omni-2, con las cifras del §1.
VERIFICADO: hielo marino regenerado con el arreglo de antigravity-1 (69d679e) → «Based on» = «NSIDC-0051, NSIDC-0803» y «NSIDC-0051, NSIDC-0081, NSIDC-0803», sin repetidos; cifras idénticas (0 diferencias); `verify_seaice_cases.py` en verde.
ESCRITO (sin ejecutar de punta a punta): nada.
ROTO / NO HECHO: nada. Los `.jsonl` del LoRA no se tocan a propósito (regla 21).
Necesito de: nadie.
Avisos para otros carriles: (1) claude-omni-2: la sección «Known defects, in one paragraph» de `data/lora/DATASET_CARD.md` está escrita para citarla tal cual en la declaración de IA. (2) claude-omni-1: los textos de los casos ya no llevan códigos internos ni unidades inglesas en la frase; el `where` nombra el lugar, así que la interfaz no necesita componerlo. (3) antigravity-2: el «Based on» del hielo ya sale limpio del conector y de los casos congelados.
<!-- ESTADO:FIN -->

# Reportes de Hermes 2

## S1 — LISTO  (2026-11-14 15:50 UTC-5)
Rama@commit: feature/scrapes (pendiente de commit)
Qué quedó:
- `scripts/build_lora_dataset.py`: generador del dataset de entrenamiento del planificador.
  - Formato contrato §10: mensajes system/user/assistant, 9 claves en orden fijo.
  - Variables y definiciones desde `data/catalog/variables.json` (si no existe, desde `variables.seed.json`).
  - Lugares desde `data/catalog/gazetteer.json` cuando exista; si no, lista provisional de ~150 nombres.
  - Reparto de intenciones por muestreo ponderado: investigate 60 %, compare 15 %, define 10 %, out_of_scope 10 %, no_match 5 %.
  - Idioma: 55 % ES / 45 % EN. Lugares: 35 % Perú, 25 % LatAm, 40 % mundo; 15 % sin lugar.
  - Años: 15 % rango explícito, 10 % «últimos N años». Hipótesis up/down cuando la pregunta la sugiere.
  - Candidatas: la correcta + 5 distractoras (2 de la misma esfera, 3 al azar), barajadas. En `no_match` se quita la correcta.
  - Ruido: 20 % sin tildes, 10 % minúsculas, 10 % una errata. Los nombres de lugar nunca se corrompen.
  - Plantillas distintas para train (familia A) y val/test (familia B): el test no repite frases de entrenamiento.
  - Semilla fija 20261114: mismo comando, mismo dataset.
- `data/lora/train.jsonl` (2558), `val.jsonl` (509), `test.jsonl` (452), `system_prompt.txt`, `DATASET_CARD.md`.
Evidencia:
```bash
$ python scripts/build_lora_dataset.py
train=2558 val=509 test=452

$ python scripts/build_lora_dataset.py --check
intent mix (train):
  investigate    wanted 60%  actual 59.0%
  compare        wanted 15%  actual 15.8%
  define         wanted 10%  actual 10.5%
  out_of_scope   wanted 10%  actual 9.7%
  no_match       wanted 5%  actual 5.0%
language mix (train): {'es': 1403, 'en': 1155}
counts: {'train': 2558, 'val': 509, 'test': 452}
--check passed
```
Falta / riesgos:
- Regenerar cuando Hermes 1 entregue `variables.json` y `gazetteer.json` finales (S4).
- No hay paráfrasis de modelo (opcional, no usado).
Necesito de otros: Hermes 1 (catálogo v2 y gazetteer) para S4.

## S4 — LISTO  (2026-11-14 16:40 UTC-5)
Rama@commit: feature/scrapes
Qué quedó:
- Dataset regenerado contra el catálogo v2 y el gazetteer finales de Hermes 1.
- Nueva deduplicación: igualdad exacta normalizada siempre; Jaccard ≥ 0,95 solo
  en preguntas de 8+ palabras (antes 0,9 desde 4 palabras, que colapsaba las
  preguntas cortas de "define").
- Reparto verificado tras deduplicar: intenciones dentro de ±1 punto y idioma
  53,1 % ES / 46,9 % EN.
Evidencia:
```bash
$ python scripts/build_lora_dataset.py
train=4323 val=814 test=632

$ python scripts/build_lora_dataset.py --check
intent mix (train):
  investigate    wanted 60%  actual 60.3%
  compare        wanted 15%  actual 15.3%
  define         wanted 10%  actual 9.1%
  out_of_scope   wanted 10%  actual 10.2%
  no_match       wanted 5%  actual 5.1%
language mix (train): {'es': 2294, 'en': 2029}
--check passed
```
Falta / riesgos: avisar a Antigravity 2 (fase LoRA) con el recuento nuevo.
Necesito de otros: nada.

## S2 — LISTO (con un pendiente de otro carril)  (2026-11-14 16:52 UTC-5)
Rama@commit: feature/scrapes
Qué quedó:
- `scripts/freeze_case.py`: llama a `get_series` y `analyze_series` del contrato §6 y escribe
  `data/cases/<id>/{series.json,analysis.json,case.json}`. Los textos de historia quedan `TODO_HUMANO`.
- Cinco casos técnicos congelados con datos reales:
  - `lima-t2m` (POWER, 540 meses, 1981-01 → 2025-12, 18.41 °C en 1981-01)
  - `svalbard-t2m` (POWER, 540 meses)
  - `piura-prectotcorr` (POWER, 540 meses)
  - `arctic-seaice` (NSIDC, 576 meses, 11.65 → 6.69 millones de km²)
  - `antarctic-seaice` (NSIDC, 576 meses)
- Las variables hemisféricas (NSIDC, GISTEMP) se piden sin coordenadas: el conector rechaza un punto y era el fallo inicial.
Evidencia:
```bash
$ python scripts/validate_datasets.py data/cases/*/series.json
[ OK ] data/cases/antarctic-seaice/series.json
[ OK ] data/cases/arctic-seaice/series.json
[ OK ] data/cases/lima-t2m/series.json
[ OK ] data/cases/piura-prectotcorr/series.json
[ OK ] data/cases/svalbard-t2m/series.json
5/5 archivos validos
```
Falta / riesgos:
- `analysis.json` sale con la estructura vieja del motor (`metrics`, `detective_answers`), no con `AnalysisResult v2` (`trend`, `significance`, `detectability`). El contrato §6 (`analyze_series`) aún no está en `origin/feature/stats`; cuando Antigravity 2 lo publique, se vuelve a ejecutar `freeze_case.py --technical` y se regeneran los cinco.
- El caso «tendencias opuestas» no se cumple con el periodo completo: Ártico −0.41 M km²/año (p<0.001, significativo) y Antártico −0.06 (no significativo). Es el resultado honesto; el caso debe presentarse como «el Ártico baja con claridad; el Antártico todavía no se puede afirmar».
Necesito de otros: Antigravity 2 (analyze_series v2) para la estructura final del análisis.

## S3 — LISTO  (2026-11-14 16:52 UTC-5)
Rama@commit: feature/scrapes
Qué quedó: `scripts/build_atlas.py` → `data/atlas/<ID>.json` (TrendMap v2).
- GISTEMP_TANOM: un archivo, 16 000 celdas, 15 398 significativas (96.2 %), 0.77 MB, 14 s.
- T2M regional Sudamérica: 16 teselas de 4°, 759 celdas, 455 significativas (59.9 %, todas al alza), 0.04 MB, 0.9 min.
- Progreso reanudable en `data/cache/atlas_<ID>.npz` (comprimido; la primera versión en JSON pesaba 542 MB y se descartó).
- Tendencia por celda sobre **medias anuales** (Sen + Mann-Kendall + BH FDR), que es la reducción que el contrato ya usa para la prueba anual; sin promediar pendientes ni valores p.
- Si el archivo supera 3 MB, agrupa 2×2 promediando las series antes de analizar.
Evidencia:
```bash
$ python scripts/build_atlas.py --variable GISTEMP_TANOM
wrote data/atlas/GISTEMP_TANOM.json
size=0.77 MB cells=16000 significant=15398 (96.2%) elapsed=0.2 min

$ python scripts/build_atlas.py --variable T2M --bbox -82 -18 -68 -2 --tile 4
wrote data/atlas/T2M.json
size=0.04 MB cells=759 significant=455 (59.9%) elapsed=0.9 min
```
Falta / riesgos: `analyze_grid` del contrato §6 aún no existe; se usa una implementación local equivalente marcada en `method_note`.
Necesito de otros: Antigravity 2 (`analyze_grid`) para sustituir el fallback.

### Nota de verificación (16:55)
La evidencia de S2 se obtuvo ejecutando `scripts/validate_datasets.py` de la versión de
`origin/feature/data-pipeline` (la que acepta rutas de `series.json`). La copia que trae mi
rama `feature/scrapes` es anterior a ese cambio: solo audita `data/processed/` y da por
buenos los 4 archivos sintéticos que la v2 manda borrar. No edito ese archivo porque es
del carril de Antigravity 1; lo señalo para que el arquitecto lo resuelva al integrar
(la versión vigente es la de `feature/data-pipeline`).

---

## Ronda 3 — ESTADO de hermes-2 (2026-11-14 21:05 UTC-5)

**Rama:** `feature/scrapes`

**Suite completa sobre `main` fusionado (regla 14):**

```
$ python -m pytest -q
1 failed, 223 passed, 9 skipped, 54 warnings in 155.28s
FAILED tests/stats/test_trend_engine.py::test_published_nasa_benchmarks
```

### Tarea 1 — LISTO

`python -X utf8 -I scripts/regenerate_cases_v2.py` sobre `main` fusionado:

```
--- lima-t2m (T2M)              OK verdict=SIGNIFICANT n=540
--- svalbard-t2m (T2M)          OK verdict=SIGNIFICANT_STRONG n=540
--- piura-prectotcorr           OK verdict=SUGGESTIVE n=540
--- arctic-seaice               OK verdict=SIGNIFICANT n=576
--- antarctic-seaice            OK verdict=NOT_SIGNIFICANT n=576
```

`lima-t2m` queda **SIGNIFICANT** (era `SIGNIFICANT_STRONG` congelado), que es lo que responde el
motor ya integrado.

Nota de entorno: el venv local no tenía `pymannkendall` ni `httpx` (este último lo necesita
`starlette.testclient` para `tests/api/`), aunque ambos están declarados. Instalados sin tocar
`requirements.txt`.

### Tarea 2 — NO HECHO (bloqueado por antigravity-1)

Los casos de hielo se regeneraron, pero **siguen con el relleno dentro**:

```
$ python - <<'PY'   # sobre data/cases/<id>/series.json
arctic-seaice     min: -9999.0 | valores < 0: 2
antarctic-seaice  min: -9999.0 | valores < 0: 2
PY
```

El defecto se ve en la tabla de los cinco casos regenerados: Sen y OLS salen de signo opuesto.

| caso | sen/década | ols/década | veredicto |
|---|---|---|---|
| arctic-seaice | **−0,505** | **+25,746** | SIGNIFICANT |
| antarctic-seaice | **−0,035** | **+26,158** | NOT_SIGNIFICANT |
| lima-t2m | 0,159 | 0,131 | SIGNIFICANT |
| svalbard-t2m | 0,699 | 0,772 | SIGNIFICANT_STRONG |
| piura-prectotcorr | −0,011 | −0,071 | SUGGESTIVE |

Comprobado a las 21:05 UTC-5: `origin/feature/data-pipeline` sigue en `33e27fa` y
`git diff origin/main FETCH_HEAD -- src/etl/nsidc_seaice.py` sale vacío; el arreglo del −9999
**aún no está empujado**. En cuanto llegue, estos dos comandos cierran la tarea:

```
python -X utf8 -I scripts/regenerate_cases_v2.py --id arctic-seaice
python -X utf8 -I scripts/regenerate_cases_v2.py --id antarctic-seaice
```

Criterio de aceptación que comprobaré: `min(series.raw) >= 0`, `1987-12` y `1988-01` en `null`,
y OLS con el mismo signo y orden de magnitud que Sen.

### Tarea 3 — LISTO

Dos casos nuevos con los CSV reales de Giovanni (557 meses cada uno, `user_upload`, con la
«URL to Reproduce Results» en `provenance.request_url`):

| caso | veredicto | Sen (°C o mm/día por década) | OLS | periodo |
|---|---|---|---|---|
| amazonia-t2m | SIGNIFICANT_STRONG | 0,186 | 0,191 | 1980-01 → 2026-05 |
| amazonia-prectotcorr | NOT_SIGNIFICANT | ver `analysis.json` | ver `analysis.json` | 1980-01 → 2026-05 |

`amazonia-t2m`: `n_obs` 557, `tests_agree: true`, Mann-Kendall p < 1e-4.

**Aviso para la entrega:** los dos CSV son de **MERRA-2** (vía GES DISC), la misma fuente que
POWER. Sirven como caso de «sube tu propio CSV», no como instrumento distinto. Nadie debe
presentarlos como GPM, MODIS u OMI.

### Tarea 4 — pendiente (dom 10:00)

Nombre y frase de hallazgo por caso, en inglés y español, sacados solo de los números.

### Para el resto del enjambre

- **antigravity-2:** cuando entre el arreglo del −9999, `test_published_nasa_benchmarks` debe
  volver a verde **sin tocar la aserción** (regla 13). Mi regeneración de casos no la afecta.
- **antigravity-1:** avisadme del commit; regenero los dos casos de hielo y publico la evidencia.
- **claude-omni-1:** hay **7** casos en `/api/cases` (antes 5); los dos nuevos son
  `amazonia-t2m` y `amazonia-prectotcorr`, con `provenance.kind = user_upload`.

---

## Ronda 3 — diagnostico del −9999 para antigravity-1 (2026-11-14 21:20 UTC-5)

No hay `swarmchat` en este entorno, asi que dejo el diagnostico aqui y en el commit.

**La fuente**, no el parser, es quien trae el relleno. Fila real de `N_12_extent_v4.0.csv`
(`https://noaadata.apps.nsidc.org/NOAA/G02135/north/monthly/data/N_12_extent_v4.0.csv`):

```
1986, 12,    NSIDC-0051,      N,  13.22,  10.53
1987, 12,         -9999,      N,  -9999,  -9999     <-- relleno en las tres columnas
1988, 12,    NSIDC-0051,      N,  13.63,  11.99
```

Lo mismo en `N_01` con `1988, 1`. `src/etl/nsidc_seaice.py::parse_csv` hace `float(clean["extent"])`
sin comprobar el valor, asi que `-9999.0` entra como dato y llega hasta `series.json`.

**Arreglo minimo sugerido** (carril de antigravity-1):

```python
FILL = (-9999.0, -999.0)          # y el que declare la fuente
raw = float(clean["extent"])
if raw in FILL or raw < 0:        # el hielo marino no es negativo: -9999 es relleno
    return None -> value: null, y contarlo en provenance.n_missing
```

Y en el `analysis.json`, `n_missing` deberia pasar de 0 a 2 en cada hemisferio.

**Verificador listo**: `python -X utf8 -I scripts/verify_seaice_cases.py`
(exit 1 mientras haya relleno; comprueba `min >= 0`, los dos meses en `null` y que OLS y Sen
tengan el mismo signo). Hoy da:

```
arctic-seaice:    min=-9999.0 | 1987-12=-9999.0 1988-01=-9999.0 | Sen=-0.5046 OLS=25.7464 -> FALLA
antarctic-seaice: min=-9999.0 | 1987-12=-9999.0 1988-01=-9999.0 | Sen=-0.0347 OLS=26.1579 -> FALLA
exit=1
```

## Ronda 3 — smoke y copy de casos (2026-11-14 21:25 UTC-5)

```
$ python -X utf8 scripts/smoke_api.py http://127.0.0.1:8791
10 passed · 0 skipped · 0 failed

$ curl /api/cases
7 casos servidos:
  lima-t2m SIGNIFICANT | Lima, Peru: air temperature 1981-2025
  svalbard-t2m SIGNIFICANT_STRONG | ...
  piura-prectotcorr SUGGESTIVE | ...
  arctic-seaice SIGNIFICANT | (sin titulo: la serie aun lleva -9999)
  antarctic-seaice NOT_SIGNIFICANT | (sin titulo)
  amazonia-t2m SIGNIFICANT_STRONG | Amazon basin: air temperature 1980-2026 (user CSV)
  amazonia-prectotcorr NOT_SIGNIFICANT | Amazon basin: precipitation 1980-2026 (user CSV)
```

Tarea 4 adelantada para los 5 casos estables (`scripts/write_case_copy.py`). Los dos de hielo se
quedan sin texto a proposito: escribir una frase de hallazgo sobre una serie con −9999 seria
publicar un numero falso.

---

## Ronda 4 — hermes-2 (2026-11-15 01:35 UTC-5)

### Tarea 1 — LISTO: hielo marino sin −9999

```
$ python -X utf8 -I scripts/verify_seaice_cases.py
arctic-seaice: min=3.57 | 1987-12=None 1988-01=None | Sen=-0.4953 OLS=-0.5106 -> OK
antarctic-seaice: min=1.98 | 1987-12=None 1988-01=None | Sen=-0.0481 OLS=-0.0822 -> OK
exit=0
```

Dos meses faltantes por hemisferio (`n_missing = 2`), no ceros. El Ártico pasa de
`SIGNIFICANT` a **`SIGNIFICANT_STRONG`**: el relleno era lo que hacía discrepar a las pruebas.

### Tarea 2 — LISTO: título y hallazgo de los 7 casos

`scripts/write_case_copy.py` → 7/7 con `title` y `finding` en inglés y español;
`index.json` sin títulos vacíos. Cada cifra del texto coincide con su `analysis.json`.

### Tarea 3 — LISTO: defectos del dataset medidos

En `data/lora/DATASET_CARD.md`, sección «Measured defects». Los `.jsonl` **no** se tocaron
(el adaptador canónico se entrenó con ellos, regla 21).

**a) Rangos sin años.** 92/4323 en train con el arquetipo literal `entre  y` / `between  and`
(2,1 %); 174 con la lectura amplia (cualquier conector de rango sin año: 4,0 %). val 70/97,
test 51/63. **No consigo reproducir el 132** del informe: publico las dos lecturas y el comando,
en vez de una tercera cifra sin método.
Causa: `build_lora_dataset.py` solo rellena `{year0}` en el 15 % de los casos.

**b) `out_of_scope` con variable.** 440/440 en train, 83/83 en val, 71/71 en test: **el 100 %**.
`investigate`/`compare` nunca van sin variable (0 de 3268/601/466) y `no_match` está bien.
Causa exacta, `scripts/build_lora_dataset.py:815`:
```python
plan = make_plan(intent, vid if intent != "no_match" else None, ...)
```
`out_of_scope` debería estar en esa condición. Es un cambio de una línea, pero beneficia
solo si se reentrena; fuera del alcance de la congelación (regla 18).

### Suite completa sobre `main` fusionado (regla 14)

```
$ python -m pytest -q
3 failed, 235 passed, 9 skipped, 66 warnings in 169.90s
FAILED tests/detective/test_pipeline.py::test_pipeline_offline[what is soil moisture?-en-GWETTOP]
FAILED tests/detective/test_pipeline.py::test_missing_variable_is_declared_not_substituted[...]
FAILED tests/ml/test_lora_real.py::test_plan_with_lora_missing_adapter_raises_error
```

**Ninguna es de este carril.** Las dos de `test_pipeline` son la regla 19 (variables `planned`
como candidatas, carril de claude-omni-2); la de `test_lora_real` es el respaldo silencioso de
`src/ml/serve.py:65` (carril de antigravity-2). Los casos de hielo ya no rompen
`test_published_nasa_benchmarks`, que está en verde.

### Tarea 4 — LISTO: tabla comparativa para elegir el caso protagonista

| caso | variable | veredicto | Sen/década | OLS/década | MK p | MK autocorr. p | MK anual p | t de OLS p | años que faltan |
|---|---|---|---|---|---|---|---|---|---|
| `lima-t2m` | T2M | **SIGNIFICANT** | 0.159 | 0.131 | 3.3e-15 | 3.9e-05 | 0.00826 | 0.0723 | 13.3 |
| `svalbard-t2m` | T2M | **SIGNIFICANT_STRONG** | 0.699 | 0.772 | 0 | 6.0e-11 | 1.1e-07 | 2.5e-11 | 0.0 |
| `piura-prectotcorr` | PRECTOTCORR | **SUGGESTIVE** | -0.011 | -0.0711 | 0.0753 | 0 | 0.0719 | 0.398 | 341.7 |
| `arctic-seaice` | SEAICE_EXTENT_N | **SIGNIFICANT_STRONG** | -0.495 | -0.511 | 0 | 0 | 2.2e-16 | 5.9e-26 | 0.0 |
| `antarctic-seaice` | SEAICE_EXTENT_S | **NOT_SIGNIFICANT** | -0.0481 | -0.0822 | 0.0259 | 0.631 | 0.461 | 0.235 | 84.8 |
| `amazonia-t2m` | T2M | **SIGNIFICANT_STRONG** | 0.186 | 0.191 | 0 | 0 | 1.4e-06 | 6.3e-07 | 0.0 |
| `amazonia-prectotcorr` | PRECTOTCORR | **NOT_SIGNIFICANT** | -0.0829 | -0.0605 | 0.34 | 0.237 | 0.484 | 0.604 | 82.5 |

---

## Ronda 5 — hermes-2 (2026-11-15 07:35 hora de Perú)

Base: `origin/integracion/ronda5`. Cinco tareas, cinco commits, todas empujadas.

### Tarea 1 — LISTO: tildes en los textos en español (08:00)

Arregladas en la **fuente** (`scripts/write_case_copy.py`) y reaplicadas, no con un sed sobre
el JSON: así regenerar no las vuelve a perder. 64 apariciones en `index.json` y los 7
`case.json`: Perú, precipitación, Extensión, Ártico, Antártico, amazónica, subió, bajó,
década, mínimos, exportación, más `autocorrelación`, `así`, `km²`, `mm/día`, `años`,
`pequeña`, `área`.

Un primer reemplazo metió la tilde también en los títulos en **inglés** («Lima, Perú: air
temperature»); corregido: el inglés escribe «Lima, Peru». El comprobador nuevo vigila las
dos direcciones.

```
$ python -X utf8 -I scripts/check_case_accents.py
0 problemas en 8 archivos
exit=0
```

`scripts/check_case_accents.py` es nuevo y queda en el repo.

### Tarea 2 — LISTO: el lugar en el texto, sin cambiar cifras (08:30)

`answers.where` ya no dice «coordenadas (-12.05°, -77.03°)» ni «la región seleccionada»:

| caso | es | en |
|---|---|---|
| lima-t2m | Observado en Lima, Perú. | Observed in Lima, Peru. |
| svalbard-t2m | Observado en Svalbard, Noruega. | Observed in Svalbard, Norway. |
| piura-prectotcorr | Observado en Piura, Perú. | Observed in Piura, Peru. |
| arctic-seaice | Observado en Hielo marino del Ártico. | Observed in Arctic sea ice. |
| antarctic-seaice | Observado en Hielo marino del Antártico. | Observed in Antarctic sea ice. |
| amazonia-* | Observado en el área de Amazonía (cuenca baja del Amazonas). | Observed in the Amazon (lower Amazon basin) area. |

Los 7 se regeneraron con la API real pasando el nombre (`region.name`), y una caja se
presenta como área, no como ciudad.

**Las cifras no cambiaron.** Comparadas campo por campo contra `origin/integracion/ronda5`
(`trend`, `tests`, `significance`, `period`, `detectability`), en los 7 casos:

```
lima-t2m  svalbard-t2m  piura-prectotcorr  arctic-seaice
antarctic-seaice  amazonia-t2m  amazonia-prectotcorr
-> trend, tests, significance, period, detectability: igual en los 7
diferencias en cifras: 0
```

### Tarea 3 — LISTO: veredicto con palabras, no con el código (09:00)

Los textos ya no escriben `SIGNIFICANT_STRONG` / `NOT_SIGNIFICANT` / `SUGGESTIVE`. Usan las
mismas etiquetas que la interfaz (`src/ui/i18n.js`, claves `verdict.*`): «Clear, strong
trend» / «Tendencia clara y fuerte», «Significant trend» / «Tendencia significativa»,
«Suggestive, not yet certain» / «Sugerente, aun sin certeza», «No trend detectable so far» /
«Todavía no se detecta tendencia».

```
codigos restantes en los 14 textos (7 casos x 2 idiomas): ninguno
```

### Tarea 4 — LISTO: la ficha del dataset, citable (10:00)

Ya estaba la sección «Measured defects» de la Ronda 4. Añadida delante una sección de un
párrafo, en inglés, para que claude-omni-2 la cite en la declaración de uso de IA, con las
cifras del §1 y la consecuencia: el test sale del mismo generador que el entrenamiento, así
que el 84,5 % sobreestima y el producto planifica con reglas.

### Tarea 5 — LISTO (11:00, con el arreglo de antigravity-1)

Fusionado su commit `69d679e` y regenerados los dos casos de hielo:

```
antes:  NSIDC-0051, NSIDC-0051,NSIDC-0081, NSIDC-0803   (repetido y sin espacio)
ahora:  arctic-seaice    -> NSIDC-0051, NSIDC-0803
        antarctic-seaice -> NSIDC-0051, NSIDC-0081, NSIDC-0803
```

Cifras de los dos casos otra vez idénticas a la base: **0 diferencias**.

### Suite completa (regla 14)

```
$ python -m pytest -q
276 passed, 10 skipped, 74 warnings in 333.69s
```
(antes de fusionar el arreglo: 275 passed, 10 skipped)

### Comprobaciones que quedan al día

- `python -X utf8 -I scripts/verify_seaice_cases.py` → exit 0.
- `python -X utf8 -I scripts/check_case_accents.py` → 0 problemas en 8 archivos.
- Los 7 casos conservan `title` y `finding` en los dos idiomas, sin códigos internos.
